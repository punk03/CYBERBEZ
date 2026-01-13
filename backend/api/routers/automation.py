"""Automation API endpoints."""

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from typing import Dict, Any, Optional

from backend.automation.orchestrator import AutomationOrchestrator
from backend.automation.workflow.approval_workflow import ApprovalWorkflow
from backend.common.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)

# Global instances (in production, use dependency injection)
automation_orchestrator = AutomationOrchestrator()
approval_workflow = ApprovalWorkflow()


class AutomationRequest(BaseModel):
    """Automation request model."""
    detection: Dict[str, Any]
    auto_approve: Optional[bool] = False


class ApprovalRequest(BaseModel):
    """Approval request model."""
    approval_id: str
    approver: str
    comment: Optional[str] = None


@router.post("/automation/execute", status_code=status.HTTP_200_OK)
async def execute_automation(
    request: AutomationRequest
) -> Dict[str, Any]:
    """
    Execute automation for a threat.
    
    Args:
        request: Automation request
    
    Returns:
        Automation result
    """
    try:
        result = await automation_orchestrator.handle_threat(
            request.detection
        )
        
        return {
            "success": result["success"],
            "actions": result["actions"],
            "approvals": result["approvals"],
            "errors": result.get("errors", []),
        }
    
    except Exception as e:
        logger.error(f"Error executing automation: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error executing automation: {str(e)}"
        )


@router.get("/automation/approvals", status_code=status.HTTP_200_OK)
async def get_pending_approvals() -> Dict[str, Any]:
    """Get pending approval requests."""
    try:
        approvals = approval_workflow.get_pending_approvals()
        
        return {
            "approvals": approvals,
            "count": len(approvals),
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving approvals: {str(e)}"
        )


@router.post("/automation/approvals/{approval_id}/approve", status_code=status.HTTP_200_OK)
async def approve_action(
    approval_id: str,
    request: ApprovalRequest
) -> Dict[str, Any]:
    """
    Approve an automation action.
    
    Args:
        approval_id: Approval request ID
        request: Approval request
    
    Returns:
        Approval result
    """
    try:
        approval_result = await approval_workflow.approve(
            approval_id=approval_id,
            approver=request.approver,
            comment=request.comment
        )
        
        if approval_result.get("success"):
            # Execute the approved action
            execution_result = await automation_orchestrator.execute_approved_action(
                approval_id
            )
            approval_result["execution"] = execution_result
        
        return approval_result
    
    except Exception as e:
        logger.error(f"Error approving action: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error approving action: {str(e)}"
        )


@router.post("/automation/approvals/{approval_id}/reject", status_code=status.HTTP_200_OK)
async def reject_action(
    approval_id: str,
    request: ApprovalRequest
) -> Dict[str, Any]:
    """Reject an automation action."""
    try:
        rejection_result = await approval_workflow.reject(
            approval_id=approval_id,
            rejector=request.approver,
            reason=request.comment
        )
        
        return rejection_result
    
    except Exception as e:
        logger.error(f"Error rejecting action: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error rejecting action: {str(e)}"
        )


@router.get("/automation/status", status_code=status.HTTP_200_OK)
async def get_automation_status() -> Dict[str, Any]:
    """Get automation system status."""
    try:
        # Get circuit breaker statuses
        circuit_breakers = {}
        for name, cb in automation_orchestrator.circuit_breakers.items():
            circuit_breakers[name] = cb.get_status()
        
        # Get quarantine status
        quarantined_devices = automation_orchestrator.device_quarantine.get_quarantined_devices()
        
        # Get blocked traffic
        blocked_traffic = automation_orchestrator.traffic_blocking.get_blocked_traffic()
        
        return {
            "circuit_breakers": circuit_breakers,
            "quarantined_devices": len(quarantined_devices),
            "blocked_traffic": len(blocked_traffic),
            "pending_approvals": len(approval_workflow.get_pending_approvals()),
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving automation status: {str(e)}"
        )
