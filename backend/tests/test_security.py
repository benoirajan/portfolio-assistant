import unittest
from datetime import timedelta
from unittest.mock import patch
from src.core.security import (
    hash_password,
    verify_password,
    encrypt_credential,
    decrypt_credential,
    create_access_token,
    decode_access_token,
    verify_google_id_token,
)

class TestSecurityModule(unittest.TestCase):
    def test_password_hashing_and_verification(self):
        password = "SecurePassword123!"
        hashed = hash_password(password)
        self.assertTrue(hashed.startswith("pbkdf2_sha256$"))
        self.assertTrue(verify_password(password, hashed))
        self.assertFalse(verify_password("WrongPassword", hashed))
        self.assertFalse(verify_password("", hashed))
        self.assertFalse(verify_password(password, ""))

    def test_empty_password_raises(self):
        with self.assertRaises(ValueError):
            hash_password("")

    def test_credential_encryption_and_decryption(self):
        enctoken = "enctoken_sample_secret_key_12345"
        encrypted = encrypt_credential(enctoken)
        self.assertNotEqual(enctoken, encrypted)
        decrypted = decrypt_credential(encrypted)
        self.assertEqual(decrypted, enctoken)

    def test_empty_credential_encryption(self):
        self.assertEqual(encrypt_credential(""), "")
        self.assertEqual(decrypt_credential(""), "")

    def test_jwt_create_and_decode(self):
        payload = {"sub": "user_123", "email": "investor@example.com", "tier": "PRO"}
        token = create_access_token(payload, expires_delta=timedelta(minutes=15))
        self.assertIsInstance(token, str)
        self.assertEqual(len(token.split(".")), 3)

        decoded = decode_access_token(token)
        self.assertIsNotNone(decoded)
        self.assertEqual(decoded.get("sub"), "user_123")
        self.assertEqual(decoded.get("email"), "investor@example.com")
        self.assertEqual(decoded.get("tier"), "PRO")

    def test_jwt_expired_token(self):
        payload = {"sub": "user_123"}
        token = create_access_token(payload, expires_delta=timedelta(seconds=-10))
        decoded = decode_access_token(token)
        self.assertIsNone(decoded)

    def test_jwt_tampered_token(self):
        payload = {"sub": "user_123"}
        token = create_access_token(payload, expires_delta=timedelta(minutes=5))
        tampered_token = token[:-5] + "XXXXX"
        decoded = decode_access_token(tampered_token)
        self.assertIsNone(decoded)

    @patch("google.oauth2.id_token.verify_oauth2_token")
    def test_google_id_token_verification(self, mock_verify):
        mock_verify.return_value = {
            "iss": "https://accounts.google.com",
            "sub": "google_sub_123",
            "email": "investor@gmail.com",
            "name": "Investor User",
            "picture": "https://lh3.googleusercontent.com/a/photo",
            "email_verified": True
        }
        result = verify_google_id_token("real_or_mock_token_structure")
        self.assertEqual(result.get("email"), "investor@gmail.com")
        self.assertEqual(result.get("sub"), "google_sub_123")
        self.assertTrue(result.get("email_verified"))

if __name__ == "__main__":
    unittest.main()

