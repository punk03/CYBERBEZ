"""Syslog parser."""

import re
from typing import Dict, Any, Optional
from datetime import datetime

from backend.ingestion.parsers.base import BaseParser
from backend.common.logging import get_logger

logger = get_logger(__name__)


class SyslogParser(BaseParser):
    """Parser for syslog messages (RFC 3164 and RFC 5424)."""
    
    # RFC 3164 pattern: <PRI>TIMESTAMP HOSTNAME TAG: MESSAGE
    RFC3164_PATTERN = re.compile(
        r"<(\d+)>"
        r"(\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})"
        r"\s+(\S+)"
        r"\s+(\S+):"
        r"\s+(.*)"
    )
    
    # RFC 5424 pattern: <PRI>VERSION TIMESTAMP HOSTNAME APP-NAME PROCID MSGID STRUCTURED-DATA MSG
    RFC5424_PATTERN = re.compile(
        r"<(\d+)>"
        r"(\d+)"
        r"\s+(\S+)"
        r"\s+(\S+)"
        r"\s+(\S+)"
        r"\s+(\S+)"
        r"\s+(\S+)"
        r"\s+(\S+)"
        r"\s+(.*)"
    )
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize syslog parser."""
        super().__init__("syslog", config)
    
    def can_parse(self, raw_log: str) -> bool:
        """Check if log looks like syslog."""
        return raw_log.startswith("<") and ">" in raw_log
    
    def _parse_priority(self, pri: str) -> Dict[str, int]:
        """Parse syslog priority."""
        priority = int(pri)
        facility = priority // 8
        severity = priority % 8
        return {
            "priority": priority,
            "facility": facility,
            "severity": severity,
        }
    
    def _parse_rfc3164(self, match: re.Match) -> Dict[str, Any]:
        """Parse RFC 3164 format."""
        pri, timestamp, hostname, tag, message = match.groups()
        
        parsed = {
            "format": "RFC3164",
            "message": message,
            "hostname": hostname,
            "tag": tag,
            "timestamp": timestamp,
        }
        
        parsed.update(self._parse_priority(pri))
        
        return parsed
    
    def _parse_rfc5424(self, match: re.Match) -> Dict[str, Any]:
        """Parse RFC 5424 format."""
        (
            pri, version, timestamp, hostname,
            app_name, proc_id, msg_id, structured_data, message
        ) = match.groups()
        
        parsed = {
            "format": "RFC5424",
            "version": int(version),
            "message": message,
            "hostname": hostname,
            "app_name": app_name,
            "proc_id": proc_id,
            "msg_id": msg_id,
            "structured_data": structured_data,
            "timestamp": timestamp,
        }
        
        parsed.update(self._parse_priority(pri))
        
        return parsed
    
    def parse(self, raw_log: str, metadata: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Parse syslog message."""
        try:
            # Try RFC 5424 first (more structured)
            match = self.RFC5424_PATTERN.match(raw_log)
            if match:
                parsed = self._parse_rfc5424(match)
            else:
                # Try RFC 3164
                match = self.RFC3164_PATTERN.match(raw_log)
                if match:
                    parsed = self._parse_rfc3164(match)
                else:
                    # Fallback: basic parsing
                    parsed = {
                        "format": "unknown",
                        "message": raw_log,
                        "raw": raw_log,
                    }
            
            # Merge with metadata
            if metadata:
                parsed.update(metadata)
            
            return parsed
        except Exception as e:
            logger.warning(f"Failed to parse syslog: {e}")
            return None
