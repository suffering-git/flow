"""
Gemini API client wrapper.

Provides simplified interface for Gemini API calls with error handling.
"""

import os
from typing import Any, Optional
import google.generativeai as genai

import config
from utils.logger import get_logger

logger = get_logger(__name__)


class GeminiClient:
    """
    Wrapper for Gemini API calls.

    Handles:
    - API configuration
    - Request execution
    - Error handling
    - Response parsing
    """

    def __init__(self, model_code: str):
        """
        Initialize Gemini client.

        Args:
            model_code: Gemini model code (e.g., 'gemini-2.5-flash-lite').
        """
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        self.model_code = model_code
        self.model = genai.GenerativeModel(model_code)

    async def generate_content(
        self,
        prompt: str,
        response_mime_type: str = "application/json"
    ) -> dict[str, Any]:
        """
        Generate content from prompt.

        Args:
            prompt: Input prompt string.
            response_mime_type: Expected response MIME type.

        Returns:
            Dictionary with:
            - response_text: Generated text
            - input_tokens: Number of input tokens
            - output_tokens: Number of output tokens
        """
        try:
            # Configure generation with response MIME type
            generation_config = genai.GenerationConfig(
                response_mime_type=response_mime_type
            )

            # Generate content
            response = await self.model.generate_content_async(
                prompt,
                generation_config=generation_config
            )

            # Extract token counts from usage metadata
            input_tokens = response.usage_metadata.prompt_token_count
            output_tokens = response.usage_metadata.candidates_token_count

            logger.debug(
                f"🤖 Generated {output_tokens} tokens "
                f"(input: {input_tokens})"
            )

            return {
                "response_text": response.text,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens
            }

        except Exception as e:
            logger.error(f"❌ Gemini API error: {e}")
            raise

    async def generate_embedding(self, text: str) -> list[float]:
        """
        Generate embedding for text.

        Args:
            text: Input text to embed.

        Returns:
            Embedding vector as list of floats.
        """
        try:
            # Generate embedding using Gemini embedding model
            result = genai.embed_content(
                model=self.model_code,
                content=text,
                task_type="retrieval_document"
            )

            logger.debug(f"🔢 Generated embedding for text ({len(text)} chars)")

            return result['embedding']

        except Exception as e:
            logger.error(f"❌ Embedding generation error: {e}")
            raise
