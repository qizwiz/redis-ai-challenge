#!/bin/bash
set -e

# Redis AI Mode Installation Script
# Installs redis-ai-mode.el and sets up the AI backend services

echo "🚀 Installing Redis AI Mode for Emacs"
echo "====================================="

# Configuration
INSTALL_DIR="$HOME/.emacs.d/redis-ai-mode"
ELISP_FILE="redis-ai-mode.el"
SERVICE_DIR="$HOME/.redis-ai-services"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check Emacs
    if ! command -v emacs &> /dev/null; then
        log_error "Emacs not found. Please install Emacs 27.1 or later."
        exit 1
    fi
    
    EMACS_VERSION=$(emacs --version | head -n1 | grep -o '[0-9]\+\.[0-9]\+')
    log_info "Found Emacs version $EMACS_VERSION"
    
    # Check Redis
    if ! command -v redis-server &> /dev/null; then
        log_warning "Redis server not found. Installing..."
        install_redis
    else
        log_success "Redis server found"
    fi
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 not found. Please install Python 3.8 or later."
        exit 1
    fi
    
    log_success "Prerequisites check complete"
}

install_redis() {
    log_info "Installing Redis..."
    
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        if command -v brew &> /dev/null; then
            brew install redis
        else
            log_error "Homebrew not found. Please install Redis manually: https://redis.io/download"
            exit 1
        fi
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        if command -v apt-get &> /dev/null; then
            sudo apt-get update
            sudo apt-get install -y redis-server
        elif command -v yum &> /dev/null; then
            sudo yum install -y redis
        elif command -v pacman &> /dev/null; then
            sudo pacman -S redis
        else
            log_error "Package manager not supported. Please install Redis manually."
            exit 1
        fi
    else
        log_error "Operating system not supported. Please install Redis manually."
        exit 1
    fi
    
    log_success "Redis installed"
}

