"""
Logging system with emoji indicators and colored output.

Provides structured logging with:
- Log levels: DEBUG, INFO, WARNING, ERROR
- Emoji indicators for quick visual identification
- Colored output using colorama
- Optional file logging with session-specific files
"""

import logging
import sys
from datetime import datetime
from colorama import Fore, Style, init

import config

# Initialize colorama for cross-platform colored output
init(autoreset=True)

# Global session timestamp for log file naming
_session_timestamp = None


def set_session_timestamp(timestamp: str = None) -> str:
    """
    Set the session timestamp for log file naming.

    Args:
        timestamp: Optional timestamp string. If None, generates current timestamp.

    Returns:
        The timestamp that was set.
    """
    global _session_timestamp
    if timestamp is None:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    _session_timestamp = timestamp
    return timestamp


def get_session_log_path() -> str:
    """
    Get the session-specific log file path.

    Returns:
        Path to the log file for this session.
    """
    global _session_timestamp

    # CRITICAL: Ensure timestamp is set exactly once, as early as possible
    # Reason: Multiple modules call get_logger() at import time
    # We need them all to use the SAME timestamp
    if _session_timestamp is None:
        # Set timestamp to current time
        _session_timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")

    # Replace .log extension with _TIMESTAMP.log
    base_path = config.LOG_FILE_PATH
    if base_path.endswith('.log'):
        base_path = base_path[:-4]

    return f"{base_path}_{_session_timestamp}.log"


# Custom formatter with emoji indicators
class EmojiFormatter(logging.Formatter):
    """
    Custom formatter that adds emoji indicators to log messages.
    """

    # Emoji mappings for log levels
    EMOJIS = {
        logging.DEBUG: "🔍",
        logging.INFO: "ℹ️",
        logging.WARNING: "🟡",
        logging.ERROR: "❌",
    }

    # Color mappings for log levels
    COLORS = {
        logging.DEBUG: Fore.CYAN,
        logging.INFO: Fore.GREEN,
        logging.WARNING: Fore.YELLOW,
        logging.ERROR: Fore.RED,
    }

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record with emoji and color.

        Args:
            record: Log record to format.

        Returns:
            Formatted log string.
        """
        # Add emoji indicator
        emoji = self.EMOJIS.get(record.levelno, "")

        # Add color
        color = self.COLORS.get(record.levelno, "")

        # Format: [timestamp] [level] [module] emoji message
        log_fmt = f"{color}%(asctime)s [%(levelname)s] [%(name)s] {emoji} %(message)s{Style.RESET_ALL}"

        formatter = logging.Formatter(log_fmt, datefmt="%Y-%m-%d %H:%M:%S")
        return formatter.format(record)


def get_logger(name: str) -> logging.Logger:
    """
    Get or create a logger with proper formatting.

    Args:
        name: Logger name (typically __name__).

    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(name)

    # Only configure if not already configured
    if not logger.handlers:
        logger.setLevel(getattr(logging, config.LOG_LEVEL))

        # Console handler with UTF-8 encoding for emoji support
        # Reason: Windows console defaults to cp1252, which can't encode emojis
        import io
        console_handler = logging.StreamHandler(
            io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)
        )
        console_handler.setFormatter(EmojiFormatter())
        logger.addHandler(console_handler)

        # File handler (optional) with UTF-8 encoding for emoji support
        # Uses session-specific log files (e.g., app_2025-11-08_145405.log)
        if config.FILE_LOGGING_ENABLED:
            import os
            log_file_path = get_session_log_path()
            os.makedirs(os.path.dirname(log_file_path), exist_ok=True)

            file_handler = logging.FileHandler(log_file_path, encoding='utf-8')
            file_handler.setFormatter(
                logging.Formatter(
                    '%(asctime)s [%(levelname)s] [%(name)s] %(message)s',
                    datefmt="%Y-%m-%d %H:%M:%S"
                )
            )
            logger.addHandler(file_handler)

    return logger
