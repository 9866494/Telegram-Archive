"""
Base database adapter interface

This module defines the abstract base class for all database adapters.
All adapters must implement these methods to ensure compatibility.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple

from .models import Chat, Message, User, Media, Reaction, SyncStatus, Metadata


class DatabaseAdapter(ABC):
    """
    Abstract base class for database adapters.

    Provides a unified interface for database operations regardless of the
    underlying database implementation (SQLite direct or SQLAlchemy-based).
    """

    @abstractmethod
    def initialize_schema(self) -> None:
        """
        Initialize database schema if not exists.
        This should create all necessary tables.
        """
        pass

    @abstractmethod
    def close(self) -> None:
        """
        Close database connection and cleanup resources.
        """
        pass

    # Chat operations
    @abstractmethod
    def upsert_chat(self, chat_data: Dict[str, Any]) -> None:
        """
        Insert or update a chat record.

        Args:
            chat_data: Dictionary with chat information
        """
        pass

    @abstractmethod
    def get_chat(self, chat_id: int) -> Optional[Dict[str, Any]]:
        """
        Get chat by ID.

        Args:
            chat_id: Telegram chat ID

        Returns:
            Dictionary with chat data or None if not found
        """
        pass

    @abstractmethod
    def get_all_chats(self, include_empty: bool = False, order_by: str = "last_message_date") -> List[Dict[str, Any]]:
        """
        Get all chats with optional filtering and ordering.

        Args:
            include_empty: Include chats without messages
            order_by: Field to order by

        Returns:
            List of chat dictionaries
        """
        pass

    @abstractmethod
    def delete_chat(self, chat_id: int) -> bool:
        """
        Delete a chat and all related data.

        Args:
            chat_id: Telegram chat ID

        Returns:
            True if deleted, False if not found
        """
        pass

    # Message operations
    @abstractmethod
    def insert_messages(self, messages: List[Dict[str, Any]]) -> None:
        """
        Insert multiple messages in batch.

        Args:
            messages: List of message dictionaries
        """
        pass

    @abstractmethod
    def get_messages(self, chat_id: int, limit: int = 100, offset: int = 0,
                    search_query: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get messages from a chat with pagination.

        Args:
            chat_id: Telegram chat ID
            limit: Number of messages to return
            offset: Number of messages to skip
            search_query: Optional text search

        Returns:
            List of message dictionaries
        """
        pass

    @abstractmethod
    def get_message_count(self, chat_id: int, search_query: Optional[str] = None) -> int:
        """
        Get total message count for a chat.

        Args:
            chat_id: Telegram chat ID
            search_query: Optional text search

        Returns:
            Number of messages
        """
        pass

    @abstractmethod
    def get_last_synced_message_id(self, chat_id: int) -> int:
        """
        Get ID of the last synced message for a chat.

        Args:
            chat_id: Telegram chat ID

        Returns:
            Last message ID or 0 if none
        """
        pass

    # User operations
    @abstractmethod
    def upsert_user(self, user_data: Dict[str, Any]) -> None:
        """
        Insert or update a user record.

        Args:
            user_data: Dictionary with user information
        """
        pass

    @abstractmethod
    def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Get user by ID.

        Args:
            user_id: Telegram user ID

        Returns:
            Dictionary with user data or None if not found
        """
        pass

    # Media operations
    @abstractmethod
    def upsert_media(self, media_data: Dict[str, Any]) -> None:
        """
        Insert or update a media record.

        Args:
            media_data: Dictionary with media information
        """
        pass

    @abstractmethod
    def get_media_by_chat(self, chat_id: int, media_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get media files for a chat.

        Args:
            chat_id: Telegram chat ID
            media_type: Optional filter by media type

        Returns:
            List of media dictionaries
        """
        pass

    @abstractmethod
    def get_media_stats(self) -> Dict[str, Any]:
        """
        Get media statistics.

        Returns:
            Dictionary with stats (count, total_size, etc.)
        """
        pass

    # Reaction operations
    @abstractmethod
    def insert_reactions(self, reactions: List[Dict[str, Any]]) -> None:
        """
        Insert message reactions.

        Args:
            reactions: List of reaction dictionaries
        """
        pass

    # Sync status operations
    @abstractmethod
    def update_sync_status(self, chat_id: int, last_message_id: int,
                          message_count: int) -> None:
        """
        Update synchronization status for a chat.

        Args:
            chat_id: Telegram chat ID
            last_message_id: Last message ID synced
            message_count: Total message count
        """
        pass

    # Metadata operations
    @abstractmethod
    def get_metadata(self, key: str) -> Optional[str]:
        """
        Get metadata value by key.

        Args:
            key: Metadata key

        Returns:
            Value or None if not found
        """
        pass

    @abstractmethod
    def set_metadata(self, key: str, value: str) -> None:
        """
        Set metadata value.

        Args:
            key: Metadata key
            value: Metadata value
        """
        pass

    # Statistics
    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """
        Get overall database statistics.

        Returns:
            Dictionary with stats (chats, messages, users, media, etc.)
        """
        pass

    # Export
    @abstractmethod
    def export_chat(self, chat_id: int) -> Optional[Dict[str, Any]]:
        """
        Export all data for a chat.

        Args:
            chat_id: Telegram chat ID

        Returns:
            Dictionary with all chat data or None if not found
        """
        pass