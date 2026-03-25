"""Rich terminal chat loop + intent router for conversational agent."""

from __future__ import annotations

import logging
import shutil
from collections.abc import Callable
from datetime import date, datetime
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

from corp_opportunity_manager.config import AppConfig
from corp_opportunity_manager.folder_manager import create_opportunity
from corp_opportunity_manager.folder_standards import (
    check_structure,
    create_subfolder,
    list_project_files,
)
from corp_opportunity_manager.llm_client import parse_intent
from corp_opportunity_manager.models import IntentResult, OpportunityConfig
from corp_opportunity_manager.templates import deck_filename

logger = logging.getLogger(__name__)

MAX_HISTORY = 10


class ChatSession:
    """Manages a conversational session with intent routing."""

    def __init__(self, config: AppConfig, console: Console) -> None:
        self.config = config
        self.console = console
        self.history: list[dict[str, str]] = []

    def run(self) -> None:
        """Main chat loop."""
        self.console.print(
            Panel(
                "Type naturally. I manage your opportunities.\nType [bold]quit[/bold] to exit.",
                title="Corp Opportunity Manager",
                border_style="cyan",
            )
        )

        while True:
            try:
                user_input = Prompt.ask("[bold green]You[/bold green]")
            except (KeyboardInterrupt, EOFError):
                self.console.print("\n[dim]Bye![/dim]")
                break

            stripped = user_input.strip()
            if not stripped:
                continue
            if stripped.lower() in ("quit", "exit", "q"):
                self.console.print("[dim]Bye![/dim]")
                break

            self._process(stripped)

    def _process(self, user_input: str) -> None:
        """Parse intent and route to the appropriate handler."""
        context = self._build_context()

        result = parse_intent(
            user_message=user_input,
            conversation_history=self.history[-MAX_HISTORY:],
            project_context=context,
        )

        logger.debug("Intent: %s (confidence=%.2f)", result.intent, result.confidence)

        # Route to handler
        handler = _INTENT_HANDLERS.get(result.intent, _handle_fallback)
        handler(self, result)

        # Update history
        self.history.append({"role": "user", "text": user_input})
        self.history.append({"role": "assistant", "text": result.response_text})

    def _build_context(self) -> str:
        """Build a project context string for the LLM."""
        parts = [f"Today: {date.today().isoformat()}"]

        if self.config.projects_root.exists():
            dirs = [d.name for d in sorted(self.config.projects_root.iterdir()) if d.is_dir()]
            if dirs:
                parts.append(f"Existing projects: {', '.join(dirs[:20])}")

        parts.append(f"Available products: {', '.join(self.config.products)}")
        return " | ".join(parts)


# --- Intent handlers ---


def _handle_create_opportunity(session: ChatSession, result: IntentResult) -> None:
    entities = result.entities
    client = entities.get("client")
    product = entities.get("product")

    if not client or not product:
        session.console.print(f"[yellow]Agent:[/yellow] {result.response_text}")
        return

    opp = OpportunityConfig(
        client=client,
        product=product,
        contact=entities.get("contact") or "",
        stage=entities.get("stage") or "discovery",
        topic=entities.get("topic") or "Discovery",
        date=_parse_date(entities.get("date")),
    )

    try:
        creation = create_opportunity(session.config, opp)
    except FileExistsError:
        session.console.print(f"[yellow]Agent:[/yellow] {result.response_text}")
        session.console.print(f"[red]Folder already exists for {client}_{product}.[/red]")
        return

    # Override response with actual results
    deck_name = creation.deck_path.name if creation.deck_path else "(no template)"
    msg = (
        f"[green]Agent:[/green] Created:\n"
        f"  Folder: [cyan]{creation.folder_path.name}/[/cyan]\n"
        f"  Deck:   [cyan]{deck_name}[/cyan]\n"
        f"  Info:   [cyan]_knowledge/project-info.yaml[/cyan]"
    )
    if opp.contact:
        msg += f" (contact: {opp.contact})"
    session.console.print(msg)

    # Try Excel update
    _try_excel_update(session, client, creation.folder_path)


def _handle_prep_deck(session: ChatSession, result: IntentResult) -> None:
    entities = result.entities
    client = entities.get("client")
    topic = entities.get("topic")

    if not client or not topic:
        session.console.print(f"[yellow]Agent:[/yellow] {result.response_text}")
        return

    project_dir = _find_project(session, client)
    if not project_dir:
        session.console.print(f"[red]Agent:[/red] No project folder found for '{client}'.")
        return

    dt = _parse_date(entities.get("date"))

    template_name = session.config.templates.get("discovery_deck", "")
    source = session.config.templates_root / template_name if template_name else None

    if not source or not source.exists():
        session.console.print(f"[red]Agent:[/red] Deck template not found: {source}")
        return

    dest_name = deck_filename(
        client=client,
        topic=topic,
        dt=dt,
        date_format=session.config.naming.get("date_format", "%Y-%m-%d"),
        pattern=session.config.naming.get("pptx_pattern", "{client}_{date}_{topic}.pptx"),
    )
    dest = project_dir / dest_name
    shutil.copy2(source, dest)
    session.console.print(
        f"[green]Agent:[/green] [cyan]{dest_name}[/cyan] created in [cyan]{project_dir.name}/[/cyan]"
    )


