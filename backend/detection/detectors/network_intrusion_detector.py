"""Network intrusion detector."""

from typing import Dict, Any, Optional
import re

from backend.detection.detectors.base import BaseDetector
from backend.common.logging import get_logger

logger = get_logger(__name__)


class NetworkIntrusionDetector(BaseDetector):
    """Detector for network intrusions."""
    
    # Intrusion patterns
    INTRUSION_PATTERNS = [
        # Port scanning
        r"(?i)(port.?scan|scanning|probe)",
        r"(?i)(connection.?refused|connection.?timeout).*\d+",
        
        # Brute force
        r"(?i)(failed.?login|authentication.?failed).*\d+",
        r"(?i)(brute.?force|password.?attack)",
        
        # Exploitation attempts
        r"(?i)(exploit|vulnerability|buffer.?overflow)",
        r"(?i)(sql.?injection|xss|cross.?site)",
        
        # Unauthorized access
        r"(?i)(unauthorized.?access|intrusion|breach)",
        r"(?i)(access.?violation|security.?breach)",
    ]
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize network intrusion detector."""
        super().__init__("network_intrusion", config)
        self.patterns = [re.compile(pattern) for pattern in self.INTRUSION_PATTERNS]
    
    async def detect(self, log_entry: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Detect network intrusion."""
        if not self.enabled:
            return None
        
        try:
            message = str(log_entry.get("message", "")).lower()
            matches = []
            
            # Check patterns
            for pattern in self.patterns:
                if pattern.search(message):
                    matches.append(pattern.pattern)
            
            if matches:
                logger.warning(
                    f"Network intrusion detected: {len(matches)} indicators matched"
                )
                
                return {
                    "attack_type": "network_intrusion",
                    "detector": self.name,
                    "indicators": matches,
                    "match_count": len(matches),
                    "severity": "high",
                    "confidence": min(1.0, len(matches) / 3.0),
                }
            
            # Check threat intel
            threat_intel = log_entry.get("threat_intel", {})
            if threat_intel.get("is_malicious") or threat_intel.get("is_suspicious"):
                return {
                    "attack_type": "network_intrusion",
                    "detector": self.name,
                    "threat_intel_detected": True,
                    "confidence": threat_intel.get("confidence", 0.0) / 100.0,
                    "severity": "high",
                }
            
            # Check ML prediction
            ml_prediction = log_entry.get("ml_prediction", {})
            if ml_prediction.get("attack_type") == "network_intrusion":
                confidence = ml_prediction.get("confidence", 0.0)
                if confidence > 0.7:
                    return {
                        "attack_type": "network_intrusion",
                        "detector": self.name,
                        "ml_detected": True,
                        "confidence": confidence,
                        "severity": "high",
                    }
            
            return None
        
        except Exception as e:
            logger.error(f"Error in network intrusion detection: {e}", exc_info=True)
            return None
