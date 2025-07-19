#!/bin/bash
# Build script for functorhk/llm-entity-graph:latest
# Builds the combined WebUI + Agent image for linux/amd64

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
IMAGE_NAME="functorhk/llm-entity-graph"
TAG="latest"
PLATFORM="linux/amd64"
PUSH="${PUSH:-false}"

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

# Check Docker
check_docker() {
    log_info "Checking Docker status..."
    if ! docker info >/dev/null 2>&1; then
        log_error "Docker is not running"
        exit 1
    fi
    log_success "Docker is running"
}

# Build the combined image (WebUI + Agent)
build_combined_image() {
    log_info "Building combined WebUI + Agent image..."
    log_info "Image: ${IMAGE_NAME}:${TAG}"
    log_info "Platform: ${PLATFORM}"
    
    # Use the main Dockerfile which includes both WebUI and Agent
    local build_cmd="docker build"
    build_cmd="$build_cmd --platform ${PLATFORM}"
    build_cmd="$build_cmd --tag ${IMAGE_NAME}:${TAG}"
    build_cmd="$build_cmd --file Dockerfile"
    build_cmd="$build_cmd ."
    
    log_info "Executing: $build_cmd"
    
    if eval $build_cmd; then
        log_success "Combined image built successfully"
    else
        log_error "Build failed"
        exit 1
    fi
}

# Test the built image
test_image() {
    log_info "Testing built image..."
    
    # Test Python execution
    if docker run --rm --platform "$PLATFORM" "${IMAGE_NAME}:${TAG}" python --version >/dev/null 2>&1; then
        log_success "Image test passed - Python is working"
    else
        log_error "Image test failed - Python execution failed"
        return 1
    fi
    
    # Test platform detection
    local detected_platform=$(docker run --rm --platform "$PLATFORM" "${IMAGE_NAME}:${TAG}" uname -m 2>/dev/null || echo "unknown")
    log_info "Detected architecture: $detected_platform"
    
    # Show image info
    log_info "Image details:"
    docker images "${IMAGE_NAME}:${TAG}" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"
}

# Push to registry
push_image() {
    log_info "Pushing image to registry..."
    
    # Check if logged in
    if ! docker info 2>/dev/null | grep -q "Username:"; then
        log_warning "Not logged into Docker registry"
        log_info "Please run: docker login"
        read -p "Do you want to login now? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            docker login
        else
            log_error "Registry login required for push"
            exit 1
        fi
    fi
    
    if docker push "${IMAGE_NAME}:${TAG}"; then
        log_success "Image pushed successfully"
        log_info "Image available at: ${IMAGE_NAME}:${TAG}"
    else
        log_error "Push failed"
        exit 1
    fi
}

# Show usage
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Build functorhk/llm-entity-graph:latest for linux/amd64"
    echo "This builds the combined WebUI + Agent image"
    echo ""
    echo "Options:"
    echo "  --push          Push to registry after build"
    echo "  --no-test       Skip image testing"
    echo "  --help          Show this help"
    echo ""
    echo "Examples:"
    echo "  $0              # Build locally"
    echo "  $0 --push       # Build and push to registry"
    echo ""
    echo "Manual commands:"
    echo "  docker build --platform linux/amd64 -t functorhk/llm-entity-graph:latest ."
    echo "  docker push functorhk/llm-entity-graph:latest"
}

# Parse arguments
RUN_TESTS=true

while [[ $# -gt 0 ]]; do
    case $1 in
        --push)
            PUSH=true
            shift
            ;;
        --no-test)
            RUN_TESTS=false
            shift
            ;;
        --help|-h)
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
    log_info "Building functorhk/llm-entity-graph:latest for linux/amd64"
    log_info "This includes both WebUI and Agent in a single container"
    echo ""
    
    # Check prerequisites
    check_docker
    
    # Build the image
    build_combined_image
    
    # Test the image
    if [ "$RUN_TESTS" = "true" ]; then
        test_image
    fi
    
    # Push if requested
    if [ "$PUSH" = "true" ]; then
        push_image
    fi
    
    echo ""
    log_success "Build completed successfully!"
    echo ""
    log_info "Next steps:"
    log_info "  1. Test locally: docker run --rm -p 5000:5000 -p 8058:8058 ${IMAGE_NAME}:${TAG}"
    log_info "  2. Access Web UI: http://localhost:5000"
    log_info "  3. Access API: http://localhost:8058"
    
    if [ "$PUSH" = "true" ]; then
        echo ""
        log_info "Image is now available on Docker Hub:"
        log_info "  docker pull ${IMAGE_NAME}:${TAG}"
    fi
}

# Run main function
main "$@"
