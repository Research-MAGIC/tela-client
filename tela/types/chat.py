from __future__ import annotations

import json
from typing import (
    TYPE_CHECKING,
    Any,
    AsyncIterator,
    Dict,
    Iterator,
    List,
    Mapping,
    Optional,
    Union,
    cast,
)

import httpx
from pydantic import BaseModel

from .._types import NOT_GIVEN, NotGiven
from .._exceptions import APIError
from .._streaming import Stream, AsyncStream
from .._history import ConversationHistory

if TYPE_CHECKING:
    from .._client import Tela, AsyncTela


class ChatCompletionMessage(BaseModel):
    """A message in a chat completion"""
    role: str
    content: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    function_call: Optional[Dict[str, Any]] = None
    name: Optional[str] = None
    
    model_config = {"extra": "allow"}


class ChatCompletionChoice(BaseModel):
    """A choice in a chat completion response"""
    index: int
    message: ChatCompletionMessage
    finish_reason: Optional[str] = None
    logprobs: Optional[Dict[str, Any]] = None
    
    model_config = {"extra": "allow"}


class ChatCompletionUsage(BaseModel):
    """Usage statistics for a chat completion"""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    
    model_config = {"extra": "allow"}


class ChatCompletion(BaseModel):
    """Response from a chat completion API call"""
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[ChatCompletionChoice]
    usage: Optional[ChatCompletionUsage] = None
    system_fingerprint: Optional[str] = None
    
    model_config = {"extra": "allow"}


class ChatCompletionChunk(BaseModel):
    """A chunk from a streaming chat completion"""
    id: str
    object: str = "chat.completion.chunk"
    created: int
    model: str
    choices: List[Dict[str, Any]]
    system_fingerprint: Optional[str] = None
    
    model_config = {"extra": "allow"}


