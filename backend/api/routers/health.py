"""Health check endpoints."""

from fastapi import APIRouter, status
from pydantic import BaseModel
from typing import Dict, Any

from backend.monitoring.health import health_checker

router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    version: str
    checks: Dict[str, Any]


@router.get("/health", response_model=HealthResponse, status_code=status.HTTP_200_OK)
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    health_data = await health_checker.check_all()
    
    return HealthResponse(
        status=health_data["status"],
        version=health_data["version"],
        checks=health_data["components"],
    )


@router.get("/ready", status_code=status.HTTP_200_OK)
async def readiness_check() -> Dict[str, str]:
    """Readiness check endpoint."""
    return {"status": "ready"}


@router.get("/live", status_code=status.HTTP_200_OK)
async def liveness_check() -> Dict[str, str]:
    """Liveness check endpoint."""
    return {"status": "alive"}
