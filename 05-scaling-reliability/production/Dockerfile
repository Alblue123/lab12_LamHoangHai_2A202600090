# syntax=docker/dockerfile:1
FROM python:3.11-slim

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y gcc libpq-dev && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY 05-scaling-reliability/production/requirements.txt ./
# Sửa dòng 12 trong Dockerfile thành:
RUN pip install --no-cache-dir --default-timeout=1000 -r requirements.txt

# Copy app code
COPY 05-scaling-reliability/production/app.py ./
COPY 05-scaling-reliability/production/utils ./utils

# Expose port
EXPOSE 8000

# Start the app
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--timeout-graceful-shutdown", "30"]
