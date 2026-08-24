"""Core application exceptions."""


class AppException(Exception):
    """Base application exception."""

    def __init__(self, message: str, code: str = "app_error") -> None:
        self.message = message
        self.code = code
        super().__init__(message)
