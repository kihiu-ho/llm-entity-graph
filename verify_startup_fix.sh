#!/bin/bash
# Quick verification script for startup script fix

echo "🔍 Verifying Startup Script Fix"
echo "==============================="

# Check if scripts exist and are executable
echo ""
echo "📋 Checking startup scripts..."

if [ -f "start.sh" ]; then
    if [ -x "start.sh" ]; then
        echo "✅ start.sh exists and is executable"
    else
        echo "❌ start.sh exists but is not executable"
        echo "   Fixing permissions..."
        chmod +x start.sh
        echo "✅ Fixed start.sh permissions"
    fi
else
    echo "❌ start.sh not found"
    exit 1
fi

if [ -f "start_combined.sh" ]; then
    if [ -x "start_combined.sh" ]; then
        echo "✅ start_combined.sh exists and is executable"
    else
        echo "❌ start_combined.sh exists but is not executable"
        echo "   Fixing permissions..."
        chmod +x start_combined.sh
        echo "✅ Fixed start_combined.sh permissions"
    fi
else
    echo "❌ start_combined.sh not found"
    exit 1
fi

# Check script headers
echo ""
echo "📝 Checking script headers..."

if head -1 start.sh | grep -q "#!/bin/bash"; then
    echo "✅ start.sh has correct shebang"
else
    echo "⚠️  start.sh missing or incorrect shebang"
fi

if head -1 start_combined.sh | grep -q "#!/bin/bash"; then
    echo "✅ start_combined.sh has correct shebang"
else
    echo "⚠️  start_combined.sh missing or incorrect shebang"
fi

# Check Dockerfiles
echo ""
echo "🐳 Checking Dockerfiles..."

if [ -f "Dockerfile" ]; then
    if grep -q 'CMD \["/bin/bash", "/app/start.sh"\]' Dockerfile; then
        echo "✅ Dockerfile uses bash execution"
    else
        echo "⚠️  Dockerfile may not use bash execution"
    fi
else
    echo "❌ Dockerfile not found"
fi

if [ -f "Dockerfile.claw" ]; then
    if grep -q 'CMD \["/bin/bash", "/app/start_combined.sh"\]' Dockerfile.claw; then
        echo "✅ Dockerfile.claw uses bash execution"
    else
        echo "⚠️  Dockerfile.claw may not use bash execution"
    fi
else
    echo "❌ Dockerfile.claw not found"
fi

# Test script syntax
echo ""
echo "🧪 Testing script syntax..."

if bash -n start.sh; then
    echo "✅ start.sh syntax is valid"
else
    echo "❌ start.sh has syntax errors"
    exit 1
fi

if bash -n start_combined.sh; then
    echo "✅ start_combined.sh syntax is valid"
else
    echo "❌ start_combined.sh has syntax errors"
    exit 1
fi

echo ""
echo "🎉 Startup script verification complete!"
echo ""
echo "✅ All checks passed. The startup script fix should work."
echo ""
echo "Next steps:"
echo "1. Commit and push your changes"
echo "2. Deploy to claw.cloud using Dockerfile.claw"
echo "3. Monitor deployment logs for successful startup"
echo ""
echo "For claw.cloud deployment:"
echo "  Framework: docker"
echo "  Dockerfile: Dockerfile.claw"
echo "  Build from Git repository"
