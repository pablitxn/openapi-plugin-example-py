"""Sample request models."""
from typing import Optional

from openapi_plugin_common import RequestBase
from pydantic import BaseModel, ConfigDict, Field


class SampleRequest(RequestBase):
    """Request model for sample endpoint."""
    
    sample_input: str = Field(
        ...,
        description="The sample input to process",
        min_length=1,
        max_length=1000,
        json_schema_extra={"example": "Hello World"}
    )
    use_cache: bool = Field(
        default=True,
        description="Whether to use caching for this request"
    )


class SampleResponse(BaseModel):
    """Response model for sample endpoint."""
    
    sample_response: str = Field(
        ...,
        description="The processed sample response"
    )
    cached: bool = Field(
        default=False,
        description="Whether the response was served from cache"
    )
    processing_time_ms: Optional[float] = Field(
        default=None,
        description="Processing time in milliseconds"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "sample_response": "Processed: HELLO WORLD",
                "cached": False,
                "processing_time_ms": 123.45
            }
        }
    )