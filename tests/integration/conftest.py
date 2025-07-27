"""Configuration for integration tests."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock
import os

# Set environment variables for testing
os.environ["BYPASS_AUTH"] = "true"
os.environ["ENVIRONMENT"] = "test"
os.environ["USE_FILESYSTEM_STORAGE"] = "true"
os.environ["FILESYSTEM_STORAGE_PATH"] = "./mock_storage"
# Disable AI services for tests
os.environ["OPENAI_API_KEY"] = ""
os.environ["AZURE_OPENAI_ENDPOINT"] = ""


@pytest.fixture
def test_client():
    """Create a test client with proper initialization."""
    # Import after setting env vars
    from main import app
    
    # Mock the LLM provider to avoid real API calls
    with patch('src.openapi_plugin_example_py.api.extensions.dependency_injection.get_llm_provider') as mock_llm:
        # Create a mock LLM provider
        mock_provider = AsyncMock()
        mock_response = MagicMock()
        mock_response.content = "AI generated response"
        mock_response.model = "gpt-4"
        mock_response.usage = {"total_tokens": 150}
        mock_provider.generate_completion.return_value = mock_response
        mock_llm.return_value = mock_provider
        
        # Create test client that will trigger lifespan
        with TestClient(app) as client:
            # Set the mock provider in app state
            if hasattr(client.app.state, 'llm_provider'):
                client.app.state.llm_provider = mock_provider
            yield client


@pytest.fixture
def mock_auth():
    """Mock authentication for tests."""
    with patch('src.openapi_plugin_example_py.infrastructure.security.auth.JWTBearer.__call__') as mock:
        mock.return_value = {"permissions": ["read", "write"]}
        yield mock