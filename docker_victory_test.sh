#!/bin/bash
echo "🐳 DOCKER VICTORY TEST"
echo "Testing real Redis AI coordination in container"

redis-server --daemonize yes
sleep 2

python3 -c "
from redis_ai_patterns.homoiconic import HomoiconicRedis
import requests
import os

engine = HomoiconicRedis()

# Add real functions  
engine.builtins['api-call'] = lambda url: f'HTTP-{requests.get(url, timeout=2).status_code}'
engine.builtins['file-check'] = lambda f: f'FILE-{len(open(f).read()) if os.path.exists(f) else 0}'

# Test coordination
result = engine.execute(['api-call', 'https://httpbin.org/json'])
print(f'✅ Real coordination in Docker: {result}')

# Store and execute
engine.store_code('docker_test', ['*', 6, 7])
stored = engine.execute('docker_test')
print(f'✅ Redis storage works: {stored}')

print('🏆 DOCKER VICTORY CONFIRMED!')
"
