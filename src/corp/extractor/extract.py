"""
Gemini API-based knowledge extraction.

For plain files (audio, docs, notes): single Gemini call with text/binary content.
For videos WITH sampled frames: uploads video + sends sampled frame images inline
so Gemini can identify unique slides and produce per-slide analysis.

Usage:
    from corp.extractor.extract import extract_knowledge, ExtractionResult, ExtractionError
    from corp.extractor.inventory import SourceFile
    from corp.extractor.frames.sampler import SampledFrame

    # Plain extraction
    result = extract_knowledge(source_file, config)

    # Video with pre-sampled frames (AI picks unique slides)
    result = extract_knowledge(source_file, config, sampled_frames=frames)
"""

import copy
import logging
import mimetypes
import os
import time
from dataclasses import dataclass, field
from pathlib import Path

from corp.extractor.frames.sampler import SampledFrame
from corp.extractor.inventory import FileType, SourceFile
from corp.extractor.post_process import post_process_extraction
from corp.extractor.taxonomy_prompt import get_taxonomy_for_prompt
from corp.extractor.text_extract import (
    TextExtractionResult,
    extract_source_date,
)
from corp.schema.utils import normalize_string_list, parse_llm_json

log = logging.getLogger(__name__)

# Max frames to send to Gemini in a single request (avoid token overload)
MAX_FRAMES_PER_REQUEST = 50


@dataclass
class SlideAnalysis:
    slide_number: int
    frame_index: int = 0  # sample_NNNN index from Gemini's response
    slide_title: str = ""
    timestamp_approx: str = ""
    speaker_insight: str = ""  # What the speaker SAID — the main content
    so_what: str = ""  # Practical implication paragraph
    critical_notes: str | None = None  # Red flags / things to verify
    key_facts: list[str] = field(default_factory=list)


@dataclass
class ExtractionResult:
    source_file: SourceFile
    title: str
    summary: str
    key_points: list[str] = field(default_factory=list)
    topics: list[str] = field(default_factory=list)
    people: list[str] = field(default_factory=list)
    products: list[str] = field(default_factory=list)
    content_type: str = "unknown"
    language: str = "en"
    quality: str = "medium"
    duration_min: int | None = None
    transcript_excerpt: str = ""
    slides: list[SlideAnalysis] = field(default_factory=list)
    raw_json: dict = field(default_factory=dict)
    tokens_used: int = 0
    links_line: str = ""  # Deterministic Links line from post-processing
    source_tool: str = "knowledge-extractor"
    validation_result: str = "valid"  # "valid", "warnings", "quarantine"
    # Schema v2 knowledge dimensions
    source_type: str = "documentation"
    layer: str = "learning"
    domains: list[str] = field(default_factory=list)
    confidentiality: str = "internal"
    authority: str = "tribal"
    client: str | None = None
    project: str | None = None
    # RFP agent enrichment fields
    source_date: str | None = None
    facts: list[dict] = field(default_factory=list)
    # Deep extraction fields
    doc_type: str | None = None
    extraction_version: int = 1
    depth: str = "standard"
    overlay: dict = field(default_factory=dict)
    # Freshness tracking
    freshness: dict = field(default_factory=dict)
    # Gemini File API URI for reuse (e.g., transcript generation)
    gemini_file_uri: str | None = None
    # Temp slide PNGs rendered from PDF (moved to output by run.py)
    slide_image_paths: list[Path] = field(default_factory=list)
    # Provenance metadata
    model_used: str = ""
    routing_reason: str = ""
    prompt_version: str = "standard_v1"
    extraction_cost_usd: float = 0.0
    # User-provided context (from manifest or --context flag)
    user_context: str = ""
    # Normalized output stem (set by build_package)
    output_stem: str = ""


class ExtractionError(Exception):
    pass


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _get_client(config: dict):
    from google import genai

    api_key_env = config.get("gemini", {}).get("api_key_env", "GEMINI_API_KEY")
    api_key = os.environ.get(api_key_env)
    if not api_key:
        raise ExtractionError(f"API key not found. Set {api_key_env} in your .env file.")
    return genai.Client(api_key=api_key)


def _get_model(config: dict) -> str:
    return config.get("model_override") or config.get("gemini", {}).get("model", "gemini-3.1-flash-lite")


def _estimate_gemini_cost(model: str, total_tokens: int) -> float:
    """Estimate cost for a Gemini call from total token count.

    Uses a blended rate (input-heavy assumption: ~80% input, ~20% output).
    """
    rates = {
        "gemini-3.1-flash-lite": 0.25,  # blended $/1M tokens
        "gemini-3.1-flash": 0.50,
        "gemini-3-flash-preview": 1.00,  # kept for backward compat
        "gemini-3.1-pro-preview": 4.00,
    }
    rate = rates.get(model, 1.00)
    return round(total_tokens * rate / 1_000_000, 6)


