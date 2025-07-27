#!/usr/bin/env python3
"""Test script for OpenAPI plugin endpoints."""
import base64
import json
import pytest
from pathlib import Path


API_PREFIX = "/api/plugin/ExamplePlugin/v1"

# Headers for requests (mock auth in development)
headers = {
    "Authorization": "Bearer mock-token",
    "x-chat-id": "test-chat-123",
    "x-agent-id": "test-agent-456",
    "x-agent-version": "1.0.0"
}


def test_health(test_client):
    """Test health endpoint."""
    print("\n=== Testing Health Endpoint ===")
    response = test_client.get("/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    assert response.status_code == 200


def test_sample(test_client):
    """Test sample endpoint."""
    print("\n=== Testing Sample Endpoint ===")
    params = {
        "sample_input": "Hello World",
        "use_cache": "false"
    }
    response = test_client.get(
        f"{API_PREFIX}/sample",
        params=params,
        headers=headers
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    assert response.status_code == 200


def test_ai_sample(test_client):
    """Test AI sample endpoint."""
    print("\n=== Testing AI Sample Endpoint ===")
    
    # Skip this test if LLM is not configured
    # The AI sample endpoint requires an LLM provider to be configured
    # which is not available in the test environment
    pytest.skip("AI service not configured for integration tests")


def test_blob_sample(test_client):
    """Test blob sample endpoint."""
    print("\n=== Testing Blob Sample Endpoint ===")
    
    # Create a test file content
    test_content = "This is a test file for blob storage."
    encoded_content = base64.b64encode(test_content.encode()).decode()
    
    data = {
        "file_name": "test_document.txt",
        "file_content_base64": encoded_content,
        "container_name": "dev-uploads",
        "metadata": {
            "description": "Test file upload",
            "uploaded_by": "test_script"
        }
    }
    response = test_client.post(
        f"{API_PREFIX}/blob-sample",
        json=data,
        headers=headers
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    assert response.status_code == 200


def test_create_plot(test_client):
    """Test create plot endpoint."""
    print("\n=== Testing Create Plot Endpoint ===")
    
    # First, create a test Excel file
    try:
        import pandas as pd
        import openpyxl
        
        # Create test data
        data = {
            'Month': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
            'Sales': [1000, 1500, 1200, 1800, 2000, 2300]
        }
        df = pd.DataFrame(data)
        
        # Save to Excel
        excel_path = Path("./mock_storage/dev-uploads/test_sales_data.xlsx")
        excel_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_excel(excel_path, index=False)
        print(f"Created test Excel file at: {excel_path}")
        
        # Upload the Excel file first
        with open(excel_path, 'rb') as f:
            excel_content = f.read()
        encoded_excel = base64.b64encode(excel_content).decode()
        
        # Upload Excel file
        upload_data = {
            "file_name": "test_sales_data.xlsx",
            "file_content_base64": encoded_excel,
            "container_name": "dev-uploads"
        }
        upload_response = test_client.post(
            f"{API_PREFIX}/blob-sample",
            json=upload_data,
            headers=headers
        )
        print(f"Excel upload status: {upload_response.status_code}")
        
        if upload_response.status_code == 200:
            blob_url = upload_response.json()["blob_url"]
            
            # Now create the plot
            # For filesystem storage, we can also use the direct file path
            plot_data = {
                "excel_url": f"file://{Path('./mock_storage/data/sales_data.xlsx').absolute()}",
                "plot_type": "bar", 
                "x_column": "Month",
                "y_column": "Sales",
                "title": "Monthly Sales Report",
                "sheet_name": "Sheet1",
                "figure_size": [10, 6]
            }
            response = test_client.post(
                f"{API_PREFIX}/create-plot",
                json=plot_data,
                headers=headers
            )
            print(f"Create plot status: {response.status_code}")
            print(f"Response: {json.dumps(response.json(), indent=2)}")
            assert response.status_code == 200
        else:
            print(f"Failed to upload Excel file: {upload_response.json()}")
            assert False
            
    except ImportError:
        print("Pandas or openpyxl not installed. Skipping create plot test.")
        pytest.skip("Pandas or openpyxl not installed")


if __name__ == "__main__":
    # Run tests using pytest
    pytest.main([__file__, "-v"])