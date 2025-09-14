from __future__ import annotations

import logging
import time
import uuid
from typing import Callable

from fastapi import Request

logger = logging.getLogger("uvicorn.access")


async def correlation_middleware(request: Request, call_next: Callable):  # type: ignore[override]
    start = time.perf_counter()

    # Correlation: request_id from header or generate
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())

    # Client info
    client_ip = (request.client.host if request.client else None) or request.headers.get("X-Forwarded-For", "-")
    user_agent = request.headers.get("User-Agent", "-")

    try:
        response = await call_next(request)
        status_code = int(getattr(response, "status_code", 500))
        # Propagate header when response exists
        try:
            response.headers.setdefault('X-Request-ID', request_id)
        except Exception:
            pass
        return response
    except Exception:
        status_code = 500
        # Log stack with context
        logging.getLogger("fastapi").exception("Unhandled exception")
        raise
    finally:
        duration_ms = int((time.perf_counter() - start) * 1000)
        extra = {
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": status_code,
            "duration_ms": duration_ms,
            "client_ip": client_ip,
            "user_agent": user_agent,
        }
        # Access log line
        logger.info("HTTP access", extra=extra)
    # In exception path, response is generated upstream; header may not be set here
