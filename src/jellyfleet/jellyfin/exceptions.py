class JellyfinError(Exception):
    pass


class AuthenticationError(JellyfinError):
    pass


class RateLimitError(JellyfinError):
    pass


class ValidationError(JellyfinError):
    pass


class NetworkError(JellyfinError):
    pass


class ApiError(JellyfinError):
    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code
