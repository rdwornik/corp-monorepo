"""PipelineConfig — portable path bundle for the corp-by-os pipeline.

Resolution order for production(): ENV_VAR > config/paths.toml > Path.home() defaults.
For isolated testing: PipelineConfig.sandbox(tmp_root) puts everything under tmp_root.

Usage:
    cfg = PipelineConfig.production()          # real run
    cfg = PipelineConfig.sandbox(tmp_path)     # test isolation
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class PipelineConfig:
    """All filesystem paths needed by the corp-by-os pipeline.

    Frozen so callers can trust paths don't mutate. Derived paths (inbox,
    db files) are computed in __post_init__ from the six base paths.
    """

    vault_path: Path
    mywork_root: Path
    projects_root: Path
    templates_root: Path
    archive_root: Path
    app_data_path: Path
    index_extra_roots: tuple[Path, ...] = ()

    # Derived paths — set by __post_init__, not passed as constructor args
    inbox_path: Path = field(init=False)
    index_db_path: Path = field(init=False)
    ops_db_path: Path = field(init=False)
    state_db_path: Path = field(init=False)

    def __post_init__(self) -> None:
        # frozen=True requires object.__setattr__ for derived fields
        object.__setattr__(self, "inbox_path", self.mywork_root / "00_Inbox")
        object.__setattr__(self, "index_db_path", self.app_data_path / "index.db")
        object.__setattr__(self, "ops_db_path", self.app_data_path / "ops.db")
        object.__setattr__(self, "state_db_path", self.app_data_path / "overnight_state.db")

    @classmethod
    def production(cls) -> PipelineConfig:
        """Load from ENV_VAR > paths.toml > Path.home() defaults.

        Never hardcodes user-specific paths — all defaults are relative to
        Path.home() or %LOCALAPPDATA%, which resolve correctly on any machine.
        """
        from corp_os_meta.config import get_path

        # vault and mywork use get_path() (paths.toml-aware)
        vault = get_path(
            "vault",
            env_var="VAULT_PATH",
            default=str(Path.home() / "Documents" / "ObsidianVault"),
        )
        mywork = get_path(
            "mywork",
            env_var="MYWORK_ROOT",
            default=str(Path.home() / "Documents" / "MyWork"),
        )

        # remaining paths: env var > Path.home()-relative default
        def _env_or(env_var: str, default: Path) -> Path:
            raw = os.environ.get(env_var)
            return Path(os.path.expandvars(raw)) if raw else default

        local_appdata = Path(os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData" / "Local")))

        extra_roots_raw = os.environ.get("INDEX_EXTRA_ROOTS", "")
        extra_roots = tuple(
            Path(os.path.expandvars(p.strip()))
            for p in extra_roots_raw.split(";")
            if p.strip()
        )

        return cls(
            vault_path=vault,
            mywork_root=mywork,
            projects_root=_env_or("PROJECTS_ROOT", mywork / "10_Projects"),
            templates_root=_env_or("TEMPLATES_ROOT", mywork / "30_Templates"),
            archive_root=_env_or("ARCHIVE_ROOT", mywork / "80_Archive"),
            app_data_path=_env_or("APP_DATA_PATH", local_appdata / "corp-by-os"),
            index_extra_roots=extra_roots,
        )

    @classmethod
    def sandbox(cls, tmp_root: Path) -> PipelineConfig:
        """Create a fully isolated config under tmp_root for testing.

        All paths live under tmp_root — no real filesystem access needed.
        """
        mywork = tmp_root / "mywork"
        return cls(
            vault_path=tmp_root / "vault",
            mywork_root=mywork,
            projects_root=mywork / "10_Projects",
            templates_root=mywork / "30_Templates",
            archive_root=mywork / "80_Archive",
            app_data_path=tmp_root / "appdata",
        )
