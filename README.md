# OpenAPI Plugin Example - Python

Example implementation of an OpenAPI plugin following the Command/Handler pattern, using the `openapi-plugin-common-py` library.

## Overview

This plugin demonstrates:
-  Command/Handler pattern implementation
-  JWT authentication with Azure AD
-  Integration with Azure services (Blob Storage, Application Insights)
-  OpenAI integration for AI capabilities
-  Redis caching
-  Structured logging and telemetry
-  OpenAPI specification compliance
-  Docker containerization

## Architecture

The plugin follows a clean architecture with clear separation of concerns:

```
src/openapi_plugin_example_py/
 api/                    # API Layer
    controllers/        # HTTP endpoints
    middlewares/        # HTTP middleware
    extensions/         # Dependency injection
 business_logic/         # Business Logic Layer
    commands/           # Command implementations
    handlers/           # Request handlers
    requests/           # Request/Response models
    options/            # Configuration options
 infrastructure/         # Infrastructure Layer
    blob_client/        # Azure Blob integration
    openai/             # OpenAI integration
    security/           # JWT authentication
    telemetry/          # Logging and monitoring
 config/                 # Configuration
```

## Setup

### Prerequisites

- Python 3.11+
- Poetry
- Redis (optional, for caching)
- Azure account (for blob storage and telemetry)
- OpenAI API key (for AI features)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd openapi-plugin-example-py
```

2. Install dependencies:
```bash
poetry install
```

3. Copy environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. Set the client secret:
```bash
export clientSecret="your-client-secret"
```

### Configuration

Key configuration files:
- `appsettings.json` - Base configuration
- `appsettings.Development.json` - Development overrides
- `.env` - Environment variables

## Running the Application

### Development

```bash
poetry run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Docker

Build and run:
```bash
docker build -t example-plugin --build-arg Environment=development .
docker run -p 8000:4260 -e clientSecret=$clientSecret example-plugin
```

## API Endpoints

### Health Check
```
GET /health
```
No authentication required.

### Sample Endpoint
```
GET /api/plugin/ExamplePlugin/v1/sample?sample_input=Hello
Headers:
  Authorization: Bearer <jwt-token>
  x-chat-id: chat-123
  x-agent-id: agent-456
```

### AI Sample Endpoint
```
POST /api/plugin/ExamplePlugin/v1/ai-sample
Headers:
  Authorization: Bearer <jwt-token>
  x-chat-id: chat-123
Body:
{
  "sample_prompt": "Explain quantum computing",
  "temperature": 0.7,
  "max_tokens": 1000
}
```

### Blob Upload Endpoint
```
POST /api/plugin/ExamplePlugin/v1/blob-sample
Headers:
  Authorization: Bearer <jwt-token>
  x-chat-id: chat-123
Body:
{
  "file_name": "document.pdf",
  "file_content_base64": "base64-encoded-content"
}
```

## Authentication

The plugin uses Azure AD JWT authentication:

1. Tenant ID: `5b973f99-77df-4beb-b27d-aa0c70b8482c` (fixed)
2. API Audience: `api://<your-client-id>`
3. All endpoints except `/health` require authentication

## Features

### Command Pattern
Commands encapsulate business logic with built-in telemetry:
```python
class SampleCommand(CommandBase[SampleCommandContext, ExamplePluginOptions]):
    async def execute_command_async(self, context: SampleCommandContext) -> None:
        # Business logic here
        pass
```

### Request Handlers
Handlers mediate between HTTP requests and commands:
```python
class SampleHandler(RequestHandlerBase[SampleRequest, SampleResponse]):
    async def execute_async(self, request: SampleRequest) -> SampleResponse:
        # Create command context and execute
        pass
```

### Telemetry
Automatic logging of:
- HTTP requests/responses
- Command execution
- Performance metrics
- Errors and exceptions

### Caching
Redis-based caching for improved performance:
- Configurable TTL
- Per-chat-session caching
- Automatic cache invalidation

## Testing

Run tests:
```bash
poetry run pytest
```

Run with coverage:
```bash
poetry run pytest --cov=src
```

## OpenAPI Specification

View the API documentation:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI JSON: http://localhost:8000/openapi.json

## Deployment

### Azure Container Apps

1. Build and push to Azure Container Registry:
```bash
docker build -t <acr>.azurecr.io/<repository>:tag .
docker push <acr>.azurecr.io/<repository>:tag
```

2. Deploy using Azure DevOps pipeline (contact GenEY team)

### Environment Variables

Required in production:
- `clientSecret` - Azure AD client secret
- `APPLICATIONINSIGHTS_CONNECTION_STRING` - For telemetry
- `AZURE_STORAGE_CONNECTION_STRING` - For blob storage
- `OPENAI_API_KEY` - For AI features

## Security Considerations

- Never commit secrets to the repository
- Use Azure Key Vault for production secrets
- Enable HTTPS in production
- Validate all input data
- Sanitize logs to prevent sensitive data exposure

## Monitoring

- Application Insights for telemetry
- Health endpoint for availability monitoring
- Structured logging with correlation IDs
- Performance metrics tracking

## License

[tool.poetry.dependencies]
python = "^3.11"
# Local dependency - adjust path as needed
openapi-plugin-common-py = {path = "../openapi-plugin-common-py", develop = true}
# Web framework
fastapi = "^0.109.0"
uvicorn = {extras = ["standard"], version = "^0.26.0"}
# Authentication
msal = "^1.26.0"
python-jose = {version = "^3.3.0", extras = ["cryptography"]}
# Additional dependencies
redis = "^5.0.1"
aiofiles = "^23.2.1"

[tool.poetry.group.dev.dependencies]
pytest = "^7.4.3"
pytest-asyncio = "^0.21.1"
black = "^23.11.0"
ruff = "^0.1.6"
mypy = "^1.7.1"

[build-system]
requires = ["poetry-core>=2.0.0,<3.0.0"]
build-backend = "poetry.core.masonry.api"
