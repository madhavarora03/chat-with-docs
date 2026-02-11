from app.exceptions.base import AppError


class InvalidCredentialsError(AppError):
    def __init__(self, message: str = "Invalid credentials"):
        super().__init__(message)


class InvalidTokenError(AppError):
    def __init__(self, message: str = "Invalid or expired token"):
        super().__init__(message)


class DuplicateEmailError(AppError):
    def __init__(self, message: str = "Email already registered"):
        super().__init__(message)


class UserNotFoundError(AppError):
    def __init__(self, message: str = "User not found"):
        super().__init__(message)
