from fastapi import APIRouter, HTTPException
from typing import List

from app.models.graph_model import (
    SearchQuery,
    UserFilter,
    UserResponse,
    GroupResponse,
)
from app.services.graph_service import call_graph_api, escape_odata_string

router = APIRouter()


# ----------------------------
# Users
# ----------------------------
@router.get("/users", response_model=List[UserResponse])
async def get_users():
    """Fetch all users (limited to first 100 by default)."""
    data = await call_graph_api("users")
    return [UserResponse(**user) for user in data.get("value", [])]


@router.get("/users/top/{count}", response_model=List[UserResponse])
async def get_users_top(count: int):
    """Fetch top N users."""
    if count > 999:
        raise HTTPException(status_code=400, detail="Maximum count is 999")

    data = await call_graph_api(f"users?$top={count}")
    return [UserResponse(**user) for user in data.get("value", [])]


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: str):
    """Fetch a specific user by ID or UPN."""
    data = await call_graph_api(f"users/{user_id}")
    if "value" in data:
        data = data["value"]
    return UserResponse(**data)



@router.get("/users/{user_id}/manager", response_model=UserResponse)
async def get_user_manager(user_id: str):
    """Get a user's manager."""
    data = await call_graph_api(f"users/{user_id}/manager")
    return UserResponse(**data)


@router.get("/users/{user_id}/direct-reports", response_model=List[UserResponse])
async def get_user_direct_reports(user_id: str):
    """Get a user's direct reports."""
    data = await call_graph_api(f"users/{user_id}/directReports")
    return [UserResponse(**user) for user in data.get("value", [])]


@router.post("/users/search", response_model=List[UserResponse])
async def search_users(search_data: SearchQuery):
    """
    Search for users by displayName or mail.
    Expected body: { "query": "search_term" }
    """
    search_term = search_data.query.strip()
    if not search_term:
        raise HTTPException(status_code=400, detail="Query parameter cannot be empty")

    escaped_term = escape_odata_string(search_term)
    filter_query = (
        f"users?$filter=startswith(displayName,'{escaped_term}') "
        f"or startswith(mail,'{escaped_term}')"
    )

    data = await call_graph_api(filter_query)
    return [UserResponse(**user) for user in data.get("value", [])]


@router.post("/users/filter", response_model=List[UserResponse])
async def filter_users(filter_data: UserFilter):
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
        raise HTTPException(
            status_code=400, detail="At least one filter criteria must be provided"
        )

    filter_expr = " and ".join(filters)  # Use AND for multiple criteria
    filter_query = f"users?$filter={filter_expr}"

    data = await call_graph_api(filter_query)
    return [UserResponse(**user) for user in data.get("value", [])]


# ----------------------------
# Groups
# ----------------------------
@router.get("/groups", response_model=List[GroupResponse])
async def get_groups():
    """Fetch all groups."""
    data = await call_graph_api("groups")
    return [GroupResponse(**group) for group in data.get("value", [])]


@router.get("/groups/top/{count}", response_model=List[GroupResponse])
async def get_groups_top(count: int):
    """Fetch top N groups."""
    if count > 999:
        raise HTTPException(status_code=400, detail="Maximum count is 999")

    data = await call_graph_api(f"groups?$top={count}")
    return [GroupResponse(**group) for group in data.get("value", [])]


@router.get("/groups/{group_id}", response_model=GroupResponse)
async def get_group(group_id: str):
    """Fetch a specific group by ID."""
    data = await call_graph_api(f"groups/{group_id}")
    return GroupResponse(**data)


@router.get("/groups/{group_id}/members", response_model=List[UserResponse])
async def get_group_members(group_id: str):
    """Fetch members of a specific group."""
    data = await call_graph_api(f"groups/{group_id}/members")
    return [UserResponse(**user) for user in data.get("value", [])]
