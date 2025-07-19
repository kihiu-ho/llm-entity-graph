# Multi-platform Dockerfile for Agentic RAG Web UI
# Supports both ARM64 (Apple Silicon) and AMD64 (Intel/x86) architectures

# Use build arguments for platform detection
ARG TARGETPLATFORM
ARG BUILDPLATFORM
ARG TARGETOS
ARG TARGETARCH

FROM python:3.11-slim

# Print build information for debugging
RUN echo "Building Web UI for platform: $TARGETPLATFORM" && \
    echo "Build platform: $BUILDPLATFORM" && \
    echo "Target OS: $TARGETOS" && \
    echo "Target architecture: $TARGETARCH"

# Set working directory
WORKDIR /app

# Install system dependencies with platform-specific optimizations
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Platform-specific pip optimizations
RUN if [ "$TARGETARCH" = "arm64" ]; then \
        echo "Configuring pip for ARM64..."; \
        pip install --upgrade pip setuptools wheel; \
    elif [ "$TARGETARCH" = "amd64" ]; then \
        echo "Configuring pip for AMD64..."; \
        pip install --upgrade pip setuptools wheel; \
    else \
        echo "Unknown architecture: $TARGETARCH"; \
        pip install --upgrade pip setuptools wheel; \
    fi

# Copy requirements first for better caching
COPY requirements.txt .
COPY web_ui/requirements.txt web_ui/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r web_ui/requirements.txt

# Copy application code
COPY . .

# Create non-root user for security (platform-agnostic)
RUN useradd --create-home --shell /bin/bash --uid 1000 app && \
    chown -R app:app /app

# Switch to non-root user
USER app

# Expose port
EXPOSE 5000

# Platform-aware health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Add platform information to runtime (with default values)
ENV DOCKER_PLATFORM=${TARGETPLATFORM:-linux/amd64}
ENV DOCKER_ARCH=${TARGETARCH:-amd64}

# Start command
CMD ["python", "web_ui/start.py", "--host", "0.0.0.0", "--port", "5000", "--skip-health-check", "--production"]
