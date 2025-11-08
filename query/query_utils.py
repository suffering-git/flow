"""
Query utilities for searching and retrieving data.

Provides user-friendly functions for:
- Full-text search (FTS5)
- Vector similarity search
- Data retrieval with context
"""

import json
from typing import Any, Optional
import os

from database.db_manager import DatabaseManager
from utils.gemini_client import GeminiClient
from utils.logger import get_logger
import config

logger = get_logger(__name__)


class QueryUtils:
    """
    Utility class for querying processed data.
    """

    def __init__(self, db_path: str = config.DATABASE_PATH):
        """
        Initialize query utilities.

        Args:
            db_path: Path to SQLite database.
        """
        self.db_manager = DatabaseManager(db_path)
        self.embedding_client = GeminiClient(config.EMBEDDING_MODEL)

    def search_text(
        self,
        query: str,
        limit: int = 10
    ) -> list[dict[str, Any]]:
        """
        Full-text search on atomic insights.

        Args:
            query: Search query string.
            limit: Maximum number of results.

        Returns:
            List of matching insights with basic metadata.
        """
        # TODO: Implement FTS5 search
        # Use db_manager.search_insights_fts()
        logger.info(f"🔍 Text search: '{query}'")
        pass

    async def search_semantic(
        self,
        query: str,
        limit: int = 10,
        similarity_threshold: float = 0.7
    ) -> list[dict[str, Any]]:
        """
        Semantic vector similarity search.

        Args:
            query: Search query string.
            limit: Maximum number of results.
            similarity_threshold: Minimum cosine similarity (0-1).

        Returns:
            List of matching insights with similarity scores.
        """
        # TODO: Implement vector search
        # 1. Generate embedding for query using embedding_client
        # 2. Query sqlite-vec for similar vectors
        # 3. Filter by similarity threshold
        # 4. Return top results

        logger.info(f"🔍 Semantic search: '{query}'")
        pass

    def get_insight_details(self, insight_id: int) -> dict[str, Any]:
        """
        Get full details for an insight including context.

        Returns:
        - Insight text and timestamps
        - Parent topic summary and timestamps
        - Video metadata
        - YouTube links for each timestamp

        Args:
            insight_id: Atomic insight ID.

        Returns:
            Dictionary with complete insight context.
        """
        # TODO: Implement detail retrieval
        # Use db_manager.get_insight_with_context()
        # Parse timestamp JSON
        # Generate YouTube URLs

        logger.debug(f"📄 Fetching insight details: {insight_id}")
        pass

    def browse_insights(
        self,
        offset: int = 0,
        limit: int = 50,
        insight_type: Optional[str] = None
    ) -> list[dict[str, Any]]:
        """
        Browse atomic insights with pagination.

        Args:
            offset: Number of results to skip.
            limit: Maximum number of results.
            insight_type: Filter by 'quantitative' or 'qualitative', or None for all.

        Returns:
            List of insights (text only for quick browsing).
        """
        # TODO: Implement browse functionality
        # Query AtomicInsights table with pagination
        # Return: insight_id, insight_text, insight_type

        logger.debug(f"📖 Browsing insights: offset={offset}, limit={limit}")
        pass

    def generate_youtube_link(
        self,
        video_id: str,
        timestamp_str: str
    ) -> str:
        """
        Generate YouTube link with timestamp.

        Args:
            video_id: YouTube video ID.
            timestamp_str: Timestamp in HH:MM:SS format.

        Returns:
            YouTube URL with time parameter.
        """
        # TODO: Implement URL generation
        # Parse HH:MM:SS to seconds
        # Return: f"https://youtube.com/watch?v={video_id}&t={seconds}s"

        pass

    def get_insights_by_video(self, video_id: str) -> list[dict[str, Any]]:
        """
        Get all insights for a specific video.

        Args:
            video_id: YouTube video ID.

        Returns:
            List of all insights from the video.
        """
        # TODO: Implement video-based query
        # Join AtomicInsights -> TopicSummaries -> Videos
        # Return all insights for video

        logger.debug(f"📹 Getting insights for video: {video_id}")
        pass

    def get_topics_by_video(self, video_id: str) -> list[dict[str, Any]]:
        """
        Get all topic summaries for a specific video.

        Args:
            video_id: YouTube video ID.

        Returns:
            List of topic summaries.
        """
        # TODO: Implement topic retrieval
        # Query TopicSummaries table filtered by video_id

        logger.debug(f"📹 Getting topics for video: {video_id}")
        pass

    def close(self) -> None:
        """Close database connection."""
        self.db_manager.close()
