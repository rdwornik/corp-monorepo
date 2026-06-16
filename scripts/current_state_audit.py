#!/usr/bin/env python3
"""Read-only current-state architecture audit of the Corporate-OS ecosystem.

Measures the real folder/knowledge/automation architecture across local roots
(and, opt-in, the OneDrive mirror) and emits a deterministic inventory JSON. The
L0-L5 gap report (judgment) is authored separately from that JSON.

STRICTLY READ-ONLY: the only file this tool writes is the inventory JSON, via the
single guarded sink ``_audit_core.write_inventory``. Enforced in code by
``tests/safety/test_audit_readonly_invariant.py`` (AST proof) and at runtime by a
``WriteLedger`` assertion. OneDrive is scanned only under ``--include-onedrive``,
read-only and placeholder-safe (cloud-only files are never hashed/hydrated); writes
or deletes under a ``OneDrive - Blue Yonder`` path are always refused.

Usage:
  python scripts/current_state_audit.py --dry-run
  python scripts/current_state_audit.py --include-onedrive
  python scripts/current_state_audit.py --include-onedrive --force --output docs/audits/x.json
"""

from __future__ import annotations

import logging
import sys
from datetime import datetime
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SRC = _REPO_ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

console = Console()
log = logging.getLogger("current_state_audit")


def _human(num_bytes: int) -> str:
    value = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if value < 1024.0 or unit == "TB":
            return f"{num_bytes} B" if unit == "B" else f"{value:.1f} {unit}"
        value /= 1024.0
    return f"{num_bytes} B"


def _summary_table(inventory) -> Table:
    table = Table(title="Filesystem inventory (read-only)", show_lines=False)
    table.add_column("Root", style="cyan", overflow="fold")
    table.add_column("Exists", justify="center")
    table.add_column("Files", justify="right")
    table.add_column("Size", justify="right")
    table.add_column("Cloud-only", justify="right", style="yellow")
    table.add_column("Errors", justify="right", style="red")
    for inv in inventory.inventories:
        table.add_row(
            inv.scan_path,
            "Y" if inv.exists else "-",
            str(inv.file_count),
            _human(inv.total_bytes),
            f"{inv.cloud_only_count} ({_human(inv.cloud_only_bytes)})",
            str(len(inv.errors)),
        )
    return table


@click.command()
@click.option(
    "--config",
    "config_path",
    type=click.Path(dir_okay=False, path_type=Path),
    default=None,
    help="Path to audit.yaml (default: config/audit.yaml under the repo).",
)
@click.option(
    "--include-onedrive",
    is_flag=True,
    help="Also scan the OneDrive mirror (read-only, placeholder-safe). Default off.",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Walk metadata and report what would be scanned; write nothing.",
)
@click.option(
    "--force",
    is_flag=True,
    help="Overwrite an existing inventory JSON at the output path.",
)
@click.option(
    "--output",
    "output_path",
    type=click.Path(dir_okay=False, path_type=Path),
    default=None,
    help="Inventory JSON path (default: <output_dir>/<date>-...-inventory.json).",
)
@click.option("-v", "--verbose", is_flag=True, help="Enable debug logging.")
def main(
    config_path: Path | None,
    include_onedrive: bool,
    dry_run: bool,
    force: bool,
    output_path: Path | None,
    verbose: bool,
) -> None:
    """Run the read-only architecture audit and emit the inventory JSON."""
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )

    import _audit_core as core

    cfg_path = config_path or (_REPO_ROOT / "config" / "audit.yaml")
    config = core.load_config(cfg_path)

    if include_onedrive:
        log.warning(
            "Scanning OneDrive mirror READ-ONLY (authorized): %s "
            "(cloud-only files inventoried by metadata only; never hydrated)",
            config.onedrive_path,
        )

    date = datetime.now().strftime("%Y-%m-%d")
    inventory = core.build_inventory(
        config, generated_at=date, include_onedrive=include_onedrive
    )

    console.print(_summary_table(inventory))

    if dry_run:
        console.print("[dim][dry-run] no file written.[/dim]")
        return

    out = output_path or (
        _REPO_ROOT
        / config.output_dir
        / f"{date}-current-state-architecture-audit-inventory.json"
    )
    ledger = core.WriteLedger()
    try:
        written = core.write_inventory(inventory, out, ledger, force=force)
    except core.OneDriveSafetyError as exc:
        raise SystemExit(f"BLOCKED by OneDrive guard: {exc}") from exc

    # Runtime read-only proof: the tool wrote exactly the inventory JSON.
    assert ledger.writes == [str(written).replace("\\", "/")], (
        f"write-ledger invariant violated: {ledger.writes}"
    )
    log.info("Read-only guarantee held: tool wrote only %s", ledger.writes)
    console.print(f"[green]Inventory written:[/green] {written}")


if __name__ == "__main__":
    main()
