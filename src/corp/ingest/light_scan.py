"""Lightweight content extraction for pre-classification.

Extracts title, headers, and first-page text WITHOUT full CKE extraction.
Designed for speed (<500ms per document) and fault tolerance.

Usage:
    result = light_scan(Path("report.pdf"))
    text = result.to_classification_text()  # for TF-IDF
    features = result.to_feature_dict()     # for logging
"""
import json as json_mod
import logging
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)

SCAN_TIMEOUT_MS = 500  # documents
SCAN_TIMEOUT_VIDEO_MS = 3000  # MP4


@dataclass
class ScanResult:
    """Uniform content features contract for all file types."""

    filename: str
    extension: str

    # Content features
    title: str = ""
    headers: list[str] = field(default_factory=list)
    snippet: str = ""  # first N chars of content

    # Structural features
    slide_titles: list[str] = field(default_factory=list)
    sheet_names: list[str] = field(default_factory=list)
    column_headers: list[str] = field(default_factory=list)
    page_count: int | None = None
    slide_count: int | None = None
    duration_seconds: float | None = None  # MP4
    word_count: int | None = None

    # Scan metadata
    scan_tier: str = "filename_only"  # "full" | "degraded" | "filename_only"
    errors: list[str] = field(default_factory=list)
    scan_time_ms: float = 0.0

    @property
    def filename_text(self) -> str:
        """Filename features only (for separate TF-IDF vectorizer)."""
        return self.filename

    @property
    def content_text(self) -> str:
        """Content features only (for separate TF-IDF vectorizer).

        Council decision: SEPARATE feature spaces. Filename char n-grams
        and content word n-grams must not be mixed in one vectorizer.
        """
        parts = [
            self.title,
            " ".join(self.headers[:10]),
            " ".join(self.slide_titles[:10]),
            " ".join(self.sheet_names[:5]),
            " ".join(self.column_headers[:10]),
            self.snippet[:800],
        ]
        return " ".join(p for p in parts if p).strip()

    def to_feature_dict(self) -> dict:
        """Structured features for logging and analysis."""
        return {
            "filename": self.filename,
            "extension": self.extension,
            "title": self.title,
            "header_count": len(self.headers),
            "slide_count": self.slide_count,
            "page_count": self.page_count,
            "duration_seconds": self.duration_seconds,
            "sheet_count": len(self.sheet_names) if self.sheet_names else None,
            "word_count": self.word_count,
            "content_text_length": len(self.content_text),
            "scan_tier": self.scan_tier,
            "has_title": bool(self.title),
            "has_agenda": any("agenda" in h.lower() for h in self.headers),
        }


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def light_scan(file_path: Path) -> ScanResult:
    """Extract lightweight features from any supported file type.

    MUST be fast (<500ms for docs, <3s for MP4) and fault-tolerant.
    Never crashes on bad files — degrades gracefully.
    """
    import time

    start = time.perf_counter()

    result = ScanResult(
        filename=file_path.name,
        extension=file_path.suffix.lower(),
    )

    try:
        ext = file_path.suffix.lower()
        if ext == ".pptx":
            _scan_pptx(file_path, result)
        elif ext == ".docx":
            _scan_docx(file_path, result)
        elif ext == ".pdf":
            _scan_pdf(file_path, result)
        elif ext in (".xlsx", ".xlsm"):
            _scan_xlsx(file_path, result)
        elif ext in (".csv", ".tsv"):
            _scan_csv(file_path, result)
        elif ext in (".txt", ".md"):
            _scan_text(file_path, result)
        elif ext == ".mp4":
            _scan_mp4(file_path, result)
        else:
            result.errors.append(f"Unsupported: {ext}")

        if not result.errors:
            result.scan_tier = "full"
    except Exception as e:
        logger.warning("Light scan failed for %s: %s", file_path.name, e)
        result.errors.append(str(e))
        result.scan_tier = "degraded" if result.title else "filename_only"

    result.scan_time_ms = (time.perf_counter() - start) * 1000
    return result


# ---------------------------------------------------------------------------
# Per-format scanners (private)
# ---------------------------------------------------------------------------


def _scan_pptx(path: Path, result: ScanResult) -> None:
    """Slide 1 title + all slide titles. No full body text."""
    try:
        from pptx import Presentation

        prs = Presentation(str(path))
        result.slide_count = len(prs.slides)

        for i, slide in enumerate(prs.slides):
            title_shape = slide.shapes.title
            if title_shape and title_shape.text.strip():
                result.slide_titles.append(title_shape.text.strip())

            # First slide: extract all text as snippet
            if i == 0:
                texts = []
                for shape in slide.shapes:
                    if hasattr(shape, "text") and shape.text.strip():
                        texts.append(shape.text.strip())
                result.snippet = " ".join(texts)[:800]

        if result.slide_titles:
            result.title = result.slide_titles[0]
            result.headers = result.slide_titles[1:6]
    except ImportError:
        result.errors.append("python-pptx not installed")
    except Exception as e:
        result.errors.append(f"PPTX parse: {e}")


