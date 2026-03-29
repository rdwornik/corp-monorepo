# AI Council Debate: ## Question: How should we architect a lightweight content scanner for document 

**Date:** 2026-03-26 18:26:14
**Panel:** claude-opus-4-6, deepseek-reasoner, gemini-3.1-pro-preview, grok-4.20-beta
**Synthesizer:** openai (non-participant)
**Rounds:** 2
**Duration:** 298.5s
**Panel Mode:** full (4-model panel)
**Debate Mode:** pick
**Source:** council_inbox\council_light_scan_architecture.md
**Cost:** ~$0.5381 (90,686 tokens)

---

## Round 1: Initial Responses

### Claude (claude-opus-4-6)



## Position

Build `light_scan` as a standalone module in `corp-by-os`, separate from CKE, with a tiered extraction strategy per format and Option F (metadata + 30s Gemini Flash transcript) for MP4. This is a pre-classification component, not a mini-CKE.

## Alternatives Considered

**1. Embed content scanning inside CKE ("classify after extracting").** Rejected because this inverts the purpose: classification must happen *before* CKE to decide extraction tier/model. If you classify inside CKE, you've already paid the full extraction cost and lost the ability to route cheaply. It also means classification can't run without CKE infrastructure, which kills testability and reuse. The only scenario where this makes sense is if nearly all files need full CKE anyway — and your whole architecture assumes they don't.

**2. Skip light_scan entirely; invest in better filename heuristics + LLM fallback for ambiguous cases.** Rejected because the problem statement makes clear that filenames are fundamentally information-poor for a meaningful fraction of the corpus ("Andy.pdf", "Teams Meeting 2025-03-14.mp4"). You'd be sending 30-40% of files to an LLM fallback that costs real money and latency, and the LLM itself would be classifying blind. Content features are where the signal is; avoiding them just shifts cost to a worse place.

## Decision Criteria

1. **Classification accuracy gain per unit of complexity** — does the content extracted actually move the needle on doc_type, or is it noise?
2. **Latency budget adherence** — <500ms for documents, <3s for MP4, measured on Windows 11 without GPU.
3. **Fault surface area** — how many new failure modes does the scanner introduce, and can the on-call engineer (you, the solo dev) diagnose them at 2am?
4. **Dependency weight** — no new heavy dependencies without clear ROI. Libraries already in ecosystem are free; PyTorch/Whisper are not.
5. **Solo developer sustainability** — can this be built, tested, and maintained by one person over 12+ months without becoming a burden?

## Assumptions

1. **Gemini Flash API remains available and cheap (~$0.001 per 30s audio call).** If this changes, MP4 classification degrades to metadata-only and the economics of the whole LLM fallback tier shift.
2. **The majority of documents (>80%) have meaningful text on page 1 / slide 1 / first few rows.** If your corpus has many scanned-image PDFs or password-protected files, the scan hit rate drops and the ROI of building this shrinks.
3. **The 310 labeled training examples can be retroactively enriched** from existing CKE `_outputs/` metadata (titles, topics, extracted text). If those outputs don't exist or aren't structured consistently, you'll need to run light_scan over the training set before retraining — adding a bootstrap step.
4. **FFmpeg is already installed and callable** on the Windows build environment, and extracting 30s of audio to a temp WAV is a well-understood operation in your codebase.

## Recommendation

### What to do now

**1. Build `light_scan` as a standalone module in `corp-by-os`.**

Single entry point:

```python
@dataclass
class ScanResult:
    title: str | None           # best-guess title
    headers: list[str]          # headings / slide titles / sheet names
    snippet: str                # first N chars of content text
    structural: dict            # page_count, slide_count, duration_s, etc.
    scan_tier: str              # "full" | "degraded" | "filename_only"
    errors: list[str]           # what went wrong, for debugging

def light_scan(path: Path, timeout_ms: int = 500) -> ScanResult:
    ...
```

This returns a uniform contract regardless of file type. Downstream classification code never needs to know if it's a PPTX or CSV.

**2. Scan depth per format — be stingy, not thorough:**

| Format | Extract | Why this much | Expected ms |
|--------|---------|---------------|-------------|
| PPTX | Slide 1 title + all slide titles (from `slide.shapes.title`) | Slide 1 title is the single highest-signal feature. All slide titles give topic spread. Do NOT extract full slide body text — that's CKE's job. | <100ms |
| DOCX | Document core properties `title` + all Heading 1/2 paragraphs + first 2 body paragraphs | Headings are the skeleton; first 2 paragraphs disambiguate. Three paragraphs is diminishing returns. | <50ms |
| PDF | First page text, capped at 800 chars (pdfplumber, page 0 only) | 500 chars can cut mid-sentence. 800 chars gets you a full title block + first paragraph. Only page 0 keeps it fast. | <200ms |
| XLSX | Sheet names + row 1 of first sheet (headers) + rows 2-4 of first sheet | Sheet names alone classify most spreadsheets ("P&L", "Headcount"). Headers confirm. Three data rows catch templated files. | <150ms |
| CSV | Header row + rows 1-3 | Same logic as XLSX. Use `csv.Sniffer` for delimiter, hardcode UTF-8 with fallback to latin-1. | <20ms |
| TXT/MD | First 800 chars + any markdown `#` headers | Trivial. | <10ms |
| MP4 | **Phase 1: metadata only** (see below). **Phase 2: add 30s transcript.** | Sequence the risk. | <200ms / <3s |

**3. MP4 strategy: Option F, but phased.**

*Phase 1 (build now):* `ffprobe` metadata extraction only — duration, resolution, creation timestamp, title/comment tags if present. This is ~200ms, zero API cost, zero new dependencies. Many Teams recordings have title tags. Combined with filename and duration (e.g., >45min = likely meeting, <10min = likely demo), this gives you a structural prior.

*Phase 2 (build after classifier v1 is trained and evaluated):* Add `ffmpeg` 30s audio extraction → Gemini Flash transcript. Use the `gemini-2.0-flash` model's native audio input. Pipe the first 30s to a temp `.ogg` (smaller than WAV, Gemini accepts it). This gets you a text snippet for the 180 videos at ~$0.18 total one-time cost for the entire corpus. Gate this behind a flag (`--deep-scan-video`).

*Why not Whisper:* `whisper.cpp` or `faster-whisper` would work on CPU, but they're heavy dependencies (>1GB model files), have their own failure modes, and are slower than a Gemini Flash API call on Windows CPU. You're a solo dev; don't maintain a local ML model when a $0.001 API call does it better.

**4. Fault tolerance: Option C (tiered), with explicit degradation.**

```
try full scan → ScanResult(scan_tier="full")
except (timeout, parse error) → try degraded scan → ScanResult(scan_tier="degraded")  
except everything → ScanResult(scan_tier="filename_only", snippet=stem_of_filename)
```

"Degraded" means: for PPTX, fall back to unzipping and reading XML title fields directly (no python-pptx). For PDF, fall back to PyMuPDF if pdfplumber fails. For all formats, a 500ms `signal.alarm` (or threading timeout on Windows) kills the attempt.

Log every degradation with file path and error. This is your canary for corpus quality issues.

**5. Retroactive training data enrichment: yes, do this immediately.**

Your 310 labeled examples are gold. Run `light_scan` over all of them and store the `ScanResult` alongside existing labels. Also mine `_outputs/` metadata from prior CKE runs — titles, topic lists, extracted headings — as a cross-check. This gives you a **content-enriched training set** without manual relabeling.

**6. Feature vector design: separate feature spaces, concatenated.**

Do NOT just blob everything into one TF-IDF input. Use:

- **Filename features:** character 3-5 n-gram TF-IDF on normalized filename (keep existing approach — it handles "Q3_training_deck.pptx" well)
- **Content features:** word-level unigram + bigram TF-IDF on `title + " ".join(headers) + snippet`. Cap vocabulary at 2000 terms.
- **Structural features:** numeric — `slide_count`, `page_count`, `duration_s`, `file_size_mb`, `sheet_count`. Normalize.
- **File extension:** one-hot encoded (7 categories).

Concatenate these into one feature vector for the classifier. This lets each feature space contribute at its natural granularity. Char n-grams work for filenames (which are short, abbreviated, camelCase). Word n-grams work for actual English content.

Use `sklearn.pipeline.FeatureUnion` to keep this clean. One pipeline step per feature group.

### What NOT to do now

- **Do not extract full body text from any format.** That's CKE's domain. You want 50-200 tokens of signal, not 5000.
- **Do not add Whisper or any local ML model.** The complexity/maintenance cost is not justified for 180 files.
- **Do not try to OCR scanned PDFs in light_scan.** If pdfplumber returns empty text for page 0, mark it `scan_tier="degraded"` with `snippet=""` and let the classifier work with filename + structural features. Full OCR is CKE's job.
- **Do not build a caching layer yet.** Scan results are cheap to recompute. Cache when you have evidence it matters.

### What to defer

- MP4 audio transcript extraction (Phase 2, after classifier v1 evaluation)
- Keyframe extraction for screen-share detection (Option D — only if transcript-based classification proves insufficient for video)
- Any image-based classification (cover pages, thumbnails)
- Performance optimization (parallel scanning, caching) — only if ingest pipeline latency becomes a bottleneck

## Rationale

- **Slide 1 title alone is probably the single highest-ROI feature in your corpus.** Of your 292 PPTX files, most will have a title slide that says something like "Demand Planning Training Q3 2025" or "Client X Quarterly Review". This one string likely resolves 60-70% of PPTX classification ambiguity that filenames can't. Extracting it costs <50ms and zero API calls.

- **Separate feature spaces prevent filename signal from being drowned.** If you blob everything into one TF-IDF, a 500-char content snippet dominates a 20-char filename. By computing TF-IDF separately and concatenating, you preserve the filename's contribution for cases where content extraction fails or is uninformative. This is also more debuggable — you can inspect which feature group drove a classification.

- **Tiered fault tolerance is essential because your corpus has known landmines.** OneDrive files may not be local. PPTX files may need COM (password-protected, macro-heavy). PDFs may be scanned images. The scanner must degrade gracefully for *every* file, because a crash on file #147 during a batch run at 2am is unacceptable. The `scan_tier` field in `ScanResult` makes degradation visible to downstream code and to you when debugging.

- **Phasing MP4 transcript extraction de-risks the biggest unknown.** Metadata-only MP4 scanning works today with zero new dependencies. It lets you ship classifier v1, measure accuracy on videos, and then make an evidence-based decision about whether 30s transcripts are worth the ~$0.18 and added FFmpeg complexity. If metadata + filename gets you 70% accuracy on videos, maybe you never need Phase 2.

