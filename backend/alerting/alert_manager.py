"""Alert manager for handling alerts and notifications."""

from typing import Dict, Any, List, Optional, Set
from datetime import datetime, timedelta
from collections import defaultdict
import uuid

from backend.common.logging import get_logger

logger = get_logger(__name__)


class Alert:
    """Alert representation."""
    
    def __init__(
        self,
        alert_id: str,
        title: str,
        message: str,
        severity: str,
        source: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Initialize alert."""
        self.alert_id = alert_id
        self.title = title
        self.message = message
        self.severity = severity
        self.source = source
        self.metadata = metadata or {}
        self.created_at = datetime.utcnow()
        self.sent_channels: Set[str] = set()
        self.status = "pending"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert alert to dictionary."""
        return {
            "alert_id": self.alert_id,
            "title": self.title,
            "message": self.message,
            "severity": self.severity,
            "source": self.source,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "sent_channels": list(self.sent_channels),
            "status": self.status,
        }


class AlertManager:
    """Manager for alerts and notifications."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize alert manager."""
        self.config = config or {}
        self.alerts: Dict[str, Alert] = {}
        self.alert_groups: Dict[str, List[str]] = defaultdict(list)
        
        # Deduplication window (seconds)
        self.dedup_window = config.get("dedup_window", 300) if config else 300
        
        # Alert history
        self.alert_history: List[Alert] = []
        self.max_history = config.get("max_history", 1000) if config else 1000
    
    def create_alert(
        self,
        title: str,
        message: str,
        severity: str = "medium",
        source: str = "system",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Alert:
        """
        Create a new alert.
        
        Args:
            title: Alert title
            message: Alert message
            severity: Alert severity (low, medium, high, critical)
            source: Alert source
            metadata: Additional metadata
        
        Returns:
            Created alert
        """
        alert_id = str(uuid.uuid4())
        alert = Alert(
            alert_id=alert_id,
            title=title,
            message=message,
            severity=severity,
            source=source,
            metadata=metadata
        )
        
        self.alerts[alert_id] = alert
        
        # Add to history
        self.alert_history.append(alert)
        if len(self.alert_history) > self.max_history:
            self.alert_history.pop(0)
        
        logger.info(f"Alert created: {title} (severity: {severity})")
        
        return alert
    
    def get_alert(self, alert_id: str) -> Optional[Alert]:
        """Get alert by ID."""
        return self.alerts.get(alert_id)
    
    def get_alerts(
        self,
        severity: Optional[str] = None,
        source: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Alert]:
        """Get alerts with filters."""
        alerts = list(self.alerts.values())
        
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        
        if source:
            alerts = [a for a in alerts if a.source == source]
        
        if status:
            alerts = [a for a in alerts if a.status == status]
        
        return sorted(alerts, key=lambda x: x.created_at, reverse=True)
    
    def mark_sent(self, alert_id: str, channel: str) -> None:
        """Mark alert as sent to a channel."""
        alert = self.alerts.get(alert_id)
        if alert:
            alert.sent_channels.add(channel)
            alert.status = "sent"
    
    def mark_resolved(self, alert_id: str) -> None:
        """Mark alert as resolved."""
        alert = self.alerts.get(alert_id)
        if alert:
            alert.status = "resolved"
            logger.info(f"Alert {alert_id} marked as resolved")
    
    def group_alerts(self, group_key: str, alert_ids: List[str]) -> None:
        """Group alerts together."""
        self.alert_groups[group_key] = alert_ids
    
    def is_duplicate(self, title: str, message: str, window_seconds: Optional[int] = None) -> bool:
        """
        Check if alert is duplicate within time window.
        
        Args:
            title: Alert title
            message: Alert message
            window_seconds: Time window in seconds
        
        Returns:
            True if duplicate found
        """
        window = window_seconds or self.dedup_window
        cutoff = datetime.utcnow() - timedelta(seconds=window)
        
        for alert in reversed(self.alert_history):
            if alert.created_at < cutoff:
                break
            
            if alert.title == title and alert.message == message:
                return True
        
        return False
