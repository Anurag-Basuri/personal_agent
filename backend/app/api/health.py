"""Health check endpoint."""

import time

from fastapi import APIRouter

from app.core.responses import success_response

router = APIRouter(tags=["Health"])

_start_time = time.time()


@router.get("/health")
async def health_check():
    uptime_seconds = round(time.time() - _start_time)
    return success_response(
        data={
            "status": "ok",
            "version": "1.0.0",
            "runtime": "python/fastapi",
            "uptime_seconds": uptime_seconds,
        },
        message="Server is healthy",
    )
