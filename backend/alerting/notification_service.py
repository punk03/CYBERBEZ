"""Notification service for sending alerts through multiple channels."""

from typing import Dict, Any, List, Optional
import asyncio

from backend.alerting.alert_manager import AlertManager
from backend.alerting.channels.email import EmailChannel
from backend.alerting.channels.slack import SlackChannel
from backend.alerting.channels.webhook import WebhookChannel
from backend.alerting.escalation import EscalationManager
from backend.common.logging import get_logger

logger = get_logger(__name__)


class NotificationService:
    """Service for sending notifications through multiple channels."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize notification service."""
        self.config = config or {}
        
        # Initialize components
        self.alert_manager = AlertManager(config.get("alert_manager", {}))
        self.escalation_manager = EscalationManager(config.get("escalation", {}))
        
        # Initialize channels
        self.channels = {
            "email": EmailChannel(config.get("email", {})),
            "slack": SlackChannel(config.get("slack", {})),
            "webhook": WebhookChannel(config.get("webhook", {})),
        }
        
        # Recipients configuration
        self.recipients = config.get("recipients", {}) if config else {}
    
    async def send_alert(
        self,
        title: str,
        message: str,
        severity: str = "medium",
        source: str = "system",
        metadata: Optional[Dict[str, Any]] = None,
        channels: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Send alert through configured channels.
        
        Args:
            title: Alert title
            message: Alert message
            severity: Alert severity
            source: Alert source
            metadata: Additional metadata
            channels: Specific channels to use (None = all enabled)
        
        Returns:
            Send result
        """
        # Check for duplicates
        if self.alert_manager.is_duplicate(title, message):
            logger.debug(f"Duplicate alert suppressed: {title}")
            return {
                "success": False,
                "reason": "duplicate",
            }
        
        # Create alert
        alert = self.alert_manager.create_alert(
            title=title,
            message=message,
            severity=severity,
            source=source,
            metadata=metadata
        )
        
        alert_dict = alert.to_dict()
        
        # Determine channels to use
        channels_to_use = channels or list(self.channels.keys())
        
        # Send to channels
        results = {}
        for channel_name in channels_to_use:
            channel = self.channels.get(channel_name)
            if not channel:
                continue
            
            try:
                if channel_name == "email":
                    # Get email recipients for severity
                    recipients = self.recipients.get("email", {}).get(severity, [])
                    if not recipients:
                        recipients = self.recipients.get("email", {}).get("default", [])
                    
                    for recipient in recipients:
                        sent = await channel.send_alert(recipient, alert_dict)
                        if sent:
                            self.alert_manager.mark_sent(alert.alert_id, f"{channel_name}:{recipient}")
                            results[f"{channel_name}:{recipient}"] = sent
                
                elif channel_name == "slack":
                    sent = await channel.send_alert(alert_dict)
                    if sent:
                        self.alert_manager.mark_sent(alert.alert_id, channel_name)
                        results[channel_name] = sent
                
                elif channel_name == "webhook":
                    sent = await channel.send_alert(alert_dict)
                    if sent:
                        self.alert_manager.mark_sent(alert.alert_id, channel_name)
                        results[channel_name] = sent
            
            except Exception as e:
                logger.error(f"Error sending alert via {channel_name}: {e}", exc_info=True)
                results[channel_name] = False
        
        success = any(results.values())
        
        return {
            "success": success,
            "alert_id": alert.alert_id,
            "channels": results,
        }
    
    async def send_threat_alert(self, detection: Dict[str, Any]) -> Dict[str, Any]:
        """Send alert for detected threat."""
        attack_type = detection.get("attack_type", "unknown")
        severity = detection.get("severity", "medium")
        source_ip = detection.get("source_ip") or detection.get("ip", "unknown")
        
        title = f"{attack_type.upper()} Attack Detected"
        message = (
            f"Attack type: {attack_type}\n"
            f"Source IP: {source_ip}\n"
            f"Severity: {severity}\n"
            f"Confidence: {detection.get('confidence', 0):.2%}"
        )
        
        return await self.send_alert(
            title=title,
            message=message,
            severity=severity,
            source="threat_detection",
            metadata=detection
        )


# Global notification service instance
notification_service = NotificationService()
