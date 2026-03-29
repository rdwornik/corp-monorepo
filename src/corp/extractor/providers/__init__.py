"""Multi-provider extraction abstraction.

Routes text extraction to Claude Haiku 4.5, multimodal to Gemini Flash.
"""

from corp.extractor.providers.base import (
    ExtractionProvider,
    ExtractionRequest,
    ExtractionResponse,
)
from corp.extractor.providers.router import get_provider, route_model

__all__ = [
    "ExtractionProvider",
    "ExtractionRequest",
    "ExtractionResponse",
    "route_model",
    "get_provider",
]
