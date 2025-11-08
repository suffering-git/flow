"""
Language detection and translation utilities.

Provides helpers for:
- Language detection using langdetect
- Translation using googletrans
- Error handling for translation failures
"""

from typing import Optional, Tuple
from langdetect import detect, LangDetectException
from googletrans import Translator

from utils.logger import get_logger

logger = get_logger(__name__)


class TranslationHelper:
    """
    Helper class for language detection and translation.
    """

    def __init__(self):
        """Initialize translation helper."""
        self.translator = Translator()

    def detect_and_translate(self, text: str) -> Tuple[str, str, bool]:
        """
        Detect language and translate to English if needed.

        Args:
            text: Input text to process.

        Returns:
            Tuple of (translated_text, original_language, is_translated)
            - If already English: (original_text, "en", False)
            - If translated: (translated_text, detected_lang, True)
            - If detection/translation fails: (original_text, "unknown", False)
        """
        # Detect language
        detected_lang = self.detect_language(text)

        # If detection failed, return original text
        if detected_lang is None:
            logger.debug("🟡 Could not detect language, keeping original text")
            return (text, "unknown", False)

        # If already English, no translation needed
        if detected_lang == "en":
            return (text, "en", False)

        # Translate to English
        translated = self.translate_to_english(text, detected_lang)

        # If translation failed, return original text
        if translated is None:
            logger.debug(
                f"🟡 Translation from {detected_lang} failed, "
                f"keeping original text"
            )
            return (text, detected_lang, False)

        # Successfully translated
        logger.debug(f"🌐 Translated from {detected_lang} to English")
        return (translated, detected_lang, True)

    def detect_language(self, text: str) -> Optional[str]:
        """
        Detect language of text.

        Args:
            text: Input text.

        Returns:
            Language code (e.g., 'en', 'es') or None if detection fails.
        """
        try:
            return detect(text)
        except LangDetectException as e:
            logger.warning(f"🟡 Language detection failed: {e}")
            return None

    def translate_to_english(self, text: str, source_lang: str) -> Optional[str]:
        """
        Translate text to English.

        Args:
            text: Input text.
            source_lang: Source language code.

        Returns:
            Translated text or None if translation fails.
        """
        try:
            result = self.translator.translate(text, src=source_lang, dest='en')
            return result.text
        except Exception as e:
            logger.warning(f"🟡 Translation failed: {e}")
            return None
