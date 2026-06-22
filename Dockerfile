# ============================================================
# Stage 1: Python dependencies
# ============================================================
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-warn-script-location \
    gunicorn==23.0.0 \
    -r requirements.txt

# ============================================================
# Stage 2: Runtime image
# ============================================================
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PORT=8000 \
    WORKERS=4 \
    MAX_REQUESTS=10000 \
    MAX_REQUESTS_JITTER=1000 \
    TIMEOUT=120 \
    KEEP_ALIVE=5 \
    LOG_LEVEL=info \
    APP_MODULE=api.main:app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && addgroup --system --gid 1001 app \
    && adduser --system --uid 1001 --gid 1001 app

WORKDIR /app

COPY --from=builder /usr/local /usr/local

RUN mkdir -p /app/uploads /app/cache /app/frontend/thumbnails /app/frontend/brain_viz \
    && chown -R app:app /app

COPY --chown=app:app . .

USER app

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

CMD exec gunicorn api.main:app \
    --worker-class uvicorn.workers.UvicornWorker \
    --workers $WORKERS \
    --bind 0.0.0.0:$PORT \
    --timeout $TIMEOUT \
    --keep-alive $KEEP_ALIVE \
    --max-requests $MAX_REQUESTS \
    --max-requests-jitter $MAX_REQUESTS_JITTER \
    --access-logfile - \
    --error-logfile - \
    --log-level $LOG_LEVEL \
    --forwarded-allow-ips '*' \
    --graceful-timeout 30
