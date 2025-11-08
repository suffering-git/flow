"""
Database manager for handling SQLite connections and operations.

Provides transaction management and common database operations.
"""

import sqlite3
from typing import Any
from contextlib import contextmanager
from datetime import datetime

from database.schema import create_schema
from utils.logger import get_logger

logger = get_logger(__name__)


class DatabaseManager:
    """
    Manages SQLite database connections and operations.

    Provides transaction-safe operations and connection pooling.
    """

    def __init__(self, db_path: str):
        """
        Initialize database manager.

        Args:
            db_path: Path to SQLite database file.
        """
        self.db_path = db_path
        self._connection: sqlite3.Connection | None = None

    @property
    def connection(self) -> sqlite3.Connection:
        """
        Get or create database connection.

        Returns:
            SQLite connection object.
        """
        if self._connection is None:
            self._connection = sqlite3.connect(self.db_path)
            self._connection.row_factory = sqlite3.Row  # Access columns by name
        return self._connection

    def initialize_database(self) -> None:
        """
        Initialize database with schema.

        Creates all tables and indexes if they don't exist.
        """
        create_schema(self.connection)

    @contextmanager
    def transaction(self):
        """
        Context manager for database transactions.

        Automatically commits on success, rolls back on exception.

        Yields:
            SQLite cursor object.
        """
        cursor = self.connection.cursor()
        try:
            yield cursor
            self.connection.commit()
        except Exception as e:
            self.connection.rollback()
            logger.error(f"❌ Transaction failed: {e}")
            raise

    def execute(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        """
        Execute a SQL query.

        Args:
            query: SQL query string.
            params: Query parameters (optional).

        Returns:
            SQLite cursor object.
        """
        return self.connection.execute(query, params)

    def fetchone(self, query: str, params: tuple = ()) -> sqlite3.Row | None:
        """
        Fetch a single row from query.

        Args:
            query: SQL query string.
            params: Query parameters (optional).

        Returns:
            Single row as sqlite3.Row or None.
        """
        cursor = self.execute(query, params)
        return cursor.fetchone()

    def fetchall(self, query: str, params: tuple = ()) -> list[sqlite3.Row]:
        """
        Fetch all rows from query.

        Args:
            query: SQL query string.
            params: Query parameters (optional).

        Returns:
            List of rows as sqlite3.Row objects.
        """
        cursor = self.execute(query, params)
        return cursor.fetchall()

    def reset_processing_data(self, reset_compressed: bool = False) -> None:
        """
        Reset AI processing results while preserving raw data.

        Args:
            reset_compressed: If True, also reset CompressedData table.
        """
        with self.transaction() as cursor:
            # Delete Stage 2 and Stage 3 results
            cursor.execute("DELETE FROM AtomicInsights")
            cursor.execute("DELETE FROM TopicSummaries")

            # Reset status flags
            cursor.execute("""
                UPDATE Status
                SET stage_2_status = 'pending',
                    embedding_status = 'pending',
                    last_updated = ?
            """, (datetime.now(),))

            if reset_compressed:
                # Also delete Stage 1 results
                cursor.execute("DELETE FROM CompressedData")
                cursor.execute("""
                    UPDATE Status
                    SET stage_1_status = 'pending',
                        last_updated = ?
                """, (datetime.now(),))

        logger.info("✅ Processing data reset completed")

    def close(self) -> None:
        """Close database connection."""
        if self._connection:
            self._connection.close()
            self._connection = None
