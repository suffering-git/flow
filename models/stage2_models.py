"""
Pydantic models for Stage 2 (Topic Extraction) validation.

Validates AI output from Stage 2 analysis process with inline timestamp syntax.
"""

from typing import Literal, Optional
from pydantic import BaseModel, Field, field_validator


class AtomicInsight(BaseModel):
    """
    A single atomic insight within a topic.

    Text contains inline timestamp syntax: {text [timestamp|timestamp]}
    """
    insight_type: Literal["quantitative", "qualitative"] = Field(
        ...,
        description="Classification: quantitative (numbers, metrics) or qualitative (descriptions, processes)"
    )
    insight_text: str = Field(
        ...,
        description="Insight text with inline timestamp syntax for transcript-derived insights"
    )
    confidence_score: int = Field(
        ...,
        ge=1,
        le=100,
        description="AI confidence score (1-100) for insight relevance and value"
    )


class TopicSummary(BaseModel):
    """
    A topic summary with nested atomic insights.

    Summary text contains inline timestamp syntax: {text [timestamp|timestamp]}
    """
    topic_title: str = Field(..., description="Brief descriptive title for the topic")
    summary_text: str = Field(
        ...,
        description="Topic summary with inline timestamp syntax for transcript-derived topics"
    )
    source_type: Literal["transcript", "comment"] = Field(
        ...,
        description="Origin of topic: transcript or comment"
    )
    confidence_score: int = Field(
        ...,
        ge=1,
        le=100,
        description="AI confidence score (1-100) for topic relevance and value"
    )
    comment_id: Optional[str] = Field(
        None,
        description="Comment ID for comment-derived topics (NULL for transcript topics)"
    )
    atomic_insights: list[AtomicInsight] = Field(
        ...,
        description="List of atomic insights nested within this topic"
    )


class Stage2Output(BaseModel):
    """
    Output structure from Stage 2 AI processing.

    Contains topics with nested atomic insights using inline timestamp syntax.
    """
    topics: list[TopicSummary] = Field(
        ...,
        description="List of topic summaries with nested atomic insights"
    )
