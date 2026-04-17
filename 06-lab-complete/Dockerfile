# Stage 1: Builder
FROM python:3.11-slim AS builder
WORKDIR /app
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim AS runtime
WORKDIR /app
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*
RUN useradd -m appuser
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY ./app ./app

# Add healthcheck
HEALTHCHECK --interval=30s --timeout=3s \
  CMD curl --fail http://localhost:${PORT:-8000}/health || exit 1

RUN chown -R appuser:appuser /app
USER appuser
CMD sh -c "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"
