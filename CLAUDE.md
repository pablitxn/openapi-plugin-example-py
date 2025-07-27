# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Running the Application
```bash
# Install dependencies
poetry install

# Run development server with hot reload
poetry run uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Run with specific environment
ENVIRONMENT=development poetry run uvicorn main:app --reload
```

### Testing
```bash
# Run all tests
poetry run pytest

# Run tests with coverage
poetry run pytest --cov=src

# Run specific test file
poetry run pytest tests/test_create_plot.py
```

### Code Quality
```bash
# Format code with Black
poetry run black src tests

# Lint with Ruff
poetry run ruff check src tests

# Type checking with MyPy
poetry run mypy src
```

### Docker Operations
```bash
# Build Docker image
docker build -t example-plugin --build-arg Environment=development .

# Run Docker container
docker run -p 8000:4260 -e clientSecret=$clientSecret example-plugin
```

## Architecture Overview

This is an OpenAPI plugin following the Command/Handler pattern using the `openapi-plugin-common-py` library. The architecture layers:

1. **API Layer** (`src/openapi_plugin_example_py/api/`)
   - Controllers handle HTTP endpoints and route to handlers
   - Middlewares provide cross-cutting concerns (telemetry, auth)
   - All endpoints except `/health` require JWT authentication

2. **Business Logic Layer** (`src/openapi_plugin_example_py/business_logic/`)
   - Commands encapsulate business logic with built-in telemetry
   - Handlers mediate between HTTP requests and commands
   - Request/Response models define API contracts
   - Commands inherit from `CommandBase` which provides automatic telemetry

3. **Infrastructure Layer** (`src/openapi_plugin_example_py/infrastructure/`)
   - External service integrations (Azure Blob, OpenAI, Redis)
   - Security handles JWT validation with Azure AD
   - Command factory creates commands with dependency injection

## Key Patterns

### Command Pattern Implementation
All business logic is encapsulated in commands that:
- Inherit from `CommandBase[TContext, TOptions]` 
- Implement `execute_command_async(context: TContext)`
- Have automatic telemetry and error handling
- Are created via the command factory with dependencies injected

### Authentication Flow
- Fixed tenant ID: `5b973f99-77df-4beb-b27d-aa0c70b8482c`
- JWT tokens validated against Azure AD
- Required headers: `Authorization: Bearer <token>`, `x-chat-id`, `x-agent-id`

### Adding New Endpoints
1. Create request/response models in `business_logic/requests/`
2. Create command in `business_logic/commands/`
3. Create handler in `business_logic/handlers/`
4. Add route in `api/controllers/plugin_controller.py`
5. Update OpenAPI spec in `openapi-spec.yaml`

## Environment Configuration

### Required Environment Variables
```bash
# Azure AD authentication
export clientSecret="your-client-secret"

# For production deployments
export APPLICATIONINSIGHTS_CONNECTION_STRING="..."
export AZURE_STORAGE_CONNECTION_STRING="..."
export OPENAI_API_KEY="..."
```

### Configuration Files
- `appsettings.json` - Base configuration
- `appsettings.Development.json` - Development overrides
- Settings loaded via `config/settings.py`

## Dependencies

This project depends on a local `openapi-plugin-common-py` library at `/home/pablitxn/repos/openapi-plugin-common-py` which provides:
- Base classes for commands, handlers, and controllers
- Common telemetry and logging infrastructure
- Authentication middleware
- Azure service integrations