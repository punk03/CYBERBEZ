"""Zero-day exploit detector."""

from typing import Dict, Any, Optional

from backend.detection.detectors.base import BaseDetector
from backend.common.logging import get_logger

logger = get_logger(__name__)


class ZeroDayDetector(BaseDetector):
    """Detector for zero-day exploits (unknown attacks)."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize zero-day detector."""
        super().__init__("zero_day", config)
        self.anomaly_threshold = config.get("anomaly_threshold", 0.8) if config else 0.8
    
    async def detect(self, log_entry: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Detect zero-day exploit."""
        if not self.enabled:
            return None
        
        try:
            # Zero-day detection relies on anomaly detection
            # If ML detects anomaly but no specific attack type, it might be zero-day
            ml_prediction = log_entry.get("ml_prediction", {})
            
            is_anomaly = ml_prediction.get("is_anomaly", False)
            anomaly_score = ml_prediction.get("anomaly_score", 0.0)
            attack_type = ml_prediction.get("attack_type", "normal")
            
            # High anomaly score but unknown attack type
            if is_anomaly and attack_type == "normal" and abs(anomaly_score) > self.anomaly_threshold:
                logger.warning(
                    f"Potential zero-day exploit detected: "
                    f"anomaly_score={anomaly_score:.2f}"
                )
                
                return {
                    "attack_type": "zero_day",
                    "detector": self.name,
                    "anomaly_score": anomaly_score,
                    "severity": "critical",
                    "confidence": min(1.0, abs(anomaly_score)),
                }
            
            return None
        
        except Exception as e:
            logger.error(f"Error in zero-day detection: {e}", exc_info=True)
            return None
