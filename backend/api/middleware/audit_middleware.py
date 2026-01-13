"""Audit middleware for logging API requests."""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable

from backend.common.audit import audit_logger, AuditAction
from backend.common.logging import get_logger

logger = get_logger(__name__)


class AuditMiddleware(BaseHTTPMiddleware):
    """Middleware for auditing API requests."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and log audit event."""
        # Get user from request (if authenticated)
        user = "anonymous"
        if hasattr(request.state, "user"):
            user = request.state.user.get("sub", "anonymous")
        
        # Get IP address
        ip_address = request.client.host if request.client else None
        
        # Determine action type from method
        method = request.method
        action_map = {
            "GET": AuditAction.READ,
            "POST": AuditAction.CREATE,
            "PUT": AuditAction.UPDATE,
            "PATCH": AuditAction.UPDATE,
            "DELETE": AuditAction.DELETE,
        }
        action = action_map.get(method, AuditAction.EXECUTE)
        
        # Execute request
        try:
            response = await call_next(request)
            success = response.status_code < 400
            
            # Log audit event (async, don't wait)
            try:
                await audit_logger.log(
                    action=action,
                    user=user,
                    resource=request.url.path,
                    details={
                        "method": method,
                        "status_code": response.status_code,
                    },
                    success=success,
                    ip_address=ip_address
                )
            except Exception as e:
                logger.warning(f"Error logging audit event: {e}")
            
            return response
        
        except Exception as e:
            # Log failed request
            try:
                await audit_logger.log(
                    action=action,
                    user=user,
                    resource=request.url.path,
                    details={
                        "method": method,
                        "error": str(e),
                    },
                    success=False,
                    ip_address=ip_address
                )
            except Exception:
                pass
            
            raise
