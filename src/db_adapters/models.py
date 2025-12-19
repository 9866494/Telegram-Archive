"""
SQLAlchemy ORM models for Telegram Archive

These models define the database schema using SQLAlchemy declarative syntax.
They are compatible with both SQLite and PostgreSQL databases.

Note: Integer types in SQLite will be mapped to BIGINT in PostgreSQL
to support large Telegram IDs.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean, Column, DateTime, ForeignKey, Integer, String, Text,
    BigInteger, Index, text as sql_text
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

# Import schema configuration
from .schema import get_schema_name


class Chat(Base):
    """Chat information"""
    __tablename__ = "chats"

    # Set schema for PostgreSQL only (will be None for SQLite)
    schema = get_schema_name()
    __table_args__ = (
        Index('idx_chat_type', 'type'),
        Index('idx_chat_username', 'username'),
    )

    # Use BigInteger for PostgreSQL compatibility (Telegram IDs can be very large)
    id = Column(BigInteger, primary_key=True)
    type = Column(String(20), nullable=False)  # private, group, channel, etc.
    title = Column(String(255))
    username = Column(String(255))
    first_name = Column(String(255))
    last_name = Column(String(255))
    phone = Column(String(50))
    description = Column(Text)
    participants_count = Column(Integer)
    last_synced_message_id = Column(BigInteger, default=0)
    created_at = Column(DateTime, server_default=sql_text("CURRENT_TIMESTAMP"))
    updated_at = Column(DateTime, server_default=sql_text("CURRENT_TIMESTAMP"))

    # Relationships
    messages = relationship("Message", back_populates="chat", cascade="all, delete-orphan")
    media_files = relationship("Media", back_populates="chat", cascade="all, delete-orphan")
    sync_status = relationship("SyncStatus", back_populates="chat", uselist=False)


class Message(Base):
    """Message data"""
    __tablename__ = "messages"

    # Use single primary key for PostgreSQL compatibility
    # In SQLite, we'll create a unique index on (id, chat_id)
    id = Column(BigInteger, primary_key=True)
    chat_id = Column(BigInteger, ForeignKey("chats.id"), nullable=False)
    sender_id = Column(BigInteger)  # User who sent the message
    date = Column(DateTime, nullable=False)
    text = Column(Text)
    reply_to_msg_id = Column(BigInteger)
    reply_to_text = Column(Text)  # Cached reply text (truncated to 100 chars)
    forward_from_id = Column(BigInteger)
    edit_date = Column(DateTime)
    media_type = Column(String(50))  # photo, video, document, audio, voice, etc.
    media_id = Column(String(255))  # Telegram file ID or unique identifier
    media_path = Column(String(500))  # Local file path
    raw_data = Column(Text)  # Serialized poll data or other special content
    created_at = Column(DateTime, server_default=sql_text("CURRENT_TIMESTAMP"))
    is_outgoing = Column(Boolean, default=False)

    # Relationships
    chat = relationship("Chat", back_populates="messages")
    # media_files relationship removed due to lack of foreign key constraint
    # media_files = relationship("Media", back_populates="message", cascade="all, delete-orphan")
    reactions = relationship("Reaction", back_populates="message", cascade="all, delete-orphan")

    # Set schema for PostgreSQL only (will be None for SQLite)
    schema = get_schema_name()
    __table_args__ = (
        Index('idx_message_chat_date', 'chat_id', 'date'),
        Index('idx_message_sender', 'sender_id'),
        Index('idx_message_media', 'media_type'),
        # Unique index on (id, chat_id) for SQLite compatibility
        # PostgreSQL will have id as primary key, SQLite uses (id, chat_id) as unique
        Index('uq_message_id_chat', 'id', 'chat_id', unique=True),
        {'schema': schema} if schema else {}
    )


class User(Base):
    """User information"""
    __tablename__ = "users"

    # Set schema for PostgreSQL only (will be None for SQLite)
    schema = get_schema_name()
    __table_args__ = (
        Index('idx_user_username', 'username'),
        Index('idx_user_phone', 'phone'),
        {'schema': schema} if schema else {}
    )

    id = Column(BigInteger, primary_key=True)
    username = Column(String(255))
    first_name = Column(String(255))
    last_name = Column(String(255))
    phone = Column(String(50))
    is_bot = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=sql_text("CURRENT_TIMESTAMP"))
    updated_at = Column(DateTime, server_default=sql_text("CURRENT_TIMESTAMP"))


class Media(Base):
    """Media file information"""
    __tablename__ = "media"

    id = Column(String(255), primary_key=True)  # Telegram file_id or unique identifier
    message_id = Column(BigInteger)
    chat_id = Column(BigInteger, ForeignKey("chats.id"))
    type = Column(String(50))  # photo, video, document, audio, voice, etc.
    file_path = Column(String(500))  # Local storage path
    file_name = Column(String(255))  # Original filename
    file_size = Column(BigInteger)
    mime_type = Column(String(100))
    width = Column(Integer)  # For photos and videos
    height = Column(Integer)  # For photos and videos
    duration = Column(Integer)  # For audio and video
    downloaded = Column(Boolean, default=False)
    download_date = Column(DateTime)
    created_at = Column(DateTime, server_default=sql_text("CURRENT_TIMESTAMP"))

    # Relationships
    # message relationship removed due to lack of foreign key constraint
    # message = relationship("Message", back_populates="media_files")
    chat = relationship("Chat", back_populates="media_files")

    # Set schema for PostgreSQL only (will be None for SQLite)
    schema = get_schema_name()
    __table_args__ = (
        Index('idx_media_type', 'type'),
        Index('idx_media_downloaded', 'downloaded'),
        {'schema': schema} if schema else {}
    )


class Reaction(Base):
    """Message reactions"""
    __tablename__ = "reactions"

    id = Column(BigInteger, primary_key=True)  # Auto-increment ID
    message_id = Column(BigInteger, ForeignKey("messages.id"), nullable=False)
    chat_id = Column(BigInteger, ForeignKey("chats.id"), nullable=False)
    emoji = Column(String(100), nullable=False)
    user_id = Column(BigInteger)  # If reaction is from a specific user
    count = Column(Integer, default=1)  # If reaction is aggregated
    created_at = Column(DateTime, server_default=sql_text("CURRENT_TIMESTAMP"))

    # Relationships
    message = relationship("Message", back_populates="reactions")

    # Set schema for PostgreSQL only (will be None for SQLite)
    schema = get_schema_name()
    __table_args__ = (
        Index('idx_reaction_message', 'message_id'),
        Index('idx_reaction_emoji', 'emoji'),
        {'schema': schema} if schema else {}
    )


class SyncStatus(Base):
    """Synchronization status for each chat"""
    __tablename__ = "sync_status"

    # Set schema for PostgreSQL only (will be None for SQLite)
    schema = get_schema_name()
    __table_args__ = (
        Index('idx_sync_date', 'last_sync_date'),
        {'schema': schema} if schema else {}
    )

    chat_id = Column(BigInteger, ForeignKey("chats.id"), primary_key=True)
    last_message_id = Column(BigInteger, default=0)
    last_sync_date = Column(DateTime, server_default=sql_text("CURRENT_TIMESTAMP"))
    message_count = Column(Integer, default=0)

    # Relationships
    chat = relationship("Chat", back_populates="sync_status")


class Metadata(Base):
    """Application metadata"""
    __tablename__ = "metadata"

    # Set schema for PostgreSQL only (will be None for SQLite)
    schema = get_schema_name()
    __table_args__ = (
        Index('idx_metadata_key', 'key'),
        {'schema': schema} if schema else {}
    )

    key = Column(String(100), primary_key=True)
    value = Column(Text)