"""
Tests for conversation history management and context handling
"""

import pytest
from unittest.mock import Mock, patch
from typing import List, Dict, Any

from tela import Tela, AsyncTela
from tela._history import ConversationHistory


def create_sample_messages() -> List[Dict[str, Any]]:
    """Create sample conversation messages"""
    return [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there!"},
        {"role": "user", "content": "How are you?"},
        {"role": "assistant", "content": "I'm doing well, thanks!"},
        {"role": "user", "content": "What's the weather like?"},
        {"role": "assistant", "content": "I don't have access to current weather data."}
    ]


class TestConversationContext:
    """Test conversation context management"""
    
    def test_get_conversation_context_all_messages(self):
        """Test getting full conversation context"""
        client = Tela(
            api_key="test-key",
            organization="test-org",
            project="test-project"
        )
        
        # Create conversation with messages
        conv = client.create_conversation("test-conv")
        sample_messages = create_sample_messages()
        
        for msg in sample_messages:
            conv.add_message(msg["role"], msg["content"])
        
        # Get full context
        context = client.get_conversation_context(conversation_id="test-conv")
        
        assert len(context) == len(sample_messages)
        for i, msg in enumerate(context):
            assert msg["role"] == sample_messages[i]["role"]
            assert msg["content"] == sample_messages[i]["content"]
    
    def test_get_conversation_context_with_limit(self):
        """Test getting limited conversation context"""
        client = Tela(
            api_key="test-key",
            organization="test-org",
            project="test-project"
        )
        
        conv = client.create_conversation("test-conv")
        sample_messages = create_sample_messages()
        
        for msg in sample_messages:
            conv.add_message(msg["role"], msg["content"])
        
        # Get limited context (last 3 messages)
        context = client.get_conversation_context(
            conversation_id="test-conv",
            max_messages=3
        )
        
        assert len(context) == 3
        # Should get the last 3 messages
        expected_messages = sample_messages[-3:]
        for i, msg in enumerate(context):
            assert msg["role"] == expected_messages[i]["role"]
            assert msg["content"] == expected_messages[i]["content"]
    
    def test_get_conversation_context_from_messages(self):
        """Test getting context directly from message list"""
        client = Tela(
            api_key="test-key",
            organization="test-org",
            project="test-project"
        )
        
        sample_messages = create_sample_messages()
        
        context = client.get_conversation_context(messages=sample_messages)
        
        assert len(context) == len(sample_messages)
        for i, msg in enumerate(context):
            assert msg["role"] == sample_messages[i]["role"]
            assert msg["content"] == sample_messages[i]["content"]
    
    def test_get_conversation_context_filters_roles(self):
        """Test that only user, assistant, system messages are included"""
        client = Tela(
            api_key="test-key",
            organization="test-org",
            project="test-project"
        )
        
        # Messages with various roles
        mixed_messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi!"},
            {"role": "system", "content": "System message"},
            {"role": "tool", "content": "Tool output"},  # Should be filtered out
            {"role": "function", "content": "Function result"},  # Should be filtered out
        ]
        
        context = client.get_conversation_context(messages=mixed_messages)
        
        # Should only have user, assistant, system messages
        assert len(context) == 3
        assert context[0]["role"] == "user"
        assert context[1]["role"] == "assistant" 
        assert context[2]["role"] == "system"


