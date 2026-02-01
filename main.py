import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request

from app.core.config import get_settings
from app.utils.logger import setup_logging, get_logger, get_uvicorn_log_config

# Initialize logging FIRST - before any other operations
# This ensures all loggers (app + uvicorn) use our config
setup_logging()

settings = get_settings()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application startup complete")
    yield
    logger.info("Application shutdown complete")


app = FastAPI(
    title=settings.APP_TITLE,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)


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


@app.get("/")
def root():
    return {"message": "Hello World"}


if __name__ == "__main__":
    import uvicorn

    logger.info(f"Starting server on {settings.HOST}:{settings.PORT}")

    uvicorn.run(
        app="main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.ENV == "dev",
        log_config=get_uvicorn_log_config(),
    )
