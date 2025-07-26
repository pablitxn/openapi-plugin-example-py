"""Requests module for the example plugin."""
from .ai_sample_request import AISampleRequest, AISampleResponse
from .blob_sample_request import BlobSampleRequest, BlobSampleResponse
from .sample_request import SampleRequest, SampleResponse

__all__ = [
    "SampleRequest",
    "SampleResponse",
    "AISampleRequest",
    "AISampleResponse",
    "BlobSampleRequest",
    "BlobSampleResponse",
]