# Install Emacs package
install_emacs_package() {
    log_info "Installing Redis AI Mode for Emacs..."
    
    # Create installation directory
    mkdir -p "$INSTALL_DIR"
    
    # Copy elisp file
    cp "$ELISP_FILE" "$INSTALL_DIR/"
    
    log_success "Elisp file installed to $INSTALL_DIR"
    
    # Create autoload configuration
    cat > "$INSTALL_DIR/redis-ai-autoload.el" << 'EOF'
;;; Redis AI Mode Autoload Configuration
(add-to-list 'load-path (file-name-directory load-file-name))
(require 'redis-ai-mode)

;; Auto-enable for programming modes
(add-hook 'python-mode-hook #'redis-ai-mode)
(add-hook 'javascript-mode-hook #'redis-ai-mode)
(add-hook 'js-mode-hook #'redis-ai-mode)
(add-hook 'java-mode-hook #'redis-ai-mode)
(add-hook 'c-mode-hook #'redis-ai-mode)
(add-hook 'c++-mode-hook #'redis-ai-mode)
(add-hook 'rust-mode-hook #'redis-ai-mode)
(add-hook 'go-mode-hook #'redis-ai-mode)
(add-hook 'emacs-lisp-mode-hook #'redis-ai-mode)

;; Optional: Enable globally
;; (global-redis-ai-mode 1)

(message "Redis AI Mode loaded and configured")
EOF
    
    log_success "Autoload configuration created"
}

# Install Python backend services
install_backend_services() {
    log_info "Installing AI backend services..."
    
    # Create service directory
    mkdir -p "$SERVICE_DIR"
    
    # Copy Python files
    cp intelligent_response_engine.py "$SERVICE_DIR/"
    cp semantic_code_analyzer.py "$SERVICE_DIR/"
    cp proactive_assistant.py "$SERVICE_DIR/"
    cp complete_dream_system.py "$SERVICE_DIR/"
    
    # Create requirements file
    cat > "$SERVICE_DIR/requirements.txt" << 'EOF'
redis>=4.0.0
anthropic>=0.7.0
openai>=1.0.0
aiohttp>=3.8.0
asyncio-mqtt>=0.11.0
python-dotenv>=0.19.0
EOF
    
    # Create virtual environment and install dependencies
    cd "$SERVICE_DIR"
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    
    log_success "Backend services installed in $SERVICE_DIR"
}

# Create startup script
create_startup_script() {
    log_info "Creating startup script..."
    
    cat > "$SERVICE_DIR/start-redis-ai.sh" << EOF
#!/bin/bash
# Redis AI Services Startup Script

cd "$SERVICE_DIR"
source venv/bin/activate

# Start Redis if not running
if ! pgrep -x "redis-server" > /dev/null; then
    echo "Starting Redis server..."
    redis-server --daemonize yes --port 6379
    sleep 2
fi

# Start AI services
echo "Starting Redis AI services..."
python3 complete_dream_system.py &
AI_PID=\$!

echo "Redis AI services started (PID: \$AI_PID)"
echo "Use 'pkill -f complete_dream_system.py' to stop"

# Keep script running
wait \$AI_PID
EOF
    
    chmod +x "$SERVICE_DIR/start-redis-ai.sh"
    log_success "Startup script created: $SERVICE_DIR/start-redis-ai.sh"
}

# Create configuration template
create_config() {
    log_info "Creating configuration template..."
    
    cat > "$SERVICE_DIR/.env.template" << 'EOF'
# Redis AI Configuration
# Copy this to .env and fill in your API keys

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379

# AI Provider API Keys (at least one required)
ANTHROPIC_API_KEY=your_claude_api_key_here
OPENAI_API_KEY=your_openai_api_key_here

# Optional: Azure OpenAI
AZURE_OPENAI_ENDPOINT=your_azure_endpoint
AZURE_OPENAI_KEY=your_azure_key

# AI Configuration
PRIMARY_AI_PROVIDER=claude
ENABLE_LOCAL_MODELS=false
ENABLE_PROACTIVE_SUGGESTIONS=true

# Logging
LOG_LEVEL=INFO
VERBOSE_LOGGING=false
EOF
    
    log_success "Configuration template created: $SERVICE_DIR/.env.template"
}

# Generate Emacs configuration
generate_emacs_config() {
    log_info "Generating Emacs configuration..."
    
    EMACS_CONFIG="$INSTALL_DIR/init-redis-ai.el"
    
    cat > "$EMACS_CONFIG" << EOF
;;; Redis AI Mode Configuration
;;; Add this to your Emacs init file (.emacs, init.el, etc.)

;; Load Redis AI Mode
(load-file "$INSTALL_DIR/redis-ai-autoload.el")

;; Configuration
(setq redis-ai-redis-host "localhost"
      redis-ai-redis-port 6379
      redis-ai-enable-proactive-suggestions t
      redis-ai-suggestion-display-time 10.0
      redis-ai-update-interval 2.0)

;; Optional: Enable for specific modes only
;; (add-hook 'python-mode-hook #'redis-ai-mode)
;; (add-hook 'javascript-mode-hook #'redis-ai-mode)

;; Optional: Enable globally for all programming modes
(global-redis-ai-mode 1)

;; Key bindings (already defined in redis-ai-mode-map)
;; C-c C-a : Dismiss AI suggestions
;; C-c C-h : Request help from AI
;; C-c C-s : Show Redis AI status

(message "Redis AI Mode configuration loaded")
EOF
    
    log_success "Emacs configuration generated: $EMACS_CONFIG"
}

# Main installation flow
main() {
    echo
    log_info "Starting Redis AI Mode installation..."
    echo
    
    check_prerequisites
    echo
    
    install_emacs_package
    echo
    
    install_backend_services
    echo
    
    create_startup_script
    echo
    
    create_config
    echo
    
    generate_emacs_config
    echo
    
    log_success "Installation complete!"
    echo
    echo "📋 Next steps:"
    echo "1. Add this to your Emacs configuration:"
    echo "   ${BLUE}(load-file \"$EMACS_CONFIG\")${NC}"
    echo
    echo "2. Configure your AI API keys:"
    echo "   ${BLUE}cp $SERVICE_DIR/.env.template $SERVICE_DIR/.env${NC}"
    echo "   ${BLUE}nano $SERVICE_DIR/.env${NC}"
    echo
    echo "3. Start the Redis AI services:"
    echo "   ${BLUE}$SERVICE_DIR/start-redis-ai.sh${NC}"
    echo
    echo "4. Restart Emacs and start coding!"
    echo
    echo "🎯 The AI will observe your development workflow and provide intelligent assistance."
    echo "   Use C-c C-h to request help, C-c C-a to dismiss suggestions."
    echo
    log_success "Enjoy your AI-powered development environment! 🧠✨"
}

# Run installation
main "$@"