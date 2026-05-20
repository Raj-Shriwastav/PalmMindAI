# Stage 1: Build dependencies
FROM python:3.10-slim AS builder

WORKDIR /build

# Install compilation packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Final minimal runtime
FROM python:3.10-slim

WORKDIR /app

# Install only runtime essentials
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy user dependencies from builder
COPY --from=builder /usr/local /usr/local
ENV PYTHONUNBUFFERED=1

# Copy application source
COPY app/ /app/app/

# Expose FastAPI default port
EXPOSE 8000

# Create non-root application user for isolation
RUN useradd -m -u 8888 appuser && chown -R appuser:appuser /app
USER appuser

# Healthcheck to verify status of FastAPI web service
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD curl --fail http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
