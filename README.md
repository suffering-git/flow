# YouTube Data Processor for Market Research

A Python-based pipeline for downloading, processing, and analyzing YouTube video transcripts and comments using AI. Designed for market research in regenerative agriculture and market gardening.

## Features

- **Data Collection**: Downloads transcripts and comments from YouTube channels
- **Multi-language Support**: Automatic translation to English
- **3-Stage AI Pipeline**:
  - Stage 1: Data compression (cost-effective)
  - Stage 2: Topic extraction and atomic insights
  - Stage 3: Vector embeddings for semantic search
- **Hybrid Search**: Full-text (FTS5) and semantic vector search
- **Resumable Operations**: Pipeline can be paused and resumed
- **Rate Limiting**: Built-in monitoring and cost tracking

## Setup

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. **Configure channels** in `config.py`:
   ```python
   CHANNEL_IDS = [
       "UC295-Dw_tDNtZXFeAPAW6Aw",  # Your channel IDs
   ]
   ```

## Usage

### Run Full Pipeline

```bash
python main.py
```

### Reset Processing Data

```bash
python reset_processing.py
```

### Query Data

```python
from query.query_utils import QueryUtils

query = QueryUtils()

# Text search
results = query.search_text("lettuce washing")

# Semantic search
results = await query.search_semantic("sustainable farming practices")

# Browse insights
insights = query.browse_insights(limit=50)

# Get insight details
details = query.get_insight_details(insight_id=123)
```

## Configuration

All settings are in `config.py`:

- `CHANNEL_IDS`: YouTube channels to process
- `STOP_AFTER_STAGE`: Halt pipeline at specific stage
- `STAGE1_MODEL`, `STAGE2_MODEL`, `EMBEDDING_MODEL`: AI models to use
- `MAX_TRANSCRIPT_CONCURRENCY`: Concurrent transcript downloads
- `RATE_LIMIT_WARNING_THRESHOLDS`: API usage warning levels

## Project Structure

```
flow/
├── config.py              # Configuration
├── main.py               # Main pipeline
├── reset_processing.py   # Reset utility
├── database/            # Database layer
├── models/              # Pydantic validation models
├── fetchers/            # Data downloaders
├── processors/          # AI processing stages
├── utils/               # Logging, rate limiting, etc.
├── prompts/            # AI prompt templates
└── query/              # Search and retrieval
```

## Documentation

- `SCOPE.md`: Complete technical specification
- `GEMINI_RATES.md`: API rate limits and pricing
- `TRANSCRIPTS.md`: youtube-transcript-api documentation

## License

Personal project - not for distribution
