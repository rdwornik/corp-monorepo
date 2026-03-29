"""MinHash near-duplicate detection for ingest pipeline.

Computes MinHash signatures (128 permutations, word 3-grams) for file content,
stores them in ops.db, and surfaces near-duplicate pairs above a similarity
threshold for human review.

Integration point: after light_scan (content available), before CKE extraction.
If near-duplicates found → skip expensive extraction, flag for review.

NEVER auto-deletes. Report only. Human decides.

Requires: pip install datasketch
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime

import numpy as np

logger = logging.getLogger(__name__)

NUM_PERM = 128
SIMILARITY_THRESHOLD = 0.6


# ---------------------------------------------------------------------------
# Data contracts
# ---------------------------------------------------------------------------


@dataclass
class NearDupCandidate:
    """A file that is a near-duplicate of the query file."""

    file_path: str
    filename: str
    similarity: float


@dataclass
class DupPair:
    """A near-duplicate pair found in the stored signatures."""

    path_a: str
    filename_a: str
    path_b: str
    filename_b: str
    similarity: float


# ---------------------------------------------------------------------------
# Text preprocessing
# ---------------------------------------------------------------------------


def _word_3grams(text: str) -> list[str]:
    """Generate word-level 3-grams from text.

    Falls back to unigrams for short text (fewer than 3 words).
    """
    words = text.lower().split()
    if len(words) < 3:
        return words
    return [" ".join(words[i : i + 3]) for i in range(len(words) - 2)]


# ---------------------------------------------------------------------------
# MinHash computation
# ---------------------------------------------------------------------------


def compute_minhash(text: str, num_perm: int = NUM_PERM):
    """Compute MinHash signature for text using word 3-grams.

    Returns a datasketch.MinHash. For empty text returns a zero-valued MinHash
    (all shingles absent) rather than None, so callers don't need None checks.

    Raises ImportError if datasketch is not installed.
    """
    from datasketch import MinHash  # noqa: PLC0415

    m = MinHash(num_perm=num_perm)
    if not text or not text.strip():
        return m  # empty but structurally valid

    for gram in _word_3grams(text):
        m.update(gram.encode("utf-8"))
    return m


# ---------------------------------------------------------------------------
# Serialization helpers
# ---------------------------------------------------------------------------


def _serialize_hashvalues(minhash) -> bytes:
    return minhash.hashvalues.tobytes()


def _deserialize_hashvalues(blob: bytes, num_perm: int) -> np.ndarray:
    """Reconstruct numpy hashvalues array from stored bytes.

    Handles both uint64 (8 bytes/element) and uint32 (4 bytes/element).
    """
    expected_u64 = num_perm * 8
    expected_u32 = num_perm * 4
    if len(blob) == expected_u64:
        return np.frombuffer(blob, dtype=np.uint64).copy()
    if len(blob) == expected_u32:
        return np.frombuffer(blob, dtype=np.uint32).copy()
    raise ValueError(
        f"Unexpected hashvalues blob size {len(blob)} for num_perm={num_perm}"
    )


def _minhash_from_row(row: dict):
    """Reconstruct a MinHash from a content_signatures DB row."""
    from datasketch import MinHash  # noqa: PLC0415

    m = MinHash(num_perm=row["num_perm"])
    m.hashvalues = _deserialize_hashvalues(row["hashvalues"], row["num_perm"])
    return m


# ---------------------------------------------------------------------------
# DB persistence
# ---------------------------------------------------------------------------


def store_signature(db, file_path: str, filename: str, minhash) -> None:
    """Upsert a MinHash signature into the content_signatures table.

    Uses INSERT OR REPLACE so re-ingesting the same file refreshes its
    signature rather than creating a duplicate.
    """
    file_path = file_path.replace("\\", "/")
    now = datetime.now().isoformat(timespec="seconds")
    blob = _serialize_hashvalues(minhash)

    db.conn.execute(
        """INSERT OR REPLACE INTO content_signatures
           (file_path, filename, hashvalues, num_perm, computed_at)
           VALUES (?, ?, ?, ?, ?)""",
        (file_path, filename, blob, len(minhash.hashvalues), now),
    )
    db.conn.commit()


def _load_all_signatures(db) -> list[dict]:
    rows = db.conn.execute(
        "SELECT file_path, filename, hashvalues, num_perm FROM content_signatures"
    ).fetchall()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Near-duplicate query
# ---------------------------------------------------------------------------


def find_near_duplicates(
    db,
    query_minhash,
    *,
    exclude_path: str | None = None,
    threshold: float = SIMILARITY_THRESHOLD,
) -> list[NearDupCandidate]:
    """Query a fresh LSH index for files similar to query_minhash.

    Builds a MinHashLSH from all stored signatures, queries it, then computes
    exact Jaccard for each candidate.

    Args:
        db: OpsDB instance (must have content_signatures table).
        query_minhash: datasketch.MinHash to query against.
        exclude_path: Skip this path when building the index (avoids
            a file matching itself when called from check_near_duplicate).
        threshold: Minimum Jaccard similarity to report.

    Returns:
        Candidates sorted by similarity descending.
    """
    from datasketch import MinHashLSH  # noqa: PLC0415

    rows = _load_all_signatures(db)
    if not rows:
        return []

    exclude = exclude_path.replace("\\", "/") if exclude_path else None

    lsh = MinHashLSH(threshold=threshold, num_perm=NUM_PERM)
    indexed: dict[str, dict] = {}

    for row in rows:
        if row["file_path"] == exclude:
            continue
        if row["num_perm"] != NUM_PERM:
            logger.debug(
                "Skipping signature with num_perm=%d (expected %d)",
                row["num_perm"],
                NUM_PERM,
            )
            continue
        try:
            m = _minhash_from_row(row)
            lsh.insert(row["file_path"], m)
            indexed[row["file_path"]] = row
        except Exception as exc:
            logger.warning("Failed to load signature for %s: %s", row["file_path"], exc)

    if not indexed:
        return []

    try:
        result_keys = lsh.query(query_minhash)
    except Exception as exc:
        logger.warning("LSH query failed: %s", exc)
        return []

    candidates: list[NearDupCandidate] = []
    for key in result_keys:
        row = indexed.get(key)
        if row is None:
            continue
        try:
            m = _minhash_from_row(row)
            sim = query_minhash.jaccard(m)
        except Exception as exc:
            logger.warning("Jaccard computation failed for %s: %s", key, exc)
            continue

        if sim >= threshold:
            candidates.append(
                NearDupCandidate(
                    file_path=row["file_path"],
                    filename=row["filename"],
                    similarity=round(sim, 3),
                )
            )

    candidates.sort(key=lambda c: c.similarity, reverse=True)
    return candidates


# ---------------------------------------------------------------------------
# Main entry point (ingest pipeline hook)
# ---------------------------------------------------------------------------


def check_near_duplicate(
    content: str,
    file_path: str,
    filename: str,
    db,
    threshold: float = SIMILARITY_THRESHOLD,
) -> list[NearDupCandidate]:
    """Compute, store, and query near-duplicates for a file's content.

    Called after light_scan (so content is available) and before CKE
    extraction (so we can skip expensive extraction for near-dupes).

    Signature is always stored even when no duplicates are found, so future
    files can be matched against this one.

    Returns:
        Near-duplicate candidates (empty list if none or content is empty).
    """
    if not content or not content.strip():
        logger.debug("Skipping near-dup check for empty content: %s", filename)
        return []

    try:
        minhash = compute_minhash(content)
        store_signature(db, file_path, filename, minhash)
        return find_near_duplicates(
            db,
            minhash,
            exclude_path=file_path,
            threshold=threshold,
        )
    except ImportError:
        logger.debug("datasketch not installed — near-dup check skipped for %s", filename)
        return []
    except Exception as exc:
        logger.warning("Near-dup check failed for %s: %s", filename, exc)
        return []


# ---------------------------------------------------------------------------
# Report (for corp dedup-report command)
# ---------------------------------------------------------------------------


def get_dedup_report(
    db,
    threshold: float = SIMILARITY_THRESHOLD,
) -> list[DupPair]:
    """Find all near-duplicate pairs stored in ops.db.

    Builds a single LSH index from all signatures, then queries each
    signature against it. Deduplicates (A, B) vs (B, A) pairs.

    Returns:
        All pairs with similarity >= threshold, sorted descending.
    """
    from datasketch import MinHashLSH  # noqa: PLC0415

    rows = _load_all_signatures(db)
    rows = [r for r in rows if r["num_perm"] == NUM_PERM]
    if len(rows) < 2:
        return []

    lsh = MinHashLSH(threshold=threshold, num_perm=NUM_PERM)
    minhashes: dict[str, tuple] = {}  # path → (MinHash, filename)

    for row in rows:
        try:
            m = _minhash_from_row(row)
            lsh.insert(row["file_path"], m)
            minhashes[row["file_path"]] = (m, row["filename"])
        except Exception as exc:
            logger.warning("Skipping signature for %s: %s", row["file_path"], exc)

    seen: set[frozenset] = set()
    pairs: list[DupPair] = []

    for path_a, (minhash_a, filename_a) in minhashes.items():
        try:
            candidates = lsh.query(minhash_a)
        except Exception as exc:
            logger.warning("LSH query failed for %s: %s", path_a, exc)
            continue

        for path_b in candidates:
            if path_b == path_a:
                continue
            pair_key: frozenset = frozenset({path_a, path_b})
            if pair_key in seen:
                continue
            seen.add(pair_key)

            entry = minhashes.get(path_b)
            if entry is None:
                continue
            minhash_b, filename_b = entry
            sim = minhash_a.jaccard(minhash_b)

            if sim >= threshold:
                pairs.append(
                    DupPair(
                        path_a=path_a,
                        filename_a=filename_a,
                        path_b=path_b,
                        filename_b=filename_b,
                        similarity=round(sim, 3),
                    )
                )

    pairs.sort(key=lambda p: p.similarity, reverse=True)
    return pairs
