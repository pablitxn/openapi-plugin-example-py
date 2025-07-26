"""Create plot command implementation."""
import io
import uuid
from datetime import datetime
from typing import Optional

import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
from openapi_plugin_common import (
    CommandBase,
    CommandContextBase,
    CommandException,
    ConfigurationException,
    ValidationException,
)

from ..options import ExamplePluginOptions

# Use non-interactive backend
matplotlib.use('Agg')


class CreatePlotCommandContext(CommandContextBase):
    """Context for the create plot command."""
    
    excel_url: str
    plot_type: str
    x_column: str
    y_column: str
    title: Optional[str] = None
    sheet_name: Optional[str] = None
    figure_size: tuple[int, int] = (10, 6)
    metadata: dict = {}


class CreatePlotCommandResult:
    """Result from the create plot command."""
    
    def __init__(
        self,
        plot_url: str,
        file_name: str,
        data_points: int
    ):
        self.plot_url = plot_url
        self.file_name = file_name
        self.data_points = data_points
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "plotUrl": self.plot_url,
            "fileName": self.file_name,
            "dataPoints": self.data_points
        }


class CreatePlotCommand(CommandBase[CreatePlotCommandContext, ExamplePluginOptions]):
    """Command to create plots from Excel data."""
    
    def __init__(
        self,
        telemetry_service: Optional[object] = None,
        blob_service: Optional[object] = None
    ) -> None:
        """Initialize the command."""
        super().__init__(telemetry_service)
        self._blob_service = blob_service
    
    async def execute_command_async(self, context: CreatePlotCommandContext) -> None:
        """Execute the create plot command logic."""
        # Validate blob service
        if not self._blob_service:
            raise ConfigurationException("Blob service is not configured")
        
        # Validate plot type
        valid_plot_types = ['line', 'bar', 'scatter', 'pie', 'histogram', 'box']
        if context.plot_type not in valid_plot_types:
            raise ValidationException(
                f"Invalid plot type '{context.plot_type}'. "
                f"Valid types: {', '.join(valid_plot_types)}"
            )
        
        try:
            # Download Excel file from blob storage
            excel_data = await self._download_excel_from_url(context.excel_url)
            
            # Read Excel file with pandas
            df = self._read_excel_data(excel_data, context.sheet_name)
            
            # Validate columns exist
            self._validate_columns(df, context.x_column, context.y_column)
            
            # Create the plot
            plot_buffer = self._create_plot(
                df,
                context.plot_type,
                context.x_column,
                context.y_column,
                context.title,
                context.figure_size
            )
            
            # Upload plot to blob storage
            plot_url, file_name = await self._upload_plot(
                plot_buffer,
                context.chat_id,
                context.plot_type
            )
            
            # Store result in context metadata
            context.metadata["result"] = CreatePlotCommandResult(
                plot_url=plot_url,
                file_name=file_name,
                data_points=len(df)
            )
            
            # Log telemetry
            if self._telemetry_service and hasattr(self._telemetry_service, "log_event"):
                self._telemetry_service.log_event("PlotCreated", {
                    "ChatId": context.chat_id,
                    "PlotType": context.plot_type,
                    "DataPoints": str(len(df)),
                    "Columns": f"{context.x_column},{context.y_column}"
                })
                
        except Exception as e:
            if self._telemetry_service and hasattr(self._telemetry_service, "log_error"):
                self._telemetry_service.log_error(
                    f"Plot creation failed: {str(e)}",
                    {"Error": str(e), "ChatId": context.chat_id}
                )
            raise CommandException(f"Failed to create plot: {str(e)}") from e
    
    async def _download_excel_from_url(self, excel_url: str) -> bytes:
        """Download Excel file from blob storage URL."""
        # Extract blob name from URL
        # Example: https://storage.azure.com/data/sales_data.xlsx
        parts = excel_url.split('/')
        if len(parts) < 5:
            raise ValidationException(f"Invalid blob storage URL: {excel_url}")
        
        container_name = parts[-2]
        blob_name = parts[-1]
        
        # Download blob
        blob_data = await self._blob_service.download_blob_async(
            blob_name=blob_name,
            container_name=container_name
        )
        
        return blob_data
    
    def _read_excel_data(self, excel_data: bytes, sheet_name: Optional[str]) -> pd.DataFrame:
        """Read Excel data into pandas DataFrame."""
        try:
            df = pd.read_excel(
                io.BytesIO(excel_data),
                sheet_name=sheet_name or 0
            )
            return df
        except Exception as e:
            raise ValidationException(f"Failed to read Excel file: {str(e)}")
    
    def _validate_columns(self, df: pd.DataFrame, x_column: str, y_column: str) -> None:
        """Validate that required columns exist in DataFrame."""
        missing_columns = []
        
        if x_column not in df.columns:
            missing_columns.append(x_column)
        
        if y_column not in df.columns:
            missing_columns.append(y_column)
        
        if missing_columns:
            available_columns = ', '.join(df.columns.tolist())
            raise ValidationException(
                f"Column(s) not found: {', '.join(missing_columns)}. "
                f"Available columns: {available_columns}"
            )
    
    def _create_plot(
        self,
        df: pd.DataFrame,
        plot_type: str,
        x_column: str,
        y_column: str,
        title: Optional[str],
        figure_size: tuple[int, int]
    ) -> io.BytesIO:
        """Create plot based on type and data."""
        plt.figure(figsize=figure_size)
        
        # Create plot based on type
        if plot_type == 'line':
            plt.plot(df[x_column], df[y_column], marker='o')
        elif plot_type == 'bar':
            plt.bar(df[x_column], df[y_column])
        elif plot_type == 'scatter':
            plt.scatter(df[x_column], df[y_column])
        elif plot_type == 'pie':
            # For pie chart, we only use y_column
            plt.pie(df[y_column], labels=df[x_column], autopct='%1.1f%%')
        elif plot_type == 'histogram':
            plt.hist(df[y_column], bins=20, edgecolor='black')
        elif plot_type == 'box':
            plt.boxplot(df[y_column])
        
        # Set labels and title
        if plot_type != 'pie':
            plt.xlabel(x_column)
            plt.ylabel(y_column)
        
        if title:
            plt.title(title)
        else:
            plt.title(f"{plot_type.capitalize()} Plot: {y_column} vs {x_column}")
        
        # Add grid for better readability
        if plot_type not in ['pie', 'box']:
            plt.grid(True, alpha=0.3)
        
        # Tight layout
        plt.tight_layout()
        
        # Save to buffer
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
        plt.close()
        
        buffer.seek(0)
        return buffer
    
    async def _upload_plot(
        self,
        plot_buffer: io.BytesIO,
        chat_id: str,
        plot_type: str
    ) -> tuple[str, str]:
        """Upload plot to blob storage."""
        # Generate unique filename
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        file_name = f"plot_{plot_type}_{timestamp}_{unique_id}.png"
        blob_name = f"{chat_id}/plots/{file_name}"
        
        # Upload to blob storage
        await self._blob_service.upload_blob_async(
            blob=plot_buffer.getvalue(),
            file_name=blob_name,
            container_name="plots",
            metadata={
                "chat_id": chat_id,
                "plot_type": plot_type,
                "content_type": "image/png"
            }
        )
        
        # Construct URL
        plot_url = f"https://storage.azure.com/plots/{blob_name}"
        
        return plot_url, file_name