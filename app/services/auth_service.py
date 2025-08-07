import httpx
from typing import Optional, Dict, Any
from app.core.config import settings
from app.utils.logger import logger


class AzureADService:
    """Azure AD service for token validation"""

    def __init__(self):
        self.client_id = settings.AZURE_CLIENT_ID
        self.client_secret = settings.AZURE_CLIENT_SECRET
        self.tenant_id = settings.AZURE_TENANT_ID
        self.graph_api_base_url = settings.GRAPH_API_BASE_URL

    async def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Validate Azure AD token and get user information.

        Args:
            token: Azure AD access token

        Returns:
            Dict containing user information and token details, or None if invalid
        """
        try:
            headers = {"Authorization": f"Bearer {token}"}

            async with httpx.AsyncClient(verify=False) as client:
                response = await client.get(
                    f"{self.graph_api_base_url}/me", headers=headers
                )

                if response.status_code == 200:
                    user_info = response.json()
                    logger.info(
                        "Token validated successfully", user_id=user_info.get("id")
                    )

                    return {"user_info": user_info, "valid": True}
                else:
                    logger.warning(
                        "Token validation failed", status_code=response.status_code
                    )
                    return None

        except Exception as e:
            logger.error("Error validating token", error=str(e))
            return None


azure_ad_service = AzureADService()
