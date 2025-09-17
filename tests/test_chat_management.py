import pytest
import json
import asyncio
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from tela import Tela, AsyncTela
from tela.types.chats import Chat, ChatList, ChatPaginatedResponse
from tela._chats import Chats, AsyncChats
from tela._history import HistoryManager, ConversationHistory
from tela._exceptions import (
    AuthenticationError,
    BadRequestError,
    NotFoundError,
    APIError,
    RateLimitError
)


class TestComprehensiveChatManagement:
    """Comprehensive test suite for chat management capabilities"""

    def test_client_initialization_with_chat_resources(self):
        """Test that both sync and async clients properly initialize chat resources"""
        # Sync client
        sync_client = Tela(
            api_key="test-key",
            organization="test-org",
            project="test-project"
        )

        assert hasattr(sync_client, 'chats')
        assert isinstance(sync_client.chats, Chats)
        assert hasattr(sync_client.chats, 'list')
        assert hasattr(sync_client.chats, 'get')
        assert hasattr(sync_client.chats, 'create')
        assert hasattr(sync_client.chats, 'update')
        assert hasattr(sync_client.chats, 'delete')

        # Async client
        async_client = AsyncTela(
            api_key="test-key",
            organization="test-org",
            project="test-project"
        )

        assert hasattr(async_client, 'chats')
        assert isinstance(async_client.chats, AsyncChats)
        assert hasattr(async_client.chats, 'list')
        assert hasattr(async_client.chats, 'get')
        assert hasattr(async_client.chats, 'create')
        assert hasattr(async_client.chats, 'update')
        assert hasattr(async_client.chats, 'delete')

    def test_history_manager_server_sync_initialization(self):
        """Test that history manager is properly initialized with server sync"""
        client = Tela(
            api_key="test-key",
            organization="test-org",
            project="test-project"
        )

        assert hasattr(client.history, 'sync_with_server')
        assert hasattr(client.history, 'create_server_chat')
        assert client.history.server_sync is True
        assert client.history._client is client

        # Test stats include server sync info
        stats = client.history.get_stats()
        assert 'server_sync' in stats
        assert stats['server_sync'] is True

    @patch('tela._base_client.SyncAPIClient.get')
    def test_list_chats_comprehensive(self, mock_get):
        """Test comprehensive chat listing functionality"""
        # Test with various response scenarios
        mock_response = {
            "data": [
                {
                    "chat_id": "chat-001",
                    "title": "Test Chat 1",
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T01:00:00Z",
                    "message_count": 5,
                    "metadata": {"priority": "high"}
                },
                {
                    "chat_id": "chat-002",
                    "title": None,  # Test null title
                    "created_at": "2024-01-02T00:00:00Z",
                    "updated_at": "2024-01-02T01:00:00Z",
                    "message_count": 0
                }
            ],
            "page": 1,
            "page_size": 10,
            "total_items": 2,
            "total_pages": 1,
            "has_next": False,
            "has_previous": False
        }
        mock_get.return_value = mock_response

        client = Tela(
            api_key="test-key",
            organization="test-org",
            project="test-project"
        )

        # Test default parameters
        result = client.chats.list()

        assert isinstance(result, ChatPaginatedResponse)
        assert len(result.data) == 2
        assert result.page == 1
        assert result.page_size == 10
        assert result.total_items == 2
        assert result.has_next is False

        # Test first chat
        chat1 = result.data[0]
        assert chat1.chat_id == "chat-001"
        assert chat1.id == "chat-001"  # Test property alias
        assert chat1.title == "Test Chat 1"
        assert chat1.message_count == 5
        assert chat1.metadata == {"priority": "high"}

        # Test second chat with null title
        chat2 = result.data[1]
        assert chat2.chat_id == "chat-002"
        assert chat2.title is None
        assert chat2.message_count == 0

        # Verify API call with default parameters
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert call_args[0][0] == "/chats"
        request_options = call_args[1]["options"]
        assert request_options.params["page"] == 1
        assert request_options.params["page_size"] == 10

    @patch('tela._base_client.SyncAPIClient.get')
    def test_list_chats_pagination_edge_cases(self, mock_get):
        """Test pagination edge cases and validation"""
        client = Tela(
            api_key="test-key",
            organization="test-org",
            project="test-project"
        )

        # Test edge case: page = 1 (minimum)
        mock_get.return_value = {"data": [], "page": 1, "page_size": 1}
        result = client.chats.list(page=1, page_size=1)
        assert result.page == 1

        # Test edge case: page_size = 100 (maximum)
        mock_get.return_value = {"data": [], "page": 1, "page_size": 100}
        result = client.chats.list(page=1, page_size=100)
        assert result.page_size == 100

        # Test validation: page < 1
        with pytest.raises(ValueError, match="Page number must be >= 1"):
            client.chats.list(page=0)

        # Test validation: page_size < 1
        with pytest.raises(ValueError, match="Page size must be between 1 and 100"):
            client.chats.list(page_size=0)

        # Test validation: page_size > 100
        with pytest.raises(ValueError, match="Page size must be between 1 and 100"):
            client.chats.list(page_size=101)

    @patch('tela._base_client.SyncAPIClient.post')
    def test_create_chat_comprehensive(self, mock_post):
        """Test comprehensive chat creation functionality"""
        mock_response = {"chat_id": "chat-new-123"}
        mock_post.return_value = mock_response

        client = Tela(
            api_key="test-key",
            organization="test-org",
            project="test-project"
        )

        # Test with default parameters
        result = client.chats.create()

        assert isinstance(result, dict)
        assert result["chat_id"] == "chat-new-123"

        # Verify API call with defaults
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[0][0] == "/chats"

        body = call_args[1]["body"]
        assert body["module_id"] == "chat"
        assert body["message"] == ""

        options = call_args[1]["options"]
        assert "Content-Type" in options.headers
        assert options.headers["Content-Type"] == "application/json"

        # Reset mock for next test
        mock_post.reset_mock()

        # Test with custom parameters
        result = client.chats.create(
            module_id="custom_module",
            message="Welcome to custom chat!"
        )

        # Verify custom parameters
        call_args = mock_post.call_args
        body = call_args[1]["body"]
        assert body["module_id"] == "custom_module"
        assert body["message"] == "Welcome to custom chat!"

    @patch('tela._base_client.SyncAPIClient.get')
    def test_get_chat_comprehensive(self, mock_get):
        """Test comprehensive get chat functionality"""
        mock_response = {
            "chat_id": "chat-detail-123",
            "title": "Detailed Chat",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T02:00:00Z",
            "message_count": 15,
            "last_message": "Last message content",
            "metadata": {
                "category": "support",
                "priority": "medium",
                "tags": ["urgent", "billing"]
            }
        }
        mock_get.return_value = mock_response

        client = Tela(
            api_key="test-key",
            organization="test-org",
            project="test-project"
        )

        result = client.chats.get("chat-detail-123")

        assert isinstance(result, Chat)
        assert result.chat_id == "chat-detail-123"
        assert result.id == "chat-detail-123"  # Test alias
        assert result.title == "Detailed Chat"
        assert result.message_count == 15
        assert result.last_message == "Last message content"
        assert result.metadata["category"] == "support"
        assert result.metadata["tags"] == ["urgent", "billing"]

        # Verify API call
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert call_args[0][0] == "/chats/chat-detail-123"

    def test_error_handling_comprehensive(self):
        """Test comprehensive error handling for all methods"""
        client = Tela(
            api_key="test-key",
            organization="test-org",
            project="test-project"
        )

        # Test various HTTP error responses
        error_scenarios = [
            (400, BadRequestError),
            (401, AuthenticationError),
            (404, NotFoundError),
            (429, RateLimitError),
            (500, APIError)
        ]

        for status_code, expected_exception in error_scenarios:
            with patch('tela._base_client.SyncAPIClient.get') as mock_get:
                # Mock HTTP error response
                error_response = Mock()
                error_response.status_code = status_code
                error_response.json.return_value = {
                    "error": {"message": f"HTTP {status_code} error"}
                }
                error_response.text = f"HTTP {status_code} error"

                # Create the appropriate exception instance
                if status_code in [400, 401, 403, 404, 409, 422, 429] or status_code >= 500:
                    if expected_exception in [BadRequestError, AuthenticationError, NotFoundError, RateLimitError]:
                        exception_instance = expected_exception(f"HTTP {status_code} error", response=error_response)
                    else:
                        exception_instance = expected_exception(f"HTTP {status_code} error")
                else:
                    exception_instance = expected_exception(f"HTTP {status_code} error")

                mock_get.side_effect = exception_instance

                with pytest.raises(expected_exception):
                    client.chats.list()

    @patch('tela._chats.Chats.list')
    def test_history_sync_comprehensive(self, mock_list):
        """Test comprehensive history synchronization"""
        # Create mock server chats with various scenarios
        mock_chat_data = [
            Chat(
                chat_id="server-chat-001",
                title="Server Chat 1",
                created_at=datetime(2024, 1, 1, 10, 0, 0),
                updated_at=datetime(2024, 1, 1, 11, 0, 0),
                message_count=5,
                metadata={"type": "support"}
            ),
            Chat(
                chat_id="server-chat-002",
                title=None,  # Test null title
                created_at=datetime(2024, 1, 2, 10, 0, 0),
                updated_at=datetime(2024, 1, 2, 11, 0, 0),
                message_count=0
            ),
            Chat(
                chat_id="server-chat-003",
                title="Server Chat 3",
                created_at=None,  # Test null dates
                updated_at=None,
                message_count=3
            )
        ]

        mock_response = ChatPaginatedResponse(
            data=mock_chat_data,
            page=1,
            page_size=100,
            total_items=3
        )
        mock_list.return_value = mock_response

        client = Tela(
            api_key="test-key",
            organization="test-org",
            project="test-project"
        )

        # Perform sync
        result = client.history.sync_with_server()

        assert result["synced"] is True
        assert result["synced_count"] == 3
        assert result["total_server_chats"] == 3
        assert len(result["errors"]) == 0

        # Verify all conversations were created locally
        for i, chat_id in enumerate(["server-chat-001", "server-chat-002", "server-chat-003"]):
            local_conv = client.history.get_conversation(chat_id)
            assert local_conv is not None
            assert local_conv.id == chat_id
            assert "synced_from_server" in local_conv.metadata
            assert local_conv.metadata["synced_from_server"] is True

        # Test duplicate sync (should not create duplicates)
        result2 = client.history.sync_with_server()
        assert result2["synced_count"] == 0  # No new chats to sync

    @patch('tela._chats.Chats.create')
    def test_history_create_server_chat_comprehensive(self, mock_create):
        """Test comprehensive server chat creation via history manager"""
        mock_create.return_value = {"chat_id": "history-created-chat"}

        client = Tela(
            api_key="test-key",
            organization="test-org",
            project="test-project"
        )

        # Test with default parameters
        chat_id = client.history.create_server_chat()

        assert chat_id == "history-created-chat"

        # Verify API call
        mock_create.assert_called_once()
        call_args = mock_create.call_args
        assert call_args[1]["module_id"] == "chat"
        assert call_args[1]["message"] == ""

        # Verify local conversation was created
        local_conv = client.history.get_conversation("history-created-chat")
        assert local_conv is not None
        assert local_conv.id == "history-created-chat"
        assert "synced_with_server" in local_conv.metadata
        assert local_conv.metadata["synced_with_server"] is True

        # Reset mock for custom parameters test
        mock_create.reset_mock()
        mock_create.return_value = {"chat_id": "custom-history-chat"}

        # Test with custom parameters
        chat_id = client.history.create_server_chat(
            module_id="custom_module",
            message="Custom message via history"
        )

        assert chat_id == "custom-history-chat"

        call_args = mock_create.call_args
        assert call_args[1]["module_id"] == "custom_module"
        assert call_args[1]["message"] == "Custom message via history"

    def test_integration_with_conversation_system(self):
        """Test integration between chat management and conversation system"""
        client = Tela(
            api_key="test-key",
            organization="test-org",
            project="test-project"
        )

        # Create a local conversation manually
        conv = client.create_conversation("integration-test-chat")
        conv.add_message("user", "Hello from integration test")
        conv.add_message("assistant", "Hello back from integration test")

        # Test getting conversation context
        context = client.get_conversation_context("integration-test-chat")
        assert len(context) == 2
        assert context[0]["role"] == "user"
        assert context[1]["role"] == "assistant"

        # Test exporting conversation
        exported_json = client.export_conversation("integration-test-chat", format="json")
        exported_text = client.export_conversation("integration-test-chat", format="text")

        assert isinstance(exported_json, (dict, str))
        assert isinstance(exported_text, str)

        # Test conversation listing
        conversations = client.list_conversations()
        assert "integration-test-chat" in conversations

    def test_chat_type_property_alias(self):
        """Test that Chat.id property correctly aliases chat_id"""
        # Test direct instantiation
        chat = Chat(chat_id="test-123", title="Test Chat")
        assert chat.chat_id == "test-123"
        assert chat.id == "test-123"
        assert chat.id == chat.chat_id

        # Test with model validation
        chat_data = {
            "chat_id": "validated-456",
            "title": "Validated Chat",
            "message_count": 10
        }
        validated_chat = Chat.model_validate(chat_data)
        assert validated_chat.chat_id == "validated-456"
        assert validated_chat.id == "validated-456"
        assert validated_chat.title == "Validated Chat"
        assert validated_chat.message_count == 10

    def test_extra_headers_and_parameters(self):
        """Test that extra headers and query parameters are properly handled"""
        client = Tela(
            api_key="test-key",
            organization="test-org",
            project="test-project"
        )

        with patch('tela._base_client.SyncAPIClient.get') as mock_get:
            mock_get.return_value = {"data": [], "page": 1, "page_size": 10}

            # Test extra headers
            client.chats.list(
                extra_headers={"X-Custom-Header": "custom-value"},
                extra_query={"custom_param": "custom_value"}
            )

            call_args = mock_get.call_args
            options = call_args[1]["options"]

            # Verify extra headers were included
            assert "X-Custom-Header" in options.headers
            assert options.headers["X-Custom-Header"] == "custom-value"

            # Verify extra query params were included
            assert "custom_param" in options.params
            assert options.params["custom_param"] == "custom_value"


