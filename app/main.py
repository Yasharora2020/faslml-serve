"""
FastML Serve - A lightweight ML inference server for sentiment analysis.

This module provides a production-ready FastAPI server that serves a pre-trained
sentiment analysis model via REST API endpoints. It includes comprehensive
monitoring, error handling, and batch processing capabilities.
"""

import logging
import time
from contextlib import asynccontextmanager
from datetime import datetime

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from starlette.middleware.base import BaseHTTPMiddleware
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

from .model import SentimentModel
from .schemas import (
    BatchPredictionRequest,
    BatchPredictionResponse,
    HealthResponse,
    PredictionRequest,
    PredictionResponse,
)

# Configure structured logging for the application
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Prometheus metrics for monitoring and observability
REQUEST_COUNT = Counter(
    "requests_total", "Total number of requests", ["method", "endpoint"]
)
REQUEST_DURATION = Histogram("request_duration_seconds", "Request duration")
PREDICTION_COUNT = Counter("predictions_total", "Total number of predictions")

# Global model instance - initialized with environment variable
import os
model_name = os.getenv("MODEL_NAME", "distilbert-base-uncased-finetuned-sst-2-english")
model = SentimentModel(model_name=model_name)
# Track application start time for uptime calculation
start_time = time.time()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """
    Application lifespan manager for startup and shutdown events.

    This context manager handles model loading during startup and
    cleanup during shutdown. It ensures the ML model is ready
    before accepting requests.

    Args:
        app: The FastAPI application instance.

    Raises:
        Exception: If model loading fails during startup.
    """
    # Startup: Load the ML model
    logger.info("Starting up...")
    try:
        model.load_model()
        logger.info("Model loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise

    yield  # Application runs here

    # Shutdown: Cleanup resources
    logger.info("Shutting down...")


# Initialize FastAPI application with metadata and lifespan manager
app = FastAPI(
    title="FastML Serve",
    description="A lightweight ML inference server for sentiment analysis",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=False,  # Cannot use True with wildcard origins
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint for monitoring and load balancer probes.

    This endpoint provides information about the application's health status,
    including whether the ML model is loaded and ready for predictions.

    Returns:
        HealthResponse: Health status including:
        - status: 'healthy' or 'unhealthy'
        - model_loaded: Whether the ML model is loaded
        - uptime: Application uptime in seconds
        - timestamp: Current timestamp
    """
    # Increment request counter for monitoring
    REQUEST_COUNT.labels(method="GET", endpoint="/health").inc()

    return HealthResponse(
        status="healthy" if model.is_loaded() else "unhealthy",
        model_loaded=model.is_loaded(),
        model_name=model_name,
        uptime=time.time() - start_time,
        timestamp=datetime.now(),
    )


@app.post("/predict", response_model=PredictionResponse)
async def predict(request: PredictionRequest):
    """
    Perform sentiment analysis on a single text input.

    This endpoint analyzes the sentiment of the provided text and returns
    the predicted sentiment (positive/negative) along with confidence score
    and processing time metrics.

    Args:
        request: PredictionRequest containing the text to analyze

    Returns:
        PredictionResponse: Prediction results including:
        - text: Original input text
        - sentiment: Predicted sentiment ('positive' or 'negative')
        - confidence: Model confidence score (0.0 to 1.0)
        - processing_time: Time taken for prediction in seconds
        - timestamp: When the prediction was made

    Raises:
        HTTPException: 500 if prediction fails
    """
    # Increment metrics for monitoring
    REQUEST_COUNT.labels(method="POST", endpoint="/predict").inc()
    PREDICTION_COUNT.inc()

    # Track request duration for performance monitoring
    with REQUEST_DURATION.time():
        try:
            # Perform sentiment analysis using the loaded model
            result = model.predict(request.text)

            return PredictionResponse(
                text=request.text,
                sentiment=result["sentiment"],
                confidence=result["confidence"],
                processing_time=result["processing_time"],
                timestamp=datetime.now(),
            )

        except Exception as e:
            logger.error(f"Prediction error: {e}")
            raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/predict/batch", response_model=BatchPredictionResponse)
async def predict_batch(request: BatchPredictionRequest):
    """
    Perform sentiment analysis on multiple texts efficiently.

    This endpoint processes multiple texts in a single request, which is
    more efficient than individual requests due to model batching capabilities.
    Useful for processing large volumes of text data.

    Args:
        request: BatchPredictionRequest containing list of texts to analyze

    Returns:
        BatchPredictionResponse: Batch prediction results including:
        - predictions: List of individual prediction results
        - total_processing_time: Total time for the entire batch
        - timestamp: When the batch prediction was completed

    Raises:
        HTTPException: 500 if batch prediction fails
    """
    # Increment metrics (count all texts in the batch)
    REQUEST_COUNT.labels(method="POST", endpoint="/predict/batch").inc()
    PREDICTION_COUNT.inc(len(request.texts))

    # Track request duration for performance monitoring
    with REQUEST_DURATION.time():
        try:
            # Track batch processing time separately from individual predictions
            batch_start = time.time()
            results = model.predict_batch(request.texts)
            total_time = time.time() - batch_start

            # Build response with individual predictions
            predictions = []
            for text, result in zip(request.texts, results, strict=False):
                predictions.append(
                    PredictionResponse(
                        text=text,
                        sentiment=result["sentiment"],
                        confidence=result["confidence"],
                        processing_time=result["processing_time"],
                        timestamp=datetime.now(),
                    )
                )

            return BatchPredictionResponse(
                predictions=predictions,
                total_processing_time=total_time,
                timestamp=datetime.now(),
            )

        except Exception as e:
            logger.error(f"Batch prediction error: {e}")
            raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/metrics")
async def get_metrics():
    """
    Prometheus metrics endpoint for monitoring and observability.

    This endpoint exposes application metrics in Prometheus format,
    including request counts, processing times, and prediction counts.
    Typically scraped by Prometheus or compatible monitoring systems.

    Returns:
        Response: Prometheus-formatted metrics data
    """
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/")
async def root():
    """
    Root endpoint providing API information and available endpoints.

    This endpoint serves as a basic API discovery mechanism, returning
    information about the service and its available endpoints.

    Returns:
        dict: API metadata and endpoint information
    """
    return {
        "message": "FastML Serve - Sentiment Analysis API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "predict": "/predict",
            "batch_predict": "/predict/batch",
            "metrics": "/metrics",
            "docs": "/docs",
        },
    }


if __name__ == "__main__":
    # Development server entry point - use uvicorn directly for production
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
