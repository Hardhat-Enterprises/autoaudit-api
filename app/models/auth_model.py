from pydantic import BaseModel, Field
from typing import Optional, List


class UserInfo(BaseModel):
    """User information model."""

    user_id: str = Field(description="User ID")
    email: str = Field(description="User email")
    name: str = Field(description="User name")
    display_name: Optional[str] = Field(default=None, description="User display name")
    roles: List[str] = Field(default=[], description="User roles")
    permissions: List[str] = Field(default=[], description="User permissions")
    tenant_id: Optional[str] = Field(default=None, description="Azure AD tenant ID")


class TokenResponse(BaseModel):
    """Token validation response model."""

    valid: bool = Field(description="Whether the token is valid")
    user_info: Optional[UserInfo] = Field(
        default=None, description="User information if token is valid"
    )
    expires_at: Optional[str] = Field(default=None, description="Token expiration time")
    scopes: List[str] = Field(default=[], description="Token scopes")


class TokenRequest(BaseModel):
    """Token request model."""

    token: str = Field(description="Token to validate")
