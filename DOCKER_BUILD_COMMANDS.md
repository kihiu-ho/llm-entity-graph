# Docker Build Commands Reference

This guide provides the correct Docker build commands for different scenarios.

## 🚨 **Common Command Errors and Fixes**

### ❌ **Incorrect Commands (Don't Use These)**

```bash
# WRONG: Extra hyphen before platform list
docker build --platform -linux/amd64,linux/arm64 -t image:tag .

# WRONG: Using docker build for multi-platform (won't work properly)
docker build --platform linux/amd64,linux/arm64 -t image:tag .
```

### ✅ **Correct Commands**

```bash
# CORRECT: Single platform with docker build
docker build --platform linux/amd64 -t functorhk/llm-entity-graph:latest .

# CORRECT: Multi-platform with docker buildx
docker buildx build --platform linux/amd64,linux/arm64 -t functorhk/llm-entity-graph:latest .
```

## 🛠️ **Recommended Build Methods**

### **1. Using Build Scripts (Recommended)**

```bash
# Simple local build for current platform
./build-local.sh --tag latest

# Multi-platform build
./build-multiplatform.sh --platforms linux/amd64,linux/arm64

# Build and push to registry
./build-multiplatform.sh \
  --registry functorhk/ \
  --tag latest \
  --platforms linux/amd64,linux/arm64 \
  --push
```

### **2. Manual Docker Commands**

#### **Single Platform Builds**

```bash
# AMD64 (Intel/x86)
docker build --platform linux/amd64 -t functorhk/llm-entity-graph:latest .

# ARM64 (Apple Silicon)
docker build --platform linux/arm64 -t functorhk/llm-entity-graph:latest .

# Auto-detect current platform
docker build -t functorhk/llm-entity-graph:latest .
```

#### **Multi-Platform Builds (Requires buildx)**

```bash
# Setup buildx builder (one-time setup)
docker buildx create --name multibuilder --use
docker buildx inspect --bootstrap

# Build for multiple platforms
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  --tag functorhk/llm-entity-graph:latest \
  .

# Build and push to registry
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  --tag functorhk/llm-entity-graph:latest \
  --push \
  .

# Build and load to local Docker (single platform only)
docker buildx build \
  --platform linux/amd64 \
  --tag functorhk/llm-entity-graph:latest \
  --load \
  .
```

## 🔧 **Troubleshooting Build Issues**

### **Issue 1: Platform Syntax Error**
```bash
# Error: --platform -linux/amd64,linux/arm64
# Fix: Remove the extra hyphen
docker buildx build --platform linux/amd64,linux/arm64 -t image:tag .
```

### **Issue 2: Multi-platform with docker build**
```bash
# Error: docker build --platform linux/amd64,linux/arm64
# Fix: Use docker buildx for multi-platform
docker buildx build --platform linux/amd64,linux/arm64 -t image:tag .
```

### **Issue 3: Registry Push Access Denied**
```bash
# Fix: Login to registry first
docker login functorhk
# or for other registries
docker login registry.example.com

# Then build and push
docker buildx build --platform linux/amd64,linux/arm64 --push -t functorhk/llm-entity-graph:latest .
```

### **Issue 4: Buildx Not Available**
```bash
# Fix: Enable buildx
docker buildx install
docker buildx create --use
```

## 📋 **Command Templates**

### **For Your Specific Case (functorhk registry)**

```bash
# 1. Login to Docker Hub
docker login

# 2. Single platform build (fastest for testing)
docker build --platform linux/amd64 -t functorhk/llm-entity-graph:latest .

# 3. Multi-platform build (for production)
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  --tag functorhk/llm-entity-graph:latest \
  --push \
  .

# 4. Using our build script (recommended)
./build-multiplatform.sh \
  --registry functorhk/ \
  --tag latest \
  --platforms linux/amd64,linux/arm64 \
  --push
```

### **Web UI Image**

```bash
# Single platform
docker build --platform linux/amd64 -f web_ui/Dockerfile -t functorhk/llm-entity-graph-webui:latest .

# Multi-platform
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  --file web_ui/Dockerfile \
  --tag functorhk/llm-entity-graph-webui:latest \
  --push \
  .
```

## 🚀 **Quick Fix for Your Command**

Your original command:
```bash
docker build --platform -linux/amd64,linux/arm64 -t functorhk/llm-entity-graph:latest .
```

**Fixed version:**
```bash
# Option 1: Single platform (fastest)
docker build --platform linux/amd64 -t functorhk/llm-entity-graph:latest .

# Option 2: Multi-platform (use buildx)
docker buildx build --platform linux/amd64,linux/arm64 -t functorhk/llm-entity-graph:latest .

# Option 3: Use our script (recommended)
./build-local.sh --tag latest --platform linux/amd64
```

## 🎯 **Best Practices**

1. **For Development**: Use single platform builds (`docker build --platform linux/amd64`)
2. **For Production**: Use multi-platform builds (`docker buildx build --platform linux/amd64,linux/arm64`)
3. **For Registry Push**: Always login first (`docker login`)
4. **For Local Testing**: Use our build scripts for convenience
5. **For CI/CD**: Use buildx with explicit platform specification

## 🔍 **Verify Your Build**

```bash
# Check built images
docker images functorhk/llm-entity-graph

# Test the image
docker run --rm functorhk/llm-entity-graph:latest python --version

# Check platform
docker inspect functorhk/llm-entity-graph:latest | grep Architecture
```

Use the build scripts for the easiest experience! 🚀
