#!/usr/bin/env python3
"""
Test script for SQLAlchemy adapters

This script tests both SQLite and PostgreSQL adapters to ensure
they work correctly with the existing data format.
"""

import os
import sys
import tempfile
import shutil
from datetime import datetime

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.config import Config
from src.db_adapters.factory import create_database_adapter, is_sqlalchemy_adapter


def test_sqlite_adapter():
    """Test the SQLite SQLAlchemy adapter"""
    print("\n=== Testing SQLite SQLAlchemy Adapter ===")

    # Create a temporary config
    config = Config()
    config.db_type = "sqlite-alchemy"

    # Create temporary database file
    temp_db = tempfile.mktemp(suffix='.db')
    config.database_path = temp_db
    print(f"Testing with temporary database: {temp_db}")

    try:
        # Create adapter
        adapter = create_database_adapter(config)
        print("✓ SQLite adapter created successfully")

        # Initialize schema
        adapter.initialize_schema()
        print("✓ Database schema initialized")

        # Test basic operations
        # 1. Upsert chat
        chat_data = {
            "id": 123456789,
            "type": "private",
            "first_name": "Test",
            "last_name": "User",
            "username": "testuser",
            "phone": "+1234567890"
        }
        adapter.upsert_chat(chat_data)
        print("✓ Chat upserted")

        # 2. Get chat
        retrieved_chat = adapter.get_chat(123456789)
        assert retrieved_chat is not None
        assert retrieved_chat["first_name"] == "Test"
        print("✓ Chat retrieved successfully")

        # 3. Insert messages
        messages = [
            {
                "id": 1,
                "chat_id": 123456789,
                "sender_id": 123456789,
                "date": datetime.utcnow(),
                "text": "Hello, world!"
            },
            {
                "id": 2,
                "chat_id": 123456789,
                "sender_id": 123456789,
                "date": datetime.utcnow(),
                "text": "Second message"
            }
        ]
        adapter.insert_messages(messages)
        print("✓ Messages inserted")

        # 4. Get messages
        retrieved_messages = adapter.get_messages(123456789)
        assert len(retrieved_messages) == 2
        print("✓ Messages retrieved successfully")

        # 5. Get stats
        stats = adapter.get_stats()
        assert stats["chats"] == 1
        assert stats["messages"] == 2
        print("✓ Statistics retrieved")

        # 6. Test metadata
        adapter.set_metadata("test_key", "test_value")
        value = adapter.get_metadata("test_key")
        assert value == "test_value"
        print("✓ Metadata operations working")

        print("\n✅ All SQLite adapter tests passed!")
        return True

    except Exception as e:
        print(f"\n❌ SQLite adapter test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        # Clean up
        if os.path.exists(temp_db):
            os.remove(temp_db)
        print(f"Cleaned up temporary database: {temp_db}")


def test_postgres_adapter():
    """Test the PostgreSQL SQLAlchemy adapter"""
    print("\n=== Testing PostgreSQL SQLAlchemy Adapter ===")

    # Check if PostgreSQL is available
    if not os.getenv("POSTGRES_PASSWORD"):
        print("⚠️  Skipping PostgreSQL test - POSTGRES_PASSWORD not set")
        print("   Set DB_TYPE=postgres-alchemy and POSTGRES_PASSWORD in .env")
        return True

    # Create config for PostgreSQL
    config = Config()
    config.db_type = "postgres-alchemy"

    try:
        # Create adapter
        adapter = create_database_adapter(config)
        print("✓ PostgreSQL adapter created successfully")

        # Initialize schema
        adapter.initialize_schema()
        print("✓ Database schema initialized")

        # Test basic operations (same as SQLite test)
        chat_data = {
            "id": 987654321,
            "type": "private",
            "first_name": "Postgres",
            "last_name": "Test",
            "username": "pgtest"
        }
        adapter.upsert_chat(chat_data)
        print("✓ Chat upserted")

        retrieved_chat = adapter.get_chat(987654321)
        assert retrieved_chat is not None
        assert retrieved_chat["first_name"] == "Postgres"
        print("✓ Chat retrieved successfully")

        # Clean up
        adapter.delete_chat(987654321)
        print("✓ Test chat deleted")

        print("\n✅ All PostgreSQL adapter tests passed!")
        return True

    except Exception as e:
        print(f"\n❌ PostgreSQL adapter test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        if 'adapter' in locals():
            adapter.close()


def test_factory():
    """Test the adapter factory"""
    print("\n=== Testing Adapter Factory ===")

    # Test SQLite config
    config = Config()
    config.db_type = "sqlite-alchemy"
    config.database_path = "/tmp/test.db"

    assert is_sqlalchemy_adapter("sqlite-alchemy") == True
    assert is_sqlalchemy_adapter("postgres-alchemy") == True
    assert is_sqlalchemy_adapter("sqlite") == False
    print("✓ is_sqlalchemy_adapter function working")

    try:
        adapter = create_database_adapter(config)
        assert adapter.__class__.__name__ == "SQLiteAdapter"
        print("✓ Factory returns SQLite adapter for sqlite-alchemy")
        adapter.close()
    except Exception as e:
        print(f"❌ Factory test failed: {e}")
        return False

    # Test PostgreSQL config
    if os.getenv("POSTGRES_PASSWORD"):
        config.db_type = "postgres-alchemy"
        try:
            adapter = create_database_adapter(config)
            assert adapter.__class__.__name__ == "PostgreSQLAdapter"
            print("✓ Factory returns PostgreSQL adapter for postgres-alchemy")
            adapter.close()
        except Exception as e:
            print(f"❌ PostgreSQL factory test failed: {e}")
            return False

    # Test invalid db_type
    config.db_type = "invalid"
    try:
        adapter = create_database_adapter(config)
        print("❌ Should have raised ValueError for invalid db_type")
        return False
    except ValueError:
        print("✓ Factory correctly raises ValueError for invalid db_type")

    # Test direct sqlite (should raise error)
    config.db_type = "sqlite"
    try:
        adapter = create_database_adapter(config)
        print("❌ Should have raised error for direct sqlite")
        return False
    except ValueError as e:
        assert "use the original src.database.Database class" in str(e)
        print("✓ Factory correctly handles direct sqlite type")

    print("\n✅ All factory tests passed!")
    return True


def main():
    """Run all tests"""
    print("Starting SQLAlchemy adapter tests...")

    results = []

    # Test factory
    results.append(test_factory())

    # Test SQLite adapter
    results.append(test_sqlite_adapter())

    # Test PostgreSQL adapter
    results.append(test_postgres_adapter())

    # Summary
    print("\n" + "="*50)
    print("TEST SUMMARY")
    print("="*50)
    test_names = ["Factory", "SQLite Adapter", "PostgreSQL Adapter"]
    for i, (name, result) in enumerate(zip(test_names, results)):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{name:.<30} {status}")

    passed = sum(results)
    total = len(results)
    print("\nOverall: {}/{} tests passed".format(passed, total))

    if passed == total:
        print("\n🎉 All tests passed! SQLAlchemy adapters are ready.")
        return 0
    else:
        print("\n💥 Some tests failed. Please review the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())