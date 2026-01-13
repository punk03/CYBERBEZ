"""Source filter."""

from typing import Dict, Any, Optional, Set

from backend.processing.filters.base import BaseFilter
from backend.common.logging import get_logger

logger = get_logger(__name__)


class SourceFilter(BaseFilter):
    """Filter logs by source."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize source filter."""
        super().__init__("source_filter", config)
        
        # Sources to include (empty = all sources)
        include_sources = config.get("include_sources", []) if config else []
        self.include_sources: Set[str] = set(include_sources) if include_sources else None
        
        # Sources to exclude
        exclude_sources = config.get("exclude_sources", []) if config else []
        self.exclude_sources: Set[str] = set(exclude_sources)
    
    async def filter(self, log_entry: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Filter log entry by source."""
        source = log_entry.get("source", "unknown")
        
        # Check exclude list
        if source in self.exclude_sources:
            logger.debug(f"Filtered out log entry from source {source} (excluded)")
            return None
        
        # Check include list
        if self.include_sources is not None and source not in self.include_sources:
            logger.debug(f"Filtered out log entry from source {source} (not in include list)")
            return None
        
        return log_entry
