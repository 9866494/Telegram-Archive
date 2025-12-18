#!/usr/bin/env python3
"""
Test SQLite to PostgreSQL migration
"""

import os
import sys
import tempfile
import sqlite3
from datetime import datetime

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.database import Database as SQLiteDatabase
from src.db_adapters.factory import create_database_adapter


class MockConfig:
    def __init__(self):
        self.db_type = "postgres-alchemy"
        self.postgres_host = "localhost"
        self.postgres_port = 5432
        self.postgres_db = "telegram_backup"
        self.postgres_user = "telegram"
        self.postgres_password = "secure_password_123"


def test_migration():
    """Test migration from SQLite to PostgreSQL"""
    print("\n=== Testing SQLite to PostgreSQL Migration ===")

    # Create a temporary SQLite database with some test data
    temp_sqlite = tempfile.mktemp(suffix='.db')
    print(f"Creating test SQLite database: {temp_sqlite}")

    try:
        # Create test data in SQLite
        conn = sqlite3.connect(temp_sqlite)
        cursor = conn.cursor()

        # Create tables
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chats (
                id INTEGER PRIMARY KEY,
                type TEXT NOT NULL,
                title TEXT,
                username TEXT,
                first_name TEXT,
                last_name TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY,
                chat_id INTEGER NOT NULL,
                text TEXT,
                date TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS metadata (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)

        # Insert test data
        cursor.execute("""
            INSERT INTO chats (id, type, title, first_name) VALUES
            (123, 'private', 'Test Chat', 'Test User')
        """)

        cursor.execute("""
            INSERT INTO messages (id, chat_id, text, date) VALUES
            (1, 123, 'Hello from SQLite', datetime('now'))
        """)

        cursor.execute("""
            INSERT INTO metadata (key, value) VALUES
            ('owner_id', '456')
        """)

        conn.commit()
        conn.close()

        print("✓ Created test data in SQLite")

        # Test PostgreSQL connection
        config = MockConfig()
        if not config.postgres_password:
            print("⚠️  Skipping migration test - PostgreSQL not configured")
            return True

        # Create PostgreSQL adapter
        pg_adapter = create_database_adapter(config)
        pg_adapter.initialize_schema()
        print("✓ Connected to PostgreSQL and initialized schema")

        # Perform migration
        from migrate_to_postgres import DataMigrator
        migrator = DataMigrator(temp_sqlite, {
            "host": config.postgres_host,
            "port": config.postgres_port,
            "database": config.postgres_db,
            "user": config.postgres_user,
            "password": config.postgres_password
        })

        print("\nMigrating tables...")
        tables = ["users", "chats", "messages", "media", "reactions", "sync_status", "metadata"]
        total_migrated = 0

        for table in tables:
            count = migrator.migrate_table(table)
            total_migrated += count

        # Verify migration
        if migrator.verify_migration():
            print(f"\n✅ Migration successful! Total records: {total_migrated}")

            # Test that we can read from PostgreSQL
            pg_stats = pg_adapter.get_stats()
            print(f"PostgreSQL stats: {pg_stats}")

            # Clean up
            pg_adapter.close()
            migrator.pg_adapter.close()
            migrator.sqlite_db.close()
            return True
        else:
            print("\n❌ Migration verification failed!")
            return False

    except Exception as e:
        print(f"\n❌ Migration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        # Clean up
        if os.path.exists(temp_sqlite):
            os.remove(temp_sqlite)
            print(f"Cleaned up: {temp_sqlite}")


if __name__ == "__main__":
    success = test_migration()
    sys.exit(0 if success else 1)