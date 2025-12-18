#!/usr/bin/env python3
"""
Migrate SQLite database to PostgreSQL

This script migrates data from the existing SQLite database
to a new PostgreSQL database using SQLAlchemy adapters.

Usage:
    python -m src.migrate_to_postgres
"""

import os
import sys
import logging
from datetime import datetime
from typing import Dict, List, Any

# Add src to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from config import Config
from database import Database as SQLiteDatabase
from db_adapters.factory import create_database_adapter, is_sqlalchemy_adapter
from db_adapters.sqlite_adapter import SQLiteAdapter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DataMigrator:
    """Handles migration from SQLite to PostgreSQL."""

    def __init__(self, sqlite_db_path: str, pg_config):
        """
        Initialize migrator.

        Args:
            sqlite_db_path: Path to SQLite database
            pg_config: PostgreSQL configuration
        """
        self.sqlite_db = SQLiteDatabase(sqlite_db_path)

        # Create PostgreSQL adapter
        from config import Config
        config = Config()
        config.db_type = "postgres-alchemy"
        config.postgres_host = pg_config["host"]
        config.postgres_port = pg_config["port"]
        config.postgres_db = pg_config["database"]
        config.postgres_user = pg_config["user"]
        config.postgres_password = pg_config["password"]

        self.pg_adapter = create_database_adapter(config)
        self.pg_adapter.initialize_schema()

        logger.info(f"Initialized migrator: {sqlite_db_path} -> PostgreSQL")

    def migrate_table(self, table_name: str, transform_func=None):
        """
        Migrate a table from SQLite to PostgreSQL.

        Args:
            table_name: Name of the table to migrate
            transform_func: Optional function to transform rows
        """
        logger.info(f"Migrating table: {table_name}")

        # Get data from SQLite
        try:
            if table_name == "chats":
                sqlite_data = self._get_chats()
            elif table_name == "messages":
                sqlite_data = self._get_messages()
            elif table_name == "users":
                sqlite_data = self._get_users()
            elif table_name == "media":
                sqlite_data = self._get_media()
            elif table_name == "reactions":
                sqlite_data = self._get_reactions()
            elif table_name == "sync_status":
                sqlite_data = self._get_sync_status()
            elif table_name == "metadata":
                sqlite_data = self._get_metadata()
            else:
                logger.warning(f"Unknown table: {table_name}")
                return 0
        except Exception as e:
            logger.error(f"Error reading {table_name} from SQLite: {e}")
            return 0

        # Transform and insert into PostgreSQL
        count = 0
        try:
            for row in sqlite_data:
                if transform_func:
                    row = transform_func(row)

                if table_name == "chats":
                    self.pg_adapter.upsert_chat(row)
                elif table_name == "messages":
                    # Batch insert messages for better performance
                    pass  # Handle separately
                elif table_name == "users":
                    self.pg_adapter.upsert_user(row)
                elif table_name == "media":
                    self.pg_adapter.upsert_media(row)
                elif table_name == "reactions":
                    self.pg_adapter.insert_reactions([row])
                elif table_name == "sync_status":
                    self.pg_adapter.update_sync_status(
                        row["chat_id"], row["last_message_id"], row["message_count"]
                    )
                elif table_name == "metadata":
                    self.pg_adapter.set_metadata(row["key"], row["value"])

                count += 1

            # Special handling for messages (batch insert)
            if table_name == "messages" and sqlite_data:
                self.pg_adapter.insert_messages(sqlite_data)

            logger.info(f"Migrated {count} rows from {table_name}")
            return count

        except Exception as e:
            logger.error(f"Error migrating {table_name}: {e}")
            return 0

    def _get_chats(self) -> List[Dict]:
        """Get chats from SQLite."""
        chats = self.sqlite_db.get_all_chats(include_empty=True)
        return [self._convert_dict(chat) for chat in chats]

    def _get_messages(self) -> List[Dict]:
        """Get all messages from SQLite."""
        # Get all chats first
        chats = self.sqlite_db.get_all_chats()
        all_messages = []

        for chat in chats:
            # Get messages for each chat
            chat_id = chat["id"]
            offset = 0
            batch_size = 1000

            while True:
                messages = self.sqlite_db.get_messages(chat_id, batch_size, offset)
                if not messages:
                    break

                for msg in messages:
                    # Convert datetime objects if needed
                    msg_dict = self._convert_dict(msg)
                    if "date" in msg_dict and msg_dict["date"]:
                        if isinstance(msg_dict["date"], str):
                            msg_dict["date"] = datetime.fromisoformat(msg_dict["date"])
                    if "edit_date" in msg_dict and msg_dict["edit_date"]:
                        if isinstance(msg_dict["edit_date"], str):
                            msg_dict["edit_date"] = datetime.fromisoformat(msg_dict["edit_date"])
                    all_messages.append(msg_dict)

                offset += batch_size
                if len(messages) < batch_size:
                    break

        return all_messages

    def _get_users(self) -> List[Dict]:
        """Get all users from SQLite."""
        # Note: SQLite Database class doesn't have a get_all_users method
        # We need to query directly
        conn = self.sqlite_db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users")
        columns = [desc[0] for desc in cursor.description]
        users = []
        for row in cursor.fetchall():
            user = dict(zip(columns, row))
            users.append(self._convert_dict(user))
        conn.close()
        return users

    def _get_media(self) -> List[Dict]:
        """Get all media from SQLite."""
        # Note: Need direct query
        conn = self.sqlite_db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM media")
        columns = [desc[0] for desc in cursor.description]
        media = []
        for row in cursor.fetchall():
            media_row = dict(zip(columns, row))
            media.append(self._convert_dict(media_row))
        conn.close()
        return media

    def _get_reactions(self) -> List[Dict]:
        """Get all reactions from SQLite."""
        conn = self.sqlite_db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM reactions")
        columns = [desc[0] for desc in cursor.description]
        reactions = []
        for row in cursor.fetchall():
            reaction = dict(zip(columns, row))
            reactions.append(self._convert_dict(reaction))
        conn.close()
        return reactions

    def _get_sync_status(self) -> List[Dict]:
        """Get sync status from SQLite."""
        conn = self.sqlite_db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sync_status")
        columns = [desc[0] for desc in cursor.description]
        status = []
        for row in cursor.fetchall():
            status_row = dict(zip(columns, row))
            status.append(self._convert_dict(status_row))
        conn.close()
        return status

    def _get_metadata(self) -> List[Dict]:
        """Get metadata from SQLite."""
        metadata = self.sqlite_db.get_metadata()
        return [{"key": k, "value": v} for k, v in metadata.items()]

    def _convert_dict(self, row: Dict) -> Dict:
        """Convert row dict values for PostgreSQL compatibility."""
        # Convert any None values to actual None
        converted = {}
        for k, v in row.items():
            if v == "":
                v = None
            converted[k] = v
        return converted

    def verify_migration(self) -> bool:
        """Verify that migration was successful by comparing counts."""
        logger.info("Verifying migration...")

        # Compare stats
        sqlite_stats = {
            "chats": self.sqlite_db.get_all_chats().__len__(),
            "messages": sum(
                self.sqlite_db.get_message_count(chat["id"])
                for chat in self.sqlite_db.get_all_chats()
            ),
        }

        pg_stats = self.pg_adapter.get_stats()

        # Compare counts
        success = True
        for key in sqlite_stats:
            if sqlite_stats[key] != pg_stats.get(key, 0):
                logger.error(
                    f"Count mismatch for {key}: "
                    f"SQLite={sqlite_stats[key]}, PostgreSQL={pg_stats.get(key, 0)}"
                )
                success = False
            else:
                logger.info(f"✓ {key}: {sqlite_stats[key]} records")

        if success:
            logger.info("✅ Migration verification successful!")
        else:
            logger.error("❌ Migration verification failed!")

        return success


