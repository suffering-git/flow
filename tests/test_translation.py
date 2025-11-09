"""
Quick test of the new Argos Translate translation system.
"""

from utils.translation import TranslationHelper

print("Initializing translation helper...")
helper = TranslationHelper()

# Test cases in different languages
test_cases = [
    ("Hello, this is in English", "en"),
    ("Bonjour, comment allez-vous?", "fr"),  # French
    ("Hola, ¿cómo estás?", "es"),  # Spanish
    ("Guten Tag, wie geht es Ihnen?", "de"),  # German
    ("こんにちは", "ja"),  # Japanese
]

print("\nTesting translations:\n")
for text, expected_lang in test_cases:
    print(f"Original: {text}")
    translated, detected_lang, was_translated = helper.detect_and_translate(text)
    print(f"  Detected: {detected_lang}")
    print(f"  Translated: {was_translated}")
    print(f"  Result: {translated}")
    print()

print("Translation test complete!")
