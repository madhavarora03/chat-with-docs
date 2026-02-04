from functools import cache
from pydantic_settings import BaseSettings
from pydantic import ConfigDict


class Settings(BaseSettings):
    # App metadata
    APP_TITLE: str = "Chat Karo Baabeyo!"
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

    model_config = ConfigDict(env_file=".env", case_sensitive=True)

    @property
    def get_database_url(self) -> str:
        return (
            f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )


@cache
def get_settings() -> Settings:
    return Settings()
