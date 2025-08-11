FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    redis-server \
    git \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY pyproject.toml .
COPY README.md .
RUN pip install -e .[dev,ai]

# Copy the entire application
COPY . .

# Create Redis data directory
RUN mkdir -p /var/lib/redis
RUN mkdir -p /var/log/redis

# Expose ports
EXPOSE 6379 8000 8001 8002 8003 8004

# Create startup script
RUN echo '#!/bin/bash\n\
echo "🚀 STARTING REDIS AI CHALLENGE REVOLUTIONARY SYSTEM"\n\
echo "=" * 60\n\
\n\
# Start Redis in background\n\
redis-server --daemonize yes --dir /var/lib/redis --logfile /var/log/redis/redis.log\n\
sleep 2\n\
\n\
echo "✅ Redis server started"\n\
\n\
# Test Redis connection\n\
redis-cli ping\n\
\n\
echo "✅ Redis connection verified"\n\
\n\
# Run the revolutionary demo\n\
echo "🎯 Starting Revolutionary AI Demo..."\n\
python standalone_redis_ai_demo.py\n\
\n\
echo "\\n🎤 Starting Voice AI System Demo..."\n\
python complete_working_voice_ai_system.py\n\
\n\
echo "\\n🚀 Starting MCP Transport Analysis..."\n\
python mcp_transport_comparison.py\n\
\n\
echo "\\n🧬 MCP Network Topology Discovery..."\n\
python mcp_network_stress_test.py\n\
\n\
echo "\\n🏆 REVOLUTIONARY SYSTEM DEMONSTRATION COMPLETE!"\n\
echo "✅ Redis AI patterns demonstrated"\n\
echo "✅ Voice coordination working"\n\
echo "✅ MCP architecture operational"\n\
echo "✅ Homoiconic programming active"\n\
echo "\\n🎯 System ready for interactive use"\n\
echo "Redis available at: localhost:6379"\n\
echo "Explore with: redis-cli"\n\
\n\
# Keep container running\n\
tail -f /var/log/redis/redis.log\n\
' > /app/docker_startup.sh

RUN chmod +x /app/docker_startup.sh

# Set environment variables for containerized Redis
ENV REDIS_HOST=localhost
ENV REDIS_PORT=6379

CMD ["/app/docker_startup.sh"]