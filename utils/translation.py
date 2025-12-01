"""
Language detection and translation utilities.

Provides helpers for:
- Language detection using Lingua (memory-efficient)
- Translation using argostranslate (offline, fast, free)
- Error handling for translation failures
"""
import os
from typing import Optional, Tuple

import argostranslate.package
import argostranslate.translate
from lingua import Language, LanguageDetectorBuilder
from google.cloud import translate_v2 as translate

from utils.logger import get_logger

logger = get_logger(__name__)


class TranslationHelper:
    """
    Helper class for language detection and translation.

    Uses Lingua for detection and Argos Translate for offline translation.
    """

    def __init__(self):
        """Initialize translation helper."""
        # Reason: Initialize Lingua in low accuracy mode to save memory.
        # Preload only the languages we have Argos packs for.
        self.detector = (
            LanguageDetectorBuilder.from_languages(
                Language.ENGLISH,
                Language.SPANISH,
                Language.PORTUGUESE,
                Language.FRENCH,
                Language.GERMAN,
                Language.RUSSIAN,
                Language.JAPANESE,
                Language.KOREAN,
            )
            .with_low_accuracy_mode()
            .build()
        )

        # Initialize Google Translate client
        self.google_translate_client = None
        try:
            # The client will automatically find credentials from the environment
            # (GOOGLE_APPLICATION_CREDENTIALS)
            self.google_translate_client = translate.Client()
            logger.info("✅ Google Translate client initialized.")
        except Exception as e:
            logger.warning(f"🟡 Google Translate client failed to initialize: {e}")
            logger.warning("🟡 Google Translate fallback will be disabled.")


        # Load installed languages once at initialization
        self.installed_languages = argostranslate.translate.get_installed_languages()

        # Build translation lookup cache: {from_code: translator}
        self.translators = {}
        for lang in self.installed_languages:
            if lang.code != 'en':
                translation = lang.get_translation(
                    argostranslate.translate.get_language_from_code('en')
                )
                if translation:
                    self.translators[lang.code] = translation

        logger.info(f"✅ Initialized translation helper with {len(self.translators)} language pairs")

    def detect_and_translate(self, text: str) -> Tuple[str, str, bool]:
        """
        Detect language and translate to English if needed.

        Args:
            text: Input text to process.

        Returns:
            Tuple of (translated_text, original_language, is_translated)
        """
        detected_lang = self.detect_language(text)

        if detected_lang is None:
            logger.debug("🟡 Could not detect language, keeping original text")
            return (text, "unknown", False)

        if detected_lang == "en":
            return (text, "en", False)

        translated = self.translate_to_english(text, detected_lang)

        if translated is None:
            logger.debug(
                f"🟡 Translation from {detected_lang} failed or not supported, "
                f"keeping original text"
            )
            return (text, detected_lang, False)

        logger.debug(f"🌐 Translated from {detected_lang} to English")
        return (translated, detected_lang, True)

    def detect_language(self, text: str) -> Optional[str]:
        """
        Detect language of text using Lingua.

        Args:
            text: Input text.

        Returns:
            Language code (e.g., 'en', 'es') or None if detection fails.
        """
        try:
            language = self.detector.detect_language_of(text)
            if language:
                return language.iso_code_639_1.name.lower()
            return None
        except Exception as e:
            logger.debug(f"🟡 Language detection failed: {e}")
            return None

    def translate_to_english(self, text: str, source_lang: str) -> Optional[str]:
        """
        Translate text to English using pre-installed Argos Translate models
        with a fallback to Google Translate API.

        Args:
            text: Input text.
            source_lang: Source language code.

        Returns:
            Translated text or None if translation fails or is not supported.
        """
        try:
            translator = self.translators.get(source_lang)

            if translator:
                return translator.translate(text)

            # Fallback to Google Translate if available
            if self.google_translate_client:
                logger.debug(f"🟡 No local translator for {source_lang}, using Google Translate API.")
                try:
                    result = self.google_translate_client.translate(
                        text, target_language='en', source_language=source_lang
                    )
                    return result['translatedText']
                except Exception as e:
                    logger.error(f"🔴 Google Translate API failed for {source_lang}: {e}")
                    return None

            logger.debug(f"🟡 No local translator and Google Translate is disabled for {source_lang}.")
            return None

        except Exception as e:
            logger.warning(f"🟡 Translation failed for {source_lang}: {e}")
            return None
