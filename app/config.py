"""Application configuration via pydantic-settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment-based configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    DATABASE_URL: str = "postgresql+asyncpg://moonbattery:moonbattery@localhost:5432/moonbattery"
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"


settings = Settings()
