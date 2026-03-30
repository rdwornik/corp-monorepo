"""Text provider extraction strategy — send text to Claude/Gemini via provider abstraction."""

from __future__ import annotations

import copy
import logging
from typing import TYPE_CHECKING

from corp.extractor.inventory import SourceFile
from corp.extractor.post_process import post_process_extraction
from corp.extractor.strategies.base import ExtractionStrategy
from corp.extractor.text_extract import TextExtractionResult, extract_source_date

if TYPE_CHECKING:
    from corp.extractor.extract import ExtractionResult

log = logging.getLogger(__name__)


class TextProviderStrategy(ExtractionStrategy):
    """Text-only extraction via provider abstraction (Claude Haiku or Gemini).

    Routes through the provider abstraction layer. For deep-eligible doc types,
    uses the deep extraction prompt with overlay fields. Falls back to standard
    prompt for general documents. Validates response and escalates to Sonnet
    on malformed JSON.

    This is the fallback strategy — always matches, always returns a result.
    """

    @property
    def name(self) -> str:
        return "text_provider"

    def can_handle(
        self,
        file: SourceFile,
        config: dict,
        text_result: TextExtractionResult,
        custom_prompt: str | None = None,
    ) -> bool:
        return True  # Always available as last resort

    def extract(
        self,
        file: SourceFile,
        config: dict,
        text_result: TextExtractionResult,
        custom_prompt: str | None = None,
        user_context: str = "",
    ) -> ExtractionResult | None:
        from corp.extractor.deep_prompt import build_deep_prompt
        from corp.extractor.doc_type_classifier import (
            classify_doc_type_hybrid,
            should_extract_deep,
        )
        from corp.extractor.extract import (
            _enrich_facts,
            _get_prompt,
            _parse_response,
            _prepend_user_context,
            _result_from_json,
            compute_token_budget,
        )
        from corp.extractor.freshness import compute_freshness_fields
        from corp.extractor.providers.base import ExtractionRequest
        from corp.extractor.providers.router import (
            DEFAULT_LARGE_CONTEXT_MODEL,
            get_provider,
            has_anthropic_key,
            route_model,
        )
        from corp.extractor.providers.validator import validate_and_retry
        from corp.extractor.taxonomy_prompt import get_taxonomy_for_prompt

        # Truncate very long text to stay within token limits
        text_content = text_result.text[:80000]

        # --- Classify doc type and decide extraction depth ---
        _doc_type, _conf, _method = classify_doc_type_hybrid(file.path.name, content=text_content)
        doc_type = _doc_type or "general"
        use_deep = should_extract_deep(doc_type) and custom_prompt is None

        # --- Route to correct model ---
        model_override = config.get("model_override")
        batch_mode = config.get("batch_mode", False)
        model = route_model(
            tier=2,
            text_length=len(text_content),
            model_override=model_override,
            batch_mode=batch_mode,
        )

        log.info(
            "Extracting %s via provider (%d chars, model=%s, doc_type=%s, deep=%s)...",
            file.path.name,
            len(text_content),
            model,
            doc_type,
            use_deep,
        )

        # --- Build prompt ---
        if custom_prompt:
            system_prompt = ""
            user_prompt = _prepend_user_context(
                f"{custom_prompt}\n\n--- FILE CONTENT ({text_result.extractor}) ---\n{text_content}",
                user_context,
            )
        elif use_deep:
            deep_prompt = build_deep_prompt(doc_type)
            taxonomy = get_taxonomy_for_prompt()
            system_prompt = "You are a structured knowledge extraction engine for a pre-sales knowledge base."
            user_prompt = _prepend_user_context(
                f"{deep_prompt}\n\n{taxonomy}\n\n--- FILE CONTENT ({text_result.extractor}) ---\n{text_content}",
                user_context,
            )
        else:
            prompt = _get_prompt(config, "extract")
            system_prompt = ""
            user_prompt = _prepend_user_context(
                f"{prompt}\n\n--- FILE CONTENT ({text_result.extractor}) ---\n{text_content}",
                user_context,
            )

        # --- Compute dynamic token budget ---
        slide_count = text_result.slide_count or 0
        token_budget = compute_token_budget(
            depth="deep" if use_deep else "standard",
            config=config,
            slide_count=slide_count,
        )

        # --- Call provider ---
        request = ExtractionRequest(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            model=model,
            max_tokens=token_budget,
            temperature=0.2,
            response_format="json",
        )

        provider = get_provider(model)
        response = provider.extract(request)

        # --- Validate and optionally escalate to Sonnet ---
        response, was_escalated = validate_and_retry(response, request)
        if was_escalated:
            log.warning("Extraction for %s was escalated to Sonnet after validation failure", file.path.name)

        tokens = response.input_tokens + response.output_tokens

        # --- Parse response ---
        data = _parse_response(response.text, file)

        # --- Handle deep extraction base/overlay split ---
        overlay_data = {}
        if use_deep and "base" in data:
            overlay_data = data.get("overlay", {})
            data = data["base"]

        # Preserve raw output before post-processing mutates it
        raw_data = copy.deepcopy(data)

        # Post-process via corp.schema
        pp = post_process_extraction(
            raw_result=data,
            source_tool="knowledge-extractor",
            source_file=str(file.path),
        )

        result = _result_from_json(pp.data, file, tokens)
        result.links_line = pp.links_line
        result.validation_result = pp.validation_result.value
        result.raw_json = raw_data

        # Deep extraction metadata
        result.doc_type = doc_type
        result.depth = "deep" if use_deep else "standard"
        result.extraction_version = 2 if use_deep else 1
        result.overlay = overlay_data

        # RFP agent enrichment: source_date, locator, polarity
        result.source_date = extract_source_date(file.path)
        result.facts = _enrich_facts(data, file, result.source_date, text_result)

        # Freshness tracking
        result.freshness = compute_freshness_fields(file.path)

        # Provenance metadata — response.model reflects escalation if it happened
        result.model_used = response.model
        if model_override:
            result.routing_reason = "manual_override"
        elif batch_mode:
            result.routing_reason = "batch_discount"
        elif model == DEFAULT_LARGE_CONTEXT_MODEL and not has_anthropic_key():
            result.routing_reason = "anthropic_key_missing"
        else:
            result.routing_reason = "text_default"
        result.prompt_version = "deep_v2" if use_deep else "standard_v1"
        result.extraction_cost_usd = response.cost_estimate
        result.user_context = user_context

        log.info(
            "Tier 2 extracted: '%s' | model=%s | deep=%s | doc_type=%s | topics=%s | tokens=%d | cost=$%.6f",
            result.title,
            model,
            use_deep,
            doc_type,
            result.topics[:3],
            tokens,
            response.cost_estimate,
        )
        return result
