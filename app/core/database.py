import logging
from typing import Annotated

from fastapi import Depends
from sqlalchemy import text
from sqlmodel import Session, create_engine
from tenacity import retry, stop_after_attempt, wait_exponential, before_sleep_log

from app.core.config import get_settings
from app.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()

engine = create_engine(settings.database_url, echo=False)


def get_session():
    with Session(engine) as session:
        yield session


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=2, max=10),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)
def ping_db() -> bool:
    """
    Check database connectivity by executing a simple query.

    Retries up to 3 times with exponential backoff (2s, 4s, 8s).

    Returns:
        True if connection is successful, raises exception otherwise.
    """
    with Session(engine) as session:
        session.exec(text("SELECT 1"))
    logger.info("Database connection verified successfully")
    return True


def dispose_engine() -> None:
    """Dispose of the database engine and log the action."""
    logger.info("Disposing database engine")
    engine.dispose()
    logger.info("Database engine disposed successfully")


SessionDep = Annotated[Session, Depends(get_session)]
