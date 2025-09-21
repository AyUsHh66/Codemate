# Use Python 3.11 slim image for smaller footprint
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install minimal system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies with optimizations for memory
RUN pip install --no-cache-dir --no-deps -r requirements.txt && \
    pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu && \
    rm -rf ~/.cache/pip

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p data storage output_parsed_markdown exports embedding_cache

# Set environment variables for memory optimization
ENV PYTHONPATH=/app
ENV FLASK_APP=server.py
ENV FLASK_ENV=production
ENV CUDA_VISIBLE_DEVICES=""
ENV TOKENIZERS_PARALLELISM=false
ENV OMP_NUM_THREADS=1

# Expose port
EXPOSE 8080

# Run the application with memory-optimized gunicorn settings
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "1", "--threads", "2", "--timeout", "300", "--worker-class", "sync", "--max-requests", "100", "--max-requests-jitter", "10", "server:app"]