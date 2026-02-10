from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    environment: str = "development"
    debug: bool = False

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # Database
    database_url: str

    # Redis
    redis_url: str

    # Logging
    log_level: str = "INFO"

    # Secrets and API keys (required - no defaults)
    supabase_url: str
    openai_api_key: str
    google_api_key: str
    supabase_service_role_key: str
    client_url: str
    stripe_secret_key: str
    stripe_price_id_pro: str
    stripe_price_id_business: str
    stripe_webhook_secret: str

    @model_validator(mode="after")
    def validate_required_fields(self) -> "Settings":
        """Validate that required fields are not empty strings."""
        required_fields = [
            "supabase_url",
            "openai_api_key",
            "google_api_key",
            "supabase_service_role_key",
            "client_url",
            "stripe_secret_key",
            "stripe_price_id_pro",
            "stripe_price_id_business",
            "stripe_webhook_secret",
            "database_url",
            "redis_url",
        ]

        missing_fields = []
        for field in required_fields:
            value = getattr(self, field)
            if not value or value.strip() == "":
                missing_fields.append(field.upper())

        if missing_fields:
            raise ValueError(
                f"Required environment variables are missing or empty: {', '.join(missing_fields)}"
            )

        return self

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


# Mypy doesn't understand that BaseSettings loads from env vars at runtime.
# The Pydantic plugin should handle this, but it's inconsistent, so we need the ignore.
settings = Settings()  # type: ignore
