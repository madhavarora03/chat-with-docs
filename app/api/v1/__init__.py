from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.chat_session import router as chat_session_router
from app.api.v1.health_check import router as health_check_router

api_router = APIRouter()
api_router.include_router(health_check_router)
api_router.include_router(auth_router)
api_router.include_router(chat_session_router)
