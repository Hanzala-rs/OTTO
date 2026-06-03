"""Simple Redis-backed rate limiter — 60 requests/minute per IP."""
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from memory.session_store import get_redis

LIMIT = 60
WINDOW = 60   # seconds


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        ip = request.client.host if request.client else "unknown"
        key = f"ratelimit:{ip}"
        r = get_redis()
        count = r.incr(key)
        if count == 1:
            r.expire(key, WINDOW)
        if count > LIMIT:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Try again in a minute."},
            )
        return await call_next(request)
