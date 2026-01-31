from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import ConfigDict


class Settings(BaseSettings):
    # App metadata
    APP_TITLE: str = "Check Karo Baabeyo!"
    APP_DESCRIPTION: str = "This is a description"
    APP_VERSION: str = "1.0.0"

    # Runtime defaults (override via .env)
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    ENV: str = "dev"

    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=True,
    )


@lru_cache()
def get_settings() -> Settings:
    return Settings()
