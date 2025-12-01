"""
Helper script to install Argos Translate language packs.

Downloads language packs needed for translation to English.
"""

import argostranslate.package
import argostranslate.translate

print("Updating package index...")
argostranslate.package.update_package_index()

# Get all available packages
available_packages = argostranslate.package.get_available_packages()

# Common languages we need (based on YouTube comment analysis)
# These are the most common non-English languages on YouTube
PRIORITY_LANGUAGES = [
    'es',  # Spanish
    'pt',  # Portuguese
    'fr',  # French
    'de',  # German
    'ru',  # Russian
    'ja',  # Japanese
    'ko',  # Korean
]

print(f"\nInstalling language packs for {len(PRIORITY_LANGUAGES)} languages...")
installed_count = 0

for pkg in available_packages:
    # We want X -> English translations
    if pkg.to_code == 'en' and pkg.from_code in PRIORITY_LANGUAGES:
        print(f"  Installing {pkg.from_name} -> English...")
        try:
            argostranslate.package.install_from_path(pkg.download())
            installed_count += 1
            print(f"    OK: Installed {pkg.from_name} -> English")
        except Exception as e:
            print(f"    FAILED: {pkg.from_name}: {e}")

print(f"\nInstallation complete! Installed {installed_count} language packs.")

# Verify installation
installed_languages = argostranslate.translate.get_installed_languages()
print(f"\nTotal installed languages: {len(installed_languages)}")
print("Installed languages:", ", ".join([lang.code for lang in installed_languages]))