def _prepend_user_context(prompt: str, user_context: str) -> str:
    """Prepend user context to a prompt if provided."""
    if not user_context:
        return prompt
    return (
        f"ADDITIONAL CONTEXT FROM USER:\n{user_context}\n\n"
        f"Use this context to guide your extraction — prioritize facts relevant to this context.\n\n"
        f"{prompt}"
    )


def _get_prompt(config: dict, prompt_name: str, custom_prompt: str | None = None) -> str:
    if custom_prompt:
        prompt = custom_prompt
    else:
        prompts = config.get("prompts") or {}
        prompt = prompts.get(prompt_name, "")
        if not prompt:
            raise ExtractionError(f"No '{prompt_name}' prompt found in config['prompts']")

    anon_terms = (config.get("anonymization") or {}).get("custom_terms", [])
    if anon_terms:
        prompt += f"\n\nRedact these terms from all output: {', '.join(anon_terms)}"

    # Inject canonical taxonomy so LLM uses correct terms from the start
    if prompt_name in ("extract", "extract_with_slides") or custom_prompt:
        prompt += f"\n\n{get_taxonomy_for_prompt()}"

    return prompt


def _upload_and_wait(client, path: Path, config: dict):
    """Upload a file via the Gemini File API and poll until ACTIVE."""

    polling_sec = config.get("gemini", {}).get("polling_interval_sec", 5)
    upload_timeout = config.get("gemini", {}).get("upload_timeout_sec", 300)

    # Warn about large files that may OOM during upload
    size_mb = path.stat().st_size / (1024 * 1024) if path.exists() else 0
    if size_mb > 300:
        log.warning(
            "File %s is %.0f MB — compression is recommended to avoid memory issues",
            path.name,
            size_mb,
        )

    log.info("Uploading %s to Gemini File API...", path.name)
    try:
        uploaded = client.files.upload(file=path)
    except MemoryError:
        raise ExtractionError(
            f"File too large for upload without compression ({size_mb:.0f} MB). "
            f"Use compression (remove --no-compress flag) or reduce file size: {path.name}"
        )

    deadline = time.time() + upload_timeout
    while True:
        file_state = uploaded.state
        state_str = file_state.name if hasattr(file_state, "name") else str(file_state)

        if state_str == "ACTIVE":
            log.info("File %s is ACTIVE", path.name)
            return uploaded
        if state_str == "FAILED":
            raise ExtractionError(f"File upload failed for {path.name}")
        if time.time() > deadline:
            raise ExtractionError(f"File upload timed out after {upload_timeout}s for {path.name}")

        log.debug("File state: %s, waiting %ss...", state_str, polling_sec)
        time.sleep(polling_sec)
        uploaded = client.files.get(name=uploaded.name)


def _slides_from_json(slides_data: list) -> list[SlideAnalysis]:
    result = []
    for i, s in enumerate(slides_data or []):
        result.append(
            SlideAnalysis(
                slide_number=int(s.get("slide_number") or (i + 1)),
                frame_index=int(s.get("frame_index") or 0),
                slide_title=s.get("slide_title") or "",
                timestamp_approx=s.get("timestamp_approx") or "",
                speaker_insight=s.get("speaker_insight") or "",
                so_what=s.get("so_what") or "",
                critical_notes=s.get("critical_notes") or None,
                key_facts=s.get("key_facts") or [],
            )
        )
    return result


def _result_from_json(data: dict, source_file: SourceFile, tokens: int) -> ExtractionResult:
    return ExtractionResult(
        source_file=source_file,
        title=data.get("title") or source_file.name,
        summary=data.get("summary") or "",
        key_points=normalize_string_list(data.get("key_points") or []),
        topics=normalize_string_list(data.get("topics") or []),
        people=normalize_string_list(data.get("people") or []),
        products=normalize_string_list(data.get("products") or []),
        content_type=data.get("content_type") or data.get("type") or "unknown",
        language=data.get("language") or "en",
        quality=data.get("quality") or "medium",
        duration_min=data.get("duration_min"),
        transcript_excerpt=data.get("transcript_excerpt") or "",
        slides=_slides_from_json(data.get("slides")),
        raw_json=data,
        tokens_used=tokens,
        source_type=data.get("source_type") or "documentation",
        layer=data.get("layer") or "learning",
        domains=normalize_string_list(data.get("domains") or []),
        confidentiality=data.get("confidentiality") or "internal",
        authority=data.get("authority") or "tribal",
        client=data.get("client"),
    )


def _parse_response(response_text: str, source_file: SourceFile) -> dict:
    log.debug("Raw Gemini response for %s: %s", source_file.path.name, response_text[:1000])
    try:
        return parse_llm_json(response_text)
    except ValueError as exc:
        raise ExtractionError(f"Failed to parse JSON response for {source_file.path.name}: {exc}") from exc


