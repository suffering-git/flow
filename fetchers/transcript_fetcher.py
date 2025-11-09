"""
Transcript fetching with Webshare proxy support.

Handles:
- Asynchronous transcript downloads via rotating proxies
- Language detection and translation
- Timestamp embedding in text
"""

import os
import asyncio
from typing import Optional
from datetime import datetime

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.proxies import WebshareProxyConfig
from youtube_transcript_api._errors import NoTranscriptFound

import config
from database.db_manager import DatabaseManager
from utils.logger import get_logger
from utils.signal_handler import shutdown_requested, pause_requested

logger = get_logger(__name__)


class TranscriptFetcher:
    """
    Fetches video transcripts asynchronously with proxy support.
    """

    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize transcript fetcher.

        Args:
            db_manager: Database manager instance.
        """
        self.db_manager = db_manager

        # Configure proxy for YouTube Transcript API if available
        proxy_username = os.getenv("WEBSHARE_PROXY_USERNAME")
        proxy_password = os.getenv("WEBSHARE_PROXY_PASSWORD")

        if proxy_username and proxy_password:
            self.proxy_config = WebshareProxyConfig(
                proxy_username=proxy_username,
                proxy_password=proxy_password,
            )
            logger.info("✅ Initialized transcript fetcher with Webshare proxies")
        else:
            self.proxy_config = None
            logger.warning("🟡 No proxy credentials found, using direct connection")

    async def fetch_all_transcripts(self) -> None:
        """
        Fetch transcripts for all pending videos concurrently.
        """
        logger.info("🔄 Starting transcript fetching")

        try:
            return await self._fetch_all_transcripts_impl()
        except Exception as e:
            logger.error(f"❌ Unhandled exception in fetch_all_transcripts: {e}", exc_info=True)
            raise
        finally:
            logger.info("🔄 Transcript fetching method exiting")

    async def _fetch_all_transcripts_impl(self) -> None:
        """Implementation of transcript fetching."""

        # Get all pending videos
        pending_videos = self.db_manager.fetchall(
            """
            SELECT video_id FROM Status
            WHERE transcript_status = 'pending'
            """
        )

        if not pending_videos:
            logger.info("✅ No pending transcripts to fetch")
            return

        video_ids = [row['video_id'] for row in pending_videos]
        logger.info(f"📥 Fetching {len(video_ids)} transcripts")

        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(config.MAX_TRANSCRIPT_CONCURRENCY)

        async def fetch_with_semaphore(video_id: str):
            """Wrapper to enforce concurrency limit."""
            async with semaphore:
                # Check for shutdown/pause signals
                if shutdown_requested.is_set() or pause_requested.is_set():
                    return
                # Wrap with timeout to prevent indefinite hanging
                # Reason: Prevent individual transcripts from hanging the pipeline
                try:
                    await asyncio.wait_for(
                        self.fetch_transcript(video_id),
                        timeout=config.TRANSCRIPT_FETCH_TIMEOUT
                    )
                except asyncio.TimeoutError:
                    logger.error(f"❌ Transcript fetch timed out for {video_id}")
                    # Mark as failed in database
                    from datetime import datetime
                    with self.db_manager.transaction() as cursor:
                        cursor.execute(
                            """
                            UPDATE Status
                            SET transcript_status = 'failed',
                                last_updated = ?
                            WHERE video_id = ?
                            """,
                            (datetime.now(), video_id)
                        )

        # Create tasks for all videos
        tasks = [fetch_with_semaphore(vid) for vid in video_ids]

        # Execute concurrently
        await asyncio.gather(*tasks, return_exceptions=True)

        # Log summary statistics
        try:
            stats = self.db_manager.fetchone("""
                SELECT
                    COUNT(CASE WHEN transcript_status = 'downloaded' THEN 1 END) as succeeded,
                    COUNT(CASE WHEN transcript_status = 'unavailable' THEN 1 END) as unavailable,
                    COUNT(CASE WHEN transcript_status = 'pending' THEN 1 END) as failed
                FROM Status
            """)

            logger.info(
                f"✅ Transcript fetching completed: "
                f"{stats['succeeded']} succeeded, "
                f"{stats['unavailable']} unavailable, "
                f"{stats['failed']} failed"
            )
        except Exception as e:
            logger.warning(f"⚠️ Could not fetch transcript statistics: {e}")
            logger.info("✅ Transcript fetching completed")

    async def fetch_transcript(self, video_id: str) -> None:
        """
        Fetch transcript for a single video.

        Handles:
        - Language detection
        - Translation to English if needed
        - Timestamp embedding
        - Error handling (permanent vs transient)

        Args:
            video_id: YouTube video ID.
        """
        logger.debug(f"📥 Fetching transcript: {video_id}")

        try:
            # Fetch transcript list (this is synchronous, so run in executor)
            # Reason: Use instance method with optional proxy configuration
            loop = asyncio.get_event_loop()

            if self.proxy_config:
                ytt_api = YouTubeTranscriptApi(proxy_config=self.proxy_config)
            else:
                ytt_api = YouTubeTranscriptApi()

            transcript_list = await loop.run_in_executor(
                None,
                lambda: ytt_api.list(video_id)
            )

            # Try to get English transcript first
            try:
                transcript = transcript_list.find_transcript(['en'])
                original_language = 'en'
                is_translated = False
            except:
                # Get any available transcript and translate
                available_transcripts = list(transcript_list)
                if not available_transcripts:
                    raise Exception("No transcripts available")

                transcript = available_transcripts[0]
                original_language = transcript.language_code

                # Translate to English if not already
                if original_language != 'en':
                    transcript = transcript.translate('en')
                    is_translated = True
                else:
                    is_translated = False

            # Fetch transcript data
            fetched_transcript = await loop.run_in_executor(
                None,
                transcript.fetch
            )

            # Convert to raw data (list of dicts)
            # Reason: FetchedTranscript has .to_raw_data() method
            transcript_data = fetched_transcript.to_raw_data()

            # Embed timestamps in text
            transcript_text = self._embed_timestamps(transcript_data)

            # Store in database
            with self.db_manager.transaction() as cursor:
                # Reason: Check if transcript already exists before inserting
                # (to handle re-runs gracefully)
                existing = cursor.execute(
                    "SELECT video_id FROM RawTranscripts WHERE video_id = ?",
                    (video_id,)
                ).fetchone()

                if not existing:
                    cursor.execute(
                        """
                        INSERT INTO RawTranscripts
                        (video_id, original_language, transcript_text, is_translated)
                        VALUES (?, ?, ?, ?)
                        """,
                        (video_id, original_language, transcript_text, is_translated)
                    )

                # Update status
                cursor.execute(
                    """
                    UPDATE Status
                    SET transcript_status = 'downloaded',
                        last_updated = ?
                    WHERE video_id = ?
                    """,
                    (datetime.now(), video_id)
                )

            # Log success at DEBUG level with details
            word_count = len(transcript_text.split())
            logger.debug(f"✅ Transcript downloaded: {video_id} ({word_count:,} words, lang: {original_language})")

        except NoTranscriptFound:
            # Permanent failure - no transcript available
            logger.warning(f"🟡 No transcript available: {video_id}")
            with self.db_manager.transaction() as cursor:
                cursor.execute(
                    """
                    UPDATE Status
                    SET transcript_status = 'unavailable',
                        last_updated = ?
                    WHERE video_id = ?
                    """,
                    (datetime.now(), video_id)
                )

        except Exception as e:
            # Transient error - leave as pending
            logger.error(f"❌ Failed to fetch transcript {video_id}: {e}")

    def _embed_timestamps(
        self,
        transcript_snippets: list[dict]
    ) -> str:
        """
        Embed timestamps into transcript text.

        Args:
            transcript_snippets: List of transcript snippets with 'text' and 'start' keys.

        Returns:
            Full transcript text with embedded timestamps.
            Format: "[00:02:42] text here [00:03:15] more text"
        """
        embedded_parts = []

        for snippet in transcript_snippets:
            timestamp = self._seconds_to_timestamp(snippet['start'])
            text = snippet['text'].strip()
            embedded_parts.append(f"[{timestamp}] {text}")

        return " ".join(embedded_parts)

    def _seconds_to_timestamp(self, seconds: float) -> str:
        """
        Convert seconds to HH:MM:SS format.

        Args:
            seconds: Time in seconds.

        Returns:
            Formatted timestamp string.
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
