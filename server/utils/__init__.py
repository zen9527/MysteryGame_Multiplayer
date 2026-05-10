"""Server utility modules for shared functionality."""

from server.utils.endpoint import normalize_endpoint
from server.utils.display_name import resolve_display_name, resolve_display_name_for_message

__all__ = [
    "normalize_endpoint",
    "resolve_display_name",
    "resolve_display_name_for_message",
]
