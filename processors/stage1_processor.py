"""
Stage 1: Data Compression Processor.

Compresses raw transcripts and comments while preserving timestamps.
Uses Gemini Flash-Lite for cost-effective compression.
"""

import asyncio
import json
from typing import Optional
from datetime import datetime
from pathlib import Path

import config
from database.db_manager import DatabaseManager
from models.stage1_models import Stage1Output
from utils.gemini_client import GeminiClient
from utils.logger import get_logger
from utils.rate_limiter import RateLimiter
from utils.signal_handler import shutdown_requested, pause_requested

logger = get_logger(__name__)


class Stage1Processor:
    """
    Processes raw data through Stage 1 compression.
    """

    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize Stage 1 processor.

        Args:
            db_manager: Database manager instance.
        """
        self.db_manager = db_manager
        self.gemini_client = GeminiClient(config.STAGE1_MODEL)
        self.rate_limiter = RateLimiter(
            config.STAGE1_MODEL,
            max_concurrent=config.STAGE1_MAX_CONCURRENT
        )
        self.semaphore = asyncio.Semaphore(config.STAGE1_MAX_CONCURRENT)

    async def process_all_videos(self) -> None:
        """
        Process all videos ready for Stage 1.

        A video is ready when:
        - transcript_status is 'downloaded' OR 'unavailable'
        - comments_status is 'downloaded' OR 'disabled'
        - stage_1_status is 'pending'
        """
        logger.info("🔄 Starting Stage 1 processing")

        # Base query to find videos ready for Stage 1
        query = """
            SELECT s.video_id FROM Status s
            JOIN Videos v ON s.video_id = v.video_id
            WHERE (s.transcript_status IN ('downloaded', 'unavailable'))
              AND (s.comments_status IN ('downloaded', 'disabled', 'failed'))
              AND s.stage_1_status = 'pending'
        """
        params = []

        # Conditionally add filter for test data
        if config.PROCESS_TEST_DATA_ONLY:
            query += " AND v.is_test_data = ?"
            params.append(True)

        ready_videos = self.db_manager.fetchall(query, tuple(params))

        if not ready_videos:
            logger.info("✅ No videos ready for Stage 1")
            return

        video_ids = [row['video_id'] for row in ready_videos]
        logger.info(f"🔄 Processing {len(video_ids)} videos through Stage 1")

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
            completed = self.db_manager.fetchone(
                "SELECT COUNT(*) as cnt FROM Status WHERE stage_1_status = 'completed'"
            )
            logger.info(f"✅ Stage 1 processing completed: {completed['cnt']} videos compressed")
        except Exception as e:
            logger.warning(f"⚠️ Could not fetch Stage 1 statistics: {e}")
            logger.info("✅ Stage 1 processing completed")

    async def process_video(self, video_id: str) -> None:
        """
        Process a single video through Stage 1.

        Args:
            video_id: YouTube video ID.
        """
        async with self.semaphore:
            try:
                logger.debug(f"🔄 Stage 1 processing: {video_id}")

                # Fetch transcript (if available)
                transcript_row = self.db_manager.fetchone(
                    """
                    SELECT transcript_text FROM RawTranscripts
                    WHERE video_id = ?
                    """,
                    (video_id,)
                )
                transcript_text = transcript_row['transcript_text'] if transcript_row else None

                # Fetch comments (if available)
                comment_rows = self.db_manager.fetchall(
                    """
                    SELECT comment_id, comment_text FROM RawComments
                    WHERE video_id = ?
                    ORDER BY published_at DESC
                    """,
                    (video_id,)
                )
                comments = [
                    {
                        'comment_id': row['comment_id'],
                        'comment_text': row['comment_text']
                    }
                    for row in comment_rows
                ]

                # Build prompt
                prompt = self._build_prompt(transcript_text, comments)

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

                # Store compressed data
                with self.db_manager.transaction() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO CompressedData
                        (video_id, compressed_transcript, compressed_comments)
                        VALUES (?, ?, ?)
                        """,
                        (
                            video_id,
                            validated_output.compressed_transcript,
                            json.dumps([c.model_dump() for c in validated_output.compressed_comments])
                        )
                    )

                    # Update status
                    cursor.execute(
                        """
                        UPDATE Status
                        SET stage_1_status = 'complete',
                            last_updated = ?
                        WHERE video_id = ?
                        """,
                        (datetime.now(), video_id)
                    )

                logger.debug(f"✅ Stage 1 completed: {video_id}")

            except Exception as e:
                logger.error(f"❌ Stage 1 failed for {video_id}: {e}")
                # Update status to failed
                with self.db_manager.transaction() as cursor:
                    cursor.execute(
                        """
                        UPDATE Status
                        SET stage_1_status = 'failed',
                            last_updated = ?
                        WHERE video_id = ?
                        """,
                        (datetime.now(), video_id)
                    )

    def _build_prompt(
        self,
        transcript_text: Optional[str],
        comments: list[dict[str, str]]
    ) -> str:
        """
        Build Stage 1 compression prompt.

        Args:
            transcript_text: Raw transcript with embedded timestamps.
            comments: List of comment dicts with comment_id and comment_text.

        Returns:
            Complete prompt string.
        """
        # Load prompt template
        prompt_path = Path("prompts/stage1_prompt.txt")
        with open(prompt_path, 'r', encoding='utf-8') as f:
            template = f.read()

        # Build data section
        data_parts = []

        # Add transcript if available
        if transcript_text:
            data_parts.append("=== TRANSCRIPT ===")
            data_parts.append(transcript_text)
            data_parts.append("")

        # Add comments if available
        if comments:
            data_parts.append("=== COMMENTS ===")
            for comment in comments:
                data_parts.append(
                    f"Comment ID: {comment['comment_id']}\n{comment['comment_text']}\n"
                )
            data_parts.append("")

        data_section = "\n".join(data_parts)

        # Combine template and data
        full_prompt = f"{template}\n\n{data_section}"

        return full_prompt

    def _validate_and_parse_response(self, response: str) -> Stage1Output:
        """
        Validate and parse AI response.

        Args:
            response: Raw JSON response from Gemini.

        Returns:
            Validated Stage1Output model.

        Raises:
            ValidationError: If response doesn't match expected structure.
        """
        # Parse JSON
        data = json.loads(response)

        # Validate with Pydantic model
        validated = Stage1Output(**data)

        return validated
