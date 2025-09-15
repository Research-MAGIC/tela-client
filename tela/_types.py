from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    List,
    Union,
    Optional,
    TypeVar,
    Protocol,
    runtime_checkable,
)
from typing_extensions import TypeAlias, TypedDict, Literal, Required
from dataclasses import dataclass
import httpx

if TYPE_CHECKING:
    from httpx._types import ProxiesTypes

__all__ = [
    "NOT_GIVEN",
    "NotGiven",
    "Headers",
    "Query",
    "Body",
    "ResponseT",
    "RequestOptions",
]

# Sentinel value for optional parameters
class NotGiven:
    """Sentinel value for parameters that should not be sent"""
    def __bool__(self) -> bool:
        return False
    
    def __repr__(self) -> str:
        return "NOT_GIVEN"

NOT_GIVEN = NotGiven()

# Type aliases
Headers: TypeAlias = Union[Dict[str, str], NotGiven]
Query: TypeAlias = Union[Dict[str, object], NotGiven]
Body: TypeAlias = Union[object, NotGiven]
ResponseT = TypeVar("ResponseT")

@dataclass
class RequestOptions:
    """Options for HTTP requests"""
    headers: Headers | None = None
    params: Query | None = None
    json_data: Body | None = None
    timeout: float | httpx.Timeout | NotGiven = NOT_GIVEN
    files: Any | None = None

# Useful type guards
def is_given(value: object) -> bool:
    """Check if a value is not NOT_GIVEN"""
    return not isinstance(value, NotGiven)

# Message types
class ChatCompletionMessageParam(TypedDict, total=False):
    """Parameters for a chat message"""
    role: Required[Literal["system", "user", "assistant", "tool"]]
    content: Required[Union[str, List[Dict[str, Any]]]]
    name: str
    tool_calls: List[Dict[str, Any]]
    tool_call_id: str

class ChatCompletionToolParam(TypedDict):
    """Parameters for a tool/function"""
    type: Literal["function"]
    function: ChatCompletionFunctionParam

class ChatCompletionFunctionParam(TypedDict):
    """Function definition"""
    name: Required[str]
    description: str
    parameters: Required[Dict[str, Any]]

class ResponseFormat(TypedDict):
    """Response format specification"""
    type: Literal["text", "json_object"]

# Streaming types
@runtime_checkable
class Stream(Protocol[ResponseT]):
    """Protocol for streaming responses"""
    
    def __iter__(self) -> Stream[ResponseT]:
        ...
    
    def __next__(self) -> ResponseT:
        ...

@runtime_checkable
class AsyncStream(Protocol[ResponseT]):
    """Protocol for async streaming responses"""
    
    def __aiter__(self) -> AsyncStream[ResponseT]:
        ...
    
    async def __anext__(self) -> ResponseT:
        ...