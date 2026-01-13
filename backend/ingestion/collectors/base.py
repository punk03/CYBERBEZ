"""Base collector class."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import asyncio

from backend.common.logging import get_logger

logger = get_logger(__name__)


class BaseCollector(ABC):
    """Base class for log collectors."""
    
    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize collector.
        
        Args:
            name: Collector name
            config: Collector configuration
        """
        self.name = name
        self.config = config or {}
        self.running = False
        self._task: Optional[asyncio.Task] = None
    
    @abstractmethod
    async def start(self) -> None:
        """Start collecting logs."""
        pass
    
    @abstractmethod
    async def stop(self) -> None:
        """Stop collecting logs."""
        pass
    
    @abstractmethod
    async def collect(self) -> Optional[Dict[str, Any]]:
        """Collect a log entry."""
        pass
    
    async def run(self) -> None:
        """Run collector loop."""
        self.running = True
        logger.info(f"Collector {self.name} started")
        
        while self.running:
            try:
                log_entry = await self.collect()
                if log_entry:
                    # Process log entry (will be implemented with Kafka producer)
                    await self.process_log(log_entry)
            except Exception as e:
                logger.error(f"Error in collector {self.name}: {e}", exc_info=True)
                await asyncio.sleep(1)  # Brief pause on error
    
    async def process_log(self, log_entry: Dict[str, Any]) -> None:
        """
        Process collected log entry.
        
        Args:
            log_entry: Log entry dictionary
        """
        # This will be implemented to send to Kafka
        logger.debug(f"Processing log entry: {log_entry}")
        pass
