"""
Timestamp syntax parser for Stage 2 output.

Parses inline timestamp syntax: {text [timestamp|timestamp]}
Converts to clean text and structured timestamp mappings.
"""

import re
from typing import Any
from utils.logger import get_logger

logger = get_logger(__name__)


class TimestampParser:
    """
    Parses and processes inline timestamp syntax.

    Syntax: {text chunk [00:04:34|00:06:23]}
    """

    # Regex pattern to match {text [timestamp|timestamp]}
    PATTERN = re.compile(r'\{([^{}\[\]]+)\s*\[([^\[\]]+)\]\}')

    def parse_text_with_timestamps(self, text_with_syntax: str) -> dict[str, Any]:
        """
        Parse text with inline timestamp syntax.

        Args:
            text_with_syntax: Text containing {text [timestamp]} syntax.

        Returns:
            Dictionary with:
            - full_text: Clean text without syntax
            - timestamped_segments: List of {"text": str, "timestamps": [str]}
        """
        # Extract both clean text and segments
        clean_text = self.extract_clean_text(text_with_syntax)
        segments = self.extract_timestamp_segments(text_with_syntax)

        return {
            "full_text": clean_text,
            "timestamped_segments": segments
        }

    def extract_clean_text(self, text_with_syntax: str) -> str:
        """
        Extract clean text without timestamp syntax.

        Args:
            text_with_syntax: Text containing {text [timestamp]} syntax.

        Returns:
            Clean text string.
        """
        # Replace {text [timestamps]} with just the text portion
        # This keeps the text but removes the curly braces and timestamps
        clean_text = self.PATTERN.sub(r'\1', text_with_syntax)
        return clean_text.strip()

    def extract_timestamp_segments(
        self,
        text_with_syntax: str
    ) -> list[dict[str, Any]]:
        """
        Extract timestamp segments from text.

        Args:
            text_with_syntax: Text containing {text [timestamp]} syntax.

        Returns:
            List of segments: [{"text": str, "timestamps": [str]}]
        """
        segments = []

        # Find all matches of {text [timestamps]}
        for match in self.PATTERN.finditer(text_with_syntax):
            text_portion = match.group(1).strip()
            timestamp_str = match.group(2).strip()

            # Parse pipe-separated timestamps
            timestamps = self._parse_timestamps(timestamp_str)

            segments.append({
                "text": text_portion,
                "timestamps": timestamps
            })

        return segments

    def _parse_timestamps(self, timestamp_str: str) -> list[str]:
        """
        Parse pipe-separated timestamps.

        Args:
            timestamp_str: String like "00:04:34|00:06:23"

        Returns:
            List of timestamp strings.
        """
        return [ts.strip() for ts in timestamp_str.split('|')]
