"""
Test auto-download functionality for missing language packs.
"""

from utils.translation import TranslationHelper

print("Initializing translation helper...")
helper = TranslationHelper()

print(f"\nCurrently installed translators: {len(helper.translators)}")
print(f"Languages: {', '.join(sorted(helper.translators.keys()))}\n")

# Test with a language we likely don't have installed yet
# Norwegian (no) and Welsh (cy) were in your logs but not in our initial 28
test_cases = [
    ("Hvordan har du det?", "no"),  # Norwegian - "How are you?"
    ("Sut mae?", "cy"),  # Welsh - "How are you?"
]

print("Testing auto-download functionality:\n")
for text, expected_lang in test_cases:
    print(f"Text: {text}")
    print(f"Expected language: {expected_lang}")

    # Check if already installed
    if expected_lang in helper.translators:
        print(f"  Already installed: YES")
    else:
        print(f"  Already installed: NO")
        print(f"  Will attempt auto-download...")

    # Try translation (should auto-download if needed)
    translated, detected_lang, was_translated = helper.detect_and_translate(text)

    print(f"  Detected language: {detected_lang}")
    print(f"  Was translated: {was_translated}")
    print(f"  Result: {translated}")
    print()

print(f"Final installed translators: {len(helper.translators)}")
print("Auto-download test complete!")