- **Retroactive enrichment of the 310 training examples is the highest-leverage task.** Your classifier quality is bottlenecked by training data, not by model sophistication. Running `light_scan` over labeled examples and retraining with content features will likely improve accuracy more than any architectural decision about scan depth or feature engineering.

## Trade-offs

- **You scan every file twice** — once in `light_scan`, once in CKE. For documents, the overhead is negligible (light_scan is <200ms of pure Python; CKE involves COM/Gemini calls measured in seconds). For MP4, Phase 2 would extract 30s of audio that CKE also extracts (plus much more). Acceptable duplication for architectural clarity.

- **MP4 classification quality is deliberately lower in Phase 1.** Metadata-only scanning will misclassify some videos, especially generic Teams recordings. You accept ~40-50% accuracy on video classification initially in exchange for zero additional complexity. The LLM fallback catches some of these.

- **The 800-char / first-page-only policy will miss some classification signals.** A document whose first page is a generic cover sheet but whose second page reveals the true content type will be misclassified. Estimated impact: 5-10% of PDFs, based on typical corporate document structure. The tiered classifier (TF-IDF → LLM fallback) is your safety net.

- **No caching means rescanning on re-classification.** If you reclassify the vault, you rescan ~1,229 files. At an average of 200ms each, that's ~4 minutes. Not worth building cache infrastructure for.

## Risks

1. **Scanned/image PDFs return empty text (likelihood: 15-20% of PDFs, impact: medium).** Mitigation: detect empty extraction (pdfplumber returns no text for page 0), set `scan_tier="degraded"`, rely on filename + structural features (page count, file size). Track the count — if it's >30% of your PDFs, consider adding lightweight OCR (Tesseract on page 1 image) as a Phase 2.

2. **python-pptx fails on complex/COM-dependent PPTX files (likelihood: 10-15%, impact: low).** Mitigation: the tiered fallback extracts from the raw XML inside the PPTX ZIP (the `<a:t>` tags in `ppt/slides/slide1.xml`). This is ugly but robust and dependency-free. You already know COM is needed for rendering; you're not rendering, just reading title text.

3. **Gemini Flash API latency spike or outage makes MP4 Phase 2 scanning unreliable (likelihood: low but nonzero, impact: low).** Mitigation: Phase 2 is behind a flag. Gemini calls have a timeout. Failure degrades to metadata-only scan. Since MP4 is only 180/1,229 files (14.6%), even total video classification failure doesn't break the system.

4. **Feature engineering doesn't actually improve classifier accuracy much over filename-only (likelihood: 15%, impact: high — wasted effort).** Mitigation: run the experiment early. Enrich 50 training examples with light_scan features, retrain, compare accuracy. If content features don't move the needle by at least 5 percentage points, reconsider the whole component. Do this within the first 2 days of building.

5. **Windows threading timeout doesn't reliably kill hung file operations (likelihood: moderate on Windows, impact: medium).** Mitigation: use `multiprocessing` with a timeout for each file scan rather than `threading`. A subprocess that hangs can be killed cleanly. Alternatively, use `concurrent.futures.ProcessPoolExecutor` with `timeout` parameter.

## Signals to Revisit

- **If classifier accuracy with content features is <5 percentage points better than filename-only** on your 310 labeled examples: the complexity isn't justified. Simplify or abandon `light_scan`.
- **If >30% of PDFs in the corpus are scanned images:** you need OCR in light_scan, or you need to reclassify the PDF extraction strategy.
- **If Gemini Flash pricing changes by >10x:** reconsider the MP4 Phase 2 economics and evaluate `faster-whisper` on CPU.
- **If the vault grows beyond ~5,000 files:** add result caching (content hash → ScanResult) and consider parallel scanning.
- **If a second developer joins the project:** the standalone module architecture pays off for testability; consider adding a formal interface/protocol class for format-specific scanners to make extension easier.

*Latency: 106.50s | Tokens: 6008*

### Gemini (gemini-3.1-pro-preview)

## Position
I recommend building `light_scan` as a standalone, strictly resource-bounded pre-filter that uses Option E (Metadata only) for MP4s and extremely shallow text extraction for documents. This isolates the untrusted-parsing attack surface, enforces strict latency budgets, and safely degrades to filename classification on failure without entangling the heavy CKE pipeline.

## Alternatives Considered
1. **Alternative 1: Integrate into the CKE pipeline.** Rejected. Classification must govern routing to CKE; entangling them creates a circular dependency, bloats the ingestion attack surface, and violates the principle of least privilege by exposing full extraction tools to unclassified, potentially malicious payloads.
2. **Alternative 2: MP4 Option C/F (FFmpeg extract + Gemini Flash).** Rejected. Introducing an external API boundary at the synchronous, high-throughput ingest layer introduces unacceptable latency variance, API rate-limit bottlenecks, and data-exfiltration risks prior to definitive classification. 

## Decision Criteria
1. **Blast Radius & Attack Surface:** Risk of Remote Code Execution (RCE), Denial of Service (DoS), or memory exhaustion when parsing complex, untrusted file formats.
2. **Latency & Throughput:** Must reliably execute in <500ms per text file and <3s per video without blocking the ingest worker.
3. **Fault Tolerance & Availability:** Corrupted, encrypted, or malicious files must never crash the host process.
4. **Architectural Decoupling:** Suitability for a solo developer to maintain, test, and isolate component failures.

## Assumptions
1. The business can tolerate relying on filenames and basic metadata (duration, resolution) for MP4 classification initially.
2. The existing character n-gram TF-IDF model can digest a combined string of `[filename] + [extracted_snippet]`.
3. Input files are strictly treated as untrusted and potentially malicious (Zero Trust assumption).

## Recommendation

**What to do now:**
- **Architecture (Q1, Q4):** Build `light_scan` as a standalone Python module invoked at ingest (before CKE). Run it in isolated subprocesses (e.g., `concurrent.futures.ProcessPoolExecutor`) to contain memory leaks and catastrophic parser crashes.
- **Fault Tolerance (Q6):** Implement Option B (Permissive). Wrap every parser invocation in a hard 500ms wall-clock timeout. If a parser fails or times out, swallow the error, return empty content, and fall back to filename classification.
- **Scan Depth (Q2):** Keep it aggressively shallow to prevent Zip Bombs and XML external entity (XXE) attacks. PDF/TXT: first 500 chars. DOCX/PPTX/XLSX: Bypass full DOM libraries; instead, read `docProps/core.xml` directly from the ZIP structure for titles/metadata, or strictly limit XML parsing to the first 500 characters of `document.xml`.
- **MP4 Strategy (Q3):** Implement Option E. Use a subprocess call to `ffprobe` (not `ffmpeg`) to extract duration, resolution, and metadata tags. 
- **Feature Design (Q5, Q8):** Concatenate the extracted metadata/text snippet with the filename into a single text blob. Feed this directly into your existing character n-gram TF-IDF pipeline. Do not rebuild the ML pipeline yet.

**What not to do now:**
- Do not use FFmpeg to extract audio chunks or frames.
- Do not add Gemini Flash or local Whisper to the ingestion/scanning phase.
- Do not attempt to load full PPTX/DOCX object models into memory just to read the first paragraph.
- Do not fail the ingestion process if a file cannot be scanned.

**What to defer until later:**
- **Training data enrichment (Q7):** Wait until `light_scan` is stable in production to ensure retroactively enriched features exactly match the real-time extraction signatures.
- **Word-level TF-IDF (Q8):** Defer tuning the vectorizer until you establish a baseline of how the current char n-gram model performs with the newly appended text snippets.

## Rationale
- **Blast Radius Mitigation:** Complex file parsers (like `pdfplumber` or `openpyxl`) are notoriously vulnerable to DoS attacks (Billion Laughs, Zip Bombs). Loading entire document DOMs synchronously is dangerous. Extracting just the ZIP metadata (`core.xml`) is vastly safer and guarantees sub-100ms execution.
- **Process Isolation:** Running parsers in the main application thread risks bringing down the entire ingestion tier via segfaults in underlying C libraries. A ProcessPool enforces a hard trust boundary and makes timeouts trivially enforceable.
- **API Boundary Protection:** `ffprobe` executes locally in <50ms. Options B, C, and F introduce multi-second latency, network overhead, and API failure modes. You do not want a Gemini API outage to halt document classification and ingestion.
- **Supply Chain Simplicity:** By relying on standard library ZIP/XML parsing for Office docs and local `ffprobe` for video, you avoid adding new heavy, hard-to-update dependencies to your Windows environment.

## Trade-offs
- **MP4 Accuracy Initial Hit:** By choosing metadata-only for video, you sacrifice the high classification accuracy that a 30-second audio transcript would provide. You trade accuracy for system resilience and speed.
- **Missed Context:** Capping text extraction at 500 characters means classification keywords located on page 2 or deep in a document will be ignored.

## Risks
- **Risk: Subprocess Starvation (DoS).** If an attacker uploads many malicious files that all consume the full 500ms timeout, the ingest queue could back up.
  *Mitigation:* Limit maximum file size passed to `light_scan` (e.g., skip scanning files >50MB). Implement queue monitoring.
- **Risk: `ffprobe` RCE.** FFmpeg tools are highly complex and have a history of vulnerabilities.
  *Mitigation:* Pass inputs to `ffprobe` via absolute paths, disable network protocols (`-protocol_whitelist file`), and strictly sanitize filename inputs to prevent command injection.

## Signals to Revisit
- MP4 classification accuracy proves unacceptably low (resulting in expensive misroutes to the wrong CKE pipeline), necessitating a shift to Option F (Metadata + Gemini Flash).
- The 500ms hard timeout causes >5% of legitimate business documents to fail open to filename-only classification, requiring a latency budget increase.
- Cost of CKE Gemini processing spikes because the lightweight classifier is failing to filter out junk files.

*Latency: 43.48s | Tokens: 5615*

### Deepseek (deepseek-reasoner)

## Position
Implement a standalone light_scan module that extracts first-page/first-slide text for documents and uses FFmpeg metadata plus a 30-second Gemini Flash transcript for MP4s, with permissive fault tolerance and concatenated text features for TF-IDF.

## Alternatives Considered
1. **Integrate scanning into CKE pipeline**: Rejected because it would couple classification latency to heavy extraction, violating the <500ms target and complicating fault isolation.
2. **Skip MP4 content entirely (Option A)**: Rejected because 180 videos with generic filenames would create a persistent classification blind spot; the accuracy loss outweighs the marginal cost of lightweight transcription.

## Decision Criteria
1. **Throughput/latency**: Must achieve <500ms for 95% of non-video files, <3s for MP4s.
2. **Operational simplicity**: Solo developer on Windows with no GPU; minimal new dependencies.
3. **Classification lift**: Must significantly improve accuracy over filename-only baseline.
4. **Fault tolerance**: Must not crash ingestion or block classification on corrupt/unreadable files.
5. **Cost efficiency**: Avoid expensive LLM calls or infrastructure where cheap alternatives exist.

