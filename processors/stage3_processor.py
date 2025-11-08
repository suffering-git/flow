"""
Stage 3: Embedding Generation Processor.

Generates vector embeddings for atomic insights.
Uses Gemini Embedding model.
"""

import asyncio
import struct
from typing import Any
from datetime import datetime

import config
from database.db_manager import DatabaseManager
from utils.gemini_client import GeminiClient
from utils.logger import get_logger
from utils.rate_limiter import RateLimiter
from utils.signal_handler import shutdown_requested, pause_requested

logger = get_logger(__name__)


class Stage3Processor:
    """
    Generates embeddings for atomic insights.
    """

    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize Stage 3 processor.

        Args:
            db_manager: Database manager instance.
        """
        self.db_manager = db_manager
        self.gemini_client = GeminiClient(config.EMBEDDING_MODEL)
        self.rate_limiter = RateLimiter(
            config.EMBEDDING_MODEL,
            max_concurrent=config.STAGE3_MAX_CONCURRENT
        )
        self.semaphore = asyncio.Semaphore(config.STAGE3_MAX_CONCURRENT)

    async def generate_all_embeddings(self) -> None:
        """
        Generate embeddings for all videos ready for Stage 3.

        A video is ready when:
        - stage_2_status is 'complete'
        - embedding_status is 'pending'
        """
        logger.info("🔄 Starting Stage 3 embedding generation")

        # Get all videos ready for Stage 3
        ready_videos = self.db_manager.fetchall(
            """
            SELECT video_id FROM Status
            WHERE stage_2_status = 'complete'
              AND embedding_status = 'pending'
            """
        )

        if not ready_videos:
            logger.info("✅ No videos ready for Stage 3")
            return

        video_ids = [row['video_id'] for row in ready_videos]
        logger.info(f"🔄 Generating embeddings for {len(video_ids)} videos")

        # Process each video
        for video_id in video_ids:
            # Check for shutdown/pause signals
            if shutdown_requested.is_set() or pause_requested.is_set():
                break

            # Get all atomic insights for this video
            insights = self.db_manager.fetchall(
                """
                SELECT ai.insight_id, ai.insight_text
                FROM AtomicInsights ai
                JOIN TopicSummaries ts ON ai.topic_summary_id = ts.topic_summary_id
                WHERE ts.video_id = ?
                  AND ai.embedding IS NULL
                """,
                (video_id,)
            )

            if not insights:
                # No insights to embed, mark as complete
                await self.finalize_video_embedding_status(video_id)
                continue

            logger.info(
                f"🔄 Generating {len(insights)} embeddings for video {video_id}"
            )

            # Create tasks for all insights
            tasks = [
                self.generate_embedding(row['insight_id'], row['insight_text'])
                for row in insights
            ]

            # Execute concurrently
            await asyncio.gather(*tasks, return_exceptions=True)

            # Mark video as complete
            await self.finalize_video_embedding_status(video_id)

        logger.info("✅ Stage 3 embedding generation completed")

    async def generate_embedding(
        self,
        insight_id: int,
        insight_text: str
    ) -> None:
        """
        Generate embedding for a single insight.

        Args:
            insight_id: Atomic insight ID.
            insight_text: Clean insight text (no timestamp syntax).
        """
        async with self.semaphore:
            try:
                logger.debug(f"🔄 Generating embedding for insight {insight_id}")

                # Generate embedding
                embedding = await self.gemini_client.generate_embedding(insight_text)

                # Note: Embedding API doesn't return token counts
                # Track as minimal usage
                await self.rate_limiter.track_request(
                    input_tokens=len(insight_text) // 4,  # Rough estimate
                    output_tokens=0
                )

                # Serialize to bytes
                embedding_bytes = self._serialize_embedding(embedding)

                # Update database
                with self.db_manager.transaction() as cursor:
                    cursor.execute(
                        """
                        UPDATE AtomicInsights
                        SET embedding = ?
                        WHERE insight_id = ?
                        """,
                        (embedding_bytes, insight_id)
                    )

                logger.debug(f"✅ Embedding generated for insight {insight_id}")

            except Exception as e:
                logger.error(f"❌ Embedding failed for insight {insight_id}: {e}")

    def _serialize_embedding(self, embedding: list[float]) -> bytes:
        """
        Serialize embedding vector to bytes for BLOB storage.

        Args:
            embedding: List of floats from Gemini API.

        Returns:
            Serialized bytes.
        """
        # Pack floats as binary data
        # Format: '<' = little-endian, 'f' = float (4 bytes each)
        return struct.pack(f'<{len(embedding)}f', *embedding)

    async def finalize_video_embedding_status(self, video_id: str) -> None:
        """
        Update embedding_status to 'complete' for a video.

        Called after all insights for a video have embeddings.

        Args:
            video_id: YouTube video ID.
        """
        with self.db_manager.transaction() as cursor:
            cursor.execute(
                """
                UPDATE Status
                SET embedding_status = 'complete',
                    last_updated = ?
                WHERE video_id = ?
                """,
                (datetime.now(), video_id)
            )
