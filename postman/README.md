# Postman Collection for OpenAPI Plugin Example

This directory contains Postman collection and environment files to test all endpoints of the OpenAPI Plugin Example.

## Files

- `OpenAPI_Plugin_Example.postman_collection.json` - Main collection with all endpoints
- `OpenAPI_Plugin_Example.postman_environment.json` - Environment variables for development
- `sample-data/` - Sample files for testing upload endpoints

## Setup

1. **Import Collection and Environment**
   - Open Postman
   - Import `OpenAPI_Plugin_Example.postman_collection.json`
   - Import `OpenAPI_Plugin_Example.postman_environment.json`
   - Select "OpenAPI Plugin Example - Development" as your environment

2. **Configure Environment Variables**
   - `base_url`: Default is `http://localhost:8000`
   - `client_id`: Your Azure AD application client ID
   - `jwt_token`: You'll need to obtain this using Azure AD authentication

3. **Obtain JWT Token**
   
   Use Azure CLI or MSAL to get a token:
   ```bash
   # Using Azure CLI
   az account get-access-token --resource api://your-client-id
   ```

   Or use the MSAL Python script:
   ```python
   from msal import ConfidentialClientApplication
   
   app = ConfidentialClientApplication(
       client_id="your-client-id",
       client_credential="your-client-secret",
       authority="https://login.microsoftonline.com/5b973f99-77df-4beb-b27d-aa0c70b8482c"
   )
   
   result = app.acquire_token_for_client(scopes=["api://your-client-id/.default"])
   print(result["access_token"])
   ```

## Endpoints

### 1. Health Check (No Auth)
- **GET** `/health`
- No authentication required
- Returns service health status

### 2. Sample Endpoint
- **GET** `/api/plugin/ExamplePlugin/v1/sample`
- Query params: `sample_input` (required), `use_cache` (optional)
- Headers: `Authorization`, `x-chat-id`, `x-agent-id`

### 3. AI Sample Endpoint
- **POST** `/api/plugin/ExamplePlugin/v1/ai-sample`
- Body: JSON with `sample_prompt`, `temperature`, `max_tokens`
- Headers: `Authorization`, `x-chat-id`

### 4. Blob Upload Endpoint
- **POST** `/api/plugin/ExamplePlugin/v1/blob-sample`
- Body: JSON with `file_name`, `file_content_base64`
- Headers: `Authorization`, `x-chat-id`
- Example includes a base64-encoded test PDF

### 5. Create Plot Endpoint
- **POST** `/api/plugin/ExamplePlugin/v1/create-plot`
- Body: JSON with plot configuration
- Headers: `Authorization`, `x-chat-id`
- Creates plots from Excel data in blob storage

## Testing Flow

1. Start with Health Check to ensure service is running
2. Set your JWT token in the environment
3. Test Sample endpoint with simple text
4. Try AI Sample with different prompts
5. Upload a test file using Blob Upload
6. Create plots from Excel data

## Common Issues

- **401 Unauthorized**: Check JWT token is valid and not expired
- **422 Validation Error**: Check request body/params match schema
- **500 Internal Server Error**: Check logs and ensure all services are configured

## Pre-request Scripts

The collection includes pre-request scripts that can be customized for:
- Automatic token refresh
- Dynamic variable generation
- Request validation

## Tests

Each request includes basic tests:
- Status code validation
- Response time checks
- Schema validation (can be added)