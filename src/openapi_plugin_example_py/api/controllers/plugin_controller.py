"""Main plugin controller with all endpoints."""
from typing import Annotated

from fastapi import APIRouter, Depends, Header, Query
from openapi_plugin_common import HttpHeaders

from ...business_logic.handlers import (
    AISampleHandler,
    BlobSampleHandler,
    CreatePlotHandler,
    SampleHandler,
)
from ...business_logic.requests import (
    AISampleRequest,
    AISampleResponse,
    BlobSampleRequest,
    BlobSampleResponse,
    CreatePlotRequest,
    CreatePlotResponse,
    SampleRequest,
    SampleResponse,
)

router = APIRouter(tags=["Plugin"])


@router.get(
    "/sample",
    summary="Process a sample request",
    description="Processes a sample input and returns a processed response",
    response_model=SampleResponse
)
async def sample(
    sample_input: Annotated[str, Query(
        description="The sample input to process",
        min_length=1,
        max_length=1000
    )],
    use_cache: Annotated[bool, Query(
        description="Whether to use caching for this request"
    )] = True,
    chat_id: Annotated[str, Header(alias=HttpHeaders.CHAT_ID)] = "",
    agent_id: Annotated[str, Header(alias=HttpHeaders.AGENT_ID)] = "",
    agent_version: Annotated[str, Header(alias=HttpHeaders.AGENT_VERSION)] = "",
    sample_handler: SampleHandler = Depends()
) -> SampleResponse:
    """Process a sample request."""
    # Create request
    request = SampleRequest(
        sample_input=sample_input,
        use_cache=use_cache,
        chat_id=chat_id,
        agent_id=agent_id,
        agent_version=agent_version
    )
    
    # Handle request
    return await sample_handler.handle_async(request)


@router.post(
    "/ai-sample",
    summary="Process an AI sample request",
    description="Processes a prompt using AI and returns the generated response",
    response_model=AISampleResponse
)
async def ai_sample(
    request_body: AISampleRequest,
    chat_id: Annotated[str, Header(alias=HttpHeaders.CHAT_ID)] = "",
    agent_id: Annotated[str, Header(alias=HttpHeaders.AGENT_ID)] = "",
    agent_version: Annotated[str, Header(alias=HttpHeaders.AGENT_VERSION)] = "",
    ai_sample_handler: AISampleHandler = Depends()
) -> AISampleResponse:
    """Process an AI sample request."""
    # Update headers from request
    request_body.chat_id = chat_id or request_body.chat_id
    request_body.agent_id = agent_id or request_body.agent_id
    request_body.agent_version = agent_version or request_body.agent_version
    
    # Handle request
    return await ai_sample_handler.handle_async(request_body)


@router.post(
    "/blob-sample",
    summary="Upload a file to blob storage",
    description="Uploads a file to Azure blob storage and returns the blob URL",
    response_model=BlobSampleResponse
)
async def blob_sample(
    request_body: BlobSampleRequest,
    chat_id: Annotated[str, Header(alias=HttpHeaders.CHAT_ID)] = "",
    agent_id: Annotated[str, Header(alias=HttpHeaders.AGENT_ID)] = "",
    agent_version: Annotated[str, Header(alias=HttpHeaders.AGENT_VERSION)] = "",
    blob_sample_handler: BlobSampleHandler = Depends()
) -> BlobSampleResponse:
    """Upload a file to blob storage."""
    # Update headers from request
    request_body.chat_id = chat_id or request_body.chat_id
    request_body.agent_id = agent_id or request_body.agent_id
    request_body.agent_version = agent_version or request_body.agent_version
    
    # Handle request
    return await blob_sample_handler.handle_async(request_body)


@router.post(
    "/create-plot",
    summary="Create a plot from Excel data",
    description="Downloads Excel file from blob storage, creates a plot, and uploads it back",
    response_model=CreatePlotResponse
)
async def create_plot(
    request_body: CreatePlotRequest,
    chat_id: Annotated[str, Header(alias=HttpHeaders.CHAT_ID)] = "",
    agent_id: Annotated[str, Header(alias=HttpHeaders.AGENT_ID)] = "",
    agent_version: Annotated[str, Header(alias=HttpHeaders.AGENT_VERSION)] = "",
    create_plot_handler: CreatePlotHandler = Depends()
) -> CreatePlotResponse:
    """Create a plot from Excel data."""
    # Update headers from request
    request_body.chat_id = chat_id or request_body.chat_id
    request_body.agent_id = agent_id or request_body.agent_id
    request_body.agent_version = agent_version or request_body.agent_version
    
    # Handle request
    return await create_plot_handler.handle_async(request_body)