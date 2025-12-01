"""
Language detection and translation utilities.

Provides helpers for:
- Language detection using Lingua (memory-efficient)
- Translation using argostranslate (offline, fast, free)
- Error handling for translation failures
"""
import os
import json
from typing import Optional, Tuple

import argostranslate.package
import argostranslate.translate
from lingua import Language, LanguageDetectorBuilder
from google.cloud import translate_v2 as translate
from google.oauth2 import service_account

from utils.logger import get_logger

logger = get_logger(__name__)


class TranslationHelper:
    """
    Helper class for language detection and translation.

    Uses Lingua for detection and Argos Translate for offline translation.
    """

    def __init__(self):
        """
        Initialize translation helper.
        """
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

        # Initialize Google Translate client with provided service account credentials
        self.google_translate_client = None
        self.argos_translated_count = 0
        self.argos_failed_count = 0
        self.google_translated_count = 0
        self.google_failed_count = 0
        self.google_char_count_per_language = {} # {lang_code: char_count}
        credentials_json = os.getenv('GOOGLE_CLOUD_CREDENTIALS')
        if credentials_json:
            try:
                credentials_dict = json.loads(credentials_json)
                credentials = service_account.Credentials.from_service_account_info(credentials_dict)
                self.google_translate_client = translate.Client(credentials=credentials)
                logger.info("✅ Google Translate client initialized with service account credentials.")
            except json.JSONDecodeError:
                logger.warning("🟡 GOOGLE_CLOUD_CREDENTIALS is not valid JSON. Google Translate fallback disabled.")
            except Exception as e:
                logger.warning(f"🟡 Google Translate client failed to initialize: {e}. Google Translate fallback disabled.")
        else:
            logger.warning("🟡 GOOGLE_CLOUD_CREDENTIALS not set. Google Translate fallback disabled.")

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
            self.argos_failed_count += 1
            return (text, "unknown", False)

        if detected_lang == "en":
            return (text, "en", False)

        translated = self.translate_to_english(text, detected_lang)

        if translated is None:
            logger.debug(
                f"🟡 Translation from {detected_lang} failed or not supported, "
                f"keeping original text"
            )
            # Failure already logged in translate_to_english, just increment generic fail
            return (text, detected_lang, False)

        logger.debug(f"🌐 Translated from {detected_lang} to English")
        if self.translators.get(detected_lang): # If translated by Argos
            self.argos_translated_count += 1
        else: # If translated by Google
            self.google_translated_count += 1
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
                self.argos_translated_count += 1
                return translator.translate(text)

            # Fallback to Google Translate if available
            if self.google_translate_client:
                logger.debug(f"🟡 No local translator for {source_lang}, using Google Translate API.")
                try:
                    result = self.google_translate_client.translate(
                        text, target_language='en', source_language=source_lang
                    )
                    self.google_translated_count += 1
                    self.google_char_count_per_language[source_lang] = \
                        self.google_char_count_per_language.get(source_lang, 0) + len(text)
                    return result['translatedText']
                except Exception as e:
                    logger.error(f"🔴 Google Translate API failed for {source_lang}: {e}")
                    self.google_failed_count += 1
                    return None

            logger.debug(f"🟡 No local translator and Google Translate is disabled for {source_lang}.")
            return None

        except Exception as e:
            logger.warning(f"🟡 Translation failed for {source_lang}: {e}")
            if self.translators.get(source_lang):
                self.argos_failed_count += 1
            return None

    def get_translation_stats(self) -> dict:
        """
        Get the current translation statistics.

        Returns:
            A dictionary containing translation statistics.
        """
        return {
            "argos_translated_count": self.argos_translated_count,
            "argos_failed_count": self.argos_failed_count,
            "google_translated_count": self.google_translated_count,
            "google_failed_count": self.google_failed_count,
            "google_char_count_per_language": self.google_char_count_per_language,
        }
