"""Unit tests for plugin controller."""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch

from src.openapi_plugin_example_py.api.controllers.plugin_controller import router
from src.openapi_plugin_example_py.business_logic.requests import (
    AISampleRequest,
    AISampleResponse,
    BlobSampleRequest,
    BlobSampleResponse,
    CreatePlotRequest,
    CreatePlotResponse,
    SampleResponse
)


class TestPluginController:
    """Test suite for plugin controller."""

    @pytest.fixture
    def mock_handlers(self):
        """Create mock handlers."""
        return {
            'sample_handler': AsyncMock(),
            'ai_sample_handler': AsyncMock(),
            'blob_sample_handler': AsyncMock(),
            'create_plot_handler': AsyncMock()
        }

    @pytest.fixture
    def app(self, mock_handlers):
        """Create a test FastAPI app."""
        app = FastAPI()
        app.include_router(router, prefix="/api/plugin/ExamplePlugin/v1")
        
        # Override dependencies
        from src.openapi_plugin_example_py.api.extensions.dependency_injection import (
            get_sample_handler,
            get_ai_sample_handler,
            get_blob_sample_handler,
            get_create_plot_handler
        )
        
        app.dependency_overrides[get_sample_handler] = lambda: mock_handlers['sample_handler']
        app.dependency_overrides[get_ai_sample_handler] = lambda: mock_handlers['ai_sample_handler']
        app.dependency_overrides[get_blob_sample_handler] = lambda: mock_handlers['blob_sample_handler']
        app.dependency_overrides[get_create_plot_handler] = lambda: mock_handlers['create_plot_handler']
        
        return app

    @pytest.fixture
    def client(self, app):
        """Create a test client."""
        return TestClient(app)

    def test_sample_endpoint_success(self, client, mock_handlers):
        """Test sample endpoint with successful response."""
        # Arrange
        mock_response = SampleResponse(
            sample_response="Processed: TEST INPUT",
            cached=False,
            processing_time_ms=100.5
        )
        mock_handlers['sample_handler'].handle_async.return_value = mock_response

        # Act
        response = client.get(
            "/api/plugin/ExamplePlugin/v1/sample",
            params={"sample_input": "test input", "use_cache": True},
            headers={
                "x-chat-id": "test-chat-123",
                "x-agent-id": "test-agent",
                "x-agent-version": "1.0.0"
            }
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["sampleResponse"] == "Processed: TEST INPUT"
        assert data["cached"] is False
        assert data["processingTimeMs"] == 100.5

        # Verify handler was called
        mock_handlers['sample_handler'].handle_async.assert_called_once()
        call_args = mock_handlers['sample_handler'].handle_async.call_args[0][0]
        assert call_args.sample_input == "test input"
        assert call_args.use_cache is True
        assert call_args.chat_id == "test-chat-123"

    def test_sample_endpoint_validation_error(self, client):
        """Test sample endpoint with validation error."""
        # Act - empty sample_input
        response = client.get(
            "/api/plugin/ExamplePlugin/v1/sample",
            params={"sample_input": ""},  # Empty string
            headers={"x-chat-id": "test-chat"}
        )

        # Assert
        assert response.status_code == 422  # Validation error

    def test_ai_sample_endpoint_success(self, client, mock_handlers):
        """Test AI sample endpoint with successful response."""
        # Arrange
        mock_response = AISampleResponse(
            ai_response="Generated AI response",
            model_used="gpt-4",
            tokens_used=150,
            cached=False
        )
        mock_handlers['ai_sample_handler'].handle_async.return_value = mock_response

        request_body = {
            "samplePrompt": "Generate something",
            "useAi": True,
            "validateSchema": True
        }

        # Act
        response = client.post(
            "/api/plugin/ExamplePlugin/v1/ai-sample",
            json=request_body,
            headers={
                "x-chat-id": "test-chat-123",
                "x-agent-id": "test-agent",
                "x-agent-version": "1.0.0"
            }
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["aiResponse"] == "Generated AI response"
        assert data["modelUsed"] == "gpt-4"
        assert data["tokensUsed"] == 150
        assert data["cached"] is False

    def test_blob_sample_endpoint_success(self, client, mock_handlers):
        """Test blob sample endpoint with successful response."""
        # Arrange
        mock_response = BlobSampleResponse(
            blob_url="https://storage.azure.com/files/test.pdf",
            file_size=1024,
            container="uploaded-files",
            upload_time_ms=250.0
        )
        mock_handlers['blob_sample_handler'].handle_async.return_value = mock_response

        request_body = {
            "fileName": "test.pdf",
            "fileContentBase64": "VGVzdCBjb250ZW50",  # "Test content" in base64
            "containerName": "uploaded-files"
        }

        # Act
        response = client.post(
            "/api/plugin/ExamplePlugin/v1/blob-sample",
            json=request_body,
            headers={
                "x-chat-id": "test-chat-123",
                "x-agent-id": "test-agent",
                "x-agent-version": "1.0.0"
            }
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["blobUrl"] == "https://storage.azure.com/files/test.pdf"
        assert data["fileSize"] == 1024
        assert data["container"] == "uploaded-files"
        assert data["uploadTimeMs"] == 250.0

    def test_create_plot_endpoint_success(self, client, mock_handlers):
        """Test create plot endpoint with successful response."""
        # Arrange
        mock_response = CreatePlotResponse(
            plot_url="https://storage.azure.com/plots/test-plot.png",
            plot_type="bar",
            file_name="test-plot.png",
            processing_time_ms=500.0,
            data_points=100
        )
        mock_handlers['create_plot_handler'].handle_async.return_value = mock_response

        request_body = {
            "excelUrl": "https://storage.azure.com/data/test.xlsx",
            "plotType": "bar",
            "xColumn": "Month",
            "yColumn": "Sales",
            "title": "Monthly Sales"
        }

        # Act
        response = client.post(
            "/api/plugin/ExamplePlugin/v1/create-plot",
            json=request_body,
            headers={
                "x-chat-id": "test-chat-123",
                "x-agent-id": "test-agent",
                "x-agent-version": "1.0.0"
            }
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["plotUrl"] == "https://storage.azure.com/plots/test-plot.png"
        assert data["plotType"] == "bar"
        assert data["fileName"] == "test-plot.png"
        assert data["processingTimeMs"] == 500.0
        assert data["dataPoints"] == 100

    def test_endpoint_with_missing_headers(self, client, mock_handlers):
        """Test endpoint behavior with missing headers."""
        # Arrange
        mock_response = SampleResponse(
            sample_response="Response",
            cached=False,
            processing_time_ms=50.0
        )
        mock_handlers['sample_handler'].handle_async.return_value = mock_response

        # Act - no headers provided
        response = client.get(
            "/api/plugin/ExamplePlugin/v1/sample",
            params={"sample_input": "test"}
        )

        # Assert
        assert response.status_code == 200
        
        # Verify empty string defaults were used
        call_args = mock_handlers['sample_handler'].handle_async.call_args[0][0]
        assert call_args.chat_id == ""
        assert call_args.agent_id == ""
        assert call_args.agent_version == ""

    def test_ai_sample_header_override(self, client, mock_handlers):
        """Test that headers override request body values."""
        # Arrange
        mock_response = AISampleResponse(
            ai_response="Response",
            model_used="gpt-4",
            tokens_used=50,
            cached=False
        )
        mock_handlers['ai_sample_handler'].handle_async.return_value = mock_response

        request_body = {
            "samplePrompt": "Test",
            "useAi": True,
            "chatId": "body-chat-id",
            "agentId": "body-agent-id",
            "agentVersion": "body-version"
        }

        # Act
        response = client.post(
            "/api/plugin/ExamplePlugin/v1/ai-sample",
            json=request_body,
            headers={
                "x-chat-id": "header-chat-id",
                "x-agent-id": "header-agent-id",
                "x-agent-version": "header-version"
            }
        )

        # Assert
        assert response.status_code == 200
        
        # Verify headers took precedence
        call_args = mock_handlers['ai_sample_handler'].handle_async.call_args[0][0]
        assert call_args.chat_id == "header-chat-id"
        assert call_args.agent_id == "header-agent-id"
        assert call_args.agent_version == "header-version"

    def test_sample_endpoint_query_parameters(self, client, mock_handlers):
        """Test sample endpoint query parameter handling."""
        # Arrange
        mock_response = SampleResponse(
            sample_response="Response",
            cached=True,
            processing_time_ms=10.0
        )
        mock_handlers['sample_handler'].handle_async.return_value = mock_response

        # Act - test with use_cache=false
        response = client.get(
            "/api/plugin/ExamplePlugin/v1/sample",
            params={"sample_input": "test input", "use_cache": False}
        )

        # Assert
        assert response.status_code == 200
        
        # Verify use_cache was properly parsed
        call_args = mock_handlers['sample_handler'].handle_async.call_args[0][0]
        assert call_args.use_cache is False

    def test_long_sample_input_validation(self, client):
        """Test sample endpoint with input exceeding max length."""
        # Act - input longer than 1000 characters
        long_input = "x" * 1001
        response = client.get(
            "/api/plugin/ExamplePlugin/v1/sample",
            params={"sample_input": long_input}
        )

        # Assert
        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_handler_exception_propagation(self, client, mock_handlers):
        """Test that handler exceptions are properly propagated."""
        # Arrange
        mock_handlers['sample_handler'].handle_async.side_effect = Exception("Handler error")

        # Act
        response = client.get(
            "/api/plugin/ExamplePlugin/v1/sample",
            params={"sample_input": "test"}
        )

        # Assert
        assert response.status_code == 500  # Internal server error