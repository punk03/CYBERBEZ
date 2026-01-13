"""DDoS attack detector."""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict

from backend.detection.detectors.base import BaseDetector
from backend.common.logging import get_logger

logger = get_logger(__name__)


class DDoSDetector(BaseDetector):
    """Detector for DDoS attacks."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize DDoS detector."""
        super().__init__("ddos", config)
        
        # Thresholds
        self.requests_per_second_threshold = config.get("rps_threshold", 100) if config else 100
        self.requests_per_minute_threshold = config.get("rpm_threshold", 5000) if config else 5000
        self.window_seconds = config.get("window_seconds", 60) if config else 60
        
        # Tracking
        self.request_counts: Dict[str, List[datetime]] = defaultdict(list)
    
    def _extract_source_ip(self, log_entry: Dict[str, Any]) -> Optional[str]:
        """Extract source IP from log entry."""
        ip_fields = ["src_ip", "ip", "ip_address", "client_ip", "remote_addr"]
        for field in ip_fields:
            if field in log_entry:
                return str(log_entry[field])
        return None
    
    async def detect(self, log_entry: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Detect DDoS attack."""
        if not self.enabled:
            return None
        
        try:
            source_ip = self._extract_source_ip(log_entry)
            if not source_ip:
                return None
            
            # Add request timestamp
            now = datetime.utcnow()
            self.request_counts[source_ip].append(now)
            
            # Clean old requests (outside window)
            cutoff = now - timedelta(seconds=self.window_seconds)
            self.request_counts[source_ip] = [
                ts for ts in self.request_counts[source_ip] if ts > cutoff
            ]
            
            # Check thresholds
            request_count = len(self.request_counts[source_ip])
            requests_per_second = request_count / self.window_seconds
            
            if requests_per_second > self.requests_per_second_threshold:
                logger.warning(
                    f"DDoS attack detected from {source_ip}: "
                    f"{requests_per_second:.2f} req/s (threshold: {self.requests_per_second_threshold})"
                )
                
                return {
                    "attack_type": "ddos",
                    "detector": self.name,
                    "source_ip": source_ip,
                    "requests_per_second": requests_per_second,
                    "request_count": request_count,
                    "threshold": self.requests_per_second_threshold,
                    "severity": "high",
                    "confidence": min(1.0, requests_per_second / (self.requests_per_second_threshold * 2)),
                }
            
            return None
        
        except Exception as e:
            logger.error(f"Error in DDoS detection: {e}", exc_info=True)
            return None
