from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    import httpx

__all__ = [
    "TelaError",
    "APIError",
    "APIConnectionError",
    "APIStatusError",
    "APITimeoutError",
    "AuthenticationError",
    "BadRequestError",
    "ConflictError",
    "InternalServerError",
    "NotFoundError",
    "PermissionDeniedError",
    "RateLimitError",
    "UnprocessableEntityError",
]


class TelaError(Exception):
    """Base exception for all Tela errors"""
    pass


class APIError(TelaError):
    """Base class for API errors"""
    
    def __init__(
        self,
        message: str,
        *,
        response: Optional[httpx.Response] = None,
        body: Optional[object] = None,
    ) -> None:
        super().__init__(message)
        self.response = response
        self.body = body
        self.message = message
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(message={self.message!r})"


class APIConnectionError(APIError):
    """Error connecting to the API"""
    pass


class APITimeoutError(APIConnectionError):
    """Request timed out"""
    pass


class APIStatusError(APIError):
    """API returned an error status code"""
    
    def __init__(
        self,
        message: str,
        *,
        response: httpx.Response,
        body: Optional[object] = None,
    ) -> None:
        super().__init__(message, response=response, body=body)
        self.status_code = response.status_code


class BadRequestError(APIStatusError):
    """400 Bad Request"""
    pass


class AuthenticationError(APIError):
    """401 Unauthorized - Invalid authentication"""
    
    def __init__(self, message: str = "Invalid authentication credentials", **kwargs: Any) -> None:
        # Handle cases where response is not required (e.g., missing credentials)
        if 'response' not in kwargs:
            super(APIError, self).__init__(message)
            self.message = message
            self.response = kwargs.get('response')
            self.body = kwargs.get('body')
        else:
            super().__init__(message, **kwargs)


class PermissionDeniedError(APIStatusError):
    """403 Forbidden - Permission denied"""
    pass


class NotFoundError(APIStatusError):
    """404 Not Found"""
    pass


class ConflictError(APIStatusError):
    """409 Conflict"""
    pass


class UnprocessableEntityError(APIStatusError):
    """422 Unprocessable Entity"""
    pass


class RateLimitError(APIStatusError):
    """429 Too Many Requests - Rate limit exceeded"""
    pass


class InternalServerError(APIStatusError):
    """500+ Internal Server Error"""
    pass