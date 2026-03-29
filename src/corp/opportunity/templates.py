"""Naming convention logic for folders, files, and decks."""

from __future__ import annotations

from datetime import date


def folder_name(client: str, product: str, pattern: str = "{client}_{product}") -> str:
    """Generate the project folder name from client + product."""
    return pattern.format(client=client, product=product)


def deck_filename(
    client: str,
    topic: str = "Discovery",
    dt: date | None = None,
    date_format: str = "%Y-%m-%d",
    pattern: str = "{client}_{date}_{topic}.pptx",
) -> str:
    """Generate a presentation filename.

    Example: Lenzing_2026-03-05_Discovery.pptx
    """
    if dt is None:
        dt = date.today()
    date_str = dt.strftime(date_format)
    return pattern.format(client=client, date=date_str, topic=topic)
