FROM python:3.10-slim AS base

# Prevent Python from writing pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies for psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# ---------------------
# Dependencies stage
# ---------------------
FROM base AS dependencies

# Install pip dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---------------------
# Production stage
# ---------------------
FROM dependencies AS production

# Create non-root user for security
RUN addgroup --system --gid 1001 appgroup && \
    adduser --system --uid 1001 --ingroup appgroup appuser

# Copy application code
COPY --chown=appuser:appgroup . .

# Create logs directory
RUN mkdir -p logs && chown appuser:appgroup logs

USER appuser

EXPOSE 8000

# Run the application
CMD ["python", "main.py"]
