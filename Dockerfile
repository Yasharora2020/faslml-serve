# Multi-stage build for optimized production image
FROM python:3.11-slim as builder

WORKDIR /build

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy project files
COPY pyproject.toml uv.lock README.md ./
COPY app/ ./app/

# Install dependencies
RUN uv sync --frozen --no-cache

# Production stage
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies and create user
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd -r appuser && useradd -r -g appuser -m appuser

# Copy the virtual environment from builder stage
COPY --from=builder /build/.venv /app/.venv

# Copy application code
COPY app/ ./app/

# Fix shebang lines in virtual environment scripts
RUN find /app/.venv/bin -type f -executable -exec sed -i '1s|^#!.*python.*|#!/app/.venv/bin/python|' {} \;

# Create HuggingFace cache directory with proper permissions
RUN mkdir -p /home/appuser/.cache/huggingface && \
    chown -R appuser:appuser /home/appuser/.cache && \
    chown -R appuser:appuser /app

USER appuser

# Add .venv to PATH and set HuggingFace cache directory
ENV PATH="/app/.venv/bin:$PATH"
ENV TRANSFORMERS_CACHE="/home/appuser/.cache/huggingface"
ENV HF_HOME="/home/appuser/.cache/huggingface"

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Run the application
CMD ["/app/.venv/bin/python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]