class TestAsyncChatManagementComprehensive:
    """Comprehensive async chat management tests"""

    @pytest.mark.asyncio
    @patch('tela._base_client.AsyncAPIClient.get')
    async def test_async_list_chats_comprehensive(self, mock_get):
        """Test comprehensive async chat listing"""
        mock_response = {
            "data": [
                {
                    "chat_id": "async-chat-001",
                    "title": "Async Chat 1",
                    "message_count": 3
                }
            ],
            "page": 1,
            "page_size": 10
        }
        mock_get.return_value = mock_response

        client = AsyncTela(
            api_key="test-key",
            organization="test-org",
            project="test-project"
        )

        result = await client.chats.list(page=2, page_size=5)

        assert isinstance(result, ChatPaginatedResponse)
        assert len(result.data) == 1
        assert result.data[0].chat_id == "async-chat-001"

        # Verify API call with parameters
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        options = call_args[1]["options"]
        assert options.params["page"] == 2
        assert options.params["page_size"] == 5

    @pytest.mark.asyncio
    @patch('tela._base_client.AsyncAPIClient.post')
    async def test_async_create_chat_comprehensive(self, mock_post):
        """Test comprehensive async chat creation"""
        mock_post.return_value = {"chat_id": "async-created-chat"}

        client = AsyncTela(
            api_key="test-key",
            organization="test-org",
            project="test-project"
        )

        result = await client.chats.create(
            module_id="async_module",
            message="Async chat message"
        )

        assert result["chat_id"] == "async-created-chat"

        # Verify API call
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        body = call_args[1]["body"]
        assert body["module_id"] == "async_module"
        assert body["message"] == "Async chat message"

    @pytest.mark.asyncio
    async def test_async_concurrent_operations(self):
        """Test concurrent async operations"""
        client = AsyncTela(
            api_key="test-key",
            organization="test-org",
            project="test-project"
        )

        with patch('tela._base_client.AsyncAPIClient.post') as mock_post:
            # Mock responses for concurrent creates
            mock_post.side_effect = [
                {"chat_id": "concurrent-1"},
                {"chat_id": "concurrent-2"},
                {"chat_id": "concurrent-3"}
            ]

            # Create multiple chats concurrently
            tasks = [
                client.chats.create(module_id="chat", message=f"Concurrent {i}")
                for i in range(3)
            ]

            results = await asyncio.gather(*tasks)

            assert len(results) == 3
            assert results[0]["chat_id"] == "concurrent-1"
            assert results[1]["chat_id"] == "concurrent-2"
            assert results[2]["chat_id"] == "concurrent-3"

            # Verify all calls were made
            assert mock_post.call_count == 3

    @pytest.mark.asyncio
    async def test_async_error_handling(self):
        """Test async error handling"""
        client = AsyncTela(
            api_key="test-key",
            organization="test-org",
            project="test-project"
        )

        with patch('tela._base_client.AsyncAPIClient.get') as mock_get:
            # Create proper error response
            error_response = Mock()
            error_response.status_code = 404
            error_response.text = "Chat not found"

            mock_get.side_effect = NotFoundError("Chat not found", response=error_response)

            with pytest.raises(NotFoundError):
                await client.chats.get("nonexistent-chat")


