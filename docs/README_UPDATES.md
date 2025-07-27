# README Updates for GenEY Compliance

The following features have been added to comply with the GenEY design guide:

## New Features Added

1. **JWT Authentication with Fixed Tenant**
   - Azure AD tenant ID: `5b973f99-77df-4beb-b27d-aa0c70b8482c`
   - Implemented in common package with plugin-specific configuration

2. **GenEY API Integration**
   - Access files uploaded in chat sessions
   - On-Behalf-Of flow for authentication
   - File streaming support for large files

3. **File Type Validation**
   - Validates against GenEY supported file types
   - Configurable allowed types per plugin
   - Default types: pdf, txt, docx, json, csv, xlsx

4. **Contract-First API Development**
   - OpenAPI specification must be approved before implementation
   - Detailed documentation for LLM understanding
   - See [Contract-First Development Guide](./CONTRACT_FIRST_DEVELOPMENT.md)

5. **Pipeline Integration**
   - Documentation for GenEY deployment pipeline
   - Azure DevOps integration
   - See [Pipeline Integration Guide](./PIPELINE_INTEGRATION.md)

## Configuration Updates

Added to `appsettings.json`:
```json
"security": {
  "tenant_id": "5b973f99-77df-4beb-b27d-aa0c70b8482c",
  "client_id": "${CLIENT_ID}",
  "api_audience": "api://${CLIENT_ID}",
  "client_secret": "${clientSecret}",
  "geney_client_id": "${GENEY_CLIENT_ID}",
  "geney_api_domain": "${GENEY_API_DOMAIN}"
}
```

## Environment Variables

New required variables:
- `clientSecret` - For authentication (provided by GenEY team for dev/qa)
- `GENEY_CLIENT_ID` - GenEY API client ID
- `GENEY_API_DOMAIN` - GenEY API base URL

## Usage Examples

### Using @requires_auth Decorator

```python
from openapi_plugin_example_py.infrastructure.security import requires_auth

@requires_auth
async def my_secure_function(token: str, data: dict):
    # Function implementation
    pass
```

### Accessing Chat Files

```python
from openapi_plugin_example_py.infrastructure.security import GenEYClient

# Initialize client
client = GenEYClient()

# Get file from chat
file_content = await client.get_file_from_chat_validated(
    chat_id="chat-123",
    file_name="document.pdf",
    user_token=auth_token
)
```

### File Type Validation

```python
from openapi_plugin_example_py.infrastructure.file_validation import FileTypeValidator

# Create validator with custom allowed types
validator = FileTypeValidator(["pdf", "docx", "xlsx"])

# Validate file
if validator.is_valid("report.pdf"):
    # Process file
    pass
```

## Documentation

- [Contract-First Development](./CONTRACT_FIRST_DEVELOPMENT.md)
- [Pipeline Integration](./PIPELINE_INTEGRATION.md)
- [OpenAPI Specification](../openapi-spec.yaml)