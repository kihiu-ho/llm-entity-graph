#!/bin/bash
# Multi-platform Docker build script for Agentic RAG
# Supports both ARM64 (Apple Silicon) and AMD64 (Intel/x86) architectures

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
IMAGE_NAME="${IMAGE_NAME:-agentic-rag}"
WEBUI_IMAGE_NAME="${WEBUI_IMAGE_NAME:-agentic-rag-webui}"
TAG="${TAG:-latest}"
REGISTRY="${REGISTRY:-}"
PLATFORMS="${PLATFORMS:-linux/amd64}"
PUSH="${PUSH:-false}"
BUILD_ARGS="${BUILD_ARGS:-}"

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker buildx is available
check_buildx() {
    log_info "Checking Docker buildx availability..."
    
    if ! docker buildx version >/dev/null 2>&1; then
        log_error "Docker buildx is not available. Please install Docker Desktop or enable buildx."
        exit 1
    fi
    
    log_success "Docker buildx is available"
}

# Check registry authentication
check_registry_auth() {
    if [ "$PUSH" = "true" ] && [ -n "$REGISTRY" ]; then
        log_info "Checking registry authentication for: $REGISTRY"

        # Extract registry hostname
        local registry_host=$(echo "$REGISTRY" | sed 's|/$||' | sed 's|.*://||')

        # Try to authenticate (this will use existing credentials)
        if ! docker buildx imagetools inspect "${REGISTRY}hello-world:latest" >/dev/null 2>&1; then
            log_warning "Registry authentication may be required for: $registry_host"
            log_info "Please ensure you are logged in with: docker login $registry_host"
        else
            log_success "Registry authentication verified"
        fi
    fi
}

# Create and use buildx builder
setup_builder() {
    log_info "Setting up multi-platform builder..."

    # Create builder if it doesn't exist
    if ! docker buildx ls | grep -q "multiplatform-builder"; then
        log_info "Creating new buildx builder..."
        docker buildx create --name multiplatform-builder --driver docker-container --bootstrap
    fi

    # Use the builder
    docker buildx use multiplatform-builder

    # Inspect builder to ensure platforms are supported
    log_info "Inspecting builder capabilities..."
    docker buildx inspect --bootstrap

    log_success "Builder setup complete"
}

# Build main application image
build_main_image() {
    log_info "Building main application image for platforms: $PLATFORMS"

    local build_cmd="docker buildx build"
    build_cmd="$build_cmd --platform $PLATFORMS"
    build_cmd="$build_cmd --file Dockerfile"
    build_cmd="$build_cmd --tag ${REGISTRY}${IMAGE_NAME}:${TAG}"

    # Add build arguments
    if [ -n "$BUILD_ARGS" ]; then
        build_cmd="$build_cmd $BUILD_ARGS"
    fi

    # Handle multi-platform builds
    if [ "$PUSH" = "true" ]; then
        # Check if registry is specified for push
        if [ -z "$REGISTRY" ]; then
            log_error "Registry must be specified when pushing (use --registry option)"
            exit 1
        fi
        build_cmd="$build_cmd --push"
        log_info "Will push to registry: ${REGISTRY}"
    else
        # For local builds, check if multi-platform
        if [[ "$PLATFORMS" == *","* ]]; then
            log_warning "Multi-platform build detected. Using --output type=image,push=false for local storage"
            build_cmd="$build_cmd --output type=image,push=false"
        else
            build_cmd="$build_cmd --load"
        fi
        log_info "Will build locally"
    fi

    build_cmd="$build_cmd ."

    log_info "Executing: $build_cmd"
    eval $build_cmd

    log_success "Main application image built successfully"
}

# Build Web UI image
build_webui_image() {
    log_info "Building Web UI image for platforms: $PLATFORMS"

    local build_cmd="docker buildx build"
    build_cmd="$build_cmd --platform $PLATFORMS"
    build_cmd="$build_cmd --file web_ui/Dockerfile"
    build_cmd="$build_cmd --tag ${REGISTRY}${WEBUI_IMAGE_NAME}:${TAG}"

    # Add build arguments
    if [ -n "$BUILD_ARGS" ]; then
        build_cmd="$build_cmd $BUILD_ARGS"
    fi

    # Handle multi-platform builds
    if [ "$PUSH" = "true" ]; then
        # Check if registry is specified for push
        if [ -z "$REGISTRY" ]; then
            log_error "Registry must be specified when pushing (use --registry option)"
            exit 1
        fi
        build_cmd="$build_cmd --push"
    else
        # For local builds, check if multi-platform
        if [[ "$PLATFORMS" == *","* ]]; then
            log_warning "Multi-platform build detected. Using --output type=image,push=false for local storage"
            build_cmd="$build_cmd --output type=image,push=false"
        else
            build_cmd="$build_cmd --load"
        fi
    fi

    build_cmd="$build_cmd ."

    log_info "Executing: $build_cmd"
    eval $build_cmd

    log_success "Web UI image built successfully"
}

