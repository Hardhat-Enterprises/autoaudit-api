
import json
import httpx
from typing import Dict, Any, Optional
from app.core.config import settings
from app.services.cache_service import cache_service
from app.utils.logger import logger

class GraphService:
    def __init__(self):
        self.base = settings.GRAPH_API_BASE_URL.rstrip("/")

    def _users_cache_key(self, token: str, top: Optional[int]) -> str:
        suffix = f":top={top}" if top else ""
        # Use only the first 16 chars of token to avoid storing full secrets
        return f"graph_users:{token[:16]}{suffix}"

    def _me_cache_key(self, token: str) -> str:
       
        return f"graph_me:{token[:16]}"

    async def list_users(self, token: str, top: Optional[int] = None) -> Dict[str, Any]:
        key = self._users_cache_key(token, top)
        cached = await cache_service.get(key)
        if cached:
            try:
                data = json.loads(cached)
                logger.info("Users fetched from cache", count=len(data.get("value", [])))
                return {"source": "cache", "data": data}
            except Exception:
                logger.warning("Users cache decode failed; calling Graph", key=key)

        headers = {"Authorization": f"Bearer {token}"}
        params = {"$top": str(top)} if top else None
        async with httpx.AsyncClient(verify=False) as client:
            resp = await client.get(f"{self.base}/users", headers=headers, params=params)

        if resp.status_code == 200:
            data = resp.json()
            await cache_service.set(key, json.dumps(data))
            logger.info("Users fetched from Graph", count=len(data.get("value", [])))
            return {"source": "graph", "data": data}

        logger.warning("Users call failed", status_code=resp.status_code, text=resp.text)
        return {"source": "graph", "error": f"{resp.status_code}: {resp.text}"}

    async def get_me(self, token: str) -> Dict[str, Any]:
        key = self._me_cache_key(token)

        cached = await cache_service.get(key)
        if cached:
            try:
                data = json.loads(cached)
                logger.info("Me fetched from cache", user_id=data.get("id"))
                return {"source": "cache", "data": data}
            except Exception:
                logger.warning("Me cache decode failed; calling Graph", key=key)

        headers = {"Authorization": f"Bearer {token}"}
        async with httpx.AsyncClient(verify=False) as client:
            resp = await client.get(f"{self.base}/me", headers=headers)

        if resp.status_code == 200:
            data = resp.json()
            await cache_service.set(key, json.dumps(data))
            logger.info("Me fetched from Graph", user_id=data.get("id"))
            return {"source": "graph", "data": data}

        logger.warning("Me call failed", status_code=resp.status_code, text=resp.text)
        return {"source": "graph", "error": f"{resp.status_code}: {resp.text}"}