class Completions:
    """
    Synchronous chat completions with history support
    
    Compatible with OpenAI SDK patterns while adding conversation history
    """
    
    def __init__(self, client: Tela, enable_history: bool = True) -> None:
        self._client = client
        self._enable_history = enable_history
    
    def create(
        self,
        *,
        messages: List[Dict[str, Any]],
        model: str = "wizard",
        conversation_id: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        frequency_penalty: Optional[float] = None,
        presence_penalty: Optional[float] = None,
        stop: Union[str, List[str], None] = None,
        stream: bool = False,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[Union[str, Dict[str, Any]]] = None,
        response_format: Optional[Dict[str, Any]] = None,
        seed: Optional[int] = None,
        user: Optional[str] = None,
        timeout: Union[float, httpx.Timeout, None, NotGiven] = NOT_GIVEN,
        extra_headers: Optional[Mapping[str, str]] = None,
        extra_query: Optional[Mapping[str, object]] = None,
        **kwargs: Any,
    ) -> Union[ChatCompletion, Stream[ChatCompletionChunk]]:
        """
        Create a chat completion
        
        Args:
            messages: List of messages in the conversation
            model: Model to use for completion
            conversation_id: Optional conversation ID for history tracking
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            top_p: Top-p sampling parameter
            frequency_penalty: Frequency penalty
            presence_penalty: Presence penalty
            stop: Stop sequences
            stream: Whether to stream the response
            tools: Available tools/functions
            tool_choice: Tool choice strategy
            response_format: Response format specification
            seed: Random seed for reproducibility
            user: User identifier
            timeout: Request timeout
            extra_headers: Additional headers
            extra_query: Additional query parameters
            **kwargs: Additional parameters
            
        Returns:
            ChatCompletion or Stream[ChatCompletionChunk]
        """
        # Prepare request data
        data = {
            "model": model,
            "messages": messages,
            "stream": stream,
        }
        
        # Add optional parameters
        if temperature is not None:
            data["temperature"] = temperature
        if max_tokens is not None:
            data["max_tokens"] = max_tokens
        if top_p is not None:
            data["top_p"] = top_p
        if frequency_penalty is not None:
            data["frequency_penalty"] = frequency_penalty
        if presence_penalty is not None:
            data["presence_penalty"] = presence_penalty
        if stop is not None:
            data["stop"] = stop
        if tools is not None:
            data["tools"] = tools
        if tool_choice is not None:
            data["tool_choice"] = tool_choice
        if response_format is not None:
            data["response_format"] = response_format
        if seed is not None:
            data["seed"] = seed
        if user is not None:
            data["user"] = user
        
        # Add any additional kwargs
        data.update(kwargs)
        
        # Prepare headers
        headers = {}
        if extra_headers:
            headers.update(extra_headers)
        
        # Prepare query parameters
        params = {}
        if extra_query:
            params.update(extra_query)
        
        # Handle conversation history
        conversation = None
        if self._enable_history and conversation_id:
            conversation = self._client.history.get_conversation(conversation_id)
            if not conversation:
                conversation = self._client.history.create_conversation(conversation_id)
        
        # Make the request
        try:
            from .._types import RequestOptions
            
            options = RequestOptions(
                headers=headers,
                params=params,
                timeout=timeout
            )
            
            if stream:
                # Import here to avoid circular imports
                from .._streaming import Stream
                
                # Request streaming response
                response = self._client.post(
                    "/chat/completions",
                    body=data,
                    options=options,
                    stream=stream,
                    stream_cls=Stream,
                )
                
                stream_response = response
                
                # Add history tracking to stream if enabled
                if conversation and self._enable_history:
                    # Add user messages to history
                    for msg in messages:
                        if msg.get("role") in ("user", "system"):
                            conversation.add_message(
                                role=msg["role"],
                                content=str(msg.get("content", "")),
                                metadata={"model": model, "stream": True}
                            )
                
                return stream_response
            else:
                # Request non-streaming response
                response = self._client.post(
                    "/chat/completions",
                    body=data,
                    options=options,
                    stream=stream,
                )
                
                # Parse non-streaming response
                completion = ChatCompletion.model_validate(response)
                
                # Add to conversation history if enabled
                if conversation and self._enable_history:
                    # Add user messages
                    for msg in messages:
                        if msg.get("role") in ("user", "system"):
                            conversation.add_message(
                                role=msg["role"],
                                content=str(msg.get("content", "")),
                                metadata={"model": model}
                            )
                    
                    # Add assistant response
                    if completion.choices:
                        assistant_message = completion.choices[0].message
                        conversation.add_message(
                            role="assistant",
                            content=assistant_message.content or "",
                            metadata={
                                "model": model,
                                "finish_reason": completion.choices[0].finish_reason,
                                "usage": completion.usage.model_dump() if completion.usage else None
                            }
                        )
                
                return completion
                
        except Exception as e:
            # Log error to conversation if available
            if conversation and self._enable_history:
                conversation.add_message(
                    role="system",
                    content=f"Error: {str(e)}",
                    metadata={"error": True, "model": model}
                )
            raise


class Chat:
    """
    Synchronous chat interface with completions
    """
    
    def __init__(self, client: Tela, enable_history: bool = True) -> None:
        self.completions = Completions(client, enable_history=enable_history)


