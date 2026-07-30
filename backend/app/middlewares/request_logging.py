import time
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logger import agent_logger
from app.core.exceptions import _get_request_id


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip noisy endpoints
        path = request.url.path
        if path in ("/api/health", "/docs", "/openapi.json", "/redoc"):
            return await call_next(request)

        request_id = _get_request_id(request)
        method = request.method
        
        agent_logger.debug("API", f"→ {method} {path}", {"request_id": request_id})
        start_time = time.time()

        try:
            response = await call_next(request)
            duration_ms = round((time.time() - start_time) * 1000)
            
            # Log response
            status = response.status_code
            if status < 400:
                agent_logger.info("API", f"← {status} {method} {path} ({duration_ms}ms)", {"request_id": request_id})
            elif status < 500:
                agent_logger.warn("API", f"← {status} {method} {path} ({duration_ms}ms)", {"request_id": request_id})
            else:
                agent_logger.error("API", f"← {status} {method} {path} ({duration_ms}ms)", None, {"request_id": request_id})
                
            return response
            
        except Exception as e:
            # Safety net: log any exception that escapes the FastAPI exception handlers
            duration_ms = round((time.time() - start_time) * 1000)
            agent_logger.error("API", f"💥 FATAL {method} {path} ({duration_ms}ms)", e, {"request_id": request_id})
            raise
