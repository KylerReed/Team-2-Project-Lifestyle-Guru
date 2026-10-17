"""Database helper functions for the Lifestyle Guru application.

This module manages connections to the SQLite database and ensures that
required database columns exist for profile and food-library features.
"""
import sqlite3


def get_database_connection(database_path):
    """Create and return a connection to the SQLite database.

    The connection uses sqlite3.Row so query results can be accessed
    by column name. Foreign-key enforcement is also enabled.
    """
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def ensure_profile_schema(database_path):
    """Ensure required profile and food-item columns exist in the database.

    This function checks the existing table structure and adds columns
    used by the final application when they are missing.
    """
    with get_database_connection(database_path) as connection:
        profile_columns = {
            row["name"] for row in connection.execute("PRAGMA table_info(profiles)")
        }

        if "goal" not in profile_columns:
            connection.execute("ALTER TABLE profiles ADD COLUMN goal TEXT")

        if "name" not in profile_columns:
            connection.execute("ALTER TABLE profiles ADD COLUMN name TEXT")

        food_columns = {
            row["name"] for row in connection.execute("PRAGMA table_info(food_items)")
        }

        if "usage_count" not in food_columns:
            connection.execute(
                "ALTER TABLE food_items ADD COLUMN usage_count INTEGER NOT NULL DEFAULT 0"
            )