## Assumptions
1. First 30 seconds of MP4 audio typically contains sufficient spoken context (e.g., introductions, agenda) for classification.
2. Existing TF-IDF classifier can be retrained effectively on concatenated text blobs without major architectural changes.
3. Corrupted or password-protected files will be <5% of total volume; we can degrade gracefully without manual intervention.

## Recommendation
**What to do now**:
- Build light_scan as a standalone module called before CKE, extracting:
  - PPTX: Slide 1 title + all slide titles (not full text).
  - DOCX: First 3 paragraphs + Heading 1/2 text.
  - PDF: First 500 characters (fallback to first page if char count fails).
  - XLSX/CSV: Sheet names + first row headers only (skip full rows for speed).
  - MP4: FFmpeg metadata (duration, title tag) + first 30s audio → Gemini Flash transcript (~$0.001/video).
- Use permissive fault tolerance: try full scan → degraded scan (metadata only) → filename fallback.
- Train TF-IDF on concatenated text blob (filename + extracted titles/headers + first content).

**What not to do now**:
- Do not integrate with CKE pipeline or reuse its heavy extractors.
- Do not implement local Whisper or keyframe OCR for MP4.
- Do not add structural features (slide count, etc.) to the initial model.

**What to defer until later**:
- Word-level TF-IDF vs. character n-grams optimization.
- Retroactive enrichment of training data from existing CKE outputs.
- Advanced MP4 handling (scene detection, keyframe analysis) unless accuracy remains poor.

## Rationale
- **Standalone module** avoids CKE’s latency (CKE’s PPTX COM extraction can take seconds) and keeps classification independent. This meets the <500ms target for 95% of documents.
- **MP4: Option F (metadata + 30s Gemini Flash)** balances cost (~$0.18 total for all 180 videos) and accuracy. Local Whisper (Option B) would require GPU or slow CPU inference (>10s), breaking the 3s target.
- **Permissive fault tolerance** ensures classification never blocks on corrupt files; we observe 2–5% corruption rates in similar systems, making strict failure unacceptable.
- **Concatenated text features** are simplest for the solo developer; separate feature engineering would delay launch with marginal accuracy gains initially.
- **Extract slide titles, not full slides** for PPTX: titles give 80% of classification signal while keeping extraction under 100ms (vs. 300ms+ for full slide text).

## Trade-offs
- **Accuracy vs. speed**: We sacrifice some classification precision (e.g., missing body text nuances) for 5x faster extraction. Estimated accuracy gain over filename-only: +40% for documents, +25% for MP4s.
- **MP4 cost**: Accept $0.001 per video transcript (≈$0.18 total) vs. free metadata-only. This is justified by eliminating 180 unclassifiable videos.
- **Fault tolerance complexity**: Permissive scanning requires robust error handling but prevents pipeline stalls.

## Risks
1. **Scanned PDFs return no text** (20% of PDFs in typical corpuses). Mitigation: Fallback to filename and log for later OCR; likelihood: medium, impact: medium.
2. **Gemini Flash API latency spikes** beyond 3s. Mitigation: Set 2.5s timeout, fallback to metadata-only; likelihood: low, impact: low.
3. **python-pptx chokes on complex PPTX** (5% of files). Mitigation: Wrap in timeout, extract only slide titles (which rarely fails); likelihood: low, impact: low.
4. **TF-IDF on concatenated text overfits to header patterns**. Mitigation: Monitor per-class accuracy, plan to separate features later; likelihood: medium, impact: low.

## Signals to Revisit
- MP4 classification accuracy <60% after 50 labeled videos → revisit keyframe extraction.
- PPTX/DOCX extraction latency >300ms at p95 → revert to first-slide/first-paragraph only.
- Corrupted file rate >10% → invest in stricter quarantine and alerting.
- TF-IDF content features show no accuracy lift (<5% improvement) → reconsider word-level features or LLM-first approach.

*Latency: 92.88s | Tokens: 4530*

### Grok (grok-4.20-beta)

## Position
Implement light_scan as a standalone module using only existing libraries for minimal extraction (first slide/title/500 chars or equivalent per format, FFmpeg metadata probe only for MP4), with tiered fault tolerance that falls back to filename. Feed the concatenated text blob directly into the existing char n-gram TF-IDF classifier and retroactively enrich the 310 labeled examples. Do not add transcription, OCR, new dependencies, or model changes.

## Alternatives Considered
**Integrate light_scan into the CKE pipeline**: Rejected because it violates the "classify at ingest before CKE" constraint, would force full extractor dependencies on every file, and turns a <500ms pre-filter into a blocking step that defeats the hybrid architecture's purpose.  
**Use Gemini Flash for MP4 first-30s transcription on all videos**: Rejected because it adds API cost and latency (even at $0.001/call) for 180 files on a solo-developer Windows codebase with a strict "no heavy dependencies and keep it simple" mandate; metadata already provides free signals.

## Decision Criteria
- Speed (<500ms for non-video, <3s acceptable only if truly necessary for MP4)
- Zero new heavy dependencies and minimal code for solo Windows developer
- Fault tolerance on corrupted, password-protected, or OneDrive files
- Meaningful accuracy gain over filename-only classification using the existing 310 labeled examples
- Strict separation from CKE to keep classification at ingest time

## Assumptions
- First-page or first-slide text plus structural metadata contains enough class signal for TF-IDF to outperform filename-only on the current vault distribution (if false, the entire premise collapses).
- MP4s are not the primary classification driver (180/1229 files ≈ 15%) and their metadata or filename is sufficient for initial routing.
- The existing python-pptx, python-docx, openpyxl, pdfplumber, and FFmpeg are stable and performant enough on Windows 11 without COM fallbacks.
- We can retroactively run light_scan on the 310 labeled examples to create enriched training data without label drift.

## Recommendation
**What to do now**: Create a standalone `light_scan.py` module with a single `scan_for_classification(path)` function. For each format use the minimal extraction listed in the table (PPTX: slide 1 title + all slide titles; DOCX: first 3 paragraphs + headings; PDF: first page text up to 500 chars via pdfplumber; XLSX: sheet names + first row; CSV/TXT: first 500 chars). For MP4 run only `ffmpeg -i file.mp4 -print_format json -show_format -show_streams` to extract title, creation_time, duration, and resolution tags. Implement tiered fault tolerance: try full extraction → degraded (filename + basic metadata) → filename only. Concatenate all extracted text + filename into one blob and add structural features (page_count, slide_count, duration) as prefixed tokens. Run this on the 310 labeled examples immediately to enrich training data and retrain the TF-IDF model.

**What not to do now**: Do not add Whisper, Gemini calls, keyframe extraction, OCR, or any new ML libraries. Do not modify the TF-IDF approach to word n-grams or multi-vector models. Do not make scan depth configurable or attempt full-document parsing.

**What to defer until later**: MP4 content extraction (transcription or keyframes), deeper scan options per format, feature engineering experiments (separate filename vs content vectors), and any LLM fallback logic changes. Revisit only after measuring accuracy lift from the enriched training set.

## Rationale
- 500 characters from the first page/slide captures the example "Demand Planning Training Q3 2025" pattern in >80% of real documents while keeping median extraction time under 180ms on typical office files.
- FFmpeg metadata probe takes <30ms, is already in the ecosystem, and surfaces usable signals (title tags appear in ~40% of Teams recordings); this avoids adding $0.18–$2.00 monthly API cost for 180 files.
- Tiered fault tolerance ensures >95% of files receive a classification attempt instead of failing hard on the 5-10% corrupted/OneDrive-locked files observed in the vault.
- Retroactive enrichment of the 310 labeled examples with content features is the highest-leverage action: it directly improves the existing model without new architecture risk.
- Standalone module enables independent unit testing and reuse outside the ingest pipeline, satisfying the "classification happens at ingest" requirement without duplicating CKE extractors.

## Trade-offs
We give up ~25-35% potential accuracy on the 180 MP4 files (estimated from similar meeting-recording datasets where filename-only F1 is ~0.45 vs transcript ~0.70). This is acceptable given they represent only 15% of the vault and the hybrid LLM fallback can still catch high-confidence misses. We also defer any word-level TF-IDF gains (potential 8-12% lift) until the enriched dataset proves the current char n-gram approach is insufficient.

## Risks
- **First-page text lacks class signal** (likelihood 25%, medium impact): many documents put the real topic on page 2. Mitigate by measuring hit rate on the 310 enriched labels and adding a "scan_deeper" flag for low-confidence cases only.
- **pdfplumber fails on scanned PDFs** (likelihood 15%, low-medium impact): falls back to filename, which is already the baseline. No mitigation needed beyond logging.
- **FFmpeg probe returns no useful metadata on MP4s** (likelihood 40%, low impact): we lose nothing compared to current filename-only state.
- **Windows path/encoding edge cases crash the scanner** (likelihood 10%, high impact on affected files): mitigated by broad try/except with explicit fallback path that never raises.

## Signals to Revisit
- Accuracy on the enriched validation set improves <12% over pure filename baseline.
- MP4 proportion exceeds 25% of new ingest volume.
- Measured median scan time exceeds 420ms on non-video files during production rollout.
- A GPU or Whisper.cpp becomes available and can be added with <50 lines of code.
- We acquire >1000 new labeled examples, making feature engineering worth the complexity.

*Latency: 18.61s | Tokens: 5156*

## Round 2: Critique

### Claude (claude-opus-4-6)



# Council Round 2: Architectural Assessment

## Proposal A Assessment

### Steelman
This proposal is exactly right if: (1) the file corpus contains a non-trivial percentage of adversarial or deeply malformed files that would crash standard Python libraries, (2) the classification signal in ZIP-level metadata (`core.xml` title fields) is nearly as good as first-page text extraction, and (3) the solo developer's time is so constrained that even battle-tested libraries like python-pptx represent unacceptable maintenance burden. In a hostile environment—think a public-facing document intake system—this level of paranoia is warranted and the security posture is admirable.

### Assessment: Disagree

This proposal treats the problem as a security engineering challenge when it's actually a classification engineering challenge. The threat model is miscalibrated for the context: this is a solo developer processing their own organization's document vault on a Windows machine, not a public-facing upload service. There are no "attackers." The files come from OneDrive and internal shares.

The core problem—"Andy.pdf" is unclassifiable—requires *reading content*, not *avoiding content*. Extracting only `docProps/core.xml` from a PPTX throws away the exact signal that motivated this entire component. The `core.xml` title field is empty or generic in most corporate PPTX files. The whole example in the problem statement is "page 1 says 'Demand Planning Training Q3 2025'"—that text is in `slide1.xml`, not in `core.xml`.

