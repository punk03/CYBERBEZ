"""Worker for processing logs from Kafka."""

import asyncio
from typing import Dict, Any

from backend.processing.stream_processor import StreamProcessor
from backend.processing.enrichers.geoip import GeoIPEnricher
from backend.processing.enrichers.threat_intel import ThreatIntelEnricher
from backend.processing.enrichers.asset_info import AssetInfoEnricher
from backend.processing.filters.level_filter import LevelFilter
from backend.processing.filters.source_filter import SourceFilter
from backend.storage.mongodb import get_mongodb_database
from backend.storage.database import get_db
from backend.common.config import settings
from backend.common.logging import get_logger

logger = get_logger(__name__)


async def save_to_mongodb(log_entry: Dict[str, Any]) -> None:
    """Save log entry to MongoDB."""
    try:
        db = await get_mongodb_database()
        await db.logs.insert_one(log_entry)
        logger.debug(f"Saved log entry to MongoDB: {log_entry.get('message', '')[:100]}")
    except Exception as e:
        logger.error(f"Error saving to MongoDB: {e}", exc_info=True)


async def save_to_timescale(log_entry: Dict[str, Any]) -> None:
    """Save log entry to TimescaleDB."""
    try:
        # This will be implemented when we create TimescaleDB models
        # For now, just log
        logger.debug(f"Would save to TimescaleDB: {log_entry.get('message', '')[:100]}")
    except Exception as e:
        logger.error(f"Error saving to TimescaleDB: {e}", exc_info=True)


async def process_log_entry(log_entry: Dict[str, Any], key: str = None) -> Dict[str, Any]:
    """
    Process a single log entry.
    
    Args:
        log_entry: Log entry to process
        key: Kafka message key
    
    Returns:
        Processed log entry
    """
    # Apply enrichers
    geoip_enricher = GeoIPEnricher()
    log_entry = await geoip_enricher.enrich(log_entry)
    
    threat_intel_enricher = ThreatIntelEnricher()
    log_entry = await threat_intel_enricher.enrich(log_entry)
    
    asset_info_enricher = AssetInfoEnricher()
    log_entry = await asset_info_enricher.enrich(log_entry)
    
    # Apply filters
    level_filter = LevelFilter()
    filtered = await level_filter.filter(log_entry)
    if filtered is None:
        return None  # Entry filtered out
    
    # Save to databases
    await save_to_mongodb(log_entry)
    await save_to_timescale(log_entry)
    
    return log_entry


class LogProcessorWorker:
    """Worker for processing logs from Kafka."""
    
    def __init__(self):
        """Initialize log processor worker."""
        self.processor: StreamProcessor = None
        self.running = False
    
    async def start(self) -> None:
        """Start log processor worker."""
        self.processor = StreamProcessor(
            topic=settings.KAFKA_TOPIC_LOGS,
            group_id="log-processor-group",
            processors=[process_log_entry]
        )
        await self.processor.start()
        self.running = True
        logger.info("Log processor worker started")
    
    async def stop(self) -> None:
        """Stop log processor worker."""
        self.running = False
        if self.processor:
            await self.processor.stop()
        logger.info("Log processor worker stopped")


# Global worker instance
log_processor_worker = LogProcessorWorker()
