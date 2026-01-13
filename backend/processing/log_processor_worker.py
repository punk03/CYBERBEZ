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
from backend.monitoring.metrics import (
    record_log_processed,
    record_threat_detected,
    record_ml_prediction,
    record_automation_action,
)
import time

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
        from backend.storage.timescale import save_log_to_timescale
        await save_log_to_timescale(log_entry)
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
    start_time = time.time()
    source = log_entry.get("source", "unknown")
    
    try:
        # Apply enrichers
        geoip_enricher = GeoIPEnricher()
        log_entry = await geoip_enricher.enrich(log_entry)
        
        threat_intel_enricher = ThreatIntelEnricher()
        log_entry = await threat_intel_enricher.enrich(log_entry)
        
        asset_info_enricher = AssetInfoEnricher()
        log_entry = await asset_info_enricher.enrich(log_entry)
        
        # ML prediction
        ml_start = time.time()
        try:
            from backend.ml.inference.predictor import MLPredictor
            predictor = MLPredictor()
            ml_prediction = await predictor.predict(log_entry)
            log_entry["ml_prediction"] = ml_prediction
            
            ml_duration = time.time() - ml_start
            result = "threat" if ml_prediction.get("is_threat") else "normal"
            record_ml_prediction("ensemble", result, ml_duration)
            
            # If threat detected, log warning
            if ml_prediction.get("is_threat"):
                logger.warning(
                    f"Threat detected: {ml_prediction.get('attack_type')} "
                    f"(confidence: {ml_prediction.get('confidence', 0):.2f})"
                )
        except Exception as e:
            logger.warning(f"Error in ML prediction: {e}")
        
        # Attack detection
        detection_start = time.time()
        try:
            from backend.detection.orchestrator import DetectorOrchestrator
            orchestrator = DetectorOrchestrator()
            detections = await orchestrator.detect(log_entry)
            
            if detections:
                log_entry["detections"] = detections
                detection_duration = time.time() - detection_start
                
                for detection in detections:
                    record_threat_detected(
                        detection.get("attack_type", "unknown"),
                        detection.get("severity", "medium"),
                        detection_duration
                    )
                
                logger.warning(
                    f"Attack detected: {len(detections)} detection(s) - "
                    f"{[d.get('attack_type') for d in detections]}"
                )
                
                # Trigger automation for each detection
                try:
                    from backend.automation.orchestrator import AutomationOrchestrator
                    automation = AutomationOrchestrator()
                    
                    for detection in detections:
                        automation_start = time.time()
                        automation_result = await automation.handle_threat(detection)
                        automation_duration = time.time() - automation_start
                        
                        log_entry["automation"] = automation_result
                        
                        status = "success" if automation_result.get("success") else "failed"
                        for action in automation_result.get("actions", []):
                            record_automation_action(
                                action.get("type", "unknown"),
                                status,
                                automation_duration
                            )
                        
                        if automation_result.get("success"):
                            logger.info(
                                f"Automation executed for {detection.get('attack_type')}: "
                                f"{len(automation_result.get('actions', []))} actions"
                            )
                        
                        # Send alert notification
                        try:
                            from backend.alerting.notification_service import notification_service
                            from backend.monitoring.metrics import record_alert_sent
                            
                            alert_result = await notification_service.send_threat_alert(detection)
                            if alert_result.get("success"):
                                for channel in alert_result.get("channels", {}).keys():
                                    record_alert_sent(channel, detection.get("severity", "medium"))
                        except Exception as e:
                            logger.error(f"Error sending alert notification: {e}", exc_info=True)
                except Exception as e:
                    logger.error(f"Error in automation: {e}", exc_info=True)
        except Exception as e:
            logger.warning(f"Error in attack detection: {e}")
        
        # Apply filters
        level_filter = LevelFilter()
        filtered = await level_filter.filter(log_entry)
        if filtered is None:
            duration = time.time() - start_time
            record_log_processed(source, "filtered", duration)
            return None  # Entry filtered out
        
        # Save to databases
        await save_to_mongodb(log_entry)
        await save_to_timescale(log_entry)
        
        duration = time.time() - start_time
        record_log_processed(source, "processed", duration)
        
        return log_entry
    
    except Exception as e:
        duration = time.time() - start_time
        record_log_processed(source, "error", duration)
        logger.error(f"Error processing log entry: {e}", exc_info=True)
        raise


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
