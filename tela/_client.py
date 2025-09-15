from __future__ import annotations

import os
import json
from typing import TYPE_CHECKING, Any, Union, Mapping, Optional, List, Dict, Literal
from typing_extensions import override
from datetime import datetime

import httpx

from ._base_client import SyncAPIClient, AsyncAPIClient
from ._types import NOT_GIVEN, NotGiven
from ._exceptions import AuthenticationError
from ._version import __version__
from ._history import ConversationHistory, HistoryManager
from .types.chat import Chat, AsyncChat
from .types.models import Model, ModelList, ModelCapabilities, UsageInfo, ParameterInfo

if TYPE_CHECKING:
    from ._types import Headers, Query

__all__ = ["Tela", "AsyncTela", "Client", "AsyncClient"]

# Default configuration
DEFAULT_BASE_URL = "https://api.telaos.com/v1"
DEFAULT_MAX_RETRIES = 2
DEFAULT_TIMEOUT = 600.0


class Tela(SyncAPIClient):
    """
    Tela/Fabric API Client with conversation history management
    
    Compatible with OpenAI SDK patterns for easy migration
    """
    
    chat: Chat
    history: HistoryManager
    
    def __init__(
        self,
        *,
        api_key: str | None = None,
        organization: str | None = None,
        project: str | None = None,
        base_url: str | httpx.URL | None = None,
        timeout: float | httpx.Timeout | None = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        default_headers: Mapping[str, str] | None = None,
        default_query: Mapping[str, object] | None = None,
        http_client: httpx.Client | None = None,
        enable_history: bool = True,
        history_file: str | None = None,
        _strict_response_validation: bool = False,
    ) -> None:
        """
        Initialize Tela client with history support
        
        Args:
            api_key: Your Tela API key (or set TELAOS_API_KEY env var)
            organization: Organization ID (or set TELAOS_ORG_ID env var)
            project: Project ID (or set TELAOS_PROJECT_ID env var)
            base_url: Override the default base URL for API requests
            timeout: Default timeout for requests
            max_retries: Maximum number of retries for failed requests
            default_headers: Default headers to include with every request
            default_query: Default query parameters to include with every request
            http_client: Pre-configured httpx.Client
            enable_history: Enable conversation history tracking
            history_file: File to persist conversation history
        """
        
        # Get credentials from environment if not provided
        if api_key is None:
            api_key = os.environ.get("TELAOS_API_KEY")
        if api_key is None or api_key == "":
            raise AuthenticationError(
                "The api_key client option must be set either by passing api_key to the client or "
                "by setting the TELAOS_API_KEY environment variable"
            )
        self.api_key = api_key
        
        if organization is None:
            organization = os.environ.get("TELAOS_ORG_ID")
        if organization is None or organization == "":
            raise AuthenticationError(
                "The organization client option must be set either by passing organization to the client or "
                "by setting the TELAOS_ORG_ID environment variable"
            )
        self.organization = organization
        
        if project is None:
            project = os.environ.get("TELAOS_PROJECT_ID")
        if project is None or project == "":
            raise AuthenticationError(
                "The project client option must be set either by passing project to the client or "
                "by setting the TELAOS_PROJECT_ID environment variable"
            )
        self.project = project
        
        if base_url is None:
            base_url = os.environ.get("TELA_BASE_URL", DEFAULT_BASE_URL)
        
        super().__init__(
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
            default_headers={
                "Authorization": f"Bearer {api_key}",
                "OpenAI-Organization": organization,
                "OpenAI-Project": project,
                "User-Agent": f"Tela/Python {__version__}",
                **(default_headers or {}),
            },
            default_query=default_query,
            http_client=http_client,
            _strict_response_validation=_strict_response_validation,
        )
        
        # Initialize chat with history support
        self.chat = Chat(self, enable_history=enable_history)
        
        # Initialize history manager
        self.history = HistoryManager(
            enabled=enable_history,
            persistence_file=history_file
        )
    
    @property
    @override
    def auth_headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.api_key}"}
    
    def create_conversation(self, conversation_id: str | None = None) -> ConversationHistory:
        """
        Create a new conversation with history tracking
        
        Args:
            conversation_id: Optional ID for the conversation
            
        Returns:
            ConversationHistory object
        """
        return self.history.create_conversation(conversation_id)
    
    def get_conversation(self, conversation_id: str) -> ConversationHistory | None:
        """
        Get an existing conversation by ID
        
        Args:
            conversation_id: The conversation ID
            
        Returns:
            ConversationHistory object or None if not found
        """
        return self.history.get_conversation(conversation_id)
    
    def list_conversations(self) -> List[str]:
        """
        List all conversation IDs
        
        Returns:
            List of conversation IDs
        """
        return self.history.list_conversations()
    
    def get_conversation_context(
        self,
        conversation_id: str | None = None,
        messages: List[Dict[str, Any]] | None = None,
        max_messages: int | None = None
    ) -> List[Dict[str, Any]]:
        """
        Get conversation messages properly formatted for model context
        
        Args:
            conversation_id: ID of conversation to get context for
            messages: Or provide messages directly
            max_messages: Maximum number of recent messages to include
            
        Returns:
            List of messages formatted for model consumption
        """
        if conversation_id:
            conv = self.get_conversation(conversation_id)
            if not conv:
                raise ValueError(f"Conversation {conversation_id} not found")
            conversation_messages = conv.get_messages()
        elif messages:
            conversation_messages = messages
        else:
            return []
        
        # Apply message limit if specified
        if max_messages and len(conversation_messages) > max_messages:
            conversation_messages = conversation_messages[-max_messages:]
        
        # Format messages for model context
        formatted_messages = []
        for msg in conversation_messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            # Only include user, assistant, and system messages
            if role in ("user", "assistant", "system"):
                formatted_messages.append({
                    "role": role,
                    "content": content
                })
        
        return formatted_messages
    
    def send_message(
        self,
        message: str,
        conversation_id: str | None = None,
        max_history: int | None = None,
        **kwargs: Any
    ) -> str:
        """
        Send a message in a conversation with proper history aggregation
        
        Args:
            message: User message to send
            conversation_id: ID of conversation to use
            max_history: Maximum number of previous messages to include as context
            **kwargs: Additional parameters for chat completion
            
        Returns:
            Assistant's response
        """
        # Get or create conversation
        if conversation_id:
            conv = self.get_conversation(conversation_id)
            if not conv:
                conv = self.create_conversation(conversation_id)
        else:
            # If no conversation_id provided, try to use the most recent conversation
            # or create a new one if none exist
            existing_conversations = self.list_conversations()
            if existing_conversations:
                # Use the most recent conversation
                conversation_id = existing_conversations[-1]
                conv = self.get_conversation(conversation_id)
            else:
                # Create new conversation
                conv = self.create_conversation()
                conversation_id = conv.id
        
        # Get conversation context
        context_messages = self.get_conversation_context(
            conversation_id=conversation_id,
            max_messages=max_history
        )
        
        # Add the new user message
        context_messages.append({"role": "user", "content": message})
        
        # Send to model with conversation context
        # Temporarily disable history tracking in completions to avoid duplicates
        orig_enable_history = self.chat.completions._enable_history
        self.chat.completions._enable_history = False
        
        try:
            response = self.chat.completions.create(
                messages=context_messages,
                conversation_id=conversation_id,
                **kwargs
            )
        finally:
            # Restore original history setting
            self.chat.completions._enable_history = orig_enable_history
        
        assistant_message = response.choices[0].message.content
        
        # Add both messages to conversation history
        conv.add_message("user", message)
        conv.add_message("assistant", assistant_message)
        
        return assistant_message
    
    def get_models(self) -> ModelList:
        """
        Get list of available models
        
        Returns:
            ModelList: Available models with metadata
        """
        response = self.get("/models")
        return ModelList.model_validate(response)
    
    def get_model_info(self, model_id: str = None) -> Model:
        """
        Get information about a specific model or current default model
        
        Args:
            model_id: Specific model ID to get info for. If None, uses default model.
            
        Returns:
            Model: Basic model information
        """
        if model_id is None:
            model_id = "wizard"  # Default model
            
        # Get all models and find the specified one
        models = self.get_models()
        
        for model in models.data:
            if model.id == model_id:
                return model
                
        raise ValueError(f"Model '{model_id}' not found. Available models: {[m.id for m in models.data[:5]]}...")
    
    def get_model_capabilities(self, model_id: str = None) -> ModelCapabilities:
        """
        Get capabilities and parameter information for a model
        
        Args:
            model_id: Model ID to get capabilities for. If None, uses default model.
            
        Returns:
            ModelCapabilities: Model capabilities and parameter ranges
        """
        if model_id is None:
            model_id = "wizard"
            
        return ModelCapabilities.from_model_id(model_id)
    
    def get_parameter_info(self) -> ParameterInfo:
        """
        Get information about supported parameters for chat completions
        
        Returns:
            ParameterInfo: Parameter descriptions and usage info
        """
        return ParameterInfo()
    
    def get_usage_from_response(self, response) -> UsageInfo | None:
        """
        Extract usage information from a completion response
        
        Args:
            response: Response from chat.completions.create()
            
        Returns:
            UsageInfo: Usage statistics if available
        """
        if hasattr(response, 'usage') and response.usage:
            return UsageInfo.model_validate(response.usage.model_dump())
        return None
    
    def list_available_models(self, category: str = None) -> List[str]:
        """
        Get a simple list of available model IDs, optionally filtered by category
        
        Args:
            category: Filter models by category ('vision', 'audio', 'coding', 'reasoning', 'large')
            
        Returns:
            List of model IDs
        """
        models = self.get_models()
        model_ids = [model.id for model in models.data]
        
        if not category:
            return sorted(model_ids)
            
        # Filter by category
        category_lower = category.lower()
        filtered_models = []
        
        for model_id in model_ids:
            model_lower = model_id.lower()
            
            if category_lower == 'vision' and any(kw in model_lower for kw in ['vision', 'llava', 'multimodal']):
                filtered_models.append(model_id)
            elif category_lower == 'audio' and any(kw in model_lower for kw in ['voice', 'tts', 'stt', 'audio']):
                filtered_models.append(model_id)
            elif category_lower == 'coding' and any(kw in model_lower for kw in ['coder', 'code']):
                filtered_models.append(model_id)
            elif category_lower == 'reasoning' and any(kw in model_lower for kw in ['thinking', 'reasoning', 'r1']):
                filtered_models.append(model_id)
            elif category_lower == 'large' and any(kw in model_lower for kw in ['405b', '235b', '120b']):
                filtered_models.append(model_id)
                
        return sorted(filtered_models)
    
    def export_conversation(
        self,
        conversation_id: str,
        format: str = "json"
    ) -> Union[str, Dict[str, Any]]:
        """
        Export a conversation history in various formats
        
        Args:
            conversation_id: The conversation ID
            format: Export format (json, text, markdown, messages)
            
        Returns:
            Exported conversation data
        """
        conv = self.get_conversation(conversation_id)
        if not conv:
            raise ValueError(f"Conversation {conversation_id} not found")
        
        if format == "json":
            return conv.to_dict()
        elif format == "messages":
            # Return raw messages for model context
            return self.get_conversation_context(conversation_id=conversation_id)
        elif format == "text":
            lines = []
            for msg in conv.get_messages():
                role = msg.get("role", "unknown")
                content = msg.get("content", "")
                lines.append(f"{role.capitalize()}: {content}")
            return "\n".join(lines)
        elif format == "markdown":
            lines = [f"# Conversation {conversation_id}", ""]
            lines.append(f"**Started:** {conv.created_at}")
            lines.append(f"**Messages:** {conv.message_count}")
            lines.append("")
            
            for msg in conv.get_messages():
                role = msg.get("role", "unknown")
                content = msg.get("content", "")
                lines.append(f"### {role.capitalize()}")
                lines.append(content)
                lines.append("")
            
            return "\n".join(lines)
        else:
            raise ValueError(f"Unsupported format: {format}. Use: json, text, markdown, messages")
    
    def copy(
        self,
        *,
        api_key: str | None = None,
        organization: str | None = None,
        project: str | None = None,
        base_url: str | httpx.URL | None = None,
        timeout: float | httpx.Timeout | None = None,
        http_client: httpx.Client | None = None,
        max_retries: int | None = None,
        default_headers: Mapping[str, str] | None = None,
        enable_history: bool | None = None,
    ) -> Tela:
        """
        Create a new client instance with different options
        """
        return self.__class__(
            api_key=api_key or self.api_key,
            organization=organization or self.organization,
            project=project or self.project,
            base_url=base_url or self.base_url,
            timeout=timeout or self.timeout,
            http_client=http_client or self._client,
            max_retries=max_retries or self.max_retries,
            default_headers={**self._custom_headers, **(default_headers or {})},
            enable_history=enable_history if enable_history is not None else self.history.enabled,
        )
    
    with_options = copy
    
    def __enter__(self) -> Tela:
        return self
    
    def __exit__(self, *args: Any) -> None:
        self.history.save()  # Save history on exit
        self.close()


