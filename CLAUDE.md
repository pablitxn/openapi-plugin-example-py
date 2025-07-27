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

# Alternative port (matches Dockerfile)
poetry run uvicorn main:app --reload --host 0.0.0.0 --port 4260
```

### Testing
```bash
# Run all tests
poetry run pytest

# Run tests with coverage
poetry run pytest --cov=src
poetry run pytest --cov=src --cov-report=html

# Run specific test file
poetry run pytest tests/test_create_plot.py

# Run tests with verbose output
poetry run pytest tests/unit/test_create_plot.py -v
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

# Run with full environment
docker run -p 8000:8000 \
  -e clientSecret=$clientSecret \
  -e ENVIRONMENT=development \
  example-plugin
```

## Architecture Overview

This is an OpenAPI plugin following Clean Architecture with the Command/Handler pattern using the `openapi-plugin-common-py` library.

### Architecture Layers

1. **API Layer** (`src/openapi_plugin_example_py/api/`)
   - Controllers handle HTTP endpoints and route to handlers
   - Middlewares provide cross-cutting concerns (telemetry, auth)
   - All endpoints except `/health` require JWT authentication

2. **Business Logic Layer** (`src/openapi_plugin_example_py/business_logic/`)
   - Commands encapsulate business logic with built-in telemetry
   - Handlers mediate between HTTP requests and commands
   - Request/Response models define API contracts
   - Commands inherit from `CommandBase[TContext, TOptions]`

3. **Infrastructure Layer** (`src/openapi_plugin_example_py/infrastructure/`)
   - External service integrations (Azure Blob, OpenAI, Redis)
   - Security handles JWT validation with Azure AD
   - Command factory creates commands with dependency injection

### Key Patterns

#### Command Pattern Implementation
All business logic is encapsulated in commands that:
- Inherit from `CommandBase[TContext, TOptions]` 
- Implement `execute_command_async(context: TContext)`
- Store results in `context.metadata` dictionary
- Have automatic telemetry and error handling
- Are created via the command factory with dependencies injected

Example command structure:
```python
class MyCommand(CommandBase[MyContext, MyOptions]):
    async def execute_command_async(self, context: MyContext) -> None:
        # Business logic here
        context.metadata["result"] = result
```

#### Handler Pattern
Handlers manage the flow between controllers and commands:
- Inherit from `BasePluginHandler`
- Transform requests into command contexts
- Execute commands via invoker
- Extract results from context metadata
- Handle timing and telemetry

#### Authentication Flow
- Fixed tenant ID: `5b973f99-77df-4beb-b27d-aa0c70b8482c`
- JWT tokens validated against Azure AD
- Required headers: `Authorization: Bearer <token>`, `x-chat-id`, `x-agent-id`
- Development bypass: Set `BYPASS_AUTH=true`

### Adding New Endpoints

1. Create request/response models in `business_logic/requests/` and `business_logic/responses/`
2. Create command in `business_logic/commands/` inheriting from `CommandBase`
3. Create handler in `business_logic/handlers/` inheriting from `BasePluginHandler`
4. Register handler in `infrastructure/service_registration.py`
5. Add route in `api/controllers/plugin_controller.py`
6. Update OpenAPI spec in `openapi-spec.yaml`

### Environment Configuration

#### Required Environment Variables
```bash
# Development mode
export ENVIRONMENT=development
export BYPASS_AUTH=true
export USE_FILESYSTEM_STORAGE=true
export FILESYSTEM_STORAGE_PATH=./mock_storage

# Production mode
export clientSecret="your-client-secret"
export APPLICATIONINSIGHTS_CONNECTION_STRING="..."
export AZURE_STORAGE_CONNECTION_STRING="..."
export OPENAI_API_KEY="..."
```

#### Configuration Files
- `appsettings.json` - Base configuration
- `appsettings.Development.json` - Development overrides
- Settings loaded via `config/settings.py` extending `PluginBaseSettings`

### Service Dependencies

The command factory (`CustomCommandInvokerFactory`) injects these services:
- **Cache Service**: Redis or mock implementation
- **Blob Service**: Azure Storage or filesystem fallback
- **LLM Service**: Azure OpenAI preferred, falls back to OpenAI
- **Telemetry Service**: Application Insights integration

### Important Implementation Details

1. **Metadata Pattern**: Commands don't return values directly; they store results in `context.metadata`

2. **Dual LLM Support**: Automatically uses Azure OpenAI if configured, otherwise standard OpenAI

3. **Service Fallbacks**: 
   - Cache failures don't break requests
   - Blob storage falls back to filesystem in development
   - Missing services handled gracefully

4. **Request Base Class**: All requests inherit from `RequestBase` with standard headers

5. **Command Wrapping**: Commands can be wrapped with `LoggedCommandWrapper` when `COMMAND_LOGGING=true`

6. **Lifespan Management**: `ExamplePluginLifespanManager` handles startup/shutdown in correct order

### Local Development Setup

```bash
# Initial setup
git clone <repo>
cd openapi-plugin-example-py
poetry install
cp .env.example .env
mkdir -p ./mock_storage

# Start development
poetry run uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Before committing
poetry run black src tests
poetry run ruff check src tests
poetry run mypy src
poetry run pytest --cov=src
```

### Working with the Common Library

This project depends on a local `openapi-plugin-common-py` library at `/home/pablitxn/repos/openapi-plugin-common-py`. The library is installed in editable mode, so changes to it are immediately available.

The common library provides:
- Base classes for commands, handlers, and controllers
- Common telemetry and logging infrastructure
- Authentication middleware
- Azure service integrations
- Base configuration management