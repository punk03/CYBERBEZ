"""Enhanced health checks."""

from typing import Dict, Any, List
from datetime import datetime

from backend.storage.database import engine
from backend.storage.mongodb import get_mongodb_client
from backend.processing.kafka_client import kafka_client
from backend.common.config import settings
from backend.common.logging import get_logger

logger = get_logger(__name__)


class HealthChecker:
    """Enhanced health checker."""
    
    def __init__(self):
        """Initialize health checker."""
        pass
    
    async def check_all(self) -> Dict[str, Any]:
        """Check health of all components."""
        checks = {
            "timestamp": datetime.utcnow().isoformat(),
            "status": "healthy",
            "version": settings.APP_VERSION,
            "components": {},
        }
        
        # Check PostgreSQL
        checks["components"]["postgresql"] = await self._check_postgresql()
        
        # Check MongoDB
        checks["components"]["mongodb"] = await self._check_mongodb()
        
        # Check Kafka
        checks["components"]["kafka"] = await self._check_kafka()
        
        # Check Redis (if configured)
        checks["components"]["redis"] = await self._check_redis()
        
        # Determine overall status
        component_statuses = [c["status"] for c in checks["components"].values()]
        if "unhealthy" in component_statuses:
            checks["status"] = "unhealthy"
        elif "degraded" in component_statuses:
            checks["status"] = "degraded"
        
        return checks
    
    async def _check_postgresql(self) -> Dict[str, Any]:
        """Check PostgreSQL health."""
        try:
            with engine.connect() as conn:
                result = conn.execute("SELECT 1")
                result.fetchone()
            
            return {
                "status": "healthy",
                "message": "PostgreSQL is accessible",
            }
        except Exception as e:
            logger.error(f"PostgreSQL health check failed: {e}")
            return {
                "status": "unhealthy",
                "message": str(e),
            }
    
    async def _check_mongodb(self) -> Dict[str, Any]:
        """Check MongoDB health."""
        try:
            client = await get_mongodb_client()
            await client.admin.command("ping")
            
            return {
                "status": "healthy",
                "message": "MongoDB is accessible",
            }
        except Exception as e:
            logger.error(f"MongoDB health check failed: {e}")
            return {
                "status": "unhealthy",
                "message": str(e),
            }
    
    async def _check_kafka(self) -> Dict[str, Any]:
        """Check Kafka health."""
        try:
            # Try to create a test producer
            await kafka_client.start_producer()
            
            return {
                "status": "healthy",
                "message": "Kafka is accessible",
            }
        except Exception as e:
            logger.error(f"Kafka health check failed: {e}")
            return {
                "status": "unhealthy",
                "message": str(e),
            }
    
    async def _check_redis(self) -> Dict[str, Any]:
        """Check Redis health."""
        try:
            import redis
            r = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                password=settings.REDIS_PASSWORD,
                socket_connect_timeout=2
            )
            r.ping()
            
            return {
                "status": "healthy",
                "message": "Redis is accessible",
            }
        except Exception as e:
            logger.warning(f"Redis health check failed: {e}")
            return {
                "status": "degraded",
                "message": str(e),
            }


# Global health checker instance
health_checker = HealthChecker()
