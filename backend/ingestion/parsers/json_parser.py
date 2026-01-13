"""JSON log parser."""

import json
from typing import Dict, Any, Optional

from backend.ingestion.parsers.base import BaseParser
from backend.common.logging import get_logger

logger = get_logger(__name__)


class JSONParser(BaseParser):
    """Parser for JSON formatted logs."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize JSON parser."""
        super().__init__("json", config)
    
    def can_parse(self, raw_log: str) -> bool:
        """Check if log is valid JSON."""
        try:
            json.loads(raw_log)
            return True
        except (json.JSONDecodeError, ValueError):
            return False
    
    def parse(self, raw_log: str, metadata: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Parse JSON log entry."""
        try:
            parsed = json.loads(raw_log)
            
            # Ensure it's a dictionary
            if not isinstance(parsed, dict):
                parsed = {"message": raw_log, "data": parsed}
            
            # Merge with metadata
            if metadata:
                parsed.update(metadata)
            
            return parsed
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Failed to parse JSON log: {e}")
            return None
