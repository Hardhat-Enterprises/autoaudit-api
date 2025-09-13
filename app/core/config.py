from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # Application Settings
    APP_NAME: str = Field(default="AutoAudit API", description="Application name")
    DEBUG: bool = Field(default=False, description="Debug mode")
    VERSION: str = Field(default="0.1.0", description="Application version")

    # Azure AD Configuration
    AZURE_CLIENT_ID: str = Field(
        description="Azure AD Client ID for application registration"
    )
    AZURE_CLIENT_SECRET: str = Field(
        description="Azure AD Client Secret for authentication"
    )
    AZURE_TENANT_ID: str = Field(description="Azure AD Tenant ID for authentication")

    # Logging
    LOG_FORMAT: str = Field(default="json", description="Log format: json, text")

    # API settings
    ALLOWED_ORIGINS: List[str] = Field(
        default=["*"], description="Allowed CORS origins"
    )
    ALLOWED_HOSTS: List[str] = Field(default=["*"], description="Allowed hosts")
    API_PREFIX: str = Field(default="/api/v1", description="API prefix")

    # Microsoft Graph API
    GRAPH_API_BASE_URL: str = Field(
        default="https://graph.microsoft.com/v1.0",
        description="Base URL for Microsoft Graph API",
    )

    #Dev Proxy (Local Testing Proxy for now)
    DEV_PROXY_URL: Optional[str] = Field(
        default=None,
        description="Dev Proxy URL for local testing (e.g., http://localhost:8000)"
    )

    class Config:
        """Pydantic configuration."""

        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = Settings()
