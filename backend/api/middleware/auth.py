"""Authentication middleware."""

from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from typing import Optional

from backend.common.config import settings
from backend.common.audit import audit_logger, AuditAction
from backend.common.logging import get_logger

logger = get_logger(__name__)

security = HTTPBearer()


async def verify_token(credentials: HTTPAuthorizationCredentials) -> dict:
    """
    Verify JWT token.
    
    Args:
        credentials: Authorization credentials
    
    Returns:
        Token payload
    """
    try:
        token = credentials.credentials
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(request: Request) -> Optional[dict]:
    """
    Get current user from request.
    
    Args:
        request: FastAPI request
    
    Returns:
        User information or None
    """
    try:
        authorization = request.headers.get("Authorization")
        if not authorization:
            return None
        
        token = authorization.replace("Bearer ", "")
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except Exception:
        return None


async def require_auth(request: Request) -> dict:
    """
    Require authentication for endpoint.
    
    Args:
        request: FastAPI request
    
    Returns:
        User information
    
    Raises:
        HTTPException: If not authenticated
    """
    user = await get_current_user(request)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user
