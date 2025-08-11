# MCP Protocol Specification - Comprehensive Technical Notes

## Overview
Model Context Protocol (MCP) is an open protocol that standardizes how applications provide context to large language models (LLMs). Version: 2025-06-18

## Transport Methods

### 1. STDIO Transport (Primary)
- **Mechanism**: Client launches MCP server as subprocess
- **Communication**: JSON-RPC messages via standard input/output  
- **Message Delimiter**: Newlines (`\n`)
- **Logging**: Server writes logs to standard error (not stdout)
- **Encoding**: UTF-8 required
- **Rule**: Server MUST NOT write non-JSON-RPC content to stdout
- **Recommendation**: Clients SHOULD support stdio whenever possible

**Implementation Pattern:**
```python
# Server reads from stdin, writes to stdout
import sys
import json

def handle_message():
    line = sys.stdin.readline()
    message = json.loads(line)
    response = process_message(message)
    sys.stdout.write(json.dumps(response) + '\n')
    sys.stdout.flush()
```

### 2. Streamable HTTP Transport (SSE-based)
- **Method**: HTTP POST and GET requests
- **Streaming**: Uses Server-Sent Events (SSE) for real-time communication
- **Session Management**: Via session ID for connection resumability  
- **Security Requirements**:
  - Validate Origin header
  - Bind to localhost only
  - Implement proper authentication
- **Features**:
  - Multiple simultaneous connections
  - Message redelivery
  - Broken connection resumption

**Key SSE Characteristics:**
- **MIME Type**: `text/event-stream`
- **Format**: UTF-8 text stream
- **Delimiter**: Double newlines (`\n\n`)
- **Reconnection**: Automatic with last message ID tracking
- **Browser Support**: 97% of browsers (HTML5 standard)
- **Memory Efficient**: Discards processed messages (vs XHR buffering)

## Message Structure (JSON-RPC 2.0)

### Request Format
```json
{
  "jsonrpc": "2.0",
  "id": "unique_id",
  "method": "method_name",
  "params": {
    "param1": "value1"
  }
}
```

### Response Format
```json
{
  "jsonrpc": "2.0", 
  "id": "unique_id",
  "result": {
    "data": "response_data"
  }
}
```

### Error Format
```json
{
  "jsonrpc": "2.0",
  "id": "unique_id", 
  "error": {
    "code": -32000,
    "message": "Error description"
  }
}
```

## Protocol Flow Patterns

### 1. Tool Calling Pattern
```
Client -> Server: tools/list (discover available tools)
Client -> Server: tools/call (invoke specific tool)
Server -> Client: tool result or error
```

### 2. Resource Pattern  
```
Client -> Server: resources/list (discover resources)
Client -> Server: resources/read (access specific resource)
Server -> Client: resource content or error
```

### 3. Streaming Pattern (SSE)
```
Client -> Server: HTTP GET /events (establish SSE connection)
Server -> Client: data: {...} (continuous event stream)
Server -> Client: data: {...} (real-time updates)
```

## Transport Comparison

| Feature | STDIO | SSE/HTTP |
|---------|-------|----------|
| **Latency** | Higher (subprocess) | Lower (HTTP) |
| **Real-time** | Request-response | True streaming |
| **Reconnection** | Process restart | Automatic |
| **Scalability** | Limited | Multiple connections |
| **Use Case** | Simple tools | Real-time apps |
| **Voice AI Fit** | Poor (blocking) | Excellent |

## SSE Technical Deep Dive

### Event Stream Format
```
data: {"type": "message", "content": "Hello"}
id: 123
event: custom_event

data: {"type": "update", "status": "processing"} 
id: 124

```

### JavaScript Client (EventSource)
```javascript
const evtSource = new EventSource('/events');
evtSource.onmessage = function(event) {
  const data = JSON.parse(event.data);
  console.log('Received:', data);
};
```

### Python SSE Server
```python
from flask import Response, Flask

def event_stream():
    while True:
        data = get_real_time_data()
        yield f"data: {json.dumps(data)}\n\n"
        
@app.route('/events')
def events():
    return Response(event_stream(), 
                   mimetype='text/event-stream',
                   headers={'Cache-Control': 'no-cache'})
```

## MCP + Redis Streams Integration

### Natural Alignment
- **Redis Streams** = Server-side event sourcing
- **SSE** = Client-side event consumption  
- **MCP Tools** = Event processors
- **Homoiconic Lisp** = Event structure as code

### Architecture Pattern
```
Redis Stream -> MCP Server -> SSE -> Client
     ↑               ↑         ↑       ↑
Event Source    Tool Router  Transport  UI
```

## Versioning & Negotiation

### Version Format
- **Pattern**: `YYYY-MM-DD` (e.g., "2025-06-18")
- **Semantics**: Last backwards-incompatible change date
- **States**: Draft, Current, Final

### Negotiation Process
```
Client -> Server: initialize (supported versions)
Server -> Client: initialized (chosen version)
// Session proceeds with agreed version
```

## Error Handling

### Standard Error Codes
- `-32700`: Parse error
- `-32600`: Invalid request  
- `-32601`: Method not found
- `-32602`: Invalid params
- `-32603`: Internal error

### Custom Error Ranges
- `-32000` to `-32099`: Server implementation errors

## Security Considerations

### STDIO Transport
- Subprocess isolation
- No network exposure
- Process-level security

### HTTP/SSE Transport  
- Origin validation required
- Localhost binding only
- Authentication mechanisms
- HTTPS for production

## Performance Characteristics

### STDIO
- **Pros**: Simple, secure, widely supported
- **Cons**: Higher latency, blocking, no reconnection

### SSE/HTTP
- **Pros**: Real-time, automatic reconnection, scalable
- **Cons**: More complex, security considerations, HTTP overhead

## Implementation Recommendations

### For Voice AI Conversation:
1. **Primary**: SSE/HTTP for real-time interaction
2. **Fallback**: STDIO for simple tool calls
3. **Coordination**: Redis Streams for backend
4. **Architecture**: Hybrid approach

### For Simple Tools:
1. **Primary**: STDIO for simplicity
2. **Use Case**: One-off tool calls, CLI integration
3. **Performance**: Adequate for non-real-time

This specification analysis shows that **SSE/HTTP transport is optimal for voice AI conversation** due to its real-time capabilities, while **STDIO remains valuable for simple tool calls**.