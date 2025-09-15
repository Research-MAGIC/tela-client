import pytest
from unittest.mock import Mock, patch
from tela import Tela
from tela.types.chat import ChatCompletion


class TestCompletions:
    """Test chat completions"""
    
    @patch('tela._client.SyncAPIClient.post')
    def test_basic_completion(self, mock_post):
        """Test basic chat completion"""
        mock_response = {
            "id": "test-123",
            "object": "chat.completion",
            "created": 1234567890,
            "model": "wizard",
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "Test response"
                },
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 5,
                "total_tokens": 15
            }
        }
        mock_post.return_value = mock_response
        
        client = Tela(
            api_key="test-key",
            organization="test-org",
            project="test-project"
        )
        
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": "Hello"}]
        )
        
        assert response.choices[0].message.content == "Test response"
        assert response.usage.total_tokens == 15
    
    def test_completion_with_history(self):
        """Test completion with conversation history"""
        client = Tela(
            api_key="test-key",
            organization="test-org",
            project="test-project"
        )
        
        conv = client.create_conversation("test-conv")
        conv.add_user_message("Hello")
        conv.add_assistant_message("Hi there!")
        
        # Verify context is included
        messages = conv.get_messages()
        assert len(messages) == 2
        assert messages[0]["content"] == "Hello"
        assert messages[1]["content"] == "Hi there!"
    
    def test_summarization_formatting(self):
        """Test conversation summarization formatting"""
        client = Tela(
            api_key="test-key",
            organization="test-org",
            project="test-project"
        )
        
        conv = client.create_conversation("test-summary")
        conv.add_assistant_message("What's your name?")
        conv.add_user_message("John")
        
        # Test data block formatting (best practice)
        data_block = conv.format_as_data_block()
        assert 'Assistant: "What\'s your name?"' in data_block
        assert 'User: "John"' in data_block
        
        # Test JSON formatting
        json_data = conv.format_as_json_data()
        assert '"speaker": "assistant"' in json_data
        assert '"text": "What\'s your name?"' in json_data
        
        # Test sentinel formatting
        sentinel_format = conv.format_with_sentinels()
        assert "BEGIN LOG" in sentinel_format
        assert "END LOG" in sentinel_format