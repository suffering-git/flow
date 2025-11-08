"""
Main entry point for the YouTube Data Processing Pipeline.

This script orchestrates the entire pipeline from data fetching through
AI processing to embedding generation.
"""

import asyncio
import os
from dotenv import load_dotenv

import config
from utils.logger import get_logger
from utils.signal_handler import setup_signal_handlers, shutdown_requested, pause_requested
from database.db_manager import DatabaseManager
from fetchers.channel_fetcher import ChannelFetcher
from fetchers.transcript_fetcher import TranscriptFetcher
from fetchers.comment_fetcher import CommentFetcher
from processors.stage1_processor import Stage1Processor
from processors.stage2_processor import Stage2Processor
from processors.stage3_processor import Stage3Processor

logger = get_logger(__name__)


async def main() -> None:
    """
    Execute the complete data processing pipeline.

    Pipeline stages:
    1. Channel & video discovery
    2. Transcript & comment downloads (concurrent)
    3. Stage 1: Data compression
    4. Stage 2: Topic extraction & atomic insights
    5. Stage 3: Embedding generation
    """
    # Load environment variables from .env file
    load_dotenv()

    # Validate required environment variables
    required_env_vars = ["YOUTUBE_API_KEY", "GEMINI_API_KEY"]
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    if missing_vars:
        logger.error(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        return

    # Setup signal handlers for graceful shutdown/pause
    setup_signal_handlers()

    logger.info("🎯 Starting YouTube Data Processing Pipeline")

    # Initialize database
    db_manager = DatabaseManager(config.DATABASE_PATH)
    db_manager.initialize_database()

    # TODO: Implement channel & video discovery
    # channel_fetcher = ChannelFetcher(db_manager)
    # await channel_fetcher.discover_channels(config.CHANNEL_IDS)

    if shutdown_requested.is_set():
        logger.info("⏸️ Shutdown requested during channel discovery")
        return

    # TODO: Implement transcript & comment fetching
    # transcript_fetcher = TranscriptFetcher(db_manager)
    # comment_fetcher = CommentFetcher(db_manager)
    # await asyncio.gather(
    #     transcript_fetcher.fetch_all_transcripts(),
    #     comment_fetcher.fetch_all_comments()
    # )

    if config.STOP_AFTER_STAGE == "downloads":
        logger.info("🎯 Stopped after downloads as configured")
        return

    if shutdown_requested.is_set():
        logger.info("⏸️ Shutdown requested after downloads")
        return

    # TODO: Implement Stage 1 processing
    # stage1 = Stage1Processor(db_manager)
    # await stage1.process_all_videos()

    if config.STOP_AFTER_STAGE == "stage_1":
        logger.info("🎯 Stopped after Stage 1 as configured")
        return

    if shutdown_requested.is_set():
        logger.info("⏸️ Shutdown requested after Stage 1")
        return

    # TODO: Implement Stage 2 processing
    # stage2 = Stage2Processor(db_manager)
    # await stage2.process_all_videos()

    if config.STOP_AFTER_STAGE == "stage_2":
        logger.info("🎯 Stopped after Stage 2 as configured")
        return

    if shutdown_requested.is_set():
        logger.info("⏸️ Shutdown requested after Stage 2")
        return

    # TODO: Implement Stage 3 processing
    # stage3 = Stage3Processor(db_manager)
    # await stage3.generate_all_embeddings()

    logger.info("✅ Pipeline completed successfully")


if __name__ == "__main__":
    asyncio.run(main())
