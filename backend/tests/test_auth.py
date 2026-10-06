import unittest
import uuid
from unittest.mock import patch
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from src.main import app
from src.db.session import bind_engine
from src.models import Base

class TestAuthAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Setup isolated in-memory SQLite database for unit tests
        cls.test_engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool
        )
        bind_engine(cls.test_engine)
        Base.metadata.create_all(bind=cls.test_engine)
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        Base.metadata.drop_all(bind=cls.test_engine)

    def test_auth_status_unauthorized(self):
        response = self.client.get("/api/v1/auth/me")
        self.assertEqual(response.status_code, 401)

    @patch("src.api.auth.verify_google_id_token")
    def test_google_auth_success(self, mock_verify):
        mock_verify.return_value = {
            "iss": "https://accounts.google.com",
            "sub": "google_uid_98765",
            "email": "investor.prod@gmail.com",
            "name": "Google Investor",
            "picture": "https://lh3.googleusercontent.com/a/dev",
            "email_verified": True
        }
        response = self.client.post(
            "/api/v1/auth/google",
            json={"credential": "valid_google_jwt_token_sample"}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("access_token", data)
        self.assertEqual(data.get("token_type"), "bearer")
        self.assertEqual(data.get("user", {}).get("email"), "investor.prod@gmail.com")

        # Test calling /me with the returned Bearer token
        token = data["access_token"]
        me_resp = self.client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        self.assertEqual(me_resp.status_code, 200)
        me_data = me_resp.json()
        self.assertEqual(me_data.get("user", {}).get("email"), "investor.prod@gmail.com")

    def test_user_registration_and_login(self):
        unique_email = f"tester_{uuid.uuid4().hex[:8]}@example.com"
        reg_resp = self.client.post(
            "/api/v1/auth/register",
            json={
                "email": unique_email,
                "password": "Password123!",
                "full_name": "Test Trader"
            }
        )
        self.assertIn(reg_resp.status_code, [200, 201])

        login_resp = self.client.post(
            "/api/v1/auth/login",
            json={
                "email": unique_email,
                "password": "Password123!"
            }
        )
        self.assertEqual(login_resp.status_code, 200)
        self.assertIn("access_token", login_resp.json())

    @patch("src.api.auth.verify_google_id_token")
    def test_broker_session_management(self, mock_verify):
        mock_verify.return_value = {
            "iss": "https://accounts.google.com",
            "sub": "google_uid_broker_test",
            "email": "broker.user@gmail.com",
            "name": "Broker Trader",
            "email_verified": True
        }
        # Authenticate via Google
        auth_resp = self.client.post(
            "/api/v1/auth/google",
            json={"credential": "sample_valid_token"}
        )
        self.assertEqual(auth_resp.status_code, 200)
        token = auth_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Store broker enctoken
        enctoken_val = "demo_enctoken_secret_value_12345"
        broker_resp = self.client.post(
            "/api/v1/auth/broker/enctoken",
            json={"enctoken": enctoken_val},
            headers=headers
        )
        self.assertEqual(broker_resp.status_code, 200)
        self.assertTrue(broker_resp.json().get("has_enctoken"))

        # Check broker status
        status_resp = self.client.get("/api/v1/auth/broker/status", headers=headers)
        self.assertEqual(status_resp.status_code, 200)
        self.assertTrue(status_resp.json().get("has_enctoken"))
        self.assertEqual(status_resp.json().get("broker"), "ZERODHA")

        # Disconnect broker
        del_resp = self.client.delete("/api/v1/auth/broker/disconnect", headers=headers)
        self.assertEqual(del_resp.status_code, 200)

        # Re-check status
        status_resp2 = self.client.get("/api/v1/auth/broker/status", headers=headers)
        self.assertFalse(status_resp2.json().get("has_enctoken"))

if __name__ == "__main__":
    unittest.main()

