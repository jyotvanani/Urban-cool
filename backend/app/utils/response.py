"""Standardized JSON response builders.

Every successful response follows:
    {"success": true, "data": {...}, "message": "..."}

Every error/fallback response follows:
    {"success": false, "error": "...", "fallback_used": true}
"""

from typing import Any


def success_response(data: Any, message: str = "Request completed successfully") -> dict:
    """Build a standard success envelope."""
    return {
        "success": True,
        "data": data,
        "message": message,
    }


def error_response(error: str, fallback_used: bool = True, data: Any = None) -> dict:
    """Build a standard error/fallback envelope.

    We prefer returning a 200 with fallback data over raising 500 errors so the
    demo never breaks. ``data`` may carry any fallback payload that was used.
    """
    payload = {
        "success": False,
        "error": error,
        "fallback_used": fallback_used,
    }
    if data is not None:
        payload["data"] = data
    return payload
