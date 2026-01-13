"""Webhook notification channel."""

from typing import Dict, Any, Optional, List
import httpx

from backend.common.logging import get_logger

logger = get_logger(__name__)


class WebhookChannel:
    """Webhook notification channel."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize webhook channel."""
        self.config = config or {}
        self.enabled = config.get("enabled", False) if config else False
        self.webhook_urls = config.get("webhook_urls", []) if config else []
        self.timeout = config.get("timeout", 10) if config else 10
    
    async def send(
        self,
        payload: Dict[str, Any],
        headers: Optional[Dict[str, str]] = None
    ) -> bool:
        """
        Send webhook notification.
        
        Args:
            payload: Payload to send
            headers: Optional headers
        
        Returns:
            True if sent successfully
        """
        if not self.enabled or not self.webhook_urls:
            logger.debug("Webhook channel disabled or not configured")
            return False
        
        success_count = 0
        
        for url in self.webhook_urls:
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        url,
                        json=payload,
                        headers=headers or {}
                    )
                    response.raise_for_status()
                    success_count += 1
                    logger.debug(f"Webhook sent to {url}")
            
            except Exception as e:
                logger.error(f"Error sending webhook to {url}: {e}", exc_info=True)
        
        return success_count > 0
    
    async def send_alert(self, alert: Dict[str, Any]) -> bool:
        """Send alert as webhook."""
        payload = {
            "event_type": "alert",
            "alert": alert,
            "timestamp": alert.get("created_at"),
        }
        
        return await self.send(payload)
