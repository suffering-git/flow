"""
Gemini API rate limits and pricing information.

Data sourced from GEMINI_RATES.md for monitoring and cost tracking.
"""

from typing import TypedDict


class ModelRateLimits(TypedDict):
    """Rate limits for a Gemini model."""
    rpm: int  # Requests per minute
    tpm: int  # Tokens per minute
    rpd: int | None  # Requests per day (None if no limit)


class ModelPricing(TypedDict):
    """Pricing information for a Gemini model (per 1M tokens)."""
    input_price: float  # USD per 1M input tokens
    output_price: float  # USD per 1M output tokens


# Rate limits for each model (Tier 1)
RATE_LIMITS: dict[str, ModelRateLimits] = {
    "gemini-2.5-pro": {
        "rpm": 150,
        "tpm": 2_000_000,
        "rpd": 10_000,
    },
    "gemini-2.5-flash": {
        "rpm": 1_000,
        "tpm": 1_000_000,
        "rpd": 10_000,
    },
    "gemini-2.5-flash-lite": {
        "rpm": 4_000,
        "tpm": 4_000_000,
        "rpd": None,  # No published limit
    },
    "gemini-embedding-001": {
        "rpm": 3_000,
        "tpm": 1_000_000,
        "rpd": None,  # No published limit
    },
}

# Pricing for each model (Standard API, per 1M tokens)
PRICING: dict[str, ModelPricing] = {
    "gemini-2.5-pro": {
        "input_price": 1.25,  # Up to 200k tokens
        "output_price": 10.00,  # Up to 200k tokens
    },
    "gemini-2.5-flash": {
        "input_price": 0.30,
        "output_price": 2.50,
    },
    "gemini-2.5-flash-lite": {
        "input_price": 0.10,
        "output_price": 0.40,
    },
    "gemini-embedding-001": {
        "input_price": 0.15,
        "output_price": 0.00,  # No output pricing for embeddings
    },
}


def get_rate_limits(model_code: str) -> ModelRateLimits:
    """
    Get rate limits for a model.

    Args:
        model_code: Gemini model code (e.g., 'gemini-2.5-flash-lite').

    Returns:
        Rate limits dictionary.

    Raises:
        KeyError: If model code not found.
    """
    return RATE_LIMITS[model_code]


def get_pricing(model_code: str) -> ModelPricing:
    """
    Get pricing for a model.

    Args:
        model_code: Gemini model code (e.g., 'gemini-2.5-flash-lite').

    Returns:
        Pricing dictionary.

    Raises:
        KeyError: If model code not found.
    """
    return PRICING[model_code]


def calculate_cost(
    model_code: str,
    input_tokens: int,
    output_tokens: int
) -> float:
    """
    Calculate API cost in USD.

    Args:
        model_code: Gemini model code.
        input_tokens: Number of input tokens.
        output_tokens: Number of output tokens.

    Returns:
        Total cost in USD.
    """
    pricing = get_pricing(model_code)
    input_cost = (input_tokens / 1_000_000) * pricing["input_price"]
    output_cost = (output_tokens / 1_000_000) * pricing["output_price"]
    return input_cost + output_cost
