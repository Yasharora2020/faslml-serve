"""
Pydantic schemas for FastML Serve API request and response models.

This module defines the data structures used for API communication,
including request validation, response serialization, and OpenAPI
documentation generation.
"""

from datetime import datetime

from pydantic import BaseModel, Field


class PredictionRequest(BaseModel):
    """
    Schema for single text sentiment analysis requests.

    This model validates and parses incoming requests for sentiment analysis
    of a single text input. It enforces length constraints to prevent
    processing extremely long texts that could impact performance.
    """

    text: str = Field(
        ...,
        min_length=1,
        max_length=512,
        description="Text to analyze for sentiment (1-512 characters)",
    )

    class Config:
        """Pydantic configuration with example for API documentation."""

        json_schema_extra = {"example": {"text": "I love this product! It's amazing."}}


class BatchPredictionRequest(BaseModel):
    """
    Schema for batch sentiment analysis requests.

    This model handles requests containing multiple texts for efficient
    batch processing. It limits the batch size to prevent memory issues
    and ensure reasonable response times.
    """

    texts: list[str] = Field(
        ...,
        min_items=1,
        max_items=32,
        description="List of texts to analyze (1-32 items, each max 512 chars)",
    )

    class Config:
        """Pydantic configuration with example for API documentation."""

        json_schema_extra = {
            "example": {
                "texts": [
                    "I love this product!",
                    "This is terrible.",
                    "Not sure how I feel about this.",
                ]
            }
        }


class PredictionResponse(BaseModel):
    """
    Schema for sentiment analysis prediction responses.

    This model structures the response from sentiment analysis operations,
    including the prediction results, confidence scores, and performance
    metrics for monitoring and debugging purposes.
    """

    text: str = Field(description="Original input text that was analyzed")
    sentiment: str = Field(description="Predicted sentiment: 'positive' or 'negative'")
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Model confidence score (0.0 to 1.0)"
    )
    processing_time: float = Field(description="Time taken for prediction in seconds")
    timestamp: datetime = Field(description="When the prediction was made")


class BatchPredictionResponse(BaseModel):
    """
    Schema for batch sentiment analysis prediction responses.

    This model structures responses from batch prediction operations,
    containing individual prediction results along with overall batch
    processing metrics.
    """

    predictions: list[PredictionResponse] = Field(
        description="List of individual prediction results"
    )
    total_processing_time: float = Field(
        description="Total time for processing the entire batch in seconds"
    )
    timestamp: datetime = Field(description="When the batch prediction was completed")


class HealthResponse(BaseModel):
    """
    Schema for health check endpoint responses.

    This model provides structured health information about the application,
    including the status of critical components like the ML model and
    performance metrics like uptime.
    """

    status: str = Field(description="Overall health status: 'healthy' or 'unhealthy'")
    model_loaded: bool = Field(description="Whether the ML model is loaded and ready")
    model_name: str = Field(description="Name of the currently loaded ML model")
    uptime: float = Field(description="Application uptime in seconds")
    timestamp: datetime = Field(description="Current server timestamp")
