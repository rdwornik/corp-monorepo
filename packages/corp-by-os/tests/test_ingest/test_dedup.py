"""Tests for MinHash near-duplicate detection (ingest/dedup.py).

All tests are skipped automatically if datasketch is not installed.
"""

from __future__ import annotations

from pathlib import Path

import pytest

# Skip entire module if datasketch is unavailable
datasketch = pytest.importorskip("datasketch")


from corp_by_os.ingest.dedup import (  # noqa: E402
    NUM_PERM,
    DupPair,
    NearDupCandidate,
    _word_3grams,
    check_near_duplicate,
    compute_minhash,
    find_near_duplicates,
    get_dedup_report,
    store_signature,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

_LONG_TEXT = (
    "supply chain optimization warehouse management system inventory tracking "
    "demand planning logistics inbound outbound replenishment cycle count "
    "picking putaway receiving shipping dock scheduling yard management "
    "transportation execution carrier selection freight audit invoice "
    "payment visibility analytics reporting dashboard kpi scorecard "
)

_SIMILAR_TEXT = (
    "supply chain optimization warehouse management system inventory tracking "
    "demand planning logistics inbound outbound replenishment cycle count "
    "picking putaway receiving shipping dock scheduling yard management "
    "transportation execution carrier selection freight audit invoice "
    "payment visibility analytics reporting dashboard kpi scorecard "
    "version five updated with minor corrections to logistics section "
)

_DIFFERENT_TEXT = (
    "financial reporting quarterly earnings revenue analysis stakeholder "
    "presentation board meeting executive summary profit loss balance sheet "
    "cash flow statement audit compliance regulatory filing disclosure "
    "investor relations capital allocation dividend buyback guidance forecast "
)


@pytest.fixture()
def ops_db(tmp_path: Path):
    """Temporary OpsDB for testing."""
    from corp_by_os.ops.database import OpsDB

    db = OpsDB(db_path=tmp_path / "ops.db")
    yield db
    db.close()


# ---------------------------------------------------------------------------
# _word_3grams
# ---------------------------------------------------------------------------


def test_word_3grams_basic():
    result = _word_3grams("the quick brown fox jumps")
    assert "the quick brown" in result
    assert "quick brown fox" in result
    assert "brown fox jumps" in result


def test_word_3grams_exactly_three_words():
    result = _word_3grams("one two three")
    assert result == ["one two three"]


def test_word_3grams_fewer_than_three_words():
    # Falls back to unigrams
    assert _word_3grams("hello world") == ["hello", "world"]
    assert _word_3grams("only") == ["only"]


def test_word_3grams_empty():
    assert _word_3grams("") == []


# ---------------------------------------------------------------------------
# compute_minhash
# ---------------------------------------------------------------------------


def test_compute_minhash_returns_correct_type():
    m = compute_minhash("the quick brown fox")
    assert isinstance(m, datasketch.MinHash)
    assert len(m.hashvalues) == NUM_PERM


def test_compute_minhash_empty_content():
    m = compute_minhash("")
    assert m is not None
    assert len(m.hashvalues) == NUM_PERM


def test_compute_minhash_identical_content_similarity_1():
    """Identical content → Jaccard similarity == 1.0."""
    m1 = compute_minhash(_LONG_TEXT)
    m2 = compute_minhash(_LONG_TEXT)
    assert m1.jaccard(m2) == pytest.approx(1.0)


def test_compute_minhash_similar_content_above_threshold():
    """Similar content (v4 vs v5) → Jaccard > 0.6."""
    m1 = compute_minhash(_LONG_TEXT)
    m2 = compute_minhash(_SIMILAR_TEXT)
    assert m1.jaccard(m2) > 0.6


def test_compute_minhash_different_content_below_threshold():
    """Different content → Jaccard < 0.3."""
    m1 = compute_minhash(_LONG_TEXT)
    m2 = compute_minhash(_DIFFERENT_TEXT)
    assert m1.jaccard(m2) < 0.3


# ---------------------------------------------------------------------------
# store_signature / round-trip
# ---------------------------------------------------------------------------


def test_store_signature_creates_row(ops_db):
    m = compute_minhash(_LONG_TEXT)
    store_signature(ops_db, "/path/file_a.docx", "file_a.docx", m)

    rows = ops_db.conn.execute(
        "SELECT file_path, filename, num_perm FROM content_signatures"
    ).fetchall()
    assert len(rows) == 1
    assert rows[0]["file_path"] == "/path/file_a.docx"
    assert rows[0]["num_perm"] == NUM_PERM


def test_store_signature_upsert_replaces(ops_db):
    """Storing the same path twice replaces rather than duplicates."""
    m1 = compute_minhash(_LONG_TEXT)
    m2 = compute_minhash(_SIMILAR_TEXT)
    store_signature(ops_db, "/path/file_a.docx", "file_a.docx", m1)
    store_signature(ops_db, "/path/file_a.docx", "file_a.docx", m2)

    count = ops_db.conn.execute("SELECT COUNT(*) FROM content_signatures").fetchone()[0]
    assert count == 1


# ---------------------------------------------------------------------------
# check_near_duplicate
# ---------------------------------------------------------------------------


def test_check_near_duplicate_first_file_no_candidates(ops_db):
    """First file stored → no existing signatures → empty candidates."""
    candidates = check_near_duplicate(_LONG_TEXT, "/path/a.docx", "a.docx", ops_db)
    assert candidates == []


def test_check_near_duplicate_identical_content(ops_db):
    """Identical content → similarity == 1.0."""
    check_near_duplicate(_LONG_TEXT, "/path/a.docx", "a.docx", ops_db)
    candidates = check_near_duplicate(_LONG_TEXT, "/path/b.docx", "b.docx", ops_db)

    assert len(candidates) == 1
    assert candidates[0].filename == "a.docx"
    assert candidates[0].similarity == pytest.approx(1.0)


def test_check_near_duplicate_similar_content(ops_db):
    """Similar content → at least one candidate above threshold."""
    check_near_duplicate(_LONG_TEXT, "/path/v4.docx", "v4.docx", ops_db)
    candidates = check_near_duplicate(_SIMILAR_TEXT, "/path/v5.docx", "v5.docx", ops_db)

    assert len(candidates) >= 1
    assert all(c.similarity > 0.6 for c in candidates)


def test_check_near_duplicate_different_content(ops_db):
    """Different content → no candidates above default threshold."""
    check_near_duplicate(_LONG_TEXT, "/path/a.docx", "a.docx", ops_db)
    candidates = check_near_duplicate(_DIFFERENT_TEXT, "/path/b.docx", "b.docx", ops_db)

    assert all(c.similarity < 0.3 for c in candidates)


def test_check_near_duplicate_empty_content(ops_db):
    """Empty content → skipped, returns empty list, no signature stored."""
    candidates = check_near_duplicate("", "/path/a.docx", "a.docx", ops_db)
    assert candidates == []

    count = ops_db.conn.execute("SELECT COUNT(*) FROM content_signatures").fetchone()[0]
    assert count == 0


def test_check_near_duplicate_does_not_match_self(ops_db):
    """A file is never returned as a candidate for itself."""
    check_near_duplicate(_LONG_TEXT, "/path/a.docx", "a.docx", ops_db)
    candidates = check_near_duplicate(_LONG_TEXT, "/path/a.docx", "a.docx", ops_db)

    paths = [c.file_path for c in candidates]
    assert "/path/a.docx" not in paths


# ---------------------------------------------------------------------------
# get_dedup_report
# ---------------------------------------------------------------------------


def test_get_dedup_report_finds_identical_pair(ops_db):
    """Identical files → reported as a pair with similarity 1.0."""
    check_near_duplicate(_LONG_TEXT, "/path/a.docx", "a.docx", ops_db)
    check_near_duplicate(_LONG_TEXT, "/path/b.docx", "b.docx", ops_db)

    pairs = get_dedup_report(ops_db)
    assert len(pairs) >= 1
    assert pairs[0].similarity == pytest.approx(1.0)


def test_get_dedup_report_no_duplicates(ops_db):
    """Distinct files → no pairs reported."""
    check_near_duplicate(_LONG_TEXT, "/path/a.docx", "a.docx", ops_db)
    check_near_duplicate(_DIFFERENT_TEXT, "/path/b.docx", "b.docx", ops_db)

    pairs = get_dedup_report(ops_db)
    assert pairs == []


def test_get_dedup_report_empty_db(ops_db):
    pairs = get_dedup_report(ops_db)
    assert pairs == []


def test_get_dedup_report_no_symmetric_duplicates(ops_db):
    """(A, B) appears once, not twice as (A, B) and (B, A)."""
    check_near_duplicate(_LONG_TEXT, "/path/a.docx", "a.docx", ops_db)
    check_near_duplicate(_LONG_TEXT, "/path/b.docx", "b.docx", ops_db)

    pairs = get_dedup_report(ops_db)
    seen = set()
    for p in pairs:
        key = frozenset({p.path_a, p.path_b})
        assert key not in seen, f"Symmetric duplicate found: {p.path_a} / {p.path_b}"
        seen.add(key)


def test_get_dedup_report_sorted_descending(ops_db):
    """Pairs are sorted by similarity descending."""
    check_near_duplicate(_LONG_TEXT, "/path/a.docx", "a.docx", ops_db)
    check_near_duplicate(_LONG_TEXT, "/path/b.docx", "b.docx", ops_db)  # sim=1.0
    check_near_duplicate(_SIMILAR_TEXT, "/path/c.docx", "c.docx", ops_db)  # sim<1.0 vs a/b

    pairs = get_dedup_report(ops_db)
    sims = [p.similarity for p in pairs]
    assert sims == sorted(sims, reverse=True)


def test_get_dedup_report_returns_dup_pair_instances(ops_db):
    check_near_duplicate(_LONG_TEXT, "/path/a.docx", "a.docx", ops_db)
    check_near_duplicate(_LONG_TEXT, "/path/b.docx", "b.docx", ops_db)

    pairs = get_dedup_report(ops_db)
    for pair in pairs:
        assert isinstance(pair, DupPair)
        assert pair.filename_a
        assert pair.filename_b
        assert 0.0 <= pair.similarity <= 1.0


# ---------------------------------------------------------------------------
# NearDupCandidate type
# ---------------------------------------------------------------------------


def test_near_dup_candidate_is_dataclass():
    c = NearDupCandidate(file_path="/x.docx", filename="x.docx", similarity=0.85)
    assert c.similarity == 0.85
