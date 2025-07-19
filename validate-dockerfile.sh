#!/bin/bash
# Dockerfile validation script to check for warnings and best practices

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Check Dockerfile syntax and warnings
check_dockerfile() {
    local dockerfile="$1"
    local name="$2"
    
    log_info "Checking $name ($dockerfile)..."
    
    # Check if file exists
    if [ ! -f "$dockerfile" ]; then
        log_error "$dockerfile not found"
        return 1
    fi
    
    # Use docker buildx to check for warnings
    log_info "Building $name to check for warnings..."
    local build_output
    build_output=$(docker buildx build --file "$dockerfile" --platform linux/amd64 --progress=plain . 2>&1 || true)
    
    # Check for specific warnings
    local warnings_found=0
    
    # Check for FromAsCasing warning
    if echo "$build_output" | grep -q "FromAsCasing"; then
        log_warning "FromAsCasing warning found in $name"
        echo "$build_output" | grep "FromAsCasing"
        warnings_found=$((warnings_found + 1))
    fi
    
    # Check for UndefinedVar warning
    if echo "$build_output" | grep -q "UndefinedVar"; then
        log_warning "UndefinedVar warning found in $name"
        echo "$build_output" | grep "UndefinedVar"
        warnings_found=$((warnings_found + 1))
    fi
    
    # Check for other common warnings
    if echo "$build_output" | grep -q "warning"; then
        log_warning "Other warnings found in $name"
        echo "$build_output" | grep -i "warning"
        warnings_found=$((warnings_found + 1))
    fi
    
    if [ $warnings_found -eq 0 ]; then
        log_success "$name passed validation with no warnings"
    else
        log_warning "$name has $warnings_found warning(s)"
    fi
    
    return $warnings_found
}

# Check for best practices
check_best_practices() {
    local dockerfile="$1"
    local name="$2"
    
    log_info "Checking best practices for $name..."
    
    local issues=0
    
    # Check for FROM AS casing consistency
    if grep -q "FROM.*as" "$dockerfile" && grep -q "FROM.*AS" "$dockerfile"; then
        log_warning "$name: Inconsistent FROM AS casing"
        issues=$((issues + 1))
    fi
    
    # Check for undefined variables in ENV
    if grep -E "ENV.*\$[A-Z_]+" "$dockerfile" | grep -v "\${.*:-"; then
        log_warning "$name: ENV variables without default values found"
        grep -E "ENV.*\$[A-Z_]+" "$dockerfile" | grep -v "\${.*:-"
        issues=$((issues + 1))
    fi
    
    # Check for COPY before USER
    local user_line=$(grep -n "^USER" "$dockerfile" | head -1 | cut -d: -f1)
    local copy_line=$(grep -n "^COPY.*\." "$dockerfile" | tail -1 | cut -d: -f1)
    
    if [ -n "$user_line" ] && [ -n "$copy_line" ] && [ "$copy_line" -gt "$user_line" ]; then
        log_warning "$name: COPY after USER directive may cause permission issues"
        issues=$((issues + 1))
    fi
    
    # Check for missing .dockerignore
    if [ ! -f ".dockerignore" ]; then
        log_warning "Missing .dockerignore file"
        issues=$((issues + 1))
    fi
    
    if [ $issues -eq 0 ]; then
        log_success "$name follows best practices"
    else
        log_warning "$name has $issues best practice issue(s)"
    fi
    
    return $issues
}

# Create .dockerignore if missing
create_dockerignore() {
    if [ ! -f ".dockerignore" ]; then
        log_info "Creating .dockerignore file..."
        cat > .dockerignore << 'EOF'
# Git
.git
.gitignore

# Python
__pycache__
*.pyc
*.pyo
*.pyd
.Python
env
pip-log.txt
pip-delete-this-directory.txt
.tox
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
*.log
.git
.mypy_cache
.pytest_cache
.hypothesis

# Virtual environments
venv/
env/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Documentation
*.md
docs/

# Tests
tests/
test_*.py
*_test.py

# Development files
docker-compose.override.yml
.env.local
.env.development

# Build artifacts
build/
dist/
*.egg-info/

# Logs
logs/
*.log

# Node modules (if any)
node_modules/
npm-debug.log*

# Temporary files
tmp/
temp/
EOF
        log_success "Created .dockerignore file"
    fi
}

# Main validation function
main() {
    log_info "Starting Dockerfile validation..."
    
    local total_warnings=0
    local total_issues=0
    
    # Create .dockerignore if missing
    create_dockerignore
    
    # Check main Dockerfile
    if check_dockerfile "Dockerfile" "Main Dockerfile"; then
        total_warnings=$((total_warnings + $?))
    fi
    
    if check_best_practices "Dockerfile" "Main Dockerfile"; then
        total_issues=$((total_issues + $?))
    fi
    
    # Check Web UI Dockerfile
    if check_dockerfile "web_ui/Dockerfile" "Web UI Dockerfile"; then
        total_warnings=$((total_warnings + $?))
    fi
    
    if check_best_practices "web_ui/Dockerfile" "Web UI Dockerfile"; then
        total_issues=$((total_issues + $?))
    fi
    
    echo ""
    log_info "Validation Summary:"
    log_info "  Total warnings: $total_warnings"
    log_info "  Total best practice issues: $total_issues"
    
    if [ $total_warnings -eq 0 ] && [ $total_issues -eq 0 ]; then
        log_success "All Dockerfiles passed validation!"
        return 0
    else
        log_warning "Validation completed with issues"
        return 1
    fi
}

# Display usage
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --fix-dockerignore      Create .dockerignore if missing"
    echo "  -h, --help              Show this help message"
    echo ""
    echo "This script validates Dockerfiles for:"
    echo "  - Docker build warnings"
    echo "  - Best practice compliance"
    echo "  - Common issues"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --fix-dockerignore)
            create_dockerignore
            exit 0
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

# Run main function
main "$@"