def _build_locator(page_ref, file_ext: str, max_pages: int) -> dict | None:
    """Build a locator dict from an LLM page/slide reference. Validates against max."""
    if page_ref is None:
        return None
    try:
        num = int(page_ref)
    except (TypeError, ValueError):
        return None
    if num < 1 or (max_pages > 0 and num > max_pages):
        return None
    if file_ext == ".pdf":
        return {"type": "pdf", "page": num}
    elif file_ext == ".pptx":
        return {"type": "slide", "number": num}
    elif file_ext == ".docx":
        return {"type": "section", "number": num}
    return None


def _enrich_facts(
    data: dict,
    source_file: SourceFile,
    source_date: str | None,
    text_result: TextExtractionResult | None,
) -> list[dict]:
    """Build enriched facts list with source_date, locator, polarity, and validation."""
    from corp.extractor.fact_validation import validate_fact_against_source
    from corp.extractor.polarity import detect_polarity

    file_ext = source_file.path.suffix.lower()
    max_pages = 0
    source_text = ""
    if text_result:
        max_pages = text_result.page_count or text_result.slide_count or 0
        source_text = text_result.text or ""

    # LLM may return facts as list[dict] with page refs, or key_points as list[str]
    raw_facts = data.get("facts") or []
    key_points = data.get("key_points") or []

    enriched = []

    if raw_facts and isinstance(raw_facts, list) and isinstance(raw_facts[0], dict):
        # LLM returned structured facts with page/slide refs
        for f in raw_facts:
            fact_text = f.get("fact") or f.get("text") or ""
            page_ref = f.get("page") or f.get("slide") or f.get("section")
            validation = validate_fact_against_source(fact_text, source_text) if source_text else None
            entry = {
                "fact": fact_text,
                "source_date": source_date,
                "locator": _build_locator(page_ref, file_ext, max_pages),
                "polarity": detect_polarity(fact_text),
            }
            if validation:
                entry["verification_status"] = validation["status"]
                if validation["anomalies"]:
                    entry["anomalies"] = validation["anomalies"]
            enriched.append(entry)
    else:
        # Fallback: enrich key_points (no locator info available)
        for kp in key_points:
            text = kp if isinstance(kp, str) else str(kp)
            validation = validate_fact_against_source(text, source_text) if source_text else None
            entry = {
                "fact": text,
                "source_date": source_date,
                "locator": None,
                "polarity": detect_polarity(text),
            }
            if validation:
                entry["verification_status"] = validation["status"]
                if validation["anomalies"]:
                    entry["anomalies"] = validation["anomalies"]
            enriched.append(entry)

    return enriched


def _build_sampled_frame_contents(
    client,
    file: SourceFile,
    sampled_frames: list[SampledFrame],
    config: dict,
    custom_prompt: str | None = None,
) -> list:
    """
    Build Gemini content parts for video + sampled frames.

    Structure: [video_file_ref, frame_0_image, frame_1_image, ..., prompt_text]

    Frame images are sent inline as PNG bytes (small enough for inline).
    The prompt includes the frame count so Gemini knows what it received.
    """
    from google.genai import types

    prompt = _get_prompt(config, "extract_with_slides", custom_prompt=custom_prompt)

    # Upload video via File API
    uploaded = _upload_and_wait(client, file.path, config)
    parts = [types.Part.from_uri(file_uri=uploaded.uri, mime_type=uploaded.mime_type)]

    # Cap frames sent to avoid token overload
    selected = sampled_frames[:MAX_FRAMES_PER_REQUEST]
    if len(sampled_frames) > MAX_FRAMES_PER_REQUEST:
        log.warning(
            "Capping frames sent to Gemini: %d → %d",
            len(sampled_frames),
            MAX_FRAMES_PER_REQUEST,
        )

    # Add each sampled frame as inline image bytes
    for sf in selected:
        mime = mimetypes.guess_type(str(sf.path))[0] or "image/png"
        data = sf.path.read_bytes()
        parts.append(types.Part.from_bytes(data=data, mime_type=mime))

    # Append prompt with frame count hint
    parts.append(
        types.Part.from_text(
            text=(
                f"[{len(selected)} sampled frame(s) provided above, "
                f"sample_0000 through sample_{len(selected) - 1:04d}.]\n\n{prompt}"
            )
        )
    )

    return parts


# ---------------------------------------------------------------------------
# Token budget computation
# ---------------------------------------------------------------------------


