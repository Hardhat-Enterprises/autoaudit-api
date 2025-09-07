from typing import List
import aiohttp
from app.core.config import Settings
from app.models.compliance_model import (
    MFASettings,
    ConditionalAccessPolicy,
    ExternalSharingSettings,
    AdminRoleAssignment
)
from app.utils.logger import get_logger

logger = get_logger(__name__)

class GraphService:
    def __init__(self):
        self.settings = Settings()
        self.base_url = self.settings.GRAPH_API_BASE_URL

    async def _make_request(self, token: str, endpoint: str) -> dict:
        headers = {"Authorization": f"Bearer {token}"}
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/{endpoint}", headers=headers) as response:
                response.raise_for_status()
                return await response.json()

    async def get_mfa_settings(self, token: str) -> MFASettings:
        try:
            data = await self._make_request(token, "policies/authenticationMethodsPolicy")
            return MFASettings(**data)
        except Exception as e:
            logger.error(f"Error fetching MFA settings: {str(e)}")
            raise

    async def get_conditional_access_policies(self, token: str) -> List[ConditionalAccessPolicy]:
        try:
            data = await self._make_request(token, "identity/conditionalAccess/policies")
            return [ConditionalAccessPolicy(**policy) for policy in data["value"]]
        except Exception as e:
            logger.error(f"Error fetching conditional access policies: {str(e)}")
            raise

    async def get_external_sharing_settings(self, token: str) -> ExternalSharingSettings:
        try:
            data = await self._make_request(token, "admin/sharepoint/settings")
            return ExternalSharingSettings(**data)
        except Exception as e:
            logger.error(f"Error fetching external sharing settings: {str(e)}")
            raise

    async def get_admin_role_assignments(self, token: str) -> List[AdminRoleAssignment]:
        try:
            data = await self._make_request(token, "directoryRoles?$expand=members")
            assignments = []
            for role in data["value"]:
                for member in role["members"]:
                    assignment = AdminRoleAssignment(
                        role_id=role["id"],
                        role_name=role["displayName"],
                        principal_id=member["id"],
                        principal_display_name=member["displayName"],
                        assigned_datetime=member.get("assignedDateTime")
                    )
                    assignments.append(assignment)
            return assignments
        except Exception as e:
            logger.error(f"Error fetching admin role assignments: {str(e)}")
            raise