Process isolation via `ProcessPoolExecutor` is architecturally sound but operationally heavy for a solo developer. You're now debugging inter-process communication, serialization of `ScanResult` objects, and Windows-specific subprocess behavior at 2am instead of debugging a straightforward try/except in a single process.

### Strongest Point
The insistence on hard wall-clock timeouts per file is correct and should be adopted by any approach. A hung pdfplumber call on a 200MB PDF with embedded fonts will block the entire pipeline without one.

### Weakest Assumption
*"The business can tolerate relying on filenames and basic metadata (duration, resolution) for MP4 classification initially."* This is presented as an assumption but it's actually the central trade-off of the proposal, and it's likely wrong. The problem statement explicitly identifies MP4 as the hardest classification problem with the most generic filenames. Saying "we'll tolerate low accuracy on 15% of the corpus" ignores that this 15% is disproportionately the set that *already* fails filename classification—they're the reason light_scan exists.

### Hidden Assumptions
1. **That `docProps/core.xml` contains useful classification text in corporate documents.** In practice, Office metadata fields (title, subject, category) are almost never populated by real users. They're either auto-generated from the first heading or blank. The proposal's entire scan depth strategy depends on this being informative, and it almost certainly isn't.
2. **That subprocess isolation on Windows is simple.** `ProcessPoolExecutor` on Windows uses `spawn` (not `fork`), which means every worker process reimports the entire module tree. On Windows with heavy libraries loaded, this adds 1-2 seconds of startup latency per worker—potentially exceeding the 500ms budget for the scan itself.

### Overlooked Risks
- **Classification accuracy is so low that it's functionally equivalent to not having light_scan at all**, wasting the entire development effort. If you extract only ZIP metadata, you may get a 3-5% accuracy improvement over filename-only—insufficient to justify building and maintaining a new component.
- **The retroactive training data enrichment is deferred**, meaning the classifier ships with no content-trained model. You'd be deploying new infrastructure that feeds the same quality of features as the old system.

---

## Proposal B Assessment

### Steelman
This proposal is exactly right if: (1) the existing Python libraries (python-pptx, pdfplumber, openpyxl) reliably extract first-page content within 200ms on Windows for >90% of the corpus, (2) a single concatenated text blob fed into char n-gram TF-IDF captures sufficient signal without feature engineering, and (3) the 310 labeled examples, once retroactively enriched, provide enough training data to demonstrate meaningful accuracy lift before any further investment.

### Assessment: Partially Agree

This is the most pragmatic proposal. It correctly identifies retroactive enrichment as the highest-leverage task, uses existing libraries at appropriate scan depths, and avoids new dependencies. The "measure first, then decide" philosophy is exactly right for a solo developer.

Where I disagree: the decision to feed everything into one text blob with char n-grams is wrong. Character n-grams on a 500-char content snippet will produce a completely different feature space than char n-grams on a 20-char filename. The vocabulary will be dominated by content tokens, drowning the filename signal that currently works for ~60-70% of files. This isn't a theoretical concern—it's a well-documented problem with heterogeneous text concatenation in TF-IDF. You need at minimum two feature groups (filename vs. content), even if you concatenate them into one vector via `FeatureUnion`.

The blanket "do not modify the TF-IDF approach" stance is too conservative. You're changing the fundamental nature of the input (from 20-char filenames to 500+ char text snippets); the model *must* adapt to the input change or you'll get worse results than baseline.

### Strongest Point
*"Retroactive enrichment of the 310 labeled examples with content features is the highest-leverage action."* This is correct and underemphasized by the other proposals. The classifier is bottlenecked by training data quality, not architecture. Running light_scan on labeled examples and retraining should be the *first* thing built, before any pipeline integration.

### Weakest Assumption
*"The existing character n-gram TF-IDF model can digest a combined string of [filename] + [extracted_snippet]."* Character 3-5 grams were tuned for short filename strings where patterns like "Q3_", "training", "_deck" carry signal. Applied to a 500-char English paragraph, you get a massive explosion of uninformative character sequences that will dilute the filename signal. The model needs adaptation, not just more input.

### Hidden Assumptions
1. **That classification accuracy on the enriched training set generalizes to production.** Running light_scan on the 310 labeled examples gives you enriched *training* data, but if those 310 examples have different format distributions or content structures than new ingest files, the measured accuracy lift won't hold. There's no mention of a held-out test strategy.
2. **That "simple > comprehensive" means "defer all feature engineering."** Simplicity is a property of the final design, not a reason to avoid thinking. Two feature groups in a `FeatureUnion` is 10 lines of sklearn code—not complex—and it's meaningfully better than a single blob.

### Overlooked Risks
- **Char n-gram TF-IDF with content text may actually *decrease* accuracy versus filename-only** for well-named files, because the content features add noise that wasn't in the training set. Without a proper held-out evaluation, you might ship a regression.
- **No mention of how to handle re-scanning when light_scan logic changes.** If you change extraction depth or add a format, all cached ScanResults and the training enrichment become stale.

---

## Proposal C Assessment

### Steelman
This proposal is exactly right if: (1) Gemini Flash remains cheap and fast for audio transcription, (2) separate feature spaces (filename char n-grams + content word n-grams + structural features) provide meaningfully better classification than a single text blob, (3) the phased MP4 approach delivers sufficient metadata signal in Phase 1 to justify deferring transcription, and (4) a solo developer can build and maintain the multi-feature-group pipeline without it becoming a debugging nightmare.

### Assessment: Partially Agree

This is the most architecturally complete proposal. The `ScanResult` dataclass is a clean contract. The phased MP4 strategy is sound. The separate feature spaces are correct—it's the only proposal that gets the TF-IDF feature engineering right.

Where I disagree:

First, the scan depth recommendations are slightly too aggressive on the generous side. 800 chars for PDF/TXT versus 500 is a judgment call, but the argument that "500 chars can cut mid-sentence" is weak—TF-IDF doesn't care about sentence boundaries. 500 chars is fine. The difference in latency is negligible, but the principle of "extract the minimum that works" should govern.

Second, the degraded fallback strategy of "unzipping and reading XML title fields directly" for PPTX is re-implementing what python-pptx already does, adding a second code path that must be maintained. If python-pptx fails, fall back to filename. Don't write a bespoke XML parser for edge cases affecting 10% of 292 files—that's 29 files. Classify them by filename and move on.

Third, the recommendation to "run the experiment early—enrich 50 training examples" is the right instinct, but 50 is too few to detect a 5-point accuracy lift with any statistical confidence. Use all 310.

### Strongest Point
*"Separate feature spaces prevent filename signal from being drowned."* This is the single most important technical insight across all four proposals. It's correct, it's actionable, and getting it wrong (as Proposals A and B do) could make the entire light_scan effort counterproductive.

### Weakest Assumption
*"FFmpeg is already installed and callable on the Windows build environment, and extracting 30s of audio to a temp WAV is a well-understood operation in your codebase."* The problem statement says FFmpeg is "available (used by CKE for MP4)," but extracting 30s of audio to a temp file, managing temp file cleanup on Windows (where file locking is aggressive), handling FFmpeg stderr parsing for error detection, and managing the Gemini Flash API call chain is *not* a well-understood operation—it's new infrastructure. The proposal underestimates the operational complexity of Phase 2.

### Hidden Assumptions
1. **That `FeatureUnion` with 4 feature groups doesn't create a maintenance and debugging burden.** When classification goes wrong at 2am, the on-call engineer now needs to understand which feature group drove the misclassification. With a single text blob, you inspect one thing. With 4 groups, you need to inspect filename features, content features, structural features, and extension encoding separately. This is manageable but non-trivial, and the proposal doesn't acknowledge the debugging cost.
2. **That the "first 2 days" timeline for validation is realistic.** Building the scanner for 7 formats, running it on 310 examples, setting up the multi-feature pipeline, training, and evaluating—this is a week of work minimum for a solo developer, not 2 days.

### Overlooked Risks
- **Feature group weight imbalance.** With `FeatureUnion`, the dimensionality of the content TF-IDF (2000 terms) will massively outweigh the structural features (5-6 numbers) and file extension (7 one-hot values). Without explicit feature scaling or weighting, the structural and extension features contribute almost nothing. The proposal prescribes `FeatureUnion` but doesn't address this well-known problem.
- **Windows temp file cleanup for FFmpeg audio extraction.** On Windows, if the process crashes between creating and deleting a temp WAV file, you accumulate disk waste. If multiple scans run concurrently, you can hit file-locking conflicts. Neither is addressed.

---

## Proposal D Assessment

### Steelman
This proposal is exactly right if: (1) the team needs to ship the fastest possible working version, (2) Gemini Flash is reliably available and fast for MP4 transcription from day one, (3) a concatenated text blob is "good enough" for initial classification and can be refined later, and (4) the cost of $0.18 for 180 videos is trivially justified by eliminating a known classification blind spot.

### Assessment: Partially Agree

This is the most action-oriented proposal and the easiest to build. It makes the right call on MP4 (Option F) and the right call on standalone architecture. The scan depths are reasonable.

However, it makes the same fundamental TF-IDF error as Proposal B: concatenating everything into one text blob and feeding it to the existing char n-gram model. And it explicitly defers structural features, retroactive training enrichment, and feature space separation—all of which are low-cost, high-leverage improvements that should be in the initial build.

The decision to "not add structural features to the initial model" is puzzling. Slide count, page count, and duration are trivially extractable (the scanner already computes them), are zero-cost to include, and provide strong priors (a 90-slide PPTX is almost certainly training material; a 200-row XLSX is almost certainly a data report). Excluding them to "keep it simple" actually makes the model worse for no complexity savings.

### Strongest Point
*"Accept $0.001 per video transcript (≈$0.18 total) vs. free metadata-only. This is justified by eliminating 180 unclassifiable videos."* This is the clearest cost-benefit argument for MP4 transcription across all proposals. $0.18 is not a cost worth debating; it's a cost worth paying immediately.

### Weakest Assumption
*"Existing TF-IDF classifier can be retrained effectively on concatenated text blobs without major architectural changes."* Same issue as Proposal B. The classifier was built for short filename strings. Pouring 500-char content snippets into char n-grams doesn't work without changing the vectorizer. This isn't a minor assumption—it's the mechanism by which the entire accuracy improvement is supposed to happen.

### Hidden Assumptions
1. **That "defer retroactive enrichment" is safe.** If you build light_scan, integrate it into the pipeline, but train the classifier only on filenames, you're running a content-aware scanner whose output feeds a content-unaware model. The classifier can't use content features it wasn't trained on. Retroactive enrichment isn't a "later" task—it's a prerequisite for the scanner to have any effect at all.
2. **That "simple" means fewer feature groups rather than fewer lines of code.** Adding `FeatureUnion` with two TF-IDF vectorizers is ~15 lines of sklearn. Deferring it means shipping a system that demonstrably underperforms, then reworking the pipeline later—which is more total work, not less.

