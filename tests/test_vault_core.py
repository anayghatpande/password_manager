import os
import json
import tempfile
from unittest.mock import patch

import pytest
from cryptography.fernet import Fernet

import vault_core


@pytest.fixture(autouse=True)
def temp_data_dir():
    """Redirect vault_core file paths to a temp directory."""
    with tempfile.TemporaryDirectory() as tmp:
        patches = [
            patch("vault_core.DATA_DIR", tmp),
            patch("vault_core.VAULT_FILE", os.path.join(tmp, "password_vault.enc")),
            patch("vault_core.MASTER_HASH_FILE", os.path.join(tmp, "master.hash")),
            patch("vault_core.SALT_FILE", os.path.join(tmp, "vault.salt")),
            patch("vault_core.RECOVERY_CODES_FILE", os.path.join(tmp, "recovery_codes.json")),
        ]
        for p in patches:
            p.start()
        yield tmp
        for p in patches:
            p.stop()


class TestVaultCore:
    def test_save_and_verify_master_password(self):
        vault_core.save_master_password("MySecret123!")
        assert vault_core.verify_master_password("MySecret123!") is True
        assert vault_core.verify_master_password("WrongPassword") is False

    def test_verify_creates_hash_on_first_call(self):
        assert vault_core.verify_master_password("FirstTimePassword") is True
        assert vault_core.verify_master_password("FirstTimePassword") is True
        assert vault_core.verify_master_password("WrongPassword") is False

    def test_derive_key_is_consistent(self):
        key1 = vault_core.derive_key("SamePassword")
        key2 = vault_core.derive_key("SamePassword")
        assert key1 == key2

    def test_derive_key_differs_for_diff_passwords(self):
        key1 = vault_core.derive_key("Password1")
        key2 = vault_core.derive_key("Password2")
        assert key1 != key2

    def test_derive_key_returns_valid_fernet_key(self):
        key = vault_core.derive_key("TestKey123")
        fernet = Fernet(key)
        token = fernet.encrypt(b"hello")
        assert fernet.decrypt(token) == b"hello"

    def test_encrypt_decrypt_roundtrip(self):
        key = vault_core.derive_key("MyKey")
        data = {"test": {"username": "user1", "password": "pass1"}}
        encrypted = vault_core.encrypt_data(data, key)
        decrypted = vault_core.decrypt_data(encrypted, key)
        assert decrypted == data

    def test_decrypt_wrong_key_fails(self):
        key = vault_core.derive_key("CorrectKey")
        wrong_key = vault_core.derive_key("WrongKey")
        data = {"foo": "bar"}
        encrypted = vault_core.encrypt_data(data, key)
        with pytest.raises(ValueError):
            vault_core.decrypt_data(encrypted, wrong_key)

    def test_save_and_load_vault(self):
        key = vault_core.derive_key("VaultKey")
        vault = {"google": {"username": "a", "password": "p1"},
                 "github": {"username": "b", "password": "p2"}}
        vault_core.save_vault(vault, key)
        loaded = vault_core.load_vault(key)
        assert loaded == vault

    def test_load_vault_empty_if_no_file(self):
        key = vault_core.derive_key("Key")
        assert vault_core.load_vault(key) == {}

    def test_save_and_load_empty_vault(self):
        key = vault_core.derive_key("Key")
        vault_core.save_vault({}, key)
        assert vault_core.load_vault(key) == {}

    def test_generate_and_verify_recovery_codes(self):
        vault_core.save_master_password("MyMasterPW")
        codes = vault_core.generate_recovery_codes("MyMasterPW")
        assert len(codes) == 5

        for code in codes:
            assert len(code) == 14
            assert code.count("-") == 2

        recovered = vault_core.verify_recovery_code(codes[0])
        assert recovered == "MyMasterPW"

    def test_recovery_code_one_time_use(self):
        vault_core.save_master_password("MasterPW")
        codes = vault_core.generate_recovery_codes("MasterPW")

        vault_core.verify_recovery_code(codes[0])
        assert vault_core.verify_recovery_code(codes[0]) is None

    def test_invalid_recovery_code(self):
        vault_core.save_master_password("PW")
        vault_core.generate_recovery_codes("PW")
        assert vault_core.verify_recovery_code("INVALID-CODE-TEST") is None

    def test_recovery_code_differs_from_password(self):
        vault_core.save_master_password("PW")
        codes = vault_core.generate_recovery_codes("PW")
        for code in codes:
            assert code != "PW"

    def test_has_recovery_codes(self):
        assert vault_core.has_recovery_codes() is False
        vault_core.save_master_password("PW")
        vault_core.generate_recovery_codes("PW")
        assert vault_core.has_recovery_codes() is True
