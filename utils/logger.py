"""
Logging system with emoji indicators and colored output.

Provides structured logging with:
- Log levels: DEBUG, INFO, WARNING, ERROR
- Emoji indicators for quick visual identification
- Colored output using colorama
- Optional file logging
"""

import logging
import sys
from colorama import Fore, Style, init

import config

# Initialize colorama for cross-platform colored output
init(autoreset=True)


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
        if config.FILE_LOGGING_ENABLED:
            import os
            os.makedirs(os.path.dirname(config.LOG_FILE_PATH), exist_ok=True)

            file_handler = logging.FileHandler(config.LOG_FILE_PATH, encoding='utf-8')
            file_handler.setFormatter(
                logging.Formatter(
                    '%(asctime)s [%(levelname)s] [%(name)s] %(message)s',
                    datefmt="%Y-%m-%d %H:%M:%S"
                )
            )
            logger.addHandler(file_handler)

    return logger
