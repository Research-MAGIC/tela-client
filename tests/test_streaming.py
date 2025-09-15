"""
Tests for streaming functionality in both CLI and NiceGUI environments
"""

import asyncio
import json
import pytest
from unittest.mock import Mock, AsyncMock, patch
from typing import List

import httpx

from tela._streaming import Stream, AsyncStream, ChatCompletionChunk
from tela._streaming_utils import StreamingDisplay
from tela import Tela, AsyncTela


class MockResponse:
    """Mock HTTP response for testing streaming"""
    
    def __init__(self, lines: List[str]):
        self.lines = lines
        self.iter_index = 0
    
    def iter_lines(self):
        """Mock iterator for sync streaming"""
        for line in self.lines:
            yield line
    
    def aiter_lines(self):
        """Mock async iterator for streaming"""
        async def async_gen():
            for line in self.lines:
                yield line
        return async_gen()
    
    def close(self):
        """Mock close method"""
        pass


def create_mock_stream_data() -> List[str]:
    """Create mock streaming data"""
    return [
        'data: {"id":"test-1","object":"chat.completion.chunk","created":1234567890,"model":"fabric-latest","choices":[{"index":0,"delta":{"role":"assistant"},"finish_reason":null}]}',
        'data: {"id":"test-1","object":"chat.completion.chunk","created":1234567890,"model":"fabric-latest","choices":[{"index":0,"delta":{"content":"Hello"},"finish_reason":null}]}',
        'data: {"id":"test-1","object":"chat.completion.chunk","created":1234567890,"model":"fabric-latest","choices":[{"index":0,"delta":{"content":" world"},"finish_reason":null}]}',
        'data: {"id":"test-1","object":"chat.completion.chunk","created":1234567890,"model":"fabric-latest","choices":[{"index":0,"delta":{"content":"!"},"finish_reason":"stop"}]}',
        'data: [DONE]'
    ]


class TestStream:
    """Test synchronous streaming functionality"""
    
    def test_basic_streaming(self):
        """Test basic stream iteration"""
        mock_response = MockResponse(create_mock_stream_data())
        mock_client = Mock()
        
        stream = Stream(response=mock_response, client=mock_client)
        
        chunks = list(stream)
        
        # Should get 4 chunks (excluding [DONE])
        assert len(chunks) == 4
        
        # Check first chunk
        first_chunk = chunks[0]
        assert hasattr(first_chunk, 'choices')
        assert len(first_chunk.choices) == 1
        assert first_chunk.choices[0].delta.role == "assistant"
    
    def test_content_extraction(self):
        """Test content extraction from chunks"""
        mock_response = MockResponse(create_mock_stream_data())
        mock_client = Mock()
        
        stream = Stream(response=mock_response, client=mock_client)
        
        content_chunks = []
        for chunk in stream:
            content = stream._extract_content(chunk)
            if content:
                content_chunks.append(content)
        
        assert content_chunks == ["Hello", " world", "!"]
    
    def test_callbacks(self):
        """Test streaming callbacks"""
        mock_response = MockResponse(create_mock_stream_data())
        mock_client = Mock()
        
        chunks_received = []
        content_received = []
        completion_called = False
        
        def on_chunk(chunk):
            chunks_received.append(chunk)
        
        def on_content(content):
            content_received.append(content)
        
        def on_complete(full_content):
            nonlocal completion_called
            completion_called = True
            assert full_content == "Hello world!"
        
        stream = Stream(
            response=mock_response,
            client=mock_client,
            on_chunk=on_chunk,
            on_content=on_content,
            on_complete=on_complete
        )
        
        list(stream)  # Consume stream
        
        assert len(chunks_received) == 4
        assert content_received == ["Hello", " world", "!"]
        assert completion_called
    
    def test_print_stream(self, capsys):
        """Test print_stream method"""
        mock_response = MockResponse(create_mock_stream_data())
        mock_client = Mock()
        
        stream = Stream(response=mock_response, client=mock_client)
        result = stream.print_stream()
        
        captured = capsys.readouterr()
        assert captured.out == "Hello world!\n"
        assert result == "Hello world!"
    
    def test_collect(self):
        """Test collect method"""
        mock_response = MockResponse(create_mock_stream_data())
        mock_client = Mock()
        
        stream = Stream(response=mock_response, client=mock_client)
        content, chunks = stream.collect()
        
        assert content == "Hello world!"
        assert len(chunks) == 4


class TestAsyncStream:
    """Test asynchronous streaming functionality"""
    
    @pytest.mark.asyncio
    async def test_basic_async_streaming(self):
        """Test basic async stream iteration"""
        mock_response = MockResponse(create_mock_stream_data())
        mock_client = Mock()
        
        stream = AsyncStream(response=mock_response, client=mock_client)
        
        chunks = []
        async for chunk in stream:
            chunks.append(chunk)
        
        assert len(chunks) == 4
        
        # Check content extraction
        first_chunk = chunks[0]
        assert hasattr(first_chunk, 'choices')
    
    @pytest.mark.asyncio
    async def test_async_callbacks(self):
        """Test async streaming callbacks"""
        mock_response = MockResponse(create_mock_stream_data())
        mock_client = Mock()
        
        chunks_received = []
        content_received = []
        completion_called = False
        
        def on_chunk(chunk):
            chunks_received.append(chunk)
        
        def on_content(content):
            content_received.append(content)
        
        def on_complete(full_content):
            nonlocal completion_called
            completion_called = True
            assert full_content == "Hello world!"
        
        stream = AsyncStream(
            response=mock_response,
            client=mock_client,
            on_chunk=on_chunk,
            on_content=on_content,
            on_complete=on_complete
        )
        
        async for chunk in stream:
            pass
        
        assert len(chunks_received) == 4
        assert content_received == ["Hello", " world", "!"]
        assert completion_called
    
    @pytest.mark.asyncio
    async def test_async_collect(self):
        """Test async collect method"""
        mock_response = MockResponse(create_mock_stream_data())
        mock_client = Mock()
        
        stream = AsyncStream(response=mock_response, client=mock_client)
        content, chunks = await stream.collect()
        
        assert content == "Hello world!"
        assert len(chunks) == 4


