import logging
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, Dict, Any
from src.services.zerodha_client import zerodha_service

logger = logging.getLogger("portfolio_assistant.api.auth")
router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])

class CallbackPayload(BaseModel):
    request_token: str
    status: Optional[str] = "success"

@router.get("/login-url")
def get_login_url():
    """Generates the Zerodha Kite OAuth login URL."""
    url = zerodha_service.get_login_url()
    logger.info("Login URL generated")
    return {"status": "success", "login_url": url}

@router.get("/demo-login")
def demo_login():
    """Provides a quick demo login route for local evaluation."""
    logger.info("Demo login initiated")
    session = zerodha_service.generate_session(request_token="demo_request_token")
    logger.info("Demo login successful")
    return {"status": "success", "message": "Logged in as Demo Investor", "session": session}

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