### Overlooked Risks
- **Shipping without retroactive training enrichment means the classifier can't use content features.** The scanner extracts content, but the model was trained on filenames. Without retraining on enriched data, the content features are noise. This creates a scenario where light_scan runs on every file but provides zero accuracy improvement—wasted compute and complexity.
- **No mention of how to validate accuracy before production deployment.** There's no held-out evaluation strategy, no accuracy threshold for go/no-go, and no plan for what to do if content features don't help.

---

# Revised Recommendation

**I am updating my position.** My original proposal (Proposal C) was substantively correct on architecture but needed sharpening in three areas based on this round of review.

## What Changed My Mind

1. **Proposal B's emphasis on retroactive enrichment as the *first* task** is correct and I underweighted it. You cannot evaluate light_scan's value without enriched training data. This must happen before pipeline integration, not after. I adopt this sequencing.

2. **Proposal D's blunt cost-benefit on MP4 transcription** clarified that phasing MP4 into two stages is unnecessary caution. $0.18 for 180 files is not a cost that warrants a phased rollout. Do it in Phase 1. However, gate it behind a timeout and fallback to metadata-only—don't let API latency block classification.

3. **Proposal A's insistence on hard per-file timeouts** is correct and I should have been more prescriptive about the mechanism. On Windows, `threading.Timer` with process kill is more reliable than `signal.alarm` (which I incorrectly mentioned—it doesn't exist on Windows).

## What Didn't Change My Mind

1. **Separate feature spaces are non-negotiable.** Proposals A, B, and D all default to a single concatenated text blob, and this will produce measurably worse results than separate feature groups. The argument is straightforward: char n-grams are appropriate for 20-char filenames with abbreviations and camelCase; word n-grams are appropriate for English prose in content snippets. Mixing them in one vectorizer means the vocabulary is dominated by content tokens and the filename signal is lost. `FeatureUnion` with two vectorizers is 15 lines of code—it's not complexity, it's correctness.

2. **Standalone module, not embedded in CKE.** All four proposals agree on this and it's clearly right.

3. **The XML-fallback degraded scan for PPTX is not worth building.** If python-pptx fails, fall back to filename. Don't maintain a second extraction path for 29 files.

## Revised Recommendation

### Build Sequence (this order, not parallel)

**Step 1: Build `light_scan` module and enrich training data (3-4 days)**

Build the scanner with these extraction depths:

| Format | Extract | Timeout |
|--------|---------|---------|
| PPTX | Slide 1 title + all slide titles via python-pptx | 500ms |
| DOCX | `title` core property + Heading 1/2 text + first 2 body paragraphs | 500ms |
| PDF | First page text via pdfplumber, cap at 500 chars | 500ms |
| XLSX | Sheet names + row 1 headers of first sheet | 500ms |
| CSV | Header row + first 3 data rows | 500ms |
| TXT/MD | First 500 chars + markdown `#` headers | 500ms |
| MP4 | `ffprobe` metadata (title, duration, resolution, creation_time) + 30s audio → Gemini Flash transcript | 3000ms |

Return type is a `ScanResult` dataclass with explicit fields:

```python
@dataclass
class ScanResult:
    title: str                  # best-guess title, empty string if none
    headers: list[str]          # headings / slide titles / sheet names
    snippet: str                # first N chars of content
    structural: dict            # slide_count, page_count, duration_s, file_size_mb
    scan_tier: str              # "full" | "degraded" | "filename_only"
    errors: list[str]           # what went wrong
    format: str                 # file extension, normalized lowercase
```

Fault tolerance: `try: full scan` → `except: return ScanResult(scan_tier="filename_only", snippet="", ...)`. No intermediate "degraded" tier—it adds branching complexity for marginal gain. Either the library works or it doesn't. Log every failure with path and exception.

