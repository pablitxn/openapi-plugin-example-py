"""Create plot request models."""
from typing import Optional

from openapi_plugin_common import RequestBase
from pydantic import BaseModel, ConfigDict, Field


class CreatePlotRequest(RequestBase):
    """Request model for create plot endpoint."""
    
    excel_url: str = Field(
        ...,
        description="URL of the Excel file in blob storage",
        json_schema_extra={"example": "https://storage.azure.com/data/sales_data.xlsx"}
    )
    plot_type: str = Field(
        ...,
        description="Type of plot to create",
        json_schema_extra={"example": "bar"}
    )
    x_column: str = Field(
        ...,
        description="Column name for X axis",
        json_schema_extra={"example": "Month"}
    )
    y_column: str = Field(
        ...,
        description="Column name for Y axis",
        json_schema_extra={"example": "Sales"}
    )
    title: Optional[str] = Field(
        default=None,
        description="Title for the plot",
        json_schema_extra={"example": "Monthly Sales Report"}
    )
    sheet_name: Optional[str] = Field(
        default=None,
        description="Excel sheet name to read from",
        json_schema_extra={"example": "Sheet1"}
    )
    figure_size: Optional[tuple[int, int]] = Field(
        default=(10, 6),
        description="Figure size in inches (width, height)",
        json_schema_extra={"example": (10, 6)}
    )


class CreatePlotResponse(BaseModel):
    """Response model for create plot endpoint."""
    
    plot_url: str = Field(
        ...,
        description="URL of the generated plot image in blob storage"
    )
    plot_type: str = Field(
        ...,
        description="Type of plot created"
    )
    file_name: str = Field(
        ...,
        description="Name of the generated plot file"
    )
    processing_time_ms: float = Field(
        ...,
        description="Processing time in milliseconds"
    )
    data_points: int = Field(
        ...,
        description="Number of data points plotted"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "plot_url": "https://storage.azure.com/plots/20240726_plot_123.png",
                "plot_type": "bar",
                "file_name": "monthly_sales_plot.png",
                "processing_time_ms": 523.45,
                "data_points": 12
            }
        }
    )