def compute_token_budget(
    depth: str,
    config: dict | None = None,
    slide_count: int = 0,
    duration_min: int = 0,
) -> int:
    """Compute dynamic token budget based on extraction type and content size.

    Proportional formulas (densified prompts need more output room):
    - deep (PPTX): base 8192 + 280 per slide, cap 24576
    - multimodal (MP4): base 6144 + 150 per 5 minutes, cap 16384
    - standard: flat 8192

    Args:
        depth: "standard", "deep", or "multimodal"
        config: Unified config dict (reads llm.token_budgets). Falls back to defaults.
        slide_count: Number of slides (for deep PPTX extraction)
        duration_min: Video duration in minutes (for multimodal extraction)

    Returns:
        Token budget (max_tokens) for the LLM call
    """
    budgets = (config or {}).get("llm", {}).get("token_budgets", {})

    if depth == "deep":
        base = budgets.get("deep_base", 8192)
        per_slide = budgets.get("deep_per_slide", 280)
        maximum = budgets.get("deep_max", 24576)
        budget = min(base + slide_count * per_slide, maximum)
        log.info("Token budget: %d for depth=%s (slides=%d)", budget, depth, slide_count)
        return budget

    elif depth == "multimodal":
        base = budgets.get("multimodal_base", 6144)
        # 150 tokens per 5-minute block
        blocks = duration_min // 5 if duration_min > 0 else 0
        per_block = budgets.get("multimodal_per_5min", 150)
        maximum = budgets.get("multimodal_max", 16384)
        budget = min(base + blocks * per_block, maximum)
        log.info("Token budget: %d for depth=%s (duration=%dmin)", budget, depth, duration_min)
        return budget

    else:  # standard
        budget = budgets.get("standard", 8192)
        log.info("Token budget: %d for depth=%s", budget, depth)
        return budget


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def _select_extraction_model(
    file: SourceFile, config: dict
) -> tuple[str, str]:
    """Select Gemini model based on file type and config overrides.

    Returns:
        (model_name, routing_reason)
    """
    from corp.extractor.providers.router import select_model

    model_override = config.get("model_override")
    has_images = file.type in (FileType.VIDEO, FileType.SLIDES)
    model, routing_reason = select_model(
        file.path,
        file.size_bytes,
        has_images=has_images,
        model_override=model_override,
    )
    # "free" means Tier 1 — shouldn't reach here, but fall back to flash-lite
    if model == "free":
        model = "gemini-3.1-flash-lite"
        routing_reason = "tier3_fallback"
    return model, routing_reason


def _build_extraction_contents(
    client,
    file: SourceFile,
    config: dict,
    sampled_frames: list[SampledFrame] | None,
    custom_prompt: str | None,
    user_context: str,
    doc_type: str,
    use_deep: bool,
) -> tuple[list, str | None, int]:
    """Build Gemini request content parts based on file type.

    Returns:
        (contents, gemini_file_uri, estimated_duration_min)
    """
    from google.genai import types

    from corp.extractor.deep_prompt import build_deep_multimodal_prompt

    INLINE_SIZE_LIMIT = 20 * 1024 * 1024  # 20MB
    gemini_file_uri = None

    # Estimate duration from sampled frames for token budget
    estimated_duration_min = 0
    if sampled_frames:
        interval_sec = config.get("frame_sampling", {}).get("interval_sec", 10)
        estimated_duration_min = int(len(sampled_frames) * interval_sec / 60)

    if file.type == FileType.VIDEO and sampled_frames:
        log.info(
            "Extracting %s with %d sampled frames (~%dmin, doc_type=%s, deep=%s)...",
            file.path.name,
            len(sampled_frames),
            estimated_duration_min,
            doc_type,
            use_deep,
        )
        if use_deep:
            deep_prompt = build_deep_multimodal_prompt(doc_type)
            taxonomy = get_taxonomy_for_prompt()
            unified_prompt = _prepend_user_context(f"{deep_prompt}\n\n{taxonomy}", user_context)

            uploaded = _upload_and_wait(client, file.path, config)
            gemini_file_uri = uploaded.uri
            contents = [types.Part.from_uri(file_uri=uploaded.uri, mime_type=uploaded.mime_type)]

            selected = sampled_frames[:MAX_FRAMES_PER_REQUEST]
            if len(sampled_frames) > MAX_FRAMES_PER_REQUEST:
                log.warning("Capping frames sent to Gemini: %d → %d", len(sampled_frames), MAX_FRAMES_PER_REQUEST)
            for sf in selected:
                mime = mimetypes.guess_type(str(sf.path))[0] or "image/png"
                contents.append(types.Part.from_bytes(data=sf.path.read_bytes(), mime_type=mime))

            contents.append(
                types.Part.from_text(
                    text=(
                        f"[{len(selected)} sampled frame(s) provided above, "
                        f"sample_0000 through sample_{len(selected) - 1:04d}.]\n\n{unified_prompt}"
                    )
                )
            )
        else:
            contents = _build_sampled_frame_contents(client, file, sampled_frames, config, custom_prompt=custom_prompt)

    elif file.type in (FileType.VIDEO, FileType.AUDIO):
        log.info("Extracting %s (no frames)...", file.path.name)
        prompt = _prepend_user_context(_get_prompt(config, "extract", custom_prompt=custom_prompt), user_context)
        uploaded = _upload_and_wait(client, file.path, config)
        gemini_file_uri = uploaded.uri
        contents = [
            types.Part.from_uri(file_uri=uploaded.uri, mime_type=uploaded.mime_type),
            types.Part.from_text(text=prompt),
        ]

    elif file.type in (FileType.DOCUMENT, FileType.SLIDES):
        log.info("Extracting %s (%s)...", file.path.name, file.type.value)
        prompt = _prepend_user_context(_get_prompt(config, "extract", custom_prompt=custom_prompt), user_context)
        if file.size_bytes > INLINE_SIZE_LIMIT:
            uploaded = _upload_and_wait(client, file.path, config)
            contents = [
                types.Part.from_uri(file_uri=uploaded.uri, mime_type=uploaded.mime_type),
                types.Part.from_text(text=prompt),
            ]
        else:
            mime = mimetypes.guess_type(str(file.path))[0] or "application/octet-stream"
            contents = [
                types.Part.from_bytes(data=file.path.read_bytes(), mime_type=mime),
                types.Part.from_text(text=prompt),
            ]

    elif file.type in (FileType.NOTE, FileType.TRANSCRIPT, FileType.SPREADSHEET):
        log.info("Extracting %s (text)...", file.path.name)
        prompt = _prepend_user_context(_get_prompt(config, "extract", custom_prompt=custom_prompt), user_context)
        try:
            text_content = file.path.read_text(encoding="utf-8", errors="replace")
        except Exception as exc:
            raise ExtractionError(f"Could not read {file.path.name}: {exc}") from exc
        contents = [types.Part.from_text(text=f"{prompt}\n\n--- FILE CONTENT ---\n{text_content[:50000]}")]

    else:
        raise ExtractionError(f"Unsupported file type {file.type} for {file.path.name}")

    return contents, gemini_file_uri, estimated_duration_min


