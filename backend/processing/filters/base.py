"""Base filter class."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

from backend.common.logging import get_logger

logger = get_logger(__name__)


class BaseFilter(ABC):
    """Base class for filters."""
    
    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize filter.
        
        Args:
            name: Filter name
            config: Filter configuration
        """
        self.name = name
        self.config = config or {}
    
    @abstractmethod
    async def filter(self, log_entry: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Filter log entry.
        
        Args:
            log_entry: Log entry to filter
        
        Returns:
            Filtered log entry or None if entry should be dropped
        """
        pass
