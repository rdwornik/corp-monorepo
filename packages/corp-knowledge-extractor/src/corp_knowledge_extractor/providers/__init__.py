"""Multi-provider extraction abstraction.

Routes text extraction to Claude Haiku 4.5, multimodal to Gemini Flash.
"""

from corp_knowledge_extractor.providers.base import ExtractionProvider, ExtractionRequest, ExtractionResponse
from corp_knowledge_extractor.providers.router import route_model, get_provider

__all__ = [
    "ExtractionProvider",
    "ExtractionRequest",
    "ExtractionResponse",
    "route_model",
    "get_provider",
]
