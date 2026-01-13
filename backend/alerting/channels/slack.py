"""Slack notification channel."""

from typing import Dict, Any, Optional
import httpx

from backend.common.logging import get_logger

logger = get_logger(__name__)


class SlackChannel:
    """Slack notification channel."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize Slack channel."""
        self.config = config or {}
        self.enabled = config.get("enabled", False) if config else False
        self.webhook_url = config.get("webhook_url", "") if config else ""
        self.channel = config.get("channel", "#alerts") if config else "#alerts"
        self.username = config.get("username", "PROKVANT") if config else "PROKVANT"
    
    async def send(
        self,
        message: str,
        severity: str = "medium",
        attachments: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        """
        Send Slack notification.
        
        Args:
            message: Message text
            severity: Alert severity
            attachments: Slack attachments (optional)
        
        Returns:
            True if sent successfully
        """
        if not self.enabled or not self.webhook_url:
            logger.debug("Slack channel disabled or not configured")
            return False
        
        try:
            # Color mapping for severity
            color_map = {
                "low": "#36a64f",      # Green
                "medium": "#ffaa00",   # Orange
                "high": "#ff0000",     # Red
                "critical": "#8b0000", # Dark red
            }
            
            payload = {
                "channel": self.channel,
                "username": self.username,
                "text": message,
                "attachments": attachments or [],
            }
            
            # Add color if severity provided
            if severity in color_map:
                if not payload["attachments"]:
                    payload["attachments"] = [{}]
                payload["attachments"][0]["color"] = color_map[severity]
            
            async with httpx.AsyncClient() as client:
                response = await client.post(self.webhook_url, json=payload)
                response.raise_for_status()
            
            logger.info(f"Slack notification sent to {self.channel}")
            return True
        
        except Exception as e:
            logger.error(f"Error sending Slack notification: {e}", exc_info=True)
            return False
    
    async def send_alert(self, alert: Dict[str, Any]) -> bool:
        """Send alert as Slack message."""
        message = f"*{alert.get('title')}*\n{alert.get('message')}"
        
        attachments = [{
            "fields": [
                {"title": "Severity", "value": alert.get("severity", "medium"), "short": True},
                {"title": "Source", "value": alert.get("source", "unknown"), "short": True},
                {"title": "Time", "value": alert.get("created_at", ""), "short": False},
            ]
        }]
        
        return await self.send(
            message=message,
            severity=alert.get("severity", "medium"),
            attachments=attachments
        )