def _handle_show_project(session: ChatSession, result: IntentResult) -> None:
    client = result.entities.get("client")
    if not client:
        session.console.print(f"[yellow]Agent:[/yellow] {result.response_text}")
        return

    project_dir = _find_project(session, client)
    if not project_dir:
        session.console.print(f"[red]Agent:[/red] No project folder found for '{client}'.")
        return

    files = list_project_files(project_dir)
    if not files:
        session.console.print(
            f"[yellow]Agent:[/yellow] Folder [cyan]{project_dir.name}/[/cyan] is empty."
        )
        return

    table = Table(title=f"{project_dir.name}/", show_header=True, border_style="blue")
    table.add_column("File", style="cyan")
    table.add_column("Size", justify="right")

    for f in files:
        table.add_row(f["path"], f["size"])

    session.console.print("[green]Agent:[/green]")
    session.console.print(table)


def _handle_list_projects(session: ChatSession, result: IntentResult) -> None:
    if not session.config.projects_root.exists():
        session.console.print("[red]Agent:[/red] Projects root not found.")
        return

    dirs = [d for d in sorted(session.config.projects_root.iterdir()) if d.is_dir()]
    if not dirs:
        session.console.print("[yellow]Agent:[/yellow] No project folders found.")
        return

    table = Table(title="Projects", border_style="blue")
    table.add_column("Folder", style="bold")
    table.add_column("Has Metadata")

    for d in dirs:
        has_meta = "yes" if (d / "_knowledge" / "project-info.yaml").exists() else "-"
        table.add_row(d.name, has_meta)

    session.console.print("[green]Agent:[/green]")
    session.console.print(table)


def _handle_create_subfolder(session: ChatSession, result: IntentResult) -> None:
    client = result.entities.get("client")
    folder_type = result.entities.get("folder_type")

    if not client or not folder_type:
        session.console.print(f"[yellow]Agent:[/yellow] {result.response_text}")
        return

    project_dir = _find_project(session, client)
    if not project_dir:
        session.console.print(f"[red]Agent:[/red] No project folder found for '{client}'.")
        return

    try:
        created = create_subfolder(project_dir, folder_type)
    except ValueError as e:
        session.console.print(f"[red]Agent:[/red] {e}")
        return

    created_names = [str(p.relative_to(project_dir)) for p in created]
    session.console.print(
        f"[green]Agent:[/green] Created in [cyan]{project_dir.name}/[/cyan]:\n"
        + "\n".join(f"  [cyan]{n}/[/cyan]" for n in created_names)
    )


def _handle_check_structure(session: ChatSession, result: IntentResult) -> None:
    client = result.entities.get("client")
    if not client:
        session.console.print(f"[yellow]Agent:[/yellow] {result.response_text}")
        return

    project_dir = _find_project(session, client)
    if not project_dir:
        session.console.print(f"[red]Agent:[/red] No project folder found for '{client}'.")
        return

    issues = check_structure(project_dir)

    if not issues:
        session.console.print(
            f"[green]Agent:[/green] [cyan]{project_dir.name}/[/cyan] — all good, no issues found."
        )
        return

    lines = [f"[green]Agent:[/green] [cyan]{project_dir.name}/[/cyan] audit:"]
    for issue in issues:
        icon = {
            "missing_folder": "[yellow]![/yellow]",
            "missing_file": "[yellow]![/yellow]",
            "non_standard_name": "[yellow]~[/yellow]",
            "misplaced_file": "[yellow]>[/yellow]",
        }.get(issue.issue_type, "?")
        short_path = Path(issue.path).name
        lines.append(f"  {icon} {short_path}: {issue.suggestion}")

    session.console.print("\n".join(lines))


def _handle_chitchat(session: ChatSession, result: IntentResult) -> None:
    session.console.print(f"[green]Agent:[/green] {result.response_text}")


def _handle_fallback(session: ChatSession, result: IntentResult) -> None:
    session.console.print(f"[yellow]Agent:[/yellow] {result.response_text}")


# --- Intent handler registry ---

_INTENT_HANDLERS: dict[str, Callable] = {
    "create_opportunity": _handle_create_opportunity,
    "prep_deck": _handle_prep_deck,
    "show_project": _handle_show_project,
    "list_projects": _handle_list_projects,
    "create_subfolder": _handle_create_subfolder,
    "check_structure": _handle_check_structure,
    "chitchat": _handle_chitchat,
    "clarify": _handle_fallback,
}


# --- Helpers ---


def _find_project(session: ChatSession, client: str) -> Path | None:
    """Find a project folder matching the client name (prefix match)."""
    if not session.config.projects_root.exists():
        return None
    client_lower = client.lower()
    for d in sorted(session.config.projects_root.iterdir()):
        if d.is_dir() and d.name.lower().startswith(client_lower):
            return d
    return None


def _parse_date(date_str: str | None) -> date:
    """Parse a YYYY-MM-DD string or return today."""
    if date_str:
        try:
            return datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            pass
    return date.today()


def _try_excel_update(session: ChatSession, client: str, folder_path: Path) -> None:
    """Attempt to update Excel with folder link."""
    if not session.config.project_codes_excel or not session.config.project_codes_excel.exists():
        return

    from corp_opportunity_manager.excel_manager import find_row_by_client, update_folder_link

    row = find_row_by_client(session.config.project_codes_excel, client)
    if row:
        update_folder_link(session.config.project_codes_excel, row.row_number, str(folder_path))
        session.console.print(f"[dim]Updated Excel row {row.row_number} with folder link.[/dim]")