class AsyncCompletions:
    """
    Asynchronous chat completions with history support
    """
    
    def __init__(self, client: AsyncTela, enable_history: bool = True) -> None:
        self._client = client
        self._enable_history = enable_history
    
    async def create(
        self,
        *,
        messages: List[Dict[str, Any]],
        model: str = "wizard",
        conversation_id: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        frequency_penalty: Optional[float] = None,
        presence_penalty: Optional[float] = None,
        stop: Union[str, List[str], None] = None,
        stream: bool = False,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[Union[str, Dict[str, Any]]] = None,
        response_format: Optional[Dict[str, Any]] = None,
        seed: Optional[int] = None,
        user: Optional[str] = None,
        timeout: Union[float, httpx.Timeout, None, NotGiven] = NOT_GIVEN,
        extra_headers: Optional[Mapping[str, str]] = None,
        extra_query: Optional[Mapping[str, object]] = None,
        **kwargs: Any,
    ) -> Union[ChatCompletion, AsyncStream[ChatCompletionChunk]]:
        """
        Async version of create method
        
        Args: Same as synchronous version
        Returns: ChatCompletion or AsyncStream[ChatCompletionChunk]
        """
        # Prepare request data (same as sync version)
        data = {
            "model": model,
            "messages": messages,
            "stream": stream,
        }
        
        # Add optional parameters
        if temperature is not None:
            data["temperature"] = temperature
        if max_tokens is not None:
            data["max_tokens"] = max_tokens
        if top_p is not None:
            data["top_p"] = top_p
        if frequency_penalty is not None:
            data["frequency_penalty"] = frequency_penalty
        if presence_penalty is not None:
            data["presence_penalty"] = presence_penalty
        if stop is not None:
            data["stop"] = stop
        if tools is not None:
            data["tools"] = tools
        if tool_choice is not None:
            data["tool_choice"] = tool_choice
        if response_format is not None:
            data["response_format"] = response_format
        if seed is not None:
            data["seed"] = seed
        if user is not None:
            data["user"] = user
        
        data.update(kwargs)
        
        headers = {}
        if extra_headers:
            headers.update(extra_headers)
        
        params = {}
        if extra_query:
            params.update(extra_query)
        
        # Handle conversation history
        conversation = None
        if self._enable_history and conversation_id:
            conversation = self._client.history.get_conversation(conversation_id)
            if not conversation:
                conversation = self._client.history.create_conversation(conversation_id)
        
        try:
            from .._types import RequestOptions
            
            options = RequestOptions(
                headers=headers,
                params=params,
                timeout=timeout
            )
            
            if stream:
                # Import here to avoid circular imports
                from .._streaming import AsyncStream
                
                # Request async streaming response
                response = await self._client.post(
                    "/chat/completions",
                    body=data,
                    options=options,
                    stream=stream,
                    stream_cls=AsyncStream,
                )
                
                async_stream_response = response
                
                # Add history tracking to stream if enabled
                if conversation and self._enable_history:
                    for msg in messages:
                        if msg.get("role") in ("user", "system"):
                            conversation.add_message(
                                role=msg["role"],
                                content=str(msg.get("content", "")),
                                metadata={"model": model, "stream": True}
                            )
                
                return async_stream_response
            else:
                # Request non-streaming async response
                response = await self._client.post(
                    "/chat/completions",
                    body=data,
                    options=options,
                    stream=stream,
                )
                
                # Parse non-streaming response
                completion = ChatCompletion.model_validate(response)
                
                # Add to conversation history if enabled
                if conversation and self._enable_history:
                    # Add user messages
                    for msg in messages:
                        if msg.get("role") in ("user", "system"):
                            conversation.add_message(
                                role=msg["role"],
                                content=str(msg.get("content", "")),
                                metadata={"model": model}
                            )
                    
                    # Add assistant response
                    if completion.choices:
                        assistant_message = completion.choices[0].message
                        conversation.add_message(
                            role="assistant",
                            content=assistant_message.content or "",
                            metadata={
                                "model": model,
                                "finish_reason": completion.choices[0].finish_reason,
                                "usage": completion.usage.model_dump() if completion.usage else None
                            }
                        )
                
                return completion
                
        except Exception as e:
            # Log error to conversation if available
            if conversation and self._enable_history:
                conversation.add_message(
                    role="system",
                    content=f"Error: {str(e)}",
                    metadata={"error": True, "model": model}
                )
            raise


class AsyncChat:
    """
    Asynchronous chat interface with completions
    """
    
    def __init__(self, client: AsyncTela, enable_history: bool = True) -> None:
        self.completions = AsyncCompletions(client, enable_history=enable_history)