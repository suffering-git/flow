"""
Database reset script for re-processing with different prompts or models.

This script safely resets AI processing results while preserving raw data.
"""

import config
from database.db_manager import DatabaseManager
from utils.logger import get_logger

logger = get_logger(__name__)


def reset_database() -> None:
    """
    Reset AI processing results with safety prompts.

    Resets:
    - TopicSummaries table (Stage 2 results)
    - AtomicInsights table (Stage 2 results and Stage 3 embeddings)
    - stage_2_status and embedding_status in Status table
    - Optionally: CompressedData table (Stage 1 results) if config.RESET_COMPRESSED_DATA=True

    Preserves:
    - All raw transcript and comment data
    - Channels, Videos, and Status tables
    - Download status flags (transcript_status, comments_status)
    """
    logger.info("🔄 Database Reset Utility")
    logger.info("=" * 60)

    # Show what will be reset
    logger.info("📋 The following will be DELETED:")
    logger.info("  • All records from TopicSummaries table")
    logger.info("  • All records from AtomicInsights table")
    logger.info("  • Processing status for stage_2_status and embedding_status")

    if config.RESET_COMPRESSED_DATA:
        logger.info("  • All records from CompressedData table (RESET_COMPRESSED_DATA=True)")
        logger.info("  • Processing status for stage_1_status")

    logger.info("\n📋 The following will be PRESERVED:")
    logger.info("  • All raw transcripts (RawTranscripts table)")
    logger.info("  • All raw comments (RawComments table)")
    logger.info("  • Channel and video metadata (Channels, Videos tables)")
    logger.info("  • Download statuses (transcript_status, comments_status)")

    if not config.RESET_COMPRESSED_DATA:
        logger.info("  • Compressed data (CompressedData table)")

    # Confirmation prompt
    logger.warning("\n⚠️  This operation cannot be undone!")
    response = input("\nType 'RESET' to confirm: ")

    if response != "RESET":
        logger.info("❌ Reset cancelled")
        return

    # Execute reset
    logger.info("\n🔄 Executing database reset...")

    db_manager = DatabaseManager(config.DATABASE_PATH)
    db_manager.reset_processing_data(reset_compressed=config.RESET_COMPRESSED_DATA)

    logger.info("✅ Database reset completed successfully")


if __name__ == "__main__":
    reset_database()
