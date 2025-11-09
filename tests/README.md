# Tests

This directory contains test files for the YouTube Data Processing Pipeline.

## Test Files

- **test_translation.py** - Tests basic translation functionality with multiple languages
- **test_autodownload.py** - Tests auto-download of missing language packs (Norwegian, Welsh)
- **test_autodownload2.py** - Tests auto-download with Afrikaans text
- **test_autodownload3.py** - Tests auto-download with Croatian text

## Running Tests

From the project root:

```bash
# Run a specific test
python tests/test_translation.py

# Or from within the tests directory
cd tests
python test_translation.py
```

## Note

These are integration tests that interact with the actual Argos Translate library and may download language packs if they're not already installed.
