#!/bin/bash
# Redis AI Server - Service Deployment Script
# Deploys the Redis AI Server as a system service on macOS or Linux

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_NAME="redis-ai-server"
MACOS_PLIST="com.redis-ai-server.plist"
LINUX_SERVICE="redis-ai-server.service"

echo "🚀 Redis AI Server - Service Deployment"
echo "======================================"

# Detect platform
if [[ "$OSTYPE" == "darwin"* ]]; then
    PLATFORM="macOS"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    PLATFORM="Linux"
else
    echo "❌ Unsupported platform: $OSTYPE"
    exit 1
fi

echo "🔍 Detected platform: $PLATFORM"

# Check dependencies
echo "📋 Checking dependencies..."

if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed"
    exit 1
fi

if ! command -v redis-server &> /dev/null; then
    echo "❌ Redis is required but not installed"
    echo "   Install with: brew install redis (macOS) or apt-get install redis-server (Linux)"
    exit 1
fi

# Check if Redis is running
if ! redis-cli ping &> /dev/null; then
    echo "⚠️  Redis is not running, attempting to start..."
    if [[ "$PLATFORM" == "macOS" ]]; then
        brew services start redis || {
            echo "❌ Failed to start Redis. Please start manually: brew services start redis"
            exit 1
        }
    else
        sudo systemctl start redis || {
            echo "❌ Failed to start Redis. Please start manually: sudo systemctl start redis"
            exit 1
        }
    fi
    
    # Wait for Redis to start
    sleep 2
    if ! redis-cli ping &> /dev/null; then
        echo "❌ Redis failed to start"
        exit 1
    fi
fi

echo "✅ Redis is running"

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip3 install --user redis flask flask-socketio &> /dev/null || {
    echo "❌ Failed to install Python dependencies"
    exit 1
}

echo "✅ Dependencies installed"

# Create log directory
LOG_DIR="$HOME/.redis-ai-logs"
mkdir -p "$LOG_DIR"
echo "✅ Created log directory: $LOG_DIR"

# Platform-specific deployment
if [[ "$PLATFORM" == "macOS" ]]; then
    echo "🍎 Deploying macOS LaunchAgent..."
    
    # Copy plist to LaunchAgents
    cp "$SCRIPT_DIR/$MACOS_PLIST" "$HOME/Library/LaunchAgents/"
    echo "✅ Copied $MACOS_PLIST to ~/Library/LaunchAgents/"
    
    # Unload existing service if running
    launchctl unload "$HOME/Library/LaunchAgents/$MACOS_PLIST" 2>/dev/null || true
    
    # Load and start service
    launchctl load "$HOME/Library/LaunchAgents/$MACOS_PLIST"
    launchctl start com.redis-ai-server
    
    echo "✅ Redis AI Server deployed and started"
    echo "📊 Web dashboard: http://localhost:8883"
    echo "📝 Logs: $LOG_DIR/server.stdout.log"
    echo ""
    echo "Management commands:"
    echo "  Stop:    launchctl stop com.redis-ai-server"
    echo "  Start:   launchctl start com.redis-ai-server"
    echo "  Disable: launchctl unload ~/Library/LaunchAgents/$MACOS_PLIST"
    
elif [[ "$PLATFORM" == "Linux" ]]; then
    echo "🐧 Deploying Linux systemd service..."
    
    # Update paths in service file for current user
    sed "s|User=jonathanhill|User=$USER|g; s|Group=staff|Group=$USER|g; s|/Users/jonathanhill|$HOME|g" \
        "$SCRIPT_DIR/$LINUX_SERVICE" > /tmp/redis-ai-server.service
    
    # Install service file
    sudo cp /tmp/redis-ai-server.service /etc/systemd/system/
    sudo systemctl daemon-reload
    
    # Enable and start service
    sudo systemctl enable redis-ai-server
    sudo systemctl start redis-ai-server
    
    echo "✅ Redis AI Server deployed and started"
    echo "📊 Web dashboard: http://localhost:8883"
    echo "📝 Logs: journalctl -u redis-ai-server -f"
    echo ""
    echo "Management commands:"
    echo "  Status:  sudo systemctl status redis-ai-server"
    echo "  Stop:    sudo systemctl stop redis-ai-server"
    echo "  Start:   sudo systemctl start redis-ai-server"
    echo "  Disable: sudo systemctl disable redis-ai-server"
fi

# Wait a moment for service to start
sleep 3

# Test if service is running
echo "🧪 Testing service..."
if curl -s http://localhost:8883/api/status &> /dev/null; then
    echo "✅ Service is running and responding"
else
    echo "⚠️  Service may still be starting... check logs if issues persist"
fi

echo ""
echo "🎉 Deployment complete!"
echo "🌐 Open http://localhost:8883 to access the Redis AI Server dashboard"
echo "🤖 Your AI workforce is now running persistently and will survive reboots"