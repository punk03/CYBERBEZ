"""Approval workflow for semi-automatic actions."""

from typing import Dict, Any, Optional, List
from enum import Enum
from datetime import datetime, timedelta
import uuid

from backend.common.logging import get_logger

logger = get_logger(__name__)


class ApprovalStatus(Enum):
    """Approval status."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    AUTO_APPROVED = "auto_approved"


class ApprovalWorkflow:
    """Approval workflow for critical actions."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize approval workflow."""
        self.config = config or {}
        self.auto_approve_timeout = config.get("auto_approve_timeout", 300) if config else 300  # 5 minutes
        self.require_approval = config.get("require_approval", True) if config else True
        self.pending_approvals: Dict[str, Dict[str, Any]] = {}
    
    async def request_approval(
        self,
        action: str,
        action_params: Dict[str, Any],
        reason: str,
        severity: str = "medium",
        auto_approve: bool = False
    ) -> Dict[str, Any]:
        """
        Request approval for an action.
        
        Args:
            action: Action to perform
            action_params: Parameters for the action
            reason: Reason for the action
            severity: Severity level (low, medium, high, critical)
            auto_approve: Whether to auto-approve after timeout
        
        Returns:
            Approval request result
        """
        approval_id = str(uuid.uuid4())
        
        approval_request = {
            "id": approval_id,
            "action": action,
            "action_params": action_params,
            "reason": reason,
            "severity": severity,
            "status": ApprovalStatus.PENDING.value,
            "created_at": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + timedelta(seconds=self.auto_approve_timeout)).isoformat(),
            "auto_approve": auto_approve,
        }
        
        self.pending_approvals[approval_id] = approval_request
        
        logger.info(
            f"Approval requested: {action} (ID: {approval_id}, "
            f"Severity: {severity}, Auto-approve: {auto_approve})"
        )
        
        # If critical severity and auto_approve enabled, auto-approve immediately
        if severity == "critical" and auto_approve:
            return await self.approve(approval_id, "auto_approved", "Critical threat - auto approved")
        
        return {
            "approval_id": approval_id,
            "status": "pending",
            "message": "Approval requested",
            "expires_at": approval_request["expires_at"],
        }
    
    async def approve(
        self,
        approval_id: str,
        approver: str,
        comment: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Approve an action.
        
        Args:
            approval_id: Approval request ID
            approver: Approver identifier
            comment: Optional comment
        
        Returns:
            Approval result
        """
        if approval_id not in self.pending_approvals:
            return {
                "success": False,
                "error": "Approval request not found",
            }
        
        approval = self.pending_approvals[approval_id]
        
        # Check if expired
        expires_at = datetime.fromisoformat(approval["expires_at"])
        if datetime.utcnow() > expires_at:
            approval["status"] = ApprovalStatus.EXPIRED.value
            return {
                "success": False,
                "error": "Approval request expired",
            }
        
        approval["status"] = ApprovalStatus.APPROVED.value
        approval["approved_by"] = approver
        approval["approved_at"] = datetime.utcnow().isoformat()
        approval["comment"] = comment
        
        logger.info(f"Approval {approval_id} approved by {approver}")
        
        return {
            "success": True,
            "approval_id": approval_id,
            "status": "approved",
        }
    
    async def reject(
        self,
        approval_id: str,
        rejector: str,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """Reject an action."""
        if approval_id not in self.pending_approvals:
            return {
                "success": False,
                "error": "Approval request not found",
            }
        
        approval = self.pending_approvals[approval_id]
        approval["status"] = ApprovalStatus.REJECTED.value
        approval["rejected_by"] = rejector
        approval["rejected_at"] = datetime.utcnow().isoformat()
        approval["rejection_reason"] = reason
        
        logger.info(f"Approval {approval_id} rejected by {rejector}: {reason}")
        
        return {
            "success": True,
            "approval_id": approval_id,
            "status": "rejected",
        }
    
    def get_pending_approvals(self) -> List[Dict[str, Any]]:
        """Get list of pending approvals."""
        return [
            approval for approval in self.pending_approvals.values()
            if approval["status"] == ApprovalStatus.PENDING.value
        ]
    
    def get_approval(self, approval_id: str) -> Optional[Dict[str, Any]]:
        """Get approval request by ID."""
        return self.pending_approvals.get(approval_id)
