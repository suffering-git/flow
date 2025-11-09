"""
Test auto-download with Afrikaans (which we tried to install but might not have gotten).
"""

from utils.translation import TranslationHelper

print("Initializing translation helper...")
helper = TranslationHelper()

print(f"\nCurrently installed translators: {len(helper.translators)}")

# Test with Afrikaans text (af) - this was in your logs
# We tried to install it in the batch but let's verify
afrikaans_text = """
Hierdie is 'n wonderlike dag.
Ek is baie bly om hier te wees en met julle te praat.
Die weer is pragtig vandag.
"""

print("\n" + "="*60)
print("Testing with Afrikaans text:")
print("="*60)
print(f"Text: {afrikaans_text[:100]}...")

# Check if already installed
print(f"\nAfrikaans in cache before: {'af' in helper.translators}")

# Try translation (should auto-download if needed)
translated, detected_lang, was_translated = helper.detect_and_translate(afrikaans_text)

print(f"\nDetected language: {detected_lang}")
print(f"Was translated: {was_translated}")
print(f"Translation: {translated[:200] if translated else 'None'}...")

print(f"\nAfrikaans in cache after: {'af' in helper.translators}")
print(f"Final translator count: {len(helper.translators)}")
