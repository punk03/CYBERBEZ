"""Log level filter."""

from typing import Dict, Any, Optional, List

from backend.processing.filters.base import BaseFilter
from backend.common.logging import get_logger

logger = get_logger(__name__)


class LevelFilter(BaseFilter):
    """Filter logs by level."""
    
    # Level hierarchy
    LEVELS = {
        "DEBUG": 0,
        "INFO": 1,
        "WARNING": 2,
        "WARN": 2,
        "ERROR": 3,
        "CRITICAL": 4,
        "FATAL": 4,
    }
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize level filter."""
        super().__init__("level_filter", config)
        
        # Minimum level to keep (default: INFO)
        min_level = config.get("min_level", "INFO") if config else "INFO"
        self.min_level_value = self.LEVELS.get(min_level.upper(), 1)
        
        # Levels to always keep (default: ERROR and above)
        always_keep = config.get("always_keep", ["ERROR", "CRITICAL", "FATAL"]) if config else ["ERROR", "CRITICAL", "FATAL"]
        self.always_keep_values = {
            self.LEVELS.get(level.upper(), 3) for level in always_keep
        }
    
    async def filter(self, log_entry: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Filter log entry by level."""
        level = log_entry.get("level", "INFO")
        level_value = self.LEVELS.get(level.upper(), 1)
        
        # Always keep critical levels
        if level_value in self.always_keep_values:
            return log_entry
        
        # Filter by minimum level
        if level_value >= self.min_level_value:
            return log_entry
        
        # Drop entry
        logger.debug(f"Filtered out log entry with level {level}")
        return None
