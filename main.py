import uvicorn

from app.core.config import get_settings
from app.utils.logger import get_logger, get_uvicorn_log_config

settings = get_settings()
logger = get_logger(__name__)

if __name__ == "__main__":
    logger.info(f"Starting server on {settings.HOST}:{settings.PORT}")

    uvicorn.run(
        app="app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.is_dev,
        log_config=get_uvicorn_log_config(),
    )
