from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings
import json

class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # Application Settings
    APP_NAME: str = Field(default="AutoAudit API", description="Application name")
    DEBUG: bool = Field(default=False, description="Debug mode")
    VERSION: str = Field(default="0.1.0", description="Application version")

    # Azure AD Configuration
    AZURE_CLIENT_ID: Optional[str] = Field(
        default=None, description="Azure AD Client ID for application registration"
    )
    AZURE_CLIENT_SECRET: Optional[str] = Field(
        default=None, description="Azure AD Client Secret for authentication"
    )
    AZURE_TENANT_ID: Optional[str] = Field(
        default=None, description="Azure AD Tenant ID for authentication"
    )


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

    # Database (needed by health checks)
    DATABASE_URL: Optional[str] = Field(
        default=None,
        description="Database connection string; if unset, DB health check is skipped",
    )

    # Health timeouts (seconds)
    HEALTH_TIMEOUT_SECONDS: float = Field(
        default=5.0, description="HTTP timeout used by health checks"
    )
    # Updated validators (DEBUG, ALLOWED_ORIGINS, API_PREFIX, HEALTH_TIMEOUT_SECONDS, DATABASE_URL)
    # --- Validators to be robust with .env inputs ---
    @field_validator("DEBUG", mode="before")
    @classmethod
    def _parse_bool(cls, v):
        if isinstance(v, bool):
            return v
        return str(v).strip().lower() in {"1", "true", "yes", "on"}

    @field_validator("ALLOWED_ORIGINS", "ALLOWED_HOSTS", mode="before")
    @classmethod
    def _parse_list(cls, v):
        if isinstance(v, list):
            return v
        s = str(v).strip()
        if not s:
            return []
        # JSON array style: ["*"] or ["http://a","http://b"]
        if s.startswith("["):
            try:
                return json.loads(s)
            except Exception:
                pass
        # CSV style: http://a, http://b
        return [item.strip() for item in s.split(",") if item.strip()]
    

    @field_validator("API_PREFIX")
    @classmethod
    def _ensure_leading_slash(cls, v: str) -> str:
        return v if v.startswith("/") else f"/{v}"

    @field_validator("HEALTH_TIMEOUT_SECONDS", mode="before")
    @classmethod
    def _parse_timeout(cls, v):
        # Accept "5", "5.0", etc.
        try:
            f = float(v)
        except Exception:
            raise ValueError("HEALTH_TIMEOUT_SECONDS must be a number")
        if f <= 0:
            raise ValueError("HEALTH_TIMEOUT_SECONDS must be > 0")
        return f

    @field_validator("DATABASE_URL")
    @classmethod
    def _db_url_if_set(cls, v: Optional[str]) -> Optional[str]:
        # Allow None (so local dev can boot). If set, sanity check.
        if v and "://" not in v:
            raise ValueError("DATABASE_URL looks invalid (missing '://')")
        return v

    
    class Config:
        """Pydantic configuration."""

        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = Settings()
