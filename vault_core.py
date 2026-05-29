import os
import json
import base64
import hashlib
import sys
import secrets
import string
import logging
from typing import Optional
from cryptography.fernet import Fernet

# --- Data Directory ---
if sys.platform == "win32":
    _BASE = os.environ.get("APPDATA", os.path.expanduser("~"))
    DATA_DIR = os.path.join(_BASE, "AnaysPasswordVault")
else:
    _BASE = os.environ.get("XDG_DATA_HOME", os.path.join(os.path.expanduser("~"), ".local", "share"))
    DATA_DIR = os.path.join(_BASE, "anays-password-vault")

os.makedirs(DATA_DIR, exist_ok=True)

# Configuration
VAULT_FILE = os.path.join(DATA_DIR, "password_vault.enc")
MASTER_HASH_FILE = os.path.join(DATA_DIR, "master.hash")
SALT_FILE = os.path.join(DATA_DIR, "vault.salt")
PBKDF2_ITERATIONS = 100000  # Key stretching iterations
RECOVERY_CODES_FILE = os.path.join(DATA_DIR, "recovery_codes.json")
RECOVERY_CODES_COUNT = 5

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def _generate_salt() -> bytes:
    """Generate a new random 16-byte salt."""
    return os.urandom(16)


def _load_salt() -> bytes:
    """Load salt from file, or create one if it doesn't exist."""
    if not os.path.exists(SALT_FILE):
        salt = _generate_salt()
        with open(SALT_FILE, "wb") as f:
            f.write(salt)
        return salt
    with open(SALT_FILE, "rb") as f:
        return f.read()


def save_master_password(master_password: str):
    """Hash master password with PBKDF2 and save with salt."""
    salt = _load_salt()
    hash_bytes = hashlib.pbkdf2_hmac(
        "sha256", master_password.encode(), salt, PBKDF2_ITERATIONS
    )
    with open(MASTER_HASH_FILE, "w") as f:
        f.write(hash_bytes.hex())


def verify_master_password(master_password: str) -> bool:
    """Verify master password against stored hash using constant-time comparison."""
    if not os.path.exists(MASTER_HASH_FILE):
        save_master_password(master_password)
        return True

    salt = _load_salt()
    with open(MASTER_HASH_FILE, "r") as f:
        stored_hash_hex = f.read().strip()

    hash_bytes = hashlib.pbkdf2_hmac(
        "sha256", master_password.encode(), salt, PBKDF2_ITERATIONS
    )
    input_hash_hex = hash_bytes.hex()

    # Constant-time comparison to prevent timing attacks
    return hashlib.sha256(stored_hash_hex.encode()).digest() == hashlib.sha256(input_hash_hex.encode()).digest()


def generate_recovery_codes(master_password: str) -> list:
    """Generate recovery codes and store them encrypted. Returns the plain text codes."""
    alphabet = string.ascii_uppercase + string.digits
    stored = []
    codes = []
    for _ in range(RECOVERY_CODES_COUNT):
        code = '-'.join(
            ''.join(secrets.choice(alphabet) for _ in range(4))
            for _ in range(3)
        )
        codes.append(code)
        code_hash = hashlib.sha256(code.encode()).hexdigest()
        code_salt = os.urandom(16)
        code_key = hashlib.pbkdf2_hmac('sha256', code.encode(), code_salt, PBKDF2_ITERATIONS, dklen=32)
        code_key_b64 = base64.urlsafe_b64encode(code_key)
        fernet = Fernet(code_key_b64)
        encrypted_pw = fernet.encrypt(master_password.encode())
        stored.append({
            "hash": code_hash,
            "salt": code_salt.hex(),
            "encrypted": base64.b64encode(encrypted_pw).decode()
        })
    with open(RECOVERY_CODES_FILE, 'w') as f:
        json.dump(stored, f)
    return codes


def verify_recovery_code(code: str) -> Optional[str]:
    """Verify a recovery code. Returns the master password if valid, None otherwise."""
    if not os.path.exists(RECOVERY_CODES_FILE):
        return None
    with open(RECOVERY_CODES_FILE, 'r') as f:
        stored = json.load(f)
    code_hash = hashlib.sha256(code.encode()).hexdigest()
    for i, entry in enumerate(stored):
        if entry["hash"] == code_hash:
            code_salt = bytes.fromhex(entry["salt"])
            encrypted_pw = base64.b64decode(entry["encrypted"])
            code_key = hashlib.pbkdf2_hmac('sha256', code.encode(), code_salt, PBKDF2_ITERATIONS, dklen=32)
            code_key_b64 = base64.urlsafe_b64encode(code_key)
            fernet = Fernet(code_key_b64)
            try:
                master_pw = fernet.decrypt(encrypted_pw).decode()
                stored.pop(i)
                with open(RECOVERY_CODES_FILE, 'w') as f:
                    json.dump(stored, f)
                return master_pw
            except Exception:
                return None
    return None


def has_recovery_codes() -> bool:
    return os.path.exists(RECOVERY_CODES_FILE)


def derive_key(master_password: str) -> bytes:
    """Derive a 32-byte Fernet key from the master password using PBKDF2."""
    salt = _load_salt()
    key = hashlib.pbkdf2_hmac(
        "sha256", master_password.encode(), salt, PBKDF2_ITERATIONS, dklen=32
    )
    return base64.urlsafe_b64encode(key)


def encrypt_data(data: dict, key: bytes) -> bytes:
    """Encrypt dictionary using Fernet (symmetric encryption)."""
    fernet = Fernet(key)
    json_data = json.dumps(data, ensure_ascii=False).encode("utf-8")
    return fernet.encrypt(json_data)


def decrypt_data(enc_data: bytes, key: bytes) -> dict:
    """Decrypt Fernet-encrypted data and return dictionary."""
    fernet = Fernet(key)
    try:
        decrypted = fernet.decrypt(enc_data)
        return json.loads(decrypted.decode("utf-8"))
    except Exception as e:
        logging.error(f"Decryption failed: {e}")
        raise ValueError("Incorrect master password or corrupted vault file.")


def load_vault(key: bytes) -> dict:
    """Load encrypted password vault from file."""
    if not os.path.exists(VAULT_FILE):
        logging.info("No vault file found. Starting fresh.")
        return {}
    with open(VAULT_FILE, "rb") as f:
        encrypted = f.read()
    if not encrypted:
        return {}
    return decrypt_data(encrypted, key)


def save_vault(data: dict, key: bytes):
    """Encrypt and save data to vault file."""
    encrypted = encrypt_data(data, key)
    with open(VAULT_FILE, "wb") as f:
        f.write(encrypted)
    logging.info(f"Vault saved with {len(data)} entries.")
