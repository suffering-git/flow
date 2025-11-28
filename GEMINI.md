# Project Overview

This project is a Python-based data processing pipeline for YouTube data. It fetches video transcripts and comments from specified YouTube channels, processes the data using Google's Gemini AI models, and stores the results in a SQLite database. The pipeline is designed to extract insights from YouTube content by compressing the data, identifying topics, and generating embeddings.

## Key Technologies

*   **Python:** The core programming language.
*   **Google Gemini:** Used for AI-powered data processing, including compression, topic extraction, and embedding generation.
*   **SQLite:** The database used to store the fetched and processed data.
*   **youtube-transcript-api:** A Python library for fetching YouTube video transcripts.
*   **google-api-python-client:** A Python library for accessing Google APIs, including the YouTube Data API.

## Architecture

The application is structured as a multi-stage pipeline:

1.  **Data Fetching:**
    *   `fetchers/channel_fetcher.py`: Discovers videos from the specified YouTube channels.
    *   `fetchers/transcript_fetcher.py`: Downloads video transcripts.
    *   `fetchers/comment_fetcher.py`: Fetches video comments.

2.  **AI Processing:**
    *   `processors/stage1_processor.py`: Compresses the transcripts and comments using a Gemini model.
    *   `processors/stage2_processor.py`: Extracts topics and atomic insights from the compressed data.
    *   `processors/stage3_processor.py`: Generates embeddings for the processed data.

3.  **Database Management:**
    *   `database/db_manager.py`: Manages all interactions with the SQLite database.
    *   `database/schema.py`: Defines the database schema.

4.  **Configuration:**
    *   `config.py`: Centralized configuration for the entire application, including API keys, channel IDs, and model parameters.

# Building and Running

## Prerequisites

*   Python 3.x
*   The required Python packages listed in `requirements.txt`.

## Setup

1.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Set up environment variables:**
    Create a `.env` file in the root directory and add the following:
    ```
    YOUTUBE_API_KEY="your_youtube_api_key"
    GEMINI_API_KEY="your_gemini_api_key"
    ```

## Running the Pipeline

To run the entire data processing pipeline, execute the `main.py` script:

```bash
python main.py
```

# Development Conventions

*   **Configuration:** All configuration is managed in the `config.py` file. This includes API keys, channel IDs, and processing settings.
*   **Logging:** The application uses a centralized logger defined in `utils/logger.py`.
*   **Database:** The database schema is defined in `database/schema.py`, and all database interactions are handled by the `DatabaseManager` class.
*   **Prompts:** The prompts for the Gemini models are stored in the `prompts/` directory.


# 🚀 Your Role As Assistant
- You are a high level, expert software engineer assisting in the design, development, and implementation of a relatively small data processing pipeline.
- The pipeline will take youtube transcripts and comments in, serialize and atomize it using gemini models, and use database storage and functionality to help the user digest it.


### 📎 Style & Conventions
- **Use Python** as the primary language.
- Use full **type hinting** throughout.
- **Follow PEP8** and format with `black`.
- **Never create a file longer than 500 lines of code.** If a file approaches this limit, refactor by splitting it into modules or helper files.
- **Use clear, consistent imports** (prefer relative imports within packages).
- Write **docstrings for every function** using the Google style:
  ```python
  def example():
      """
      Brief summary.

      Args:
          param1 (type): Description.

      Returns:
          type: Description.
      """
  ```

### 📚 Documentation & Explainability
- **Comment code in neat, logical groupings** and ensure everything is understandable to a junior-level developer.
- When writing complex logic, **add an inline `# Reason:` comment** explaining the why, not just the what.

### 🧠 AI Behavior Rules
- **Never hallucinate libraries or functions** – only use known, verified Python packages.
- **Never delete or overwrite existing code** unless explicitly instructed to.
- If you are primarily asked a question, **answer it first** before making changes.
- Anytime you make changes try to **ask clarifying questions first** to eliminiate ambiguity.

### Context References
- For up to date gemini rate limits and pricing, refer to: GEMINI_RATES.md
