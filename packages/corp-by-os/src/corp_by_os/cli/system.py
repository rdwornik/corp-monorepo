"""System / doctor CLI commands."""

import subprocess

import click
from corp_by_os.cli._common import console
from corp_by_os.config import get_config
from corp_os_meta.pipeline_config import PipelineConfig
from rich.table import Table


@click.command()
def doctor() -> None:
    """Check all agent CLIs are on PATH and working."""
    cfg = get_config()

    table = Table(title="Agent Health Check", show_lines=False)
    table.add_column("Agent", style="cyan", width=28)
    table.add_column("CLI", style="white", width=20)
    table.add_column("Status", width=10)
    table.add_column("Detail", style="dim")

    for name, agent in cfg.agents.items():
        cli_cmd = agent.get("cli", "")
        status_flag = agent.get("status", "")

        if status_flag == "legacy":
            table.add_row(name, cli_cmd, "[yellow]legacy[/yellow]", "Needs rewire")
            continue

        if not cli_cmd or cli_cmd == "TBD":
            table.add_row(name, cli_cmd or "–", "[yellow]TBD[/yellow]", "CLI not configured")
            continue

        # Check if CLI is available
        # Handle compound commands like "python -m src.cli"
        check_cmd = cli_cmd.split()[0]
        try:
            result = subprocess.run(
                [check_cmd, "--help"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=10,
            )
            if result.returncode == 0:
                table.add_row(name, cli_cmd, "[green]OK[/green]", "")
            else:
                table.add_row(name, cli_cmd, "[red]FAIL[/red]", f"exit code {result.returncode}")
        except FileNotFoundError:
            table.add_row(name, cli_cmd, "[red]NOT FOUND[/red]", "Not on PATH")
        except subprocess.TimeoutExpired:
            table.add_row(name, cli_cmd, "[yellow]TIMEOUT[/yellow]", "Took >10s")
        except Exception as e:
            table.add_row(name, cli_cmd, "[red]ERROR[/red]", str(e)[:50])

    console.print(table)

    # --- System Integrity Checks ---
    from corp_by_os.doctor.integrity import check_all
    from corp_by_os.index_builder import get_index_path
    from corp_by_os.ops.database import get_ops_db_path

    console.print("\n[bold]System Integrity[/bold]")

    integrity = check_all(
        mywork_root=cfg.mywork_root,
        vault_root=cfg.vault_path,
        index_db_path=get_index_path(),
        ops_db_path=get_ops_db_path(),
        registry_path=cfg.repo_path / "config" / "content_registry.yaml",
        routing_map_path=cfg.mywork_root / "90_System" / "routing_map.yaml",
    )

    if integrity.issues:
        issue_table = Table(title="Integrity Issues")
        issue_table.add_column("Severity", width=8)
        issue_table.add_column("Category", width=10)
        issue_table.add_column("Issue", max_width=60)
        issue_table.add_column("Fix", max_width=40, style="dim")

        sev_styles = {
            "error": "red bold",
            "warning": "yellow",
            "info": "dim",
        }
        for issue in integrity.issues:
            sev_style = sev_styles.get(issue.severity, "")
            issue_table.add_row(
                f"[{sev_style}]{issue.severity}[/{sev_style}]",
                issue.category,
                issue.description,
                issue.fix_hint or "",
            )
        console.print(issue_table)

    console.print(
        f"\n  Passed: {integrity.checks_passed}  "
        f"Warnings: {integrity.checks_warned}  "
        f"Errors: {integrity.checks_failed}",
    )
    if integrity.healthy:
        console.print("[green]  System healthy.[/green]")
    else:
        console.print("[red]  Issues found -- see above.[/red]")


@click.command("trust-status")
def trust_status() -> None:
    """Show trust_level distribution across vault notes."""
    cfg = get_config()
    vault = cfg.vault_path

    if not vault.exists():
        console.print(f"[red]Vault not found: {vault}[/red]")
        return

    counts: dict[str, int] = {}
    total = 0
    conflicts = 0

    for md_file in vault.rglob("*.md"):
        if md_file.name.startswith("."):
            continue
        total += 1
        if "_conflict_" in md_file.name:
            conflicts += 1
            continue
        try:
            text = md_file.read_text(encoding="utf-8")
            if text.startswith("---"):
                end = text.find("---", 3)
                if end != -1:
                    import yaml as _yaml

                    fm = _yaml.safe_load(text[3:end])
                    level = fm.get("trust_level", "none") if isinstance(fm, dict) else "none"
                    counts[level] = counts.get(level, 0) + 1
                    continue
        except Exception:
            pass
        counts["none"] = counts.get("none", 0) + 1

    table = Table(title="Vault Trust Level Distribution")
    table.add_column("Trust Level", style="cyan", width=15)
    table.add_column("Count", justify="right", width=8)
    table.add_column("", width=20)

    level_styles = {
        "verified": "[green]protected[/green]",
        "extracted": "[yellow]overwritable[/yellow]",
        "generated": "[yellow]overwritable[/yellow]",
        "draft": "[yellow]overwritable[/yellow]",
        "none": "[dim]legacy (no field)[/dim]",
    }

    for level in ("verified", "extracted", "generated", "draft", "none"):
        if level in counts:
            table.add_row(level, str(counts[level]), level_styles.get(level, ""))

    # Any unexpected values
    for level, count in sorted(counts.items()):
        if level not in ("verified", "extracted", "generated", "draft", "none"):
            table.add_row(level, str(count), "[red]unknown[/red]")

    console.print(table)
    console.print(f"\n  Total notes: {total}")
    if conflicts:
        console.print(f"  [yellow]Pending conflicts: {conflicts}[/yellow]")


@click.command("routing-review")
@click.pass_obj
def routing_review(obj: dict) -> None:
    """Show routing override patterns for manual rule updates."""
    from corp_by_os.ops.database import OpsDB

    config = (obj or {}).get("config") or PipelineConfig.production()
    try:
        ops = OpsDB(config=config)
    except Exception as e:
        console.print(f"[red]Cannot open ops.db: {e}[/red]")
        return

    overrides = ops.get_routing_overrides()
    if overrides:
        table = Table(title="Unreviewed Routing Overrides")
        table.add_column("Destination", style="cyan")
        table.add_column("Count", justify="right")
        table.add_column("Example Files", max_width=60, style="dim")

        for row in overrides:
            examples = row.get("examples", "")
            table.add_row(
                row["final_destination"],
                str(row["cnt"]),
                (examples[:60] + "...") if len(examples) > 60 else examples,
            )
        console.print(table)
    else:
        console.print("[green]No unreviewed routing overrides.[/green]")

    stats = ops.get_routing_stats()
    console.print(
        f"\nTotal: {stats['total']} | Auto: {stats['auto']} "
        f"| Manual: {stats['manual']} | Batch: {stats['batch']}"
    )

    loose = stats["auto"] + stats["manual"]
    if loose > 0:
        override_rate = stats["manual"] / loose * 100
        console.print(f"Override rate (loose files): {override_rate:.0f}%")
        if override_rate > 40:
            console.print(
                "[yellow]Override rate >40% -- consider adding rules to "
                "content_registry.yaml[/yellow]"
            )

    ops.close()


@click.command("routing-mark-reviewed")
@click.pass_obj
def routing_mark_reviewed(obj: dict) -> None:
    """Mark all current routing feedback as reviewed."""
    from corp_by_os.ops.database import OpsDB

    config = (obj or {}).get("config") or PipelineConfig.production()
    try:
        ops = OpsDB(config=config)
    except Exception as e:
        console.print(f"[red]Cannot open ops.db: {e}[/red]")
        return

    count = ops.mark_routing_reviewed()
    console.print(f"Marked {count} entries as reviewed.")
    ops.close()
