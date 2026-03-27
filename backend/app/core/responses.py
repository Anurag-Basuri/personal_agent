"""
Standardized API response utilities.

Every endpoint should return responses via these helpers
to guarantee a consistent JSON envelope.
"""

from __future__ import annotations

import math
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi.responses import JSONResponse


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def success_response(
    data: Any = None,
    message: str = "OK",
    status_code: int = 200,
    request_id: str | None = None,
) -> JSONResponse:
    """Return a standardized success response."""
    return JSONResponse(
        status_code=status_code,
        content={
            "success": True,
            "message": message,
            "data": data,
            "request_id": request_id or str(uuid.uuid4()),
            "timestamp": _now_iso(),
        },
    )


def paginated_response(
    items: list[Any],
    total: int,
    page: int,
    limit: int,
    message: str = "OK",
    request_id: str | None = None,
) -> JSONResponse:
    """Return a standardized paginated response."""
    return JSONResponse(
        status_code=200,
        content={
            "success": True,
            "message": message,
            "data": {
                "items": items,
                "total": total,
                "page": page,
                "limit": limit,
                "total_pages": math.ceil(total / limit) if limit else 0,
            },
            "request_id": request_id or str(uuid.uuid4()),
            "timestamp": _now_iso(),
        },
    )
