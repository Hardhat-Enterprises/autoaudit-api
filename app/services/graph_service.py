import httpx
from app.utils.logger import logger
from fastapi import HTTPException
from app.core.config import settings


def escape_odata_string(value: str) -> str:
    """Escape single quotes in OData string values for OData queries."""
    return value.replace("'", "''")


async def call_graph_api(path: str):
    """
    Helper function to call Microsoft Graph API (optionally via Dev Proxy).
    Handles errors, adds logging, and enforces consistent responses.
    
    Args:
        path (str): The relative Graph API path (e.g., "users", "groups/{id}")
    
    Returns:
        dict: Parsed JSON response from Graph API.
    """
    clean_path = path.lstrip("/")
    url = f"{settings.GRAPH_API_BASE_URL}/{clean_path}"

    # Configure transport for DEV_PROXY_URL is set
    transport = None
    if getattr(settings, "DEV_PROXY_URL", None):
        transport = httpx.AsyncHTTPTransport(proxy=settings.DEV_PROXY_URL, verify=False) #Make sure to remove the verification false later

    try:
        async with httpx.AsyncClient(
            transport=transport,
            verify=False,
            timeout=30,
        ) as client:
            resp = await client.get(
                url,
                headers={"User-Agent": "FastAPI-DevProxy/1.0"}
            )
    except httpx.TimeoutException:
        logger.error(f"Request timeout for {url}")
        raise HTTPException(status_code=504, detail="Request timeout")
    except httpx.RequestError as e:
        logger.error(f"Request failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Graph API request failed: {str(e)}")

    # Handle specific status codes in relation to HTTPExcptions
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

