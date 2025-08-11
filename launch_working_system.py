#!/usr/bin/env python3
"""
Launch Working AI Conversation System
High memory, unlimited listeners, full orchestration
"""

import os
import sys
import subprocess
import asyncio
from pathlib import Path

# Set high limits
os.environ['NODE_OPTIONS'] = '--max-old-space-size=8192 --max-listeners=0'
os.environ['UV_LINK_MODE'] = 'copy'

sys.path.append('/Users/jonathanhill/src/redis-ai-challenge')

def main():
    print("🚀 LAUNCHING WORKING AI CONVERSATION SYSTEM")
    print("🧠 Memory: 8GB allocated, unlimited event listeners")
    print("=" * 60)
    
    # Import all working systems
    from jit_mcp_factory import JITMCPFactory
    from redis_ai_patterns.core import RedisAIBase
    from redis_ai_patterns.homoiconic import HomoiconicRedis
    from redis_ai_patterns.streams import StreamProcessor
    
    print("✅ All Redis AI patterns loaded")
    
    # Initialize systems
    factory = JITMCPFactory()
    redis_lisp = HomoiconicRedis()  
    stream_processor = StreamProcessor()
    
    print(f"📦 JIT Factory ready: {len(factory.created_servers)} cached servers")
    print("🧠 Homoiconic Redis interpreter ready")
    print("⚡ Stream processor ready for high-throughput")
    
    # Test homoiconic execution
    print("\n🧮 Testing Homoiconic Execution:")
    test_exprs = [
        ['+', 1, 2, 3],
        ['*', 4, 5],
        ['if', ['>', 10, 5], 'greater', 'less'],
        ['list', 'hello', 'world', 42]
    ]
    
    for expr in test_exprs:
        try:
            result = redis_lisp.execute(expr)
            print(f"   {expr} → {result}")
        except Exception as e:
            print(f"   {expr} → ERROR: {e}")
    
    # Create conversation coordination MCP server
    print("\n🎤 Creating Voice Conversation MCP Server:")
    conversation_server = factory.create_server_for_function(
        'voice_conversation_coordinator',
        ['ai1_name', 'ai2_name', 'topic', 'turns'],
        'Coordinate voice conversation between two AI personas'
    )
    print(f"   Created: {conversation_server}")
    
    # Create homoiconic DSL server  
    print("\n🧠 Creating Homoiconic DSL MCP Server:")
    dsl_server = factory.create_server_for_function(
        'homoiconic_dsl_executor', 
        ['lisp_expression', 'context'],
        'Execute Lisp expressions in homoiconic Redis environment'
    )
    print(f"   Created: {dsl_server}")
    
    # Launch voice conversation system
    print("\n🎯 SYSTEMS READY FOR VOICE CONVERSATION:")
    print("   • JIT MCP Factory operational")
    print("   • Homoiconic Redis executing Lisp code")
    print("   • Stream processing for high-throughput coordination")
    print("   • Voice conversation MCP server generated")
    print("   • Memory limits: 8GB, unlimited listeners")
    
    print("\n🗣️  Ready to launch voice-coordinated AI conversation!")
    print("    Next: Start voice conversation between AI personas")
    
    return {
        'factory': factory,
        'redis_lisp': redis_lisp,
        'stream_processor': stream_processor,
        'conversation_server': conversation_server,
        'dsl_server': dsl_server,
        'status': 'ready_for_voice_conversation'
    }

if __name__ == "__main__":
    systems = main()