"""Extraction strategy interface — Strategy pattern for extract_from_text() dispatch."""

from __future__ import annotations

from abc import ABC, abstractmethod

from corp.extractor.extract import ExtractionResult
from corp.extractor.inventory import SourceFile
from corp.extractor.text_extract import TextExtractionResult


class ExtractionStrategy(ABC):
    """Single extraction approach (PDF multimodal, PPTX→PDF multimodal, text provider).

    Strategies are tried in order by extract_from_text(). Each returns
    ExtractionResult on success or None to signal fallback to the next strategy.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Strategy name for logging."""
        ...

    @abstractmethod
    def can_handle(
        self,
        file: SourceFile,
        config: dict,
        text_result: TextExtractionResult,
        custom_prompt: str | None = None,
    ) -> bool:
        """Return True if this strategy applies to the given file."""
        ...

    @abstractmethod
    def extract(
        self,
        file: SourceFile,
        config: dict,
        text_result: TextExtractionResult,
        custom_prompt: str | None = None,
        user_context: str = "",
    ) -> ExtractionResult | None:
        """Attempt extraction. Return result or None to fall through."""
        ...