class TestStreamingDisplay:
    """Test StreamingDisplay utility"""
    
    def test_cli_mode(self, capsys):
        """Test StreamingDisplay in CLI mode"""
        display = StreamingDisplay(output_type="cli")
        
        display.update_content("Hello")
        display.update_content(" world")
        result = display.finalize()
        
        captured = capsys.readouterr()
        assert captured.out == "Hello world\n"
        assert result == "Hello world"
    
    def test_accumulation(self):
        """Test content accumulation"""
        display = StreamingDisplay(output_type="cli")
        
        display.update_content("Part 1")
        display.update_content(" Part 2") 
        display.update_content(" Part 3")
        
        assert display.accumulated_text == "Part 1 Part 2 Part 3"
    
    def test_clear(self):
        """Test clearing display"""
        display = StreamingDisplay(output_type="cli")
        
        display.update_content("Some content")
        assert display.accumulated_text == "Some content"
        
        display.clear()
        assert display.accumulated_text == ""


class TestErrorHandling:
    """Test error handling in streaming"""
    
    def test_invalid_json_handling(self):
        """Test handling of invalid JSON in stream"""
        invalid_data = [
            'data: {"invalid": json}',  # Invalid JSON
            'data: {"id":"test","object":"chat.completion.chunk","created":1234567890,"model":"fabric-latest","choices":[{"index":0,"delta":{"content":"Hello"},"finish_reason":null}]}',
            'data: [DONE]'
        ]
        
        mock_response = MockResponse(invalid_data)
        mock_client = Mock()
        
        stream = Stream(response=mock_response, client=mock_client)
        chunks = list(stream)
        
        # Should only get 1 valid chunk (invalid JSON is skipped)
        assert len(chunks) == 1
        assert stream._extract_content(chunks[0]) == "Hello"
    
    def test_empty_lines_handling(self):
        """Test handling of empty lines in stream"""
        data_with_empty_lines = [
            '',
            'data: {"id":"test","object":"chat.completion.chunk","created":1234567890,"model":"fabric-latest","choices":[{"index":0,"delta":{"content":"Hello"},"finish_reason":null}]}',
            '',
            'data: [DONE]'
        ]
        
        mock_response = MockResponse(data_with_empty_lines)
        mock_client = Mock()
        
        stream = Stream(response=mock_response, client=mock_client)
        chunks = list(stream)
        
        assert len(chunks) == 1
        assert stream._extract_content(chunks[0]) == "Hello"


# Legacy tests for backward compatibility
class TestStreaming:
    """Test streaming functionality - legacy tests"""
    
    def test_stream_parsing(self):
        """Test parsing of SSE stream"""
        mock_response = Mock()
        mock_client = Mock()
        
        # Mock SSE lines
        mock_response.iter_lines.return_value = iter([
            'data: {"choices":[{"delta":{"content":"Hello"}}]}',
            'data: {"choices":[{"delta":{"content":" world"}}]}',
            'data: [DONE]'
        ])
        
        stream = Stream(response=mock_response, client=mock_client)
        chunks = list(stream)
        
        assert len(chunks) == 2
        assert chunks[0].choices[0].delta.content == "Hello"
        assert chunks[1].choices[0].delta.content == " world"
    
    def test_stream_empty_lines(self):
        """Test that empty lines are skipped"""
        mock_response = Mock()
        mock_client = Mock()
        
        mock_response.iter_lines.return_value = iter([
            '',
            'data: {"choices":[{"delta":{"content":"Test"}}]}',
            '',
            'data: [DONE]'
        ])
        
        stream = Stream(response=mock_response, client=mock_client)
        chunks = list(stream)
        
        assert len(chunks) == 1
        assert chunks[0].choices[0].delta.content == "Test"
    
    @pytest.mark.asyncio
    async def test_async_stream(self):
        """Test async streaming"""
        mock_response = Mock()
        mock_client = Mock()
        
        # Mock async iterator
        async def mock_aiter_lines():
            lines = [
                'data: {"choices":[{"delta":{"content":"Async"}}]}',
                'data: {"choices":[{"delta":{"content":" test"}}]}',
                'data: [DONE]'
            ]
            for line in lines:
                yield line
        
        mock_response.aiter_lines.return_value = mock_aiter_lines()
        
        stream = AsyncStream(response=mock_response, client=mock_client)
        chunks = []
        async for chunk in stream:
            chunks.append(chunk)
        
        assert len(chunks) == 2
        assert chunks[0].choices[0].delta.content == "Async"
        assert chunks[1].choices[0].delta.content == " test"


if __name__ == "__main__":
    pytest.main([__file__])