"""Shared state for all CLI domain modules."""

import logging

from rich.console import Console

# ASCII-safe markers for Windows legacy console compatibility
CHECK = "Y"
DASH = "-"

console = Console()
logger = logging.getLogger("corp_by_os.cli")
