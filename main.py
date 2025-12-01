"""
Main entry point for the YouTube Data Processing Pipeline.

This script orchestrates the entire pipeline from data fetching through
AI processing to embedding generation.
"""

import asyncio
import os
from dotenv import load_dotenv
from utils.logger import get_logger, set_session_timestamp, get_session_log_path

# Load environment variables and set session timestamp as early as possible
# Reason: Ensures consistent timestamp for all loggers and makes env vars available immediately
load_dotenv()
set_session_timestamp()

# Get the logger after the timestamp is set
logger = get_logger(__name__)

# All other imports should come after the logger is ready
import config
from utils.signal_handler import setup_signal_handlers, shutdown_requested, pause_requested
from utils.heartbeat import start_heartbeat, stop_heartbeat
from database.db_manager import DatabaseManager
from fetchers.channel_fetcher import ChannelFetcher
from fetchers.transcript_fetcher import TranscriptFetcher
from fetchers.comment_fetcher import CommentFetcher
from processors.stage1_processor import Stage1Processor
from processors.stage2_processor import Stage2Processor
from processors.stage3_processor import Stage3Processor


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
    # Use the globally initialized logger
    global logger

    try:
        # Validate required environment variables
        logger.debug("🔍 Validating environment variables.")
        required_env_vars = ["YOUTUBE_API_KEY", "GEMINI_API_KEY"]
        missing_vars = [var for var in required_env_vars if not os.getenv(var)]
        if missing_vars:
            logger.error(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
            return
        logger.debug("🔍 Environment variables validated.")

        # Setup signal handlers for graceful shutdown/pause
        setup_signal_handlers()
        logger.debug("🔍 Signal handlers configured.")

        # Start heartbeat monitor for diagnostics
        start_heartbeat(interval=10)
        logger.debug("🔍 Heartbeat monitor started.")

        logger.info("🎯 Starting YouTube Data Processing Pipeline")

        # Initialize database
        db_manager = DatabaseManager(config.DATABASE_PATH)
        db_manager.initialize_database()

        # Stage 1: Channel & video discovery
        channel_fetcher = ChannelFetcher(db_manager)
        await channel_fetcher.discover_channels(config.CHANNEL_IDS)

        if shutdown_requested.is_set():
            logger.info("⏸️ Shutdown requested during channel discovery")
            return

        # Stage 2: Transcript & comment fetching (concurrent)
        logger.info("🔄 Starting concurrent transcript & comment fetching")
        import threading
        logger.info(f"📊 Active threads before fetch: {threading.active_count()}")

        transcript_fetcher = TranscriptFetcher(db_manager)
        comment_fetcher = CommentFetcher(db_manager)

        await transcript_fetcher.fetch_all_transcripts()
        comment_fetcher.fetch_all_comments()


        if config.STOP_AFTER_STAGE == "downloads":
            logger.info("🎯 Stopped after downloads as configured")
            return

        if shutdown_requested.is_set():
            logger.info("⏸️ Shutdown requested after downloads")
            return

        # Stage 3: Data compression (Stage 1)
        stage1 = Stage1Processor(db_manager)
        await stage1.process_all_videos()

        if config.STOP_AFTER_STAGE == "stage_1":
            logger.info("🎯 Stopped after Stage 1 as configured")
            return

        if shutdown_requested.is_set():
            logger.info("⏸️ Shutdown requested after Stage 1")
            return

        # Stage 4: Topic extraction & atomic insights (Stage 2)
        stage2 = Stage2Processor(db_manager)
        await stage2.process_all_videos()

        if config.STOP_AFTER_STAGE == "stage_2":
            logger.info("🎯 Stopped after Stage 2 as configured")
            return

        if shutdown_requested.is_set():
            logger.info("⏸️ Shutdown requested after Stage 2")
            return

        # Stage 5: Embedding generation (Stage 3)
        stage3 = Stage3Processor(db_manager)
        logger.info("✅ Pipeline completed successfully")
        logger.info("=" * 80)

    except Exception as e:
        logger.error(f"❌ Pipeline failed with exception: {e}", exc_info=True)
        logger.info("=" * 80)
        raise
    finally:
        # Stop heartbeat monitor
        logger.info("🔄 Cleaning up...")
        stop_heartbeat()
        logger.info("✅ Cleanup completed")


if __name__ == "__main__":
    # --- Early Initialization for Immediate Logging ---
    logger.debug("🔍 .env loaded and initial logger created.")
    logger.debug(f"🔍 Session timestamp set to {set_session_timestamp(None)}")

    # Extract session ID from log file path
    log_file = get_session_log_path()
    session_id = os.path.basename(log_file).replace('app_', '').replace('.log', '')

    # Log session start
    logger.info("=" * 80)
    logger.info(f"🆔 SESSION START: {session_id}")
    logger.info(f"📄 Log file: {log_file}")
    logger.info("=" * 80)

    try:
        logger.info("🔄 Starting asyncio.run()")
        asyncio.run(main())
        logger.info("✅ asyncio.run() completed normally")
    except KeyboardInterrupt:
        logger.info("=" * 80)
        logger.info("⏸️ Pipeline interrupted by user")
        logger.info("=" * 80)
    except SystemExit as e:
        logger.info("=" * 80)
        logger.error(f"❌ SystemExit raised with code: {e.code}")
        logger.info("=" * 80)
        raise
    except Exception as e:
        logger.info("=" * 80)
        logger.error(f"❌ Unhandled exception in main: {e}", exc_info=True)
        logger.info("=" * 80)
        raise
    finally:
        logger.info("=" * 80)
        logger.info("🔄 Main block exiting")
        logger.info("=" * 80)
