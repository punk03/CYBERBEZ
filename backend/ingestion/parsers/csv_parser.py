"""CSV log parser."""

import csv
import io
from typing import Dict, Any, Optional, List

from backend.ingestion.parsers.base import BaseParser
from backend.common.logging import get_logger

logger = get_logger(__name__)


class CSVParser(BaseParser):
    """Parser for CSV formatted logs."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize CSV parser."""
        super().__init__("csv", config)
        self.delimiter = config.get("delimiter", ",") if config else ","
        self.has_header = config.get("has_header", True) if config else True
        self.fieldnames: Optional[List[str]] = None
    
    def can_parse(self, raw_log: str) -> bool:
        """Check if log looks like CSV."""
        return self.delimiter in raw_log
    
    def parse(self, raw_log: str, metadata: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Parse CSV log entry."""
        try:
            reader = csv.DictReader(
                io.StringIO(raw_log),
                delimiter=self.delimiter,
                fieldnames=self.fieldnames,
            )
            
            rows = list(reader)
            if not rows:
                return None
            
            # Use first row as parsed data
            parsed = rows[0]
            
            # Merge with metadata
            if metadata:
                parsed.update(metadata)
            
            return parsed
        except Exception as e:
            logger.warning(f"Failed to parse CSV log: {e}")
            return None
