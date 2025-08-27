"""
FastML Serve - A lightweight ML inference server for sentiment analysis.

This package provides a production-ready FastAPI application that serves
sentiment analysis predictions via REST API endpoints, complete with
monitoring, error handling, and batch processing capabilities.

Modules:
    main: FastAPI application with API endpoints
    model: Sentiment analysis model wrapper
    schemas: Pydantic models for request/response validation

Usage:
    Run the server with: uv run python -m uvicorn app.main:app
"""
