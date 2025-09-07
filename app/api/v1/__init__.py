from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.compliance import router as compliance_router


router = APIRouter()

# Include individual routers
router.include_router(auth_router)
router.include_router(compliance_router)
