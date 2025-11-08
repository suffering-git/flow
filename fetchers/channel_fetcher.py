"""
Channel and video discovery from YouTube Data API.

Handles:
- Channel metadata fetching
- Video list retrieval
- Video metadata fetching
"""

import os
import re
from typing import Any
from datetime import datetime
from googleapiclient.discovery import build

from database.db_manager import DatabaseManager
from utils.logger import get_logger

logger = get_logger(__name__)


class ChannelFetcher:
    """
    Fetches channel and video metadata from YouTube Data API v3.
    """

    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize channel fetcher.

        Args:
            db_manager: Database manager instance.
        """
        self.db_manager = db_manager
        self.youtube = build(
            "youtube",
            "v3",
            developerKey=os.getenv("YOUTUBE_API_KEY")
        )

    async def discover_channels(self, channel_ids: list[str]) -> None:
        """
        Discover and process all configured channels.

        For each channel:
        1. Fetch channel metadata
        2. Fetch all video IDs
        3. Fetch video metadata
        4. Initialize status records

        Args:
            channel_ids: List of YouTube channel IDs to process.
        """
        logger.info(f"🔄 Discovering {len(channel_ids)} channels")

        for channel_id in channel_ids:
            await self._process_channel(channel_id)

        logger.info("✅ Channel discovery completed")

    async def _process_channel(self, channel_id: str) -> None:
        """
        Process a single channel.

        Args:
            channel_id: YouTube channel ID.
        """
        logger.info(f"🔄 Processing channel: {channel_id}")

        # Check if channel already exists
        existing_channel = self.db_manager.fetchone(
            "SELECT channel_id FROM Channels WHERE channel_id = ?",
            (channel_id,)
        )

        # If channel doesn't exist, fetch metadata and insert
        if not existing_channel:
            channel_metadata = self._fetch_channel_metadata(channel_id)
            with self.db_manager.transaction() as cursor:
                cursor.execute(
                    """
                    INSERT INTO Channels (channel_id, channel_name)
                    VALUES (?, ?)
                    """,
                    (channel_metadata["channel_id"],
                     channel_metadata["channel_name"])
                )
            logger.info(f"✅ Added channel: {channel_metadata['channel_name']}")

        # Fetch all video IDs from channel
        video_ids = self._fetch_channel_videos(channel_id)

        # Process each video
        new_videos_count = 0
        for video_id in video_ids:
            # Check if video already exists
            existing_video = self.db_manager.fetchone(
                "SELECT video_id FROM Videos WHERE video_id = ?",
                (video_id,)
            )

            if not existing_video:
                # Fetch video metadata and insert
                try:
                    video_metadata = self._fetch_video_metadata(video_id)

                    with self.db_manager.transaction() as cursor:
                        # Insert video
                        cursor.execute(
                            """
                            INSERT INTO Videos
                            (video_id, channel_id, video_title, published_date,
                             duration_seconds, view_count, like_count)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                            """,
                            (
                                video_metadata["video_id"],
                                channel_id,
                                video_metadata["video_title"],
                                video_metadata["published_date"],
                                video_metadata["duration_seconds"],
                                video_metadata["view_count"],
                                video_metadata["like_count"]
                            )
                        )

                        # Initialize Status record
                        cursor.execute(
                            """
                            INSERT INTO Status (video_id)
                            VALUES (?)
                            """,
                            (video_id,)
                        )

                    new_videos_count += 1

                except Exception as e:
                    logger.error(f"❌ Failed to process video {video_id}: {e}")

        logger.info(
            f"✅ Channel {channel_id} processed: "
            f"{new_videos_count} new videos added "
            f"(total: {len(video_ids)})"
        )

    def _fetch_channel_metadata(self, channel_id: str) -> dict[str, Any]:
        """
        Fetch channel metadata from YouTube API.

        Args:
            channel_id: YouTube channel ID.

        Returns:
            Channel metadata dictionary.
        """
        request = self.youtube.channels().list(
            part="snippet",
            id=channel_id
        )
        response = request.execute()

        if not response.get("items"):
            raise ValueError(f"Channel not found: {channel_id}")

        snippet = response["items"][0]["snippet"]
        return {
            "channel_id": channel_id,
            "channel_name": snippet["title"]
        }

    def _fetch_channel_videos(self, channel_id: str) -> list[str]:
        """
        Fetch all video IDs from a channel.

        Args:
            channel_id: YouTube channel ID.

        Returns:
            List of video IDs.
        """
        # Get channel's uploads playlist ID
        request = self.youtube.channels().list(
            part="contentDetails",
            id=channel_id
        )
        response = request.execute()

        if not response.get("items"):
            raise ValueError(f"Channel not found: {channel_id}")

        uploads_playlist_id = (
            response["items"][0]["contentDetails"]
            ["relatedPlaylists"]["uploads"]
        )

        # Paginate through all videos in uploads playlist
        video_ids = []
        next_page_token = None

        while True:
            request = self.youtube.playlistItems().list(
                part="contentDetails",
                playlistId=uploads_playlist_id,
                maxResults=50,
                pageToken=next_page_token
            )
            response = request.execute()

            # Extract video IDs
            for item in response.get("items", []):
                video_id = item["contentDetails"]["videoId"]
                video_ids.append(video_id)

            # Check for more pages
            next_page_token = response.get("nextPageToken")
            if not next_page_token:
                break

        logger.debug(f"📹 Found {len(video_ids)} videos in channel {channel_id}")
        return video_ids

    def _fetch_video_metadata(self, video_id: str) -> dict[str, Any]:
        """
        Fetch video metadata from YouTube API.

        Args:
            video_id: YouTube video ID.

        Returns:
            Video metadata dictionary with fields:
            - video_title
            - published_date
            - duration_seconds
            - view_count
            - like_count
        """
        request = self.youtube.videos().list(
            part="snippet,contentDetails,statistics",
            id=video_id
        )
        response = request.execute()

        if not response.get("items"):
            raise ValueError(f"Video not found: {video_id}")

        item = response["items"][0]
        snippet = item["snippet"]
        content_details = item["contentDetails"]
        statistics = item["statistics"]

        # Parse ISO 8601 duration to seconds
        duration_str = content_details["duration"]
        duration_seconds = self._parse_iso8601_duration(duration_str)

        # Parse published date
        published_date = datetime.fromisoformat(
            snippet["publishedAt"].replace("Z", "+00:00")
        )

        return {
            "video_id": video_id,
            "video_title": snippet["title"],
            "published_date": published_date,
            "duration_seconds": duration_seconds,
            "view_count": int(statistics.get("viewCount", 0)),
            "like_count": int(statistics.get("likeCount", 0))
        }

    def _parse_iso8601_duration(self, duration_str: str) -> int:
        """
        Parse ISO 8601 duration to seconds.

        Args:
            duration_str: Duration string (e.g., "PT4M13S", "PT1H2M10S")

        Returns:
            Duration in seconds.
        """
        # Pattern: PT(nH)?(nM)?(nS)?
        pattern = r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?'
        match = re.match(pattern, duration_str)

        if not match:
            logger.warning(f"Could not parse duration: {duration_str}")
            return 0

        hours = int(match.group(1) or 0)
        minutes = int(match.group(2) or 0)
        seconds = int(match.group(3) or 0)

        return hours * 3600 + minutes * 60 + seconds
