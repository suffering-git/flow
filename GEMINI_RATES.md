Here is the updated document with the requested model codes and input/output token limits for Gemini 2.5 Pro, 2.5 Flash, 2.5 Flash-Lite, and Gemini Embedding.

### **Gemini 2.5 Pro**

Gemini 2.5 Pro is a state-of-the-art multipurpose model, excelling at coding and complex reasoning tasks.

*   **Model code:** `gemini-2.5-pro`
*   **Input token limit:** 1,048,576
*   **Output token limit:** 65,536

**Standard API Costs (Tier 1, per 1M tokens):**
*   **Input price:**
    *   $1.25 for prompts up to 200k tokens
    *   $2.50 for prompts greater than 200k tokens
*   **Output price (including thinking tokens):**
    *   $10.00 for prompts up to 200k tokens
    *   $15.00 for prompts greater than 200k tokens
*   **Context caching price:**
    *   $0.31 for prompts up to 200k tokens
    *   $0.625 for prompts greater than 200k tokens
    *   $4.50 / 1,000,000 tokens per hour for storage
*   **Grounding with Google Search:** 1,500 RPD (free), then $35 / 1,000 requests

**Batch Mode Costs (Tier 1, per 1M tokens):**
*   **Input price:**
    *   $0.625 for prompts up to 200k tokens
    *   $1.25 for prompts greater than 200k tokens
*   **Output price (including thinking tokens):**
    *   $5.00 for prompts up to 200k tokens
    *   $7.50 for prompts greater than 200k tokens
*   **Context caching price:**
    *   $0.31 for prompts up to 200k tokens
    *   $0.625 for prompts greater than 200k tokens
    *   $4.50 / 1,000,000 tokens per hour for storage
*   **Grounding with Google Search:** 1,500 RPD (free), then $35 / 1,000 requests

**Rate Limits (Tier 1):**
*   **RPM (Requests Per Minute):** 150
*   **TPM (Tokens Per Minute):** 2,000,000
*   **RPD (Requests Per Day):** 10,000
*   **Batch Enqueued Tokens:** 5,000,000

---

### **Gemini 2.5 Flash**

Gemini 2.5 Flash is a hybrid reasoning model supporting a 1M token context window and has thinking budgets.

*   **Model code:** `gemini-2.5-flash`
*   **Input token limit:** 1,048,576
*   **Output token limit:** 65,536

**Standard API Costs (Tier 1, per 1M tokens):**
*   **Input price:** $0.30 (text / image / video), $1.00 (audio)
*   **Output price (including thinking tokens):** $2.50
*   **Context caching price:** $0.075 (text / image / video), $0.25 (audio), $1.00 / 1,000,000 tokens per hour (storage)
*   **Grounding with Google Search:** 1,500 RPD (free, limit shared with Flash-Lite RPD), then $35 / 1,000 requests
*   **Live API:** Input: $0.50 (text), $3.00 (audio / image [video]), Output: $2.00 (text), $12.00 (audio)

**Batch Mode Costs (Tier 1, per 1M tokens):**
*   **Input price:** $0.15 (text / image / video), $0.50 (audio)
*   **Output price (including thinking tokens):** $1.25
*   **Context caching price:** $0.075 (text / image / video), $0.25 (audio), $1.00 / 1,000,000 tokens per hour (storage)
*   **Grounding with Google Search:** 1,500 RPD (free, limit shared with Flash-Lite RPD), then $35 / 1,000 requests

**Rate Limits (Tier 1):**
*   **RPM (Requests Per Minute):** 1,000
*   **TPM (Tokens Per Minute):** 1,000,000
*   **RPD (Requests Per Day):** 10,000
*   **Batch Enqueued Tokens:** 3,000,000

---

### **Gemini 2.5 Flash-Lite**

Gemini 2.5 Flash-Lite is the smallest and most cost-effective model, built for at-scale usage.

*   **Model code:** `gemini-2.5-flash-lite`
*   **Input token limit:** 1,048,576
*   **Output token limit:** 65,536

**Standard API Costs (Tier 1, per 1M tokens):**
*   **Input price (text, image, video):** $0.10 (text / image / video), $0.30 (audio)
*   **Output price (including thinking tokens):** $0.40
*   **Context caching price:** $0.025 (text / image / video), $0.125 (audio), $1.00 / 1,000,000 tokens per hour (storage)
*   **Grounding with Google Search:** 1,500 RPD (free, limit shared with Flash RPD), then $35 / 1,000 requests

**Batch Mode Costs (Tier 1, per 1M tokens):**
*   **Input price (text, image, video):** $0.05 (text / image / video), $0.15 (audio)
*   **Output price (including thinking tokens):** $0.20
*   **Context caching price:** $0.025 (text / image / video), $0.125 (audio), $1.00 / 1,000,000 tokens per hour (storage)
*   **Grounding with Google Search:** 1,500 RPD (free, limit shared with Flash RPD), then $35 / 1,000 requests

**Rate Limits (Tier 1):**
*   **RPM (Requests Per Minute):** 4,000
*   **TPM (Tokens Per Minute):** 4,000,000
*   **RPD (Requests Per Day):** No published rate limits
*   **Batch Enqueued Tokens:** 10,000,000

---

### **Gemini Embedding**

Gemini Embedding is the newest embeddings model, more stable and with higher rate limits than previous versions.

*   **Model code:** `gemini-embedding-001`
*   **Input token limit:** 2,048
*   **Output:** Text embeddings (Flexible dimension size: 128 - 3072, Recommended: 768)

**Standard API Costs (Tier 1, per 1M tokens):**
*   **Input price:** $0.15

**Batch Mode Costs (Tier 1, per 1M tokens):**
*   **Input price:** $0.075

**Rate Limits (Tier 1):**
*   **RPM (Requests Per Minute):** 3,000
*   **TPM (Tokens Per Minute):** 1,000,000
*   **RPD (Requests Per Day):** No published rate limits
*   **Batch Enqueued Tokens:** No published rate limits

---

### **Batch Mode Details**

Batch mode requests have their own rate limits, separate from non-batch API calls.

*   **Concurrent batch requests:** 100
*   **Input file size limit:** 2GB
*   **File storage limit:** 20GB
*   **Enqueued tokens per model:** The "Batch Enqueued Tokens" in the rate limits tables above represent the maximum number of tokens that can be enqueued for batch processing across all your active batch jobs for a given model.