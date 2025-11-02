"""RFC 7807 Problem Details for HTTP APIs implementation."""

from typing import Any, Dict
from uuid import uuid4

from starlette.responses import JSONResponse


def problem(
    status: int,
    title: str,
    detail: str,
    type_: str = "about:blank",
    extras: Dict[str, Any] | None = None,
) -> JSONResponse:
    """
    Create RFC 7807 Problem Details response.

    Args:
        status: HTTP status code
        title: Short, human-readable summary of the problem type
        detail: Human-readable explanation specific to this occurrence
        type_: URI reference that identifies the problem type
        extras: Additional problem-specific fields

    Returns:
        JSONResponse with RFC 7807 format
    """
    correlation_id = str(uuid4())
    payload = {
        "type": type_,
        "title": title,
        "status": status,
        "detail": detail,
        "correlation_id": correlation_id,
    }
    if extras:
        payload.update(extras)
    return JSONResponse(payload, status_code=status)
