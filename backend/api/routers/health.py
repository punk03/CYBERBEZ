"""Health check endpoints."""

from fastapi import APIRouter, status
from pydantic import BaseModel
from typing import Dict, Any

from backend.storage.database import engine
from backend.storage.mongodb import get_mongodb_client

router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    version: str
    checks: Dict[str, Any]


@router.get("/health", response_model=HealthResponse, status_code=status.HTTP_200_OK)
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    checks = {}
    
    # Check PostgreSQL
    try:
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        checks["postgresql"] = "healthy"
    except Exception as e:
        checks["postgresql"] = f"unhealthy: {str(e)}"
    
    # Check MongoDB
    try:
        client = await get_mongodb_client()
        await client.admin.command("ping")
        checks["mongodb"] = "healthy"
    except Exception as e:
        checks["mongodb"] = f"unhealthy: {str(e)}"
    
    # Determine overall status
    overall_status = "healthy" if all("healthy" in str(v) for v in checks.values()) else "degraded"
    
    return HealthResponse(
        status=overall_status,
        version="0.1.0",
        checks=checks,
    )


@router.get("/ready", status_code=status.HTTP_200_OK)
async def readiness_check() -> Dict[str, str]:
    """Readiness check endpoint."""
    return {"status": "ready"}


@router.get("/live", status_code=status.HTTP_200_OK)
async def liveness_check() -> Dict[str, str]:
    """Liveness check endpoint."""
    return {"status": "alive"}
