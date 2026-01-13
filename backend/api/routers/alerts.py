"""Alerts API endpoints."""

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

from backend.alerting.notification_service import notification_service
from backend.alerting.alert_manager import AlertManager
from backend.common.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)


class AlertRequest(BaseModel):
    """Alert request model."""
    title: str
    message: str
    severity: str = "medium"
    source: str = "api"
    metadata: Optional[Dict[str, Any]] = None
    channels: Optional[List[str]] = None


@router.post("/alerts", status_code=status.HTTP_201_CREATED)
async def create_alert(request: AlertRequest) -> Dict[str, Any]:
    """Create and send alert."""
    try:
        result = await notification_service.send_alert(
            title=request.title,
            message=request.message,
            severity=request.severity,
            source=request.source,
            metadata=request.metadata,
            channels=request.channels
        )
        
        return result
    
    except Exception as e:
        logger.error(f"Error creating alert: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating alert: {str(e)}"
        )


@router.get("/alerts", status_code=status.HTTP_200_OK)
async def get_alerts(
    severity: Optional[str] = None,
    source: Optional[str] = None,
    status: Optional[str] = None
) -> Dict[str, Any]:
    """Get alerts."""
    try:
        alerts = notification_service.alert_manager.get_alerts(
            severity=severity,
            source=source,
            status=status
        )
        
        return {
            "alerts": [alert.to_dict() for alert in alerts],
            "count": len(alerts),
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving alerts: {str(e)}"
        )


@router.post("/alerts/{alert_id}/resolve", status_code=status.HTTP_200_OK)
async def resolve_alert(alert_id: str) -> Dict[str, Any]:
    """Mark alert as resolved."""
    try:
        notification_service.alert_manager.mark_resolved(alert_id)
        return {"success": True, "alert_id": alert_id}
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error resolving alert: {str(e)}"
        )
