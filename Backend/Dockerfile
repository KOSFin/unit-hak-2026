FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONPATH=/app

WORKDIR /app

# gosu lets the container fix mounted-volume permissions as root and then
# drop privileges before starting the application process.
RUN apt-get update \
    && apt-get install -y --no-install-recommends gosu \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies first (layer cache)
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# App source
COPY . .
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh

# Non-root user for security
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser
RUN chmod +x /usr/local/bin/docker-entrypoint.sh \
    && mkdir -p /app/uploads \
    && chown -R appuser:appgroup /app /usr/local/bin/docker-entrypoint.sh

ENTRYPOINT ["docker-entrypoint.sh"]

# Default command (overridden in docker-compose per service)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
