#!/bin/bash
# Simple local Docker build script (single platform)
# Use this for quick local testing without multi-platform complexity

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
IMAGE_NAME="agentic-rag"
WEBUI_IMAGE_NAME="agentic-rag-webui"
TAG="${TAG:-latest}"
PLATFORM="${PLATFORM:-linux/$(uname -m | sed 's/x86_64/amd64/' | sed 's/aarch64/arm64/')}"

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

# Check if Docker is running
check_docker() {
    log_info "Checking Docker status..."
    if ! docker info >/dev/null 2>&1; then
        log_error "Docker is not running"
        exit 1
    fi
    log_success "Docker is running"
}

# Build main application image
build_main_image() {
    log_info "Building main application image for platform: $PLATFORM"

    # Check if multi-platform build is requested
    if [[ "$PLATFORM" == *","* ]]; then
        log_info "Multi-platform build detected, using buildx..."
        if docker buildx build \
            --platform "$PLATFORM" \
            --tag "${IMAGE_NAME}:${TAG}" \
            --file Dockerfile \
            --load \
            .; then
            log_success "Main application image built successfully"
        else
            log_error "Main application image build failed"
            exit 1
        fi
    else
        log_info "Single platform build using standard docker build..."
        if docker build \
            --platform "$PLATFORM" \
            --tag "${IMAGE_NAME}:${TAG}" \
            --file Dockerfile \
            .; then
            log_success "Main application image built successfully"
        else
            log_error "Main application image build failed"
            exit 1
        fi
    fi
}

# Build Web UI image
build_webui_image() {
    log_info "Building Web UI image for platform: $PLATFORM"

    # Check if multi-platform build is requested
    if [[ "$PLATFORM" == *","* ]]; then
        log_info "Multi-platform build detected, using buildx..."
        if docker buildx build \
            --platform "$PLATFORM" \
            --tag "${WEBUI_IMAGE_NAME}:${TAG}" \
            --file web_ui/Dockerfile \
            --load \
            .; then
            log_success "Web UI image built successfully"
        else
            log_error "Web UI image build failed"
            exit 1
        fi
    else
        log_info "Single platform build using standard docker build..."
        if docker build \
            --platform "$PLATFORM" \
            --tag "${WEBUI_IMAGE_NAME}:${TAG}" \
            --file web_ui/Dockerfile \
            .; then
            log_success "Web UI image built successfully"
        else
            log_error "Web UI image build failed"
            exit 1
        fi
    fi
}

# Test built images
test_images() {
    log_info "Testing built images..."
    
    # Test main image
    log_info "Testing main application image..."
    if docker run --rm --platform "$PLATFORM" "${IMAGE_NAME}:${TAG}" python --version >/dev/null 2>&1; then
        log_success "Main image test passed"
    else
        log_error "Main image test failed"
        return 1
    fi
    
    # Test Web UI image
    log_info "Testing Web UI image..."
    if docker run --rm --platform "$PLATFORM" "${WEBUI_IMAGE_NAME}:${TAG}" python --version >/dev/null 2>&1; then
        log_success "Web UI image test passed"
    else
        log_error "Web UI image test failed"
        return 1
    fi
}

# Display usage
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -t, --tag TAG           Image tag (default: latest)"
    echo "  -p, --platform PLATFORM Target platform (default: auto-detect)"
    echo "  --main-only             Build only the main application image"
    echo "  --webui-only            Build only the Web UI image"
    echo "  --no-test               Skip image testing"
    echo "  -h, --help              Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                                    # Build both images for current platform"
    echo "  $0 --tag v1.0.0                      # Build with specific tag"
    echo "  $0 --platform linux/amd64 --main-only # Build only main image for AMD64"
}

# Parse command line arguments
BUILD_MAIN=true
BUILD_WEBUI=true
RUN_TESTS=true

while [[ $# -gt 0 ]]; do
    case $1 in
        -t|--tag)
            TAG="$2"
            shift 2
            ;;
        -p|--platform)
            PLATFORM="$2"
            shift 2
            ;;
        --main-only)
            BUILD_WEBUI=false
            shift
            ;;
        --webui-only)
            BUILD_MAIN=false
            shift
            ;;
        --no-test)
            RUN_TESTS=false
            shift
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
    log_info "Starting local Docker build"
    log_info "Configuration:"
    log_info "  Platform: $PLATFORM"
    log_info "  Tag: $TAG"
    log_info "  Build main: $BUILD_MAIN"
    log_info "  Build WebUI: $BUILD_WEBUI"
    log_info "  Run tests: $RUN_TESTS"
    
    # Check prerequisites
    check_docker
    
    # Build images
    if [ "$BUILD_MAIN" = "true" ]; then
        build_main_image
    fi
    
    if [ "$BUILD_WEBUI" = "true" ]; then
        build_webui_image
    fi
    
    # Test images
    if [ "$RUN_TESTS" = "true" ]; then
        test_images
    fi
    
    log_success "Local build completed successfully!"
    
    log_info "Built images:"
    [ "$BUILD_MAIN" = "true" ] && log_info "  ${IMAGE_NAME}:${TAG}"
    [ "$BUILD_WEBUI" = "true" ] && log_info "  ${WEBUI_IMAGE_NAME}:${TAG}"
    
    echo ""
    log_info "Next steps:"
    log_info "  1. Test with: docker run --rm ${IMAGE_NAME}:${TAG} python --version"
    log_info "  2. Deploy with: docker-compose up -d"
    log_info "  3. Access Web UI at: http://localhost:5000"
}

# Run main function
main "$@"
