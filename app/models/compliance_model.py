from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class MFASettings(BaseModel):
    enabled: bool
    enforced: bool
    excluded_users: List[str]
    methods_allowed: List[str]

class ConditionalAccessPolicy(BaseModel):
    id: str
    display_name: str
    state: str
    conditions: dict
    grant_controls: dict
    created_datetime: datetime
    modified_datetime: datetime

class ExternalSharingSettings(BaseModel):
    sharing_capability: str
    anonymous_link_enabled: bool
    require_external_sharing_expiration: bool
    expiration_days: Optional[int]
    domains_allowed: List[str]

class AdminRoleAssignment(BaseModel):
    role_id: str
    role_name: str
    principal_id: str
    principal_display_name: str
    assigned_datetime: datetime