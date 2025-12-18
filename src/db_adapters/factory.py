"""
Factory for creating database adapters

This module provides a factory function to create the appropriate
database adapter based on the configuration.
"""

import logging

from .adapter import DatabaseAdapter
from .sqlite_adapter import SQLiteAdapter
from .postgres_adapter import PostgreSQLAdapter

logger = logging.getLogger(__name__)


def create_database_adapter(config) -> DatabaseAdapter:
    """
    Factory function to create the appropriate database adapter.

    Args:
        config: Configuration object with database settings

    Returns:
        DatabaseAdapter: Instance of the appropriate adapter

    Supported db_type values:
        - "sqlite": Original sqlite3 implementation (from src.database)
        - "sqlite-alchemy": SQLite through SQLAlchemy adapter
        - "postgres-alchemy": PostgreSQL through SQLAlchemy adapter

    Example:
        >>> adapter = create_database_adapter(config)
        >>> adapter.initialize_schema()
    """
    db_type = getattr(config, "db_type", "sqlite").lower()

    logger.info(f"Creating database adapter for type: {db_type}")

    if db_type == "sqlite":
        # This should be handled by the main application logic
        # to use the original src.database.Database class
        raise ValueError(
            "For db_type='sqlite', use the original src.database.Database class. "
            "Set db_type='sqlite-alchemy' to use the SQLAlchemy SQLite adapter."
        )
    elif db_type == "sqlite-alchemy":
        return SQLiteAdapter(
            database_path=config.database_path,
            timeout=config.database_timeout
        )
    elif db_type == "postgres-alchemy":
        # Get PostgreSQL settings from config
        host = getattr(config, "postgres_host", "localhost")
        port = getattr(config, "postgres_port", 5432)
        database = getattr(config, "postgres_db", "telegram_backup")
        user = getattr(config, "postgres_user", "postgres")
        password = getattr(config, "postgres_password", "")
        pool_size = getattr(config, "postgres_pool_size", 5)

        if not password:
            raise ValueError("PostgreSQL password is required when using postgres-alchemy")

        return PostgreSQLAdapter(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password,
            pool_size=pool_size
        )
    else:
        raise ValueError(f"Unsupported database type: {db_type}")


def is_sqlalchemy_adapter(db_type: str) -> bool:
    """
    Check if the database type uses SQLAlchemy adapters.

    Args:
        db_type: Database type string

    Returns:
        True if using SQLAlchemy adapters, False otherwise
    """
    return db_type.lower() in ("sqlite-alchemy", "postgres-alchemy")