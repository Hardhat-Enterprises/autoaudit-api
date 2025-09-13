from pydantic import BaseModel, Field
from typing import Optional, List

# ==========================================================
# Graph API Models
# ----------------------------------------------------------
# Request models validate incoming payloads.
# Response models define structured outputs for API routes.
# ==========================================================

# -------------------------
# Request Models
# -------------------------
class SearchQuery(BaseModel):
    """
    Request model for searching users in Microsoft Graph API.
    Used by POST /users/search endpoint.
    """
    query: str = Field(..., description="Search term for displayName or mail")


class UserFilter(BaseModel):
    """
    Request model for filtering users in Microsoft Graph API.
    Used by POST /users/filter endpoint.
    """
    display_name: Optional[str] = Field(
        default=None, description="Filter users by displayName prefix"
    )
    mail: Optional[str] = Field(
        default=None, description="Filter users by mail prefix"
    )


# -------------------------
# Response Models
# -------------------------
class UserResponse(BaseModel):
    """
    Response model representing a Microsoft Graph User.
    """
    id: str = Field(..., description="Unique identifier of the user")
    displayName: Optional[str] = Field(None, description="The user's display name")
    mail: Optional[str] = Field(None, description="The user's primary email address")
    userPrincipalName: Optional[str] = Field(
        None, description="The user's UPN (User Principal Name)"
    )


class GroupResponse(BaseModel):
    """
    Response model representing a Microsoft Graph Group.
    """
    id: str = Field(..., description="Unique identifier of the group")
    displayName: Optional[str] = Field(None, description="The group's display name")
    mail: Optional[str] = Field(None, description="The group's email address")
    mailEnabled: Optional[bool] = Field(None, description="Whether the group is mail-enabled")
    securityEnabled: Optional[bool] = Field(None, description="Whether the group is security-enabled")
    groupTypes: Optional[List[str]] = Field(
        None, description="Types of the group (e.g., 'Unified')"
    )
