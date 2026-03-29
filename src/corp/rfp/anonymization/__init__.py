"""
anonymization package
Clean architecture for data anonymization.
"""

from .config import (
    add_to_blocklist,
    get_blocklist,
    get_session,
    get_settings,
    load_config,
    set_session_customer,
)
from .core import anonymize, check, deanonymize
from .middleware import AnonymizationMiddleware

__all__ = [
    # Core functions
    "anonymize",
    "deanonymize",
    "check",
    # Config functions
    "load_config",
    "get_blocklist",
    "get_session",
    "set_session_customer",
    "add_to_blocklist",
    "get_settings",
    # Middleware
    "AnonymizationMiddleware",
]