class TestBackwardsCompatibility:
    """Test backwards compatibility with existing functionality"""

    def test_existing_conversation_functionality_unchanged(self):
        """Test that existing conversation functionality still works"""
        client = Tela(
            api_key="test-key",
            organization="test-org",
            project="test-project"
        )

        # Test existing methods still work
        conv = client.create_conversation("compat-test")
        assert conv.id == "compat-test"

        conv.add_message("user", "Test message")
        assert conv.message_count == 1

        retrieved_conv = client.get_conversation("compat-test")
        assert retrieved_conv is not None
        assert retrieved_conv.id == "compat-test"

        conversations = client.list_conversations()
        assert "compat-test" in conversations

        # Test export functionality
        exported = client.export_conversation("compat-test", format="json")
        assert exported is not None

    def test_chat_completion_functionality_unchanged(self):
        """Test that chat completion functionality is unchanged"""
        client = Tela(
            api_key="test-key",
            organization="test-org",
            project="test-project"
        )

        # Verify chat completion interface is still available
        assert hasattr(client, 'chat')
        assert hasattr(client.chat, 'completions')
        assert hasattr(client.chat.completions, 'create')

        # Verify send_message method is still available
        assert hasattr(client, 'send_message')

    def test_model_discovery_functionality_unchanged(self):
        """Test that model discovery functionality is unchanged"""
        client = Tela(
            api_key="test-key",
            organization="test-org",
            project="test-project"
        )

        # Verify model methods are still available
        assert hasattr(client, 'get_models')
        assert hasattr(client, 'get_model_info')
        assert hasattr(client, 'get_model_capabilities')
        assert hasattr(client, 'list_available_models')


