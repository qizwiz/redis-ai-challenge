#!/bin/bash
# Setup script for AI-Emacs Integration Demo

echo "🚀 Setting up AI-Emacs Integration Demo..."

# Check if Redis is installed
if ! command -v redis-server &> /dev/null; then
    echo "❌ Redis not found. Installing Redis..."
    
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        if command -v brew &> /dev/null; then
            brew install redis
        else
            echo "Please install Homebrew first: https://brew.sh"
            exit 1
        fi
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        sudo apt-get update
        sudo apt-get install -y redis-server
    else
        echo "Please install Redis manually for your platform"
        exit 1
    fi
fi

echo "✅ Redis installation verified"

# Start Redis if not running
if ! pgrep -x "redis-server" > /dev/null; then
    echo "🔧 Starting Redis server..."
    
    if [[ "$OSTYPE" == "darwin"* ]]; then
        brew services start redis
    else
        sudo systemctl start redis-server
    fi
    
    sleep 2
fi

# Test Redis connection
if redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis server is running"
else
    echo "❌ Could not connect to Redis. Please check Redis installation."
    exit 1
fi

# Check Python packages
echo "📦 Checking Python dependencies..."

python3 -c "import redis, asyncio, json" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ Python dependencies satisfied"
else
    echo "🔧 Installing Python dependencies..."
    pip3 install redis asyncio
fi

# Check if Emacs is available
if command -v emacs &> /dev/null; then
    echo "✅ Emacs found"
    
    # Check if emacsclient is available
    if command -v emacsclient &> /dev/null; then
        echo "✅ emacsclient found"
        
        # Test if Emacs server is running
        if emacsclient --eval "(+ 1 1)" &> /dev/null; then
            echo "✅ Emacs server is running"
        else
            echo "⚠️  Emacs server not running. To enable full Emacs integration:"
            echo "   1. Start Emacs server: emacs --daemon"
            echo "   2. Or run in Emacs: M-x server-start"
        fi
    else
        echo "⚠️  emacsclient not found in PATH"
    fi
else
    echo "⚠️  Emacs not found. Core demo will work, but Emacs integration will be limited."
fi

echo ""
echo "🎯 Setup complete! Ready to run AI-Emacs Integration Demo"
echo ""
echo "Run the demo:"
echo "  python3 ai_emacs_integration_demo.py           # Full automatic demo"
echo "  python3 ai_emacs_integration_demo.py --interactive  # Step-by-step demo"
echo ""
echo "For Emacs integration:"
echo "  1. Load ai-workspace.el in Emacs: (load-file \"ai-workspace.el\")"
echo "  2. Create AI workspace: M-x ai-workspace-create"
echo ""