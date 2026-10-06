# Multi-stage production Dockerfile for Portfolio Assistant FastAPI Backend
FROM python:3.10-slim AS builder

WORKDIR /app

# Install build dependencies for C-extensions (e.g. psycopg2, cryptography)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Final runtime stage
FROM python:3.10-slim AS runner

WORKDIR /app

# Install runtime dependencies (curl for container health checks)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create unprivileged application user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copy installed Python packages from builder
COPY --from=builder /root/.local /home/appuser/.local
ENV PATH=/home/appuser/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Copy application configuration, database migrations, and source code
COPY --chown=appuser:appuser alembic.ini .
COPY --chown=appuser:appuser alembic/ ./alembic/
COPY --chown=appuser:appuser src/ ./src/

RUN mkdir -p /app/logs && chown -R appuser:appuser /app

USER appuser

# GCP Cloud Run injects $PORT (default 8080)
EXPOSE 8080

# Execute uvicorn server binding dynamically to $PORT or default 8080
CMD ["sh", "-c", "exec uvicorn src.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
