# Multi-Platform Docker Guide

This guide covers building and deploying the Agentic RAG system with support for both ARM64 (Apple Silicon) and AMD64 (Intel/x86) architectures.

## 🏗️ Architecture Support

The system now supports:

- **AMD64 (x86_64)**: Intel/AMD processors, most cloud providers
- **ARM64 (aarch64)**: Apple Silicon (M1/M2/M3), ARM-based servers, AWS Graviton

## 🚀 Quick Start

### Prerequisites

- Docker Desktop 4.0+ with buildx enabled
- docker-compose 2.0+
- At least 4GB RAM available for Docker

### Basic Multi-Platform Build

```bash
# Build for both platforms
./build-multiplatform.sh

# Build for specific platform only
./build-multiplatform.sh --platforms linux/amd64

# Build and push to registry
./build-multiplatform.sh --tag v1.0.0 --registry myregistry.com/ --push
```

### Quick Deployment

```bash
# Development (auto-detects platform)
docker-compose up -d

# Production with platform specification
TARGETPLATFORM=linux/amd64 docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## 🔧 Multi-Platform Features

### Dockerfile Enhancements

Both `Dockerfile` and `web_ui/Dockerfile` now include:

```dockerfile
# Platform detection
ARG TARGETPLATFORM
ARG BUILDPLATFORM
ARG TARGETOS
ARG TARGETARCH

# Platform-specific optimizations
RUN if [ "$TARGETARCH" = "arm64" ]; then \
        echo "Configuring for ARM64..."; \
    elif [ "$TARGETARCH" = "amd64" ]; then \
        echo "Configuring for AMD64..."; \
    fi

# Runtime platform information
ENV DOCKER_PLATFORM=$TARGETPLATFORM
ENV DOCKER_ARCH=$TARGETARCH
```

### Docker Compose Platform Support

```yaml
services:
  agentic-rag-combined:
    build:
      platforms:
        - linux/amd64
        - linux/arm64
      args:
        - BUILDPLATFORM=${BUILDPLATFORM:-linux/amd64}
        - TARGETPLATFORM=${TARGETPLATFORM:-linux/amd64}
```

## 🛠️ Build Scripts

### Multi-Platform Build Script

The `build-multiplatform.sh` script provides comprehensive build automation:

```bash
# Basic usage
./build-multiplatform.sh

# Advanced usage
./build-multiplatform.sh \
  --tag v1.0.0 \
  --registry myregistry.com/ \
  --platforms linux/amd64,linux/arm64 \
  --push

# Build only specific components
./build-multiplatform.sh --main-only
./build-multiplatform.sh --webui-only
```

**Options:**
- `--tag TAG`: Image tag (default: latest)
- `--registry REGISTRY`: Registry prefix
- `--platforms PLATFORMS`: Target platforms
- `--push`: Push to registry after build
- `--main-only`: Build only main application
- `--webui-only`: Build only Web UI
- `--build-args ARGS`: Additional build arguments

### Testing Script

The `test-multiplatform.sh` script validates multi-platform functionality:

```bash
# Run all tests
./test-multiplatform.sh

# Test specific platforms
./test-multiplatform.sh --platforms linux/amd64

# Skip time-consuming tests
./test-multiplatform.sh --skip-builds --skip-runtime
```

## 🌐 Deployment Scenarios

### 1. Local Development (Auto-Platform)

```bash
# Automatically uses your machine's architecture
docker-compose up -d
```

### 2. Production Deployment (Specific Platform)

```bash
# Force AMD64 for cloud deployment
export TARGETPLATFORM=linux/amd64
export BUILDPLATFORM=linux/amd64
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### 3. Apple Silicon Development

```bash
# Optimized for ARM64
export TARGETPLATFORM=linux/arm64
export BUILDPLATFORM=linux/arm64
docker-compose up -d
```

### 4. Multi-Platform Registry Push

```bash
# Build and push both architectures
./build-multiplatform.sh \
  --registry myregistry.com/ \
  --tag v1.0.0 \
  --push
```

## 🔍 Platform Detection

### Runtime Platform Information

The containers expose platform information via environment variables:

