FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
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

# Ensure session.json is a file, not a directory (remove dir if exists)
USER root
RUN rm -rf /app/session.json && touch /app/session.json && chown appuser:appuser /app/session.json
USER appuser

# Expose dashboard port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

CMD ["python", "-m", "src.main"]