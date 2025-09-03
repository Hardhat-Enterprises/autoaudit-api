from starlette.types import ASGIApp, Receive, Scope, Send
from fastapi import Request, Response
from app.services.cache_service import cache_service
from app.core.config import settings
import json

class CacheMiddleware:
    """Middleware to cache GET responses."""

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        # Only cache HTTP GET requests
        if scope["type"] == "http" and scope["method"] == "GET":
            request = Request(scope, receive)
            key = request.url.path + "?" + (request.url.query or "")
            if settings.CACHE_ENABLED:
                # Try to fetch from cache
                cached = await cache_service.get(key)
                if cached:
                    # Return cached response
                    headers = {"content-type": "application/json"}
                    response = Response(content=cached, status_code=200, headers=headers)
                    await response(scope, receive, send)
                    return

            # Capture the response
            responder = _ResponseCatcher(self.app, key)
            await responder(scope, receive, send)
            return

        # Non-GET or caching disabled: continue normally
        await self.app(scope, receive, send)


class _ResponseCatcher:
    """Helper to capture response body and cache it."""

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
                self.headers = dict(message.get("headers", []))
            elif message["type"] == "http.response.body":
                self.body += message.get("body", b"")
            await send(message)

        await self.app(scope, receive, send_wrapper)

        # Cache successful GET responses
        if self.status_code == 200:
            await cache_service.set(self.key, self.body.decode(), settings.CACHE_TTL_DEFAULT)