class TestSendMessage:
    """Test send_message functionality"""
    
    def test_send_message_creates_conversation(self):
        """Test that send_message creates conversation if needed"""
        client = Tela(
            api_key="test-key",
            organization="test-org",
            project="test-project"
        )
        
        # Mock the chat completions create method on the instance
        with patch.object(client.chat.completions, 'create') as mock_create:
            mock_response = Mock()
            mock_response.choices = [Mock(message=Mock(content="Test response"))]
            mock_create.return_value = mock_response
            
            response = client.send_message("Hello")
            
            # Should create a conversation
            conversations = client.list_conversations()
            assert len(conversations) > 0
            
            # Should add messages to history
            conv_id = conversations[0]
            conv = client.get_conversation(conv_id)
            assert conv.message_count == 2  # User message + assistant response
    
    def test_send_message_with_existing_conversation(self):
        """Test send_message with existing conversation ID"""
        client = Tela(
            api_key="test-key",
            organization="test-org",
            project="test-project"
        )
        
        # Create conversation and add some history
        conv = client.create_conversation("existing-conv")
        conv.add_message("user", "Previous message")
        conv.add_message("assistant", "Previous response")
        
        with patch.object(client.chat.completions, 'create') as mock_create:
            mock_response = Mock()
            mock_response.choices = [Mock(message=Mock(content="Test response"))]
            mock_create.return_value = mock_response
            
            response = client.send_message(
                "New message",
                conversation_id="existing-conv"
            )
            
            # Check that context was included in the API call
            mock_create.assert_called_once()
            call_args = mock_create.call_args
            messages_sent = call_args.kwargs['messages']
            
            # Should include previous messages + new message
            assert len(messages_sent) == 3
            assert messages_sent[0]['content'] == "Previous message"
            assert messages_sent[1]['content'] == "Previous response"
            assert messages_sent[2]['content'] == "New message"
            
            # Should add new messages to history
            assert conv.message_count == 4
    
    def test_send_message_with_max_history(self):
        """Test send_message with history limit"""
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Test response"))]
        mock_create.return_value = mock_response
        
        client = Tela(
            api_key="test-key",
            organization="test-org",
            project="test-project"
        )
        
        # Create conversation with many messages
        conv = client.create_conversation("history-limit")
        for i in range(10):
            conv.add_message("user", f"Message {i}")
            conv.add_message("assistant", f"Response {i}")
        
        response = client.send_message(
            "New message",
            conversation_id="history-limit",
            max_history=4  # Only include last 4 messages
        )
        
        call_args = mock_create.call_args
        messages_sent = call_args.kwargs['messages']
        
        # Should include 4 history messages + 1 new message = 5 total
        assert len(messages_sent) == 5
        
        # Should be the last 4 messages from history + new message
        assert "Message 8" in messages_sent[0]['content']
        assert "New message" in messages_sent[-1]['content']


class TestConversationExport:
    """Test conversation export functionality"""
    
    def test_export_messages_format(self):
        """Test exporting conversation as messages for model consumption"""
        client = Tela(
            api_key="test-key",
            organization="test-org",
            project="test-project"
        )
        
        conv = client.create_conversation("export-test")
        sample_messages = create_sample_messages()
        
        for msg in sample_messages:
            conv.add_message(msg["role"], msg["content"])
        
        exported = client.export_conversation("export-test", format="messages")
        
        assert isinstance(exported, list)
        assert len(exported) == len(sample_messages)
        
        for i, msg in enumerate(exported):
            assert msg["role"] == sample_messages[i]["role"]
            assert msg["content"] == sample_messages[i]["content"]
            # Should only have role and content (clean for model)
            assert set(msg.keys()) == {"role", "content"}
    
    def test_export_json_format(self):
        """Test exporting conversation as JSON"""
        client = Tela(
            api_key="test-key",
            organization="test-org",
            project="test-project"
        )
        
        conv = client.create_conversation("json-export")
        conv.add_message("user", "Hello")
        conv.add_message("assistant", "Hi there!")
        
        exported = client.export_conversation("json-export", format="json")
        
        assert isinstance(exported, dict)
        assert "id" in exported
        assert "messages" in exported
        assert "created_at" in exported
        assert "message_count" in exported
        assert exported["message_count"] == 2
    
    def test_export_text_format(self):
        """Test exporting conversation as text"""
        client = Tela(
            api_key="test-key",
            organization="test-org",
            project="test-project"
        )
        
        conv = client.create_conversation("text-export")
        conv.add_message("user", "Hello")
        conv.add_message("assistant", "Hi there!")
        
        exported = client.export_conversation("text-export", format="text")
        
        assert isinstance(exported, str)
        assert "User: Hello" in exported
        assert "Assistant: Hi there!" in exported
    
    def test_export_markdown_format(self):
        """Test exporting conversation as markdown"""
        client = Tela(
            api_key="test-key",
            organization="test-org",
            project="test-project"
        )
        
        conv = client.create_conversation("md-export")
        conv.add_message("user", "Hello")
        conv.add_message("assistant", "Hi there!")
        
        exported = client.export_conversation("md-export", format="markdown")
        
        assert isinstance(exported, str)
        assert "# Conversation md-export" in exported
        assert "### User" in exported
        assert "### Assistant" in exported
        assert "Hello" in exported
        assert "Hi there!" in exported


