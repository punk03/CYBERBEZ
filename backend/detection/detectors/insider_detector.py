"""Insider threat detector."""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict

from backend.detection.detectors.base import BaseDetector
from backend.common.logging import get_logger

logger = get_logger(__name__)


class InsiderThreatDetector(BaseDetector):
    """Detector for insider threats."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize insider threat detector."""
        super().__init__("insider_threat", config)
        
        # Tracking user activity
        self.user_activity: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.suspicious_patterns: Dict[str, int] = defaultdict(int)
        
        # Thresholds
        self.unusual_hours_threshold = config.get("unusual_hours_threshold", 3) if config else 3
        self.failed_access_threshold = config.get("failed_access_threshold", 5) if config else 5
    
    def _extract_user(self, log_entry: Dict[str, Any]) -> Optional[str]:
        """Extract user from log entry."""
        user_fields = ["user", "username", "user_id", "account"]
        for field in user_fields:
            if field in log_entry:
                return str(log_entry[field])
        return None
    
    def _is_unusual_hours(self, log_entry: Dict[str, Any]) -> bool:
        """Check if activity is during unusual hours."""
        try:
            timestamp = log_entry.get("timestamp", datetime.utcnow().isoformat())
            if isinstance(timestamp, str):
                dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            else:
                dt = timestamp
            
            hour = dt.hour
            # Unusual hours: 22:00 - 06:00
            return hour >= 22 or hour < 6
        except Exception:
            return False
    
    async def detect(self, log_entry: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Detect insider threat."""
        if not self.enabled:
            return None
        
        try:
            user = self._extract_user(log_entry)
            if not user:
                return None
            
            # Track activity
            self.user_activity[user].append({
                "timestamp": log_entry.get("timestamp"),
                "action": log_entry.get("message", ""),
                "level": log_entry.get("level", "INFO"),
            })
            
            # Check for suspicious patterns
            indicators = []
            
            # Unusual hours
            if self._is_unusual_hours(log_entry):
                self.suspicious_patterns[f"{user}_unusual_hours"] += 1
                if self.suspicious_patterns[f"{user}_unusual_hours"] >= self.unusual_hours_threshold:
                    indicators.append("unusual_hours")
            
            # Failed access attempts
            if "failed" in log_entry.get("message", "").lower() or log_entry.get("level") == "ERROR":
                self.suspicious_patterns[f"{user}_failed"] += 1
                if self.suspicious_patterns[f"{user}_failed"] >= self.failed_access_threshold:
                    indicators.append("multiple_failed_access")
            
            # Privilege escalation
            if "sudo" in log_entry.get("message", "").lower() or "admin" in log_entry.get("message", "").lower():
                indicators.append("privilege_escalation")
            
            # Data exfiltration patterns
            if any(keyword in log_entry.get("message", "").lower() for keyword in ["download", "export", "copy", "transfer"]):
                indicators.append("data_access")
            
            if indicators:
                logger.warning(
                    f"Insider threat detected for user {user}: {indicators}"
                )
                
                return {
                    "attack_type": "insider_threat",
                    "detector": self.name,
                    "user": user,
                    "indicators": indicators,
                    "severity": "high",
                    "confidence": min(1.0, len(indicators) / 3.0),
                }
            
            # Check ML prediction
            ml_prediction = log_entry.get("ml_prediction", {})
            if ml_prediction.get("attack_type") == "insider_threat":
                confidence = ml_prediction.get("confidence", 0.0)
                if confidence > 0.7:
                    return {
                        "attack_type": "insider_threat",
                        "detector": self.name,
                        "user": user,
                        "ml_detected": True,
                        "confidence": confidence,
                        "severity": "high",
                    }
            
            return None
        
        except Exception as e:
            logger.error(f"Error in insider threat detection: {e}", exc_info=True)
            return None
