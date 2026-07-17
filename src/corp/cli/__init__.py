"""CLI entry point for corp.

Commands:
    corp project list [--status active]
    corp project show <name>
    corp project open <name>
    corp vault validate [project]
    corp doctor
    corp run <workflow> [PARAMS]
    corp run --list
    corp task add "Title" [--project X] [--deadline DATE] [--priority high]
    corp task list [--status todo] [--project X]
    corp task done "Title"
    corp tasks
    corp index rebuild [--project X]
    corp index stats
    corp query "search terms" [--project X] [--product Y] [--topic Z]
    corp analytics report
    corp analytics products --client CLIENT
    corp analytics timeline --client CLIENT
    corp analytics clients --product PRODUCT
    corp analytics overlap --product PRODUCT
    corp analytics compare --clients "C1,C2"
    corp analytics recent
    corp template list
    corp template scan
    corp template select "goal description"
    corp extract <folder> [--batch] [--dry-run] [--output-dir PATH]
    corp overnight [--scope SCOPE] [--budget N] [--dry-run] [--batch]
    corp cleanup-scan [--output PATH]
    corp apply-moves <moves-file> [--dry-run]
    corp cleanup [--scope all|duplicates|overlap|artifacts] [--execute]
    corp audit [--skip-gemini] [--budget 0.30]
    corp ingest [PATH] [--dry-run] [--no-extract]
    corp finalize [--approve-all]
    corp chat [--no-llm]
    corp retrieve "query" [--client X] [--product Y] [--top N] [--format json|table]
    corp prep <client> [--model M] [--output DIR]
    corp rfp answer "question" [--client X] [--product Y] [--model M]
    corp freshness [--verbose]
"""

from __future__ import annotations

import logging

import click

from corp.cli.analytics import (
    analytics_group,
    dedup_report_command,
    files_stats_command,
    naming_stats_command,
)
from corp.cli.cleanup import (
    apply_moves_command,
    audit_command,
    cleanup_cmd,
    cleanup_scan_command,
)
from corp.cli.extract import extract_command
from corp.cli.index import index_group
from corp.cli.ingest import (
    classify_command,
    finalize_command,
    freshness_cmd,
    ingest_command,
    ingest_extractions_cmd,
    ingest_inbox_command,
)
from corp.cli.misc import chat_command, test_pipeline_command
from corp.cli.overnight import overnight_command
from corp.cli.project import project
from corp.cli.query import folder_review_command, query_command
from corp.cli.retrieve import prep_cmd, retrieve_cmd
from corp.cli.rfp import rfp_group
from corp.cli.system import (
    doctor,
    routing_mark_reviewed,
    routing_review,
    trust_status,
)
from corp.cli.template import template_group
from corp.cli.vault import vault
from corp.cli.workflow import run_workflow
from corp.schema.pipeline_config import PipelineConfig


@click.group()
@click.option("--verbose", "-v", is_flag=True, help="Enable debug logging")
@click.pass_context
def cli(ctx: click.Context, verbose: bool) -> None:
    """Corp-by-os — root orchestrator for the agent ecosystem."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(levelname)s %(name)s: %(message)s")
    ctx.ensure_object(dict)
    ctx.obj["config"] = PipelineConfig.production()


cli.add_command(project)
cli.add_command(vault)
cli.add_command(template_group)
cli.add_command(index_group)
cli.add_command(rfp_group)
cli.add_command(doctor)
cli.add_command(trust_status)
cli.add_command(routing_review)
cli.add_command(routing_mark_reviewed)
cli.add_command(run_workflow)
cli.add_command(query_command)
cli.add_command(folder_review_command)
cli.add_command(analytics_group)
cli.add_command(dedup_report_command)
cli.add_command(files_stats_command)
cli.add_command(naming_stats_command)
cli.add_command(test_pipeline_command)
cli.add_command(chat_command)
cli.add_command(retrieve_cmd)
cli.add_command(prep_cmd)
cli.add_command(extract_command)
cli.add_command(cleanup_scan_command)
cli.add_command(apply_moves_command)
cli.add_command(cleanup_cmd)
cli.add_command(audit_command)
cli.add_command(ingest_command)
cli.add_command(ingest_inbox_command)
cli.add_command(finalize_command)
cli.add_command(classify_command)
cli.add_command(freshness_cmd)
cli.add_command(ingest_extractions_cmd)
cli.add_command(overnight_command)

if __name__ == "__main__":
    cli()
