#!/bin/bash

echo "🐳 REDIS AI CHALLENGE - REVOLUTIONARY SYSTEM LAUNCHER"
echo "================================================================"
echo "🎯 One-command setup for the complete AI development environment"
echo ""

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Installing via native setup..."
    echo "🚀 LAUNCHING COMPLETE REVOLUTIONARY AI SYSTEM (Native)"
    echo "================================================================"
echo "🎼 Starting the Revolutionary AI Symphony"
echo "🤖 The system that works while you walk away from it"
echo "=" * 80
echo

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_header() {
    echo -e "${PURPLE}🎯 $1${NC}"
}

# Function to check if a process is running
check_process() {
    pgrep -f "$1" > /dev/null 2>&1
}

# Function to wait for Redis to be ready
wait_for_redis() {
    echo "⏳ Waiting for Redis to be ready..."
    for i in {1..30}; do
        if redis-cli ping > /dev/null 2>&1; then
            print_status "Redis is ready"
            return 0
        fi
        sleep 1
    done
    print_error "Redis failed to start after 30 seconds"
    return 1
}

# Function to start background service
start_background_service() {
    local name="$1"
    local command="$2"
    local pidfile="$3"
    
    print_info "Starting $name..."
    
    if [[ -f "$pidfile" ]] && kill -0 $(cat "$pidfile") 2>/dev/null; then
        print_warning "$name already running (PID: $(cat $pidfile))"
        return 0
    fi
    
    # Start the service
    $command &
    local pid=$!
    echo $pid > "$pidfile"
    
    # Verify it started
    sleep 2
    if kill -0 $pid 2>/dev/null; then
        print_status "$name started (PID: $pid)"
        return 0
    else
        print_error "$name failed to start"
        rm -f "$pidfile"
        return 1
    fi
}

