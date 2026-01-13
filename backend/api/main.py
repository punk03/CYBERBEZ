"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.common.config import settings
from backend.common.logging import setup_logging
from backend.api.routers import health, logs, threats, automation, alerts, metrics
from backend.processing.kafka_client import kafka_client
from backend.processing.log_processor_worker import log_processor_worker

# Setup logging
setup_logging(settings.LOG_LEVEL)

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Система анализа логов и защиты энергосистем",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix=settings.API_PREFIX, tags=["health"])
app.include_router(logs.router, prefix=settings.API_PREFIX, tags=["logs"])
app.include_router(threats.router, prefix=settings.API_PREFIX, tags=["threats"])
app.include_router(automation.router, prefix=settings.API_PREFIX, tags=["automation"])
app.include_router(alerts.router, prefix=settings.API_PREFIX, tags=["alerts"])
app.include_router(metrics.router, tags=["metrics"])  # No prefix for Prometheus compatibility


@app.on_event("startup")
async def startup_event():
    """Startup event handler."""
    print(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"Environment: {settings.APP_ENV}")
    print(f"API available at: http://{settings.API_HOST}:{settings.API_PORT}{settings.API_PREFIX}")
    
    # Start Kafka producer
    await kafka_client.start_producer()
    
    # Start log processor worker
    await log_processor_worker.start()


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event handler."""
    print(f"Shutting down {settings.APP_NAME}")
    
    # Stop log processor worker
    await log_processor_worker.stop()
    
    # Stop Kafka producer
    await kafka_client.stop_producer()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.api.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
    )
