"""DEPRECATED — import from corp.schema.naming_config instead.

naming_config was moved to corp.schema (layer 0) so that retrieve/ and other
modules below ingest/ can import it without creating an upward layer dependency.
"""
from corp.schema.naming_config import *  # noqa: F401,F403
