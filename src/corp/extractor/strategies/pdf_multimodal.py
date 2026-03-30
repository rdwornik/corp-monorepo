"""PDF multimodal extraction strategy — upload PDF to Gemini for native extraction."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from corp.extractor.inventory import SourceFile
from corp.extractor.strategies.base import ExtractionStrategy
from corp.extractor.text_extract import TextExtractionResult

if TYPE_CHECKING:
    from corp.extractor.extract import ExtractionResult

log = logging.getLogger(__name__)


class PDFMultimodalStrategy(ExtractionStrategy):
    """Upload PDF directly to Gemini Pro for native multimodal extraction.

    Large PDF guard: >50 pages or >30MB → truncate to 50 pages for upload,
    full text via pdfplumber (no truncation).
    """

    @property
    def name(self) -> str:
        return "pdf_multimodal"

    def can_handle(
        self,
        file: SourceFile,
        config: dict,
        text_result: TextExtractionResult,
        custom_prompt: str | None = None,
    ) -> bool:
        return file.path.suffix.lower() == ".pdf" and custom_prompt is None

    def extract(
        self,
        file: SourceFile,
        config: dict,
        text_result: TextExtractionResult,
        custom_prompt: str | None = None,
        user_context: str = "",
    ) -> ExtractionResult | None:
        from google.genai import types

        from corp.extractor.deep_prompt import build_deep_multimodal_prompt
        from corp.extractor.doc_type_classifier import (
            classify_doc_type_hybrid,
            should_extract_deep,
        )
        from corp.extractor.extract import (
            _assemble_extraction_result,
            _enrich_facts,
            _get_client,
            _get_prompt,
            _parse_response,
            _prepend_user_context,
            _render_cover_page,
            _run_haiku_enrichment,
            _select_extraction_model,
            _truncate_large_pdf,
            _upload_and_wait,
            compute_token_budget,
            get_taxonomy_for_prompt,
        )

        client = _get_client(config)
        model, routing_reason = _select_extraction_model(file, config)

        _doc_type, _conf, _method = classify_doc_type_hybrid(file.path.name)
        doc_type = _doc_type or "general"
        use_deep = should_extract_deep(doc_type)

        # Large PDF guard
        pdf_path, multimodal_truncated, page_count, temp_dir = _truncate_large_pdf(
            file.path, file.size_bytes
        )

        # Build prompt
        if use_deep:
            deep_prompt = build_deep_multimodal_prompt(doc_type)
            taxonomy = get_taxonomy_for_prompt()
            prompt = _prepend_user_context(f"{deep_prompt}\n\n{taxonomy}", user_context)
        else:
            prompt = _prepend_user_context(_get_prompt(config, "extract"), user_context)

        text_grounding = text_result.text[:30000] if text_result.text else ""
        if text_grounding:
            prompt += f"\n\n--- TEXT GROUNDING (from pdfplumber) ---\n{text_grounding}"

        # Upload and extract
        uploaded = _upload_and_wait(client, pdf_path, config)
        contents = [
            types.Part.from_uri(file_uri=uploaded.uri, mime_type="application/pdf"),
            types.Part.from_text(text=prompt),
        ]

        token_budget = compute_token_budget(
            depth="deep" if use_deep else "standard",
            config=config,
            slide_count=page_count,
        )

        response = client.models.generate_content(
            model=model,
            contents=contents,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                max_output_tokens=token_budget,
            ),
        )

        response_text = response.text or ""
        tokens = 0
        if hasattr(response, "usage_metadata") and response.usage_metadata:
            tokens = getattr(response.usage_metadata, "total_token_count", 0) or 0

        data = _parse_response(response_text, file)

        # Assemble result
        result = _assemble_extraction_result(
            data, file, tokens, use_deep, doc_type,
            model, routing_reason, user_context, None,
        )
        # PDF-specific: override facts with text_result enrichment
        result.facts = _enrich_facts(data, file, result.source_date, text_result)

        # Haiku enrichment pass
        _run_haiku_enrichment(result, data, file, text_result)

        # Render cover page PNG
        result.slide_image_paths = _render_cover_page(file.path)

        # Cleanup temp truncated PDF
        if temp_dir:
            try:
                for f in temp_dir.iterdir():
                    f.unlink(missing_ok=True)
                temp_dir.rmdir()
            except OSError:
                pass

        if multimodal_truncated:
            result.raw_json["multimodal_truncated"] = True

        log.info(
            "PDF multimodal extracted: '%s' | pages=%d | truncated=%s | doc_type=%s | deep=%s | tokens=%d | model=%s",
            result.title,
            page_count,
            multimodal_truncated,
            doc_type,
            use_deep,
            tokens,
            model,
        )
        return result
