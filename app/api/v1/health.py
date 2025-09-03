from fastapi import APIRouter
import os
import httpx

from app.core.config import settings

router = APIRouter(tags=["Health"])

#tiny helpers to keep responses consistent ----------

def ok(name: str, detail: dict | None = None):
    return {"name": name, "status": "healthy", "detail": detail or {}}

def bad(name: str, error: str):
    return {"name": name, "status": "unhealthy", "detail": {"error": error}}

def skipped(name: str, reason: str):
    return {"name": name, "status": "skipped", "detail": {"reason": reason}}


#1) Basic health ----------

@router.get("/health", summary="Basic liveness check")
async def health_basic():
    """Very small check to prove the API is running."""
    return {"status": "healthy", "version": settings.VERSION}


#2) Database health (simple) ----------

@router.get("/health/database", summary="Check database connectivity")
async def health_database():
    """
    Simple rule:
    - If DATABASE_URL is missing -> 'skipped'
    - If present -> we check the format looks like a URL.
      (For a student project, that's enough. Later you can plug a real SELECT 1.)
    """
    db_url = os.getenv("DATABASE_URL") or getattr(settings, "DATABASE_URL", None)

    if not db_url:
        return skipped("database", "DATABASE_URL not set (skipping in local dev)")

    if "://" not in db_url:
        return bad("database", "DATABASE_URL format looks wrong")

    # If it looks OK, we treat database as healthy for now.
    return ok("database", {"configured": True})


#3) Microsoft Graph health (simple) ----------

@router.get("/health/microsoft-graph", summary="Check Microsoft Graph availability")
async def health_graph():
    """
    Try to get an Azure AD token (client credentials) and call a tiny Graph endpoint.
    If Azure secrets are missing, we 'skip' the check so local dev still works.
    """
    client_id = settings.AZURE_CLIENT_ID or ""
    client_secret = settings.AZURE_CLIENT_SECRET or ""
    tenant_id = settings.AZURE_TENANT_ID or ""

    if not client_id or not client_secret or not tenant_id:
        return skipped("microsoft_graph", "Azure secrets not set (skipping in local dev)")

    token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
    data = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
        "scope": "https://graph.microsoft.com/.default",
    }

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            # get token
            token_resp = await client.post(token_url, data=data)
            if token_resp.status_code != 200:
                return bad("microsoft_graph", f"token error: {token_resp.status_code}")

            access_token = token_resp.json().get("access_token")
            if not access_token:
                return bad("microsoft_graph", "no access_token in token response")

            # ping a tiny Graph endpoint
            graph_url = settings.GRAPH_API_BASE_URL.rstrip("/") + "/organization?$select=id"
            headers = {"Authorization": f"Bearer {access_token}"}
            graph_resp = await client.get(graph_url, headers=headers)

            if 200 <= graph_resp.status_code < 300:
                return ok("microsoft_graph", {"status_code": graph_resp.status_code})
            else:
                return bad("microsoft_graph", f"graph error: {graph_resp.status_code}")

    except Exception as e:
        return bad("microsoft_graph", str(e))


#4) Overall health

@router.get("/health/overall", summary="Overall system health")
async def health_overall():
    """
    We call the two checks above and summarize:
    - If any check is 'unhealthy' -> overall is 'unhealthy'
    - 'skipped' checks do NOT fail overall (handy for local/student projects)
    """
    db = await health_database()
    graph = await health_graph()

    components = [db, graph]
    any_unhealthy = any(c["status"] == "unhealthy" for c in components)
    overall = "unhealthy" if any_unhealthy else "healthy"

    return {
        "status": overall,
        "version": settings.VERSION,
        "components": components,
    }