```bash
# Check platform in running container
docker exec <container> printenv DOCKER_PLATFORM
docker exec <container> printenv DOCKER_ARCH

# Check architecture
docker exec <container> uname -m
```

### Build-Time Platform Detection

During build, the Dockerfiles automatically detect and log:

```
Building for platform: linux/arm64
Build platform: linux/amd64
Target OS: linux
Target architecture: arm64
```

## ⚡ Performance Optimizations

### Platform-Specific Optimizations

The Dockerfiles include platform-aware optimizations:

```dockerfile
# ARM64 optimizations
RUN if [ "$TARGETARCH" = "arm64" ]; then \
        export OMP_NUM_THREADS=8; \
        export OPENBLAS_NUM_THREADS=8; \
    fi

# AMD64 optimizations
RUN if [ "$TARGETARCH" = "amd64" ]; then \
        export OMP_NUM_THREADS=4; \
        export OPENBLAS_NUM_THREADS=4; \
    fi
```

### Resource Limits by Platform

Production configuration includes platform-aware resource limits:

```yaml
deploy:
  resources:
    limits:
      cpus: '4.0'      # Adjust based on platform capabilities
      memory: 8G       # ARM64 may need different limits
```

## 🧪 Testing Multi-Platform Builds

### Automated Testing

```bash
# Comprehensive test suite
./test-multiplatform.sh

# Test specific aspects
./test-multiplatform.sh --skip-builds  # Skip build tests
./test-multiplatform.sh --platforms linux/amd64  # Test single platform
```

### Manual Testing

```bash
# Test AMD64 build
docker buildx build --platform linux/amd64 --tag test-amd64 .
docker run --rm --platform linux/amd64 test-amd64 python --version

# Test ARM64 build
docker buildx build --platform linux/arm64 --tag test-arm64 .
docker run --rm --platform linux/arm64 test-arm64 python --version
```

## 🚨 Troubleshooting

### Common Issues

1. **Buildx Not Available**
   ```bash
   # Enable buildx
   docker buildx install
   docker buildx create --use
   ```

2. **Platform Emulation Slow**
   ```bash
   # Use native platform for development
   export TARGETPLATFORM=linux/$(uname -m | sed 's/x86_64/amd64/' | sed 's/aarch64/arm64/')
   ```

3. **Registry Push Fails**
   ```bash
   # Login to registry first
   docker login myregistry.com
   ```

4. **Memory Issues on ARM64**
   ```bash
   # Increase Docker memory limit
   # Docker Desktop > Settings > Resources > Memory
   ```

### Debug Commands

```bash
# Check buildx status
docker buildx ls

# Inspect builder capabilities
docker buildx inspect

# Check platform support
docker buildx inspect --bootstrap

# View build logs
docker buildx build --progress=plain --platform linux/arm64 .
```

## 📊 Platform Comparison

| Feature | AMD64 | ARM64 |
|---------|-------|-------|
| Build Speed | Fast | Moderate (emulated) |
| Runtime Performance | Excellent | Excellent (native) |
| Memory Usage | Standard | Potentially lower |
| Cloud Support | Universal | Growing (AWS Graviton, etc.) |
| Development | Standard | Optimized for Apple Silicon |

## 🔄 CI/CD Integration

### GitHub Actions Example

```yaml
- name: Set up Docker Buildx
  uses: docker/setup-buildx-action@v2

- name: Build multi-platform
  run: |
    ./build-multiplatform.sh \
      --platforms linux/amd64,linux/arm64 \
      --tag ${{ github.sha }} \
      --registry ghcr.io/${{ github.repository }}/ \
      --push
```

### GitLab CI Example

```yaml
build-multiplatform:
  script:
    - docker buildx create --use
    - ./build-multiplatform.sh --platforms linux/amd64,linux/arm64 --push
```

## 📈 Best Practices

1. **Use Native Platform for Development**: Faster builds and testing
2. **Multi-Platform for Production**: Ensures compatibility across environments
3. **Test Both Platforms**: Use automated testing scripts
4. **Monitor Resource Usage**: ARM64 may have different resource patterns
5. **Cache Build Layers**: Use registry cache for faster multi-platform builds

The multi-platform setup ensures your Agentic RAG system runs optimally on any architecture! 🚀
