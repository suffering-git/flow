"""
Central configuration management for the YouTube Data Processor.

All user-configurable settings are managed here.
"""

from typing import Literal

# =============================================================================
# Database Configuration
# =============================================================================

DATABASE_PATH: str = "data/youtube_data.db"

# =============================================================================
# API Credentials (loaded from .env file)
# =============================================================================

# These will be loaded from environment variables via python-dotenv
# YOUTUBE_API_KEY: str
# GEMINI_API_KEY: str
# WEBSHARE_PROXY_USERNAME: str
# WEBSHARE_PROXY_PASSWORD: str

# =============================================================================
# Channel Configuration
# =============================================================================

# List of YouTube channel IDs to process
CHANNEL_IDS: list[str] = [
    # "UC295-Dw_tDNtZXFeAPAW6Aw",  # Example channel ID
    "UCufnDvlHF9NHzEL4c3ECZUA"
]

# =============================================================================
# Processing Configuration
# =============================================================================

# Stop after specific stage: 'downloads', 'stage_1', 'stage_2', 'stage_3', or None for full pipeline
STOP_AFTER_STAGE: Literal["downloads", "stage_1", "stage_2", "stage_3"] | None = "downloads"

# =============================================================================
# Fetcher Configuration
# =============================================================================

# Maximum concurrent transcript downloads (Webshare allows up to 500)
MAX_TRANSCRIPT_CONCURRENCY: int = 100

# Timeout for transcript download operations (seconds)
TRANSCRIPT_FETCH_TIMEOUT: int = 120

# Maximum concurrent comment API requests (respect 10 RPS limit)
MAX_COMMENT_CONCURRENCY: int = 10

# Timeout for individual comment API requests (seconds)
COMMENT_REQUEST_TIMEOUT: int = 30

# Overall timeout for fetching all comments from a single video (seconds)
# This accounts for pagination - videos with many comments may take longer
COMMENT_FETCH_TIMEOUT: int = 300

# =============================================================================
# AI Model Configuration
# =============================================================================

# Model codes for each processing stage
STAGE1_MODEL: str = "gemini-2.5-flash-lite"  # Cost-effective compression
STAGE2_MODEL: str = "gemini-2.5-pro"  # Powerful analysis
EMBEDDING_MODEL: str = "gemini-embedding-001"  # Embeddings

# Embedding dimension size (128-3072, recommended: 768)
EMBEDDING_DIMENSION: int = 768

# =============================================================================
# Rate Limiting Configuration
# =============================================================================

# Maximum concurrent Gemini API requests for each stage
STAGE1_MAX_CONCURRENT: int = 100
STAGE2_MAX_CONCURRENT: int = 50
STAGE3_MAX_CONCURRENT: int = 100

# Rate limit monitoring thresholds (percentage of official limits)
RATE_LIMIT_WARNING_THRESHOLDS: list[int] = [50, 75, 90]

# Log API usage summary every N requests
LOG_USAGE_EVERY_N_REQUESTS: int = 100

# Log API usage summary every X tokens
LOG_USAGE_EVERY_X_TOKENS: int = 1_000_000

# =============================================================================
# Gemini Client Configuration
# =============================================================================

# Maximum number of retries for failed API requests
GEMINI_MAX_RETRIES: int = 5

# Initial backoff delay in seconds for API retries
GEMINI_INITIAL_BACKOFF: float = 2.0


# =============================================================================
# Database Reset Configuration
# =============================================================================

# Whether to also reset Stage 1 compressed data during reset
# (Default False since compression is typically unaffected by prompt changes)
RESET_COMPRESSED_DATA: bool = False

# =============================================================================
# Logging Configuration
# =============================================================================

# Log level: DEBUG, INFO, WARNING, ERROR
LOG_LEVEL: str = "INFO"

# Enable file logging in addition to console
FILE_LOGGING_ENABLED: bool = True
LOG_FILE_PATH: str = "data/app.log"
