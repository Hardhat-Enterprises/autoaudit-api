from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
import requests
import os
import logging
from typing import Optional

router = APIRouter()

# --- Config ---
DEV_PROXY = os.getenv("DEV_PROXY_URL", "http://localhost:8000")
GRAPH_API = os.getenv("GRAPH_API_URL", "https://graph.microsoft.com/v1.0")

# --- Logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Pydantic models for validation ---
class SearchQuery(BaseModel):
    query: str

class UserFilter(BaseModel):
    display_name: Optional[str] = None
    mail: Optional[str] = None

# --- Helper function ---
def call_graph_api(path: str):
    """
    Helper to call Microsoft Graph API via Dev Proxy.
    Handles errors and enforces consistent responses.
    """
    # Ensure path doesn't have double slashes
    clean_path = path.lstrip('/')
    url = f"{GRAPH_API}/{clean_path}"
    
    try:
        logger.info(f"Calling Graph API via proxy: {url}")
        resp = requests.get(
            url,
            proxies={"https": DEV_PROXY, "http": DEV_PROXY},  # Handle both HTTP and HTTPS
            verify=False,  # Dev Proxy uses self-signed certs
            timeout=30,    # Increased timeout for dev proxy
            headers={
                "User-Agent": "FastAPI-DevProxy/1.0"  # Help identify requests in logs
            }
        )
        
        logger.info(f"Response status: {resp.status_code}")
        
    except requests.Timeout:
        logger.error(f"Request timeout for {url}")
        raise HTTPException(status_code=504, detail="Request timeout")
    except requests.RequestException as e:
        logger.error(f"Request failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Graph API request failed: {str(e)}")

    # Handle specific status codes
    if resp.status_code == 404:
        raise HTTPException(status_code=404, detail="Resource not found")
    elif resp.status_code == 403:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    elif resp.status_code >= 400:
        try:
            error_data = resp.json()
            error_msg = error_data.get("error", {}).get("message", resp.text)
            error_code = error_data.get("error", {}).get("code", "UnknownError")
            logger.error(f"Graph API error {resp.status_code}: {error_msg} (Code: {error_code})")
        except Exception:
            error_msg = resp.text
            logger.error(f"Graph API error {resp.status_code}: {error_msg}")
        
        raise HTTPException(status_code=resp.status_code, detail=error_msg)

    # Parse JSON response
    try:
        return resp.json()
    except ValueError:
        logger.warning("Response is not valid JSON")
        return {"raw_response": resp.text}

def escape_odata_string(value: str) -> str:
    """Escape single quotes in OData string values"""
    return value.replace("'", "''")

# --- Endpoints ---
# @router.get("/health")
# def health_check():
#     """Health check endpoint"""
#     return {
#         "status": "healthy",
#         "proxy_url": DEV_PROXY,
#         "graph_api": GRAPH_API
#     }

@router.get("/users")
def get_users():
    """Fetch all users (limited to first 100 by default)."""
    return call_graph_api("users")

@router.get("/users/top/{count}")
def get_users_top(count: int):
    """Fetch top N users."""
    if count > 999:
        raise HTTPException(status_code=400, detail="Maximum count is 999")
    return call_graph_api(f"users?$top={count}")

@router.get("/groups")
def get_groups():
    """Fetch all groups."""
    return call_graph_api("groups")

@router.get("/groups/top/{count}")
def get_groups_top(count: int):
    """Fetch top N groups."""
    if count > 999:
        raise HTTPException(status_code=400, detail="Maximum count is 999")
    return call_graph_api(f"groups?$top={count}")

@router.get("/users/{user_id}")
def get_user(user_id: str):
    """Fetch a specific user by ID or UPN."""
    # Note: Dev Proxy should handle URL encoding, but we can be safe
    return call_graph_api(f"users/{user_id}")

@router.get("/groups/{group_id}")
def get_group(group_id: str):
    """Fetch a specific group by ID."""
    return call_graph_api(f"groups/{group_id}")

@router.get("/groups/{group_id}/members")
def get_group_members(group_id: str):
    """Fetch members of a specific group."""
    return call_graph_api(f"groups/{group_id}/members")

@router.post("/users/search")
def search_users(search_data: SearchQuery):
    """
    Search for users by displayName or mail.
    Expected body: { "query": "search_term" }
    """
    search_term = search_data.query.strip()
    if not search_term:
        raise HTTPException(status_code=400, detail="Query parameter cannot be empty")
    
    # Escape single quotes for OData
    escaped_term = escape_odata_string(search_term)
    
    # Build filter exactly as Dev Proxy expects
    filter_query = (
        f"users?$filter=startswith(displayName,'{escaped_term}') "
        f"or startswith(mail,'{escaped_term}')"
    )
    
    return call_graph_api(filter_query)

@router.post("/users/filter")
def filter_users(filter_data: UserFilter):
    """
    Filter users by displayName and/or mail.
    Expected body: { "display_name": "John", "mail": "john@company.com" }
    """
    filters = []
    
    if filter_data.display_name:
        escaped_name = escape_odata_string(filter_data.display_name.strip())
        filters.append(f"startswith(displayName,'{escaped_name}')")
    
    if filter_data.mail:
        escaped_mail = escape_odata_string(filter_data.mail.strip())
        filters.append(f"startswith(mail,'{escaped_mail}')")
    
    if not filters:
        raise HTTPException(status_code=400, detail="At least one filter criteria must be provided")
    
    filter_expr = " and ".join(filters)  # Use AND for multiple criteria
    filter_query = f"users?$filter={filter_expr}"
    
    return call_graph_api(filter_query)

@router.get("/users/{user_id}/manager")
def get_user_manager(user_id: str):
    """Get a user's manager."""
    return call_graph_api(f"users/{user_id}/manager")

@router.get("/users/{user_id}/direct-reports")
def get_user_direct_reports(user_id: str):
    """Get a user's direct reports."""
    return call_graph_api(f"users/{user_id}/directReports")


# --- Raw query endpoint for testing purposes ( delete later) ---
# @router.post("/raw-query")
# def raw_graph_query(query_data: dict = Body(...)):
#     """
#     Execute a raw Graph API query for testing purposes.
#     Expected body: { "path": "users?$filter=..." }
#     """
#     path = query_data.get("path", "").strip()
#     if not path:
#         raise HTTPException(status_code=400, detail="Path parameter is required")
    
#     # Basic safety check - don't allow certain operations in dev
#     dangerous_operations = ["$batch", "DELETE", "PUT", "PATCH"]
#     if any(op in path.upper() for op in dangerous_operations):
#         raise HTTPException(status_code=400, detail="Operation not allowed in development mode")
    
#     return call_graph_api(path)