def _scan_docx(path: Path, result: ScanResult) -> None:
    """Core title + Heading 1/2 + first 2 body paragraphs."""
    try:
        from docx import Document

        doc = Document(str(path))

        body_paras = []
        for para in doc.paragraphs[:50]:
            text = para.text.strip()
            if not text:
                continue

            style = para.style.name if para.style else ""
            if style.startswith("Heading") or style == "Title":
                result.headers.append(text)
                if not result.title and style in ("Heading 1", "Title"):
                    result.title = text
            else:
                body_paras.append(text)

        result.snippet = " ".join(body_paras[:3])[:800]
        result.word_count = sum(len(p.split()) for p in body_paras)

        if not result.title and body_paras:
            result.title = body_paras[0][:100]
    except ImportError:
        result.errors.append("python-docx not installed")
    except Exception as e:
        result.errors.append(f"DOCX parse: {e}")


def _scan_pdf(path: Path, result: ScanResult) -> None:
    """First page text, capped at 800 chars."""
    try:
        import pdfplumber

        with pdfplumber.open(str(path)) as pdf:
            result.page_count = len(pdf.pages)
            if pdf.pages:
                text = pdf.pages[0].extract_text() or ""
                result.snippet = text[:800]
                lines = [line.strip() for line in text.split("\n") if line.strip()]
                if lines:
                    result.title = lines[0][:100]
                    result.headers = lines[1:6]
    except ImportError:
        # Fallback to PyMuPDF
        try:
            import fitz  # type: ignore[import]

            doc = fitz.open(str(path))
            result.page_count = len(doc)
            if len(doc) > 0:
                text = doc[0].get_text()[:800]
                result.snippet = text
                lines = [line.strip() for line in text.split("\n") if line.strip()]
                if lines:
                    result.title = lines[0][:100]
                    result.headers = lines[1:6]
            doc.close()
        except ImportError:
            result.errors.append("No PDF library available")
    except Exception as e:
        result.errors.append(f"PDF parse: {e}")


def _scan_xlsx(path: Path, result: ScanResult) -> None:
    """Sheet names + first-sheet headers + first 3 data rows."""
    try:
        from openpyxl import load_workbook

        wb = load_workbook(str(path), read_only=True, data_only=True)
        result.sheet_names = wb.sheetnames[:10]

        ws = wb[wb.sheetnames[0]]
        rows_text = []
        for i, row in enumerate(ws.iter_rows(max_row=4, values_only=True)):
            cells = [str(c) for c in row if c is not None]
            if i == 0:
                result.column_headers = cells[:20]
            rows_text.append(" ".join(cells))

        result.snippet = " ".join(rows_text)[:800]
        result.title = result.sheet_names[0] if result.sheet_names else ""
        wb.close()
    except ImportError:
        result.errors.append("openpyxl not installed")
    except Exception as e:
        result.errors.append(f"XLSX parse: {e}")


def _scan_csv(path: Path, result: ScanResult) -> None:
    """Headers + first 3 rows."""
    import csv

    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            reader = csv.reader(f)
            headers = next(reader, [])
            result.column_headers = [h.strip() for h in headers if h.strip()][:20]

            rows = []
            for i, row in enumerate(reader):
                if i >= 3:
                    break
                rows.append(" ".join(str(c) for c in row))

            result.snippet = " ".join(rows)[:800]
            result.title = " | ".join(result.column_headers[:5])
    except Exception as e:
        result.errors.append(f"CSV parse: {e}")


def _scan_text(path: Path, result: ScanResult) -> None:
    """First 800 chars + markdown headers."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")[:800]
        result.snippet = text
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        if lines:
            result.title = lines[0].lstrip("#").strip()[:100]
            result.headers = [
                line.lstrip("#").strip() for line in lines if line.startswith("#")
            ][:10]
    except Exception as e:
        result.errors.append(f"Text read: {e}")


def _scan_mp4(path: Path, result: ScanResult) -> None:
    """FFprobe metadata only. Phase 2 adds transcript.

    Extracts: duration, title tag, comment tag, creation time.
    Duration hints: >45min likely meeting, <10min likely demo/clip.
    """
    try:
        cmd = [
            "ffprobe",
            "-v",
            "quiet",
            "-print_format",
            "json",
            "-show_format",
            str(path),
        ]
        # gotcha: use encoding="utf-8", errors="replace" for subprocess on Windows
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=3,
        )

        if proc.returncode == 0:
            data = json_mod.loads(proc.stdout)
            fmt = data.get("format", {})
            tags = fmt.get("tags", {})

            # Duration
            duration = float(fmt.get("duration", 0))
            result.duration_seconds = duration

            # Title/comment tags (Teams recordings sometimes have these)
            title = tags.get("title", "") or tags.get("comment", "")
            if title:
                result.title = title[:100]

            # Build snippet from available metadata
            parts = []
            if title:
                parts.append(title)
            if duration > 0:
                mins = int(duration / 60)
                if mins > 45:
                    parts.append("long recording likely meeting")
                elif mins > 15:
                    parts.append("medium recording")
                elif mins < 5:
                    parts.append("short clip likely demo")

            result.snippet = " ".join(parts)[:800]

            if not result.title:
                result.title = f"Video {int(duration / 60)}min"
        else:
            result.errors.append(f"ffprobe failed: {proc.stderr[:200]}")
    except FileNotFoundError:
        result.errors.append("ffprobe not found (FFmpeg not installed)")
    except subprocess.TimeoutExpired:
        result.errors.append("ffprobe timeout (>3s)")
    except Exception as e:
        result.errors.append(f"MP4 probe: {e}")
