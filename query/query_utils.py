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
        logger.info(f"🔍 Text search: '{query}'")

        results = self.db_manager.fetchall(
            """
            SELECT
                ai.insight_id,
                ai.insight_text,
                ai.insight_type,
                ai.confidence_score,
                ts.topic_title,
                v.video_title,
                v.video_id
            FROM insights_fts fts
            JOIN AtomicInsights ai ON fts.rowid = ai.insight_id
            JOIN TopicSummaries ts ON ai.topic_summary_id = ts.topic_summary_id
            JOIN Videos v ON ts.video_id = v.video_id
            WHERE insights_fts MATCH ?
            ORDER BY rank
            LIMIT ?
            """,
            (query, limit)
        )

        return [dict(row) for row in results]

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
        logger.info(f"🔍 Semantic search: '{query}'")

        # Generate embedding for query
        query_embedding = await self.embedding_client.generate_embedding(query)

        # Note: This is a simplified implementation
        # For production, you'd use sqlite-vec for efficient vector search
        # Here we're using a basic approach for demonstration

        # Get all insights with embeddings
        all_insights = self.db_manager.fetchall(
            """
            SELECT
                ai.insight_id,
                ai.insight_text,
                ai.insight_type,
                ai.embedding,
                ts.topic_title,
                v.video_title,
                v.video_id
            FROM AtomicInsights ai
            JOIN TopicSummaries ts ON ai.topic_summary_id = ts.topic_summary_id
            JOIN Videos v ON ts.video_id = v.video_id
            WHERE ai.embedding IS NOT NULL
            """
        )

        # Calculate similarity scores
        # (In production, use sqlite-vec for efficient vector search)
        results_with_scores = []
        for row in all_insights:
            # Deserialize embedding
            import struct
            embedding_bytes = row['embedding']
            num_floats = len(embedding_bytes) // 4
            embedding = list(struct.unpack(f'<{num_floats}f', embedding_bytes))

            # Calculate cosine similarity
            dot_product = sum(a * b for a, b in zip(query_embedding, embedding))
            query_norm = sum(a * a for a in query_embedding) ** 0.5
            embedding_norm = sum(b * b for b in embedding) ** 0.5
            similarity = dot_product / (query_norm * embedding_norm)

            if similarity >= similarity_threshold:
                result = dict(row)
                result['similarity'] = similarity
                del result['embedding']  # Don't return raw embedding
                results_with_scores.append(result)

        # Sort by similarity and limit
        results_with_scores.sort(key=lambda x: x['similarity'], reverse=True)
        return results_with_scores[:limit]

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
        logger.debug(f"📄 Fetching insight details: {insight_id}")

        # Get full context
        result = self.db_manager.fetchone(
            """
            SELECT
                ai.insight_id,
                ai.insight_text,
                ai.insight_timestamps,
                ai.insight_type,
                ai.confidence_score AS insight_confidence,
                ts.topic_title,
                ts.summary_text,
                ts.summary_timestamps,
                ts.confidence_score AS topic_confidence,
                v.video_id,
                v.video_title,
                v.published_date,
                c.channel_name
            FROM AtomicInsights ai
            JOIN TopicSummaries ts ON ai.topic_summary_id = ts.topic_summary_id
            JOIN Videos v ON ts.video_id = v.video_id
            JOIN Channels c ON v.channel_id = c.channel_id
            WHERE ai.insight_id = ?
            """,
            (insight_id,)
        )

        if not result:
            return None

        # Convert to dict
        details = dict(result)

        # Parse timestamp JSON
        import json
        details['insight_timestamps'] = json.loads(details['insight_timestamps'])
        details['summary_timestamps'] = json.loads(details['summary_timestamps'])

        # Generate YouTube links for insight timestamps
        video_id = details['video_id']
        for segment in details['insight_timestamps'].get('timestamped_segments', []):
            segment['youtube_links'] = [
                self.generate_youtube_link(video_id, ts)
                for ts in segment['timestamps']
            ]

        return details

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
        logger.debug(f"📖 Browsing insights: offset={offset}, limit={limit}")

        if insight_type:
            results = self.db_manager.fetchall(
                """
                SELECT
                    insight_id,
                    insight_text,
                    insight_type,
                    confidence_score
                FROM AtomicInsights
                WHERE insight_type = ?
                ORDER BY insight_id DESC
                LIMIT ? OFFSET ?
                """,
                (insight_type, limit, offset)
            )
        else:
            results = self.db_manager.fetchall(
                """
                SELECT
                    insight_id,
                    insight_text,
                    insight_type,
                    confidence_score
                FROM AtomicInsights
                ORDER BY insight_id DESC
                LIMIT ? OFFSET ?
                """,
                (limit, offset)
            )

        return [dict(row) for row in results]

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
        # Parse HH:MM:SS to seconds
        parts = timestamp_str.split(':')
        if len(parts) == 3:
            hours, minutes, seconds = map(int, parts)
            total_seconds = hours * 3600 + minutes * 60 + seconds
        elif len(parts) == 2:
            minutes, seconds = map(int, parts)
            total_seconds = minutes * 60 + seconds
        else:
            total_seconds = int(parts[0])

        return f"https://youtube.com/watch?v={video_id}&t={total_seconds}s"

    def get_insights_by_video(self, video_id: str) -> list[dict[str, Any]]:
        """
        Get all insights for a specific video.

        Args:
            video_id: YouTube video ID.

        Returns:
            List of all insights from the video.
        """
        logger.debug(f"📹 Getting insights for video: {video_id}")

        results = self.db_manager.fetchall(
            """
            SELECT
                ai.insight_id,
                ai.insight_text,
                ai.insight_type,
                ai.confidence_score,
                ts.topic_title
            FROM AtomicInsights ai
            JOIN TopicSummaries ts ON ai.topic_summary_id = ts.topic_summary_id
            WHERE ts.video_id = ?
            ORDER BY ai.insight_id
            """,
            (video_id,)
        )

        return [dict(row) for row in results]

    def get_topics_by_video(self, video_id: str) -> list[dict[str, Any]]:
        """
        Get all topic summaries for a specific video.

        Args:
            video_id: YouTube video ID.

        Returns:
            List of topic summaries.
        """
        logger.debug(f"📹 Getting topics for video: {video_id}")

        results = self.db_manager.fetchall(
            """
            SELECT
                topic_summary_id,
                topic_title,
                summary_text,
                source_type,
                confidence_score
            FROM TopicSummaries
            WHERE video_id = ?
            ORDER BY topic_summary_id
            """,
            (video_id,)
        )

        return [dict(row) for row in results]

    def close(self) -> None:
        """Close database connection."""
        self.db_manager.close()
