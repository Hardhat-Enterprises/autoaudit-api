from fastapi import APIRouter, HTTPException
from app.services.auth_service import azure_ad_service
from app.models.auth import TokenResponse, TokenRequest, UserInfo
from app.utils.logger import logger

router = APIRouter()


@router.post("/validate-token", response_model=TokenResponse)
async def validate_token(token_request: TokenRequest):
    """
    Validate Azure AD token and return user information.

    This endpoint validates an Azure AD access token by calling the Microsoft Graph API
    and returns detailed user information if the token is valid.

    Args:
        token_request: TokenRevoke object containing the token to validate

    Returns:
        TokenValidation object with validation result and user information
    """
    try:
        logger.info("Token validation requested")

        validation_result = await azure_ad_service.validate_token(token_request.token)

        if validation_result and validation_result.get("valid"):
            user_info = validation_result["user_info"]

            # Convert to UserInfo model
            user_info_model = UserInfo(
                user_id=user_info["id"],
                email=user_info.get("userPrincipalName", ""),
                name=user_info.get("displayName", ""),
                display_name=user_info.get("displayName"),
                roles=[],
                permissions=[],
                tenant_id=user_info.get("tenantId"),
            )

            logger.info("Token validation successful", user_id=user_info["id"])

            return TokenResponse(
                valid=True,
                user_info=user_info_model,
                expires_at=None,
                scopes=[],
            )
        else:
            logger.warning("Token validation failed")
            return TokenResponse(valid=False)

    except Exception as e:
        logger.error("Error in token validation", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")
