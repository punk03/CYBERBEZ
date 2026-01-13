"""Audit logging for security compliance."""

from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum

from backend.storage.mongodb import get_mongodb_database
from backend.common.logging import get_logger

logger = get_logger(__name__)


class AuditAction(Enum):
    """Audit action types."""
    LOGIN = "login"
    LOGOUT = "logout"
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    READ = "read"
    EXECUTE = "execute"
    APPROVE = "approve"
    REJECT = "reject"
    CONFIG_CHANGE = "config_change"
    AUTOMATION_TRIGGERED = "automation_triggered"
    ISOLATION_APPLIED = "isolation_applied"
    FAILOVER_ACTIVATED = "failover_activated"


class AuditLogger:
    """Audit logger for compliance."""
    
    def __init__(self):
        """Initialize audit logger."""
        pass
    
    async def log(
        self,
        action: AuditAction,
        user: str,
        resource: str,
        details: Optional[Dict[str, Any]] = None,
        success: bool = True,
        ip_address: Optional[str] = None
    ) -> None:
        """
        Log audit event.
        
        Args:
            action: Action type
            user: User who performed the action
            resource: Resource affected
            details: Additional details
            success: Whether action was successful
            ip_address: IP address of user
        """
        try:
            audit_entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "action": action.value,
                "user": user,
                "resource": resource,
                "details": details or {},
                "success": success,
                "ip_address": ip_address,
            }
            
            # Save to MongoDB audit collection
            db = await get_mongodb_database()
            await db.audit_logs.insert_one(audit_entry)
            
            logger.info(
                f"Audit: {action.value} by {user} on {resource} "
                f"(success: {success})"
            )
        
        except Exception as e:
            logger.error(f"Error logging audit event: {e}", exc_info=True)
    
    async def get_audit_logs(
        self,
        user: Optional[str] = None,
        action: Optional[str] = None,
        resource: Optional[str] = None,
        limit: int = 100
    ) -> list:
        """
        Get audit logs with filters.
        
        Args:
            user: Filter by user
            action: Filter by action
            resource: Filter by resource
            limit: Maximum number of logs
        
        Returns:
            List of audit logs
        """
        try:
            db = await get_mongodb_database()
            query = {}
            
            if user:
                query["user"] = user
            if action:
                query["action"] = action
            if resource:
                query["resource"] = resource
            
            cursor = db.audit_logs.find(query).sort("timestamp", -1).limit(limit)
            logs = await cursor.to_list(length=limit)
            
            # Convert ObjectId to string
            for log in logs:
                log["_id"] = str(log["_id"])
            
            return logs
        
        except Exception as e:
            logger.error(f"Error retrieving audit logs: {e}", exc_info=True)
            return []


# Global audit logger instance
audit_logger = AuditLogger()
