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
from .types.chats import (
    Chat as ServerChat,
    ChatList,
    ChatPaginatedResponse,
)
from ._chats import (
    Chats,
    AsyncChats,
)
from ._audio import (
    Audio,
    AsyncAudio,
    Transcriptions,
    AsyncTranscriptions,
)
from .types.audio import (
    TranscriptionResponse,
    TranscriptionSegment,
    TranscriptionRequest,
    VoiceListResponse,
    TTSResponse,
    Voice,
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

    # Chat Management
    "ServerChat",
    "ChatList",
    "ChatPaginatedResponse",
    "Chats",
    "AsyncChats",

    # Audio
    "Audio",
    "AsyncAudio",
    "Transcriptions",
    "AsyncTranscriptions",
    "TranscriptionResponse",
    "TranscriptionSegment",
    "TranscriptionRequest",
    "VoiceListResponse",
    "TTSResponse",
    "Voice",
    
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