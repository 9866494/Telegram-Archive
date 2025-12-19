"""
Schema configuration for PostgreSQL

This module provides a way to set the schema for SQLAlchemy models
when using PostgreSQL with a custom schema.
"""

# Default schema name (will be overridden by config)
schema_name = None

def set_schema_name(schema: str):
    """Set the schema name for all models"""
    global schema_name
    schema_name = schema

def get_schema_name():
    """Get the current schema name"""
    return schema_name