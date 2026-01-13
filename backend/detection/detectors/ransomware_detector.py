"""Ransomware detector."""

from typing import Dict, Any, Optional
import re

from backend.detection.detectors.base import BaseDetector
from backend.common.logging import get_logger

logger = get_logger(__name__)


class RansomwareDetector(BaseDetector):
    """Detector for ransomware activity."""
    
    # Ransomware indicators
    RANSOMWARE_PATTERNS = [
        # File encryption
        r"(?i)(encrypt|encryption).*(file|document|data)",
        r"(?i)(\.encrypted|\.locked|\.crypto)",
        
        # Ransom notes
        r"(?i)(ransom|ransomware|decrypt|payment|bitcoin)",
        r"(?i)(readme\.txt|decrypt.*instructions)",
        
        # Suspicious file operations
        r"(?i)(mass.?delete|bulk.?rename|file.?modification)",
        r"(?i)(shadow.?copy|volume.?shadow)",
    ]
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize ransomware detector."""
        super().__init__("ransomware", config)
        self.patterns = [re.compile(pattern) for pattern in self.RANSOMWARE_PATTERNS]
    
    async def detect(self, log_entry: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Detect ransomware activity."""
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
                logger.critical(
                    f"Ransomware detected: {len(matches)} indicators matched"
                )
                
                return {
                    "attack_type": "ransomware",
                    "detector": self.name,
                    "indicators": matches,
                    "match_count": len(matches),
                    "severity": "critical",
                    "confidence": min(1.0, len(matches) / 2.0),
                }
            
            # Check ML prediction
            ml_prediction = log_entry.get("ml_prediction", {})
            if ml_prediction.get("attack_type") == "ransomware":
                confidence = ml_prediction.get("confidence", 0.0)
                if confidence > 0.6:
                    return {
                        "attack_type": "ransomware",
                        "detector": self.name,
                        "ml_detected": True,
                        "confidence": confidence,
                        "severity": "critical",
                    }
            
            return None
        
        except Exception as e:
            logger.error(f"Error in ransomware detection: {e}", exc_info=True)
            return None
