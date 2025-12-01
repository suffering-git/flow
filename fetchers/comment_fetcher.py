"""
Comment fetching from YouTube Data API with language translation.

Handles:
- Synchronous comment downloads with pagination
- Language detection and translation
- Thread structure preservation
"""

import os
import time
import socket
from typing import Any, Optional
from datetime import datetime
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from httplib2 import Http

import config
from database.db_manager import DatabaseManager
from utils.logger import get_logger
from utils.translation import TranslationHelper
from utils.signal_handler import shutdown_requested, pause_requested

logger = get_logger(__name__)


class CommentFetcher:
    """
    Fetches video comments with language translation support.
    """

    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize comment fetcher.

        Args:
            db_manager: Database manager instance.
        """
        self.db_manager = db_manager
        http_client = Http(timeout=config.COMMENT_REQUEST_TIMEOUT)
        self.youtube = build(
            "youtube",
            "v3",
            developerKey=os.getenv("YOUTUBE_API_KEY"),
            http=http_client
        )
        self.translation_helper = TranslationHelper()

    def fetch_all_comments(self) -> None:
        """
        Fetch comments for all pending videos synchronously.
        """
        logger.info("🔄 Starting comment fetching")

        try:
            self._fetch_all_comments_impl()
        except Exception as e:
            logger.error(f"❌ Unhandled exception in fetch_all_comments: {e}", exc_info=True)
            raise
        finally:
            logger.info("🔄 Comment fetching method exiting")

    def _fetch_all_comments_impl(self) -> None:
        """Implementation of comment fetching."""

        # Base query to find pending comments
        query = """
            SELECT s.video_id FROM Status s
            JOIN Videos v ON s.video_id = v.video_id
            WHERE s.comments_status = 'pending'
        """
        params = []

        # Conditionally add filter for test data
        if config.PROCESS_TEST_DATA_ONLY:
            query += " AND v.is_test_data = ?"
            params.append(True)

        pending_videos = self.db_manager.fetchall(query, tuple(params))

        if not pending_videos:
            logger.info("✅ No pending comments to fetch")
            return

        video_ids = [row['video_id'] for row in pending_videos]
        logger.info(f"💬 Fetching comments for {len(video_ids)} videos")

        for video_id in video_ids:
            if shutdown_requested.is_set() or pause_requested.is_set():
                logger.info("Shutdown or pause requested, stopping comment fetching.")
                break
            try:
                self.fetch_comments(video_id)
            except Exception as e:
                logger.error(f"❌ An error occurred while fetching comments for {video_id}: {e}", exc_info=True)


        # Log summary statistics
        try:
            stats = self.db_manager.fetchone("""
                SELECT
                    COUNT(CASE WHEN comments_status = 'downloaded' THEN 1 END) as succeeded,
                    COUNT(CASE WHEN comments_status = 'disabled' THEN 1 END) as disabled,
                    COUNT(CASE WHEN comments_status = 'pending' THEN 1 END) as failed,
                    (SELECT COUNT(*) FROM RawComments) as total_comments
                FROM Status
            """)

            logger.info(
                f"✅ Comment fetching completed: "
                f"{stats['succeeded']} videos succeeded ({stats['total_comments']:,} comments), "
                f"{stats['disabled']} disabled, "
                f"{stats['failed']} failed"
            )
        except Exception as e:
            logger.warning(f"⚠️ Could not fetch comment statistics: {e}")
            logger.info("✅ Comment fetching completed")

    def fetch_comments(self, video_id: str) -> None:
        """
        Fetch all comments for a single video with pagination and retry logic.

        Args:
            video_id: YouTube video ID.
        """
        logger.debug(f"💬 Fetching comments: {video_id}")

        # Retry configuration
        max_retries = 3
        base_delay = 1.0  # seconds

        for attempt in range(max_retries + 1):
            try:
                # Recreate YouTube client on retries to get fresh SSL connection
                # Reason: Stale connections cause SSL handshake failures
                if attempt > 0:
                    logger.debug(f"🔄 Retry {attempt}/{max_retries} for comments: {video_id}")
                    http_client = Http(timeout=config.COMMENT_REQUEST_TIMEOUT)
                    self.youtube = build(
                        "youtube",
                        "v3",
                        developerKey=os.getenv("YOUTUBE_API_KEY"),
                        http=http_client
                    )
                    # Exponential backoff
                    time.sleep(base_delay * (2 ** (attempt - 1)))

                all_comments = []
                next_page_token = None

                # Paginate through all comment threads
                while True:
                    request = self.youtube.commentThreads().list(
                        part="snippet,replies",
                        videoId=video_id,
                        maxResults=100,
                        pageToken=next_page_token
                    )

                    response = request.execute()

                    # Process each comment thread
                    for item in response.get('items', []):
                        # Process top-level comment
                        processed_comment = self._process_comment(item)
                        processed_comment['video_id'] = video_id
                        all_comments.append(processed_comment)

                        # Process replies if any
                        if 'replies' in item:
                            for reply in item['replies']['comments']:
                                processed_reply = self._process_comment(reply)
                                processed_reply['video_id'] = video_id
                                all_comments.append(processed_reply)

                    # Check for more pages
                    next_page_token = response.get('nextPageToken')
                    if not next_page_token:
                        break

                # Store all comments in database
                if all_comments:
                    with self.db_manager.transaction() as cursor:
                        for comment in all_comments:
                            # Reason: Use INSERT OR IGNORE to handle re-runs gracefully
                            # (comments may already exist from previous runs)
                            cursor.execute(
                                """
                                INSERT OR IGNORE INTO RawComments
                                (comment_id, video_id, author_name, author_channel_id,
                                    comment_text, original_language, is_translated,
                                    parent_comment_id, like_count, published_at)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                """,
                                (
                                    comment['comment_id'],
                                    comment['video_id'],
                                    comment['author_name'],
                                    comment['author_channel_id'],
                                    comment['comment_text'],
                                    comment['original_language'],
                                    comment['is_translated'],
                                    comment['parent_comment_id'],
                                    comment['like_count'],
                                    comment['published_at']
                                )
                            )

                        # Update status
                        cursor.execute(
                            """
                            UPDATE Status
                            SET comments_status = 'downloaded',
                                last_updated = ?
                            WHERE video_id = ?
                            """,
                            (datetime.now(), video_id)
                        )

                # Log success at DEBUG level with details
                logger.debug(
                    f"✅ Comments downloaded: {video_id} ({len(all_comments):,} comments)"
                )

                # Success - break retry loop
                break

            except HttpError as e:
                error_reason = e.reason if hasattr(e, 'reason') else str(e)
                # Check if comments are disabled (permanent failure)
                if 'commentsDisabled' in str(e):
                    logger.warning(f"🟡 Comments disabled: {video_id}")
                    with self.db_manager.transaction() as cursor:
                        cursor.execute(
                            """
                            UPDATE Status
                            SET comments_status = 'disabled',
                                last_updated = ?
                            WHERE video_id = ?
                            """,
                            (datetime.now(), video_id)
                        )
                    break  # Don't retry for disabled comments
                elif 'videoNotFound' in str(e) or 'forbidden' in str(e):
                    logger.error(f"❌ Permanent error fetching comments for {video_id}: {error_reason}")
                    with self.db_manager.transaction() as cursor:
                        cursor.execute(
                            """
                            UPDATE Status
                            SET comments_status = 'failed',
                                last_updated = ?
                            WHERE video_id = ?
                            """,
                            (datetime.now(), video_id)
                        )
                    break
                else:
                    # Transient or unknown HTTP error - leave as pending
                    logger.error(f"❌ HTTP error for {video_id}: {error_reason} - leaving as pending.")
                    break  # Don't retry in this run

            except (TimeoutError, socket.timeout):
                # Request timeout - retry with backoff
                if attempt < max_retries:
                    logger.warning(
                        f"⚠️ Request timeout for {video_id} (attempt {attempt + 1}/{max_retries + 1})"
                    )
                    continue  # Retry
                else:
                    logger.error(
                        f"❌ Failed to fetch comments {video_id} after {max_retries + 1} attempts: Request timeout"
                    )
                    break

            except (OSError, ConnectionError) as e:
                # SSL/network errors - retry with backoff
                error_name = e.__class__.__name__
                is_ssl_error = 'SSL' in str(e) or 'ssl' in str(e).lower()

                if attempt < max_retries:
                    # Will retry
                    logger.warning(
                        f"⚠️ {error_name} for {video_id} (attempt {attempt + 1}/{max_retries + 1}): {e}"
                    )
                    continue  # Retry
                else:
                    # Max retries exhausted - log and leave as pending
                    logger.error(
                        f"❌ Failed to fetch comments {video_id} after {max_retries + 1} attempts: {e}"
                    )
                    break

            except Exception as e:
                # Unknown errors - check if SSL-related
                is_ssl_error = 'SSL' in str(e) or 'ssl' in str(e).lower()
                is_connection_error = any(x in str(e).lower() for x in [
                    'connection', 'timeout', 'remote end closed'
                ])

                if (is_ssl_error or is_connection_error) and attempt < max_retries:
                    # SSL/connection error - retry
                    logger.warning(
                        f"⚠️ Connection error for {video_id} (attempt {attempt + 1}/{max_retries + 1}): {e}"
                    )
                    continue  # Retry
                else:
                    # Non-retryable or max retries exhausted, log and leave as pending
                    if attempt >= max_retries:
                        logger.error(
                            f"❌ Failed to fetch comments {video_id} after {max_retries + 1} attempts: {e}"
                        )
                    else:
                        logger.error(f"❌ Unhandled error for {video_id}: {e}")
                    break

    def _process_comment(self, comment_data: dict[str, Any]) -> dict[str, Any]:
        """
        Process a single comment (detect language, translate if needed).

        Args:
            comment_data: Raw comment data from API.

        Returns:
            Processed comment dictionary ready for database insertion.
        """
        # Extract metadata
        metadata = self._extract_comment_metadata(comment_data)

        # Detect language and translate if needed
        original_text = metadata['comment_text']
        translated_text, original_lang, is_translated = (
            self.translation_helper.detect_and_translate(original_text)
        )

        # Return processed comment
        return {
            'comment_id': metadata['comment_id'],
            'author_name': metadata['author_name'],
            'author_channel_id': metadata['author_channel_id'],
            'comment_text': translated_text,
            'original_language': original_lang,
            'is_translated': is_translated,
            'parent_comment_id': metadata['parent_comment_id'],
            'like_count': metadata['like_count'],
            'published_at': metadata['published_at']
        }

    def _extract_comment_metadata(self, item: dict[str, Any]) -> dict[str, Any]:
        """
        Extract relevant fields from API response.

        Args:
            item: Comment item from API response.

        Returns:
            Dictionary with extracted fields.
        """
        # Determine if this is a top-level comment or a reply
        if 'snippet' in item and 'topLevelComment' in item['snippet']:
            # This is a comment thread - extract top-level comment
            comment = item['snippet']['topLevelComment']['snippet']
            comment_id = item['snippet']['topLevelComment']['id']
            parent_id = None
        else:
            # This is a reply
            comment = item['snippet']
            comment_id = item['id']
            parent_id = comment.get('parentId')

        return {
            'comment_id': comment_id,
            'author_name': comment['authorDisplayName'],
            'author_channel_id': comment.get('authorChannelId', {}).get('value', ''),
            'comment_text': comment['textDisplay'],
            'parent_comment_id': parent_id,
            'like_count': comment['likeCount'],
            'published_at': datetime.fromisoformat(
                comment['publishedAt'].replace('Z', '+00:00')
            )
        }
