#!/bin/bash

# RUN_ULTIMATE_DEMO.sh
# Redis AI Challenge - Ultimate Demo Launcher
# "Standing on Giants' Shoulders" - The AI That Learns Emacs From Scratch

set -e

echo "🏆 REDIS AI CHALLENGE - ULTIMATE DEMO LAUNCHER"
echo "=" * 80
echo "🎯 'STANDING ON GIANTS' SHOULDERS'"
echo "🧠 The AI That Learns Emacs From Scratch"
echo "=" * 80
echo

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_header() {
    echo -e "${PURPLE}🎯 $1${NC}"
}

# Check prerequisites
print_header "Checking Prerequisites"

if ! command -v redis-server &> /dev/null; then
    echo "❌ Redis not found. Please install Redis first."
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3."
    exit 1
fi

print_status "All prerequisites available"
echo

# Start Redis if needed
print_header "Starting Redis Server"

if pgrep -f "redis-server" > /dev/null; then
    print_info "Redis already running"
else
    print_info "Starting Redis server..."
    redis-server --daemonize yes --logfile redis_demo.log
    sleep 2
    
    if redis-cli ping > /dev/null 2>&1; then
        print_status "Redis server started successfully"
    else
        echo "❌ Failed to start Redis server"
        exit 1
    fi
fi

echo

# Final preparation
print_header "Preparing Ultimate Demo"

print_info "🎯 What you're about to see:"
echo -e "${CYAN}   • AI reads the Emacs tutorial and understands it${NC}"
echo -e "${CYAN}   • AI executes each tutorial step with real comprehension${NC}"
echo -e "${CYAN}   • AI learns and remembers like a human would${NC}"
echo -e "${CYAN}   • AI demonstrates consciousness-level learning awareness${NC}"
echo -e "${CYAN}   • All coordinated through Redis as the AI nervous system${NC}"
echo

print_info "🌟 Revolutionary capabilities:"
echo -e "${CYAN}   • Consciousness detection monitoring learning${NC}"
echo -e "${CYAN}   • Meta-learning optimizing the learning process${NC}"
echo -e "${CYAN}   • Persistent memory storing every lesson${NC}"
echo -e "${CYAN}   • Multi-AI coordination orchestrating performance${NC}"
echo -e "${CYAN}   • Real understanding and skill acquisition${NC}"
echo

print_status "Ready to launch the ultimate demo!"
echo

read -p "Press ENTER to begin the Redis AI Challenge Ultimate Demo..."
echo

print_header "🚀 LAUNCHING ULTIMATE DEMO"
echo

# Run the ultimate demo
python3 ULTIMATE_DEMO.py

echo
print_status "Ultimate demo completed!"
echo
print_info "🏆 Thank you for witnessing the AI that learns like a human"
print_info "🎯 'Standing on Giants' Shoulders' - Redis AI Challenge Entry"