"""Tests for scripts/validate_audit_casing.py -- corp's ADR-101 R4 casing gate (fleet ruling d1).

Firing tests, not presence. The pure `casing_violation` classifier is exercised directly
(UPPERCASE / underscore / CamelCase / .MD fail; well-formed lowercase-kebab passes; every one
of the 11 enumerated grandfathered names passes), and the prospective-only/grandfather
behavior is proven end-to-end against a REAL temp git repo (an added off-casing file BLOCKS
while a modified grandfathered one PASSES). Mirrors the hub's test_validate_hermetization.py,
scoped to the single casing branch corp carries.
"""

import importlib.util
import subprocess
import sys
from pathlib import Path

_P = Path(__file__).resolve().parents[2] / "scripts" / "validate_audit_casing.py"


def _load():
    spec = importlib.util.spec_from_file_location("validate_audit_casing", _P)
    module = importlib.util.module_from_spec(spec)
    sys.modules["validate_audit_casing"] = module
    spec.loader.exec_module(module)
    return module


vac = _load()


# --- casing_violation: the R4 casing branch ----------------------------------

def test_blocks_uppercase_underscore_corp_class():
    # The motivating fixture: corp's UPPERCASE _AUDIT_/_BRIEF_ divergence (R4).
    r = vac.casing_violation("docs/audits/2026-07-12_AUDIT_new-thing.md")
    assert r is not None and "casing" in r


def test_blocks_underscore_lowercase():
    r = vac.casing_violation("docs/audits/2026-07-12-technical_foo.md")
    assert r is not None and "casing" in r


def test_blocks_camelcase():
    r = vac.casing_violation("docs/audits/2026-07-12-technicalFoo.md")
    assert r is not None and "casing" in r


def test_blocks_uppercase_md_extension():
    # An uppercase .MD extension must NOT dodge the gate (apply is extension-case-insensitive).
    r = vac.casing_violation("docs/audits/2026-07-12-technical-good.MD")
    assert r is not None and "casing" in r


def test_allows_wellformed_lowercase_kebab():
    assert vac.casing_violation("docs/audits/2026-07-12-technical-foo.md") is None
    assert vac.casing_violation("docs/audits/2026-07-12-estate-recon.md") is None
    assert vac.casing_violation("docs/audits/2026-07-12-deep-dealloop.md") is None


def test_allows_dot_carveout_repo_version_token():
    # `.` allowed inside the slug for repo/version tokens (ADR-101 R4 carve-out).
    assert vac.casing_violation("docs/audits/2026-07-12-technical-v3.4-abort.md") is None
    assert vac.casing_violation(
        "docs/audits/2026-07-12-census-.dev-knowledge-sweep.md") is None


def test_casing_only_not_class_or_date_grammar():
    # corp carries ONLY casing: an off-enum class or an impossible date SHAPE still passes
    # as long as the name is all-lowercase-kebab (the hub's Rule B enum/date branches are
    # deliberately NOT carried here).
    assert vac.casing_violation("docs/audits/2026-07-12-bogusclass-foo.md") is None
    assert vac.casing_violation("docs/audits/not-a-date-at-all.md") is None
    assert vac.casing_violation("docs/audits/2026-13-99-technical-x.md") is None


def test_all_11_grandfathered_names_pass():
    # The enumerated skip-set: every pre-existing UPPERCASE _TYPE_ file is exempt by name.
    for fname in vac.LEGACY_GRANDFATHERED:
        assert vac.casing_violation(f"docs/audits/{fname}") is None, fname
    assert len(vac.LEGACY_GRANDFATHERED) == 11


def test_silent_on_non_audit_paths():
    assert vac.casing_violation("docs/audits/README.md") is None       # generated index
    assert vac.casing_violation("docs/audits/readme.md") is None       # lowercase variant
    assert vac.casing_violation("docs/decisions/ADR-102-X.md") is None  # different genre
    assert vac.casing_violation("scripts/BadName.py") is None           # not an audit .md
    assert vac.casing_violation("docs/audits/2026-07-12-technical-x.txt") is None  # not .md


# --- check aggregation -------------------------------------------------------

def test_check_aggregates_and_labels():
    reasons = vac.check([
        "scripts/ok.py",                                  # clean (not in scope)
        "docs/audits/2026-07-12-technical-ok.md",         # clean
        "docs/audits/2026-07-12_BAD_NAME.md",             # casing violation
    ])
    assert len(reasons) == 1
    assert reasons[0].startswith("docs/audits/2026-07-12_BAD_NAME.md:")
    assert "casing" in reasons[0]


