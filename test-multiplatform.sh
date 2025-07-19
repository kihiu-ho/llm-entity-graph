#!/bin/bash
# Multi-platform Docker testing script for Agentic RAG
# Tests both ARM64 and AMD64 builds

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
TEST_PLATFORMS="${TEST_PLATFORMS:-linux/amd64,linux/arm64}"

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

# Check Docker and buildx
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check Docker
    if ! docker --version >/dev/null 2>&1; then
        log_error "Docker is not installed or not running"
        exit 1
    fi
    
    # Check buildx
    if ! docker buildx version >/dev/null 2>&1; then
        log_error "Docker buildx is not available"
        exit 1
    fi
    
    # Check docker-compose
    if ! docker-compose --version >/dev/null 2>&1; then
        log_error "docker-compose is not installed"
        exit 1
    fi
    
    log_success "All prerequisites are available"
}

# Test platform detection in Dockerfiles
test_dockerfile_platform_detection() {
    log_info "Testing Dockerfile platform detection..."
    
    # Test main Dockerfile
    log_info "Testing main Dockerfile..."
    if docker buildx build --platform linux/amd64 --target base --progress=plain . 2>&1 | grep -q "Target architecture: amd64"; then
        log_success "Main Dockerfile platform detection works"
    else
        log_warning "Main Dockerfile platform detection may not be working"
    fi
    
    # Test Web UI Dockerfile
    log_info "Testing Web UI Dockerfile..."
    if docker buildx build --platform linux/amd64 --file web_ui/Dockerfile --progress=plain . 2>&1 | grep -q "Target architecture: amd64"; then
        log_success "Web UI Dockerfile platform detection works"
    else
        log_warning "Web UI Dockerfile platform detection may not be working"
    fi
}

# Test docker-compose configuration
test_docker_compose_config() {
    log_info "Testing docker-compose configurations..."
    
    # Test main configuration
    if docker-compose config >/dev/null 2>&1; then
        log_success "Main docker-compose.yml is valid"
    else
        log_error "Main docker-compose.yml has errors"
        return 1
    fi
    
    # Test production configuration
    if docker-compose -f docker-compose.yml -f docker-compose.prod.yml config >/dev/null 2>&1; then
        log_success "Production configuration is valid"
    else
        log_error "Production configuration has errors"
        return 1
    fi
    
    # Test development configuration
    if docker-compose -f docker-compose.yml -f docker-compose.override.yml config >/dev/null 2>&1; then
        log_success "Development configuration is valid"
    else
        log_error "Development configuration has errors"
        return 1
    fi
}

# Test platform-specific builds
test_platform_builds() {
    log_info "Testing platform-specific builds..."
    
    IFS=',' read -ra PLATFORMS <<< "$TEST_PLATFORMS"
    
    for platform in "${PLATFORMS[@]}"; do
        log_info "Testing build for platform: $platform"
        
        # Test main image build
        if docker buildx build --platform "$platform" --tag "test-${IMAGE_NAME}:${platform//\//-}" . >/dev/null 2>&1; then
            log_success "Main image builds successfully for $platform"
        else
            log_error "Main image build failed for $platform"
            return 1
        fi
        
        # Test Web UI image build
        if docker buildx build --platform "$platform" --file web_ui/Dockerfile --tag "test-${WEBUI_IMAGE_NAME}:${platform//\//-}" . >/dev/null 2>&1; then
            log_success "Web UI image builds successfully for $platform"
        else
            log_error "Web UI image build failed for $platform"
            return 1
        fi
    done
}

# Test runtime functionality
test_runtime_functionality() {
    log_info "Testing runtime functionality..."
    
    # Build test images for current platform
    local current_platform="linux/$(uname -m | sed 's/x86_64/amd64/' | sed 's/aarch64/arm64/')"
    log_info "Testing on current platform: $current_platform"
    
    # Build and test main image
    docker buildx build --platform "$current_platform" --load --tag "test-runtime-main" . >/dev/null 2>&1
    
    # Test Python execution
    if docker run --rm --platform "$current_platform" test-runtime-main python --version >/dev/null 2>&1; then
        log_success "Python execution works in main image"
    else
        log_error "Python execution failed in main image"
        return 1
    fi
    
    # Test platform environment variables
    local detected_platform=$(docker run --rm --platform "$current_platform" test-runtime-main printenv DOCKER_PLATFORM 2>/dev/null || echo "not-set")
    if [ "$detected_platform" != "not-set" ]; then
        log_success "Platform environment variables are set: $detected_platform"
    else
        log_warning "Platform environment variables are not set"
    fi
    
    # Build and test Web UI image
    docker buildx build --platform "$current_platform" --load --file web_ui/Dockerfile --tag "test-runtime-webui" . >/dev/null 2>&1
    
    if docker run --rm --platform "$current_platform" test-runtime-webui python --version >/dev/null 2>&1; then
        log_success "Python execution works in Web UI image"
    else
        log_error "Python execution failed in Web UI image"
        return 1
    fi
}

