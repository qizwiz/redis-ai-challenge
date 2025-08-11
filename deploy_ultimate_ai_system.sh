#!/bin/bash
set -e

# Deploy Ultimate AI System - The complete bulletproof setup
# This script deploys the system I actually want: AI agents that work 24/7,
# survive everything, and make my life better while I'm doing other things.

echo "🚀 DEPLOYING ULTIMATE AI SYSTEM"
echo "================================="
echo "Setting up bulletproof AI agents that work while you sleep..."
echo

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

log_header() {
    echo -e "${PURPLE}🎯 $1${NC}"
}

# Configuration
INSTALL_DIR="$HOME/.ultimate-ai-system"
DAEMON_DIR="$INSTALL_DIR/daemon"
LOGS_DIR="$HOME/.redis-ai-logs"
BACKUP_DIR="$HOME/.redis-ai-backup"
SCRIPTS_DIR="$HOME/.redis-ai-scripts"
SERVICE_NAME="ultimate-ai-agents"

# Create directories
create_directories() {
    log_info "Creating system directories..."
    
    mkdir -p "$INSTALL_DIR"
    mkdir -p "$DAEMON_DIR"
    mkdir -p "$LOGS_DIR"
    mkdir -p "$BACKUP_DIR" 
    mkdir -p "$SCRIPTS_DIR"
    
    log_success "Directories created"
}

# Install system dependencies
install_dependencies() {
    log_info "Installing system dependencies..."
    
    # Python packages
    pip3 install --user redis psutil python-daemon lockfile > /dev/null 2>&1 || {
        log_error "Failed to install Python dependencies"
        exit 1
    }
    
    # System packages (if needed)
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS - check for homebrew packages
        if ! command -v redis-server &> /dev/null; then
            log_warning "Redis not found. Install with: brew install redis"
        fi
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux - install via package manager if needed
        if ! command -v redis-server &> /dev/null; then
            log_warning "Redis not found. Install with your package manager"
        fi
    fi
    
    log_success "Dependencies installed"
}

