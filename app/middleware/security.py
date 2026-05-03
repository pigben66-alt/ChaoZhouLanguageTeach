import time
import re
from collections import defaultdict
from datetime import datetime, timedelta
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from app.config import get_settings

settings = get_settings()


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, requests_per_minute: int = 100):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.client_requests: dict[str, list[float]] = defaultdict(list)

    def _get_client_id(self, request: Request) -> str:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    def _is_rate_limited(self, client_id: str) -> bool:
        now = time.time()
        minute_ago = now - 60

        if client_id in self.client_requests:
            self.client_requests[client_id] = [
                t for t in self.client_requests[client_id] if t > minute_ago
            ]

        if len(self.client_requests[client_id]) >= self.requests_per_minute:
            return True

        self.client_requests[client_id].append(now)
        return False

    async def dispatch(self, request: Request, call_next):
        client_id = self._get_client_id(request)

        if self._is_rate_limited(client_id):
            return Response(
                content='{"detail":"请求过于频繁，请稍后再试"}',
                status_code=429,
                media_type="application/json",
                headers={"Retry-After": "60"},
            )

        response = await call_next(request)
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:;"

        return response


class InputSanitizationMiddleware(BaseHTTPMiddleware):
    DANGEROUS_PATTERNS = [
        r"(<script[^>]*>.*?</script>)",
        r"(<iframe[^>]*>.*?</iframe>)",
        r"(javascript:)",
        r"(onerror\s*=)",
        r"(onload\s*=)",
        r"(onclick\s*=)",
        r"(\bunion\b.*\bselect\b)",
        r"(\bdrop\b.*\btable\b)",
        r"(\bexec\b\s*\()",
        r"(\bshutdown\b)",
    ]

    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.dangerous_regex = [re.compile(p, re.IGNORECASE) for p in self.DANGEROUS_PATTERNS]

    def _sanitize_input(self, text: str) -> str:
        text = re.sub(r"[<>'\";&]", "", text)
        return text.strip()

    def _check_dangerous(self, text: str) -> bool:
        for pattern in self.dangerous_regex:
            if pattern.search(text):
                return True
        return False

    async def dispatch(self, request: Request, call_next):
        if request.method in ["POST", "PUT", "PATCH"]:
            content_type = request.headers.get("content-type", "")

            if "application/json" in content_type or "application/x-www-form-urlencoded" in content_type:
                query_params = dict(request.query_params)
                for key, value in query_params.items():
                    if isinstance(value, str):
                        sanitized = self._sanitize_input(value)
                        if sanitized != value:
                            return Response(
                                content='{"detail":"输入包含非法字符"}',
                                status_code=400,
                                media_type="application/json",
                            )

                        if self._check_dangerous(value):
                            return Response(
                                content='{"detail":"输入包含潜在危险内容"}',
                                status_code=400,
                                media_type="application/json",
                            )

        response = await call_next(request)
        return response
