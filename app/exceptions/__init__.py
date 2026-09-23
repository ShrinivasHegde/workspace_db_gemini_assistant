class AppError(Exception):
    """Expected application error that can be presented safely to users."""


class DatabaseConnectionError(AppError):
    pass


class GeminiServiceError(AppError):
    pass
