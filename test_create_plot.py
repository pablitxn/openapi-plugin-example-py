"""Test script for create-plot endpoint."""
import json
import requests
import base64
import pandas as pd
import io

# First, let's create a sample Excel file
data = {
    'Month': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
    'Sales': [15000, 18000, 22000, 19000, 24000, 28000],
    'Costs': [8000, 9000, 10000, 9500, 11000, 12000]
}

df = pd.DataFrame(data)

# Save to Excel
excel_buffer = io.BytesIO()
with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
    df.to_excel(writer, sheet_name='Sales Data', index=False)

excel_buffer.seek(0)

# Base64 encode the Excel file
excel_base64 = base64.b64encode(excel_buffer.getvalue()).decode('utf-8')

# First, we need to upload the Excel file using the blob-sample endpoint
print("1. Uploading Excel file to blob storage...")

blob_request = {
    "file_name": "test_sales_data.xlsx",
    "file_content_base64": excel_base64,
    "container_name": "data"
}

# Note: In a real scenario, you'd need a valid JWT token
# For testing without auth, you can comment out the auth dependencies in main.py
headers = {
    "Content-Type": "application/json",
    "x-chat-id": "test-chat-123",
    "x-agent-id": "test-agent",
    "x-agent-version": "1.0.0",
    # "Authorization": "Bearer YOUR_JWT_TOKEN"  # Add valid token here
}

try:
    # Step 1: Upload Excel file
    response = requests.post(
        "http://localhost:8000/api/plugin/ExamplePlugin/v1/blob-sample",
        json=blob_request,
        headers=headers
    )
    
    if response.status_code == 200:
        blob_response = response.json()
        excel_url = blob_response['blob_url']
        print(f"✓ Excel file uploaded: {excel_url}")
        
        # Step 2: Create plot
        print("\n2. Creating plot from Excel data...")
        
        plot_request = {
            "excel_url": excel_url,
            "plot_type": "bar",
            "x_column": "Month",
            "y_column": "Sales",
            "title": "Monthly Sales Report 2024",
            "sheet_name": "Sales Data",
            "figure_size": [10, 6]
        }
        
        response = requests.post(
            "http://localhost:8000/api/plugin/ExamplePlugin/v1/create-plot",
            json=plot_request,
            headers=headers
        )
        
        if response.status_code == 200:
            plot_response = response.json()
            print(f"✓ Plot created successfully!")
            print(f"  - Plot URL: {plot_response['plot_url']}")
            print(f"  - Plot type: {plot_response['plot_type']}")
            print(f"  - Data points: {plot_response['data_points']}")
            print(f"  - Processing time: {plot_response['processing_time_ms']}ms")
        else:
            print(f"✗ Failed to create plot: {response.status_code}")
            print(f"  Response: {response.text}")
            
    else:
        print(f"✗ Failed to upload Excel file: {response.status_code}")
        print(f"  Response: {response.text}")
        
except requests.exceptions.ConnectionError:
    print("✗ Could not connect to the server. Make sure it's running on http://localhost:8000")
except Exception as e:
    print(f"✗ Error: {e}")

print("\n3. Testing different plot types...")
plot_types = ['line', 'scatter', 'pie', 'histogram']

for plot_type in plot_types:
    print(f"\n   Creating {plot_type} plot...")
    plot_request['plot_type'] = plot_type
    
    # For pie chart, we don't need x_column for labels
    if plot_type == 'histogram':
        plot_request['y_column'] = 'Sales'  # Histogram only uses y_column
    
    try:
        response = requests.post(
            "http://localhost:8000/api/plugin/ExamplePlugin/v1/create-plot",
            json=plot_request,
            headers=headers
        )
        
        if response.status_code == 200:
            plot_response = response.json()
            print(f"   ✓ {plot_type} plot created: {plot_response['plot_url']}")
        else:
            print(f"   ✗ Failed to create {plot_type} plot: {response.status_code}")
    except Exception as e:
        print(f"   ✗ Error creating {plot_type} plot: {e}")