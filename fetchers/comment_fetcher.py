"""
Comment fetching from YouTube Data API with language translation.

Handles:
- Asynchronous comment downloads with pagination
- Language detection and translation
- Thread structure preservation
"""

import os
import asyncio
from typing import Any, Optional
from datetime import datetime
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

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
        self.youtube = build(
            "youtube",
            "v3",
            developerKey=os.getenv("YOUTUBE_API_KEY")
        )
        self.translation_helper = TranslationHelper()
        self.semaphore = asyncio.Semaphore(config.MAX_COMMENT_CONCURRENCY)

    async def fetch_all_comments(self) -> None:
        """
        Fetch comments for all pending videos concurrently.

        Respects MAX_COMMENT_CONCURRENCY limit (default 10 RPS).
        """
        logger.info("🔄 Starting comment fetching")

        # Get all pending videos
        pending_videos = self.db_manager.fetchall(
            """
            SELECT video_id FROM Status
            WHERE comments_status = 'pending'
            """
        )

        if not pending_videos:
            logger.info("✅ No pending comments to fetch")
            return

        video_ids = [row['video_id'] for row in pending_videos]
        logger.info(f"💬 Fetching comments for {len(video_ids)} videos")

        # Create tasks for all videos
        tasks = []
        for video_id in video_ids:
            # Check for shutdown/pause signals
            if shutdown_requested.is_set() or pause_requested.is_set():
                break
            tasks.append(self.fetch_comments(video_id))

        # Execute concurrently (semaphore in fetch_comments controls rate)
        await asyncio.gather(*tasks, return_exceptions=True)

        logger.info("✅ Comment fetching completed")

    async def fetch_comments(self, video_id: str) -> None:
        """
        Fetch all comments for a single video with pagination.

        Args:
            video_id: YouTube video ID.
        """
        async with self.semaphore:
            logger.debug(f"💬 Fetching comments: {video_id}")

            try:
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

                    # Execute request in thread pool (it's synchronous)
                    loop = asyncio.get_event_loop()
                    response = await loop.run_in_executor(
                        None,
                        request.execute
                    )

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
                            cursor.execute(
                                """
                                INSERT INTO RawComments
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

                logger.debug(
                    f"✅ Fetched {len(all_comments)} comments for {video_id}"
                )

            except HttpError as e:
                # Check if comments are disabled
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
                else:
                    # Transient error - leave as pending
                    logger.error(f"❌ Failed to fetch comments {video_id}: {e}")

            except Exception as e:
                # Other errors - leave as pending
                logger.error(f"❌ Failed to fetch comments {video_id}: {e}")

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
