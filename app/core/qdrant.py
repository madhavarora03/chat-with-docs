import logging
from typing import Annotated

from fastapi import Depends
from qdrant_client import QdrantClient
from tenacity import before_sleep_log, retry, stop_after_attempt, wait_exponential

from app.core.config import get_settings
from app.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()

_client: QdrantClient | None = None


def get_qdrant_client() -> QdrantClient:
    global _client
    if _client is None:
        _client = QdrantClient(url=settings.QDRANT_URL)
    return _client


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=2, max=10),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)
def ping_qdrant() -> bool:
    """
    Check Qdrant connectivity by fetching collections list.

    Retries up to 3 times with exponential backoff (2s, 4s, 8s).

    Returns:
        True if connection is successful, raises exception otherwise.
    """
    get_qdrant_client().get_collections()
    logger.info("Qdrant connection verified successfully")
    return True


def close_qdrant_client() -> None:
    """Close the Qdrant client connection."""
    global _client
    if _client is not None:
        _client.close()
        _client = None
        logger.info("Qdrant client closed")


QdrantDep = Annotated[QdrantClient, Depends(get_qdrant_client)]
