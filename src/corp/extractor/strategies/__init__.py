"""Extraction strategy classes for extract_from_text() dispatch chain."""

from corp.extractor.strategies.base import ExtractionStrategy
from corp.extractor.strategies.pdf_multimodal import PDFMultimodalStrategy
from corp.extractor.strategies.pptx_pdf_multimodal import PPTXPdfMultimodalStrategy
from corp.extractor.strategies.text_provider import TextProviderStrategy

# Strategy chain — tried in order by extract_from_text().
# PDF multimodal first, PPTX→PDF second, text provider as fallback.
STRATEGIES: list[ExtractionStrategy] = [
    PDFMultimodalStrategy(),
    PPTXPdfMultimodalStrategy(),
    TextProviderStrategy(),
]

__all__ = [
    "ExtractionStrategy",
    "PDFMultimodalStrategy",
    "PPTXPdfMultimodalStrategy",
    "STRATEGIES",
    "TextProviderStrategy",
]
