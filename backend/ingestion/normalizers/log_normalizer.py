"""Log normalizer for converting logs to unified format."""

from typing import Dict, Any, Optional
from datetime import datetime

from backend.common.logging import get_logger

logger = get_logger(__name__)


class LogNormalizer:
    """Normalize logs to unified format."""
    
    # Standard fields in normalized log
    STANDARD_FIELDS = [
        "timestamp",
        "source",
        "host",
        "service",
        "level",
        "message",
        "raw",
        "metadata",
    ]
    
    def __init__(self):
        """Initialize log normalizer."""
        pass
    
    def normalize(self, log_entry: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize log entry to unified format.
        
        Args:
            log_entry: Parsed log entry
        
        Returns:
            Normalized log entry
        """
        normalized = {
            "timestamp": self._extract_timestamp(log_entry),
            "source": log_entry.get("source", "unknown"),
            "host": log_entry.get("host") or log_entry.get("hostname") or "unknown",
            "service": log_entry.get("service") or log_entry.get("app_name") or log_entry.get("tag") or "unknown",
            "level": self._extract_level(log_entry),
            "message": self._extract_message(log_entry),
            "raw": log_entry.get("raw") or str(log_entry),
            "metadata": self._extract_metadata(log_entry),
        }
        
        # Add any additional fields as metadata
        for key, value in log_entry.items():
            if key not in normalized and key not in self.STANDARD_FIELDS:
                normalized["metadata"][key] = value
        
        return normalized
    
    def _extract_timestamp(self, log_entry: Dict[str, Any]) -> str:
        """Extract and normalize timestamp."""
        timestamp = log_entry.get("timestamp")
        
        if timestamp:
            # Try to parse if it's a string
            if isinstance(timestamp, str):
                try:
                    # Try various formats
                    dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                    return dt.isoformat()
                except ValueError:
                    pass
            
            return str(timestamp)
        
        # Default to current time
        return datetime.utcnow().isoformat()
    
    def _extract_level(self, log_entry: Dict[str, Any]) -> str:
        """Extract log level."""
        # Check various possible fields
        level = (
            log_entry.get("level") or
            log_entry.get("severity") or
            log_entry.get("log_level") or
            "INFO"
        )
        
        # Normalize level
        level_str = str(level).upper()
        valid_levels = ["DEBUG", "INFO", "WARNING", "WARN", "ERROR", "CRITICAL", "FATAL"]
        
        if level_str in valid_levels:
            return level_str
        
        # Map numeric severity to level (syslog)
        if isinstance(level, int):
            severity_map = {
                0: "EMERGENCY",
                1: "ALERT",
                2: "CRITICAL",
                3: "ERROR",
                4: "WARNING",
                5: "NOTICE",
                6: "INFO",
                7: "DEBUG",
            }
            return severity_map.get(level, "INFO")
        
        return "INFO"
    
    def _extract_message(self, log_entry: Dict[str, Any]) -> str:
        """Extract log message."""
        message = (
            log_entry.get("message") or
            log_entry.get("text") or
            log_entry.get("_text") or
            log_entry.get("raw") or
            str(log_entry)
        )
        
        return str(message).strip()
    
    def _extract_metadata(self, log_entry: Dict[str, Any]) -> Dict[str, Any]:
        """Extract metadata from log entry."""
        metadata = {}
        
        # Common metadata fields
        metadata_fields = [
            "priority", "facility", "format", "version",
            "proc_id", "msg_id", "structured_data",
            "file_path", "port", "tag", "app_name",
        ]
        
        for field in metadata_fields:
            if field in log_entry:
                metadata[field] = log_entry[field]
        
        return metadata
