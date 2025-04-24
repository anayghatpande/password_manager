import os
import json
import base64
import getpass
import hashlib
from cryptography.fernet import Fernet

VAULT_FILE = "password_vault.enc"

# Add this to the top
MASTER_HASH_FILE = "master.hash"

def save_master_password(master_password: str):
    hash_value = hashlib.sha256(master_password.encode()).hexdigest()
    with open(MASTER_HASH_FILE, "w") as f:
        f.write(hash_value)

def verify_master_password(master_password: str) -> bool:
    if not os.path.exists(MASTER_HASH_FILE):
        save_master_password(master_password)  # First time setup
        return True
    with open(MASTER_HASH_FILE, "r") as f:
        stored_hash = f.read().strip()
    input_hash = hashlib.sha256(master_password.encode()).hexdigest()
    return stored_hash == input_hash

def derive_key(master_password: str) -> bytes:
    """Derive a 32-byte Fernet key from the master password."""
    return base64.urlsafe_b64encode(hashlib.sha256(master_password.encode()).digest())

def encrypt_data(data: dict, key: bytes) -> bytes:
    """Encrypt dictionary using Fernet."""
    fernet = Fernet(key)
    json_data = json.dumps(data).encode()
    return fernet.encrypt(json_data)

def decrypt_data(enc_data: bytes, key: bytes) -> dict:
    """Decrypt Fernet-encrypted data and return dictionary."""
    fernet = Fernet(key)
    try:
        decrypted = fernet.decrypt(enc_data)
        return json.loads(decrypted.decode())
    except Exception:
        raise ValueError("Incorrect master password or corrupted file.")

def load_vault(key: bytes) -> dict:
    """Load encrypted password vault."""
    if not os.path.exists(VAULT_FILE):
        return {}
    with open(VAULT_FILE, "rb") as f:
        encrypted = f.read()
    return decrypt_data(encrypted, key)

def save_vault(data: dict, key: bytes):
    """Encrypt and save data to vault file."""
    encrypted = encrypt_data(data, key)
    with open(VAULT_FILE, "wb") as f:
        f.write(encrypted)
