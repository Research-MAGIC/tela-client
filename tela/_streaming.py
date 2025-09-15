from __future__ import annotations

import json
import sys
import time
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Generic,
    Iterator,
    AsyncIterator,
    Optional,
    TypeVar,
    Union,
    cast,
)
import httpx

if TYPE_CHECKING:
    from ._base_client import BaseClient

T = TypeVar("T")


class Stream(Generic[T]):
    """Synchronous streaming response handler with CLI and NiceGUI support"""
    
    def __init__(
        self,
        *,
        response: httpx.Response,
        client: BaseClient,
        on_chunk: Optional[Callable[[T], None]] = None,
        on_content: Optional[Callable[[str], None]] = None,
        on_complete: Optional[Callable[[str], None]] = None,
    ) -> None:
        self.response = response
        self.client = client
        self._iterator = response.iter_lines()
        self.on_chunk = on_chunk  # Called for each chunk
        self.on_content = on_content  # Called for each content piece
        self.on_complete = on_complete  # Called with full content
        self._accumulated_content = ""
        self._chunks = []
    
    def __iter__(self) -> Iterator[T]:
        return self
    
    def __next__(self) -> T:
        while True:
            try:
                line = next(self._iterator)
            except StopIteration:
                # Call completion callback with accumulated content
                if self.on_complete and self._accumulated_content:
                    self.on_complete(self._accumulated_content)
                raise
            
            if not line:
                continue
            
            if line.startswith("data: "):
                data = line[6:]  # Remove "data: " prefix
                
                if data == "[DONE]":
                    if self.on_complete and self._accumulated_content:
                        self.on_complete(self._accumulated_content)
                    raise StopIteration
                
                try:
                    chunk = self._process_chunk(json.loads(data))
                    self._chunks.append(chunk)
                    
                    # Extract content for callbacks
                    content = self._extract_content(chunk)
                    if content:
                        self._accumulated_content += content
                        if self.on_content:
                            self.on_content(content)
                    
                    # Call chunk callback
                    if self.on_chunk:
                        self.on_chunk(chunk)
                    
                    return chunk
                except json.JSONDecodeError:
                    # Skip invalid JSON
                    continue
    
    def _process_chunk(self, data: dict) -> T:
        """Process a streaming chunk"""
        return cast(T, ChatCompletionChunk(**data))
    
    def _extract_content(self, chunk: T) -> str:
        """Extract content from a chunk for callbacks"""
        if hasattr(chunk, 'choices') and chunk.choices:
            choice = chunk.choices[0]
            if hasattr(choice, 'delta') and choice.delta and choice.delta.content:
                return choice.delta.content
        return ""
    
    def print_stream(self, end: str = "\n", flush: bool = True) -> str:
        """Print streaming content to stdout (CLI usage)"""
        accumulated = ""
        for chunk in self:
            content = self._extract_content(chunk)
            if content:
                print(content, end="", flush=flush)
                accumulated += content
        print(end, end="")
        return accumulated
    
    def collect(self) -> tuple[str, list[T]]:
        """Collect all streaming content and chunks"""
        chunks = list(self)
        return self._accumulated_content, chunks
    
    def close(self) -> None:
        """Close the stream"""
        self.response.close()
    
    def __enter__(self) -> Stream[T]:
        return self
    
    def __exit__(self, *args: Any) -> None:
        self.close()


class AsyncStream(Generic[T]):
    """Asynchronous streaming response handler with CLI and NiceGUI support"""
    
    def __init__(
        self,
        *,
        response: httpx.Response,
        client: BaseClient,
        on_chunk: Optional[Callable[[T], None]] = None,
        on_content: Optional[Callable[[str], None]] = None,
        on_complete: Optional[Callable[[str], None]] = None,
    ) -> None:
        self.response = response
        self.client = client
        self._iterator = response.aiter_lines()
        self.on_chunk = on_chunk  # Called for each chunk
        self.on_content = on_content  # Called for each content piece
        self.on_complete = on_complete  # Called with full content
        self._accumulated_content = ""
        self._chunks = []
    
    def __aiter__(self) -> AsyncIterator[T]:
        return self
    
    async def __anext__(self) -> T:
        while True:
            try:
                line = await self._iterator.__anext__()
            except StopAsyncIteration:
                # Call completion callback with accumulated content
                if self.on_complete and self._accumulated_content:
                    self.on_complete(self._accumulated_content)
                raise
            
            if not line:
                continue
            
            if line.startswith("data: "):
                data = line[6:]  # Remove "data: " prefix
                
                if data == "[DONE]":
                    if self.on_complete and self._accumulated_content:
                        self.on_complete(self._accumulated_content)
                    raise StopAsyncIteration
                
                try:
                    chunk = self._process_chunk(json.loads(data))
                    self._chunks.append(chunk)
                    
                    # Extract content for callbacks
                    content = self._extract_content(chunk)
                    if content:
                        self._accumulated_content += content
                        if self.on_content:
                            self.on_content(content)
                    
                    # Call chunk callback
                    if self.on_chunk:
                        self.on_chunk(chunk)
                    
                    return chunk
                except json.JSONDecodeError:
                    # Skip invalid JSON
                    continue
    
    def _process_chunk(self, data: dict) -> T:
        """Process a streaming chunk"""
        return cast(T, ChatCompletionChunk(**data))
    
    def _extract_content(self, chunk: T) -> str:
        """Extract content from a chunk for callbacks"""
        if hasattr(chunk, 'choices') and chunk.choices:
            choice = chunk.choices[0]
            if hasattr(choice, 'delta') and choice.delta and choice.delta.content:
                return choice.delta.content
        return ""
    
    async def print_stream(self, end: str = "\n", flush: bool = True) -> str:
        """Print streaming content to stdout (CLI usage)"""
        accumulated = ""
        async for chunk in self:
            content = self._extract_content(chunk)
            if content:
                print(content, end="", flush=flush)
                accumulated += content
        print(end, end="")
        return accumulated
    
    async def collect(self) -> tuple[str, list[T]]:
        """Collect all streaming content and chunks"""
        chunks = [chunk async for chunk in self]
        return self._accumulated_content, chunks
    
    async def close(self) -> None:
        """Close the stream"""
        self.response.close()
    
    async def __aenter__(self) -> AsyncStream[T]:
        return self
    
    async def __aexit__(self, *args: Any) -> None:
        await self.close()


# Streaming response types
class ChatCompletionChunk:
    """A chunk of a streaming chat completion"""
    
    def __init__(self, **data: Any) -> None:
        self.id = data.get("id")
        self.object = data.get("object")
        self.created = data.get("created")
        self.model = data.get("model")
        self.choices = [Choice(**c) for c in data.get("choices", [])]
    
    def __repr__(self) -> str:
        return f"ChatCompletionChunk(id={self.id}, choices={len(self.choices)})"


class Choice:
    """A choice in a completion"""
    
    def __init__(self, **data: Any) -> None:
        self.index = data.get("index", 0)
        self.delta = Delta(**data.get("delta", {}))
        self.finish_reason = data.get("finish_reason")
        self.logprobs = data.get("logprobs")
    
    def __repr__(self) -> str:
        return f"Choice(index={self.index}, finish_reason={self.finish_reason})"


class Delta:
    """Delta content in a streaming response"""
    
    def __init__(self, **data: Any) -> None:
        self.role = data.get("role")
        self.content = data.get("content")
        self.tool_calls = data.get("tool_calls")
        self.function_call = data.get("function_call")
    
    def __repr__(self) -> str:
        content_preview = self.content[:20] if self.content else None
        return f"Delta(role={self.role}, content={content_preview}...)"