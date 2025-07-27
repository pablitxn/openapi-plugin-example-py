# Contract-First API Development Guide

This guide explains the contract-first development approach required for GenEY plugins.

## Overview

Contract-first development means defining your API specification **before** implementing the code. This ensures:
- Clear API contracts that LLMs can understand
- Consistent API design across plugins
- Early feedback on API design
- Better documentation

## Process

### 1. Create OpenAPI Specification

**BEFORE writing any code**, create your OpenAPI specification:

1. **Create `openapi-spec.yaml`** in your repository root
2. **Define all endpoints**, parameters, and responses
3. **Document thoroughly** - this is what the LLM will read

Example structure:
```yaml
openapi: 3.0.0
info:
  title: Your Plugin API
  description: Detailed description for LLM understanding
  version: 1.0.0
paths:
  /your-endpoint:
    post:
      summary: Clear summary of what this does
      description: |
        Detailed description including:
        - What the endpoint does
        - When to use it
        - Any limitations
      parameters:
        # Document all parameters clearly
      requestBody:
        # Define request schema
      responses:
        # Define all possible responses
```

### 2. Use VS Code Extension

Install the OpenAPI extension to visualize your specification:

1. **Install Extension**: Search for "OpenAPI" in VS Code extensions
2. **Preview**: Right-click on your YAML file and select "Preview"
3. **Validate**: Ensure no errors or warnings

### 3. Submit for Review

**IMPORTANT**: The OpenAPI spec must be reviewed and approved BEFORE development:

1. **Check in the spec file** to the repository
2. **Create a Pull Request** with only the OpenAPI specification
3. **Request review** from GenEY team
4. **Wait for approval** before starting implementation

Review criteria:
- Completeness of documentation
- Appropriate parameter definitions
- Clear response schemas
- Consistency with GenEY standards

### 4. Implement Against Contract

Once approved, implement your API to match the specification exactly:

```python
from fastapi import FastAPI, Query, Header
from pydantic import BaseModel

app = FastAPI()

# Your models should match the OpenAPI schemas exactly
class YourRequest(BaseModel):
    """Must match the schema in openapi-spec.yaml"""
    field: str
    
class YourResponse(BaseModel):
    """Must match the response schema"""
    result: str

@app.post(
    "/your-endpoint",
    summary="Same as in OpenAPI spec",
    description="Same as in OpenAPI spec",
    response_model=YourResponse
)
async def your_endpoint(
    request: YourRequest,
    chat_id: str = Header(None, alias="x-chat-id")
) -> YourResponse:
    # Implementation
    pass
```

### 5. Validate Implementation

FastAPI will generate runtime OpenAPI documentation. Ensure it matches your contract:

1. **Run your application**
   ```bash
   poetry run uvicorn main:app --reload
   ```

2. **Check generated spec** at `http://localhost:8000/openapi.json`

3. **Compare** with your original `openapi-spec.yaml`

4. **Fix any discrepancies**

## Best Practices

### 1. Documentation Quality

Remember: **The LLM will read your OpenAPI spec** to understand when and how to call your API.

Good example:
```yaml
/analyze-document:
  post:
    summary: Analyze a document for tax-relevant information
    description: |
      This endpoint analyzes uploaded documents (PDF, DOCX) to extract
      tax-relevant information such as income, deductions, and entities.
      
      Use this endpoint when:
      - User uploads a tax document
      - User asks to analyze a financial document
      - User needs information extracted from a PDF or Word document
      
      The endpoint will:
      1. Download the document from blob storage
      2. Extract text and structured data
      3. Identify tax-relevant information
      4. Return structured results
```

### 2. Parameter Documentation

Document every parameter clearly:

```yaml
parameters:
  - name: document_url
    in: query
    required: true
    description: |
      URL of the document in blob storage.
      Must be a valid blob storage URL accessible by the plugin.
    schema:
      type: string
      format: uri
    example: "https://storage.blob.core.windows.net/documents/tax-form.pdf"
```

### 3. Response Examples

Provide realistic examples:

```yaml
responses:
  '200':
    description: Document successfully analyzed
    content:
      application/json:
        schema:
          $ref: '#/components/schemas/AnalysisResult'
        example:
          entities:
            - name: "John Doe"
              type: "taxpayer"
              tin: "XXX-XX-1234"
          income:
            - source: "Employment"
              amount: 75000
              year: 2023
          deductions:
            - type: "Mortgage Interest"
              amount: 12000
```

## Common Mistakes to Avoid

1. **Starting code before spec approval**
   - Always wait for contract approval
   - Changes after implementation are costly

2. **Insufficient documentation**
   - LLMs need detailed descriptions
   - Include use cases and examples

3. **Mismatched implementation**
   - FastAPI decorators must match spec
   - Response models must be identical

4. **Missing error responses**
   - Document all possible error cases
   - Include problem details format

## Validation Checklist

Before submitting for review:

- [ ] All endpoints documented
- [ ] All parameters have descriptions and examples
- [ ] All responses documented (success and errors)
- [ ] Schemas have clear property descriptions
- [ ] Examples provided for requests/responses
- [ ] No validation errors in VS Code
- [ ] Spec explains when LLM should use each endpoint

## Tools and Resources

- **OpenAPI Specification**: https://swagger.io/specification/
- **VS Code Extension**: "OpenAPI (Swagger) Editor"
- **Online Validator**: https://editor.swagger.io/
- **FastAPI OpenAPI**: https://fastapi.tiangolo.com/tutorial/metadata/

## Support

For contract review and questions:
- GenEY Development Team
- API Design Guidelines
- OpenAPI Best Practices