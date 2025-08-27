"""
Unit tests for FastML Serve API endpoints.

This module contains comprehensive test cases for all API endpoints,
including happy path scenarios, error cases, and input validation.
Tests use mocked models to avoid dependencies on actual ML inference.
"""

import os
import sys
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.main import app


@pytest.fixture
def client():
    """
    FastAPI test client fixture.

    Returns:
        TestClient: Configured test client for the FastML Serve app
    """
    return TestClient(app)


@pytest.fixture
def mock_model():
    """
    Mock sentiment model fixture for testing without actual ML inference.

    This fixture mocks the model behavior to return predictable responses,
    allowing tests to focus on API logic rather than model performance.

    Yields:
        Mock: Mocked model with pre-configured responses
    """
    with patch("app.main.model") as mock:
        # Configure mock to simulate a loaded, working model
        mock.is_loaded.return_value = True

        # Mock single prediction response
        mock.predict.return_value = {
            "sentiment": "positive",
            "confidence": 0.9999,
            "processing_time": 0.001,
        }

        # Mock batch prediction response (2 predictions)
        mock.predict_batch.return_value = [
            {"sentiment": "positive", "confidence": 0.9999, "processing_time": 0.001},
            {"sentiment": "negative", "confidence": 0.9998, "processing_time": 0.001},
        ]
        yield mock


class TestHealthEndpoint:
    """Test cases for the health check endpoint."""

    def test_health_check_healthy(self, client, mock_model):
        """
        Test health endpoint returns healthy status when model is loaded.

        Verifies that the health check endpoint returns appropriate status
        information when the ML model is loaded and ready.
        """
        response = client.get("/health")

        # Verify response structure and status
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["model_loaded"] is True
        assert "uptime" in data
        assert "timestamp" in data


class TestPredictionEndpoints:
    """Test cases for sentiment prediction endpoints."""

    def test_single_prediction(self, client, mock_model):
        """
        Test single text prediction endpoint with valid input.

        Verifies that the prediction endpoint correctly processes single
        text inputs and returns properly structured responses.
        """
        test_data = {"text": "I love this product!"}
        response = client.post("/predict", json=test_data)

        # Verify successful prediction response
        assert response.status_code == 200
        data = response.json()
        assert data["text"] == "I love this product!"
        assert data["sentiment"] == "positive"
        assert 0.0 <= data["confidence"] <= 1.0
        assert "processing_time" in data
        assert "timestamp" in data

    def test_batch_prediction(self, client, mock_model):
        """
        Test batch prediction endpoint with multiple texts.

        Verifies that the batch endpoint processes multiple texts
        and returns results for each input in the correct format.
        """
        test_data = {"texts": ["I love this product!", "This is terrible."]}
        response = client.post("/predict/batch", json=test_data)

        # Verify successful batch prediction response
        assert response.status_code == 200
        data = response.json()
        assert len(data["predictions"]) == 2
        assert "total_processing_time" in data
        assert "timestamp" in data

        # Verify each prediction in the batch
        for prediction in data["predictions"]:
            assert prediction["sentiment"] in ["positive", "negative"]
            assert 0.0 <= prediction["confidence"] <= 1.0

    def test_empty_text_validation(self, client):
        """
        Test input validation rejects empty text.

        Verifies that the API properly validates input and rejects
        requests with empty text strings.
        """
        test_data = {"text": ""}
        response = client.post("/predict", json=test_data)
        # Should return 422 Unprocessable Entity for validation error
        assert response.status_code == 422

    def test_long_text_validation(self, client):
        """
        Test input validation rejects excessively long text.

        Verifies that the API enforces maximum text length limits
        to prevent performance issues with very long inputs.
        """
        test_data = {"text": "x" * 1000}  # Exceeds 512 character limit
        response = client.post("/predict", json=test_data)
        # Should return 422 Unprocessable Entity for validation error
        assert response.status_code == 422

    def test_empty_batch_validation(self, client):
        """
        Test batch validation rejects empty text lists.

        Verifies that batch prediction endpoint rejects requests
        with empty lists of texts.
        """
        test_data = {"texts": []}
        response = client.post("/predict/batch", json=test_data)
        # Should return 422 Unprocessable Entity for validation error
        assert response.status_code == 422

    def test_large_batch_validation(self, client):
        """
        Test batch validation rejects excessively large batches.

        Verifies that the API enforces maximum batch size limits
        to prevent memory issues and ensure reasonable response times.
        """
        test_data = {"texts": ["test"] * 50}  # Exceeds 32 item limit
        response = client.post("/predict/batch", json=test_data)
        # Should return 422 Unprocessable Entity for validation error
        assert response.status_code == 422


class TestMetricsEndpoint:
    """Test cases for Prometheus metrics endpoint."""

    def test_metrics_endpoint(self, client, mock_model):
        """
        Test metrics endpoint returns Prometheus-formatted data.

        Verifies that the metrics endpoint is accessible and returns
        data in the expected Prometheus text format.
        """
        response = client.get("/metrics")

        # Verify metrics are returned successfully
        assert response.status_code == 200
        assert "text/plain" in response.headers["content-type"]


class TestRootEndpoint:
    """Test cases for the root API information endpoint."""

    def test_root_endpoint(self, client):
        """
        Test root endpoint returns API information.

        Verifies that the root endpoint provides basic API metadata
        and endpoint discovery information.
        """
        response = client.get("/")

        # Verify API information is returned
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "endpoints" in data
