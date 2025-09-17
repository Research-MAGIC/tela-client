from __future__ import annotations

import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


class ConversationHistory(BaseModel):
    """
    Represents a conversation with history tracking capabilities
    
    Uses Pydantic v2 for validation and serialization with Python 3.9+ compatibility
    """
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    messages: List[Dict[str, Any]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    model_config = {"arbitrary_types_allowed": True}
    
    def add_message(
        self,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Add a message to the conversation history
        
        Args:
            role: The message role (system, user, assistant, etc.)
            content: The message content
            metadata: Optional metadata for the message
        """
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        if metadata:
            message["metadata"] = metadata
            
        self.messages.append(message)
        self.updated_at = datetime.utcnow()
    
    def get_messages(self, role_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get messages from the conversation, optionally filtered by role
        
        Args:
            role_filter: Optional role to filter messages by
            
        Returns:
            List of message dictionaries
        """
        if role_filter:
            return [msg for msg in self.messages if msg.get("role") == role_filter]
        return self.messages.copy()
    
    @property
    def message_count(self) -> int:
        """Get the total number of messages in the conversation"""
        return len(self.messages)
    
    @property
    def last_message(self) -> Optional[Dict[str, Any]]:
        """Get the last message in the conversation"""
        return self.messages[-1] if self.messages else None
    
    def clear_messages(self) -> None:
        """Clear all messages from the conversation"""
        self.messages.clear()
        self.updated_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the conversation to a dictionary for serialization
        
        Returns:
            Dictionary representation of the conversation
        """
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "messages": self.messages,
            "metadata": self.metadata,
            "message_count": self.message_count
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ConversationHistory:
        """
        Create a ConversationHistory from a dictionary
        
        Args:
            data: Dictionary containing conversation data
            
        Returns:
            ConversationHistory instance
        """
        # Handle datetime parsing for backwards compatibility
        if isinstance(data.get("created_at"), str):
            data["created_at"] = datetime.fromisoformat(data["created_at"].replace('Z', '+00:00'))
        if isinstance(data.get("updated_at"), str):
            data["updated_at"] = datetime.fromisoformat(data["updated_at"].replace('Z', '+00:00'))
            
        return cls(**data)


class HistoryManager:
    """
    Manages multiple conversation histories with persistence capabilities
    
    Features:
    - In-memory conversation storage
    - Optional file-based persistence
    - Thread-safe operations
    - Automatic cleanup of old conversations
    """
    
    def __init__(
        self,
        enabled: bool = True,
        persistence_file: Optional[str] = None,
        max_conversations: int = 1000,
        client: Optional[Any] = None,
        server_sync: bool = False
    ) -> None:
        """
        Initialize the history manager

        Args:
            enabled: Whether history tracking is enabled
            persistence_file: Optional file path for persisting history
            max_conversations: Maximum number of conversations to keep in memory
            client: Optional Tela client for server-side chat management
            server_sync: Whether to sync conversations with server-side chat management
        """
        self.enabled = enabled
        self.persistence_file = persistence_file
        self.max_conversations = max_conversations
        self._conversations: Dict[str, ConversationHistory] = {}
        self._client = client
        self.server_sync = server_sync and client is not None

        if self.enabled and self.persistence_file:
            self._load_from_file()
    
    def create_conversation(
        self,
        conversation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ConversationHistory:
        """
        Create a new conversation
        
        Args:
            conversation_id: Optional custom ID for the conversation
            metadata: Optional metadata for the conversation
            
        Returns:
            New ConversationHistory instance
        """
        if not self.enabled:
            # Return a temporary conversation that won't be persisted
            return ConversationHistory(
                id=conversation_id or str(uuid.uuid4()),
                metadata=metadata or {}
            )
        
        conv = ConversationHistory(
            id=conversation_id or str(uuid.uuid4()),
            metadata=metadata or {}
        )
        
        self._conversations[conv.id] = conv
        self._cleanup_old_conversations()
        
        return conv
    
    def get_conversation(self, conversation_id: str) -> Optional[ConversationHistory]:
        """
        Retrieve a conversation by ID
        
        Args:
            conversation_id: The conversation ID to retrieve
            
        Returns:
            ConversationHistory instance or None if not found
        """
        if not self.enabled:
            return None
            
        return self._conversations.get(conversation_id)
    
    def list_conversations(self) -> List[str]:
        """
        List all conversation IDs
        
        Returns:
            List of conversation IDs
        """
        if not self.enabled:
            return []
            
        return list(self._conversations.keys())
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """
        Delete a conversation by ID
        
        Args:
            conversation_id: The conversation ID to delete
            
        Returns:
            True if deleted, False if not found
        """
        if not self.enabled:
            return False
            
        if conversation_id in self._conversations:
            del self._conversations[conversation_id]
            return True
        return False
    
    def clear_all_conversations(self) -> None:
        """Clear all conversations from memory"""
        if self.enabled:
            self._conversations.clear()
    
    def save(self) -> None:
        """Save conversations to persistence file if configured"""
        if not self.enabled or not self.persistence_file:
            return
            
        try:
            # Create directory if it doesn't exist
            Path(self.persistence_file).parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                "conversations": {
                    conv_id: conv.to_dict() 
                    for conv_id, conv in self._conversations.items()
                },
                "saved_at": datetime.utcnow().isoformat()
            }
            
            with open(self.persistence_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            # Fail silently to avoid breaking client operations
            pass
    
    def _load_from_file(self) -> None:
        """Load conversations from persistence file"""
        if not os.path.exists(self.persistence_file):
            return
            
        try:
            with open(self.persistence_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            conversations_data = data.get("conversations", {})
            for conv_id, conv_data in conversations_data.items():
                try:
                    conv = ConversationHistory.from_dict(conv_data)
                    self._conversations[conv_id] = conv
                except Exception:
                    # Skip corrupted conversation data
                    continue
                    
        except Exception:
            # Fail silently if file is corrupted
            pass
    
    def _cleanup_old_conversations(self) -> None:
        """Remove oldest conversations if limit exceeded"""
        if len(self._conversations) <= self.max_conversations:
            return
            
        # Sort by updated_at and remove oldest
        sorted_convs = sorted(
            self._conversations.items(),
            key=lambda x: x[1].updated_at
        )
        
        to_remove = len(self._conversations) - self.max_conversations
        for i in range(to_remove):
            conv_id, _ = sorted_convs[i]
            del self._conversations[conv_id]
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the history manager
        
        Returns:
            Dictionary with statistics
        """
        if not self.enabled:
            return {"enabled": False}
            
        total_messages = sum(conv.message_count for conv in self._conversations.values())
        
        return {
            "enabled": True,
            "total_conversations": len(self._conversations),
            "total_messages": total_messages,
            "persistence_enabled": bool(self.persistence_file),
            "persistence_file": self.persistence_file,
            "max_conversations": self.max_conversations,
            "server_sync": self.server_sync
        }

    def sync_with_server(self) -> Dict[str, Any]:
        """
        Sync local conversations with server-side chat management

        Returns:
            Dictionary with sync statistics
        """
        if not self.server_sync or not hasattr(self._client, 'chats'):
            return {"synced": False, "reason": "Server sync not enabled or client not available"}

        try:
            # Get server-side chats
            server_chats = self._client.chats.list(page_size=100)
            synced_count = 0
            errors = []

            # Check if we got an empty response due to endpoint unavailability
            if not server_chats.data and server_chats.total == 0:
                return {
                    "synced": True,
                    "synced_count": 0,
                    "total_server_chats": 0,
                    "errors": ["Server chat endpoints may not be available"],
                    "note": "Graceful degradation - no server chats available"
                }

            for server_chat in server_chats.data:
                try:
                    # Check if we already have this conversation
                    chat_id = getattr(server_chat, 'chat_id', getattr(server_chat, 'id', None))
                    if not chat_id:
                        continue

                    local_conv = self.get_conversation(chat_id)
                    if not local_conv:
                        # Create local conversation from server chat
                        # Use current time if server doesn't provide timestamps
                        created_at = getattr(server_chat, 'created_at', None) or datetime.utcnow()
                        updated_at = getattr(server_chat, 'updated_at', None) or datetime.utcnow()

                        local_conv = ConversationHistory(
                            id=chat_id,
                            created_at=created_at,
                            updated_at=updated_at,
                            metadata={
                                "server_title": getattr(server_chat, 'title', None),
                                "server_metadata": getattr(server_chat, 'metadata', None),
                                "synced_from_server": True
                            }
                        )
                        self._conversations[chat_id] = local_conv
                        synced_count += 1
                except Exception as e:
                    chat_id_for_error = getattr(server_chat, 'chat_id', getattr(server_chat, 'id', 'unknown'))
                    errors.append(f"Error syncing chat {chat_id_for_error}: {str(e)}")

            return {
                "synced": True,
                "synced_count": synced_count,
                "total_server_chats": len(server_chats.data),
                "errors": errors
            }

        except Exception as e:
            return {"synced": False, "reason": f"Sync failed: {str(e)}"}

    def create_server_chat(
        self,
        conversation_id: Optional[str] = None,
        module_id: str = "chat",
        message: str = ""
    ) -> Optional[str]:
        """
        Create a new chat on the server and optionally sync locally

        Args:
            conversation_id: Optional conversation ID (for local tracking)
            module_id: Module ID for the chat (default: "chat")
            message: Initial message content (default: "")

        Returns:
            Chat ID if created successfully, None otherwise
        """
        if not self.server_sync or not hasattr(self._client, 'chats'):
            return None

        try:
            server_response = self._client.chats.create(
                module_id=module_id,
                message=message
            )

            # Extract chat_id from response
            chat_id = server_response.get("chat_id")
            if not chat_id:
                return None

            # Check if this is a local fallback chat ID
            is_local_fallback = chat_id.startswith("local_")

            # Create local conversation if requested
            if conversation_id or self.enabled:
                local_conv = ConversationHistory(
                    id=chat_id,
                    metadata={
                        "server_module_id": module_id,
                        "server_initial_message": message,
                        "synced_with_server": not is_local_fallback,
                        "local_fallback": is_local_fallback
                    }
                )
                if self.enabled:
                    self._conversations[chat_id] = local_conv

            return chat_id

        except Exception:
            return None