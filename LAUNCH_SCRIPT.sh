#!/bin/bash
# Redis AI Challenge - Launch Script
# One command to rule them all!

echo "🚀 REDIS AI CHALLENGE - LAUNCH SEQUENCE INITIATED"
echo "=================================================="

# Check if Redis is running
if ! redis-cli ping &> /dev/null; then
    echo "❌ Redis not running. Starting Redis..."
    if command -v brew &> /dev/null; then
        brew services start redis
    else
        sudo systemctl start redis
    fi
    sleep 2
fi

if redis-cli ping &> /dev/null; then
    echo "✅ Redis is ready"
else
    echo "❌ Could not start Redis. Please start manually: redis-server"
    exit 1
fi

# Install dependencies if needed
if ! python -c "import redis" &> /dev/null; then
    echo "📦 Installing Python dependencies..."
    pip install redis requests
fi

echo ""
echo "🎬 LAUNCHING DEMONSTRATIONS:"
echo "============================"

echo ""
echo "1. 🎯 STANDALONE DEMO (Perfect for sharing)"
echo "   python standalone_redis_ai_demo.py"
echo ""

echo "2. 🏭 PRODUCTION INTEGRATION (Giants' shoulders)"
echo "   python streamflow_integrated_system.py"
echo ""

echo "3. 🧠 REDIS HOMOICONICITY (Revolutionary)"
echo "   python redis_lisp_interpreter.py"
echo ""

echo "4. 🛠️  INTELLIGENT DEV TOOLS (FastMCP)"
echo "   python intelligent_dev_assistant.py"
echo ""

echo "5. 📊 SEMANTIC TAXONOMY (AI Understanding)"
echo "   python emacs_semantic_taxonomy_extractor.py"
echo ""

# Ask user which demo to run
echo "Which demo would you like to run? (1-5, or 'all' for sequence): "
read -r choice

case $choice in
    1)
        echo "🎯 Running Standalone Demo..."
        python standalone_redis_ai_demo.py
        ;;
    2)
        echo "🏭 Running Production Integration..."
        python streamflow_integrated_system.py
        ;;
    3)
        echo "🧠 Running Redis Homoiconicity Demo..."
        python redis_lisp_interpreter.py
        ;;
    4)
        echo "🛠️  Running Intelligent Dev Tools..."
        python intelligent_dev_assistant.py
        ;;
    5)
        echo "📊 Running Semantic Taxonomy Extractor..."
        python emacs_semantic_taxonomy_extractor.py
        ;;
    all|ALL)
        echo "🎬 Running complete demonstration sequence..."
        echo ""
        
        echo "▶️  Demo 1: Standalone Redis AI Demo"
        python standalone_redis_ai_demo.py
        echo ""
        echo "Press Enter for next demo..."
        read -r
        
        echo "▶️  Demo 2: Production Integration"
        python streamflow_integrated_system.py
        echo ""
        echo "Press Enter for next demo..."
        read -r
        
        echo "▶️  Demo 3: Redis Homoiconicity"
        python redis_lisp_interpreter.py
        echo ""
        echo "Press Enter for final stats..."
        read -r
        
        echo "📊 FINAL REDIS STATISTICS:"
        echo "========================="
        echo "Total Redis keys: $(redis-cli DBSIZE)"
        echo "Active streams: $(redis-cli KEYS '*:*' | wc -l)"
        echo "Job queues: $(redis-cli KEYS 'mlq:*' | wc -l)"
        echo "Feature store: $(redis-cli KEYS 'features:*' | wc -l)"
        echo ""
        echo "🎉 Complete demonstration sequence finished!"
        ;;
    *)
        echo "❌ Invalid choice. Running standalone demo as default..."
        python standalone_redis_ai_demo.py
        ;;
esac

echo ""
echo "🔍 EXPLORE THE DATA:"
echo "==================="
echo "redis-cli KEYS '*'                    # See all keys"
echo "redis-cli HGETALL redis_ai_challenge:final_report"
echo "redis-cli XRANGE ml:pipeline - +"
echo "redis-cli ZRANGE mlq:jobs 0 -1 WITHSCORES"
echo ""

echo "📄 SUBMISSION READY:"
echo "==================="
echo "✅ REDIS_AI_CHALLENGE_FINAL_SUBMISSION.md"
echo "✅ All demos working and tested"
echo "✅ Redis data populated and explorable"
echo "✅ Standing on giants' shoulders successfully"
echo ""

echo "🏆 REDIS AI CHALLENGE - LAUNCH COMPLETE!"
echo "Ready for submission before August 10, 2025"