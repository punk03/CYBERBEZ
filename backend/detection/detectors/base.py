"""Base detector class."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List

from backend.common.logging import get_logger

logger = get_logger(__name__)


class BaseDetector(ABC):
    """Base class for attack detectors."""
    
    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize detector.
        
        Args:
            name: Detector name
            config: Detector configuration
        """
        self.name = name
        self.config = config or {}
        self.enabled = config.get("enabled", True) if config else True
    
    @abstractmethod
    async def detect(self, log_entry: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Detect attack in log entry.
        
        Args:
            log_entry: Log entry to analyze
        
        Returns:
            Detection result or None if no attack detected
        """
        pass
    
    def is_enabled(self) -> bool:
        """Check if detector is enabled."""
        return self.enabled