def _assemble_extraction_result(
    data: dict,
    file: SourceFile,
    tokens: int,
    use_deep: bool,
    doc_type: str,
    model: str,
    routing_reason: str,
    user_context: str,
    gemini_file_uri: str | None,
) -> ExtractionResult:
    """Post-process extraction data and build ExtractionResult."""
    from corp.extractor.freshness import compute_freshness_fields

    # Handle deep extraction: extract overlay from doc_type-specific key
    overlay_data = {}
    if use_deep:
        overlay_key = f"{doc_type}_overlay"
        if overlay_key in data:
            overlay_data = data.pop(overlay_key) or {}

    # Always preserve raw data so key_facts/entities flow to output
    raw_data = copy.deepcopy(data)

    # Post-process: normalize terms, apply taxonomy, cap cardinality, build links line
    pp = post_process_extraction(
        raw_result=data,
        source_tool="knowledge-extractor",
        source_file=str(file.path),
    )
    if pp.changes:
        log.debug("Normalized: %s", pp.changes)

    result = _result_from_json(pp.data, file, tokens)
    result.links_line = pp.links_line
    result.validation_result = pp.validation_result.value
    result.raw_json = raw_data

    # Deep extraction v2 metadata
    result.doc_type = doc_type
    result.depth = "deep" if use_deep else "standard"
    result.extraction_version = 2 if use_deep else 1
    result.overlay = overlay_data

    # RFP agent enrichment: source_date, locator, polarity
    result.source_date = extract_source_date(file.path)
    result.facts = _enrich_facts(data, file, result.source_date, None)

    # Freshness tracking
    result.freshness = compute_freshness_fields(file.path)

    # Store Gemini file URI for transcript reuse
    result.gemini_file_uri = gemini_file_uri

    # Provenance metadata
    result.model_used = model
    result.routing_reason = routing_reason
    result.prompt_version = "deep_v2" if use_deep else "standard_v1"
    result.extraction_cost_usd = _estimate_gemini_cost(model, tokens)
    result.user_context = user_context

    log.info(
        "Extracted: '%s' | slides=%d | doc_type=%s | deep=%s"
        " | overlay=%s | key_facts=%d | topics=%s | tokens=%d | model=%s | routing=%s",
        result.title,
        len(result.slides),
        doc_type,
        use_deep,
        bool(overlay_data),
        len(raw_data.get("key_facts") or []),
        result.topics[:3],
        tokens,
        model,
        routing_reason,
    )
    return result


