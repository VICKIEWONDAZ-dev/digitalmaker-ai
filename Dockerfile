# Production Dockerfile for DigitalMaker AI
FROM python:3.11-slim

# Install system dependencies & FFmpeg
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

# Expose server port
EXPOSE 8000

# Start server
CMD ["python", "backend/app.py"]