class TestAsyncConversation:
    """Test async conversation functionality"""
    
    @pytest.mark.asyncio
    @patch('tela.AsyncTela.chat.completions.create')
    async def test_async_send_message(self, mock_create):
        """Test async send_message functionality"""
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Async response"))]
        mock_create.return_value = mock_response
        
        client = AsyncTela(
            api_key="test-key",
            organization="test-org",
            project="test-project"
        )
        
        try:
            response = await client.send_message("Hello async")
            
            assert response == "Async response"
            
            # Check conversation was created
            conversations = client.list_conversations()
            assert len(conversations) > 0
            
        finally:
            await client.close()
    
    @pytest.mark.asyncio
    async def test_async_conversation_context(self):
        """Test async conversation context management"""
        client = AsyncTela(
            api_key="test-key",
            organization="test-org",
            project="test-project"
        )
        
        try:
            # Create conversation and add messages
            conv = client.create_conversation("async-context")
            sample_messages = create_sample_messages()
            
            for msg in sample_messages:
                conv.add_message(msg["role"], msg["content"])
            
            # Get context
            context = client.get_conversation_context(conversation_id="async-context")
            
            assert len(context) == len(sample_messages)
            
        finally:
            await client.close()


class TestConversationBestPractices:
    """Test that best practices are followed"""
    
    @patch('tela.Tela.chat.completions.create')
    def test_proper_message_role_handling(self, mock_create):
        """Test that message roles are preserved correctly"""
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Response"))]
        mock_create.return_value = mock_response
        
        client = Tela(
            api_key="test-key",
            organization="test-org",
            project="test-project"
        )
        
        # Create conversation with mixed roles
        conv = client.create_conversation("role-test")
        conv.add_message("system", "You are helpful")
        conv.add_message("user", "Hello")
        conv.add_message("assistant", "Hi!")
        
        client.send_message("Follow up", conversation_id="role-test")
        
        # Check API call preserved roles
        call_args = mock_create.call_args
        messages_sent = call_args.kwargs['messages']
        
        assert messages_sent[0]['role'] == 'system'
        assert messages_sent[1]['role'] == 'user'
        assert messages_sent[2]['role'] == 'assistant'
        assert messages_sent[3]['role'] == 'user'
        
        # No role manipulation or data formatting
        assert all('DATA' not in str(msg) for msg in messages_sent)
        assert all('STATIC' not in str(msg) for msg in messages_sent)
    
    def test_conversation_context_limits(self):
        """Test that context limits work properly"""
        client = Tela(
            api_key="test-key",
            organization="test-org",
            project="test-project"
        )
        
        # Create long conversation
        conv = client.create_conversation("limit-test")
        for i in range(50):
            conv.add_message("user", f"Message {i}")
            conv.add_message("assistant", f"Response {i}")
        
        # Test various limits
        context_10 = client.get_conversation_context("limit-test", max_messages=10)
        context_20 = client.get_conversation_context("limit-test", max_messages=20)
        context_all = client.get_conversation_context("limit-test")
        
        assert len(context_10) == 10
        assert len(context_20) == 20
        assert len(context_all) == 100  # 50 pairs
        
        # Should get most recent messages
        assert "Message 49" in context_10[-2]['content']  # Second to last
        assert "Response 49" in context_10[-1]['content']  # Last


if __name__ == "__main__":
    pytest.main([__file__, "-v"])