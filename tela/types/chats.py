from __future__ import annotations

from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime

__all__ = [
    "Chat",
    "ChatList",
    "ChatPaginatedResponse",
]


class Chat(BaseModel):
    """Represents a chat/conversation from the server-side chat management API"""
    chat_id: str  # The API returns chat_id, not id
    title: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    message_count: Optional[int] = None
    last_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    model_config = {"extra": "allow"}

    @property
    def id(self) -> str:
        """Alias for chat_id for backwards compatibility"""
        return self.chat_id


class ChatList(BaseModel):
    """List of chats"""
    data: List[Chat]

    model_config = {"extra": "allow"}


class ChatPaginatedResponse(BaseModel):
    """Paginated response for chat listings"""
    data: List[Chat]
    page: int
    page_size: int
    total_items: Optional[int] = None
    total_pages: Optional[int] = None
    has_next: Optional[bool] = None
    has_previous: Optional[bool] = None

    model_config = {"extra": "allow"}