"""Extract CLI command and supported file extensions."""

import sys
from pathlib import Path

import click

from corp.cli._common import console
from corp.config import get_config

EXTRACT_EXTENSIONS = [
    ".pptx",
    ".ppt",
    ".pdf",
    ".docx",
    ".doc",
    ".xlsx",
    ".xls",
    ".xlsm",
    ".csv",
    ".txt",
    ".md",
    ".msg",
    ".eml",
    ".mp4",
    ".mkv",
    ".mp3",
    ".wav",
]


@click.command("extract")
@click.argument("folder", type=click.Path(exists=True, file_okay=False))
@click.option("--batch", is_flag=True, help="Use Gemini Batch API (50% cheaper, slower)")
@click.option("--dry-run", is_flag=True, help="Build manifest but don't extract")
@click.option("--output-dir", default=None, type=click.Path(), help="Override output directory")
def extract_command(
    folder: str,
    batch: bool,
    dry_run: bool,
    output_dir: str | None,
) -> None:
    """Extract knowledge from a MyWork folder via CKE."""
    from corp.extraction.folder_policy import load_policy
    from corp.extraction.manifest_emitter import build_manifest, write_manifest
    from corp.extraction.routing import resolve_route
    from corp.extraction.scanner import scan_folder
    from corp.overnight.cke_client import is_available

    cfg = get_config()
    folder_path = Path(folder).resolve()
    mywork_root = cfg.mywork_root

    # Load routing
    routing_map_path = mywork_root / "90_System" / "routing_map.yaml"
    if not routing_map_path.exists():
        console.print(f"[red]routing_map.yaml not found: {routing_map_path}[/red]")
        sys.exit(1)

    import yaml

    with open(routing_map_path, encoding="utf-8") as f:
        routing_map = yaml.safe_load(f)

    route = resolve_route(folder_path, routing_map, mywork_root=mywork_root)
    console.print(f"[dim]Route: {route.vault_target} (scope={route.provenance_scope})[/dim]")

    # Load policy
    policy = load_policy(folder_path)
    if not policy.enabled:
        console.print(
            "[yellow]Extraction disabled for this folder (folder_manifest.yaml).[/yellow]"
        )
        sys.exit(1)

    extensions = policy.allow_extensions or EXTRACT_EXTENSIONS
    console.print(f"[dim]Scanning {folder_path}...[/dim]")
    scan_results = scan_folder(folder_path, allow_extensions=extensions)

    if not scan_results:
        console.print("[yellow]No extractable files found.[/yellow]")
        return

    console.print(f"Found [bold]{len(scan_results)}[/bold] files")

    # Build manifest
    out_dir = Path(output_dir) if output_dir else cfg.app_data_path / "staging" / folder_path.name
    manifest = build_manifest(
        scan_results,
        route,
        policy,
        out_dir,
        project_name=folder_path.name,
        mywork_root=mywork_root,
    )

    manifest_path = out_dir / "manifest.json"
    write_manifest(manifest, manifest_path)
    console.print(f"Manifest: {manifest_path} ({len(manifest['files'])} entries)")

    if dry_run:
        console.print("[yellow]Dry run — manifest written, no extraction.[/yellow]")
        return

    # Check CKE availability
    ok, err = is_available()
    if not ok:
        console.print(f"[red]CKE not available: {err}[/red]")
        sys.exit(1)

    from corp.overnight.cke_client import extract_batch, extract_sync

    console.print(f"[bold]Starting extraction ({'batch' if batch else 'sync'})...[/bold]")
    if batch:
        result = extract_batch(manifest_path)
    else:
        result = extract_sync(manifest_path)

    done = result.get("done", 0)
    errors = result.get("error", 0)
    cost = result.get("cost", 0.0)
    console.print(
        f"[green]Done: {done}[/green], errors: {errors}, cost: ${cost:.4f}",
    )

    # Move to vault
    if done > 0:
        from corp.extraction.vault_writer import move_to_vault

        moved = move_to_vault(out_dir, cfg.vault_path, route.vault_target)
        console.print(f"[green]Moved {moved} files to vault ({route.vault_target})[/green]")
