FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY dashboard/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy dashboard application
COPY dashboard/ .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV FLASK_DEBUG=false
ENV DASH_DEBUG=false

# Expose the port the app runs on
EXPOSE 8050

# Add healthcheck
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8050/ || exit 1

# Command to run the application with gunicorn
CMD ["gunicorn", "--workers=2", "--threads=2", "--bind=0.0.0.0:8050", "--timeout=120", "app:server"] 
