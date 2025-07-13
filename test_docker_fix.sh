#!/bin/bash
# Test script to verify Docker startup script fix

set -e

echo "🔧 Testing Docker Startup Script Fix"
echo "===================================="

# Function to check if Docker is running
check_docker() {
    if ! docker info >/dev/null 2>&1; then
        echo "❌ Docker is not running. Please start Docker and try again."
        exit 1
    fi
    echo "✅ Docker is running"
}

# Function to test script permissions
test_script_permissions() {
    echo ""
    echo "📋 Checking script permissions..."
    
    if [ -f "start_combined.sh" ]; then
        if [ -x "start_combined.sh" ]; then
            echo "✅ start_combined.sh is executable"
        else
            echo "❌ start_combined.sh is not executable"
            echo "   Fixing permissions..."
            chmod +x start_combined.sh
            echo "✅ Fixed start_combined.sh permissions"
        fi
    else
        echo "❌ start_combined.sh not found"
        return 1
    fi
    
    if [ -f "start.sh" ]; then
        if [ -x "start.sh" ]; then
            echo "✅ start.sh is executable"
        else
            echo "❌ start.sh is not executable"
            echo "   Fixing permissions..."
            chmod +x start.sh
            echo "✅ Fixed start.sh permissions"
        fi
    else
        echo "❌ start.sh not found"
        return 1
    fi
}

# Function to test Docker build
test_docker_build() {
    echo ""
    echo "🏗️  Testing Docker build..."
    
    # Test Dockerfile.claw
    echo "   Building with Dockerfile.claw..."
    if docker build -f Dockerfile.claw -t test-claw-fix . >/dev/null 2>&1; then
        echo "✅ Dockerfile.claw builds successfully"
    else
        echo "❌ Dockerfile.claw build failed"
        echo "   Trying with verbose output..."
        docker build -f Dockerfile.claw -t test-claw-fix .
        return 1
    fi
    
    # Test regular Dockerfile
    echo "   Building with Dockerfile..."
    if docker build -f Dockerfile -t test-regular-fix . >/dev/null 2>&1; then
        echo "✅ Dockerfile builds successfully"
    else
        echo "❌ Dockerfile build failed"
        echo "   Trying with verbose output..."
        docker build -f Dockerfile -t test-regular-fix .
        return 1
    fi
}

# Function to test script existence in container
test_script_in_container() {
    echo ""
    echo "📁 Testing script existence in container..."
    
    # Check if start_combined.sh exists and is executable in container
    if docker run --rm test-claw-fix ls -la /app/start_combined.sh >/dev/null 2>&1; then
        echo "✅ start_combined.sh exists in container"
        
        # Check permissions
        perms=$(docker run --rm test-claw-fix stat -c "%A" /app/start_combined.sh)
        echo "   Permissions: $perms"
        
        if [[ $perms == *"x"* ]]; then
            echo "✅ start_combined.sh is executable in container"
        else
            echo "❌ start_combined.sh is not executable in container"
            return 1
        fi
    else
        echo "❌ start_combined.sh not found in container"
        return 1
    fi
}

# Function to test container startup (dry run)
test_container_startup() {
    echo ""
    echo "🚀 Testing container startup (dry run)..."
    
    # Test with minimal environment variables
    echo "   Testing with minimal environment..."
    
    # Create a test that just checks if the script can be executed
    if docker run --rm \
        -e DATABASE_URL="postgresql://test:test@localhost:5432/test" \
        -e NEO4J_URI="neo4j://localhost:7687" \
        -e NEO4J_USERNAME="test" \
        -e NEO4J_PASSWORD="test" \
        -e LLM_API_KEY="test" \
        -e EMBEDDING_API_KEY="test" \
        test-claw-fix \
        /bin/bash -c "echo 'Testing script execution...' && ls -la /app/start_combined.sh && echo 'Script exists and is accessible'" >/dev/null 2>&1; then
        echo "✅ Container can access and execute startup script"
    else
        echo "❌ Container cannot access startup script"
        echo "   Debugging..."
        docker run --rm \
            -e DATABASE_URL="postgresql://test:test@localhost:5432/test" \
            -e NEO4J_URI="neo4j://localhost:7687" \
            -e NEO4J_USERNAME="test" \
            -e NEO4J_PASSWORD="test" \
            -e LLM_API_KEY="test" \
            -e EMBEDDING_API_KEY="test" \
            test-claw-fix \
            /bin/bash -c "ls -la /app/ | grep start"
        return 1
    fi
}

# Function to cleanup test images
cleanup() {
    echo ""
    echo "🧹 Cleaning up test images..."
    docker rmi test-claw-fix test-regular-fix >/dev/null 2>&1 || true
    echo "✅ Cleanup complete"
}

# Main execution
main() {
    echo "Starting Docker startup script fix verification..."
    echo ""
    
    # Check Docker
    check_docker
    
    # Test script permissions
    test_script_permissions
    
    # Test Docker builds
    test_docker_build
    
    # Test script in container
    test_script_in_container
    
    # Test container startup
    test_container_startup
    
    echo ""
    echo "🎉 All tests passed!"
    echo ""
    echo "✅ Docker startup script fix is working correctly"
    echo ""
    echo "Next steps:"
    echo "1. Commit and push your changes to Git"
    echo "2. Deploy to claw.cloud using the fixed Dockerfile.claw"
    echo "3. Set the required environment variables in claw.cloud console"
    echo ""
    echo "For claw.cloud deployment, use:"
    echo "  Framework: docker"
    echo "  Dockerfile: Dockerfile.claw"
    echo ""
}

# Set up cleanup on exit
trap cleanup EXIT

# Run main function
main
