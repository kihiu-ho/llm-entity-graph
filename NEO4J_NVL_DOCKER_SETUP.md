# 🐳 Neo4j NVL Library Docker Setup Guide

## 📋 Overview

This guide documents the complete setup for including the Neo4j NVL library and interaction handlers in Docker deployments.

## ✅ What Was Implemented

### 1. 📦 Package Installation
- **Added**: `@neo4j-nvl/base` - Core NVL library
- **Added**: `@neo4j-nvl/interaction-handlers` - DragNodeInteraction and other handlers
- **Location**: `web_ui/package.json`

### 2. 🔧 Bundle Configuration
- **Enhanced**: `web_ui/src/nvl-bundle.js` to include all interaction handlers
- **Exposed**: All 6 interaction handlers globally:
  - `DragNodeInteraction` ✅
  - `ClickInteraction` ✅
  - `HoverInteraction` ✅
  - `ZoomInteraction` ✅
  - `PanInteraction` ✅
  - `LassoInteraction` ✅

### 3. 🐳 Docker Files Updated

#### Main Dockerfile
```dockerfile
# Install Node.js for Neo4j NVL
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    procps \
    lsof \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Build Neo4j NVL bundle
WORKDIR /app/web_ui
RUN npm install && npm run build
WORKDIR /app
```

#### Web UI Dockerfile
```dockerfile
# Install Node.js for Neo4j NVL
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Build Neo4j NVL bundle
WORKDIR /app/web_ui
RUN npm install && npm run build
WORKDIR /app
```

#### Dockerfile.claw (Claw Cloud Optimized)
```dockerfile
# Optimized for Claw Cloud with Neo4j NVL
FROM python:3.11-slim

# Install Node.js for Neo4j NVL
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Build Neo4j NVL bundle
WORKDIR /app/web_ui
RUN npm install && npm run build

# Verify bundle creation
RUN ls -la static/js/dist/ && \
    echo "Neo4j NVL bundle size:" && \
    du -h static/js/dist/nvl.bundle.js
```

#### Dockerfile.combined (API + Web UI)
```dockerfile
# Combined deployment with Neo4j NVL
# Same Node.js installation and build steps
# Supports both API (port 8058) and Web UI (port 5000)
```

### 4. 🐙 Docker Compose Files

#### docker-compose.yml (Updated)
```yaml
agentic-rag-combined:
  build:
    context: .
    dockerfile: Dockerfile.combined  # Uses combined Dockerfile
```

#### docker-compose.claw.yml (New)
```yaml
# Claw Cloud specific deployment
web-ui:
  build:
    dockerfile: Dockerfile.claw
  ports:
    - "5000:5000"

combined:
  build:
    dockerfile: Dockerfile.combined
  ports:
    - "5000:5000"  # Web UI
    - "8058:8058"  # API
```

## 🚀 Build Process

### Local Development
```bash
# Install dependencies
cd web_ui
npm install

# Build NVL bundle
npm run build

# Verify bundle
ls -la static/js/dist/nvl.bundle.js
```

### Docker Build
```bash
# Build with Neo4j NVL library
docker build -f Dockerfile.claw -t agentic-rag-webui .

# Or use docker-compose
docker-compose -f docker-compose.claw.yml build
```

### Claw Cloud Deployment
```bash
# Deploy web UI only
docker-compose -f docker-compose.claw.yml up web-ui

# Deploy combined API + Web UI
docker-compose -f docker-compose.claw.yml --profile combined up
```

## ✅ Verification Steps

### 1. Bundle Creation
```bash
# Check if bundle exists and has reasonable size
ls -la web_ui/static/js/dist/nvl.bundle.js
du -h web_ui/static/js/dist/nvl.bundle.js
```

### 2. Interaction Handlers Available
Check browser console for:
```
✅ Neo4j NVL library and interaction handlers loaded and bundled successfully
🎮 DragNodeInteraction available: function
🎮 ClickInteraction available: function
🎮 HoverInteraction available: function
🎮 ZoomInteraction available: function
🎮 PanInteraction available: function
🎮 LassoInteraction available: function
```

### 3. DragNodeInteraction Working
Check browser console for:
```
✅ Drag node interaction enabled
🎯 Started dragging nodes: [...]
🎯 Dragged nodes: [...]
🎯 Finished dragging nodes: [...]
```

## 📁 File Structure

```
├── Dockerfile                    # Updated with Node.js
├── Dockerfile.claw              # Claw Cloud optimized
├── Dockerfile.combined          # API + Web UI
├── docker-compose.yml           # Updated to use combined
├── docker-compose.claw.yml      # Claw Cloud specific
├── web_ui/
│   ├── package.json             # Neo4j NVL dependencies
│   ├── webpack.config.js        # Bundle configuration
│   ├── src/
│   │   └── nvl-bundle.js        # Enhanced with interaction handlers
│   └── static/js/
│       ├── dist/
│       │   └── nvl.bundle.js    # Built bundle (auto-generated)
│       └── neo4j-graph-visualization.js  # Uses DragNodeInteraction
```

## 🔧 Environment Variables

All Docker files support these environment variables:
- `FLASK_ENV=production`
- `PYTHONUNBUFFERED=1`
- `WEB_UI_HOST=0.0.0.0`
- `WEB_UI_PORT=5000`
- Database and LLM configuration variables

## 🎯 Key Benefits

1. **✅ Complete DragNodeInteraction**: Full Neo4j NVL drag functionality
2. **✅ All 6 Interaction Handlers**: Comprehensive interaction support
3. **✅ Optimized Builds**: Separate Dockerfiles for different deployment scenarios
4. **✅ Claw Cloud Ready**: Optimized Dockerfile.claw for cloud deployment
5. **✅ Verification Steps**: Built-in bundle verification during Docker build
6. **✅ Multi-Platform**: Support for AMD64 and ARM64 architectures

## 🚨 Important Notes

- **Bundle Size**: The NVL bundle increases from ~1.71 MiB to 1.74 MiB with interaction handlers
- **Build Time**: Docker builds take longer due to npm install and webpack build
- **Node.js Required**: All Docker images now include Node.js for the build process
- **Verification**: Bundle creation is verified during Docker build to catch issues early

## 🔄 Deployment Options

1. **Web UI Only**: Use `Dockerfile.claw` for lightweight web UI deployment
2. **Combined**: Use `Dockerfile.combined` for API + Web UI in one container
3. **Local Development**: Use updated `Dockerfile` for local testing
4. **Claw Cloud**: Use `docker-compose.claw.yml` for cloud deployment
