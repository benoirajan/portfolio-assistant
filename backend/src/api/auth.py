import hashlib
import logging
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select, delete

from src.core.config import settings
from src.core.security import (
    hash_password,
    verify_password,
    encrypt_credential,
    decrypt_credential,
    create_access_token,
    verify_google_id_token,
    get_current_user,
)
from src.db.session import get_db_session
from src.models.user import User
from src.models.session import UserSession
from src.services.zerodha_client import zerodha_service

logger = logging.getLogger("portfolio_assistant.api.auth")
router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


# ==============================================================================
# Pydantic Schemas
# ==============================================================================

class RegisterPayload(BaseModel):
    email: str = Field(..., description="User email address")
    password: str = Field(..., min_length=6, description="Password (min 6 characters)")
    full_name: Optional[str] = Field(None, description="User full name")


class LoginPayload(BaseModel):
    email: str
    password: str


class GoogleAuthPayload(BaseModel):
    credential: str = Field(..., description="Google ID Token issued by Google Identity Services / IAM")


class EnctokenPayload(BaseModel):
    enctoken: str = Field(..., description="Zerodha web session enctoken")


class CallbackPayload(BaseModel):
    request_token: str
    status: Optional[str] = "success"


# ==============================================================================
# Auth Routes (Google IAM, Email/Password, Profile)
# ==============================================================================

@router.post("/google", status_code=status.HTTP_200_OK)
def google_auth(payload: GoogleAuthPayload):
    """
    Authenticates or registers a user via Google IAM / OAuth 2.0 ID Token.
    Validates token claims, provisions user in database, and returns JWT access token.
    """
    try:
        id_info = verify_google_id_token(payload.credential)
        email = id_info.get("email")
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Google token does not contain a valid email address"
            )

        full_name = id_info.get("name")

        with get_db_session() as db:
            stmt = select(User).where(User.email == email.lower().strip())
            user = db.execute(stmt).scalar_one_or_none()

            if not user:
                user = User(
                    email=email.lower().strip(),
                    full_name=full_name,
                    tier="FREE",
                    is_active=True,
                )
                db.add(user)
                db.flush()
                logger.info("New user registered via Google IAM: %s (id=%s)", email, user.id)
            else:
                if full_name and not user.full_name:
                    user.full_name = full_name
                logger.info("User logged in via Google IAM: %s (id=%s)", email, user.id)

            access_token = create_access_token(
                data={"sub": user.id, "email": user.email, "tier": user.tier}
            )

            return {
                "status": "success",
                "access_token": access_token,
                "token_type": "bearer",
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "full_name": user.full_name,
                    "tier": user.tier,
                },
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Google auth failed: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Google authentication failed: {str(e)}"
        )


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(payload: RegisterPayload):
    """Registers a new user account with email and hashed password."""
    clean_email = payload.email.lower().strip()
    if not clean_email or "@" not in clean_email:
        raise HTTPException(status_code=400, detail="Invalid email address format")

    with get_db_session() as db:
        stmt = select(User).where(User.email == clean_email)
        existing = db.execute(stmt).scalar_one_or_none()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="An account with this email already exists"
            )

        hashed = hash_password(payload.password)
        user = User(
            email=clean_email,
            hashed_password=hashed,
            full_name=payload.full_name.strip() if payload.full_name else None,
            tier="FREE",
            is_active=True,
        )
        db.add(user)
        db.flush()

        logger.info("User registered successfully: %s (id=%s)", clean_email, user.id)

        access_token = create_access_token(
            data={"sub": user.id, "email": user.email, "tier": user.tier}
        )

        return {
            "status": "success",
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "tier": user.tier,
            },
        }


@router.post("/login")
def login(payload: LoginPayload):
    """Authenticates an existing user and returns a JWT access token."""
    clean_email = payload.email.lower().strip()

    with get_db_session() as db:
        stmt = select(User).where(User.email == clean_email)
        user = db.execute(stmt).scalar_one_or_none()

        if not user or not user.hashed_password:
            logger.warning("Login failed for email: %s (user not found or uses social login)", clean_email)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not verify_password(payload.password, user.hashed_password):
            logger.warning("Invalid password attempt for email: %s", clean_email)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account has been deactivated"
            )

        logger.info("User authenticated: %s (id=%s)", clean_email, user.id)

        access_token = create_access_token(
            data={"sub": user.id, "email": user.email, "tier": user.tier}
        )

        return {
            "status": "success",
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "tier": user.tier,
            },
        }


