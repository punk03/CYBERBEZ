"""Time window aggregator."""

from typing import Dict, Any, List
from datetime import datetime, timedelta
from collections import defaultdict

from backend.common.logging import get_logger

logger = get_logger(__name__)


class TimeWindowAggregator:
    """Aggregate logs within time windows."""
    
    def __init__(self, window_seconds: int = 60):
        """
        Initialize time window aggregator.
        
        Args:
            window_seconds: Time window size in seconds
        """
        self.window_seconds = window_seconds
        self.windows: Dict[str, Dict[str, Any]] = {}
        self.window_data: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    
    def _get_window_key(self, timestamp: str) -> str:
        """Get window key for timestamp."""
        try:
            dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            # Round down to window boundary
            window_start = dt - timedelta(
                seconds=dt.second % self.window_seconds,
                microseconds=dt.microsecond
            )
            return window_start.isoformat()
        except Exception:
            return datetime.utcnow().isoformat()
    
    def add_log(self, log_entry: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add log entry to aggregation window.
        
        Args:
            log_entry: Log entry
        
        Returns:
            Aggregated entry if window is complete, None otherwise
        """
        timestamp = log_entry.get("timestamp", datetime.utcnow().isoformat())
        window_key = self._get_window_key(timestamp)
        
        # Add to window
        self.window_data[window_key].append(log_entry)
        
        # Check if window is complete (older than window_seconds)
        window_dt = datetime.fromisoformat(window_key.replace("Z", "+00:00"))
        now = datetime.utcnow()
        
        if (now - window_dt).total_seconds() >= self.window_seconds:
            # Window is complete, aggregate
            aggregated = self._aggregate_window(window_key)
            del self.window_data[window_key]
            return aggregated
        
        return None
    
    def _aggregate_window(self, window_key: str) -> Dict[str, Any]:
        """Aggregate logs in a window."""
        logs = self.window_data.get(window_key, [])
        
        if not logs:
            return None
        
        # Count by level
        level_counts = defaultdict(int)
        sources = set()
        hosts = set()
        
        for log in logs:
            level = log.get("level", "INFO")
            level_counts[level] += 1
            sources.add(log.get("source", "unknown"))
            hosts.add(log.get("host", "unknown"))
        
        # Create aggregated entry
        aggregated = {
            "type": "aggregated",
            "window_start": window_key,
            "window_seconds": self.window_seconds,
            "count": len(logs),
            "level_counts": dict(level_counts),
            "sources": list(sources),
            "hosts": list(hosts),
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        logger.info(
            f"Aggregated {len(logs)} logs in window {window_key}: "
            f"{dict(level_counts)}"
        )
        
        return aggregated
