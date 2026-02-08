FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements-gateway.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements-gateway.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 asmblr && chown -R asmblr:asmblr /app
USER asmblr

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Run the application
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
