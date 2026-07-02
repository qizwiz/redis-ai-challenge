#!/bin/bash

# Integration Test - Test all components together

echo "🧪 Running Multi-Interface Integration Test..."

# Test Redis connectivity
echo "Testing Redis connectivity..."
redis-cli ping >/dev/null 2>&1 && echo "✅ Redis connected" || echo "❌ Redis failed"

# Test component files exist
components=(
    "websocket_chat_server.js"
    "hid_device_controller.py"
    "advanced_window_manager.py"
    "multi_session_ai_coordinator.py"
    "input_device_router.py"
)

for component in "${components[@]}"; do
    if [[ -f "/Users/jonathanhill/src/redis-ai-challenge/$component" ]]; then
        echo "✅ Component exists: $component"
    else
        echo "❌ Component missing: $component"
    fi
done

# Test component imports (Python)
python_components=(
    "hid_device_controller.py"
    "advanced_window_manager.py"
    "multi_session_ai_coordinator.py"
    "input_device_router.py"
)

for component in "${python_components[@]}"; do
    python3 -c "import sys; sys.path.append('/Users/jonathanhill/src/redis-ai-challenge'); exec(open('/Users/jonathanhill/src/redis-ai-challenge/$component').read().split('if __name__')[0])" 2>/dev/null && echo "✅ Python syntax valid: $component" || echo "❌ Python syntax error: $component"
done

# Test WebSocket server syntax
node -c /Users/jonathanhill/src/redis-ai-challenge/websocket_chat_server.js 2>/dev/null && echo "✅ Node.js syntax valid: websocket_chat_server.js" || echo "❌ Node.js syntax error: websocket_chat_server.js"

echo "Integration test complete!"
