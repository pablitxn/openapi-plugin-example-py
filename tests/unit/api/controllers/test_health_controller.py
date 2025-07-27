"""Unit tests for health controller."""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch

from src.openapi_plugin_example_py.api.controllers.health_controller import router


class TestHealthController:
    """Test suite for health controller."""

    @pytest.fixture
    def app(self):
        """Create a test FastAPI app."""
        app = FastAPI()
        app.include_router(router)
        
        # Mock app state
        app.state.telemetry_service = MagicMock()
        
        return app

    @pytest.fixture
    def client(self, app):
        """Create a test client."""
        return TestClient(app)

    def test_health_check_endpoint(self, client):
        """Test health check endpoint."""
        # Arrange
        with patch('main.app', 
                   create=True) as mock_app:
            mock_app.state.telemetry_service = MagicMock()
            
            # Act
            response = client.get("/health")

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["service"] == "ExamplePlugin"
            assert data["version"] == "1.0.0"
            assert data["telemetry_enabled"] is True

    def test_health_check_without_telemetry(self, client):
        """Test health check when telemetry is disabled."""
        # Arrange
        with patch('main.app', 
                   create=True) as mock_app:
            mock_app.state.telemetry_service = None
            
            # Act
            response = client.get("/health")

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["telemetry_enabled"] is False

    def test_root_endpoint(self, client):
        """Test root endpoint."""
        # Act
        response = client.get("/")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Example Plugin API"
        assert data["docs"] == "/docs"
        assert data["openapi"] == "/openapi.json"
        assert data["health"] == "/health"

    def test_health_check_response_format(self, client):
        """Test health check response format."""
        # Arrange
        with patch('main.app', 
                   create=True) as mock_app:
            mock_app.state.telemetry_service = MagicMock()
            
            # Act
            response = client.get("/health")

            # Assert
            assert response.status_code == 200
            data = response.json()
            
            # Verify all expected fields are present
            expected_fields = ["status", "service", "version", "telemetry_enabled"]
            for field in expected_fields:
                assert field in data

    def test_root_endpoint_response_format(self, client):
        """Test root endpoint response format."""
        # Act
        response = client.get("/")

        # Assert
        assert response.status_code == 200
        data = response.json()
        
        # Verify all expected fields are present
        expected_fields = ["message", "docs", "openapi", "health"]
        for field in expected_fields:
            assert field in data

    @pytest.mark.asyncio
    async def test_health_check_async(self):
        """Test health check function directly."""
        # Arrange
        from src.openapi_plugin_example_py.api.controllers.health_controller import health_check
        
        with patch('main.app', 
                   create=True) as mock_app:
            mock_app.state.telemetry_service = MagicMock()
            
            # Act
            result = await health_check()

            # Assert
            assert result["status"] == "healthy"
            assert result["service"] == "ExamplePlugin"
            assert result["version"] == "1.0.0"
            assert result["telemetry_enabled"] is True

    @pytest.mark.asyncio
    async def test_root_async(self):
        """Test root function directly."""
        # Arrange
        from src.openapi_plugin_example_py.api.controllers.health_controller import root
        
        # Act
        result = await root()

        # Assert
        assert result["message"] == "Example Plugin API"
        assert result["docs"] == "/docs"
        assert result["openapi"] == "/openapi.json"
        assert result["health"] == "/health"