def main():
    """Main migration function."""
    logger.info("Starting SQLite to PostgreSQL migration...")

    # Get configuration
    config = Config()

    # Check PostgreSQL configuration
    if not os.getenv("POSTGRES_PASSWORD"):
        logger.error("POSTGRES_PASSWORD not set in environment")
        return 1

    pg_config = {
        "host": getattr(config, "postgres_host", "localhost"),
        "port": getattr(config, "postgres_port", 5432),
        "database": getattr(config, "postgres_db", "telegram_backup"),
        "user": getattr(config, "postgres_user", "postgres"),
        "password": getattr(config, "postgres_password", ""),
    }

    # Verify database path exists
    if not os.path.exists(config.database_path):
        logger.error(f"SQLite database not found: {config.database_path}")
        return 1

    logger.info(f"Migrating from SQLite: {config.database_path}")
    logger.info(f"Migrating to PostgreSQL: {pg_config['host']}:{pg_config['port']}/{pg_config['database']}")

    # Create backup of SQLite database
    backup_path = config.database_path + ".backup"
    import shutil
    shutil.copy2(config.database_path, backup_path)
    logger.info(f"Created backup: {backup_path}")

    # Perform migration
    try:
        migrator = DataMigrator(config.database_path, pg_config)

        # Migrate all tables in order (respecting foreign keys)
        tables = [
            "users",      # No dependencies
            "chats",      # No dependencies
            "messages",   # Depends on chats, users
            "media",      # Depends on messages, chats
            "reactions",  # Depends on messages
            "sync_status", # Depends on chats
            "metadata",   # No dependencies
        ]

        total_migrated = 0
        for table in tables:
            count = migrator.migrate_table(table)
            total_migrated += count

        # Verify migration
        if migrator.verify_migration():
            logger.info(f"\n✅ Migration completed successfully!")
            logger.info(f"Total records migrated: {total_migrated}")
            logger.info(f"Backup available at: {backup_path}")
            logger.info("\nTo use the new database:")
            logger.info("1. Set DB_TYPE=postgres-alchemy in your .env file")
            logger.info("2. Make sure POSTGRES_* variables are set correctly")
            logger.info("3. Restart the services")
            return 0
        else:
            logger.error("\n❌ Migration verification failed!")
            return 1

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

    finally:
        # Close connections
        if 'migrator' in locals():
            migrator.pg_adapter.close()
            migrator.sqlite_db.close()


if __name__ == "__main__":
    sys.exit(main())