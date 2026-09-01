from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, Dict, Any
from src.services.zerodha_client import zerodha_service

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])

class CallbackPayload(BaseModel):
    request_token: str
    status: Optional[str] = "success"

@router.get("/login-url")
def get_login_url():
    """Generates the Zerodha Kite OAuth login URL."""
    url = zerodha_service.get_login_url()
    return {"status": "success", "login_url": url}

@router.get("/demo-login")
def demo_login():
    """Provides a quick demo login route for local evaluation."""
    session = zerodha_service.generate_session(request_token="demo_request_token")
    return {"status": "success", "message": "Logged in as Demo Investor", "session": session}

@router.post("/callback")
def auth_callback(payload: CallbackPayload):
    """Callback endpoint to receive request_token from Zerodha redirect."""
    try:
        session_data = zerodha_service.generate_session(payload.request_token)
        return {"status": "success", "data": session_data}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
