from fastapi import APIRouter, Depends, HTTPException
from app.core.security import get_token
from app.services.graph_service import GraphService
from app.models.compliance_model import (
    MFASettings,
    ConditionalAccessPolicy,
    ExternalSharingSettings,
    AdminRoleAssignment
)
from app.utils.logger import get_logger

logger = get_logger(__name__)

#Router
router = APIRouter(prefix="/compliance/security", tags=["Security Compliance"]) 

graph_service = GraphService()

#MFA Settings Endpoint
@router.get("/mfa-settings", 
    response_model=MFASettings,
    summary="Get MFA Settings",
    description="Retrieve Multi-Factor Authentication configuration settings")
async def get_mfa_settings(token: str = Depends(get_token)):
    try:
        return await graph_service.get_mfa_settings(token)
    except Exception as e:
        logger.error(f"MFA settings endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve MFA settings")

#Conditional Access Policies Endpoint
@router.get("/conditional-access", 
    response_model=list[ConditionalAccessPolicy],
    summary="Get Conditional Access Policies",
    description="Retrieve all conditional access policies")
async def get_conditional_access(token: str = Depends(get_token)):
    try:
        return await graph_service.get_conditional_access_policies(token)
    except Exception as e:
        logger.error(f"Conditional access endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve conditional access policies")

#External Sharing Settings Endpoint
@router.get("/external-sharing", 
    response_model=ExternalSharingSettings,
    summary="Get External Sharing Settings",
    description="Retrieve external sharing configuration")
async def get_external_sharing(token: str = Depends(get_token)):
    try:
        return await graph_service.get_external_sharing_settings(token)
    except Exception as e:
        logger.error(f"External sharing endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve external sharing settings")

#Admin Role Assignments Endpoint
@router.get("/admin-roles", 
    response_model=list[AdminRoleAssignment],
    summary="Get Admin Role Assignments",
    description="Retrieve all admin role assignments")
async def get_admin_roles(token: str = Depends(get_token)):
    try:
        return await graph_service.get_admin_role_assignments(token)
    except Exception as e:
        logger.error(f"Admin roles endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve admin role assignments")