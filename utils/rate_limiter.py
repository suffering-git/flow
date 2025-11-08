"""
Rate limiting and cost tracking for Gemini API.

Tracks:
- Requests per minute (RPM)
- Tokens per minute (TPM)
- Total cost in USD
- Warning when approaching limits
"""

import asyncio
from datetime import datetime, timedelta
from typing import Optional

import config
from models.gemini_rate_limits import get_rate_limits, calculate_cost
from utils.logger import get_logger

logger = get_logger(__name__)


class RateLimiter:
    """
    Tracks and limits Gemini API usage.

    Monitors RPM, TPM, and cost. Issues warnings when approaching limits.
    """

    def __init__(self, model_code: str, max_concurrent: int):
        """
        Initialize rate limiter.

        Args:
            model_code: Gemini model code (e.g., 'gemini-2.5-flash-lite').
            max_concurrent: Maximum concurrent requests allowed.
        """
        self.model_code = model_code
        self.max_concurrent = max_concurrent
        self.limits = get_rate_limits(model_code)

        # Tracking data
        self.request_count = 0
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_cost = 0.0

        # Per-minute tracking
        self.current_minute_requests = 0
        self.current_minute_tokens = 0
        self.minute_start = datetime.now()

        # Logging intervals
        self.requests_since_log = 0
        self.tokens_since_log = 0

    async def track_request(
        self,
        input_tokens: int,
        output_tokens: int
    ) -> None:
        """
        Track a completed API request.

        Updates counters and logs warnings if approaching limits.

        Args:
            input_tokens: Number of input tokens used.
            output_tokens: Number of output tokens generated.
        """
        # TODO: Implement tracking logic
        # 1. Update counters
        # 2. Calculate cost
        # 3. Check if current minute has passed, reset if needed
        # 4. Check against rate limits and log warnings
        # 5. Log periodic summaries based on config intervals

        pass

    def _check_rate_limits(self) -> None:
        """
        Check current usage against rate limits.

        Logs warnings when approaching thresholds.
        """
        # TODO: Implement limit checking
        # Calculate percentage of RPM and TPM used
        # Compare against config.RATE_LIMIT_WARNING_THRESHOLDS
        # Log warnings at 50%, 75%, 90% thresholds

        pass

    def _log_usage_summary(self) -> None:
        """
        Log current API usage summary.
        """
        logger.info(
            f"📊 API Usage: {self.request_count} requests, "
            f"{self.total_input_tokens:,} input tokens, "
            f"{self.total_output_tokens:,} output tokens, "
            f"${self.total_cost:.4f} total cost"
        )

    def get_current_rpm(self) -> int:
        """
        Get current requests per minute.

        Returns:
            Requests in current minute.
        """
        if datetime.now() - self.minute_start > timedelta(minutes=1):
            return 0
        return self.current_minute_requests

    def get_current_tpm(self) -> int:
        """
        Get current tokens per minute.

        Returns:
            Tokens in current minute.
        """
        if datetime.now() - self.minute_start > timedelta(minutes=1):
            return 0
        return self.current_minute_tokens
