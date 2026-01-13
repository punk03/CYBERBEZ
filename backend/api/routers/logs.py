"""Logs API endpoints."""

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

from backend.ingestion.parsers.json_parser import JSONParser
from backend.ingestion.parsers.csv_parser import CSVParser
from backend.ingestion.parsers.xml_parser import XMLParser
from backend.ingestion.parsers.syslog_parser import SyslogParser
from backend.ingestion.normalizers.log_normalizer import LogNormalizer
from backend.storage.mongodb import get_mongodb_database

router = APIRouter()

# Initialize parsers
parsers = [
    JSONParser(),
    CSVParser(),
    XMLParser(),
    SyslogParser(),
]

normalizer = LogNormalizer()


class LogEntryRequest(BaseModel):
    """Request model for log entry."""
    log: str
    source: Optional[str] = "api"
    format: Optional[str] = None  # json, csv, xml, syslog, auto
    metadata: Optional[Dict[str, Any]] = None


class LogEntryResponse(BaseModel):
    """Response model for log entry."""
    success: bool
    message: str
    log_id: Optional[str] = None


@router.post("/logs", response_model=LogEntryResponse, status_code=status.HTTP_201_CREATED)
async def receive_log(
    log_request: LogEntryRequest,
    db=Depends(get_mongodb_database)
) -> LogEntryResponse:
    """
    Receive and process a log entry.
    
    Args:
        log_request: Log entry request
        db: MongoDB database dependency
    
    Returns:
        Log entry response
    """
    try:
        # Determine parser
        parser = None
        if log_request.format:
            # Use specified parser
            parser_map = {
                "json": JSONParser(),
                "csv": CSVParser(),
                "xml": XMLParser(),
                "syslog": SyslogParser(),
            }
            parser = parser_map.get(log_request.format.lower())
        else:
            # Auto-detect parser
            for p in parsers:
                if p.can_parse(log_request.log):
                    parser = p
                    break
        
        if not parser:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unable to parse log entry. Unsupported format."
            )
        
        # Parse log
        metadata = log_request.metadata or {}
        metadata["source"] = log_request.source
        parsed = parser.parse(log_request.log, metadata)
        
        if not parsed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to parse log entry"
            )
        
        # Normalize log
        normalized = normalizer.normalize(parsed)
        
        # Save to MongoDB
        result = await db.logs.insert_one(normalized)
        
        return LogEntryResponse(
            success=True,
            message="Log entry received and processed",
            log_id=str(result.inserted_id)
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing log entry: {str(e)}"
        )


@router.get("/logs", status_code=status.HTTP_200_OK)
async def get_logs(
    limit: int = 100,
    skip: int = 0,
    source: Optional[str] = None,
    db=Depends(get_mongodb_database)
) -> Dict[str, Any]:
    """
    Get logs from database.
    
    Args:
        limit: Maximum number of logs to return
        skip: Number of logs to skip
        source: Filter by source
        db: MongoDB database dependency
    
    Returns:
        List of logs
    """
    try:
        query = {}
        if source:
            query["source"] = source
        
        cursor = db.logs.find(query).skip(skip).limit(limit).sort("timestamp", -1)
        logs = await cursor.to_list(length=limit)
        
        # Convert ObjectId to string
        for log in logs:
            log["_id"] = str(log["_id"])
        
        total = await db.logs.count_documents(query)
        
        return {
            "logs": logs,
            "total": total,
            "limit": limit,
            "skip": skip,
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving logs: {str(e)}"
        )
