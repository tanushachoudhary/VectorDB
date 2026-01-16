FROM python:3.11-slim 
# balance between size and compatibility

# Set working directory
WORKDIR /app

# Set environment variables (reduce layer count by combining)
# forces python output to stdout/stderr (no buffering)
# without this logs delayed
ENV PYTHONUNBUFFERED=1 \
    # prevents python from writing .pyc files
    PYTHONDONTWRITEBYTECODE=1 \
    # prevents pip from caching packages
    PIP_NO_CACHE_DIR=1 \
    # skips checking for newer pip version
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies in single RUN (reduces layers)
# slim base has apt-get
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    libmagic1 \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy requirements first (leverages Docker layer caching - changes less frequently)
COPY requirements.txt .

# Install dependencies in single layer
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt

# Copy application code (changes frequently - placed after dependencies)
COPY . .

# Create persistent directory
RUN mkdir -p /app/chroma_db

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]