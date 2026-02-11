class AppError(Exception):
    """Base exception for application domain errors."""

    def __init__(self, message: str = "An unexpected error occurred"):
        self.message = message
        super().__init__(self.message)
