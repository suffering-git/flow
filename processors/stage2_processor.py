"""
Stage 2: Topic Extraction and Analysis Processor.

Generates topic summaries and atomic insights with timestamp preservation.
Uses Gemini Pro for powerful analysis.
"""

import asyncio
import json
from typing import Any
from datetime import datetime
from pathlib import Path

import config
from database.db_manager import DatabaseManager
from models.stage2_models import Stage2Output
from processors.timestamp_parser import TimestampParser
from utils.gemini_client import GeminiClient
from utils.logger import get_logger
from utils.rate_limiter import RateLimiter
from utils.signal_handler import shutdown_requested, pause_requested

logger = get_logger(__name__)


class Stage2Processor:
    """
    Processes compressed data through Stage 2 analysis.
    """

    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize Stage 2 processor.

        Args:
            db_manager: Database manager instance.
        """
        self.db_manager = db_manager
        self.gemini_client = GeminiClient(config.STAGE2_MODEL)
        self.rate_limiter = RateLimiter(
            config.STAGE2_MODEL,
            max_concurrent=config.STAGE2_MAX_CONCURRENT
        )
        self.timestamp_parser = TimestampParser()
        self.semaphore = asyncio.Semaphore(config.STAGE2_MAX_CONCURRENT)

    async def process_all_videos(self) -> None:
        """
        Process all videos ready for Stage 2.

        A video is ready when:
        - stage_1_status is 'complete'
        - stage_2_status is 'pending'
        """
        logger.info("🔄 Starting Stage 2 processing")

        # Get all videos ready for Stage 2
        ready_videos = self.db_manager.fetchall(
            """
            SELECT video_id FROM Status
            WHERE stage_1_status = 'complete'
              AND stage_2_status = 'pending'
            """
        )

        if not ready_videos:
            logger.info("✅ No videos ready for Stage 2")
            return

        video_ids = [row['video_id'] for row in ready_videos]
        logger.info(f"🔄 Processing {len(video_ids)} videos through Stage 2")

        # Create tasks for concurrent processing
        tasks = []
        for video_id in video_ids:
            # Check for shutdown/pause signals
            if shutdown_requested.is_set() or pause_requested.is_set():
                break
            tasks.append(self.process_video(video_id))

        # Execute concurrently
        await asyncio.gather(*tasks, return_exceptions=True)

        # Log summary statistics
        try:
            stats = self.db_manager.fetchone("""
                SELECT
                    COUNT(*) as videos_processed,
                    (SELECT COUNT(*) FROM TopicSummaries) as topics_created,
                    (SELECT COUNT(*) FROM AtomicInsights) as insights_created
                FROM Status
                WHERE stage_2_status = 'completed'
            """)
            logger.info(
                f"✅ Stage 2 processing completed: "
                f"{stats['videos_processed']} videos, "
                f"{stats['topics_created']} topics, "
                f"{stats['insights_created']} insights"
            )
        except Exception as e:
            logger.warning(f"⚠️ Could not fetch Stage 2 statistics: {e}")
            logger.info("✅ Stage 2 processing completed")

    async def process_video(self, video_id: str) -> None:
        """
        Process a single video through Stage 2.

        Args:
            video_id: YouTube video ID.
        """
        async with self.semaphore:
            try:
                logger.debug(f"🔄 Stage 2 processing: {video_id}")

                # Fetch compressed data
                compressed_row = self.db_manager.fetchone(
                    """
                    SELECT compressed_transcript, compressed_comments
                    FROM CompressedData
                    WHERE video_id = ?
                    """,
                    (video_id,)
                )

                if not compressed_row:
                    logger.warning(f"🟡 No compressed data for {video_id}")
                    return

                compressed_transcript = compressed_row['compressed_transcript']
                compressed_comments_json = compressed_row['compressed_comments']

                # Parse comments JSON
                compressed_comments = json.loads(compressed_comments_json) if compressed_comments_json else []

                # Build prompt
                prompt = self._build_prompt(compressed_transcript, compressed_comments)

                # Call Gemini API
                response = await self.gemini_client.generate_content(prompt)

                # Track usage
                await self.rate_limiter.track_request(
                    response['input_tokens'],
                    response['output_tokens']
                )

                # Validate and parse response
                validated_output = self._validate_and_parse_response(
                    response['response_text']
                )

                # Process and store topics with timestamp parsing
                self._process_and_store_topics(video_id, validated_output)

                # Update status
                with self.db_manager.transaction() as cursor:
                    cursor.execute(
                        """
                        UPDATE Status
                        SET stage_2_status = 'complete',
                            last_updated = ?
                        WHERE video_id = ?
                        """,
                        (datetime.now(), video_id)
                    )

                logger.debug(f"✅ Stage 2 completed: {video_id}")

            except Exception as e:
                logger.error(f"❌ Stage 2 failed for {video_id}: {e}")
                # Update status to failed
                with self.db_manager.transaction() as cursor:
                    cursor.execute(
                        """
                        UPDATE Status
                        SET stage_2_status = 'failed',
                            last_updated = ?
                        WHERE video_id = ?
                        """,
                        (datetime.now(), video_id)
                    )

    def _build_prompt(
        self,
        compressed_transcript: str,
        compressed_comments: list[dict[str, str]]
    ) -> str:
        """
        Build Stage 2 analysis prompt.

        Args:
            compressed_transcript: Compressed transcript with timestamps.
            compressed_comments: List of dicts with comment_id and compressed_text.

        Returns:
            Complete prompt string.
        """
        # Load prompt template
        prompt_path = Path("prompts/stage2_prompt.txt")
        with open(prompt_path, 'r', encoding='utf-8') as f:
            template = f.read()

        # Build data section
        data_parts = []

        # Add compressed transcript
        if compressed_transcript:
            data_parts.append("=== COMPRESSED TRANSCRIPT ===")
            data_parts.append(compressed_transcript)
            data_parts.append("")

        # Add compressed comments
        if compressed_comments:
            data_parts.append("=== COMPRESSED COMMENTS ===")
            for comment in compressed_comments:
                data_parts.append(
                    f"Comment ID: {comment['comment_id']}\n{comment['compressed_text']}\n"
                )
            data_parts.append("")

        data_section = "\n".join(data_parts)

        # Combine template and data
        full_prompt = f"{template}\n\n{data_section}"

        return full_prompt

    def _validate_and_parse_response(self, response: str) -> Stage2Output:
        """
        Validate and parse AI response.

        Args:
            response: Raw JSON response from Gemini.

        Returns:
            Validated Stage2Output model.

        Raises:
            ValidationError: If response doesn't match expected structure.
        """
        # Parse JSON
        data = json.loads(response)

        # Validate with Pydantic model
        validated = Stage2Output(**data)

        return validated

    def _process_and_store_topics(
        self,
        video_id: str,
        stage2_output: Stage2Output
    ) -> None:
        """
        Process topics and store in database.

        Parses inline timestamp syntax and flattens nested structure.

        Args:
            video_id: YouTube video ID.
            stage2_output: Validated Stage 2 output.
        """
        with self.db_manager.transaction() as cursor:
            for topic in stage2_output.topics:
                # Parse timestamp syntax from summary text
                parsed_summary = self.timestamp_parser.parse_text_with_timestamps(
                    topic.summary_text
                )

                # Store topic summary
                cursor.execute(
                    """
                    INSERT INTO TopicSummaries
                    (video_id, topic_title, summary_text, summary_timestamps,
                     source_type, confidence_score, comment_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        video_id,
                        topic.topic_title,
                        parsed_summary['full_text'],
                        json.dumps(parsed_summary['timestamped_segments']),
                        topic.source_type,
                        topic.confidence_score,
                        topic.comment_id
                    )
                )

                # Get the summary_id
                summary_id = cursor.lastrowid

                # Store nested atomic insights
                for insight in topic.atomic_insights:
                    # Parse timestamp syntax from insight text
                    parsed_insight = self.timestamp_parser.parse_text_with_timestamps(
                        insight.insight_text
                    )

                    cursor.execute(
                        """
                        INSERT INTO AtomicInsights
                        (summary_id, insight_type, insight_text,
                         insight_timestamps, confidence_score, source_type)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (
                            summary_id,
                            insight.insight_type,
                            parsed_insight['full_text'],
                            json.dumps(parsed_insight['timestamped_segments']),
                            insight.confidence_score,
                            topic.source_type
                        )
                    )
