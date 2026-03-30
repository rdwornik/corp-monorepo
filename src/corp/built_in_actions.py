"""Built-in Python actions for workflows — re-export shim.

All action logic has moved to corp.actions/ package.
This module re-exports names for backward compatibility.
"""

from corp.actions import get_action, register_action  # noqa: F401
from corp.actions._helpers import _slugify  # noqa: F401
from corp.actions.analytics_actions import _write_analytics_dashboard  # noqa: F401
from corp.actions.archive_actions import archive_project  # noqa: F401
from corp.actions.brief_actions import generate_project_brief  # noqa: F401
from corp.actions.inbox_actions import scan_inbox  # noqa: F401
from corp.actions.monitoring_actions import (  # noqa: F401
    generate_attention_dashboard,
    scan_attention,
)
from corp.actions.vault_actions import (  # noqa: F401
    copy_to_vault_action,
    create_vault_skeleton,
    validate_project,
)