def extract_knowledge(
    file: SourceFile,
    config: dict,
    sampled_frames: list[SampledFrame] | None = None,
    custom_prompt: str | None = None,
    user_context: str = "",
) -> ExtractionResult:
    """
    Send a file to Gemini and return structured extracted knowledge.

    Strategy:
    - VIDEO + sampled_frames → File API upload + inline frame images + extract_with_slides prompt
      Gemini identifies unique slides, returns slides[] with frame_index references
    - VIDEO / AUDIO (no frames) → File API upload + extract prompt
    - DOCUMENT / SLIDES > 20MB → File API upload + extract prompt
    - DOCUMENT / SLIDES ≤ 20MB → inline bytes + extract prompt
    - NOTE / TRANSCRIPT / SPREADSHEET → text embedded in prompt

    Args:
        file: SourceFile to extract from
        config: Unified config dict from load_config()
        sampled_frames: Time-sampled frames from sampler.py (video only)

    Returns:
        ExtractionResult with slides[] populated when sampled_frames given

    Raises:
        ExtractionError: Caller logs and skips
    """
    from google.genai import types

    from corp.extractor.doc_type_classifier import (
        classify_doc_type_hybrid,
        should_extract_deep,
    )

    client = _get_client(config)
    model, routing_reason = _select_extraction_model(file, config)

    # Classify doc type BEFORE Gemini call
    _doc_type, _conf, _method = classify_doc_type_hybrid(file.path.name)
    doc_type = _doc_type or "general"
    use_deep = should_extract_deep(doc_type) and custom_prompt is None

    # Build content parts for the request
    contents, gemini_file_uri, duration_min = _build_extraction_contents(
        client, file, config, sampled_frames, custom_prompt, user_context, doc_type, use_deep
    )

    # Compute dynamic token budget and call Gemini
    multimodal_budget = compute_token_budget(
        depth="multimodal",
        config=config,
        duration_min=duration_min,
    )
    response = client.models.generate_content(
        model=model,
        contents=contents,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            max_output_tokens=multimodal_budget,
        ),
    )

    response_text = response.text or ""
    tokens = 0
    if hasattr(response, "usage_metadata") and response.usage_metadata:
        tokens = getattr(response.usage_metadata, "total_token_count", 0) or 0

    data = _parse_response(response_text, file)

    return _assemble_extraction_result(
        data, file, tokens, use_deep, doc_type,
        model, routing_reason, user_context, gemini_file_uri,
    )


def _haiku_enrichment(
    existing_facts: list[str],
    source_text: str,
    source_file: SourceFile,
    source_date: str | None,
    text_result: TextExtractionResult | None,
) -> list[dict]:
    """Call Haiku to extract additional facts not captured by Gemini.

    Returns enriched fact dicts tagged with source_extractor="haiku_enrichment".
    Returns empty list on failure (non-blocking).
    """
    if not source_text or not existing_facts:
        return []

    try:
        import json

        from corp.extractor.fact_validation import (
            validate_fact_against_source,
        )
        from corp.extractor.polarity import detect_polarity
        from corp.extractor.providers.base import ExtractionRequest
        from corp.extractor.providers.router import get_provider

        model = "claude-haiku-4-5-20251001"
        provider = get_provider(model)

        existing_json = json.dumps(existing_facts, indent=2)
        # Cap source text to avoid excessive input
        capped_text = source_text[:40000]

        request = ExtractionRequest(
            system_prompt=(
                "You are a fact extraction specialist. Given existing extracted facts "
                "and raw source text, identify ADDITIONAL specific factual claims not "
                "already captured."
            ),
            user_prompt=(
                f"EXISTING FACTS:\n{existing_json}\n\n"
                f"SOURCE TEXT:\n{capped_text}\n\n"
                "Extract additional key_facts not already in the list above. "
                "Each fact must contain at least one specific number, date, metric, "
                "company name, or product detail. Output JSON array of strings only. "
                "If no additional facts found, return empty array []."
            ),
            model=model,
            max_tokens=4096,
        )

        response = provider.extract(request)
        new_facts_raw = json.loads(response.text)

        if not isinstance(new_facts_raw, list):
            return []

        enriched = []
        for fact_text in new_facts_raw:
            if not isinstance(fact_text, str) or not fact_text.strip():
                continue
            entry = {
                "fact": fact_text.strip(),
                "source_date": source_date,
                "locator": None,
                "polarity": detect_polarity(fact_text),
                "source_extractor": "haiku_enrichment",
            }
            if source_text:
                validation = validate_fact_against_source(fact_text, source_text)
                entry["verification_status"] = validation["status"]
                if validation["anomalies"]:
                    entry["anomalies"] = validation["anomalies"]
            enriched.append(entry)

        return enriched

    except Exception as exc:
        log.warning("Haiku enrichment failed for %s: %s", source_file.path.name, exc)
        return []


def _render_pdf_to_slides(pdf_path: Path, temp_dir: Path) -> list[Path]:
    """Render PDF pages as slide PNGs using PyMuPDF."""
    import fitz

    slides_dir = temp_dir / "slides"
    slides_dir.mkdir(parents=True, exist_ok=True)

    doc = fitz.open(str(pdf_path))
    paths = []
    for i, page in enumerate(doc, 1):
        mat = fitz.Matrix(2, 2)  # 2x zoom for quality
        pix = page.get_pixmap(matrix=mat)
        png_path = slides_dir / f"slide_{i:03d}.png"
        pix.save(str(png_path))
        paths.append(png_path)
    doc.close()
    return paths


