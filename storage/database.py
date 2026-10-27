
import json
import sqlite3
from pathlib import Path

DATABASE_PATH = Path(__file__).resolve().parent / "configurations.db"


def get_connection():
    """Create a connection to the SQLite database."""
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():
    """Create the configuration history table if it doesn't exist."""
    with get_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS configurations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                config_name TEXT NOT NULL,
                version INTEGER NOT NULL,
                criteria_weights TEXT NOT NULL,
                preferences TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(config_name, version)
            )
        """)


def save_configuration(config_name, criteria_weights, preferences=None):
    """Save a new version without overwriting previous versions."""
    if not config_name or not config_name.strip():
        raise ValueError("Configuration name cannot be empty.")

    if not isinstance(criteria_weights, dict) or not criteria_weights:
        raise ValueError("Criteria weights must be a non-empty dictionary.")

    if any(
        not isinstance(weight, (int, float)) or isinstance(weight, bool)
        or weight < 0
        for weight in criteria_weights.values()
    ):
        raise ValueError("Criteria weights must be non-negative numbers.")

    if preferences is None:
        preferences = {}

    if not isinstance(preferences, dict):
        raise ValueError("Preferences must be a dictionary.")

    initialize_database()

    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT COALESCE(MAX(version), 0) + 1 AS next_version
            FROM configurations
            WHERE config_name = ?
            """,
            (config_name.strip(),),
        ).fetchone()

        version = row["next_version"]

        connection.execute(
            """
            INSERT INTO configurations
                (config_name, version, criteria_weights, preferences)
            VALUES (?, ?, ?, ?)
            """,
            (
                config_name.strip(),
                version,
                json.dumps(criteria_weights),
                json.dumps(preferences),
            ),
        )

    return version


def get_configuration(config_name, version=None):
    """Retrieve a specific version, or the latest version by default."""
    initialize_database()

    with get_connection() as connection:
        if version is None:
            row = connection.execute(
                """
                SELECT * FROM configurations
                WHERE config_name = ?
                ORDER BY version DESC
                LIMIT 1
                """,
                (config_name.strip(),),
            ).fetchone()
        else:
            row = connection.execute(
                """
                SELECT * FROM configurations
                WHERE config_name = ? AND version = ?
                """,
                (config_name.strip(), version),
            ).fetchone()

    if row is None:
        return None

    result = dict(row)
    result["criteria_weights"] = json.loads(
        result["criteria_weights"]
    )
    result["preferences"] = json.loads(result["preferences"])

    return result


def get_configuration_history(config_name):
    """Return all versions of a configuration, oldest first."""
    initialize_database()

    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, config_name, version, created_at
            FROM configurations
            WHERE config_name = ?
            ORDER BY version ASC
            """,
            (config_name.strip(),),
        ).fetchall()

    return [dict(row) for row in rows]
