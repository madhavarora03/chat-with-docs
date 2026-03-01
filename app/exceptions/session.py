from app.exceptions.base import AppError


class SessionNotFoundError(AppError):
    def __init__(self, message: str = "Session not found"):
        super().__init__(message)
