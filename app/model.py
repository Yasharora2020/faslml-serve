"""Sentiment analysis model wrapper using HuggingFace Transformers."""

import logging
import time
from typing import Any

import torch
from transformers import pipeline

# Configure logger for this module
logger = logging.getLogger(__name__)


class SentimentModel:
    """
    A wrapper class for sentiment analysis using pre-trained HuggingFace models.

    This class provides a high-level interface for loading and running sentiment
    analysis models, with support for both single and batch predictions.
    """

    def __init__(
        self, model_name: str = "distilbert-base-uncased-finetuned-sst-2-english"
    ) -> None:
        """
        Initialize the sentiment model.

        Args:
            model_name: HuggingFace model identifier for sentiment analysis.
                       Defaults to DistilBERT fine-tuned on SST-2.
        """
        self.model_name = model_name
        self.model = None  # Placeholder for the actual model
        self.tokenizer = None  # Placeholder for tokenizer
        self.pipeline = None  # HuggingFace pipeline for inference

        # Automatically detect and use GPU if available
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Using device: {self.device}")

    def load_model(self) -> None:
        """
        Load the pre-trained model and create an inference pipeline.

        This method downloads the model (if not cached), initializes the
        pipeline, and performs a warmup prediction to ensure everything
        is working correctly.

        Raises:
            Exception: If model loading fails for any reason.
        """
        try:
            logger.info(f"Loading model: {self.model_name}")
            start_time = time.time()

            # Create HuggingFace pipeline for sentiment analysis
            # device=0 for GPU (CUDA), -1 for CPU
            self.pipeline = pipeline(
                "sentiment-analysis",
                model=self.model_name,
                device=0 if self.device == "cuda" else -1,
            )

            # Warmup: Run a dummy prediction to load model into memory
            # This ensures the first real prediction isn't slow
            self.pipeline("This is a test")

            load_time = time.time() - start_time
            logger.info(f"Model loaded successfully in {load_time:.2f} seconds")

        except Exception as e:
            logger.error(f"Failed to load model: {str(e)}")
            raise

    def predict(self, text: str) -> dict[str, Any]:
        """
        Perform sentiment analysis on a single text.

        Args:
            text: Input text to analyze for sentiment.

        Returns:
            Dictionary containing:
            - sentiment: 'positive' or 'negative'
            - confidence: Confidence score between 0.0 and 1.0
            - processing_time: Time taken for inference in seconds

        Raises:
            RuntimeError: If the model is not loaded.
            Exception: If prediction fails.
        """
        if not self.pipeline:
            raise RuntimeError("Model not loaded")

        start_time = time.time()

        try:
            # Get prediction from the pipeline (returns list with single result)
            result = self.pipeline(text)[0]
            processing_time = time.time() - start_time

            # Map model output labels to standardized format
            # HuggingFace models typically return 'POSITIVE'/'NEGATIVE'
            sentiment_map = {"POSITIVE": "positive", "NEGATIVE": "negative"}

            return {
                "sentiment": sentiment_map.get(
                    result["label"], result["label"].lower()
                ),
                "confidence": result["score"],
                "processing_time": processing_time,
            }

        except Exception as e:
            logger.error(f"Prediction failed: {str(e)}")
            raise

    def predict_batch(self, texts: list[str]) -> list[dict[str, Any]]:
        """
        Perform sentiment analysis on multiple texts efficiently.

        Batch processing is more efficient than individual predictions
        as it leverages vectorized operations and reduces overhead.

        Args:
            texts: List of input texts to analyze.

        Returns:
            List of dictionaries, each containing:
            - sentiment: 'positive' or 'negative'
            - confidence: Confidence score between 0.0 and 1.0
            - processing_time: Average time per prediction in seconds

        Raises:
            RuntimeError: If the model is not loaded.
            Exception: If batch prediction fails.
        """
        if not self.pipeline:
            raise RuntimeError("Model not loaded")

        start_time = time.time()

        try:
            # Process all texts in a single batch for efficiency
            results = self.pipeline(texts)
            processing_time = time.time() - start_time

            # Map model output labels to standardized format
            sentiment_map = {"POSITIVE": "positive", "NEGATIVE": "negative"}

            predictions = []
            # Process each result and calculate average processing time
            for result in results:
                predictions.append(
                    {
                        "sentiment": sentiment_map.get(
                            result["label"], result["label"].lower()
                        ),
                        "confidence": result["score"],
                        # Distribute total processing time across all predictions
                        "processing_time": processing_time / len(texts),
                    }
                )

            return predictions

        except Exception as e:
            logger.error(f"Batch prediction failed: {str(e)}")
            raise

    def is_loaded(self) -> bool:
        """
        Check if the model is loaded and ready for predictions.

        Returns:
            True if the model pipeline is initialized, False otherwise.
        """
        return self.pipeline is not None
