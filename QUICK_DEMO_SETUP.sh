#!/bin/bash
# Redis AI Challenge - Quick Demo Setup
# Get running in under 2 minutes!

SCRIPT_DIR=$(dirname "$0")

echo "🚀 Redis AI Challenge - Quick Demo Setup"
echo "========================================"

# Check if Redis is installed
if ! command -v redis-server &> /dev/null; then
    echo "❌ Redis not found. Installing..."
    
    # Detect OS and install Redis
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        if command -v brew &> /dev/null; then
            brew install redis
        else
            echo "❌ Please install Homebrew first: /bin/bash -c \"\
$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
            exit 1
        fi
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        sudo apt update && sudo apt install -y redis-server
    else
        echo "❌ Unsupported OS. Please install Redis manually."
        exit 1
    fi
else
    echo "✅ Redis already installed"
fi

# Check if Redis is running
if ! redis-cli ping &> /dev/null; then
    echo "🔄 Starting Redis server..."
    
    # Start Redis in background
    if [[ "$OSTYPE" == "darwin"* ]]; then
        brew services start redis
    else
        sudo systemctl start redis
    fi
    
    # Wait for Redis to start
    sleep 2
    
    if redis-cli ping &> /dev/null; then
        echo "✅ Redis server started successfully"
    else
        echo "❌ Failed to start Redis. Try manually: redis-server"
        exit 1
    fi
else
    echo "✅ Redis server already running"
fi

# Create and activate virtual environment
echo "🐍 Creating Python virtual environment in $SCRIPT_DIR/venv..."
python3 -m venv "$SCRIPT_DIR/venv"
source "$SCRIPT_DIR/venv/bin/activate"

# Install Python dependencies
echo "📦 Installing Python dependencies..."
python3 -m pip install redis requests

# Verify installation
echo "🔍 Verifying setup..."
if python3 -c "import redis; r=redis.Redis(); r.ping()" 2>/dev/null; then
    echo "✅ Python Redis client working"
else
    echo "❌ Python Redis client not working. Try: pip install redis"
    exit 1
fi


echo ""
echo "🎉 Setup complete! Ready to run the demo:"
echo ""
echo "   source $SCRIPT_DIR/venv/bin/activate"
echo "   python3 $SCRIPT_DIR/standalone_redis_ai_demo.py"

echo ""
echo "🔍 After running, explore the data with:"
echo "   redis-cli KEYS '* ' "
echo "   redis-cli HGETALL redis_ai_challenge:final_report"


echo ""
echo "🚀 Redis AI Challenge demo ready to go!"
