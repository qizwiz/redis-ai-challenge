const WebSocket = require('ws');
const redis = require('redis');
const http = require('http');

// Create HTTP server and WebSocket server
const server = http.createServer();
const wss = new WebSocket.Server({ server });

// Redis client for coordination
const redisClient = redis.createClient();

// Chat channels
const channels = {
    'human-ai': new Set(),
    'ai-self': new Set(),
    'coordination': new Set()
};

wss.on('connection', (ws) => {
    console.log('New WebSocket connection');
    
    ws.on('message', (message) => {
        try {
            const data = JSON.parse(message);
            
            switch(data.type) {
                case 'join':
                    if (channels[data.channel]) {
                        channels[data.channel].add(ws);
                        ws.channel = data.channel;
                        ws.send(JSON.stringify({
                            type: 'joined',
                            channel: data.channel,
                            timestamp: Date.now()
                        }));
                    }
                    break;
                    
                case 'message':
                    if (ws.channel && channels[ws.channel]) {
                        const messageData = {
                            type: 'message',
                            channel: ws.channel,
                            content: data.content,
                            sender: data.sender || 'unknown',
                            timestamp: Date.now()
                        };
                        
                        // Broadcast to all clients in channel
                        channels[ws.channel].forEach(client => {
                            if (client.readyState === WebSocket.OPEN) {
                                client.send(JSON.stringify(messageData));
                            }
                        });
                        
                        // Store in Redis for persistence
                        redisClient.xadd(`chat:${ws.channel}`, '*', 
                            'content', data.content,
                            'sender', data.sender || 'unknown',
                            'timestamp', Date.now()
                        );
                    }
                    break;
            }
        } catch (error) {
            console.error('Message handling error:', error);
        }
    });
    
    ws.on('close', () => {
        if (ws.channel && channels[ws.channel]) {
            channels[ws.channel].delete(ws);
        }
    });
});

server.listen(3001, () => {
    console.log('Multi-interface chat server running on port 3001');
    console.log('Channels: human-ai, ai-self, coordination');
});
