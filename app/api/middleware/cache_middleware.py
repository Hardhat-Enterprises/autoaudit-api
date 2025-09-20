from starlette.types import ASGIApp, Receive, Scope, Send
from fastapi import Request, Response
from app.services.cache_service import cache_service
from app.core.config import settings
import json
from structlog import get_logger

logger = get_logger()


class CacheMiddleware:
    """Middleware to cache GET responses, including headers."""

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        # Only cache HTTP GET requests and if caching is enabled
        if scope["type"] == "http" and scope["method"] == "GET" and settings.CACHE_ENABLED:
            request = Request(scope, receive)
            key = request.url.path + "?" + (request.url.query or "")
            try:
                cached = await cache_service.get(key)
            except Exception as e:
                logger.error("Redis failure on cache GET", error=str(e))
                cached = None

            if cached:
                # Try to restore full response (body + headers + status)
                try:
                    cached_obj = json.loads(cached)
                    response = Response(
                        content=cached_obj.get("body", ""),
                        status_code=cached_obj.get("status_code", 200),
                        headers=cached_obj.get("headers", {}),
                    )
                    logger.debug("Cache hit", key=key)
                except Exception as e:
                    logger.error("Failed to parse cached response", error=str(e))
                    response = Response(content=cached, status_code=200)
                await response(scope, receive, send)
                return

            # Capture and cache the response if not in cache
            responder = _ResponseCatcher(self.app, key)
            await responder(scope, receive, send)
            return

        # Non-GET or caching disabled: continue normally
        await self.app(scope, receive, send)


class _ResponseCatcher:
    """Helper to capture response body, headers, and cache them."""

    def __init__(self, app: ASGIApp, key: str):
        self.app = app
        self.key = key
        self.body = b""
        self.status_code = 200
        self.headers = {}

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                self.status_code = message["status"]
                raw_headers = message.get("headers", [])
                # Decode headers into dict[str, str]
                self.headers = {k.decode(): v.decode() for k, v in raw_headers}
            elif message["type"] == "http.response.body":
                self.body += message.get("body", b"")
            await send(message)

        await self.app(scope, receive, send_wrapper)

        # Cache successful GET responses, only if enabled and Redis is available
        if self.status_code == 200 and settings.CACHE_ENABLED:
            try:
                payload = {
                    "body": self.body.decode(),
                    "headers": self.headers,
                    "status_code": self.status_code,
                }
                await cache_service.set(self.key, json.dumps(payload), settings.CACHE_TTL_DEFAULT)
                logger.debug("Response cached", key=self.key, ttl=settings.CACHE_TTL_DEFAULT)
            except Exception as e:
                logger.error("Redis failure on cache SET", error=str(e))
