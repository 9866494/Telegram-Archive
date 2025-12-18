"""
Database adapters for Telegram Archive

This package provides database adapters using SQLAlchemy ORM to support
both SQLite and PostgreSQL databases while maintaining backward compatibility
with the existing sqlite3-based implementation.

Usage:
    from src.db_adapters.factory import create_database_adapter

    # SQLite adapter (new implementation)
    adapter = create_database_adapter(config)  # When config.db_type = "sqlite-alchemy"

    # PostgreSQL adapter
    adapter = create_database_adapter(config)  # When config.db_type = "postgres-alchemy"
"""

from .factory import create_database_adapter
from .adapter import DatabaseAdapter

__all__ = ["create_database_adapter", "DatabaseAdapter"]