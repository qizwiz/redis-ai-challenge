const WebSocket = require('ws');
const http = require('http');
const redis = require('redis');

// Create HTTP server for WebSocket
const server = http.createServer();
const wss = new WebSocket.Server({ server });

// Redis client for persistence
const redisClient = redis.createClient();
redisClient.connect();

// Track connections by channel
const channels = {
    'human-ai': new Set(),
    'ai-self': new Set(), 
    'coordination': new Set()
};

// Handle WebSocket connections
wss.on('connection', (ws) => {
    console.log('New connection established');
    let currentChannel = null;
    
    ws.on('message', async (data) => {
        try {
            const message = JSON.parse(data);
            
            if (message.type === 'join') {
                // Join channel
                currentChannel = message.channel;
                if (channels[currentChannel]) {
                    channels[currentChannel].add(ws);
                    console.log(`Client joined ${currentChannel}`);
                    
                    ws.send(JSON.stringify({
                        type: 'system',
                        message: `Joined ${currentChannel} channel`,
                        channel: currentChannel
                    }));
                }
            } else if (message.type === 'message' && currentChannel) {
                // Broadcast message to channel
                const broadcastMessage = {
                    type: 'message',
                    channel: currentChannel,
                    sender: message.sender || 'anonymous',
                    content: message.content,
                    timestamp: Date.now()
                };
                
                // Store in Redis (convert timestamp to string)
                const redisMessage = {
                    type: broadcastMessage.type,
                    channel: broadcastMessage.channel,
                    sender: broadcastMessage.sender,
                    content: broadcastMessage.content,
                    timestamp: broadcastMessage.timestamp.toString()
                };
                await redisClient.xAdd(`chat:${currentChannel}`, '*', redisMessage);
                
                // Broadcast to all clients in channel
                channels[currentChannel].forEach(client => {
                    if (client.readyState === WebSocket.OPEN) {
                        client.send(JSON.stringify(broadcastMessage));
                    }
                });
                
                console.log(`Message in ${currentChannel}: ${message.content}`);
            }
        } catch (error) {
            console.error('Message handling error:', error);
        }
    });
    
    ws.on('close', () => {
        // Remove from all channels
        Object.keys(channels).forEach(channel => {
            channels[channel].delete(ws);
        });
        console.log('Connection closed');
    });
});

// Start server
const PORT = 3003;
server.listen(PORT, () => {
    console.log(`Real AI Chat Server listening on port ${PORT}`);
    console.log('Channels available: human-ai, ai-self, coordination');
});

// Handle graceful shutdown
process.on('SIGTERM', () => {
    console.log('Shutting down server...');
    wss.close();
    redisClient.quit();
    server.close();
});