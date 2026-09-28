import sqlite3


def get_database_connection(database_path):
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def ensure_profile_schema(database_path):
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
