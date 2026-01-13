"""Threats API endpoints."""

from fastapi import APIRouter, HTTPException, status, Depends, Query
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

from backend.storage.mongodb import get_mongodb_database

router = APIRouter()


class ThreatResponse(BaseModel):
    """Threat response model."""
    threat_id: str
    attack_type: str
    severity: str
    confidence: float
    source_ip: Optional[str] = None
    timestamp: str
    detection_details: Dict[str, Any]
    automation_status: Optional[Dict[str, Any]] = None


@router.get("/threats", status_code=status.HTTP_200_OK)
async def get_threats(
    limit: int = Query(100, ge=1, le=1000),
    skip: int = Query(0, ge=0),
    attack_type: Optional[str] = None,
    severity: Optional[str] = None,
    db=Depends(get_mongodb_database)
) -> Dict[str, Any]:
    """
    Get detected threats.
    
    Args:
        limit: Maximum number of threats to return
        skip: Number of threats to skip
        attack_type: Filter by attack type
        severity: Filter by severity
        db: MongoDB database dependency
    
    Returns:
        List of threats
    """
    try:
        query = {}
        
        # Build query filters
        if attack_type:
            query["detections.attack_type"] = attack_type
        
        if severity:
            query["detections.severity"] = severity
        
        # Find logs with detections
        cursor = db.logs.find(
            {"detections": {"$exists": True, "$ne": []}},
            query
        ).skip(skip).limit(limit).sort("timestamp", -1)
        
        logs = await cursor.to_list(length=limit)
        
        # Extract threats from logs
        threats = []
        for log in logs:
            detections = log.get("detections", [])
            for detection in detections:
                threat = {
                    "threat_id": str(log["_id"]),
                    "attack_type": detection.get("attack_type", "unknown"),
                    "severity": detection.get("severity", "medium"),
                    "confidence": detection.get("confidence", 0.0),
                    "source_ip": detection.get("source_ip") or detection.get("ip"),
                    "timestamp": log.get("timestamp", datetime.utcnow().isoformat()),
                    "detection_details": detection,
                    "automation_status": log.get("automation"),
                }
                threats.append(threat)
        
        total = await db.logs.count_documents({"detections": {"$exists": True, "$ne": []}})
        
        return {
            "threats": threats,
            "total": total,
            "limit": limit,
            "skip": skip,
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving threats: {str(e)}"
        )


@router.get("/threats/{threat_id}", response_model=ThreatResponse, status_code=status.HTTP_200_OK)
async def get_threat(
    threat_id: str,
    db=Depends(get_mongodb_database)
) -> ThreatResponse:
    """
    Get threat by ID.
    
    Args:
        threat_id: Threat ID
        db: MongoDB database dependency
    
    Returns:
        Threat details
    """
    try:
        from bson import ObjectId
        
        log = await db.logs.find_one({"_id": ObjectId(threat_id)})
        
        if not log:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Threat not found"
            )
        
        detections = log.get("detections", [])
        if not detections:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No detections found for this log"
            )
        
        # Use first detection
        detection = detections[0]
        
        return ThreatResponse(
            threat_id=str(log["_id"]),
            attack_type=detection.get("attack_type", "unknown"),
            severity=detection.get("severity", "medium"),
            confidence=detection.get("confidence", 0.0),
            source_ip=detection.get("source_ip") or detection.get("ip"),
            timestamp=log.get("timestamp", datetime.utcnow().isoformat()),
            detection_details=detection,
            automation_status=log.get("automation"),
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving threat: {str(e)}"
        )


@router.get("/threats/stats/summary", status_code=status.HTTP_200_OK)
async def get_threats_summary(
    db=Depends(get_mongodb_database)
) -> Dict[str, Any]:
    """Get threats summary statistics."""
    try:
        # Get all logs with detections
        cursor = db.logs.find({"detections": {"$exists": True, "$ne": []}})
        logs = await cursor.to_list(length=None)
        
        # Calculate statistics
        total_threats = 0
        attack_types = {}
        severities = {}
        automation_executed = 0
        
        for log in logs:
            detections = log.get("detections", [])
            total_threats += len(detections)
            
            for detection in detections:
                attack_type = detection.get("attack_type", "unknown")
                attack_types[attack_type] = attack_types.get(attack_type, 0) + 1
                
                severity = detection.get("severity", "medium")
                severities[severity] = severities.get(severity, 0) + 1
            
            if log.get("automation", {}).get("success"):
                automation_executed += 1
        
        return {
            "total_threats": total_threats,
            "attack_types": attack_types,
            "severities": severities,
            "automation_executed": automation_executed,
            "automation_rate": automation_executed / total_threats if total_threats > 0 else 0.0,
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error calculating statistics: {str(e)}"
        )