@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    """Returns profile and broker connection state for the authenticated user."""
    with get_db_session() as db:
        stmt = select(UserSession).where(UserSession.user_id == current_user.id)
        session_record = db.execute(stmt).scalar_one_or_none()
        has_enctoken = bool(session_record and session_record.enctoken_encrypted)

        return {
            "status": "success",
            "user": {
                "id": current_user.id,
                "email": current_user.email,
                "full_name": current_user.full_name,
                "tier": current_user.tier,
                "is_active": current_user.is_active,
                "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
            },
            "broker_status": {
                "has_enctoken": has_enctoken,
                "broker": "ZERODHA" if has_enctoken else None,
            },
        }


# ==============================================================================
# Encrypted Broker Credential Management
# ==============================================================================

@router.post("/broker/enctoken")
def save_broker_enctoken(
    payload: EnctokenPayload,
    current_user: User = Depends(get_current_user)
):
    """Securely encrypts and stores the user's Zerodha enctoken at rest."""
    raw_token = payload.enctoken
    clean_token = zerodha_service.sanitize_token(raw_token)
    if not clean_token:
        raise HTTPException(status_code=400, detail="Enctoken cannot be empty")

    token_hash = hashlib.sha256(clean_token.encode()).hexdigest()[:16]
    encrypted_token = encrypt_credential(clean_token)

    with get_db_session() as db:
        stmt = select(UserSession).where(UserSession.user_id == current_user.id)
        session_record = db.execute(stmt).scalar_one_or_none()

        if not session_record:
            session_record = UserSession(
                user_id=current_user.id,
                token_hash=token_hash,
                enctoken_encrypted=encrypted_token,
            )
            db.add(session_record)
        else:
            session_record.token_hash = token_hash
            session_record.enctoken_encrypted = encrypted_token

    logger.info("Encrypted broker enctoken saved for user %s", current_user.id)
    return {
        "status": "success",
        "message": "Broker session connected and encrypted",
        "has_enctoken": True,
    }


@router.get("/broker/status")
def get_broker_status(current_user: User = Depends(get_current_user)):
    """Checks whether the authenticated user has an active encrypted enctoken."""
    with get_db_session() as db:
        stmt = select(UserSession).where(UserSession.user_id == current_user.id)
        session_record = db.execute(stmt).scalar_one_or_none()
        has_enctoken = bool(session_record and session_record.enctoken_encrypted)
        return {
            "status": "success",
            "has_enctoken": has_enctoken,
            "broker": "ZERODHA" if has_enctoken else None,
        }


@router.delete("/broker/disconnect")
def disconnect_broker(current_user: User = Depends(get_current_user)):
    """Deletes stored broker session credentials for the authenticated user."""
    with get_db_session() as db:
        stmt = delete(UserSession).where(UserSession.user_id == current_user.id)
        db.execute(stmt)

    logger.info("Broker disconnected for user %s", current_user.id)
    return {"status": "success", "message": "Broker session disconnected"}


# ==============================================================================
# Zerodha Kite OAuth Routes
# ==============================================================================

@router.get("/login-url")
def get_login_url():
    """Generates the Zerodha Kite OAuth login URL."""
    url = zerodha_service.get_login_url()
    logger.info("Login URL generated")
    return {"status": "success", "login_url": url}


@router.post("/callback")
def auth_callback(payload: CallbackPayload):
    """Callback endpoint to receive request_token from Zerodha redirect."""
    try:
        logger.info("OAuth callback received — exchanging request_token")
        session_data = zerodha_service.generate_session(payload.request_token)
        logger.info("OAuth session established successfully")
        return {"status": "success", "data": session_data}
    except Exception as e:
        logger.error("OAuth callback failed: %s", e, exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))
