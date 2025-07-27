#!/bin/bash
# Development server startup script

echo "Starting OpenAPI Plugin Example in development mode..."

# Load environment variables from .env file
export $(grep -v '^#' .env | xargs)

# Ensure mock storage directories exist
mkdir -p ./mock_storage/dev-uploads
mkdir -p ./mock_storage/plots

# Run the development server
poetry run uvicorn main:app --reload --host 0.0.0.0 --port 8000