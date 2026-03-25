FROM python:3.11-slim

WORKDIR /app

# Install system dependencies including curl for healthchecks
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY templates/ ./templates/

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose dashboard port
EXPOSE 5000

# Health check - longer start period for app initialization
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=5 \
    CMD curl -f http://localhost:5000/health || exit 1

CMD ["python", "-m", "src.main"]