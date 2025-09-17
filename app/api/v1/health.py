from typing import Any, Dict, Literal

import httpx
from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.core.config import settings


router = APIRouter(tags=["Health"])


class HealthComponent(BaseModel):
    name: str = Field(..., description="Name of the component being checked.")
    status: Literal["healthy", "unhealthy", "skipped"] = Field(..., description="Result of the health check.")
    detail: Dict[str, Any] = Field(default_factory=dict, description="Additional diagnostic information.")


class BasicHealthResponse(BaseModel):
    status: Literal["healthy", "unhealthy"] = Field(..., description="Overall status of the API.")
    version: str = Field(..., description="Application version string.")


class OverallHealthResponse(BaseModel):
    status: Literal["healthy", "unhealthy"] = Field(..., description="Aggregated status across all checks.")
    version: str = Field(..., description="Application version string.")
    components: list[HealthComponent] = Field(..., description="Detailed results for each component.")


# Tiny helpers to keep responses consistent ----------

def ok(name: str, detail: Dict[str, Any] | None = None) -> HealthComponent:
    """Return a healthy response payload."""
    return HealthComponent(name=name, status="healthy", detail=detail or {})


def bad(name: str, error: str) -> HealthComponent:
    """Return an unhealthy response payload."""
    return HealthComponent(name=name, status="unhealthy", detail={"error": error})


def skipped(name: str, reason: str) -> HealthComponent:
    """Return a skipped response payload."""
    return HealthComponent(name=name, status="skipped", detail={"reason": reason})


# 1) Basic health ----------

@router.get(
    "/health",
    summary="Basic liveness check",
    description="Lightweight liveness check that verifies the application is running.",
    response_model=BasicHealthResponse,
    responses={
        200: {
            "description": "The API is reachable and responding.",
            "content": {
                "application/json": {
                    "example": {"status": "healthy", "version": "0.1.0"}
                }
            },
        }
    },
)
async def health_basic() -> BasicHealthResponse:
    """Very small check to prove the API is running."""
    return BasicHealthResponse(status="healthy", version=settings.VERSION)


# 2) Database health (simple) ----------

@router.get(
    "/health/database",
    summary="Check database connectivity",
    description=(
        "Reports database readiness. Local development environments without a database "
        "surface a skipped result rather than failing the overall health state."
    ),
    response_model=HealthComponent,
    responses={
        200: {
            "description": "Database configuration status.",
            "content": {
                "application/json": {
                    "examples": {
                        "healthy": {
                            "summary": "Database configured",
                            "value": {
                                "name": "database",
                                "status": "healthy",
                                "detail": {"configured": True},
                            },
                        },
                        "skipped": {
                            "summary": "Configuration missing",
                            "value": {
                                "name": "database",
                                "status": "skipped",
                                "detail": {
                                    "reason": "DATABASE_URL not set (skipping in local dev)"
                                },
                            },
                        },
                    }
                }
            },
        }
    },
)
async def health_database() -> HealthComponent:
    """
    Simple rule:
    - If DATABASE_URL is missing -> 'skipped'
    - If present -> we check the format looks like a URL.
      (For a student project, that's enough. Later you can plug a real SELECT 1.)
    """
    db_url = settings.DATABASE_URL

    if not db_url:
        return skipped("database", "DATABASE_URL not set (skipping in local dev)")

    if "://" not in db_url:
        return bad("database", "DATABASE_URL format looks wrong")

    # If it looks OK, we treat database as healthy for now.
    return ok("database", {"configured": True})


# 3) Microsoft Graph health (simple) ----------

@router.get(
    "/health/microsoft-graph",
    summary="Check Microsoft Graph availability",
    description=(
        "Performs a client credentials flow against Azure AD and pings a lightweight "
        "Microsoft Graph endpoint. Missing Azure configuration results in a skipped "
        "check so that local development remains functional."
    ),
    response_model=HealthComponent,
    responses={
        200: {
            "description": "Microsoft Graph connectivity status.",
            "content": {
                "application/json": {
                    "examples": {
                        "healthy": {
                            "summary": "Graph reachable",
                            "value": {
                                "name": "microsoft_graph",
                                "status": "healthy",
                                "detail": {"status_code": 200},
                            },
                        },
                        "skipped": {
                            "summary": "Missing Azure secrets",
                            "value": {
                                "name": "microsoft_graph",
                                "status": "skipped",
                                "detail": {
                                    "reason": "Azure secrets not set (skipping in local dev)"
                                },
                            },
                        },
                        "unhealthy": {
                            "summary": "Graph service issue",
                            "value": {
                                "name": "microsoft_graph",
                                "status": "unhealthy",
                                "detail": {"error": "token error: 401"},
                            },
                        },
                    }
                }
            },
        }
    },
)
async def health_graph() -> HealthComponent:
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
        async with httpx.AsyncClient(timeout=settings.HEALTH_TIMEOUT_SECONDS) as client:
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

    except Exception as exc:  # pragma: no cover - diagnostic path
        return bad("microsoft_graph", str(exc))


# 4) Overall health ----------

@router.get(
    "/health/overall",
    summary="Overall system health",
    description=(
        "Calls the individual database and Microsoft Graph health checks and aggregates "
        "their results. Skipped checks do not fail the overall status."
    ),
    response_model=OverallHealthResponse,
    responses={
        200: {
            "description": "Aggregated health report.",
            "content": {
                "application/json": {
                    "example": {
                        "status": "healthy",
                        "version": "0.1.0",
                        "components": [
                            {
                                "name": "database",
                                "status": "healthy",
                                "detail": {"configured": True},
                            },
                            {
                                "name": "microsoft_graph",
                                "status": "skipped",
                                "detail": {
                                    "reason": "Azure secrets not set (skipping in local dev)"
                                },
                            },
                        ],
                    }
                }
            },
        }
    },
)
async def health_overall() -> OverallHealthResponse:
    """
    Call the two checks above and summarize:
    - If any check is 'unhealthy' -> overall is 'unhealthy'
    - 'skipped' checks do NOT fail overall (handy for local/student projects)
    """
    db = await health_database()
    graph = await health_graph()

    components = [db, graph]
    any_unhealthy = any(component.status == "unhealthy" for component in components)
    overall = "unhealthy" if any_unhealthy else "healthy"

    return OverallHealthResponse(
        status=overall,
        version=settings.VERSION,
        components=components,
    )