def _truncate_large_pdf(
    file_path: Path,
    size_bytes: int,
    max_pages: int = 50,
) -> tuple[Path, bool, int, Path | None]:
    """Truncate large PDFs for multimodal upload.

    Returns:
        (pdf_path, was_truncated, page_count, temp_dir_to_clean)
    """
    import tempfile

    try:
        import fitz

        doc = fitz.open(str(file_path))
        page_count = len(doc)
        doc.close()
    except Exception:
        return file_path, False, 0, None

    if page_count <= max_pages and size_bytes <= 30 * 1024 * 1024:
        return file_path, False, page_count, None

    log.info(
        "Large PDF: %d pages, %.1f MB — truncating to %d pages for multimodal",
        page_count,
        size_bytes / (1024 * 1024),
        max_pages,
    )
    try:
        import fitz

        temp_dir = Path(tempfile.mkdtemp(prefix="cke_pdf_trunc_"))
        doc = fitz.open(str(file_path))
        truncated = fitz.open()
        truncated.insert_pdf(doc, to_page=min(max_pages - 1, len(doc) - 1))
        truncated_path = temp_dir / f"truncated_{file_path.name}"
        truncated.save(str(truncated_path))
        truncated.close()
        doc.close()
        return truncated_path, True, page_count, temp_dir
    except Exception as exc:
        log.warning("PDF truncation failed: %s — uploading full PDF", exc)
        return file_path, False, page_count, None


def _render_cover_page(file_path: Path) -> list[Path]:
    """Render first page of PDF as cover PNG. Returns list of image paths."""
    import tempfile

    try:
        import fitz

        cover_dir = Path(tempfile.mkdtemp(prefix="cke_pdf_cover_"))
        doc = fitz.open(str(file_path))
        mat = fitz.Matrix(2, 2)  # 2x zoom for quality
        pix = doc[0].get_pixmap(matrix=mat)
        cover_path = cover_dir / "cover_001.png"
        pix.save(str(cover_path))
        doc.close()
        log.info("Rendered cover page PNG for %s", file_path.name)
        return [cover_path]
    except Exception as exc:
        log.warning("Failed to render cover page PNG: %s", exc)
        return []


def _run_haiku_enrichment(
    result: ExtractionResult,
    data: dict,
    file: SourceFile,
    text_result: TextExtractionResult,
) -> None:
    """Run Haiku enrichment pass and update result in-place."""
    enrichment_facts = _haiku_enrichment(
        existing_facts=[f.get("fact", "") for f in result.facts],
        source_text=text_result.text or "",
        source_file=file,
        source_date=result.source_date,
        text_result=text_result,
    )
    if enrichment_facts:
        result.facts.extend(enrichment_facts)
        existing_kf = result.raw_json.get("key_facts") or []
        result.raw_json["key_facts"] = existing_kf + [f["fact"] for f in enrichment_facts]
        log.info("Haiku enrichment added %d facts for %s", len(enrichment_facts), file.path.name)


def _try_pdf_multimodal(
    file: SourceFile,
    config: dict,
    text_result: TextExtractionResult,
    user_context: str = "",
) -> ExtractionResult | None:
    """Backward-compat shim — delegates to PDFMultimodalStrategy."""
    from corp.extractor.strategies.pdf_multimodal import PDFMultimodalStrategy

    return PDFMultimodalStrategy().extract(file, config, text_result, user_context=user_context)


def _try_pptx_pdf_multimodal(
    file: SourceFile,
    config: dict,
    text_result: TextExtractionResult,
    user_context: str = "",
) -> ExtractionResult | None:
    """Backward-compat shim — delegates to PPTXPdfMultimodalStrategy."""
    from corp.extractor.strategies.pptx_pdf_multimodal import PPTXPdfMultimodalStrategy

    return PPTXPdfMultimodalStrategy().extract(file, config, text_result, user_context=user_context)


def extract_from_text(
    file: SourceFile,
    config: dict,
    text_result: TextExtractionResult,
    custom_prompt: str | None = None,
    user_context: str = "",
) -> ExtractionResult:
    """
    Tier 2: Send pre-extracted text to AI provider (Claude Haiku or Gemini).

    Routes through a chain of extraction strategies in order:
    1. PDF multimodal (Gemini Pro with native file upload)
    2. PPTX→PDF multimodal (Gemini Pro after PDF conversion)
    3. Text provider fallback (Claude Haiku or Gemini via provider abstraction)

    Each strategy checks applicability via can_handle(), attempts extraction,
    and falls through to the next on failure or None result.

    Args:
        file: SourceFile metadata
        config: Unified config dict
        text_result: Pre-extracted text from local extraction (Tier 1)
        custom_prompt: Optional custom prompt override (bypasses multimodal strategies)

    Returns:
        ExtractionResult with AI-structured knowledge
    """
    from corp.extractor.strategies import STRATEGIES

    for strategy in STRATEGIES:
        if strategy.can_handle(file, config, text_result, custom_prompt):
            try:
                result = strategy.extract(file, config, text_result, custom_prompt, user_context)
                if result is not None:
                    return result
            except Exception as exc:
                log.warning(
                    "%s failed for %s: %s — trying next strategy",
                    strategy.name,
                    file.path.name,
                    exc,
                )

    raise ExtractionError(f"All extraction strategies exhausted for {file.path.name}")


