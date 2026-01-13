"""Stream processor for real-time log processing."""

import asyncio
from typing import Dict, Any, Optional, Callable, List
from aiokafka import AIOKafkaConsumer

from backend.processing.kafka_client import kafka_client
from backend.common.logging import get_logger

logger = get_logger(__name__)


class StreamProcessor:
    """Stream processor for processing logs in real-time."""
    
    def __init__(
        self,
        topic: str,
        group_id: str,
        processors: Optional[List[Callable]] = None
    ):
        """
        Initialize stream processor.
        
        Args:
            topic: Kafka topic to consume from
            group_id: Consumer group ID
            processors: List of processor functions
        """
        self.topic = topic
        self.group_id = group_id
        self.processors = processors or []
        self.running = False
        self._task: Optional[asyncio.Task] = None
        self._consumer: Optional[AIOKafkaConsumer] = None
    
    async def start(self) -> None:
        """Start stream processor."""
        self.running = True
        self._consumer = await kafka_client.create_consumer(
            self.topic,
            self.group_id
        )
        self._task = asyncio.create_task(self._process_loop())
        logger.info(f"Stream processor started for topic {self.topic}")
    
    async def stop(self) -> None:
        """Stop stream processor."""
        self.running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        if self._consumer:
            await kafka_client.stop_consumer(self.topic)
        logger.info(f"Stream processor stopped for topic {self.topic}")
    
    async def _process_loop(self) -> None:
        """Main processing loop."""
        try:
            async for message in self._consumer:
                try:
                    log_entry = message.value
                    key = message.key
                    
                    # Process through all processors
                    processed_entry = log_entry
                    for processor in self.processors:
                        processed_entry = await self._run_processor(
                            processor,
                            processed_entry,
                            key
                        )
                        if processed_entry is None:
                            break  # Processor filtered out the entry
                    
                    # If entry passed all processors, handle it
                    if processed_entry:
                        await self._handle_processed_entry(processed_entry)
                
                except Exception as e:
                    logger.error(f"Error processing message: {e}", exc_info=True)
                    # Continue processing other messages
        
        except asyncio.CancelledError:
            logger.info("Processing loop cancelled")
        except Exception as e:
            logger.error(f"Error in processing loop: {e}", exc_info=True)
    
    async def _run_processor(
        self,
        processor: Callable,
        entry: Dict[str, Any],
        key: Optional[str]
    ) -> Optional[Dict[str, Any]]:
        """
        Run a processor function.
        
        Args:
            processor: Processor function
            entry: Log entry
            key: Message key
        
        Returns:
            Processed entry or None if filtered out
        """
        try:
            if asyncio.iscoroutinefunction(processor):
                return await processor(entry, key)
            else:
                return processor(entry, key)
        except Exception as e:
            logger.error(f"Error in processor {processor.__name__}: {e}")
            return entry  # Continue with original entry
    
    async def _handle_processed_entry(self, entry: Dict[str, Any]) -> None:
        """
        Handle processed log entry.
        
        Args:
            entry: Processed log entry
        """
        # This will be extended to save to databases, trigger alerts, etc.
        logger.debug(f"Processed entry: {entry.get('message', '')[:100]}")
    
    def add_processor(self, processor: Callable) -> None:
        """
        Add a processor function.
        
        Args:
            processor: Processor function
        """
        self.processors.append(processor)
        logger.info(f"Added processor: {processor.__name__}")
