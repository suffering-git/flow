"""
Signal handling for graceful pause and shutdown.

Handles SIGTERM for shutdown and SIGUSR1 for pause.
Sets global flags checked by processing loops.
"""

import signal
import asyncio
from utils.logger import get_logger

logger = get_logger(__name__)

# Global flags
shutdown_requested = asyncio.Event()
pause_requested = asyncio.Event()


def handle_shutdown(signum: int, frame) -> None:
    """
    Handle shutdown signal (SIGTERM).

    Args:
        signum: Signal number.
        frame: Current stack frame.
    """
    logger.warning("🛑 Shutdown signal received, finishing current tasks...")
    shutdown_requested.set()


def handle_pause(signum: int, frame) -> None:
    """
    Handle pause signal (SIGUSR1).

    Args:
        signum: Signal number.
        frame: Current stack frame.
    """
    logger.warning("⏸️ Pause signal received, finishing current tasks...")
    pause_requested.set()


def setup_signal_handlers() -> None:
    """
    Setup signal handlers for graceful shutdown and pause.
    """
    import platform

    # Always register SIGTERM for shutdown
    signal.signal(signal.SIGTERM, handle_shutdown)

    # SIGINT (Ctrl+C) for shutdown as well
    signal.signal(signal.SIGINT, handle_shutdown)

    # Platform-specific pause signal
    # SIGUSR1 only available on Unix-like systems
    if platform.system() != 'Windows':
        try:
            signal.signal(signal.SIGUSR1, handle_pause)
            logger.info("✅ Signal handlers configured (SIGTERM, SIGINT, SIGUSR1)")
        except AttributeError:
            logger.info("✅ Signal handlers configured (SIGTERM, SIGINT)")
    else:
        logger.info("✅ Signal handlers configured (SIGTERM, SIGINT)")
        logger.debug("ℹ️  SIGUSR1 not available on Windows")
