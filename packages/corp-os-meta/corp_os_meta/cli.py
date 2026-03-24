"""
corp-meta CLI — validate, normalize, and report on Obsidian vault notes.

Usage:
  corp-meta validate path/to/note.md
  corp-meta validate path/to/vault/ --recursive
  corp-meta normalize path/to/note.md --in-place
  corp-meta report path/to/vault/
"""

import re
from pathlib import Path

from dotenv import load_dotenv

# Global API keys (Documents/.secrets/.env)
_global_env = Path.home() / "Documents" / ".secrets" / ".env"
if _global_env.exists():
    load_dotenv(_global_env, override=False)

# Local .env (project-specific vars only)
load_dotenv(override=False)

import click
import yaml
from rich.console import Console
from rich.table import Table

from corp_os_meta import (
    load_taxonomy,
    normalize_frontmatter,
    validate_frontmatter,
)

console = Console()


def extract_yaml_frontmatter(text: str) -> tuple[dict | None, str]:
    """Parse YAML frontmatter from markdown file."""
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
    if not match:
        return None, text
    try:
        data = yaml.safe_load(match.group(1))
        body = text[match.end() :]
        return data, body
    except yaml.YAMLError:
        return None, text


@click.group()
def main():
    """corp-meta: Metadata management for corp-by-os vault."""
    pass


@main.command()
@click.argument("path", type=click.Path(exists=True))
@click.option(
    "--recursive", "-r", is_flag=True, help="Process all .md files in directory"
)
@click.option("--strict", is_flag=True, help="Fail on any validation issue")
def validate(path: str, recursive: bool, strict: bool):
    """Validate note frontmatter against schema."""
    target = Path(path)
    files = list(target.rglob("*.md")) if target.is_dir() and recursive else [target]

    stats = {"valid": 0, "warnings": 0, "quarantine": 0, "no_frontmatter": 0}

    for f in files:
        if "_quarantine" in str(f):
            continue
        text = f.read_text(encoding="utf-8")
        data, _ = extract_yaml_frontmatter(text)
        if not data:
            stats["no_frontmatter"] += 1
            continue
        result, _, issues = validate_frontmatter(data)
        stats[result.value] += 1
        if issues:
            console.print(f"  [yellow]{f.name}[/]: {', '.join(issues)}")

    console.print(
        f"\n[bold]Results:[/] {stats['valid']} valid, {stats['warnings']} warnings, "
        f"{stats['quarantine']} quarantine, {stats['no_frontmatter']} no frontmatter"
    )

    if strict and (stats["quarantine"] > 0 or stats["warnings"] > 0):
        raise SystemExit(1)


@main.command()
@click.argument("path", type=click.Path(exists=True))
@click.option(
    "--in-place", "-i", is_flag=True, help="Overwrite file with normalized version"
)
def normalize(path: str, in_place: bool):
    """Normalize taxonomy terms in note frontmatter."""
    target = Path(path)
    text = target.read_text(encoding="utf-8")
    data, body = extract_yaml_frontmatter(text)
    if not data:
        console.print("[red]No YAML frontmatter found[/]")
        return

    taxonomy = load_taxonomy()
    normalized, changes, unknown = normalize_frontmatter(data, taxonomy)

    if changes:
        console.print(f"[green]Normalized:[/] {', '.join(changes)}")
    if unknown:
        console.print(f"[yellow]Unknown terms:[/] {', '.join(unknown)}")
    if not changes and not unknown:
        console.print("[dim]Nothing to normalize[/]")

    if in_place and changes:
        frontmatter_str = yaml.dump(
            normalized, default_flow_style=False, allow_unicode=True, sort_keys=False
        )
        output = f"---\n{frontmatter_str}---\n{body}"
        target.write_text(output, encoding="utf-8")
        console.print(f"[green]Written:[/] {target}")


@main.command()
@click.argument("vault_path", type=click.Path(exists=True))
def report(vault_path: str):
    """Report on vault health: term coverage, quarantine, unknown terms."""
    vault = Path(vault_path)
    files = list(vault.rglob("*.md"))

    quarantine_count = sum(1 for f in files if "_quarantine" in str(f))
    note_files = [f for f in files if "_quarantine" not in str(f)]

    all_topics: dict[str, int] = {}
    all_unknown: list[str] = []
    taxonomy = load_taxonomy()

    for f in note_files:
        text = f.read_text(encoding="utf-8")
        data, _ = extract_yaml_frontmatter(text)
        if not data or "topics" not in data:
            continue
        _, _, unknown = normalize_frontmatter(dict(data), taxonomy)
        all_unknown.extend(unknown)
        for topic in data.get("topics", []):
            all_topics[topic] = all_topics.get(topic, 0) + 1

    # Topic frequency table
    table = Table(title="Topic Frequency")
    table.add_column("Topic", style="cyan")
    table.add_column("Count", justify="right")
    for topic, count in sorted(all_topics.items(), key=lambda x: -x[1]):
        table.add_row(topic, str(count))
    console.print(table)

    # Domain frequency
    all_domains: dict[str, int] = {}
    stale_count = 0
    from datetime import date as date_type

    for f in note_files:
        text = f.read_text(encoding="utf-8")
        data, _ = extract_yaml_frontmatter(text)
        if not data:
            continue
        for domain in data.get("domains", []):
            all_domains[domain] = all_domains.get(domain, 0) + 1
        valid_to = data.get("valid_to")
        if valid_to:
            if isinstance(valid_to, str):
                valid_to = date_type.fromisoformat(valid_to)
            if isinstance(valid_to, date_type) and valid_to < date_type.today():
                stale_count += 1

    if all_domains:
        domain_table = Table(title="Domain Distribution")
        domain_table.add_column("Domain", style="cyan")
        domain_table.add_column("Count", justify="right")
        for domain, count in sorted(all_domains.items(), key=lambda x: -x[1]):
            domain_table.add_row(domain, str(count))
        console.print(domain_table)

    console.print("\n[bold]Vault stats:[/]")
    console.print(f"  Notes: {len(note_files)}")
    console.print(f"  Quarantined: {quarantine_count}")
    console.print(f"  Unique topics: {len(all_topics)}")
    if all_domains:
        console.print(f"  Unique domains: {len(all_domains)}")
    if stale_count:
        console.print(f"  [yellow]Stale notes (past valid_to): {stale_count}[/]")
    if all_unknown:
        console.print(f"  [yellow]Unknown terms: {', '.join(set(all_unknown))}[/]")


if __name__ == "__main__":
    main()