def extract_pptx_multimodal(
    file: SourceFile,
    config: dict,
    rendered_slides: list,
    custom_prompt: str | None = None,
    user_context: str = "",
) -> ExtractionResult:
    """
    Tier 3 for PPTX: Send rendered slide PNGs to Gemini multimodal.

    Unlike video extraction, there's no video file upload — just inline
    slide images. Every rendered slide is sent (no AI selection needed
    since each slide is intentional content, unlike video frames).

    Args:
        file: SourceFile (the original .pptx)
        config: Unified config dict
        rendered_slides: List of RenderedSlide from slides.renderer
        custom_prompt: Optional custom prompt override

    Returns:
        ExtractionResult with per-slide analysis
    """
    from google.genai import types

    from corp.extractor.deep_prompt import build_deep_multimodal_prompt
    from corp.extractor.doc_type_classifier import (
        classify_doc_type_hybrid,
        should_extract_deep,
    )
    from corp.extractor.providers.router import select_model

    client = _get_client(config)
    model_override = config.get("model_override")
    model, routing_reason = select_model(
        file.path,
        file.size_bytes,
        has_images=True,
        model_override=model_override,
    )

    # --- Classify doc type BEFORE Gemini call ---
    _doc_type, _conf, _method = classify_doc_type_hybrid(file.path.name)
    doc_type = _doc_type or "general"
    use_deep = should_extract_deep(doc_type) and custom_prompt is None

    # Choose prompt: unified deep multimodal or standard extract_pptx_slides
    if use_deep:
        deep_prompt = build_deep_multimodal_prompt(doc_type)
        taxonomy = get_taxonomy_for_prompt()
        prompt = _prepend_user_context(f"{deep_prompt}\n\n{taxonomy}", user_context)
    else:
        prompt = _prepend_user_context(
            _get_prompt(config, "extract_pptx_slides", custom_prompt=custom_prompt), user_context
        )

    log.info(
        "Extracting %s via PPTX multimodal (%d slides, doc_type=%s, deep=%s)...",
        file.path.name,
        len(rendered_slides),
        doc_type,
        use_deep,
    )

    # Build content: slide images + prompt
    parts = []
    for rs in rendered_slides:
        mime = "image/png"
        data = rs.image_path.read_bytes()
        parts.append(types.Part.from_bytes(data=data, mime_type=mime))

    parts.append(
        types.Part.from_text(
            text=(
                f"[{len(rendered_slides)} slide image(s) provided above, "
                f"slides 1 through {len(rendered_slides)}.]\n\n{prompt}"
            )
        )
    )

    # --- Compute token budget ---
    slide_budget = compute_token_budget(
        depth="deep" if use_deep else "standard",
        config=config,
        slide_count=len(rendered_slides),
    )

    response = client.models.generate_content(
        model=model,
        contents=parts,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            max_output_tokens=slide_budget,
        ),
    )

    response_text = response.text or ""
    tokens = 0
    if hasattr(response, "usage_metadata") and response.usage_metadata:
        tokens = getattr(response.usage_metadata, "total_token_count", 0) or 0

    data = _parse_response(response_text, file)

    # Use shared assembly helper (eliminates ~45 lines of duplication)
    result = _assemble_extraction_result(
        data, file, tokens, use_deep, doc_type,
        model, routing_reason, user_context, None,
    )

    log.info(
        "PPTX multimodal extracted: '%s' | %d slides | doc_type=%s | deep=%s"
        " | overlay=%s | key_facts=%d | topics=%s | tokens=%d | model=%s",
        result.title,
        len(result.slides),
        doc_type,
        use_deep,
        bool(result.overlay),
        len(result.raw_json.get("key_facts") or []),
        result.topics[:3],
        tokens,
        model,
    )
    return result


def extract_local(
    file: SourceFile,
    text_result: TextExtractionResult,
) -> ExtractionResult:
    """
    Tier 1: Build ExtractionResult from locally-extracted text only (FREE).

    No API call. Uses the file name as title and the raw text as summary.
    Still post-processes through corp-os-meta for normalization.

    Args:
        file: SourceFile metadata
        text_result: Pre-extracted text from local extraction

    Returns:
        ExtractionResult with basic structure (no AI insight)
    """
    log.info(
        "Local extraction for %s (%d chars, no API call)...",
        file.path.name,
        text_result.char_count,
    )

    # Build a minimal raw result for post-processing
    raw_result = {
        "title": file.name,
        "summary": text_result.text[:2000],
        "topics": [],
        "products": [],
        "people": [],
        "type": file.type.value,
        "language": "en",
        "quality": "local",
    }

    pp = post_process_extraction(
        raw_result=raw_result,
        source_tool="knowledge-extractor",
        source_file=str(file.path),
    )

    result = _result_from_json(pp.data, file, tokens=0)
    result.links_line = pp.links_line
    result.validation_result = pp.validation_result.value

    # RFP agent enrichment: source_date, locator, polarity
    result.source_date = extract_source_date(file.path)
    result.facts = _enrich_facts(raw_result, file, result.source_date, text_result)

    # Freshness tracking
    from corp.extractor.freshness import compute_freshness_fields

    result.freshness = compute_freshness_fields(file.path)

    log.info("Tier 1 local extraction: '%s'", result.title)
    return result
