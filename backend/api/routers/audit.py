"""Audit logs API endpoints."""

from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import Optional

from backend.common.audit import audit_logger
from backend.api.middleware.auth import require_auth
from backend.common.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.get("/audit", status_code=status.HTTP_200_OK)
async def get_audit_logs(
    user: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    resource: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    current_user: dict = Depends(require_auth)
) -> dict:
    """
    Get audit logs.
    
    Requires authentication.
    """
    try:
        logs = await audit_logger.get_audit_logs(
            user=user,
            action=action,
            resource=resource,
            limit=limit
        )
        
        return {
            "logs": logs,
            "count": len(logs),
        }
    
    except Exception as e:
        logger.error(f"Error retrieving audit logs: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving audit logs: {str(e)}"
        )
