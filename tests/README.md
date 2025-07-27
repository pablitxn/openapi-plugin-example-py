# Test Suite Documentation

This directory contains the comprehensive test suite for the OpenAPI Plugin Example.

## Structure

```
tests/
├── unit/                           # Unit tests
│   ├── api/                       # API layer tests
│   │   └── controllers/           # Controller tests
│   ├── business_logic/            # Business logic tests
│   │   ├── commands/             # Command tests
│   │   └── handlers/             # Handler tests
│   ├── config/                    # Configuration tests
│   ├── infrastructure/            # Infrastructure tests
│   └── security/                  # Security tests
└── integration/                    # Integration tests (existing)
```

## Unit Test Coverage

### Business Logic Layer
- **Commands**: Full test coverage for all command classes
  - `test_sample_command.py`: Tests for SampleCommand including caching, telemetry, and error handling
  - `test_ai_sample_command.py`: Tests for AISampleCommand including OpenAI integration and schema validation
  - `test_blob_sample_command.py`: Tests for BlobSampleCommand including file validation and blob storage
  - `test_create_plot_command.py`: Tests for CreatePlotCommand including plot generation and Excel processing

- **Handlers**: Complete handler test coverage
  - `test_sample_handler.py`: Tests request handling and response formatting
  - `test_ai_sample_handler.py`: Tests AI request processing and option overrides
  - `test_blob_sample_handler.py`: Tests file upload handling and validation
  - `test_create_plot_handler.py`: Tests plot creation request handling

### Infrastructure Layer
- `test_filesystem_service.py`: Tests for filesystem-based blob storage
- `test_openai_service.py`: Tests for OpenAI service integration
- `test_command_factory.py`: Tests for dependency injection factory
- `test_file_validation.py`: Tests for file type validation

### API Layer
- `test_health_controller.py`: Tests for health check endpoints
- `test_plugin_controller.py`: Tests for all plugin endpoints

### Security Layer
- `test_auth.py`: Tests for JWT authentication and authorization
- `test_geney_client.py`: Tests for GenEY API client

### Configuration
- `test_settings.py`: Tests for application settings and configuration

## Running Tests

### Run all unit tests
```bash
poetry run pytest tests/unit/
```

### Run with coverage report
```bash
poetry run pytest tests/unit/ --cov=src/openapi_plugin_example_py --cov-report=html
```

### Run specific test file
```bash
poetry run pytest tests/unit/business_logic/commands/test_sample_command.py
```

### Run with verbose output
```bash
poetry run pytest tests/unit/ -v
```

## Test Patterns

The test suite follows these patterns:

1. **Fixtures**: Using pytest fixtures for mock objects and test data
2. **Mocking**: Extensive use of `unittest.mock` for external dependencies
3. **Async Testing**: Using `pytest.mark.asyncio` for async function tests
4. **Parametrized Tests**: Using `pytest.mark.parametrize` for testing multiple scenarios
5. **Exception Testing**: Verifying proper error handling and exceptions

## Key Test Features

- **Isolation**: Each test is independent and doesn't affect others
- **Mocking**: External dependencies are mocked to ensure unit test isolation
- **Coverage**: Comprehensive coverage of happy paths and error scenarios
- **Assertions**: Detailed assertions to verify behavior
- **Documentation**: Each test has a clear docstring explaining its purpose