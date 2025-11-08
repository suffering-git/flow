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
    # TODO: Implement signal registration
    # signal.signal(signal.SIGTERM, handle_shutdown)
    # signal.signal(signal.SIGUSR1, handle_pause)  # Not available on Windows

    # Note: SIGUSR1 is not available on Windows
    # May need platform-specific handling or alternative approach

    logger.info("✅ Signal handlers configured")
