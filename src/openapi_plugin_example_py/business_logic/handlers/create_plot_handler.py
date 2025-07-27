"""Create plot request handler."""
import time
from typing import Optional

from openapi_plugin_common import ValidationException

from .base_plugin_handler import BasePluginHandler
from ..commands import CreatePlotCommand, CreatePlotCommandContext
from ..options import ExamplePluginOptions
from ..requests import CreatePlotRequest, CreatePlotResponse


class CreatePlotHandler(BasePluginHandler[CreatePlotRequest, CreatePlotResponse]):
    """Handler for create plot requests."""
    
    def __init__(
        self,
        command_invoker_factory,
        plugin_options: ExamplePluginOptions,
        telemetry_service: Optional[object] = None
    ) -> None:
        """Initialize the handler."""
        super().__init__(command_invoker_factory, plugin_options, telemetry_service)
    
    async def execute_async(self, request: CreatePlotRequest) -> CreatePlotResponse:
        """Execute the create plot request."""
        start_time = time.time()
        
        # Validate request
        if not request.excel_url:
            raise ValidationException("Excel URL is required")
        
        if not request.x_column or not request.y_column:
            raise ValidationException("Both x_column and y_column are required")
        
        # Create command context
        context = CreatePlotCommandContext(
            chat_id=request.chat_id,
            agent_id=request.agent_id,
            agent_version=request.agent_version,
            excel_url=request.excel_url,
            plot_type=request.plot_type,
            x_column=request.x_column,
            y_column=request.y_column,
            title=request.title,
            sheet_name=request.sheet_name,
            figure_size=request.figure_size
        )
        
        # Execute command
        await self.execute_command_async(CreatePlotCommand, context)
        
        # Get result from context metadata
        result = context.metadata.get("result")
        if not result:
            raise ValidationException("Command did not produce a result")
        
        # Calculate processing time
        processing_time_ms = (time.time() - start_time) * 1000
        
        # Create response
        return CreatePlotResponse(
            plot_url=result.plot_url,
            plot_type=request.plot_type,
            file_name=result.file_name,
            processing_time_ms=processing_time_ms,
            data_points=result.data_points
        )