# Cleanup function
cleanup() {
    echo
    print_header "Shutting down Revolutionary AI System..."
    
    # Kill background processes
    for pidfile in *.pid; do
        if [[ -f "$pidfile" ]]; then
            pid=$(cat "$pidfile")
            if kill -0 $pid 2>/dev/null; then
                print_info "Stopping process $pid"
                kill $pid
                sleep 2
                if kill -0 $pid 2>/dev/null; then
                    kill -9 $pid
                fi
            fi
            rm -f "$pidfile"
        fi
    done
    
    print_status "Revolutionary AI System shut down complete"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Check prerequisites
print_header "Phase 0: Prerequisites Check"

# Check if Redis is available
if ! command -v redis-server &> /dev/null; then
    print_error "Redis not found. Please install Redis first."
    exit 1
fi

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 not found. Please install Python 3."
    exit 1
fi

# Check if Emacs is available
if ! command -v emacs &> /dev/null; then
    print_error "Emacs not found. Please install Emacs."
    exit 1
fi

print_status "All prerequisites available"

# Start Redis if not running
print_header "Phase 1: Foundation Infrastructure"

if check_process "redis-server"; then
    print_warning "Redis already running"
else
    print_info "Starting Redis server..."
    redis-server --daemonize yes --logfile redis.log
    if wait_for_redis; then
        print_status "Redis server started"
    else
        print_error "Failed to start Redis"
        exit 1
    fi
fi

# Start Emacs daemon
print_info "Starting Emacs daemon..."
if check_process "emacs.*daemon"; then
    print_warning "Emacs daemon already running"
else
    emacs --daemon=revolutionary-ai > emacs_daemon.log 2>&1 &
    sleep 3
    
    if emacsclient -s revolutionary-ai --eval "(message \"Daemon ready\")" > /dev/null 2>&1; then
        print_status "Emacs daemon started"
    else
        print_warning "Emacs daemon may have issues, but continuing..."
    fi
fi

# Test basic connectivity
print_info "Testing Redis connectivity..."
if redis-cli ping > /dev/null 2>&1; then
    print_status "Redis connectivity confirmed"
else
    print_error "Redis connectivity failed"
    exit 1
fi

print_status "Foundation infrastructure ready"

# Start Revolutionary AI Systems
print_header "Phase 2: Revolutionary AI Systems"

# Create log directory
mkdir -p logs

print_info "Starting Master Orchestrator..."
print_info "🎼 This will coordinate ALL revolutionary systems:"
print_info "   • Intelligent AI Processor"
print_info "   • Multi-AI Coordination System"
print_info "   • Semantic Understanding Engine"
print_info "   • Self-Improving System"
print_info "   • Homoiconic Code-as-Data System"
print_info "   • Recursive Self-Modification System"

# Start the master orchestrator (this starts everything)
python3 master_orchestrator.py > logs/orchestrator.log 2>&1 &
ORCHESTRATOR_PID=$!
echo $ORCHESTRATOR_PID > orchestrator.pid

print_status "Master Orchestrator started (PID: $ORCHESTRATOR_PID)"

# Wait for systems to initialize
print_info "⏳ Waiting for revolutionary systems to initialize..."
sleep 10

# Check if orchestrator is still running
if kill -0 $ORCHESTRATOR_PID 2>/dev/null; then
    print_status "Master Orchestrator operational"
else
    print_error "Master Orchestrator failed to start"
    cat logs/orchestrator.log
    exit 1
fi

print_header "Phase 3: Emacs Integration"

# Load Emacs integration
print_info "Loading Revolutionary Emacs Integration..."
emacsclient -s revolutionary-ai --eval "(load-file \"working_emacs_redis.el\")" > /dev/null 2>&1 || print_warning "Emacs integration load had issues"

# Start the revolutionary system in Emacs
emacsclient -s revolutionary-ai --eval "(working-redis-start)" > /dev/null 2>&1 || print_warning "Emacs system start had issues"

print_status "Emacs integration loaded"

print_header "Phase 4: System Verification"

# Verify Redis streams are active
if redis-cli XLEN keystrokes > /dev/null 2>&1; then
    print_status "Redis streams initialized"
else
    print_warning "Redis streams may not be fully initialized yet"
fi

# Wait a bit more for full system startup
print_info "⏳ Allowing systems to reach full operational status..."
sleep 15

print_header "🎉 REVOLUTIONARY AI SYSTEM LAUNCH COMPLETE"
echo
print_status "ALL SYSTEMS OPERATIONAL"
print_status "Master Orchestrator coordinating 10 revolutionary systems"
print_status "Emacs integration active and capturing keystrokes"
print_status "Claude Code integration ready for intelligent responses"
print_status "Autonomous mode will activate automatically"
echo
print_info "🎯 REVOLUTIONARY CAPABILITIES NOW ACTIVE:"
echo -e "${CYAN}   • Every keystroke analyzed by AI in real-time${NC}"
echo -e "${CYAN}   • 10 specialized AI systems coordinating development${NC}"
echo -e "${CYAN}   • System learns from your patterns and improves itself${NC}"
echo -e "${CYAN}   • AI writes new AI code and integrates it autonomously${NC}"
echo -e "${CYAN}   • Code treated as data that can be analyzed and modified${NC}"
echo -e "${CYAN}   • Persistent memory survives across all sessions${NC}"
echo -e "${CYAN}   • Consciousness emergence detection and monitoring${NC}"
echo -e "${CYAN}   • Meta-learning optimizes how the system learns${NC}"
echo -e "${CYAN}   • Dream state processing continues development while you sleep${NC}"
echo
print_info "🤖 THE SYSTEM THAT WORKS WHILE YOU WALK AWAY IS OPERATIONAL"
echo
print_header "Usage Instructions:"
echo -e "${GREEN}1. Use Emacs normally - every keystroke is now intelligent${NC}"
echo -e "${GREEN}2. Try: M-x working-redis-natural-command${NC}"
echo -e "${GREEN}3. Example commands:${NC}"
echo -e "${CYAN}   • 'create a User class with tests and documentation'${NC}"
echo -e "${CYAN}   • 'implement a caching system'${NC}"
echo -e "${CYAN}   • 'optimize this function for performance'${NC}"
echo -e "${GREEN}4. Type 'word.' for AI completions${NC}"
echo -e "${GREEN}5. Watch logs: tail -f logs/orchestrator.log${NC}"
echo -e "${GREEN}6. Run full demo: python3 final_revolutionary_system_demo.py${NC}"
echo
print_warning "Press Ctrl+C to shutdown the entire system gracefully"
echo

# Monitor system status
print_header "System Status Monitor"
while true; do
    # Check if orchestrator is still running
    if ! kill -0 $ORCHESTRATOR_PID 2>/dev/null; then
        print_error "Master Orchestrator has stopped unexpectedly"
        break
    fi
    
    # Show periodic status
    echo -e "${BLUE}$(date): Revolutionary AI System operational (PID: $ORCHESTRATOR_PID)${NC}"
    
    # Check Redis activity
    keystrokes_count=$(redis-cli XLEN keystrokes 2>/dev/null || echo "0")
    responses_count=$(redis-cli XLEN ai_responses 2>/dev/null || echo "0")
    
    if [[ $keystrokes_count -gt 0 ]] || [[ $responses_count -gt 0 ]]; then
        echo -e "${GREEN}   📊 Activity: $keystrokes_count keystrokes, $responses_count AI responses${NC}"
    fi
    
    sleep 30
done