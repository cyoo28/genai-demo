# Stage 1: Build stage
FROM python:3.13-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libffi-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install deps to a custom directory
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --prefix=/install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# Stage 2: Final runtime image
FROM python:3.13-slim

WORKDIR /app

# Copy installed Python packages from builder
COPY --from=builder /install /usr/local

# Copy app code
COPY --from=builder /app .

# Expose port
EXPOSE 8080

# Environment variables
ENV GCPREGION=us-central1 \
    FLASK_APP=genai_webapp \
    PORT=8080

# Run your app
CMD ["waitress-serve", "--host=0.0.0.0", "--port=8080", "genai_webapp:app"]
