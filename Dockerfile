# Multi-stage Dockerfile for Agentic RAG with Web UI
FROM python:3.11-slim as base

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy web UI requirements and install
COPY web_ui/requirements.txt web_ui_requirements.txt
RUN pip install --no-cache-dir -r web_ui_requirements.txt

# Install curl for health checks
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Copy application code
COPY . .

# Ensure startup script exists and is executable
RUN ls -la /app/start.sh && chmod +x /app/start.sh

# Expose ports
EXPOSE 5000 8058

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Start both services using bash explicitly
CMD ["/bin/bash", "/app/start.sh"]
