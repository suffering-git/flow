### **Project Scope and Technical Specification: YouTube Data Scraper & Processor **

- [\*\*Project Scope and Technical Specification: YouTube Data Scraper \& Processor \*\*](#project-scope-and-technical-specification-youtube-data-scraper--processor-)
  - [**Project Summary**](#project-summary)
  - [**Core Features / User Stories**](#core-features--user-stories)
  - [**Technical Stack**](#technical-stack)
  - [**Implementation Details / Logic**](#implementation-details--logic)
  - [**Data Model / Schema**](#data-model--schema)


#### **Project Summary**
A Python-based tool to download video transcripts and comments from YouTube channels for market research. The goal is to inform a market garden and orchard business plan focused on regenerative agriculture. The system performs a multi-stage AI processing pipeline on the raw data, structuring it into a normalized database of topic-based summaries and atomic insights. A hybrid search system combines full-text search with AI-powered semantic search via vector embeddings for comprehensive data discovery.

#### **Core Features / User Stories**
*   **Downloads Raw Data:** Downloads ALL video transcripts and ALL comments for specified channels, saving each directly in the database.
*   **Resumable Processing:** A status tracking system in the database, acting as the single source of truth for pipeline progression, ensures that if the script is stopped or crashes at any point, it can be resumed without re-doing completed work. All asynchronous processes will be designed to be pausable, resumable, and gracefully exitable; upon receiving a pause or exit signal, the system will wait for all currently running tasks to fully complete and write their results to the database, ensuring no in-flight requests are dropped.
*   **Structured AI Analysis:** A logical 3-stage AI pipeline extracts and summarizes the raw data into topic-based summaries, then further refines and atomizes this content into two distinct data types: `quantitative` (numerical insights) and `qualitative` (descriptive insights), and finally generates embeddings for semantic search. Each stage runs independently on the previous level of data and saves its output to the database.
*   **Vector Embedding Generation:** Automatically generates AI embeddings for all atomic insights to enable semantic search capabilities.
*   **Hybrid Search System:** Offers traditional full-text search (FTS5) for exact word matching and vector similarity search for semantic/conceptual queries across atomic insights.
*   **Database Reset Utility:** A safe reset function to clear all AI processing results while preserving raw data and video metadata, enabling complete re-processing with different prompts or models.
*   **Simplified Query Interface:** Provides a suite of user-friendly Python functions (in `query_utils.py`) for retrieving data from the database without needing to write raw SQL while still allowing the option to, including both text and semantic search capabilities.
*   **Comprehensive Logging:** Industry-standard logging with emoji indicators for clear visual feedback on successes, failures, and progress throughout all processing stages.

#### **Technical Stack**
*   **Programming Language:** Python
*   **Dependency Management:** A `requirements.txt` file will list all necessary packages and their versions for reproducible environments.
*   **Key Libraries:**
    *   `youtube_transcript_api`: For fetching video transcripts.
    *   `google-api-python-client`: The official Google client for interacting with the YouTube Data API v3 to fetch comments and video metadata.
    *   `asyncio`: For performing concurrent transcript downloads to improve speed when using proxies.
    *   `aiosqlite`: For saving data from asynchronous responses to the database.
    *   `python-dotenv`: To load credentials (API keys, proxy info) from a `.env` file into the script's environment.
    *   `google-generativeai`: The SDK for making calls to the Gemini API for all AI processing stages and embedding generation.
    *   `sqlite3`: The built-in Python library for interacting with the SQLite database file.
    *   `sqlite-vec`: SQLite extension for vector similarity search functionality.
    *   `pydantic`: For data validation at critical points where external data could be corrupted or malformed.
    *   `logging`: Python's built-in logging library for structured logging with emoji indicators.
    *   `colorama`: For cross-platform colored terminal output to enhance log readability.
*   **Services:** Webshare (for proxies), YouTube Data API v3, Gemini API (for processing and embeddings).
*   **Database:** SQLite, with the **FTS5 (Full-Text Search 5) extension** enabled for traditional text queries and **sqlite-vec extension** for vector similarity search.

#### **Implementation Details / Logic**
*   **Configuration:** A central `config.py` file will manage all user-configurable settings, including the `list of target YouTube channels`, all `API parameters` (e.g., model names for each AI stage, embedding model),`update intervals` (the number of days to wait before re-checking a channel for new videos), and more.
*   **Rate Limiting Controls:** Manual rate limiting is governed by four specific settings in `config.py`: a `youtube_api_delay` for the `time.sleep` call between comment requests, and three distinct 'max concurrent requests' values to independently control asynchronous job limits for each Gemini model (pro, flash, and embeddings).
*   **Credentials:** All sensitive credentials (YouTube API Key, Gemini API Key, Webshare proxy credentials) will be stored in a `.env` file and loaded into the script's environment using the `python-dotenv` library.
*   **Logging System:** A comprehensive logging framework will provide clear feedback throughout all operations:
    *   **Log Levels:** DEBUG, INFO, WARNING, ERROR with emoji indicators for quick visual identification.
    *   **Success Indicators:** ✅ for successful operations (downloads, processing completions, database writes, embedding generation).
    *   **Failure Indicators:** ❌ for errors and failures, 🟡 for warnings and retry attempts.
    *   **Progress Indicators:** 🔄 for ongoing operations, 📊 for statistics and summaries.
    *   **Information Indicators:** ℹ️ for general information, 🎯 for important milestones.
    *   **Log Output:** Console output with colored formatting, plus optional file logging for debugging.
    *   **Structured Format:** Timestamp, log level, module name, emoji indicator, and detailed message.
    *   📊 **Rate Limit & Cost Monitoring:** Tracks and periodically logs Gemini API usage summaries (every N requests or X tokens, both configurable) to monitor Requests Per Minute (RPM) and Tokens Per Minute (TPM). Issues `🟡` warning messages when usage exceeds configurable thresholds (e.g., 50%, 75%, 90%) of the official limits. Also reports costs. Logic uses stage-specific model codes from config.py to look up associated rate limits & costs from a dict created according to information from `GEMINI_RATES.md`. 
*   **Data Validation:** Pydantic models will be used to validate ai outputs:
    *   Models for Stage 1 topic summaries (including source attribution) and Stage 2 atomic insights to ensure required fields are present and properly formatted JSON is returned.
*   **Idempotency & State Management:** The entire pipeline will be resumable and will not repeat completed work. Each stage is fully decoupled, allowing for independent execution and inspection of intermediate results.
    *   **Primary Mechanism:** A `VideoProcessingStatus` table in the database will have one row for every video and will track its state through all stages: `transcript_status`, `comments_status`, `stage_1_status`, `stage_2_status`, `embedding_status`. Before any action is taken on a video, the script will first query this table to check its status.
    *   **Stage Dependencies:** The system enforces clear dependencies between stages:
        *   Stage 1 requires completed transcript/comment downloads
        *   Stage 2 requires completed Stage 1 (topic summaries must exist)
        *   Stage 3 (embeddings) requires completed Stage 2 (atomic insights must exist)
    *   **Single Source of Truth:** The database status table is the authoritative source for all processing state.
*   **Channel & Video Setup Logic:** The system handles both initial setup and reset scenarios:
    *   **Channel Discovery:** For each configured channel ID, the system first checks if a record exists in the `Channels` table. If not, it fetches the channel name from the YouTube API and creates the record with ✅ logging.
    *   **Video Discovery:** For each channel, the system fetches the latest video list from the YouTube API. For each video, it checks if a record exists in the `Videos` table. If not, it creates the video record and initializes a corresponding `VideoProcessingStatus` record with all statuses set to 'pending'.
    *   **Reset Compatibility:** After a database reset, existing `Channels` and `Videos` records are preserved, so the video discovery logic will find existing records and skip re-creating them, only creating `VideoProcessingStatus` records for truly new videos discovered since the last run.
*   **Data Fetching & Translation:**
    *   **Transcripts:** Fetched via asynchronous requests routed through rotating Webshare proxies to mitigate IP bans and improve speed. Raw transcript data is stored directly in the database as fetch jobs complete using `aiosqlite`.
    *   **Comments:** Fetched via sequential, synchronous requests to the YouTube Data API. A `time.sleep()` call of a configurable duration will be placed between each request to ensure rate limits are respected. Comment data is stored directly in the database.
*   **Data Integrity (Database Transactions):** To prevent database corruption from a crash during a write operation, the system will employ database transactions with rollback capability on failure.
*   **Error Handling:** The script will not crash on non-critical errors, with comprehensive logging at each step:
    *   **Permanent Errors:** If the YouTube API reports that transcripts are disabled or comments are disabled for a video, the `VideoProcessingStatus` table will be updated with a final state (e.g., 'unavailable', 'disabled'), and the specific error message will be logged with ❌ indicator. The video will be skipped in all future runs.
    *   **Transient Errors:** For network timeouts, proxy connection errors, or temporary API rate limits, the error will be logged with 🟡 indicator and full traceback, but the video's status in the database will remain unchanged, making it eligible to be retried automatically on the next script run.
    *   **Success Logging:** Each successful operation will be logged with ✅ indicator, including download completions, processing milestones, database updates, and embedding generation.
*   **AI Processing Pipeline (3-Stage, Fully Decoupled):**
    *   **Stage 1 (Extract & Summarize):** **Input:** Raw text from both transcript and all comments for a video retrieved from the database, processed together in a single request. **Process:** A cost-effective model (e.g., Gemini Flash) is prompted to extract all valuable data and organize it into paragraph summaries of each major topic discussed, clearly identifying whether each topic originated from the transcript or a comment. **Output:** Multiple topic-based paragraph blurbs stored in the `TopicSummaries` table with source attribution. **Status Update:** `stage_1_status` set to 'complete' with ✅ log entry.
    *   **Stage 2 (Refine & Atomize):** **Input:** All topic blurbs for a video (both transcript and comment-derived) from the `TopicSummaries` table. **Process:** A powerful model (e.g., Gemini Pro) processes the entire video's blurbs at once to: 1) filter out vague or low-value content, and 2) break down the remaining valuable content into atomic records classified as either `quantitative` or `qualitative`. Source attribution is preserved through foreign key relationships. **Output:** Atomic insights stored in the `AtomicInsights` table with foreign key references to their source topic summaries. **Status Update:** `stage_2_status` set to 'complete' with ✅ log entry.
    *   **Stage 3 (Generate Embeddings):** **Input:** All atomic insights for a video from the `AtomicInsights` table. **Process:** Each atomic insight text is sent to Gemini's embedding API to generate a vector representation. **Output:** Embedding vectors stored in the `embedding_vector` column of the `AtomicInsights` table and indexed via sqlite-vec. **Status Update:** `embedding_status` set to 'complete' with ✅ log entry.
*   **Database Reset Logic:** The system includes a safe reset mechanism for experimentation:
    *   **What Gets Reset:** All AI processing results are cleared from the database:
        *   All records from `TopicSummaries` table (Stage 1 results)
        *   All records from `AtomicInsights` table (Stage 2 results and embeddings)
        *   Processing status flags reset to 'pending' for `stage_1_status`, `stage_2_status`, and `embedding_status` in `VideoProcessingStatus` table
    *   **What Gets Preserved:** Raw data and metadata remain intact:
        *   All raw transcript and comment data stored in the `RawTranscripts` and `RawComments` tables
        *   All records in `Channels`, `Videos`, and `VideoProcessingStatus` tables
        *   Download status flags (`transcript_status`, `comments_status`) remain unchanged
    *   **Implementation:** A dedicated `reset_processing.py` script provides a safe, logged operation with confirmation prompts and progress indicators using ✅ and 🔄 emoji logging.
*   **Hybrid Search System:**
    *   **Full-Text Search (FTS5):** The system will use SQLite's FTS5 extension for exact keyword-based search on atomic insights only.
        *   A virtual table (`AtomicInsights_fts`) will index the `insight_text` column for searching atomic insights directly.
    *   **Vector Similarity Search:** The system will use sqlite-vec for semantic search capabilities.
        *   Atomic insight embeddings will be stored in the `embedding_vector` column and indexed for similarity search.
        *   Search queries will be converted to embeddings via Gemini API and matched against stored vectors using cosine similarity.
        *   Results can be filtered by similarity threshold and combined with traditional search results.
    *   **Query-Time Embedding Generation:** Each semantic search requires converting the user's search query to an embedding vector via a real-time API call to Gemini's embedding service.
    *   **Search Strategy:** Use FTS5 for exact word searches ("lettuce pricing") and vector search for broader conceptual searches ("sustainable farming practices").
    *   **Sample/Experimental Batch:** A function allows the user to fully pipe a hand-selected batch of specific videos rather than entire channels for experimentation.
  
#### **Data Model / Schema**
*   **Database Indexing:** To ensure fast queries, the foreign key columns (`video_id` in `TopicSummaries`, and `summary_id` in `AtomicInsights`) will be explicitly indexed. Vector similarity searches will be optimized via sqlite-vec indexing on the `embedding_vector` column in the `AtomicInsights` table.
*   **Database Schema:**

    *   **`Channels` Table**
        *   `channel_id` (TEXT, Primary Key) --- *The unique YouTube channel ID (e.g., UC295-Dw_tDNtZXFeAPAW6Aw).*
        *   `channel_name` (TEXT) --- *The human-readable name of the channel.*

    *   **`Videos` Table**
        *   `video_id` (TEXT, Primary Key) --- *The unique YouTube video ID (e.g., dQw4w9WgXcQ).*
        *   `channel_id` (TEXT, Foreign Key) --- *Links to the `Channels` table.*
        *   `video_title` (TEXT) --- *The title of the video.*
        *   `published_date` (DATETIME) --- *The original upload date of the video.*
        *   `duration_seconds` (INTEGER) --- *The length of the video in seconds.*
        *   `view_count` (INTEGER) --- *The view count at the time of metadata fetching.*
        *   `like_count` (INTEGER) --- *The like count at the time of metadata fetching.*

    *   **`VideoProcessingStatus` Table**
        *   `video_id` (TEXT, Primary Key, Foreign Key referencing `Videos`) --- *Links to the `Videos` table.*
        *   `transcript_status` (TEXT) --- *e.g., 'pending', 'downloaded', 'unavailable'.*
        *   `comments_status` (TEXT) --- *e.g., 'pending', 'downloaded', 'disabled'.*
        *   `stage_1_status` (TEXT) --- *Tracks Stage 1 processing (e.g., 'pending', 'complete', 'failed').*
        *   `stage_2_status` (TEXT) --- *Tracks Stage 2 processing (e.g., 'pending', 'complete', 'failed').*
        *   `embedding_status` (TEXT) --- *Tracks embedding generation (e.g., 'pending', 'complete', 'failed').*
        *   `last_updated` (DATETIME) --- *Timestamp of the last status change for this video.*

    *   **`RawTranscripts` Table**
        *   `transcript_id` (INTEGER, Primary Key) --- *Unique identifier for each transcript record.*
        *   `video_id` (TEXT, Foreign Key) --- *Links to the `Videos` table.*
        *   `original_language` (TEXT) --- *The original language of the transcript (e.g., 'en', 'es').*
        *   `transcript_text` (TEXT) --- *The raw transcript text in English.*
        *   `is_translated` (BOOLEAN) --- *Whether this transcript was auto-translated to English.*
        *   `downloaded_at` (DATETIME) --- *Timestamp when the transcript was fetched.*

    *   **`RawComments` Table**
        *   `comment_id` (TEXT, Primary Key) --- *The unique YouTube comment ID.*
        *   `video_id` (TEXT, Foreign Key) --- *Links to the `Videos` table.*
        *   `author_name` (TEXT) --- *The display name of the comment author.*
        *   `comment_text` (TEXT) --- *The raw comment text.*
        *   `like_count` (INTEGER) --- *The like count for this specific comment.*
        *   `published_at` (DATETIME) --- *When the comment was originally posted.*
        *   `downloaded_at` (DATETIME) --- *Timestamp when the comment was fetched.*

    *   **`TopicSummaries` Table**
        *   `summary_id` (INTEGER, Primary Key) --- *Unique identifier for each topic-based summary blurb.*
        *   `video_id` (TEXT, Foreign Key) --- *Links to the `Videos` table.*
        *   `summary_text` (TEXT) --- *The AI-generated paragraph summary of a specific topic from the video.*
        *   `source_type` (TEXT) --- *The origin of this topic: 'transcript' or 'comment'.*
        *   `like_count` (INTEGER) --- *NULL for transcript-derived topics, like count for comment-derived topics.*

    *   **`AtomicInsights` Table**
        *   `insight_id` (INTEGER, Primary Key) --- *Unique identifier for each atomic insight.*
        *   `summary_id` (INTEGER, Foreign Key referencing `TopicSummaries`) --- *Links each insight back to its source topic summary.*
        *   `insight_type` (TEXT) --- *The data classification: `"quantitative"` or `"qualitative"`.*
        *   `confidence_score` (INTEGER) --- *The AI's score (1-100) of the insight's relevance and value.*
        *   `insight_text` (TEXT) --- *A single, concise sentence that describes this specific atomic insight.*
        *   `embedding_vector` (BLOB) --- *The vector embedding representation of the insight_text for semantic search.*
        *   `source_type` (TEXT) --- *Inherited from parent TopicSummary: 'transcript' or 'comment'.*
        *   `like_count` (INTEGER) --- *Inherited from parent TopicSummary: NULL for transcript, like count for comments.*