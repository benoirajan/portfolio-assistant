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

    @patch("src.services.email_service.email_service.send_verification_otp")
    def test_user_registration_and_login(self, mock_send_email):
        mock_send_email.return_value = True
        unique_email = f"tester_{uuid.uuid4().hex[:8]}@example.com"
        reg_resp = self.client.post(
            "/api/v1/auth/register",
            json={
                "email": unique_email,
                "password": "Password123!",
                "full_name": "Test Trader"
            }
        )
        self.assertEqual(reg_resp.status_code, 201)
        reg_data = reg_resp.json()
        self.assertEqual(reg_data.get("status"), "otp_sent")
        mock_send_email.assert_called_once()

        # Query OTP from test database
        from sqlalchemy import select
        from src.models.user import User
        from src.db.session import get_db_session

        with get_db_session() as db:
            user_rec = db.execute(select(User).where(User.email == unique_email)).scalar_one()
            otp_code = user_rec.verification_otp

        self.assertIsNotNone(otp_code)
        self.assertEqual(len(otp_code), 6)

        # Login before verification should be blocked with 403 EMAIL_NOT_VERIFIED
        unverified_login = self.client.post(
            "/api/v1/auth/login",
            json={
                "email": unique_email,
                "password": "Password123!"
            }
        )
        self.assertEqual(unverified_login.status_code, 403)
        self.assertEqual(unverified_login.json().get("detail"), "EMAIL_NOT_VERIFIED")

        # Wrong OTP fails with 400
        wrong_otp_resp = self.client.post(
            "/api/v1/auth/verify-otp",
            json={"email": unique_email, "otp": "000000"}
        )
        self.assertEqual(wrong_otp_resp.status_code, 400)

        # Correct OTP verifies user and returns access token
        verify_resp = self.client.post(
            "/api/v1/auth/verify-otp",
            json={"email": unique_email, "otp": otp_code}
        )
        self.assertEqual(verify_resp.status_code, 200)
        verify_data = verify_resp.json()
        self.assertIn("access_token", verify_data)
        self.assertTrue(verify_data.get("user", {}).get("is_verified"))

        # Subsequent login now succeeds with 200
        login_resp = self.client.post(
            "/api/v1/auth/login",
            json={
                "email": unique_email,
                "password": "Password123!"
            }
        )
        self.assertEqual(login_resp.status_code, 200)
        self.assertIn("access_token", login_resp.json())

    @patch("src.services.email_service.email_service.send_verification_otp")
    def test_resend_otp(self, mock_send_email):
        mock_send_email.return_value = True
        unique_email = f"resend_{uuid.uuid4().hex[:8]}@example.com"
        self.client.post(
            "/api/v1/auth/register",
            json={"email": unique_email, "password": "Password123!"}
        )
        resend_resp = self.client.post(
            "/api/v1/auth/resend-otp",
            json={"email": unique_email}
        )
        self.assertEqual(resend_resp.status_code, 200)
        self.assertEqual(resend_resp.json().get("status"), "success")

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

