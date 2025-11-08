"""
Pydantic models for Stage 1 (Data Compression) validation.

Validates AI output from Stage 1 compression process.
"""

from pydantic import BaseModel, Field


class CompressedComment(BaseModel):
    """
    A single compressed comment.

    Contains only comment_id and compressed_text for token efficiency.
    """
    comment_id: str = Field(..., description="YouTube comment ID for source attribution")
    compressed_text: str = Field(..., description="Compressed/filtered comment text")


class Stage1Output(BaseModel):
    """
    Output structure from Stage 1 AI processing.

    Contains compressed transcript and comments with timestamps preserved.
    """
    compressed_transcript: str = Field(
        ...,
        description="Compressed transcript with embedded timestamps e.g., '[00:02:42] text'"
    )
    compressed_comments: list[CompressedComment] = Field(
        ...,
        description="List of compressed comments with IDs for attribution"
    )
