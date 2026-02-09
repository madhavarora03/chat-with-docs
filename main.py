import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request

from app.api.v1 import api_router
from app.core.config import get_settings
from app.core.database import dispose_engine, ping_db
from app.utils.logger import get_logger, get_uvicorn_log_config, setup_logging

# Initialize logging FIRST - before any other operations
# This ensures all loggers (app + uvicorn) use our config
setup_logging()

settings = get_settings()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: verify database connection
    ping_db()
    logger.info("Application startup complete")

    yield

    # Shutdown: dispose database engine
    dispose_engine()
    logger.info("Application shutdown complete")


app = FastAPI(
    title=settings.APP_TITLE,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs" if settings.is_dev else None,
    redoc_url="/redoc" if settings.is_dev else None,
    openapi_url="/openapi.json" if settings.is_dev else None,
)
app.include_router(api_router, prefix="/api/v1")


@app.middleware("http")
async def log_request_time(request: Request, call_next):
    """Middleware to log the processing time for each request."""
    start_time = time.perf_counter()

    response = await call_next(request)

    process_time_ms = (time.perf_counter() - start_time) * 1000
    logger.info(
        f"{request.method} {request.url.path} - {response.status_code} - {process_time_ms:.2f}ms"
    )

    # Optionally add timing header for debugging
    response.headers["X-Process-Time"] = f"{process_time_ms:.2f}ms"

    return response


if __name__ == "__main__":
    import uvicorn

    logger.info(f"Starting server on {settings.HOST}:{settings.PORT}")

    uvicorn.run(
        app="main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.is_dev,
        log_config=get_uvicorn_log_config(),
    )
