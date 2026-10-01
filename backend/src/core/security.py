import base64
import hashlib
import hmac
import json
import logging
import os
import secrets
import time
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any

from cryptography.fernet import Fernet
from fastapi import Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select

from src.core.config import settings
from src.db.session import get_db_session
from src.models.user import User

logger = logging.getLogger("portfolio_assistant.security")

# Security Bearer Scheme
bearer_scheme = HTTPBearer(auto_error=False)


# ==============================================================================
# 1. Password Hashing (PBKDF2-HMAC-SHA256)
# ==============================================================================

def hash_password(password: str, iterations: int = 100_000) -> str:
    """Hashes password using PBKDF2-HMAC-SHA256 with a random 16-byte salt."""
    if not password:
        raise ValueError("Password cannot be empty")
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        iterations
    )
    return f"pbkdf2_sha256${iterations}${salt}${key.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against the stored PBKDF2-HMAC-SHA256 hash."""
    if not plain_password or not hashed_password:
        return False
    try:
        parts = hashed_password.split("$")
        if len(parts) != 4 or parts[0] != "pbkdf2_sha256":
            return False
        iterations = int(parts[1])
        salt = parts[2]
        expected_key_hex = parts[3]

        computed_key = hashlib.pbkdf2_hmac(
            "sha256",
            plain_password.encode("utf-8"),
            salt.encode("utf-8"),
            iterations
        )
        return hmac.compare_digest(computed_key.hex(), expected_key_hex)
    except Exception as e:
        logger.error("Password verification error: %s", e)
        return False


# ==============================================================================
# 2. Fernet AES-256 Symmetric Credential Encryption
# ==============================================================================

def _get_fernet() -> Fernet:
    """Returns a Fernet instance keyed with ENCRYPTION_SECRET_KEY."""
    raw_key = settings.ENCRYPTION_SECRET_KEY
    if not raw_key:
        raw_key = "vXz7e9K3N4P1Q8R6T2U5W7Y9A1B3C5E7G9I1K3M5O7Q="
    try:
        return Fernet(raw_key.encode() if isinstance(raw_key, str) else raw_key)
    except Exception:
        derived = base64.urlsafe_b64encode(hashlib.sha256(str(raw_key).encode()).digest())
        return Fernet(derived)


def encrypt_credential(plain_text: str) -> str:
    """Encrypts a sensitive string (e.g. Zerodha enctoken) using Fernet AES-256."""
    if not plain_text:
        return ""
    fernet = _get_fernet()
    encrypted_bytes = fernet.encrypt(plain_text.encode("utf-8"))
    return encrypted_bytes.decode("utf-8")


def decrypt_credential(cipher_text: str) -> str:
    """Decrypts a Fernet AES-256 encrypted credential string."""
    if not cipher_text:
        return ""
    try:
        fernet = _get_fernet()
        decrypted_bytes = fernet.decrypt(cipher_text.encode("utf-8"))
        return decrypted_bytes.decode("utf-8")
    except Exception as e:
        logger.error("Credential decryption failed: %s", e)
        return ""


# ==============================================================================
# 3. JWT Token Encoding & Decoding (HS256)
# ==============================================================================

def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")


def _b64url_decode(data_str: str) -> bytes:
    padding = 4 - (len(data_str) % 4)
    if padding != 4:
        data_str += "=" * padding
    return base64.urlsafe_b64decode(data_str)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Creates a signed HS256 JWT access token."""
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp())
    })

    header = {"alg": settings.JWT_ALGORITHM, "typ": "JWT"}
    header_json = json.dumps(header, separators=(",", ":")).encode("utf-8")
    payload_json = json.dumps(to_encode, separators=(",", ":"), default=str).encode("utf-8")

    header_b64 = _b64url_encode(header_json)
    payload_b64 = _b64url_encode(payload_json)

    signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
    signature = hmac.new(
        settings.JWT_SECRET_KEY.encode("utf-8"),
        signing_input,
        hashlib.sha256
    ).digest()
    signature_b64 = _b64url_encode(signature)

    return f"{header_b64}.{payload_b64}.{signature_b64}"


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Validates signature and expiration, returning decoded JWT payload."""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None

        header_b64, payload_b64, signature_b64 = parts
        signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
        expected_sig = hmac.new(
            settings.JWT_SECRET_KEY.encode("utf-8"),
            signing_input,
            hashlib.sha256
        ).digest()
        expected_sig_b64 = _b64url_encode(expected_sig)

        if not hmac.compare_digest(signature_b64, expected_sig_b64):
            logger.warning("JWT signature verification failed")
            return None

        payload_bytes = _b64url_decode(payload_b64)
        payload = json.loads(payload_bytes.decode("utf-8"))

        # Check expiration
        exp = payload.get("exp")
        if exp and int(time.time()) > int(exp):
            logger.warning("JWT token expired")
            return None

        return payload
    except Exception as e:
        logger.warning("JWT decode error: %s", e)
        return None


# ==============================================================================
# 4. Google IAM / OAuth 2.0 ID Token Verification
# ==============================================================================

def verify_google_id_token(id_token_str: str) -> Dict[str, Any]:
    """
    Verifies a Google ID Token issued by Google Identity Services / IAM.
    Returns the parsed user claims (email, sub, name, picture).
    """
    if not id_token_str:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google ID token cannot be empty"
        )


    try:
        from google.oauth2 import id_token
        from google.auth.transport import requests as google_requests

        request = google_requests.Request()
        client_id = settings.GOOGLE_CLIENT_ID or None
        
        # Verify token with Google's public keys
        id_info = id_token.verify_oauth2_token(id_token_str, request, client_id)
        
        # Verify issuer
        if id_info.get("iss") not in ["accounts.google.com", "https://accounts.google.com"]:
            raise ValueError("Wrong issuer in Google ID token")

        return id_info
    except ImportError:
        logger.error("google-auth package is missing")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google Auth provider not installed on server"
        )
    except Exception as e:
        logger.error("Google ID Token verification failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid Google ID Token: {str(e)}"
        )



# ==============================================================================
# 5. FastAPI Current User Dependencies
# ==============================================================================

def get_current_user(
    auth: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    token: Optional[str] = Query(None, description="Optional JWT bearer token for SSE EventSource streams")
) -> User:
    """
    Strict FastAPI dependency enforcing Authorization: Bearer <token> or ?token=<token> for SSE.
    Returns the authenticated User from PostgreSQL or raises HTTP 401.
    """
    raw_token = auth.credentials if (auth and auth.credentials) else token
    if not raw_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(raw_token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload structure",
            headers={"WWW-Authenticate": "Bearer"},
        )

    with get_db_session() as db:
        stmt = select(User).where(User.id == user_id)
        user = db.execute(stmt).scalar_one_or_none()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive",
            )
        # Ensure scalar attributes are populated
        _ = (user.id, user.email, user.full_name, user.tier, user.is_active, user.created_at)
        db.expunge(user)
        return user


def get_user_enctoken(user_id: str) -> Optional[str]:
    """Retrieves and decrypts the stored broker enctoken for a given user_id."""
    if not user_id:
        return None
    try:
        from src.models.session import UserSession
        with get_db_session() as db:
            stmt = select(UserSession).where(UserSession.user_id == user_id)
            session_rec = db.execute(stmt).scalar_one_or_none()
            if session_rec and session_rec.enctoken_encrypted:
                return decrypt_credential(session_rec.enctoken_encrypted)
    except Exception as e:
        logger.error("Error retrieving user enctoken: %s", e)
    return None