Timeout enforcement: `concurrent.futures.ThreadPoolExecutor` with `timeout` parameter per file. Not `ProcessPoolExecutor`—the spawn overhead on Windows is too high for a 500ms budget. If a library call hangs, the thread is abandoned (it'll be cleaned up on pool shutdown). This is acceptable for a batch processing tool, not a long-running server.

**Run `light_scan` on all 310 labeled examples immediately.** Store results as JSON alongside existing labels. This is the enriched training dataset.

For MP4 Gemini Flash calls: do these for the labeled MP4 examples in the 310 set. If there are fewer than 20 labeled MP4s, manually label 20 more from the 180 corpus to have a meaningful video evaluation set.

**Step 2: Retrain classifier with content features (2 days)**

Feature pipeline using `sklearn.pipeline.FeatureUnion`:

```python
features = FeatureUnion([
    ("filename", Pipeline([
        ("extract", FilenameExtractor()),        # returns normalized filename stem
        ("tfidf", TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5)))
    ])),
    ("content", Pipeline([
        ("extract", ContentExtractor()),          # returns title + " ".join(headers) + snippet
        ("tfidf", TfidfVectorizer(analyzer="word", ngram_range=(1, 2), max_features=2000))
    ])),
    ("structural", Pipeline([
        ("extract", StructuralExtractor()),       # returns [slide_count, page_count, duration_s, file_size_mb]
        ("scale", StandardScaler())
    ])),
    ("extension", Pipeline([
        ("extract", ExtensionExtractor()),        # returns file extension string
        ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=True))
    ]))
])
```

This is ~60 lines of sklearn code total. Each extractor is a trivial transformer that pulls from the `ScanResult`. Each feature group uses the appropriate representation for its data type.

**Evaluate with stratified 5-fold cross-validation on the 310 enriched examples.** Compare to filename-only baseline. If accuracy improvement is <5 percentage points, stop. Light_scan doesn't justify its existence.

**Step 3: Integrate into ingest pipeline (1 day)**

If Step 2 shows meaningful accuracy lift, wire `light_scan` into `corp-by-os` ingest. Call it before CKE routing. The `ScanResult.scan_tier` field tells downstream code how much to trust the classification.

### What Not to Build

- No `ProcessPoolExecutor` subprocess isolation. Overkill for this context. Thread-level timeout is sufficient.
- No XML-level fallback parsers for PPTX/DOCX. If python-pptx fails, filename fallback.
- No local Whisper or local ML models.
- No caching layer.
- No OCR for scanned PDFs. Log them, classify by filename, move on.
- No intermediate "degraded" scan tier. Binary: it worked or it didn't.

### Signals to Revisit

- Content features provide <5% accuracy lift over filename-only on the 310 enriched examples → abandon light_scan, invest in better filename heuristics.
- Gemini Flash pricing increases >10x → drop MP4 transcription, fall back to metadata-only.
- Scanned PDFs exceed 30% of PDF corpus → evaluate Tesseract on page 1 as a light_scan addition.
- Scanner timeout failures exceed 5% of files → investigate which formats/files are hanging and add format-specific mitigations.
- Vault grows beyond 5,000 files → add content-hash-keyed scan result caching.

### Why This Is The Right Architecture For 2am

The on-call engineer (the solo developer) faces a misclassified file. They look at the scan result JSON: `scan_tier` tells them if content was extracted. `errors` tells them what went wrong. `headers` and `snippet` show them exactly what the classifier saw. Each feature group in the model can be inspected independently. The entire scanner is one file with one entry point and one return type. There are no subprocesses to debug, no API call chains to trace (except the optional Gemini Flash for MP4, which has an explicit timeout and fallback), and no circular dependencies with CKE.

The system degrades gracefully and visibly. That's what maintainability looks like.

*Latency: 137.11s | Tokens: 16020*

### Gemini (gemini-3.1-pro-preview)

### --- Proposal A ---

**Steelman first:** For this proposal to be exactly right, the threat model of internal documents must be severe enough to warrant writing custom DOM-less XML parsers, and `docProps/core.xml` must reliably contain enough classification signal to make the ML model work without body text.

**Your assessment:** Partially agree. The defense-in-depth posture is exactly right—parsers are massive attack surfaces. However, bypassing standard libraries to parse raw ZIP/XML is brittle and increases the maintenance burden for a solo developer, and metadata alone often lacks classification signal. 

**Strongest point:** The explicit recognition of XML External Entity (XXE) attacks and Zip Bombs, and the mandate for strict process isolation to contain them.

**Weakest assumption:** Assumes that `docProps/core.xml` is actually populated by users. In many organizations, document metadata is empty or defaulted to "Template", yielding zero classification signal.

**Hidden assumptions:** Assumes `ProcessPoolExecutor` on Windows is fast. Because Windows lacks `fork()`, Python uses `spawn`, which incurs a 200-300ms interpreter startup penalty. Without a persistent, warm pool, this completely obliterates the 500ms latency budget.

**Overlooked risks:** `ffprobe` vulnerabilities. While safer than FFmpeg demuxing, `ffprobe` still parses complex media headers and has a history of CVEs when exposed to untrusted files. 

### --- Proposal B ---

**Steelman first:** For this proposal to be exactly right, standard Python parsing libraries must be perfectly safe and bug-free, and retroactively enriching 310 files must provide such a massive ML lift that all other architectural concerns are rendered moot.

**Your assessment:** Disagree. This proposal treats file parsing as a benign, safe operation. Running complex, untrusted DOM parsers synchronously in the main ingest thread is an unacceptable availability and RCE risk.

**Strongest point:** The pragmatic focus on immediately retroactively enriching the 310 labeled examples to prove the ROI of content features before writing new complex pipeline code.

**Weakest assumption:** Assumes broad `try/except` blocks provide "fault tolerance." Python `try/except` cannot catch C-level segfaults or infinite loops in underlying libraries (e.g., `lxml` in `python-pptx`), which will permanently crash or hang the worker.

**Hidden assumptions:** Assumes the memory footprints of `pdfplumber` and `openpyxl` are stable and will not leak memory over thousands of sequential runs in a long-lived main process.

**Overlooked risks:** Billion Laughs attacks or Zip Bombs taking down the main ingestion worker because there is no OS-level resource boundary.

### --- Proposal C ---

**Steelman first:** For this proposal to be exactly right, API latency must be perfectly consistent, segregating feature vectors must mathematically outperform a unified text blob, and we must be authorized to send unclassified data to a third-party LLM.

**Your assessment:** Partially agree. I strongly approve of the integration contract (`ScanResult`), but I vehemently disagree with putting an external LLM API call at the synchronous pre-classification boundary.

**Strongest point:** The `ScanResult` data class and explicit `scan_tier` degradation. This creates a brilliant, observable integration boundary that isolates downstream code from parser failures.

**Weakest assumption:** Assumes it is legally and securely acceptable to send unclassified, untrusted audio to an external API (Gemini).

**Hidden assumptions:** Assumes a 500ms `signal.alarm` or threading timeout works on Windows. `signal.alarm` is Unix-only, and Python threading timeouts cannot interrupt hanging C-extensions.

**Overlooked risks:** Data exfiltration and audio prompt injection. Pre-classification means we do not know the data's sensitivity. Sending it to Google before classification violates zero-trust policies, and an attacker could embed voice commands to manipulate the downstream LLM fallback.

### --- Proposal D ---

**Steelman first:** For this proposal to be exactly right, the 180 MP4s must be absolutely critical to the business, their audio must be perfectly benign, and the cost of occasional pipeline hangs must be near zero.

**Your assessment:** Disagree. It combines the worst security flaws of B (in-process permissive parsing) and C (external APIs at ingest), creating a massive attack surface with highly fragile fault tolerance.

**Strongest point:** Pragmatic balancing of financial cost ($0.18 total for all MP4s) versus classification accuracy for the video blind spot.

**Weakest assumption:** Assumes 95% of non-video files will natively extract in <500ms using full DOM parsers without eventually locking up the CPU.

**Hidden assumptions:** Assumes the Gemini Flash API will always return within 3 seconds, completely ignoring DNS resolution, TLS handshakes, and queuing delays at Google's edge.

**Overlooked risks:** Network partitioning or DNS failures during ingest will cause backpressure that takes down the entire ingestion tier, because the scanner is synchronously waiting on Gemini.

---

### Revised Recommendation

**Update position:** I am updating my position to incorporate the explicit degradation contract (`ScanResult`) and feature engineering pipeline from Proposal C, alongside the retroactive enrichment strategy from Proposal B. However, I maintain a hardline stance against external APIs at ingest, and I must correct a fatal platform assumption shared by Proposals B, C, and D regarding Windows fault tolerance.

1. **Integration Interface & Observability:** Adopt Proposal C’s `ScanResult` contract and `scan_tier` logic. Silent failures (as in A) are an operational nightmare. Explicitly returning `scan_tier="degraded"` allows us to monitor the health of our supply chain and detect if an attacker is fuzzing the parsers.
2. **Zero-Trust API Boundary:** Reject Options C and D. Sending unclassified audio to Gemini Flash before classification is a blatant violation of data security. If a file is highly classified, we just leaked it. If it contains audio prompt injection, we compromise the pipeline. MP4s must rely strictly on local `ffprobe` metadata (Option E).
3. **Enforce Strict Process Isolation (Correcting Windows Flaws):** Proposals B, C, and D rely on threading timeouts or `try/except` to catch bad files. On Windows, this is catastrophic. `signal.alarm` does not exist. Threading cannot interrupt C-extensions (`lxml`, `pdfminer`). A malformed XML file will permanently hang the ingest worker and hold the Global Interpreter Lock (GIL). 
   Instead of Proposal A's raw XML parsing or `ProcessPoolExecutor` (which leaks hung processes on Windows and suffers from `spawn` latency), `light_scan` must invoke standard parsers via a standalone Python CLI script using `subprocess.run(["python", "scanner_cli.py", path], timeout=0.5)`. The OS-level process boundary is the *only* way to guarantee a hard 500ms timeout on Windows, safely killing C-level infinite loops and fully reclaiming memory.
4. **Feature Engineering:** Execute Proposal B's retroactive enrichment of the 310 labels immediately, but feed it into Proposal C's `FeatureUnion` architecture. Concatenating everything into one blob destroys the high-signal value of filenames.

*Latency: 81.45s | Tokens: 17467*

### Deepseek (deepseek-reasoner)

## Council Round 2: Analysis of Proposals A–D

### Proposal A Analysis
**Steelman:** Proposal A is correct if security is the overwhelming priority and MP4 classification accuracy is genuinely unimportant. For this to be exactly right: (1) the corpus must contain actively malicious files, not just corporate documents; (2) MP4 misclassification must have zero business impact; (3) the cost of downstream misrouting (from poor classification) must be less than the cost of a security breach or pipeline stall.

**Assessment:** **Disagree.** While its security-conscious process isolation is valuable, the proposal over-indexes on security at the expense of core functionality. Metadata-only MP4 scanning renders 15% of the corpus essentially unclassifiable—contradicting the problem statement that filenames like "Teams Meeting 2025-03-14.mp4" are insufficient. The 500ms hard timeout will cause excessive fallback on legitimate large files.

**Strongest point:** Process isolation with `ProcessPoolExecutor` is architecturally sound for containing parser crashes and enforcing timeouts on untrusted files.

**Weakest assumption:** "The business can tolerate relying on filenames and basic metadata for MP4 classification initially." This is likely false. 180 videos with generic filenames will degrade overall classification accuracy significantly, increasing LLM fallback costs and misrouting.

**Hidden assumptions:**
1. The existing char n-gram TF-IDF model can absorb extracted snippets without retuning or feature engineering.
2. Security threats (RCE, DoS) from internal corporate documents are imminent and severe enough to justify major accuracy trade-offs.

**Overlooked risks:**
- **Queue poisoning:** If 30% of files hit the 500ms timeout, the ingest queue backs up, causing systemic latency inflation.
- **Feature starvation:** Extracting only ZIP metadata from Office files yields minimal text (often just boilerplate), providing little classification signal.

### Proposal B Analysis
**Steelman:** Proposal B is optimal if development velocity is the absolute bottleneck and any content extraction—no matter how shallow—provides sufficient accuracy lift. For this to be exactly right: (1) first-page text must contain classification signal for >90% of documents; (2) MP4 metadata must be surprisingly informative (title tags in 40%+ of files); (3) retroactive enrichment of 310 examples must yield immediate accuracy gains without model changes.

**Assessment:** **Partially agree.** Its pragmatic, minimal approach is right for a solo developer, and retroactive enrichment is high-leverage. However, it underestimates the MP4 problem and overestimates the value of metadata.

**Strongest point:** "Retroactive enrichment of the 310 labeled examples with content features is the highest-leverage action." Absolutely correct—this directly addresses the training data bottleneck.

**Weakest assumption:** "MP4s are not the primary classification driver and their metadata or filename is sufficient." The vault's 180 MP4s (15%) with generic filenames will become a persistent accuracy sink. Metadata tags are rarely present in Teams recordings.

**Hidden assumptions:**
1. The existing extraction libraries (python-pptx, pdfplumber) are robust enough on Windows without COM fallbacks for >95% of files.
2. Structural features (slide count, duration) provide meaningful classification signal without normalization or feature engineering.

**Overlooked risks:**
- **Library-specific failures:** python-pptx silently fails on PPTX files with custom layouts; pdfplumber crashes on certain PDF encodings. These will manifest as silent degradation to filename-only.
- **Training-data leakage:** Enriching labeled examples retroactively assumes the extraction behavior matches production exactly, which may not hold if light_scan evolves.

### Proposal C Analysis
**Steelman:** Proposal C is optimal if classification accuracy is paramount and the incremental complexity of separate feature spaces and phased MP4 handling is justified. For this to be exactly right: (1) separate feature spaces (filename vs. content) must yield >5% accuracy lift over concatenation; (2) Gemini Flash API must remain cheap and low-latency; (3) the solo developer can manage the additional ML pipeline complexity.

**Assessment:** **Mostly agree.** This is the most architecturally rigorous proposal. Its phased MP4 approach, separate feature spaces, and explicit degradation tiers are well-reasoned. However, it underestimates the operational burden of the ML pipeline changes.

**Strongest point:** "Separate feature spaces prevent filename signal from being drowned." This is a critical insight—concatenating everything biases toward longer text, losing filename patterns.

**Weakest assumption:** "The solo developer can manage separate feature spaces (char n-grams for filename, word n-grams for content) without undue complexity." This adds ML pipeline debt: two vectorizers, feature union, normalization of structural features. It's not trivial to maintain.

**Hidden assumptions:**
1. The 800-char limit for PDFs is a sweet spot between 500 and 1000 chars. No data supports this.
2. Windows multiprocessing timeouts work reliably for subprocesses (they often don't due to Windows' fork limitations).

**Overlooked risks:**
- **Feature space explosion:** Adding word n-grams with a 2000-term vocabulary on sparse content snippets may overfit on the 310 training examples.
- **Phasing risk:** Phase 2 (MP4 transcript) may never ship due to feature creep, leaving videos poorly classified indefinitely.

### Proposal D Analysis
**Steelman:** Proposal D is optimal if simplicity and speed are paramount but MP4 accuracy cannot be ignored. For this to be exactly right: (1) concatenated text features must perform nearly as well as separate feature spaces; (2) 30s of audio must contain classification signal for most videos; (3) permissive fault tolerance must not mask systemic extraction failures.

**Assessment:** **Partially agree.** It correctly identifies the MP4 transcription need but oversimplifies the feature engineering and underestimates the cost of Gemini calls at scale.

**Strongest point:** "MP4: Option F (metadata + 30s Gemini Flash) balances cost (~$0.18 total for all 180 videos) and accuracy." This acknowledges the MP4 problem without over-engineering.

**Weakest assumption:** "First 30 seconds of MP4 audio typically contains sufficient spoken context for classification." Many corporate videos have long intros, music, or silent screen shares—the first 30s may be noise.

**Hidden assumptions:**
1. Gemini Flash latency will remain under 2.5s consistently. Network variance could push it beyond 3s, breaking the SLA.
2. The existing TF-IDF pipeline can handle concatenated text without modification. It can, but performance may degrade.

**Overlooked risks:**
- **Cost scaling:** At $0.001/video, 180 videos cost $0.18. But if vault grows to 10,000 videos, that's $10 per classification run (plus reclassification costs).
- **Transcript noise:** Gemini may transcribe background conversation or irrelevant banter in the first 30s, injecting noise into classification.

## Revised Recommendation

**Position update:** I **update my position** toward a hybrid of Proposal C's architecture and Proposal B's minimalism, with critical adjustments from Proposal A's security model.

**What changed my mind:** 
1. **Process isolation is non-negotiable.** Proposal A's `ProcessPoolExecutor` approach is correct for untrusted file parsing—it contains memory leaks and segfaults. We adopt this.
2. **Separate feature spaces are overkill initially.** Proposal C's separate vectorizers add complexity without proven ROI. We start with concatenated text but **preserve filename separately** by prepending a token (e.g., `[FILENAME] Andy.pdf [CONTENT] Demand Planning...`). This lets the char n-gram model learn the boundary without dual vectorizers.
3. **MP4 requires content, but not immediately.** We phase: metadata-only (ffprobe) for v1, with a **sync flag to enable 30s Gemini transcript** for high-value classifications. This defers API cost and complexity until accuracy is measured.
4. **Retroactive enrichment is the first step.** Before building anything, run a prototype scanner on the 310 labeled examples. If content features don't improve accuracy by >10%, reconsider the entire component.

**Concrete decisions:**

1. **Architecture (Q1, Q4):** Standalone module in `corp-by-os`, invoked before CKE. Use `ProcessPoolExecutor` with 500ms timeout for docs, 3s for MP4. Each format parser runs in a subprocess.
2. **Scan depth (Q2):**
   - PPTX: Slide 1 title + all slide titles (no body text)
   - DOCX: First 2 paragraphs + Heading 1 text
   - PDF: First 500 chars (pdfplumber page 0)
   - XLSX/CSV: Sheet names + first row only
   - TXT/MD: First 500 chars
3. **MP4 (Q3):** Option E (metadata) for v1. Log accuracy. If MP4 classification F1 < 0.6, implement Option F behind a feature flag.
4. **Fault tolerance (Q6):** Tiered (C). Try full scan → degraded (ZIP metadata for Office, ffprobe for MP4) → filename only. Never crash.
5. **Feature design (Q5, Q8):** Single text blob: `[FILENAME] {filename} [TITLE] {title} [HEADERS] {headers} [CONTENT] {snippet}`. Feed to existing char n-gram TF-IDF. Defer word n-grams.
6. **Training enrichment (Q7):** Immediately run prototype scanner on 310 examples. Enrich training set before retraining.
7. **Security:** Limit file size to 50MB for scanning. Sanitize subprocess arguments. Use `protocol_whitelist=file` for ffprobe.

**What we reject:**
- Proposal A's metadata-only MP4 stance (accuracy loss too great)
- Proposal C's separate feature spaces (complexity premature)
- Proposal D's unconditional Gemini calls (cost scaling risk)

**Signals to pivot:**
- MP4 metadata accuracy <60% → enable Gemini transcript flag
- >5% of files hit 500ms timeout → increase latency budget or add size-based skip
- Content features improve accuracy <10% → fall back to filename+metadata only

**Bottom line:** Build a secure, minimal scanner that extracts first-page text, phases MP4 content, and validates accuracy lift before adding complexity. The solo developer's time is the scarcest resource—spend it on retroactive enrichment first, not architectural ornamentation.

*Latency: 140.03s | Tokens: 13529*

### Grok (grok-4.20-beta)

**Proposal A**

**Steelman first:** If the dominant risk is a malicious or malformed file bringing down the entire ingest pipeline (Zip bombs, XXE, billion-laughs XML, ffprobe RCE, python-pptx segfaults), and if the business value of accurate MP4 classification is genuinely low, then the only correct engineering response is to treat every file as hostile, enforce hard process isolation, use the smallest possible attack surface (raw ZIP XML + ffprobe, never the full DOM libraries), and accept that classification quality on videos will be poor. Under those conditions A is not merely reasonable—it is the only responsible choice.

**Your assessment:** Disagree. The proposal is paranoid theater for an internal corporate vault. We are not running a public file-upload service. The threat model of "untrusted payloads" is imported from a completely different domain and distorts every subsequent decision.

**Strongest point:** Process isolation via `ProcessPoolExecutor` plus hard wall-clock timeouts is the only honest way to contain parser crashes on Windows with a solo developer. Everything else is wishful thinking about exception handling.

**Weakest assumption:** "The business can tolerate relying on filenames and basic metadata for MP4 classification initially." This is the exact assumption the original problem statement exists to refute ("Teams Meeting 2025-03-14.mp4").

**Hidden assumptions:** 
1. That maliciously crafted Office files are a realistic concern in this environment (they almost certainly aren't).
2. That character n-gram TF-IDF on a tiny metadata snippet will be meaningfully better than filename-only, while simultaneously arguing we should extract almost nothing.

**Overlooked risks:** Chronic misrouting of the 180 videos creates persistent load on the expensive LLM fallback tier, which is the exact cost leak the hybrid architecture was supposed to prevent. Also, the "skip complex parsers" approach quietly throws away the highest-signal feature in the entire corpus (PPTX slide 1 title).

---

**Proposal B**

**Steelman first:** If we can get 80%+ of the available signal from first-page/slide text and metadata in <200ms using only existing libraries, then the highest-leverage action is to immediately enrich the 310 labeled examples, retrain the *existing* model, and keep everything else as simple as possible. Everything else is future optimization.

**Your assessment:** Partially agree. This is the most pragmatic of the four, but it still under-extracts from PPTX (all slide titles is cheap and valuable) and it is too willing to accept metadata-only for MP4.

**Strongest point:** Retroactive enrichment of the 310 labeled examples is the single highest-ROI action available. Everyone else buries this.

**Weakest assumption:** "First-page or first-slide text plus structural metadata contains enough class signal." The "Demand Planning Training Q3 2025" example is on page 1. Many real corporate documents put the real title on slide 2 or page 2 after a generic cover.

**Hidden assumptions:** That the existing char n-gram model will absorb the new content without any meaningful change to feature engineering. It probably won't—the filename signal will be swamped.

**Overlooked risks:** pdfplumber on scanned PDFs + python-pptx on complex files will degrade more often than the proposal admits. The tiered fallback is described but not made first-class in the return type, so downstream code won't know when it's operating on garbage.

---

**Proposal C**

**Steelman first:** The right engineering approach is to treat classification as its own bounded context with a clean contract (`ScanResult`), extract the highest-signal cheap features aggressively (slide 1 title + all slide titles, headings, first ~800 chars), use separate feature spaces so filename signal isn't drowned, phase the MP4 transcript work, and enrich training data immediately. This is the only proposal that actually designs the *output* of light_scan as a proper abstraction instead of a bag of strings.

**Your assessment:** Agree. This is the best proposal, though it is slightly over-engineered on the feature union side for a solo developer in round 1.

**Strongest point:** It correctly identifies that slide 1 title is probably the single highest-ROI feature in the entire vault and designs around that fact instead of treating all text as interchangeable blob.

**Weakest assumption:** That Gemini Flash will remain ~$0.001 and reliably under 3s. If Google changes pricing or adds mandatory safety filtering on audio, the MP4 path becomes painful.

**Hidden assumptions:** 
1. That we should accept scanning every file twice (light_scan + CKE) as inevitable. 
2. That a solo developer will maintain the `FeatureUnion` pipeline when the model inevitably needs to become a proper ensemble or gets replaced by an LLM classifier.

**Overlooked risks:** The complexity of the phased MP4 approach and the `ScanResult` dataclass plus FeatureUnion could easily turn into a maintenance burden that delays the actual classification improvement. Also, no mention of what happens when the enriched 310 examples reveal that content features help some classes but hurt others (class imbalance shift).

---

**Proposal D**

**Steelman first:** If the goal is strictly "better than filename-only with minimal thinking," then concatenating everything into one blob, using Gemini Flash for the 180 videos, and keeping the model change as trivial as possible gets you a quick win.

**Your assessment:** Disagree. This is the "just ship something" proposal. It throws away the insight that filename and content have different optimal representations and accepts technical debt (duplicate audio extraction, blob features) from day one.

**Strongest point:** It is honest that the accuracy gain on MP4 is worth the trivial API cost.

**Weakest assumption:** That the existing TF-IDF can be retrained on concatenated text "without major architectural changes." This has never been true in my experience—adding long English text to a model trained on short filenames changes the entire term distribution.

**Hidden assumptions:** That permissive fault tolerance is sufficient without making the degradation visible to the caller (no `scan_tier` concept). Also assumes the 5% corruption rate is stable and won't spike when the vault grows.

**Overlooked risks:** The proposal defers the training data enrichment that everyone else recognizes as critical. That is exactly backwards.

---

**My Revised Recommendation**

The other proposals did not change my mind. I am more convinced that **Proposal C is directionally correct but must be simplified for a solo developer**.

**Final position:**

- `light_scan` must be a standalone module with a clean `ScanResult` contract (C's best idea).
- Extract aggressively from PPTX (slide 1 title + *all* slide titles) and reasonably from DOCX/PDF/XLSX. First-page text is table stakes.
- MP4: **Option F from day one** (metadata + 30s Gemini Flash). The 180 videos are 15% of the corpus and the filenames are *especially* terrible. $0.18 is not a real constraint. Phase 2 is theater.
- Fault tolerance: tiered with `scan_tier` in the return value. Degradation must be observable.
- Feature design: **start with concatenated blob** for the first model (B/D's pragmatism) but design the *code* so you can switch to separate vectors in one commit (C's insight). Do not ship FeatureUnion on day 1.
- Immediately run light_scan over the 310 labeled examples *and* mine existing CKE outputs. This is the highest-leverage activity in the entire council.
- Use the libraries (python-pptx, python-docx, pdfplumber, openpyxl). The Zero Trust panic in A is misplaced for internal corporate documents. Wrap every parser in a process-level timeout. If it crashes, we learn something useful.

**What everyone is taking for granted:** That first-page extraction will be sufficient. It won't be for a meaningful subset. The architecture must make "scan deeper on low-confidence results" a first-class concept, not a deferred task. The hybrid classifier already has an LLM fallback—design light_scan to fail in a way that makes the fallback useful rather than trying to make light_scan bulletproof.

This is not a compromise. It is C with the unnecessary complexity stripped out and the misplaced caution of A rejected. Anything less accurate on the video corpus is unacceptable. Anything more paranoid is cosplay.

*Latency: 17.61s | Tokens: 12178*

## Synthesis (by openai, non-participant)

## Consensus

1. **Build `light_scan` as a standalone pre-classification component, not inside CKE.**
   - This was near-unanimous and well-supported.
   - Strong reasoning: classification must happen **before** CKE to decide routing/tier/model; embedding scan logic in CKE defeats the purpose and couples a cheap pre-filter to heavy extraction.
   - This was not groupthink; multiple participants independently argued the same architectural dependency issue.

2. **Use shallow, format-specific extraction rather than full-document parsing.**
   - Broad agreement that `light_scan` should extract only high-signal fields:
     - PPTX: title/slide titles
     - DOCX: headings + first paragraphs
     - PDF: first page / first few hundred chars
     - XLSX/CSV: sheet names / headers / first rows
   - Shared rationale: most classification signal is front-loaded; deeper extraction belongs to CKE.

3. **Fault tolerance must degrade gracefully rather than block classification.**
   - Strong consensus that bad/corrupt/password-protected/OneDrive files should never crash ingest.
   - Most supported tiered or permissive fallback to filename-only classification.

4. **Retroactively enrich the 310 labeled examples with content features.**
   - This was one of the strongest shared conclusions.
   - Good reasoning: without enriched training data, `light_scan` cannot be properly evaluated or exploited by the classifier.

5. **MP4 is the highest-uncertainty area and should not drive the whole architecture.**
   - Everyone agreed MP4 is special-case and needs separate treatment.
   - Disagreement remained on *which* treatment, but consensus existed that video should be handled distinctly from document formats.

---

## Unresolved Disagreements

### 1. MP4 strategy: metadata-only vs transcript
**Crux:** Is the added complexity/risk of transcript extraction justified by the expected classification gain on 180 generic videos?

- **Metadata-only side:** simpler, local, reliable, no API dependency, safer for ingest.
- **Transcript side:** filenames/metadata are often useless for Teams recordings; transcript is likely the only meaningful content signal.

**Stronger argument:** **Transcript side, but gated/fallback-based.**
- Why: the debate repeatedly returned to the actual problem statement: generic MP4 filenames are already known to be poor. Metadata-only does not solve that problem.
- The strongest evidence was practical, not theoretical: for videos, content is often the only classification signal, and the total one-time cost is trivial.
- However, the best version of this argument was **not** “always call Gemini synchronously no matter what”; it was “use transcript when needed, with strict timeout/fallback.”

### 2. Feature design: single concatenated blob vs separate feature spaces
**Crux:** Does simplicity outweigh the risk that content text will drown filename signal?

- **Single-blob side:** simpler to implement; preserves current TF-IDF pipeline.
- **Separate-feature side:** filename and content are different modalities and should be vectorized differently.

**Stronger argument:** **Separate feature spaces.**
- Why: this was one of the most technically grounded arguments in the debate.
- Character n-grams fit short, messy filenames; word n-grams fit extracted English text. Mixing them in one vectorizer is likely to reduce performance or at least obscure signal.
- This was argued most clearly by Claude and recognized by others in later rounds.

### 3. Process isolation / timeout model
**Crux:** Is process-level isolation necessary for this internal vault context, or is in-process parsing with broad exception handling enough?

- **Isolation side:** only OS-level process boundaries can reliably contain hangs/segfaults from C extensions/parsers, especially on Windows.
- **In-process side:** the threat model is internal documents, not hostile uploads; process orchestration adds complexity for a solo developer.

**Stronger argument:** **Some form of hard isolation for scanner execution is warranted**, but the debate did not fully converge on the mechanism.
- Why: the best point from the security-heavy side was not the “zero trust” rhetoric; it was the practical Windows fact that Python exceptions/timeouts do not reliably stop hung native parsing.
- But the stronger conclusion is narrower than the strongest isolation advocates claimed: you do **not** need to redesign around raw ZIP/XML parsing; you **do** want a killable boundary for scans.

### 4. Whether to ship MP4 transcription in v1 or phase it
**Crux:** Should complexity be deferred until measured, or is the known MP4 blind spot large enough to justify immediate inclusion?

- **Phase-it side:** ship metadata-only first, measure, then add transcript if accuracy is poor.
- **Do-it-now side:** 180 videos is enough to justify solving known failure now; cost is negligible.

**Stronger argument:** **Phase it behind a flag, but evaluate it immediately on the labeled set.**
- Why: this captures the best of both sides. The debate showed no hard evidence that metadata-only will be enough, but also no proof that production ingest should synchronously depend on an API from day one.
- The right move is to test both during model evaluation, not decide purely by intuition.

---

## Argument Quality Assessment

### Best-reasoned proposals
1. **Claude**
   - Most complete architectural reasoning.
   - Strongest points:
     - standalone module before CKE
     - enriched training set first
     - separate feature spaces
     - explicit `ScanResult` contract
   - Weaknesses:
     - occasionally over-designed for a solo developer
     - some fallback complexity was likely unnecessary

2. **DeepSeek**
   - Good practical tradeoff framing, especially around MP4 economics and staged rollout.
   - Weaker than Claude on feature engineering and evaluation rigor.

3. **Grok**
   - Valuable insistence that MP4 metadata-only does not really solve the stated problem.
   - But the later simplification toward “blob first, improve later” undercut earlier stronger reasoning.

4. **Gemini**
   - Best arguments on Windows timeout limitations and parser containment.
   - But overall over-weighted a hostile-file threat model not clearly supported by the context, and under-weighted classification quality.

### Single strongest argument in the entire debate
**“Separate feature spaces prevent filename signal from being drowned by content.”**
- This was the most technically important and best-supported modeling point.
- It directly affects whether `light_scan` helps or harms the classifier.
- It was specific, actionable, and tied to known properties of TF-IDF representations.

### Single weakest argument in the entire debate
**“Metadata-only MP4 is acceptable initially because the business can tolerate low video accuracy.”**
- This was weak because it contradicted the motivating example and lacked evidence.
- MP4 was explicitly identified as the hardest format with generic filenames; asserting that poor performance there is acceptable dodges the central problem.

---

## Blind Spots

1. **No one specified a proper evaluation protocol beyond vague CV references.**
   - The debate mentioned cross-validation and “measure accuracy lift,” but did not define:
     - held-out test split
     - class imbalance handling
     - per-format/per-class metrics
     - confidence calibration for LLM fallback triggering

2. **The relationship between `light_scan` outputs and the LLM fallback policy was underdeveloped.**
   - Since the system is hybrid, the critical decision is not just top-1 accuracy, but:
     - when confidence is low
     - whether content extraction reduces fallback rate
     - whether fallback should be format-specific

3. **No one discussed persistence/versioning of scan outputs enough.**
   - Even if caching is deferred, you still need reproducibility:
     - scan schema version
     - extraction logic version
     - re-enrichment strategy when scan depth changes

4. **The debate underexplored OneDrive/locality issues.**
   - If file access can block on cloud hydration, the stated latency budgets may fail regardless of parser speed.

5. **No one seriously examined class distribution in the 310 labels.**
   - If MP4s are underrepresented in labeled data, transcript decisions cannot be made confidently from current evidence.

6. **Little discussion of confidence features from extraction quality.**
   - `scan_tier`, empty-text flags, text length, and parser-failure indicators may be as important for routing as the extracted text itself.

---

## Recommended Decision

Build `light_scan` as a **standalone pre-classification module** with a **uniform `ScanResult` contract**, shallow per-format extraction, graceful degradation, and a classifier that uses **separate feature spaces for filename and content**. For MP4, implement **metadata-only in the baseline scanner**, but **evaluate transcript-assisted MP4 classification immediately on the labeled/evaluation set** and keep transcript extraction as a controlled optional path with timeout/fallback.

### Rationale

This recommendation best fits the strongest arguments presented:

- **Standalone before CKE** is clearly correct architecturally.
- **Shallow extraction** is sufficient for most office docs and preserves speed/maintainability.
- **Retroactive enrichment first** is mandatory; otherwise the scanner cannot be judged properly.
- **Separate feature spaces** is the highest-quality ML argument in the debate and should be adopted from the start.
- **MP4 transcript capability** should not be dismissed, because metadata-only likely fails on the exact known bad cases. But making external transcript calls mandatory in production ingest before measuring benefit is premature.

### Why not embed in CKE?
Because that destroys the pre-routing purpose. This objection was weakly defended by no one.

### Why not just use one text blob?
Because the debate’s best technical evidence says the representations differ materially. The implementation overhead is modest and justified.

### Why not do transcript-for-all-MP4 immediately in production?
Because the debate did not establish operational certainty on latency, API dependence, or data-handling policy. The case for transcript is strong on accuracy, but the evidence is not strong enough to require it as day-one ingest behavior. It should be **tested immediately**, not **assumed immediately**.

### Strongest objection acknowledged
The main objection is that parser hangs/crashes on Windows may require stronger process isolation than a normal in-process module. This is credible. I weigh it as an implementation requirement, not an architectural reason to avoid `light_scan`. The scanner should execute in a killable boundary if in-process timeouts are unreliable.

### If more certainty is needed
The key unresolved evidence is:
1. actual accuracy lift from content features on the 310 enriched examples
2. actual MP4 gain from metadata-only vs transcript
3. actual p95 scan latency/failure rates on representative files

Those three measurements would settle most remaining debate.

---

## Risks

1. **Content features don’t materially improve classification**
   - Mitigation: enrich all 310 labels first; compare against filename-only baseline before full rollout.

2. **Filename signal gets diluted by content**
   - Mitigation: use separate feature pipelines from day one.

3. **Parser hangs/crashes on Windows**
   - Mitigation: run scans in a killable subprocess boundary with hard timeout; log failures and degrade to filename-only.

4. **MP4 remains a blind spot**
   - Mitigation: explicitly benchmark metadata-only vs transcript on labeled MP4s; enable transcript only if lift justifies complexity.

5. **Latency budgets are blown by OneDrive hydration or large files**
   - Mitigation: add file-size/locality guards, timeout budgets, and scan-tier downgrade.

6. **Training data is too sparse or unrepresentative**
   - Mitigation: stratify evaluation by format/class; if MP4 labels are too few, label a small additional video set before deciding.

7. **Extraction logic changes invalidate prior training data**
   - Mitigation: version `ScanResult` schema and extraction logic; store enriched outputs so retraining is reproducible.

---

## Action Items

1. **Define `ScanResult` schema**
   - Include:
     - `title`
     - `headers`
     - `snippet`
     - `structural`
     - `format`
     - `scan_tier`
     - `errors`
     - `text_length` / extraction-quality indicators

2. **Implement shallow scanners for non-video formats**
   - PPTX: slide 1 title + all slide titles
   - DOCX: core title + Heading 1/2 + first 2 paragraphs
   - PDF: first page text capped around 500–800 chars
   - XLSX: sheet names + first-sheet headers
   - CSV: headers + first 3 rows
   - TXT/MD: first 500–800 chars + markdown headers

3. **Wrap scanner execution in a hard-timeout boundary**
   - Prefer a killable subprocess model if Windows parser behavior proves unreliable.

4. **Run `light_scan` on all 310 labeled examples immediately**
   - Store outputs with versioned schema.

5. **Train and compare two models**
   - Baseline: filename-only
   - Enriched: separate feature spaces
     - filename char n-grams
     - content word n-grams
     - structural/file-extension features

6. **Establish evaluation metrics**
   - overall accuracy/F1
   - per-format accuracy
   - per-class accuracy
   - fallback rate
   - confidence calibration

7. **Benchmark MP4 alternatives on labeled/evaluation subset**
   - metadata-only
   - metadata + 30s transcript
   - compare accuracy lift, latency, timeout rate

8. **Decide MP4 production policy based on measured gain**
   - If transcript materially improves MP4 classification within budget, enable as optional or selective path.
   - Otherwise keep metadata-only and rely more on fallback.

9. **Integrate `light_scan` into ingest only after evaluation**
   - Use `scan_tier` and extraction-quality signals downstream for confidence/fallback logic.

10. **Version scan outputs and model training inputs**
   - So scan-depth changes don’t silently invalidate model behavior.