class AsyncTela(AsyncAPIClient):
    """
    Async Tela/Fabric API Client with conversation history support
    """
    
    chat: AsyncChat
    history: HistoryManager
    
    def __init__(
        self,
        *,
        api_key: str | None = None,
        organization: str | None = None,
        project: str | None = None,
        base_url: str | httpx.URL | None = None,
        timeout: float | httpx.Timeout | None = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        default_headers: Mapping[str, str] | None = None,
        default_query: Mapping[str, object] | None = None,
        http_client: httpx.AsyncClient | None = None,
        enable_history: bool = True,
        history_file: str | None = None,
        _strict_response_validation: bool = False,
    ) -> None:
        """Initialize async client with history support"""
        
        if api_key is None:
            api_key = os.environ.get("TELAOS_API_KEY")
        if api_key is None:
            raise AuthenticationError(
                "The api_key client option must be set either by passing api_key to the client or "
                "by setting the TELAOS_API_KEY environment variable"
            )
        self.api_key = api_key
        
        if organization is None:
            organization = os.environ.get("TELAOS_ORG_ID")
        if organization is None or organization == "":
            raise AuthenticationError(
                "The organization client option must be set either by passing organization to the client or "
                "by setting the TELAOS_ORG_ID environment variable"
            )
        self.organization = organization
        
        if project is None:
            project = os.environ.get("TELAOS_PROJECT_ID")
        if project is None or project == "":
            raise AuthenticationError(
                "The project client option must be set either by passing project to the client or "
                "by setting the TELAOS_PROJECT_ID environment variable"
            )
        self.project = project
        
        if base_url is None:
            base_url = os.environ.get("TELA_BASE_URL", DEFAULT_BASE_URL)
        
        super().__init__(
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
            default_headers={
                "Authorization": f"Bearer {api_key}",
                "OpenAI-Organization": organization,
                "OpenAI-Project": project,
                "User-Agent": f"Tela/Python {__version__}",
                **(default_headers or {}),
            },
            default_query=default_query,
            http_client=http_client,
            _strict_response_validation=_strict_response_validation,
        )
        
        self.chat = AsyncChat(self, enable_history=enable_history)
        self.history = HistoryManager(
            enabled=enable_history,
            persistence_file=history_file
        )
    
    @property
    @override
    def auth_headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.api_key}"}
    
    def create_conversation(self, conversation_id: str | None = None) -> ConversationHistory:
        """Create a new conversation with history tracking"""
        return self.history.create_conversation(conversation_id)
    
    def get_conversation(self, conversation_id: str) -> ConversationHistory | None:
        """Get an existing conversation by ID"""
        return self.history.get_conversation(conversation_id)
    
    def list_conversations(self) -> List[str]:
        """List all conversation IDs"""
        return self.history.list_conversations()
    
    def get_conversation_context(
        self,
        conversation_id: str | None = None,
        messages: List[Dict[str, Any]] | None = None,
        max_messages: int | None = None
    ) -> List[Dict[str, Any]]:
        """Get conversation messages properly formatted for model context"""
        if conversation_id:
            conv = self.get_conversation(conversation_id)
            if not conv:
                raise ValueError(f"Conversation {conversation_id} not found")
            conversation_messages = conv.get_messages()
        elif messages:
            conversation_messages = messages
        else:
            return []
        
        # Apply message limit if specified
        if max_messages and len(conversation_messages) > max_messages:
            conversation_messages = conversation_messages[-max_messages:]
        
        # Format messages for model context
        formatted_messages = []
        for msg in conversation_messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            # Only include user, assistant, and system messages
            if role in ("user", "assistant", "system"):
                formatted_messages.append({
                    "role": role,
                    "content": content
                })
        
        return formatted_messages
    
    async def send_message(
        self,
        message: str,
        conversation_id: str | None = None,
        max_history: int | None = None,
        **kwargs: Any
    ) -> str:
        """Send a message in a conversation with proper history aggregation"""
        # Get or create conversation
        if conversation_id:
            conv = self.get_conversation(conversation_id)
            if not conv:
                conv = self.create_conversation(conversation_id)
        else:
            # If no conversation_id provided, try to use the most recent conversation
            # or create a new one if none exist
            existing_conversations = self.list_conversations()
            if existing_conversations:
                # Use the most recent conversation
                conversation_id = existing_conversations[-1]
                conv = self.get_conversation(conversation_id)
            else:
                # Create new conversation
                conv = self.create_conversation()
                conversation_id = conv.id
        
        # Get conversation context
        context_messages = self.get_conversation_context(
            conversation_id=conversation_id,
            max_messages=max_history
        )
        
        # Add the new user message
        context_messages.append({"role": "user", "content": message})
        
        # Send to model with conversation context
        # Temporarily disable history tracking in completions to avoid duplicates
        orig_enable_history = self.chat.completions._enable_history
        self.chat.completions._enable_history = False
        
        try:
            response = await self.chat.completions.create(
                messages=context_messages,
                conversation_id=conversation_id,
                **kwargs
            )
        finally:
            # Restore original history setting
            self.chat.completions._enable_history = orig_enable_history
        
        assistant_message = response.choices[0].message.content
        
        # Add both messages to conversation history
        conv.add_message("user", message)
        conv.add_message("assistant", assistant_message)
        
        return assistant_message
    
    async def get_models(self) -> ModelList:
        """
        Get list of available models
        
        Returns:
            ModelList: Available models with metadata
        """
        response = await self.get("/models")
        return ModelList.model_validate(response)
    
    async def get_model_info(self, model_id: str = None) -> Model:
        """
        Get information about a specific model or current default model
        
        Args:
            model_id: Specific model ID to get info for. If None, uses default model.
            
        Returns:
            Model: Basic model information
        """
        if model_id is None:
            model_id = "wizard"  # Default model
            
        # Get all models and find the specified one
        models = await self.get_models()
        
        for model in models.data:
            if model.id == model_id:
                return model
                
        raise ValueError(f"Model '{model_id}' not found. Available models: {[m.id for m in models.data[:5]]}...")
    
    def get_model_capabilities(self, model_id: str = None) -> ModelCapabilities:
        """
        Get capabilities and parameter information for a model
        
        Args:
            model_id: Model ID to get capabilities for. If None, uses default model.
            
        Returns:
            ModelCapabilities: Model capabilities and parameter ranges
        """
        if model_id is None:
            model_id = "wizard"
            
        return ModelCapabilities.from_model_id(model_id)
    
    def get_parameter_info(self) -> ParameterInfo:
        """
        Get information about supported parameters for chat completions
        
        Returns:
            ParameterInfo: Parameter descriptions and usage info
        """
        return ParameterInfo()
    
    def get_usage_from_response(self, response) -> UsageInfo | None:
        """
        Extract usage information from a completion response
        
        Args:
            response: Response from chat.completions.create()
            
        Returns:
            UsageInfo: Usage statistics if available
        """
        if hasattr(response, 'usage') and response.usage:
            return UsageInfo.model_validate(response.usage.model_dump())
        return None
    
    async def list_available_models(self, category: str = None) -> List[str]:
        """
        Get a simple list of available model IDs, optionally filtered by category
        
        Args:
            category: Filter models by category ('vision', 'audio', 'coding', 'reasoning', 'large')
            
        Returns:
            List of model IDs
        """
        models = await self.get_models()
        model_ids = [model.id for model in models.data]
        
        if not category:
            return sorted(model_ids)
            
        # Filter by category
        category_lower = category.lower()
        filtered_models = []
        
        for model_id in model_ids:
            model_lower = model_id.lower()
            
            if category_lower == 'vision' and any(kw in model_lower for kw in ['vision', 'llava', 'multimodal']):
                filtered_models.append(model_id)
            elif category_lower == 'audio' and any(kw in model_lower for kw in ['voice', 'tts', 'stt', 'audio']):
                filtered_models.append(model_id)
            elif category_lower == 'coding' and any(kw in model_lower for kw in ['coder', 'code']):
                filtered_models.append(model_id)
            elif category_lower == 'reasoning' and any(kw in model_lower for kw in ['thinking', 'reasoning', 'r1']):
                filtered_models.append(model_id)
            elif category_lower == 'large' and any(kw in model_lower for kw in ['405b', '235b', '120b']):
                filtered_models.append(model_id)
                
        return sorted(filtered_models)
    
    def export_conversation(
        self,
        conversation_id: str,
        format: str = "json"
    ) -> Union[str, Dict[str, Any]]:
        """Export a conversation history in various formats"""
        conv = self.get_conversation(conversation_id)
        if not conv:
            raise ValueError(f"Conversation {conversation_id} not found")
        
        if format == "json":
            return conv.to_dict()
        elif format == "messages":
            # Return raw messages for model context
            return self.get_conversation_context(conversation_id=conversation_id)
        elif format == "text":
            lines = []
            for msg in conv.get_messages():
                role = msg.get("role", "unknown")
                content = msg.get("content", "")
                lines.append(f"{role.capitalize()}: {content}")
            return "\n".join(lines)
        elif format == "markdown":
            lines = [f"# Conversation {conversation_id}", ""]
            lines.append(f"**Started:** {conv.created_at}")
            lines.append(f"**Messages:** {conv.message_count}")
            lines.append("")
            
            for msg in conv.get_messages():
                role = msg.get("role", "unknown")
                content = msg.get("content", "")
                lines.append(f"### {role.capitalize()}")
                lines.append(content)
                lines.append("")
            
            return "\n".join(lines)
        else:
            raise ValueError(f"Unsupported format: {format}. Use: json, text, markdown, messages")
    
    def copy(
        self,
        *,
        api_key: str | None = None,
        organization: str | None = None,
        project: str | None = None,
        base_url: str | httpx.URL | None = None,
        timeout: float | httpx.Timeout | None = None,
        http_client: httpx.AsyncClient | None = None,
        max_retries: int | None = None,
        default_headers: Mapping[str, str] | None = None,
        enable_history: bool | None = None,
    ) -> AsyncTela:
        """Create a new client instance with different options"""
        return self.__class__(
            api_key=api_key or self.api_key,
            organization=organization or self.organization,
            project=project or self.project,
            base_url=base_url or self.base_url,
            timeout=timeout or self.timeout,
            http_client=http_client or self._client,
            max_retries=max_retries or self.max_retries,
            default_headers={**self._custom_headers, **(default_headers or {})},
            enable_history=enable_history if enable_history is not None else self.history.enabled,
        )
    
    with_options = copy
    
    async def __aenter__(self) -> AsyncTela:
        return self
    
    async def __aexit__(self, *args: Any) -> None:
        self.history.save()
        await self.close()


# Convenience exports
Client = Tela
AsyncClient = AsyncTela