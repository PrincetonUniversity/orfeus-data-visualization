# Multi-arch slim Python base
FROM python:3.8-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8055

# Install system dependencies (optional but useful)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first (leverage layer caching)
COPY requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy only necessary application files (avoid bringing data/ into the image)
COPY app.py wsgi.py ./
COPY assets/ assets/
COPY pages/ pages/
COPY inputs/ inputs/
COPY utils/ utils/
COPY markdown/ markdown/

# Ensure runtime mount point exists even when volume not attached
RUN mkdir -p /app/data

EXPOSE 8055

# Gunicorn config via env: PORT, WEB_CONCURRENCY, THREADS
CMD ["/bin/sh", "-c", "gunicorn -w ${WEB_CONCURRENCY:-2} -k gthread --threads ${THREADS:-8} -b 0.0.0.0:${PORT:-8055} wsgi:server"]
