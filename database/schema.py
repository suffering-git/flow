"""
Database schema creation and management.

Defines all table structures and indexes according to SCOPE.md specifications.
"""

import sqlite3
from utils.logger import get_logger

logger = get_logger(__name__)


def create_schema(conn: sqlite3.Connection) -> None:
    """
    Create all database tables and indexes.

    Args:
        conn: SQLite database connection.
    """
    cursor = conn.cursor()

    # Enable foreign keys
    cursor.execute("PRAGMA foreign_keys = ON")

    # Channels Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Channels (
            channel_id TEXT PRIMARY KEY,
            channel_name TEXT NOT NULL
        )
    """)

    # Videos Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Videos (
            video_id TEXT PRIMARY KEY,
            channel_id TEXT NOT NULL,
            video_title TEXT NOT NULL,
            published_date DATETIME NOT NULL,
            duration_seconds INTEGER NOT NULL,
            view_count INTEGER NOT NULL,
            like_count INTEGER NOT NULL,
            is_legacy_data BOOLEAN NOT NULL DEFAULT 0,
            is_test_data BOOLEAN NOT NULL DEFAULT 0,
            FOREIGN KEY (channel_id) REFERENCES Channels(channel_id)
        )
    """)

    # Status Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Status (
            video_id TEXT PRIMARY KEY,
            transcript_status TEXT NOT NULL DEFAULT 'pending',
            comments_status TEXT NOT NULL DEFAULT 'pending',
            stage_1_status TEXT NOT NULL DEFAULT 'pending',
            stage_2_status TEXT NOT NULL DEFAULT 'pending',
            embedding_status TEXT NOT NULL DEFAULT 'pending',
            transcript_failure_count INTEGER NOT NULL DEFAULT 0,
            transcript_last_failure_date TEXT,
            last_updated DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (video_id) REFERENCES Videos(video_id)
        )
    """)

    # RawTranscripts Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS RawTranscripts (
            transcript_id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_id TEXT NOT NULL,
            original_language TEXT NOT NULL,
            transcript_text TEXT NOT NULL,
            is_translated BOOLEAN NOT NULL,
            downloaded_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (video_id) REFERENCES Videos(video_id)
        )
    """)

    # RawComments Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS RawComments (
            comment_id TEXT PRIMARY KEY,
            video_id TEXT NOT NULL,
            author_name TEXT NOT NULL,
            author_channel_id TEXT NOT NULL,
            comment_text TEXT NOT NULL,
            parent_comment_id TEXT,
            like_count INTEGER NOT NULL,
            published_at DATETIME NOT NULL,
            downloaded_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (video_id) REFERENCES Videos(video_id)
        )
    """)

    # CompressedData Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS CompressedData (
            compressed_id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_id TEXT NOT NULL UNIQUE,
            compressed_transcript TEXT NOT NULL,
            compressed_comments TEXT NOT NULL,
            processed_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (video_id) REFERENCES Videos(video_id)
        )
    """)

    # TopicSummaries Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS TopicSummaries (
            summary_id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_id TEXT NOT NULL,
            topic_title TEXT NOT NULL,
            summary_text TEXT NOT NULL,
            summary_timestamps TEXT,
            source_type TEXT NOT NULL,
            confidence_score INTEGER NOT NULL,
            comment_id TEXT,
            FOREIGN KEY (video_id) REFERENCES Videos(video_id),
            FOREIGN KEY (comment_id) REFERENCES RawComments(comment_id)
        )
    """)

    # AtomicInsights Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS AtomicInsights (
            insight_id INTEGER PRIMARY KEY AUTOINCREMENT,
            summary_id INTEGER NOT NULL,
            insight_type TEXT NOT NULL,
            confidence_score INTEGER NOT NULL,
            insight_text TEXT NOT NULL,
            insight_timestamps TEXT,
            embedding_vector BLOB,
            source_type TEXT NOT NULL,
            FOREIGN KEY (summary_id) REFERENCES TopicSummaries(summary_id)
        )
    """)

    # Create indexes for fast queries
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_videos_channel ON Videos(channel_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_transcripts_video ON RawTranscripts(video_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_comments_video ON RawComments(video_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_compressed_video ON CompressedData(video_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_topics_video ON TopicSummaries(video_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_insights_summary ON AtomicInsights(summary_id)")

    # Create FTS5 virtual table for full-text search on atomic insights
    cursor.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS AtomicInsights_fts USING fts5(
            insight_text,
            content=AtomicInsights,
            content_rowid=insight_id
        )
    """)

    # TODO: Setup sqlite-vec extension for vector similarity search
    # This requires loading the sqlite-vec extension and creating vector index

    conn.commit()
    logger.info("✅ Database schema created successfully")


def drop_all_tables(conn: sqlite3.Connection) -> None:
    """
    Drop all tables (for testing/reset purposes).

    Args:
        conn: SQLite database connection.
    """
    cursor = conn.cursor()

    tables = [
        "AtomicInsights_fts",
        "AtomicInsights",
        "TopicSummaries",
        "CompressedData",
        "RawComments",
        "RawTranscripts",
        "Status",
        "Videos",
        "Channels",
    ]

    for table in tables:
        cursor.execute(f"DROP TABLE IF EXISTS {table}")

    conn.commit()
    logger.info("✅ All tables dropped")
