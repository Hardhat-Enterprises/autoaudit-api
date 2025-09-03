from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.services.graph_service import GraphService

router = APIRouter()
graph_service = GraphService()  

class UsersRequest(BaseModel):
    token: str
    top: Optional[int] = None

class MeRequest(BaseModel):
    token: str

@router.post("/graph/users")
async def graph_users(req: UsersRequest):
    try:
        result = await graph_service.list_users(req.token, req.top)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Unhandled exception: {e}")
    if "error" in result:
        raise HTTPException(status_code=502, detail=result["error"])
    return result

@router.post("/graph/me")
async def graph_me(req: MeRequest):
    try:
        result = await graph_service.get_me(req.token)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Unhandled exception: {e}")
    if "error" in result:
        raise HTTPException(status_code=502, detail=result["error"])
    return result
