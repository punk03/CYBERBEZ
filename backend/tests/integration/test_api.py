"""Integration tests for API."""

import pytest
from fastapi.testclient import TestClient


class TestHealthEndpoint:
    """Tests for health endpoint."""
    
    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "checks" in data


class TestLogsEndpoint:
    """Tests for logs endpoint."""
    
    def test_send_log(self, client):
        """Test sending log via API."""
        response = client.post(
            "/api/v1/logs",
            json={
                "log": '{"message": "test", "level": "INFO"}',
                "source": "test",
                "format": "json"
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
    
    def test_get_logs(self, client):
        """Test getting logs."""
        response = client.get("/api/v1/logs?limit=10")
        assert response.status_code == 200
        data = response.json()
        assert "logs" in data
        assert "total" in data
