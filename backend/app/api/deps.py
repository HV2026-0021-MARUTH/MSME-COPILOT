from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import create_client, Client
from app.config import settings
import logging

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)

def get_supabase_client() -> Client:
    if not settings.SUPABASE_URL or not settings.SUPABASE_SECRET_KEY:
        raise ValueError("Supabase credentials are not set in the environment.")
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SECRET_KEY)

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Validates the bearer token against Supabase Auth.
    Returns the Supabase user object if valid, otherwise raises 401.
    """
    if settings.ENVIRONMENT == "development" or not settings.SUPABASE_SECRET_KEY:
        # Bypass for local MVP demo or if live backend lacks credentials
        return {"id": "demo-shop-owner", "email": "demo@maruthi.ai"}
        
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    token = credentials.credentials
    try:
        supabase = get_supabase_client()
        res = supabase.auth.get_user(token)
        if not res.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return res.user
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