# Test built images
test_images() {
    if [ "$PUSH" = "true" ]; then
        log_warning "Skipping local tests because images were pushed to registry"
        return
    fi
    
    log_info "Testing built images..."
    
    # Test main image
    log_info "Testing main application image..."
    if docker run --rm --platform linux/amd64 ${REGISTRY}${IMAGE_NAME}:${TAG} python --version; then
        log_success "Main image test passed"
    else
        log_error "Main image test failed"
        return 1
    fi
    
    # Test Web UI image
    log_info "Testing Web UI image..."
    if docker run --rm --platform linux/amd64 ${REGISTRY}${WEBUI_IMAGE_NAME}:${TAG} python --version; then
        log_success "Web UI image test passed"
    else
        log_error "Web UI image test failed"
        return 1
    fi
}

# Display usage information
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -t, --tag TAG           Image tag (default: latest)"
    echo "  -r, --registry REGISTRY Registry prefix (e.g., myregistry.com/)"
    echo "  -p, --platforms PLATFORMS Comma-separated list of platforms (default: linux/amd64,linux/arm64)"
    echo "  --push                  Push images to registry after build"
    echo "  --main-only             Build only the main application image"
    echo "  --webui-only            Build only the Web UI image"
    echo "  --build-args ARGS       Additional build arguments"
    echo "  -h, --help              Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                                          # Build both images for AMD64 and ARM64"
    echo "  $0 --tag v1.0.0 --push                     # Build and push with specific tag"
    echo "  $0 --platforms linux/amd64 --main-only     # Build only main image for AMD64"
    echo "  $0 --registry myregistry.com/ --push       # Build and push to custom registry"
}

# Parse command line arguments
BUILD_MAIN=true
BUILD_WEBUI=true

while [[ $# -gt 0 ]]; do
    case $1 in
        -t|--tag)
            TAG="$2"
            shift 2
            ;;
        -r|--registry)
            REGISTRY="$2"
            if [[ ! "$REGISTRY" =~ /$ ]]; then
                REGISTRY="${REGISTRY}/"
            fi
            shift 2
            ;;
        -p|--platforms)
            PLATFORMS="$2"
            shift 2
            ;;
        --push)
            PUSH=true
            shift
            ;;
        --main-only)
            BUILD_WEBUI=false
            shift
            ;;
        --webui-only)
            BUILD_MAIN=false
            shift
            ;;
        --build-args)
            BUILD_ARGS="$2"
            shift 2
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# Main execution
main() {
    log_info "Starting multi-platform Docker build"
    log_info "Configuration:"
    log_info "  Platforms: $PLATFORMS"
    log_info "  Tag: $TAG"
    log_info "  Registry: ${REGISTRY:-<none>}"
    log_info "  Push: $PUSH"
    log_info "  Build main: $BUILD_MAIN"
    log_info "  Build WebUI: $BUILD_WEBUI"
    
    # Check prerequisites
    check_buildx
    check_registry_auth
    setup_builder
    
    # Build images
    if [ "$BUILD_MAIN" = "true" ]; then
        build_main_image
    fi
    
    if [ "$BUILD_WEBUI" = "true" ]; then
        build_webui_image
    fi
    
    # Test images
    test_images
    
    log_success "Multi-platform build completed successfully!"
    
    if [ "$PUSH" = "true" ]; then
        log_info "Images pushed to registry:"
        [ "$BUILD_MAIN" = "true" ] && log_info "  ${REGISTRY}${IMAGE_NAME}:${TAG}"
        [ "$BUILD_WEBUI" = "true" ] && log_info "  ${REGISTRY}${WEBUI_IMAGE_NAME}:${TAG}"
    else
        log_info "Images available locally:"
        [ "$BUILD_MAIN" = "true" ] && log_info "  ${REGISTRY}${IMAGE_NAME}:${TAG}"
        [ "$BUILD_WEBUI" = "true" ] && log_info "  ${REGISTRY}${WEBUI_IMAGE_NAME}:${TAG}"
    fi
}

# Run main function
main "$@"
