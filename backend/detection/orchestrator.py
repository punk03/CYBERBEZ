"""Orchestrator for coordinating attack detectors."""

from typing import Dict, Any, List, Optional
import asyncio

from backend.detection.detectors.ddos_detector import DDoSDetector
from backend.detection.detectors.malware_detector import MalwareDetector
from backend.detection.detectors.scada_detector import SCADADetector
from backend.detection.detectors.insider_detector import InsiderThreatDetector
from backend.detection.detectors.network_intrusion_detector import NetworkIntrusionDetector
from backend.detection.detectors.apt_detector import APTDetector
from backend.detection.detectors.ransomware_detector import RansomwareDetector
from backend.detection.detectors.zero_day_detector import ZeroDayDetector
from backend.common.logging import get_logger

logger = get_logger(__name__)


class DetectorOrchestrator:
    """Orchestrator for coordinating multiple detectors."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize detector orchestrator."""
        self.config = config or {}
        
        # Initialize detectors
        self.detectors = [
            DDoSDetector(config.get("ddos", {})),
            MalwareDetector(config.get("malware", {})),
            SCADADetector(config.get("scada", {})),
            InsiderThreatDetector(config.get("insider", {})),
            NetworkIntrusionDetector(config.get("network_intrusion", {})),
            APTDetector(config.get("apt", {})),
            RansomwareDetector(config.get("ransomware", {})),
            ZeroDayDetector(config.get("zero_day", {})),
        ]
        
        # Filter enabled detectors
        self.detectors = [d for d in self.detectors if d.is_enabled()]
        logger.info(f"Initialized {len(self.detectors)} attack detectors")
    
    async def detect(self, log_entry: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Run all detectors on log entry.
        
        Args:
            log_entry: Log entry to analyze
        
        Returns:
            List of detection results
        """
        detections = []
        
        # Run detectors in parallel
        tasks = [detector.detect(log_entry) for detector in self.detectors]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Error in detector {self.detectors[i].name}: {result}")
                continue
            
            if result:
                detections.append(result)
        
        if detections:
            logger.info(f"Detected {len(detections)} threats in log entry")
        
        return detections
    
    def get_detector(self, name: str):
        """Get detector by name."""
        for detector in self.detectors:
            if detector.name == name:
                return detector
        return None
