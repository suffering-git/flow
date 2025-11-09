"""
Heartbeat monitor to detect when execution stops.

Logs periodic heartbeat messages to help diagnose sudden process termination.
"""

import asyncio
import threading
from typing import Optional

from utils.logger import get_logger

logger = get_logger(__name__)


class HeartbeatMonitor:
    """
    Background thread that logs periodic heartbeat messages.

    Helps diagnose where/when the process dies unexpectedly.
    """

    def __init__(self, interval: int = 10):
        """
        Initialize heartbeat monitor.

        Args:
            interval: Seconds between heartbeat logs.
        """
        self.interval = interval
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self._counter = 0

    def start(self) -> None:
        """Start the heartbeat monitor."""
        if self.running:
            return

        self.running = True
        self.thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        self.thread.start()
        logger.info(f"💓 Heartbeat monitor started (interval: {self.interval}s)")

    def stop(self) -> None:
        """Stop the heartbeat monitor."""
        if not self.running:
            return

        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
        logger.info("💓 Heartbeat monitor stopped")

    def _heartbeat_loop(self) -> None:
        """Background thread that logs heartbeats."""
        import time
        import threading

        while self.running:
            self._counter += 1
            # Log thread count and basic stats
            thread_count = threading.active_count()
            logger.debug(
                f"💓 Heartbeat #{self._counter} | "
                f"Threads: {thread_count}"
            )
            time.sleep(self.interval)


# Global heartbeat instance
_heartbeat: Optional[HeartbeatMonitor] = None


def start_heartbeat(interval: int = 10) -> None:
    """
    Start global heartbeat monitor.

    Args:
        interval: Seconds between heartbeat logs.
    """
    global _heartbeat
    if _heartbeat is None:
        _heartbeat = HeartbeatMonitor(interval)
    _heartbeat.start()


def stop_heartbeat() -> None:
    """Stop global heartbeat monitor."""
    global _heartbeat
    if _heartbeat:
        _heartbeat.stop()
