from . import types
from ._client import Tela, AsyncTela, Client, AsyncClient
from ._version import __version__
from ._exceptions import (
    TelaError,
    APIError,
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AuthenticationError,
    BadRequestError,
    ConflictError,
    InternalServerError,
    NotFoundError,
    PermissionDeniedError,
    RateLimitError,
    UnprocessableEntityError,
)
from ._history import (
    ConversationHistory,
    HistoryManager,
)
from .types.models import (
    Model,
    ModelList, 
    ModelCapabilities,
    UsageInfo,
    ParameterInfo,
)

__all__ = [
    # Main clients
    "types",
    "Tela",
    "AsyncTela", 
    "Client",
    "AsyncClient",
    
    # History management
    "ConversationHistory",
    "HistoryManager",
    
    # Model information
    "Model",
    "ModelList",
    "ModelCapabilities", 
    "UsageInfo",
    "ParameterInfo",
    
    # Exceptions
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
    
    # Version
    "__version__",
]