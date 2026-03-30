"""PPTX→PDF multimodal extraction strategy — convert PPTX to PDF, send to Gemini."""

from __future__ import annotations

import logging
from pathlib import Path

from corp.extractor.extract import (
    ExtractionResult,
    _assemble_extraction_result,
    _enrich_facts,
    _get_client,
    _get_prompt,
    _parse_response,
    _prepend_user_context,
    _render_pdf_to_slides,
    _run_haiku_enrichment,
    _select_extraction_model,
    _upload_and_wait,
    compute_token_budget,
)
from corp.extractor.inventory import SourceFile
from corp.extractor.strategies.base import ExtractionStrategy
from corp.extractor.taxonomy_prompt import get_taxonomy_for_prompt
from corp.extractor.text_extract import TextExtractionResult

log = logging.getLogger(__name__)


class PPTXPdfMultimodalStrategy(ExtractionStrategy):
    """Attempt PPTX→PDF conversion and Gemini multimodal extraction.

    Returns ExtractionResult on success, None if PDF conversion fails.
    """

    @property
    def name(self) -> str:
        return "pptx_pdf_multimodal"

    def can_handle(
        self,
        file: SourceFile,
        config: dict,
        text_result: TextExtractionResult,
        custom_prompt: str | None = None,
    ) -> bool:
        return file.path.suffix.lower() == ".pptx" and custom_prompt is None

    def extract(
        self,
        file: SourceFile,
        config: dict,
        text_result: TextExtractionResult,
        custom_prompt: str | None = None,
        user_context: str = "",
    ) -> ExtractionResult | None:
        import tempfile

        from google.genai import types

        from corp.extractor.deep_prompt import build_deep_multimodal_prompt
        from corp.extractor.doc_type_classifier import (
            classify_doc_type_hybrid,
            should_extract_deep,
        )
        from corp.extractor.slides.pdf_converter import convert_pptx_to_pdf

        pdf_dir = Path(tempfile.mkdtemp(prefix="cke_pptx_pdf_"))
        pdf_path = convert_pptx_to_pdf(file.path, pdf_dir)

        if pdf_path is None:
            return None

        log.info("PPTX→PDF conversion succeeded for %s, sending PDF to Gemini multimodal", file.path.name)

        client = _get_client(config)
        model, routing_reason = _select_extraction_model(file, config)

        _doc_type, _conf, _method = classify_doc_type_hybrid(file.path.name)
        doc_type = _doc_type or "general"
        use_deep = should_extract_deep(doc_type)

        # Build prompt with text grounding
        if use_deep:
            deep_prompt = build_deep_multimodal_prompt(doc_type)
            taxonomy = get_taxonomy_for_prompt()
            prompt = _prepend_user_context(f"{deep_prompt}\n\n{taxonomy}", user_context)
        else:
            prompt = _prepend_user_context(_get_prompt(config, "extract"), user_context)

        # Include text grounding from python-pptx
        text_grounding = text_result.text[:30000] if text_result.text else ""
        if text_grounding:
            prompt += f"\n\n--- TEXT GROUNDING (from python-pptx) ---\n{text_grounding}"

        # Upload PDF and send to Gemini
        uploaded = _upload_and_wait(client, pdf_path, config)
        contents = [
            types.Part.from_uri(file_uri=uploaded.uri, mime_type="application/pdf"),
            types.Part.from_text(text=prompt),
        ]

        slide_count = text_result.slide_count or 0
        token_budget = compute_token_budget(
            depth="deep" if use_deep else "standard",
            config=config,
            slide_count=slide_count,
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

        # Assemble result using shared helper
        result = _assemble_extraction_result(
            data, file, tokens, use_deep, doc_type,
            model, routing_reason, user_context, None,
        )
        # Override facts with text_result enrichment
        result.facts = _enrich_facts(data, file, result.source_date, text_result)

        # Haiku enrichment pass
        _run_haiku_enrichment(result, data, file, text_result)

        # Render slide PNGs from PDF before cleanup
        try:
            slide_paths = _render_pdf_to_slides(pdf_path, pdf_dir)
            result.slide_image_paths = slide_paths
            log.info("Rendered %d slide PNGs from PDF for %s", len(slide_paths), file.path.name)
        except Exception as exc:
            log.warning("Failed to render slide PNGs from PDF: %s", exc)

        # Cleanup temp PDF (keep slide PNGs for run.py to copy)
        try:
            pdf_path.unlink(missing_ok=True)
        except OSError:
            pass

        log.info(
            "PPTX PDF multimodal extracted: '%s' | doc_type=%s | deep=%s | tokens=%d | model=%s",
            result.title,
            doc_type,
            use_deep,
            tokens,
            model,
        )
        return result
