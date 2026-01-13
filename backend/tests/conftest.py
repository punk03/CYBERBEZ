"""Pytest configuration and fixtures."""

import pytest
from typing import Generator
from fastapi.testclient import TestClient

from backend.api.main import app
from backend.storage.database import SessionLocal, Base, engine


@pytest.fixture(scope="function")
def db_session() -> Generator:
    """Create database session for testing."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client() -> Generator:
    """Create test client."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def sample_log_entry():
    """Sample log entry for testing."""
    return {
        "timestamp": "2024-01-01T12:00:00Z",
        "source": "test",
        "host": "test-host",
        "service": "test-service",
        "level": "INFO",
        "message": "Test log message",
        "raw": "Test log message",
        "metadata": {},
    }


@pytest.fixture
def sample_threat_detection():
    """Sample threat detection for testing."""
    return {
        "attack_type": "ddos",
        "detector": "ddos_detector",
        "source_ip": "192.168.1.100",
        "severity": "high",
        "confidence": 0.85,
    }
