# OpenAPI Plugin Example - Python Template

A production-ready template for building enterprise-grade OpenAPI plugins using Python, FastAPI, and Azure services. This template demonstrates best practices, design patterns, and architectural decisions for creating scalable, maintainable, and secure plugins.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Design Patterns](#design-patterns)
- [Getting Started](#getting-started)
- [Project Structure](#project-structure)
- [Core Features](#core-features)
- [Creating Your Own Plugin](#creating-your-own-plugin)
- [Configuration](#configuration)
- [Development Workflow](#development-workflow)
- [Testing Strategy](#testing-strategy)
- [Deployment](#deployment)
- [Security Considerations](#security-considerations)
- [Contributing](#contributing)
- [Support and Resources](#support-and-resources)

## Overview

This template provides a complete implementation of an OpenAPI plugin that follows enterprise software development best practices. It leverages the [`openapi-plugin-common-py`](../openapi-plugin-common-py) library to provide standardized patterns and utilities across all plugins in your organization.

### Key Benefits

- **Standardized Architecture**: Consistent structure across all plugins
- **Enterprise Security**: Azure AD authentication with JWT validation
- **Production Ready**: Built-in telemetry, error handling, and monitoring
- **Type Safety**: Full type hints and Pydantic validation
- **Testable**: Comprehensive testing patterns and utilities
- **Scalable**: Async/await support with proper resource management

### Target Audience

This template is designed for:
- **Development Teams** building microservices and APIs
- **Platform Engineers** establishing organizational standards
- **Security Teams** requiring compliant authentication patterns
- **DevOps Engineers** needing observable and deployable services

## Architecture

### Layered Architecture

The plugin follows a clean architecture approach with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────┐
│                        API Layer                             │
│  (Controllers, Middleware, OpenAPI Spec)                    │
├─────────────────────────────────────────────────────────────┤
│                   Business Logic Layer                       │
│  (Commands, Handlers, Request/Response Models)              │
├─────────────────────────────────────────────────────────────┤
│                  Infrastructure Layer                        │
│  (External Services, Security, Telemetry)                   │
├─────────────────────────────────────────────────────────────┤
│                    Common Library                            │
│  (openapi-plugin-common-py: Base Classes, Utilities)        │
└─────────────────────────────────────────────────────────────┘
```

### Component Interaction Flow

```
Client Request
    ↓
Authentication Middleware (JWT Validation)
    ↓
Controller (Route Handling)
    ↓
Handler (Request Orchestration)
    ↓
Command (Business Logic)
    ↓
Infrastructure Services (Storage, AI, etc.)
    ↓
Response
```

## Design Patterns

### 1. Command Pattern

**Purpose**: Encapsulate business logic as discrete, testable units

**Implementation**:
```python
class CreatePlotCommand(CommandBase[CreatePlotCommandContext, CreatePlotOptions]):
    """
    Command encapsulates:
    - Business logic
    - Validation rules
    - Telemetry tracking
    - Error handling
    """
    async def execute_command_async(self, context: CreatePlotCommandContext) -> CreatePlotResult:
        # Business logic here
        pass
```

**Benefits**:
- Single Responsibility Principle
- Easy unit testing
- Automatic telemetry
- Consistent error handling

### 2. Handler Pattern

**Purpose**: Mediate between HTTP requests and business commands

**Implementation**:
```python
class CreatePlotHandler(BaseHandler):
    """
    Handler responsibilities:
    - Request validation
    - Command creation
    - Response mapping
    - Error transformation
    """
    async def handle_async(self, request: CreatePlotRequest) -> CreatePlotResponse:
        command = self._command_factory.create_plot_command(request)
        result = await command.execute_async()
        return self._map_to_response(result)
```

**Benefits**:
- Decouples HTTP concerns from business logic
- Centralized request/response mapping
- Consistent error handling

### 3. Factory Pattern

**Purpose**: Centralize object creation with dependency injection

**Implementation**:
```python
class CommandFactory:
    """
    Factory provides:
    - Dependency injection
    - Configuration management
    - Service instantiation
    - Lifecycle management
    """
    def create_plot_command(self, options: CreatePlotOptions) -> CreatePlotCommand:
        return CreatePlotCommand(
            options=options,
            blob_service=self._blob_service,
            llm_provider=self._llm_provider,
            logger=self._logger
        )
```

**Benefits**:
- Loose coupling
- Testability (easy mocking)
- Configuration flexibility

### 4. Repository Pattern

**Purpose**: Abstract data access operations

**Implementation**:
```python
class FileRepository:
    """
    Repository abstracts:
    - Storage implementation
    - Data access patterns
    - Caching strategies
    """
    async def save_file(self, file: FileModel) -> str:
        # Implementation agnostic storage
        pass
```

**Benefits**:
- Storage abstraction
- Testable data access
- Easy to switch implementations

### 5. Middleware Pattern

**Purpose**: Cross-cutting concerns (auth, telemetry, errors)

**Implementation**:
- Authentication Middleware: JWT validation
- Telemetry Middleware: Request/response tracking
- Error Middleware: Consistent error responses

### 6. Dependency Injection

**Purpose**: Manage dependencies and configuration

**Implementation**:
- Constructor injection for services
- Configuration injection via settings
- Lifetime management via FastAPI

## Getting Started

### Prerequisites

- Python 3.9+
- Poetry (dependency management)
- Azure subscription (for Azure services)
- Docker (optional, for containerization)

### Quick Start

1. **Clone the Template**
   ```bash
   git clone https://github.com/your-org/openapi-plugin-example-py.git my-plugin
   cd my-plugin
   ```

2. **Install Dependencies**
   ```bash
   poetry install
   ```

3. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

   Keep real credentials in your local `.env` or inject them at runtime. Git and
   Docker exclude private `.env` files; only the sanitized `.env.example` belongs
   in the repository. Container deployments must supply their settings at runtime,
   for example with `docker run --env-file /path/to/private.env ...`. Do not use
   the development authentication bypass in production. OpenAI remains optional.

   If a credential was previously committed, revoke or rotate it with its provider;
   deleting the file does not invalidate copies in Git history or existing images.

4. **Run Development Server**
   ```bash
   poetry run uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

5. **Run Tests**
   ```bash
   poetry run pytest
   ```

## Project Structure

```
openapi-plugin-example-py/
├── src/openapi_plugin_example_py/
│   ├── api/                      # API Layer
│   │   ├── controllers/          # Route handlers
│   │   ├── middleware/           # Cross-cutting concerns
│   │   └── dependencies.py       # FastAPI dependencies
│   │
│   ├── business_logic/           # Business Layer
│   │   ├── commands/             # Business logic units
│   │   ├── handlers/             # Request handlers
│   │   ├── requests/             # Request DTOs
│   │   └── responses/            # Response DTOs
│   │
│   ├── infrastructure/           # Infrastructure Layer
│   │   ├── azure_blob/           # Azure Blob Storage
│   │   ├── llm/                  # LLM integrations
│   │   ├── security/             # Authentication
│   │   └── telemetry/            # Monitoring
│   │
│   └── config/                   # Configuration
│       ├── settings.py           # Settings management
│       └── constants.py          # Application constants
│
├── tests/                        # Test Suite
│   ├── unit/                     # Unit tests
│   ├── integration/              # Integration tests
│   └── fixtures/                 # Test fixtures
│
├── deployment/                   # Deployment Configs
│   ├── Dockerfile               # Container definition
│   ├── docker-compose.yml       # Local development
│   └── kubernetes/              # K8s manifests
│
├── docs/                        # Documentation
│   ├── API.md                   # API documentation
│   ├── ARCHITECTURE.md          # Architecture details
│   └── DEPLOYMENT.md            # Deployment guide
│
├── openapi-spec.yaml            # OpenAPI specification
├── pyproject.toml               # Poetry configuration
├── CLAUDE.md                    # AI assistant instructions
└── README.md                    # This file
```

## Core Features

### 1. Authentication & Authorization

- **Azure AD Integration**: Enterprise-grade authentication
- **JWT Validation**: Secure token validation
- **Scope-Based Authorization**: Fine-grained access control
- **Multi-Tenant Support**: Isolated tenant operations

### 2. Command Processing

- **Async Command Execution**: Non-blocking operations
- **Automatic Telemetry**: Built-in performance tracking
- **Validation**: Input validation with Pydantic
- **Error Handling**: Structured error responses

### 3. External Service Integration

- **Azure Blob Storage**: Secure file operations
- **OpenAI/Azure OpenAI**: LLM capabilities
- **Redis Cache**: Performance optimization
- **HTTP Clients**: Resilient external API calls

### 4. Observability

- **Structured Logging**: Consistent log format
- **Distributed Tracing**: Request flow tracking
- **Metrics Collection**: Performance monitoring
- **Health Checks**: Service availability

## Creating Your Own Plugin

### Step 1: Fork the Template

```bash
# Clone the template
git clone https://github.com/your-org/openapi-plugin-example-py.git my-awesome-plugin
cd my-awesome-plugin

# Remove template history
rm -rf .git
git init

# Update project name in pyproject.toml
sed -i 's/openapi-plugin-example-py/my-awesome-plugin/g' pyproject.toml
```

### Step 2: Define Your Business Logic

1. **Create Command Models**
   ```python
   # src/my_plugin/business_logic/commands/my_command.py
   from openapi_plugin_common.commands import CommandBase
   
   class MyCommandOptions(BaseModel):
       # Define your command inputs
       pass
   
   class MyCommand(CommandBase[CommandContext, MyCommandOptions]):
       async def execute_command_async(self, context: CommandContext):
           # Implement your business logic
           pass
   ```

2. **Create Request/Response Models**
   ```python
   # src/my_plugin/business_logic/requests/my_request.py
   from openapi_plugin_common.http import RequestBase
   
   class MyRequest(RequestBase):
       # Define request structure
       pass
   ```

3. **Implement Handler**
   ```python
   # src/my_plugin/business_logic/handlers/my_handler.py
   from openapi_plugin_common.handlers import BaseHandler
   
   class MyHandler(BaseHandler):
       async def handle_async(self, request: MyRequest) -> MyResponse:
           # Handle request
           pass
   ```

### Step 3: Wire Up the API

1. **Add Controller Route**
   ```python
   # src/my_plugin/api/controllers/plugin_controller.py
   @router.post("/my-endpoint")
   async def my_endpoint(
       request: MyRequest,
       handler: MyHandler = Depends(get_my_handler)
   ):
       return await handler.handle_async(request)
   ```

2. **Update OpenAPI Spec**
   ```yaml
   # openapi-spec.yaml
   paths:
     /my-endpoint:
       post:
         summary: My endpoint description
         # ... specification details
   ```

### Step 4: Add Tests

1. **Unit Tests**
   ```python
   # tests/unit/test_my_command.py
   async def test_my_command_success():
       # Test command logic
       pass
   ```

2. **Integration Tests**
   ```python
   # tests/integration/test_my_endpoint.py
   async def test_my_endpoint_e2e():
       # Test full request flow
       pass
   ```

### Step 5: Configure Dependencies

Update `pyproject.toml` with any additional dependencies your plugin requires.

## Configuration

### Environment Variables

```bash
# Authentication
AZURE_TENANT_ID=5b973f99-77df-4beb-b27d-aa0c70b8482c
AZURE_CLIENT_ID=your-client-id
clientSecret=your-client-secret

# Azure Services
AZURE_STORAGE_CONNECTION_STRING=your-connection-string
APPLICATIONINSIGHTS_CONNECTION_STRING=your-app-insights

# OpenAI
OPENAI_API_KEY=your-api-key
# OR Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
AZURE_OPENAI_API_KEY=your-key

# Application
ENVIRONMENT=development
LOG_LEVEL=INFO
```

### Configuration Files

- `appsettings.json`: Base configuration
- `appsettings.{Environment}.json`: Environment-specific overrides
- `config/settings.py`: Settings management

## Development Workflow

### 1. Local Development

```bash
# Install dependencies
poetry install

# Run with hot reload
poetry run uvicorn main:app --reload

# Run specific environment
ENVIRONMENT=development poetry run uvicorn main:app --reload
```

### 2. Code Quality

```bash
# Format code
poetry run black src tests

# Lint
poetry run ruff check src tests

# Type checking
poetry run mypy src
```

### 3. Testing

```bash
# All tests
poetry run pytest

# With coverage
poetry run pytest --cov=src --cov-report=html

# Specific test
poetry run pytest tests/unit/test_create_plot.py -v
```

### 4. Docker Development

```bash
# Build image
docker build -t my-plugin .

# Run container
docker-compose up

# With environment variables
docker run -p 8000:8000 \
  -e clientSecret=$clientSecret \
  -e ENVIRONMENT=development \
  my-plugin
```

## Testing Strategy

### Unit Tests

- Test individual commands in isolation
- Mock external dependencies
- Focus on business logic
- Use pytest fixtures for common setups

### Integration Tests

- Test complete request flows
- Use TestClient for API testing
- Test with real service configurations
- Validate error scenarios

### Contract Tests

- Validate OpenAPI specification
- Test request/response contracts
- Ensure backward compatibility

### Performance Tests

- Load testing with locust
- Measure command execution times
- Monitor resource usage

## Deployment

### Docker Deployment

```dockerfile
# Multi-stage build for optimization
FROM python:3.9-slim as builder
# ... build steps

FROM python:3.9-slim
# ... runtime configuration
```

### Kubernetes Deployment

```yaml
# deployment/kubernetes/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-plugin
spec:
  replicas: 3
  # ... deployment configuration
```

### CI/CD Pipeline

```yaml
# .github/workflows/deploy.yml
name: Deploy
on:
  push:
    branches: [main]
jobs:
  test:
    # ... testing steps
  deploy:
    # ... deployment steps
```

## Security Considerations

### Authentication

- All endpoints require JWT authentication (except `/health`)
- Tokens validated against Azure AD
- Token expiration enforced
- Scope-based authorization

### Data Protection

- Sensitive data encrypted at rest
- HTTPS enforced for all communications
- Secrets managed via environment variables
- No credentials in code or logs

### Input Validation

- All inputs validated with Pydantic
- File type validation for uploads
- Size limits enforced
- SQL injection prevention

### Compliance

- GDPR compliance for data handling
- Audit logging for sensitive operations
- Data retention policies
- Right to deletion support

## Contributing

### Contributing to the Template

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

### Contributing to Common Library

The `openapi-plugin-common-py` library is the foundation for all plugins. Improvements benefit all teams:

1. Discuss changes in issues first
2. Ensure backward compatibility
3. Add comprehensive tests
4. Update documentation

### Code Standards

- Follow PEP 8 style guide
- Use type hints
- Write docstrings
- Add unit tests
- Update documentation

## Support and Resources

### Documentation

- **Common Library**: [`openapi-plugin-common-py`](../openapi-plugin-common-py/README.md)
- **API Documentation**: [docs/API.md](docs/API.md)
- **Architecture Guide**: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- **Deployment Guide**: [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)

### Getting Help

- **Issues**: [GitHub Issues](https://github.com/your-org/openapi-plugin-example-py/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/openapi-plugin-example-py/discussions)
- **Wiki**: [Project Wiki](https://github.com/your-org/openapi-plugin-example-py/wiki)
- **Slack**: #plugin-development channel

### Training Resources

- Internal workshops on plugin development
- Video tutorials on common patterns
- Architecture decision records (ADRs)
- Code review guidelines

### Monitoring and Support

- **Production Monitoring**: Azure Application Insights dashboards
- **On-Call Runbook**: [wiki/on-call-runbook](wiki/on-call-runbook)
- **Incident Response**: Follow organization incident management process
- **Performance Baselines**: [docs/PERFORMANCE.md](docs/PERFORMANCE.md)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built on [`openapi-plugin-common-py`](../openapi-plugin-common-py) foundation
- Powered by [FastAPI](https://fastapi.tiangolo.com/)
- Authentication by [Azure Active Directory](https://azure.microsoft.com/services/active-directory/)
- Monitoring with [Azure Application Insights](https://azure.microsoft.com/services/monitor/)