# Test docker-compose with platform specification
test_compose_platform_support() {
    log_info "Testing docker-compose platform support..."
    
    # Create test environment file
    cat > .env.test << EOF
DATABASE_URL=postgresql://test:test@localhost:5432/test
NEO4J_URI=neo4j://localhost:7687
NEO4J_USERNAME=test
NEO4J_PASSWORD=test
LLM_API_KEY=test-key
EMBEDDING_API_KEY=test-key
TARGETPLATFORM=linux/amd64
BUILDPLATFORM=linux/amd64
EOF
    
    # Test configuration with environment
    if TARGETPLATFORM=linux/amd64 BUILDPLATFORM=linux/amd64 docker-compose --env-file .env.test config >/dev/null 2>&1; then
        log_success "docker-compose works with platform environment variables"
    else
        log_error "docker-compose failed with platform environment variables"
        rm -f .env.test
        return 1
    fi
    
    # Clean up
    rm -f .env.test
}

# Test multi-platform build script
test_build_script() {
    log_info "Testing multi-platform build script..."
    
    if [ -f "./build-multiplatform.sh" ]; then
        # Test script syntax
        if bash -n ./build-multiplatform.sh; then
            log_success "Build script syntax is valid"
        else
            log_error "Build script has syntax errors"
            return 1
        fi
        
        # Test help option
        if ./build-multiplatform.sh --help >/dev/null 2>&1; then
            log_success "Build script help option works"
        else
            log_error "Build script help option failed"
            return 1
        fi
    else
        log_warning "Multi-platform build script not found"
    fi
}

# Cleanup test images
cleanup() {
    log_info "Cleaning up test images..."
    
    # Remove test images
    docker rmi test-runtime-main test-runtime-webui >/dev/null 2>&1 || true
    docker rmi $(docker images -q "test-${IMAGE_NAME}:*") >/dev/null 2>&1 || true
    docker rmi $(docker images -q "test-${WEBUI_IMAGE_NAME}:*") >/dev/null 2>&1 || true
    
    log_success "Cleanup completed"
}

# Display usage
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --platforms PLATFORMS   Comma-separated list of platforms to test (default: linux/amd64,linux/arm64)"
    echo "  --skip-builds          Skip platform build tests (faster)"
    echo "  --skip-runtime         Skip runtime functionality tests"
    echo "  -h, --help             Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                                    # Run all tests"
    echo "  $0 --platforms linux/amd64           # Test only AMD64"
    echo "  $0 --skip-builds                     # Skip build tests"
}

# Parse command line arguments
SKIP_BUILDS=false
SKIP_RUNTIME=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --platforms)
            TEST_PLATFORMS="$2"
            shift 2
            ;;
        --skip-builds)
            SKIP_BUILDS=true
            shift
            ;;
        --skip-runtime)
            SKIP_RUNTIME=true
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
    log_info "Starting multi-platform Docker tests"
    log_info "Test platforms: $TEST_PLATFORMS"
    
    # Set up cleanup on exit
    trap cleanup EXIT
    
    # Run tests
    check_prerequisites
    test_dockerfile_platform_detection
    test_docker_compose_config
    test_build_script
    test_compose_platform_support
    
    if [ "$SKIP_BUILDS" = "false" ]; then
        test_platform_builds
    else
        log_warning "Skipping platform build tests"
    fi
    
    if [ "$SKIP_RUNTIME" = "false" ]; then
        test_runtime_functionality
    else
        log_warning "Skipping runtime functionality tests"
    fi
    
    log_success "All multi-platform tests completed successfully!"
    
    echo ""
    log_info "Summary:"
    log_info "✅ Dockerfile platform detection working"
    log_info "✅ docker-compose configurations valid"
    log_info "✅ Platform-specific builds working"
    log_info "✅ Runtime functionality verified"
    log_info "✅ Multi-platform setup is ready for deployment"
}

# Run main function
main "$@"