def test_check_empty_is_clean():
    assert vac.check([]) == []
    assert vac.check(["scripts/a.py", "docs/audits/2026-07-12-technical-a.md"]) == []


# --- prospective-only / grandfather: REAL temp git repo ----------------------

def _git(repo: Path, *args: str) -> str:
    out = subprocess.run(["git", "-C", str(repo), *args],
                         capture_output=True, text=True, encoding="utf-8")
    assert out.returncode == 0, f"git {args} failed: {out.stderr}"
    return out.stdout


def _init_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "t@t")
    _git(repo, "config", "user.name", "t")
    _git(repo, "config", "commit.gpgsign", "false")
    (repo / "docs" / "audits").mkdir(parents=True)
    (repo / "seed.txt").write_text("seed\n", encoding="utf-8")
    _git(repo, "add", "seed.txt")
    _git(repo, "commit", "-q", "-m", "seed")
    return repo


def _run_hook(repo: Path) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(_P)], cwd=str(repo),
                          capture_output=True, text=True, encoding="utf-8")


def test_prospective_grandfathers_modified_existing(tmp_path):
    # A mis-named audit file that ALREADY EXISTS (committed) is grandfathered: modifying and
    # staging it is status M, not A, so the gate is silent.
    repo = _init_repo(tmp_path)
    bad = repo / "docs" / "audits" / "2026-07-08_BRIEF_metadata-charter-T1.md"
    bad.write_text("# grandfathered\n", encoding="utf-8")
    _git(repo, "add", "-f", str(bad))
    _git(repo, "commit", "-q", "-m", "grandfather the bad name")
    bad.write_text("# grandfathered, edited\n", encoding="utf-8")
    _git(repo, "add", "-f", str(bad))            # staged as MODIFIED
    res = _run_hook(repo)
    assert res.returncode == 0, res.stderr


def test_blocks_newly_added_off_casing_audit(tmp_path):
    repo = _init_repo(tmp_path)
    new = repo / "docs" / "audits" / "2026-07-12_TECHNICAL_AUDIT.md"
    new.write_text("# new bad\n", encoding="utf-8")
    _git(repo, "add", str(new))
    res = _run_hook(repo)
    assert res.returncode == 1
    assert "casing" in res.stderr


def test_allows_newly_added_conformant(tmp_path):
    repo = _init_repo(tmp_path)
    good = repo / "docs" / "audits" / "2026-07-12-technical-clean.md"
    good.write_text("# ok\n", encoding="utf-8")
    _git(repo, "add", str(good))
    res = _run_hook(repo)
    assert res.returncode == 0, res.stderr


def test_newly_added_grandfathered_name_passes(tmp_path):
    # Belt-and-suspenders: a delete+re-add of an enumerated legacy name surfaces as ADD but
    # the skip-set exempts it by name (prospective alone would not catch this case).
    repo = _init_repo(tmp_path)
    legacy = repo / "docs" / "audits" / "2026-07-07_AUDIT_demo-prep-recon.md"
    legacy.write_text("# legacy re-add\n", encoding="utf-8")
    _git(repo, "add", "-f", str(legacy))
    res = _run_hook(repo)
    assert res.returncode == 0, res.stderr


def test_rename_to_bad_audit_name_is_blocked(tmp_path):
    # A rename INTRODUCES a new pathname; --no-renames surfaces it as an ADD so the off-casing
    # destination is policed (not silently skipped as status R).
    repo = _init_repo(tmp_path)
    good = repo / "docs" / "audits" / "2026-07-12-technical-ok.md"
    good.write_text("# ok\n", encoding="utf-8")
    _git(repo, "add", str(good))
    _git(repo, "commit", "-q", "-m", "add a good audit")
    _git(repo, "mv", str(good), str(repo / "docs" / "audits" / "2026-07-12_BAD_RENAME.md"))
    res = _run_hook(repo)
    assert res.returncode == 1
    assert "casing" in res.stderr


def test_main_fail_open_on_git_error(monkeypatch, capsys):
    def _boom():
        raise RuntimeError("simulated git failure")

    monkeypatch.setattr(vac, "staged_added_paths", _boom)
    assert vac.main() == 0                          # fail OPEN
    assert "skipped" in capsys.readouterr().err     # but LOUD
