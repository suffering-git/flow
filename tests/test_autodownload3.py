"""
Test auto-download with a language that exists but wasn't pre-installed.
Let's try Bosnian (bs) or Croatian (hr) or Serbian (sr).
"""

from utils.translation import TranslationHelper

print("Initializing translation helper...")
helper = TranslationHelper()

print(f"\nCurrently installed translators: {len(helper.translators)}")

# Test with Croatian text (hr) - this was in PRIORITY_LANGUAGES but might not have installed
croatian_text = """
Danas je divan dan.
Jako sam sretan što sam ovdje i razgovaram s vama.
Vrijeme je danas prekrasno.
"""

print("\n" + "="*60)
print("Testing auto-download with Croatian text:")
print("="*60)
print(f"Text: {croatian_text[:100]}...")

# Check if already installed
print(f"\nCroatian (hr) in cache before: {'hr' in helper.translators}")

# Try translation (should auto-download if needed)
translated, detected_lang, was_translated = helper.detect_and_translate(croatian_text)

print(f"\nDetected language: {detected_lang}")
print(f"Was translated: {was_translated}")
if translated:
    print(f"Translation: {translated[:200]}...")
else:
    print("Translation: None")

print(f"\nCroatian (hr) in cache after: {'hr' in helper.translators}")
print(f"Final translator count: {len(helper.translators)}")

if 'hr' in helper.translators:
    print("\n✅ Auto-download successful!")
else:
    print("\n❌ Auto-download failed or pack not available")
