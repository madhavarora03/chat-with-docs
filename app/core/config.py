from functools import cache

from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL


class Settings(BaseSettings):
    # App metadata
    APP_TITLE: str = "Chat With Docs API"
    APP_DESCRIPTION: str = (
        "API for chatting with uploaded documents using "
        "session-isolated RAG and vector search."
    )
    APP_VERSION: str = "1.0.0"

    # Runtime defaults (override via .env)
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    ENV: str = "dev"

    # Logging configuration
    LOG_LEVEL: str = "INFO"
    LOG_FILE_ENABLED: bool = False
    LOG_FILE_PATH: str = "logs/app.log"

    # Database settings
    POSTGRES_HOST: str
    POSTGRES_DB: str
    POSTGRES_PORT: int
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str

    # JWT settings (expiry in minutes)
    JWT_ACCESS_SECRET: str
    JWT_ACCESS_EXPIRES_MINUTES: int
    JWT_ALGORITHM: str = "HS256"
    JWT_ISSUER: str | None = None

    # Refresh token settings (opaque tokens stored hashed in DB)
    REFRESH_TOKEN_BYTES: int = 32
    REFRESH_TOKEN_EXPIRES_DAYS: int = 10

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

    @property
    def is_dev(self) -> bool:
        """Check if running in development environment."""
        return self.ENV == "dev"

    @property
    def database_url(self) -> URL:
        """Database connection URL"""
        return URL.create(
            drivername="postgresql+psycopg2",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_HOST,
            port=self.POSTGRES_PORT,
            database=self.POSTGRES_DB,
        )


@cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
