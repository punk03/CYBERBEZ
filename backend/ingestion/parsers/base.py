"""Base parser class."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

from backend.common.logging import get_logger

logger = get_logger(__name__)


class BaseParser(ABC):
    """Base class for log parsers."""
    
    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize parser.
        
        Args:
            name: Parser name
            config: Parser configuration
        """
        self.name = name
        self.config = config or {}
    
    @abstractmethod
    def parse(self, raw_log: str, metadata: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Parse raw log entry.
        
        Args:
            raw_log: Raw log string
            metadata: Additional metadata (source, timestamp, etc.)
        
        Returns:
            Parsed log entry or None if parsing failed
        """
        pass
    
    def can_parse(self, raw_log: str) -> bool:
        """
        Check if parser can parse this log entry.
        
        Args:
            raw_log: Raw log string
        
        Returns:
            True if parser can parse, False otherwise
        """
        return True  # Default implementation
