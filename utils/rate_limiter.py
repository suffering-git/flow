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
        # Calculate cost for this request
        cost = calculate_cost(self.model_code, input_tokens, output_tokens)

        # Update total counters
        self.request_count += 1
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        self.total_cost += cost

        # Update tracking for logging
        self.requests_since_log += 1
        self.tokens_since_log += input_tokens + output_tokens

        # Check if we've entered a new minute
        now = datetime.now()
        if now - self.minute_start > timedelta(minutes=1):
            # Reset per-minute counters
            self.current_minute_requests = 0
            self.current_minute_tokens = 0
            self.minute_start = now

        # Update current minute counters
        self.current_minute_requests += 1
        self.current_minute_tokens += input_tokens + output_tokens

        # Check rate limits and log warnings if needed
        self._check_rate_limits()

        # Log periodic summaries
        if self.requests_since_log >= config.LOG_USAGE_EVERY_N_REQUESTS:
            self._log_usage_summary()
            self.requests_since_log = 0
            self.tokens_since_log = 0
        elif self.tokens_since_log >= config.LOG_USAGE_EVERY_X_TOKENS:
            self._log_usage_summary()
            self.requests_since_log = 0
            self.tokens_since_log = 0

    def _check_rate_limits(self) -> None:
        """
        Check current usage against rate limits.

        Logs warnings when approaching thresholds.
        """
        # Calculate percentage of limits used
        # Reason: TypedDict is a regular dict at runtime, use bracket access
        rpm_percent = (self.current_minute_requests / self.limits["rpm"]) * 100
        tpm_percent = (self.current_minute_tokens / self.limits["tpm"]) * 100

        # Check against warning thresholds
        for threshold in config.RATE_LIMIT_WARNING_THRESHOLDS:
            # Check RPM threshold
            if rpm_percent >= threshold and rpm_percent < threshold + 10:
                logger.warning(
                    f"⚠️  RPM at {rpm_percent:.1f}% "
                    f"({self.current_minute_requests}/{self.limits['rpm']})"
                )

            # Check TPM threshold
            if tpm_percent >= threshold and tpm_percent < threshold + 10:
                logger.warning(
                    f"⚠️  TPM at {tpm_percent:.1f}% "
                    f"({self.current_minute_tokens:,}/{self.limits['tpm']:,})"
                )

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
