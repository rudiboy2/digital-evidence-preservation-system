# ============================================================
# Blockchain Evidence Preservation System - Backend Dockerfile
# ============================================================
FROM python:3.11-slim AS base

# System dependencies (libmagic for python-magic, libpq for asyncpg)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libmagic1 \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ---- Dependency stage ----
FROM base AS builder
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# ---- Runtime stage ----
FROM base AS runtime

# Create non-root user for security
RUN groupadd -r beps && useradd -r -g beps beps

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11 /usr/local/lib/python3.11
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY backend/ /app/backend/
COPY .env.example /app/.env.example

# Create evidence storage directory
RUN mkdir -p /app/evidence_storage && chown -R beps:beps /app

USER beps

# Set Python path so imports resolve correctly
ENV PYTHONPATH=/app/backend
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
COPY alembic.ini /app/
COPY migrations /app/migrations
