"""TimescaleDB operations."""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from backend.storage.database import SessionLocal
from backend.common.logging import get_logger

logger = get_logger(__name__)


async def save_log_to_timescale(log_entry: Dict[str, Any]) -> None:
    """
    Save log entry to TimescaleDB.
    
    Args:
        log_entry: Log entry dictionary
    """
    try:
        # For MVP, we'll use raw SQL
        # In production, create SQLAlchemy models for TimescaleDB
        db = SessionLocal()
        
        try:
            # Insert into timescale hypertable
            # Assuming table structure: logs (time, source, host, level, message, metadata)
            query = """
                INSERT INTO logs (time, source, host, level, message, metadata)
                VALUES (:time, :source, :host, :level, :message, :metadata)
            """
            
            db.execute(
                query,
                {
                    "time": datetime.fromisoformat(log_entry.get("timestamp", datetime.utcnow().isoformat())),
                    "source": log_entry.get("source", "unknown"),
                    "host": log_entry.get("host", "unknown"),
                    "level": log_entry.get("level", "INFO"),
                    "message": log_entry.get("message", ""),
                    "metadata": str(log_entry.get("metadata", {})),
                }
            )
            db.commit()
            logger.debug("Log entry saved to TimescaleDB")
        
        finally:
            db.close()
    
    except Exception as e:
        logger.error(f"Error saving to TimescaleDB: {e}", exc_info=True)


async def query_timescale_logs(
    start_time: datetime,
    end_time: datetime,
    source: Optional[str] = None,
    limit: int = 1000
) -> List[Dict[str, Any]]:
    """
    Query logs from TimescaleDB.
    
    Args:
        start_time: Start time
        end_time: End time
        source: Filter by source
        limit: Maximum number of logs
    
    Returns:
        List of log entries
    """
    try:
        db = SessionLocal()
        
        try:
            query = """
                SELECT time, source, host, level, message, metadata
                FROM logs
                WHERE time >= :start_time AND time <= :end_time
            """
            params = {
                "start_time": start_time,
                "end_time": end_time,
            }
            
            if source:
                query += " AND source = :source"
                params["source"] = source
            
            query += " ORDER BY time DESC LIMIT :limit"
            params["limit"] = limit
            
            result = db.execute(query, params)
            rows = result.fetchall()
            
            logs = []
            for row in rows:
                logs.append({
                    "timestamp": row[0].isoformat(),
                    "source": row[1],
                    "host": row[2],
                    "level": row[3],
                    "message": row[4],
                    "metadata": eval(row[5]) if row[5] else {},
                })
            
            return logs
        
        finally:
            db.close()
    
    except Exception as e:
        logger.error(f"Error querying TimescaleDB: {e}", exc_info=True)
        return []
