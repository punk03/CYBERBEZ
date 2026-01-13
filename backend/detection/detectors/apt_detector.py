"""APT (Advanced Persistent Threat) detector."""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict

from backend.detection.detectors.base import BaseDetector
from backend.common.logging import get_logger

logger = get_logger(__name__)


class APTDetector(BaseDetector):
    """Detector for Advanced Persistent Threats."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize APT detector."""
        super().__init__("apt", config)
        
        # Track long-term patterns
        self.activity_timeline: Dict[str, List[datetime]] = defaultdict(list)
        self.command_history: Dict[str, list] = defaultdict(list)
        
        # Thresholds
        self.timeline_days = config.get("timeline_days", 30) if config else 30
        self.min_activities = config.get("min_activities", 10) if config else 10
    
    async def detect(self, log_entry: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Detect APT activity."""
        if not self.enabled:
            return None
        
        try:
            source_ip = log_entry.get("src_ip") or log_entry.get("ip")
            if not source_ip:
                return None
            
            # Track activity timeline
            now = datetime.utcnow()
            self.activity_timeline[source_ip].append(now)
            
            # Clean old activities
            cutoff = now - timedelta(days=self.timeline_days)
            self.activity_timeline[source_ip] = [
                ts for ts in self.activity_timeline[source_ip] if ts > cutoff
            ]
            
            # Check for persistent activity
            activity_count = len(self.activity_timeline[source_ip])
            
            if activity_count >= self.min_activities:
                # Check for stealth patterns
                indicators = []
                
                # Low and slow activity
                if activity_count > 0:
                    time_span = (now - self.activity_timeline[source_ip][0]).days
                    if time_span > 7 and activity_count / time_span < 2:  # Less than 2 activities per day
                        indicators.append("low_and_slow")
                
                # Check ML prediction for APT
                ml_prediction = log_entry.get("ml_prediction", {})
                if ml_prediction.get("attack_type") == "apt":
                    indicators.append("ml_detected")
                
                if indicators:
                    logger.warning(
                        f"APT activity detected from {source_ip}: {indicators}"
                    )
                    
                    return {
                        "attack_type": "apt",
                        "detector": self.name,
                        "source_ip": source_ip,
                        "indicators": indicators,
                        "activity_count": activity_count,
                        "timeline_days": time_span if activity_count > 0 else 0,
                        "severity": "critical",
                        "confidence": min(1.0, activity_count / (self.min_activities * 2)),
                    }
            
            return None
        
        except Exception as e:
            logger.error(f"Error in APT detection: {e}", exc_info=True)
            return None
