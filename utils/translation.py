"""
Language detection and translation utilities.

Provides helpers for:
- Language detection using langdetect
- Translation using argostranslate (offline, fast, free)
- Error handling for translation failures
"""

import json
from typing import Optional, Tuple
from langdetect import detect, LangDetectException
import argostranslate.translate
import argostranslate.package
import threading

from utils.logger import get_logger

logger = get_logger(__name__)

# Global lock for package installation to prevent concurrent downloads
_package_install_lock = threading.Lock()


class TranslationHelper:
    """
    Helper class for language detection and translation.

    Uses Argos Translate for fast, offline, free translation.
    """

    def __init__(self):
        """Initialize translation helper."""
        # Load installed languages once at initialization
        # Reason: Caching improves performance for repeated translations
        self.installed_languages = argostranslate.translate.get_installed_languages()

        # Build translation lookup cache: {from_code: translator}
        self.translators = {}
        for lang in self.installed_languages:
            if lang.code != 'en':
                # Get translation object from this language to English
                translation = lang.get_translation(
                    argostranslate.translate.get_language_from_code('en')
                )
                if translation:
                    self.translators[lang.code] = translation
        
        self.download_attempts_file = ".download_attempts.json"
        try:
            with open(self.download_attempts_file, "r") as f:
                self.attempted_downloads = set(json.load(f))
        except (FileNotFoundError, json.JSONDecodeError):
            self.attempted_downloads = set()

        logger.info(f"✅ Initialized translation helper with {len(self.translators)} language pairs")

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
            # Reason: Language detection fails on emojis/short text (~0.16% of comments)
            # This is expected behavior, so log at DEBUG level to avoid noise
            logger.debug(f"🟡 Language detection failed: {e}")
            return None

    def _download_language_pack(self, from_code: str) -> bool:
        """
        Download and install a language pack if available.

        Args:
            from_code: Source language code to download.

        Returns:
            True if successfully downloaded and installed, False otherwise.
        """
        if from_code in self.attempted_downloads:
            logger.debug(f"Skipping download for {from_code}, already attempted this session.")
            return False
        
        self.attempted_downloads.add(from_code)
        with open(self.download_attempts_file, "w") as f:
            json.dump(list(self.attempted_downloads), f)
        # Use lock to prevent multiple threads from downloading the same pack
        # Reason: Concurrent downloads could cause corruption or duplicate work
        with _package_install_lock:
            # Check if pack was installed by another thread while we waited
            if from_code in self.translators:
                return True

            try:
                logger.info(f"📦 Downloading language pack: {from_code} → en")

                # Update package index to get latest available packages
                argostranslate.package.update_package_index()
                available_packages = argostranslate.package.get_available_packages()

                # Find the package for this language to English
                target_package = None
                for pkg in available_packages:
                    if pkg.from_code == from_code and pkg.to_code == 'en':
                        target_package = pkg
                        break

                if not target_package:
                    logger.warning(f"🟡 No language pack available for {from_code} → en")
                    return False

                # Download and install the package
                download_path = target_package.download()
                argostranslate.package.install_from_path(download_path)

                # Reload installed languages and rebuild cache
                self.installed_languages = argostranslate.translate.get_installed_languages()

                # Add the new translator to cache
                from_lang = argostranslate.translate.get_language_from_code(from_code)
                to_lang = argostranslate.translate.get_language_from_code('en')

                if from_lang and to_lang:
                    translation = from_lang.get_translation(to_lang)
                    if translation:
                        self.translators[from_code] = translation
                        logger.info(f"✅ Successfully installed {from_code} → en language pack")
                        return True

                return False

            except Exception as e:
                import traceback
                traceback.print_exc()
                logger.warning(f"🟡 Failed to download language pack {from_code}: {e}")
                return False

    def translate_to_english(self, text: str, source_lang: str) -> Optional[str]:
        """
        Translate text to English using Argos Translate.

        Automatically downloads missing language packs if needed.

        Args:
            text: Input text.
            source_lang: Source language code.

        Returns:
            Translated text or None if translation fails.
        """
        try:
            # Check if we have a translator for this language
            translator = self.translators.get(source_lang)

            if not translator:
                # Try to download the language pack automatically
                logger.debug(f"🔍 No translator cached for {source_lang}, attempting auto-download...")
                if self._download_language_pack(source_lang):
                    # Successfully downloaded, get the translator
                    translator = self.translators.get(source_lang)
                else:
                    # Download failed, cannot translate
                    logger.debug(f"🟡 No translator available for language: {source_lang}")
                    return None

            # Translate using cached translator
            # Reason: Argos Translate is fast (50-200ms) and fully offline
            result = translator.translate(text)
            return result
        except Exception as e:
            logger.warning(f"🟡 Translation failed for {source_lang}: {e}")
            return None
