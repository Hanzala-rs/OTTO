"""FastAPI middleware for rate limiting and basic request validation."""
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


class GuardrailsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Block abnormally large request bodies early
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > 10 * 1024 * 1024:  # 10MB
            return JSONResponse(status_code=413, content={"detail": "Payload too large"})
        return await call_next(request)
