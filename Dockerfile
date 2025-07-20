# Multi-platform Dockerfile for Agentic RAG with Web UI
# Supports both ARM64 (Apple Silicon) and AMD64 (Intel/x86) architectures

# Use build arguments for platform detection
ARG TARGETPLATFORM
ARG BUILDPLATFORM
ARG TARGETOS
ARG TARGETARCH

# Base stage with platform-aware optimizations
FROM python:3.11-slim AS base

# Print build information for debugging
RUN echo "Building for platform: $TARGETPLATFORM" && \
    echo "Build platform: $BUILDPLATFORM" && \
    echo "Target OS: $TARGETOS" && \
    echo "Target architecture: $TARGETARCH"

# Set working directory
WORKDIR /app

# Install system dependencies with platform-specific optimizations
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    procps \
    lsof \
    nodejs \
    npm \
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

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy web UI requirements and install
COPY web_ui/requirements.txt web_ui_requirements.txt
RUN pip install --no-cache-dir -r web_ui_requirements.txt

# Copy application code
COPY . .

# Build Neo4j NVL bundle for web UI
WORKDIR /app/web_ui
RUN npm install && npm run build

# Return to app directory
WORKDIR /app

# Fix line endings and ensure startup script exists and is executable
# Handle both Unix and Windows line endings
RUN sed -i 's/\r$//' /app/start.sh && \
    ls -la /app/start.sh && \
    chmod +x /app/start.sh

# Create non-root user for security (platform-agnostic)
RUN useradd --create-home --shell /bin/bash --uid 1000 app && \
    chown -R app:app /app

# Switch to non-root user
USER app

# Expose ports
EXPOSE 5000 8058

# Platform-aware health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Add platform information to runtime (with default values)
ENV DOCKER_PLATFORM=${TARGETPLATFORM:-linux/amd64}
ENV DOCKER_ARCH=${TARGETARCH:-amd64}

# Start both services using bash explicitly
CMD ["/bin/bash", "/app/start.sh"]
