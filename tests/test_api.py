from fastapi.testclient import TestClient
import pytest

# We import the main app instance for controller testing
from app.main import app


def test_health_check_endpoint():
    """Verify that the health diagnostics endpoint is active and returns status 200."""
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert "PalmMind" in data["service"]
