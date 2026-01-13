"""Base enricher class."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

from backend.common.logging import get_logger

logger = get_logger(__name__)


class BaseEnricher(ABC):
    """Base class for data enrichers."""
    
    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize enricher.
        
        Args:
            name: Enricher name
            config: Enricher configuration
        """
        self.name = name
        self.config = config or {}
    
    @abstractmethod
    async def enrich(self, log_entry: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich log entry with additional data.
        
        Args:
            log_entry: Log entry to enrich
        
        Returns:
            Enriched log entry
        """
        pass
