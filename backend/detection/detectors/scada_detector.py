"""SCADA attack detector."""

from typing import Dict, Any, Optional
import re

from backend.detection.detectors.base import BaseDetector
from backend.common.logging import get_logger

logger = get_logger(__name__)


class SCADADetector(BaseDetector):
    """Detector for SCADA-specific attacks."""
    
    # SCADA protocols
    SCADA_PROTOCOLS = ["modbus", "dnp3", "iec61850", "opc", "bacnet", "profinet"]
    
    # SCADA attack patterns
    SCADA_ATTACK_PATTERNS = [
        # Unauthorized access
        r"(?i)(unauthorized|forbidden).*(scada|ics|plc|hmi)",
        r"(?i)(access.?denied).*(industrial|control)",
        
        # Command manipulation
        r"(?i)(write|modify).*(register|coil|holding)",
        r"(?i)(setpoint|control.?value).*(manipulation|change)",
        
        # Protocol violations
        r"(?i)(invalid.?function.?code|illegal.?data.?address)",
        r"(?i)(exception.?response|error.?code)",
        
        # Suspicious operations
        r"(?i)(emergency.?stop|shutdown|reset).*(unauthorized)",
        r"(?i)(bypass|override).*(safety|protection)",
    ]
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize SCADA detector."""
        super().__init__("scada", config)
        self.patterns = [re.compile(pattern) for pattern in self.SCADA_ATTACK_PATTERNS]
    
    def _is_scada_protocol(self, log_entry: Dict[str, Any]) -> bool:
        """Check if log entry is from SCADA protocol."""
        protocol = str(log_entry.get("protocol", "")).lower()
        service = str(log_entry.get("service", "")).lower()
        message = str(log_entry.get("message", "")).lower()
        
        for scada_protocol in self.SCADA_PROTOCOLS:
            if scada_protocol in protocol or scada_protocol in service or scada_protocol in message:
                return True
        
        return False
    
    async def detect(self, log_entry: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Detect SCADA attack."""
        if not self.enabled:
            return None
        
        try:
            # Check if it's SCADA-related
            if not self._is_scada_protocol(log_entry):
                return None
            
            message = str(log_entry.get("message", "")).lower()
            matches = []
            
            # Check attack patterns
            for pattern in self.patterns:
                if pattern.search(message):
                    matches.append(pattern.pattern)
            
            if matches:
                logger.warning(
                    f"SCADA attack detected: {len(matches)} indicators matched"
                )
                
                return {
                    "attack_type": "scada_attack",
                    "detector": self.name,
                    "indicators": matches,
                    "match_count": len(matches),
                    "severity": "critical",
                    "confidence": min(1.0, len(matches) / 3.0),
                }
            
            # Check ML prediction
            ml_prediction = log_entry.get("ml_prediction", {})
            if ml_prediction.get("attack_type") == "scada_attack":
                confidence = ml_prediction.get("confidence", 0.0)
                if confidence > 0.6:
                    return {
                        "attack_type": "scada_attack",
                        "detector": self.name,
                        "ml_detected": True,
                        "confidence": confidence,
                        "severity": "critical",
                    }
            
            return None
        
        except Exception as e:
            logger.error(f"Error in SCADA detection: {e}", exc_info=True)
            return None