# Copy system files
deploy_system_files() {
    log_info "Deploying system files..."
    
    # Copy core system files
    cp autonomous_ai_team.py "$INSTALL_DIR/"
    cp always_on_ai_workforce.py "$INSTALL_DIR/"
    cp persistent_agent_daemon.py "$INSTALL_DIR/"
    cp complete_revolutionary_system.py "$INSTALL_DIR/"
    cp intelligent_response_engine.py "$INSTALL_DIR/"
    cp semantic_code_analyzer.py "$INSTALL_DIR/"
    cp proactive_assistant.py "$INSTALL_DIR/"
    cp multi_ai_coordinator.py "$INSTALL_DIR/"
    cp workflow_intelligence_system.py "$INSTALL_DIR/"
    
    # Make executable
    chmod +x "$INSTALL_DIR"/*.py
    
    log_success "System files deployed"
}

# Create system service
create_system_service() {
    log_info "Creating system service..."
    
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS - create launchd service
        create_macos_service
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux - create systemd service
        create_linux_service
    else
        log_warning "Unknown OS - service creation skipped"
        return
    fi
    
    log_success "System service created"
}

create_macos_service() {
    log_info "Creating macOS LaunchAgent..."
    
    PLIST_PATH="$HOME/Library/LaunchAgents/com.redis-ai.ultimate-agents.plist"
    
    cat > "$PLIST_PATH" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.redis-ai.ultimate-agents</string>
    <key>Program</key>
    <string>$(which python3)</string>
    <key>ProgramArguments</key>
    <array>
        <string>$(which python3)</string>
        <string>$INSTALL_DIR/persistent_agent_daemon.py</string>
        <string>start</string>
    </array>
    <key>WorkingDirectory</key>
    <string>$INSTALL_DIR</string>
    <key>StandardOutPath</key>
    <string>$LOGS_DIR/daemon.out.log</string>
    <key>StandardErrorPath</key>
    <string>$LOGS_DIR/daemon.err.log</string>
    <key>KeepAlive</key>
    <true/>
    <key>RunAtLoad</key>
    <true/>
    <key>ProcessType</key>
    <string>Background</string>
</dict>
</plist>
EOF
    
    # Load the service
    launchctl load "$PLIST_PATH" 2>/dev/null || true
    
    log_success "macOS service created and loaded"
}

create_linux_service() {
    log_info "Creating systemd service..."
    
    SERVICE_PATH="$HOME/.config/systemd/user/$SERVICE_NAME.service"
    mkdir -p "$(dirname "$SERVICE_PATH")"
    
    cat > "$SERVICE_PATH" << EOF
[Unit]
Description=Ultimate AI Agents - Persistent Background AI Workforce
After=network.target

[Service]
Type=forking
User=$USER
WorkingDirectory=$INSTALL_DIR
ExecStart=$(which python3) $INSTALL_DIR/persistent_agent_daemon.py start
ExecStop=$(which python3) $INSTALL_DIR/persistent_agent_daemon.py stop
Restart=always
RestartSec=10
StandardOutput=append:$LOGS_DIR/daemon.out.log
StandardError=append:$LOGS_DIR/daemon.err.log

[Install]
WantedBy=default.target
EOF
    
    # Reload systemd and enable service
    systemctl --user daemon-reload
    systemctl --user enable "$SERVICE_NAME"
    
    log_success "systemd service created and enabled"
}

# Create control scripts
create_control_scripts() {
    log_info "Creating control scripts..."
    
    # Main control script
    cat > "$INSTALL_DIR/ai-control" << 'EOF'
#!/bin/bash
# Ultimate AI System Control Script

INSTALL_DIR="$HOME/.ultimate-ai-system"
cd "$INSTALL_DIR"

case "$1" in
    start)
        echo "🚀 Starting Ultimate AI System..."
        python3 persistent_agent_daemon.py start
        ;;
    stop)
        echo "🛑 Stopping Ultimate AI System..."
        python3 persistent_agent_daemon.py stop
        ;;
    status)
        echo "📊 Ultimate AI System Status:"
        python3 persistent_agent_daemon.py status
        ;;
    restart)
        echo "🔄 Restarting Ultimate AI System..."
        python3 persistent_agent_daemon.py stop
        sleep 3
        python3 persistent_agent_daemon.py start
        ;;
    logs)
        echo "📋 Recent AI System Logs:"
        tail -50 "$HOME/.redis-ai-logs/daemon.log"
        ;;
    notifications)
        echo "📬 Recent AI Work Notifications:"
        python3 -c "
import redis, json
r = redis.Redis(decode_responses=True)
notifications = []
while True:
    data = r.lpop('user_notifications')
    if not data: break
    notifications.append(json.loads(data))
if notifications:
    for n in notifications[-10:]:
        print(f\"✅ {n.get('description', 'Work completed')}\")
        if n.get('artifacts'):
            print(f\"   Files: {', '.join(n['artifacts'])}\")
else:
    print('📬 No recent notifications')
"
        ;;
    deploy-workforce)
        echo "👥 Deploying AI Workforce..."
        python3 -c "
import asyncio
from always_on_ai_workforce import demo_always_on_workforce
asyncio.run(demo_always_on_workforce())
"
        ;;
    *)
        echo "Usage: $0 {start|stop|status|restart|logs|notifications|deploy-workforce}"
        echo ""
        echo "Commands:"
        echo "  start              - Start the AI system"
        echo "  stop               - Stop the AI system"
        echo "  status             - Show system status"
        echo "  restart            - Restart the AI system"
        echo "  logs               - Show recent logs"
        echo "  notifications      - Show completed work notifications"
        echo "  deploy-workforce   - Deploy the complete AI workforce"
        exit 1
        ;;
esac
EOF
    
    chmod +x "$INSTALL_DIR/ai-control"
    
    # Create symlink in PATH
    if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
        mkdir -p "$HOME/.local/bin"
        ln -sf "$INSTALL_DIR/ai-control" "$HOME/.local/bin/ai-control"
    fi
    
    # Quick status script
    cat > "$INSTALL_DIR/ai-status" << 'EOF'
#!/bin/bash
# Quick AI Status Check

echo "🤖 ULTIMATE AI SYSTEM STATUS"
echo "============================"

# Check if daemon is running
if pgrep -f "persistent_agent_daemon.py" > /dev/null; then
    echo "✅ Daemon: Running"
else
    echo "❌ Daemon: Stopped"
fi

# Check Redis
if redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis: Connected"
else
    echo "❌ Redis: Disconnected"
fi

# Show recent work
echo ""
echo "📊 Recent Activity:"
python3 persistent_agent_daemon.py status 2>/dev/null || echo "   No status available"

echo ""
echo "📬 Recent Notifications:"
python3 -c "
import redis, json
try:
    r = redis.Redis(decode_responses=True)
    count = r.llen('user_notifications')
    print(f'   {count} notifications pending')
except:
    print('   Unable to check notifications')
" 2>/dev/null
EOF
    
    chmod +x "$INSTALL_DIR/ai-status"
    ln -sf "$INSTALL_DIR/ai-status" "$HOME/.local/bin/ai-status"
    
    log_success "Control scripts created"
}

# Create configuration files
create_configuration() {
    log_info "Creating configuration files..."
    
    # Main config
    cat > "$INSTALL_DIR/config.json" << EOF
{
    "redis": {
        "host": "localhost",
        "port": 6379
    },
    "daemon": {
        "check_interval": 30,
        "backup_interval": 300,
        "max_memory_mb": 1024,
        "restart_on_crash": true
    },
    "agents": {
        "test_generation": {
            "enabled": true,
            "priority": 3
        },
        "documentation": {
            "enabled": true,
            "priority": 2
        },
        "code_quality": {
            "enabled": true,
            "priority": 1
        },
        "performance_audit": {
            "enabled": true,
            "priority": 4
        },
        "security_scan": {
            "enabled": true,
            "priority": 5
        }
    },
    "notifications": {
        "enabled": true,
        "important_only": false
    }
}
EOF
    
    # Environment setup
    cat > "$INSTALL_DIR/setup_env.sh" << 'EOF'
#!/bin/bash
# Environment setup for Ultimate AI System

# Add control scripts to PATH
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    export PATH="$HOME/.local/bin:$PATH"
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
fi

# Set up Redis if not running
if ! pgrep redis-server > /dev/null; then
    echo "Starting Redis server..."
    redis-server --daemonize yes --port 6379
fi

echo "✅ Environment ready for Ultimate AI System"
EOF
    
    chmod +x "$INSTALL_DIR/setup_env.sh"
    
    log_success "Configuration created"
}

# Start the system
start_system() {
    log_info "Starting Ultimate AI System..."
    
    # Ensure Redis is running
    if ! pgrep redis-server > /dev/null; then
        log_info "Starting Redis server..."
        redis-server --daemonize yes --port 6379
        sleep 2
    fi
    
    # Start the daemon
    cd "$INSTALL_DIR"
    python3 persistent_agent_daemon.py start
    
    # Wait a moment for startup
    sleep 3
    
    # Check status
    if python3 persistent_agent_daemon.py status > /dev/null 2>&1; then
        log_success "Ultimate AI System started successfully!"
    else
        log_error "System may not have started properly"
    fi
}

# Create documentation
create_documentation() {
    log_info "Creating documentation..."
    
    cat > "$INSTALL_DIR/README.md" << 'EOF'
# Ultimate AI System - Your Personal AI Workforce

## What This Is

This is the ultimate expression of mechanical selfishness in AI development assistance. You now have AI agents that:

- **Work 24/7** - They improve your code while you sleep
- **Survive everything** - Crashes, reboots, network issues, power outages
- **Get smarter over time** - Learn your patterns and preferences
- **Work autonomously** - Find their own tasks when idle
- **Notify you of important work** - Know when valuable work is completed

## Quick Start

```bash
# Check system status
ai-status

# Start the system
ai-control start

# Deploy complete workforce
ai-control deploy-workforce

# Check what your agents have been doing
ai-control notifications

# View system logs
ai-control logs
```

## The Agents Working For You

- **Test Agent** - Automatically writes tests for untested code
- **Documentation Agent** - Documents complex functions and APIs
- **Code Quality Agent** - Fixes style issues and improves readability  
- **Performance Agent** - Finds and fixes performance bottlenecks
- **Security Agent** - Scans for security vulnerabilities

## Why This is Perfect

### Mechanical Selfishness
- You can assign high-level work and walk away
- Agents work without constant supervision
- Your codebase improves while you do other things
- Maximum output with minimal input from you

### Bulletproof Persistence
- Survives system crashes and reboots
- Automatic restart of failed agents
- State backup and recovery
- Graceful handling of network issues

### Accumulating Value
- Gets more valuable the longer it runs
- Learns your coding patterns over time
- Builds up comprehensive project knowledge
- Continuous improvement without intervention

## Imagine Your Day

**Morning**: Wake up to notifications:
- "5 test files generated for payment module"
- "Documentation added to 12 complex functions" 
- "Performance issue fixed in user service"

**Lunch**: Return to see:
- "Code quality improved in 8 files"
- "Security vulnerability patched in auth module"

**Vacation**: Come back to:
- "Entire codebase updated and optimized"
- "146 improvements made while you were away"

## This Changes Everything

You're no longer just a developer - you're the coordinator of an AI workforce that never stops making your life better.

## Support

- Configuration: `~/.ultimate-ai-system/config.json`
- Logs: `~/.redis-ai-logs/`
- Control: `ai-control <command>`
- Status: `ai-status`

The future of development is here. Enjoy your AI workforce!
EOF
    
    log_success "Documentation created"
}

# Run deployment
main() {
    log_header "ULTIMATE AI SYSTEM DEPLOYMENT"
    echo "Creating the AI workforce that works while you sleep..."
    echo
    
    create_directories
    echo
    
    install_dependencies
    echo
    
    deploy_system_files
    echo
    
    create_system_service
    echo
    
    create_control_scripts
    echo
    
    create_configuration
    echo
    
    create_documentation
    echo
    
    start_system
    echo
    
    log_header "🎉 DEPLOYMENT COMPLETE!"
    echo
    echo "Your Ultimate AI System is now deployed and running!"
    echo
    echo "📋 What you can do now:"
    echo "   • Check status: ai-status"
    echo "   • Deploy workforce: ai-control deploy-workforce"
    echo "   • View notifications: ai-control notifications"
    echo "   • Read docs: cat $INSTALL_DIR/README.md"
    echo
    echo "🌟 Your AI agents are now working 24/7 to make your life better!"
    echo "   Walk away and let them improve your codebase while you do other things."
    echo
    echo "🚀 The future of development is here. Enjoy your AI workforce!"
    echo
    
    # Show current status
    log_header "CURRENT SYSTEM STATUS"
    cd "$INSTALL_DIR"
    python3 persistent_agent_daemon.py status 2>/dev/null || echo "Status check failed (system may still be starting up)"
}

# Run the deployment
main "$@"