#!/usr/bin/env python3
"""
Quick test of Redis browser control system
"""

import redis
import time
import json

def test_redis_browser_commands():
    """Test Redis browser command system"""
    
    print("🧪 TESTING REDIS BROWSER CONTROL")
    print("=" * 40)
    
    r = redis.Redis(host='localhost', port=6379, decode_responses=True)
    
    # Test 1: Send navigation command
    print("📡 Test 1: Sending navigation command via Redis...")
    nav_id = r.xadd('browser:commands', {
        'action': 'navigate',
        'url': 'https://dev.to/new',
        'test': 'true'
    })
    print(f"✅ Command sent with ID: {nav_id}")
    
    # Test 2: Send article submission command  
    print("\n📡 Test 2: Sending DEV.to submission command...")
    article_data = {
        'action': 'submit_devto_article',
        'title': 'Redis Browser Control Demo - LIVE from Redis Streams!',
        'content': '''# Redis Browser Control Demo

This article is being submitted live via Redis streams controlling my browser!

## How it works:

```bash
# Send Redis command to control browser
redis-cli xadd browser:commands * \\
  action submit_devto_article \\
  title "My Article" \\
  content "Content here"
```

This demonstrates Redis as the ultimate coordination platform - it can control anything, including web browsers!

#redis #browser #automation #demo
''',
        'tags': 'redis,browser,demo,automation',
        'test': 'true'
    }
    
    submit_id = r.xadd('browser:commands', article_data)
    print(f"✅ Submission command sent with ID: {submit_id}")
    
    # Test 3: Check commands in stream
    print("\n📊 Test 3: Checking command stream...")
    recent_commands = r.xrevrange('browser:commands', count=5)
    
    for cmd_id, cmd_data in recent_commands:
        action = cmd_data.get('action', 'unknown')
        print(f"   • {action} (ID: {cmd_id[:12]}...)")
    
    print("\n🚀 REDIS BROWSER CONTROL TEST COMPLETE!")
    print("Start the browser daemon with: ./ULTIMATE_REDIS_BROWSER_DEMO.sh")
    print("Or manually: python3 redis_browser_control.py daemon")
    
    return True

if __name__ == "__main__":
    test_redis_browser_commands()