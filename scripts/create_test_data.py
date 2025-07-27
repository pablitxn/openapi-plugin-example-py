#!/usr/bin/env python3
"""Create test Excel data for the create-plot endpoint."""
import pandas as pd
import numpy as np
from pathlib import Path

# Create mock storage directories
Path("./mock_storage/data").mkdir(parents=True, exist_ok=True)
Path("./mock_storage/dev-uploads").mkdir(parents=True, exist_ok=True)

# Create sample sales data
months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
sales_data = {
    'Month': months,
    'Sales': [45000, 52000, 48000, 61000, 58000, 67000, 72000, 69000, 75000, 82000, 78000, 91000],
    'Expenses': [32000, 35000, 33000, 38000, 36000, 40000, 42000, 41000, 43000, 45000, 44000, 48000],
    'Profit': [13000, 17000, 15000, 23000, 22000, 27000, 30000, 28000, 32000, 37000, 34000, 43000],
    'Units_Sold': [450, 520, 480, 610, 580, 670, 720, 690, 750, 820, 780, 910]
}

# Create DataFrame
df = pd.DataFrame(sales_data)

# Save to Excel in data directory
excel_path = Path("./mock_storage/data/sales_data.xlsx")
df.to_excel(excel_path, index=False, sheet_name='Sheet1')
print(f"Created Excel file: {excel_path}")

# Also create a version in dev-uploads for direct upload testing
upload_path = Path("./mock_storage/dev-uploads/sales_data.xlsx")
df.to_excel(upload_path, index=False, sheet_name='Sheet1')
print(f"Created Excel file: {upload_path}")

# Create another dataset with different data
products_data = {
    'Product': ['Laptop', 'Desktop', 'Tablet', 'Phone', 'Monitor', 'Keyboard', 'Mouse', 'Printer'],
    'Q1_Sales': [120, 85, 95, 210, 65, 45, 35, 28],
    'Q2_Sales': [135, 90, 110, 195, 70, 50, 40, 32],
    'Q3_Sales': [145, 95, 125, 225, 75, 55, 45, 30],
    'Q4_Sales': [160, 110, 140, 250, 85, 60, 50, 35],
    'Price': [999, 799, 499, 699, 299, 79, 29, 199]
}

df_products = pd.DataFrame(products_data)
products_path = Path("./mock_storage/data/products_data.xlsx")
df_products.to_excel(products_path, index=False, sheet_name='Products')
print(f"Created Excel file: {products_path}")

# Create a time series dataset
import datetime
dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='D')
daily_data = {
    'Date': dates,
    'Temperature': 20 + 10 * np.sin(np.arange(len(dates)) * 2 * np.pi / 365) + np.random.normal(0, 2, len(dates)),
    'Humidity': 60 + 20 * np.sin(np.arange(len(dates)) * 2 * np.pi / 365 + np.pi/4) + np.random.normal(0, 5, len(dates)),
    'Pressure': 1013 + 5 * np.sin(np.arange(len(dates)) * 2 * np.pi / 365 + np.pi/2) + np.random.normal(0, 2, len(dates))
}

df_weather = pd.DataFrame(daily_data)
weather_path = Path("./mock_storage/data/weather_data.xlsx")
df_weather.to_excel(weather_path, index=False, sheet_name='Weather')
print(f"Created Excel file: {weather_path}")

print("\nAll test data files created successfully!")
print("\nAvailable files:")
for file in Path("./mock_storage/data").glob("*.xlsx"):
    print(f"  - {file}")