class TestRealWorldScenarios:
    """Test real-world usage scenarios"""

    @patch('tela._base_client.SyncAPIClient.get')
    @patch('tela._base_client.SyncAPIClient.post')
    def test_complete_chat_lifecycle(self, mock_post, mock_get):
        """Test complete chat lifecycle from creation to usage"""
        # Mock responses
        mock_post.return_value = {"chat_id": "lifecycle-chat"}
        mock_get.side_effect = [
            # First call: list chats (empty)
            {"data": [], "page": 1, "page_size": 10},
            # Second call: get specific chat
            {
                "chat_id": "lifecycle-chat",
                "title": "Lifecycle Chat",
                "message_count": 0
            }
        ]

        client = Tela(
            api_key="test-key",
            organization="test-org",
            project="test-project"
        )

        # 1. List existing chats (should be empty)
        initial_chats = client.chats.list()
        assert len(initial_chats.data) == 0

        # 2. Create a new chat
        chat_response = client.chats.create(
            module_id="chat",
            message="Welcome to lifecycle test!"
        )
        chat_id = chat_response["chat_id"]
        assert chat_id == "lifecycle-chat"

        # 3. Get the created chat details
        chat_details = client.chats.get(chat_id)
        assert chat_details.chat_id == "lifecycle-chat"

        # 4. Use chat with conversation system
        local_conv = client.create_conversation(chat_id)
        local_conv.add_message("user", "Hello in lifecycle chat")

        # 5. Verify integration
        conversations = client.list_conversations()
        assert chat_id in conversations

    def test_pagination_workflow(self):
        """Test realistic pagination workflow"""
        client = Tela(
            api_key="test-key",
            organization="test-org",
            project="test-project"
        )

        page_responses = [
            # Page 1
            {
                "data": [{"chat_id": f"chat-{i}", "title": f"Chat {i}"} for i in range(1, 6)],
                "page": 1,
                "page_size": 5,
                "total_items": 12,
                "has_next": True
            },
            # Page 2
            {
                "data": [{"chat_id": f"chat-{i}", "title": f"Chat {i}"} for i in range(6, 11)],
                "page": 2,
                "page_size": 5,
                "total_items": 12,
                "has_next": True
            },
            # Page 3
            {
                "data": [{"chat_id": f"chat-{i}", "title": f"Chat {i}"} for i in range(11, 13)],
                "page": 3,
                "page_size": 5,
                "total_items": 12,
                "has_next": False
            }
        ]

        all_chats = []

        with patch('tela._base_client.SyncAPIClient.get') as mock_get:
            mock_get.side_effect = page_responses

            # Simulate realistic pagination
            page = 1
            while True:
                response = client.chats.list(page=page, page_size=5)
                all_chats.extend(response.data)

                if not response.has_next:
                    break
                page += 1

        # Verify we got all chats
        assert len(all_chats) == 12
        assert all_chats[0].chat_id == "chat-1"
        assert all_chats[-1].chat_id == "chat-12"