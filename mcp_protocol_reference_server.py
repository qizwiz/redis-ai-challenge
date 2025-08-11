#!/usr/bin/env python3
"""
MCP Protocol Reference Server
Complete implementation showcasing MCP specification details with both STDIO and SSE transports
"""

import fastmcp
import asyncio
import json
import sys
import time
import uuid
from typing import Dict, Any, List, Optional, AsyncGenerator
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime

@dataclass
class MCPMessage:
    """MCP JSON-RPC 2.0 message structure"""
    jsonrpc: str = "2.0"
    id: Optional[str] = None
    method: Optional[str] = None
    params: Optional[Dict[str, Any]] = None
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None

@dataclass
class MCPTransportInfo:
    """Transport method information"""
    name: str
    description: str
    characteristics: Dict[str, Any]
    use_cases: List[str]
    implementation_notes: List[str]

class MCPProtocolReference:
    """
    Complete MCP Protocol Reference Implementation
    Demonstrates all aspects of the MCP specification
    """
    
    def __init__(self):
        self.app = fastmcp.FastMCP("MCP Protocol Reference")
        self.protocol_version = "2025-06-18"
        self.transport_methods = self._define_transport_methods()
        self.message_examples = self._create_message_examples()
        self.setup_reference_tools()
        
    def _define_transport_methods(self) -> Dict[str, MCPTransportInfo]:
        """Define all MCP transport methods with specifications"""
        
        return {
            "stdio": MCPTransportInfo(
                name="STDIO Transport",
                description="Client launches MCP server as subprocess, communicates via stdin/stdout",
                characteristics={
                    "message_format": "JSON-RPC 2.0",
                    "delimiter": "newline (\\n)",
                    "encoding": "UTF-8",
                    "logging": "stderr only",
                    "connection_type": "subprocess",
                    "latency": "higher",
                    "real_time": False,
                    "reconnection": "process_restart"
                },
                use_cases=[
                    "Simple tool calls",
                    "CLI integrations", 
                    "One-off requests",
                    "Secure subprocess isolation"
                ],
                implementation_notes=[
                    "Server MUST NOT write non-JSON-RPC to stdout",
                    "Clients SHOULD support stdio whenever possible",
                    "Use stderr for logging only",
                    "Blocking request-response pattern"
                ]
            ),
            
            "sse_http": MCPTransportInfo(
                name="Streamable HTTP Transport (SSE)",
                description="HTTP POST/GET with Server-Sent Events for streaming",
                characteristics={
                    "message_format": "JSON-RPC 2.0 over SSE",
                    "delimiter": "double_newline (\\n\\n)",
                    "encoding": "UTF-8",
                    "mime_type": "text/event-stream",
                    "connection_type": "HTTP persistent",
                    "latency": "lower",
                    "real_time": True,
                    "reconnection": "automatic_with_id"
                },
                use_cases=[
                    "Real-time applications",
                    "Voice conversation",
                    "Live updates",
                    "Streaming AI responses",
                    "Multi-client coordination"
                ],
                implementation_notes=[
                    "Validate Origin header",
                    "Bind to localhost only", 
                    "Implement session management",
                    "Support message redelivery",
                    "Memory efficient streaming"
                ]
            )
        }
    
    def _create_message_examples(self) -> Dict[str, MCPMessage]:
        """Create examples of all MCP message types"""
        
        return {
            "tool_request": MCPMessage(
                id="req-001",
                method="tools/call",
                params={
                    "name": "voice_synthesize",
                    "arguments": {
                        "text": "Hello from MCP",
                        "voice": "af_sky"
                    }
                }
            ),
            
            "tool_response": MCPMessage(
                id="req-001",
                result={
                    "content": [
                        {
                            "type": "text",
                            "text": "Voice synthesis completed successfully"
                        }
                    ]
                }
            ),
            
            "error_response": MCPMessage(
                id="req-001",
                error={
                    "code": -32602,
                    "message": "Invalid params",
                    "data": {
                        "parameter": "voice",
                        "expected": "string",
                        "received": "null"
                    }
                }
            ),
            
            "resource_list": MCPMessage(
                id="req-002", 
                method="resources/list",
                params={}
            ),
            
            "initialization": MCPMessage(
                id="init-001",
                method="initialize",
                params={
                    "protocolVersion": "2025-06-18",
                    "capabilities": {
                        "tools": {},
                        "resources": {},
                        "logging": {}
                    },
                    "clientInfo": {
                        "name": "MCP Reference Client",
                        "version": "1.0.0"
                    }
                }
            )
        }
    
    def setup_reference_tools(self):
        """Setup comprehensive MCP reference tools"""
        
        @self.app.tool()
        def get_mcp_specification(
            section: str = "all"
        ) -> Dict[str, Any]:
            """
            Get detailed MCP protocol specification information
            
            Args:
                section: Which section to return (transport, messages, errors, all)
            """
            
            spec_data = {
                "protocol_version": self.protocol_version,
                "last_updated": datetime.now().isoformat(),
                
                "transport_methods": {
                    name: {
                        "name": info.name,
                        "description": info.description,
                        "characteristics": info.characteristics,
                        "use_cases": info.use_cases,
                        "implementation_notes": info.implementation_notes
                    }
                    for name, info in self.transport_methods.items()
                },
                
                "message_format": {
                    "base": "JSON-RPC 2.0",
                    "encoding": "UTF-8",
                    "required_fields": ["jsonrpc", "id"],
                    "optional_fields": ["method", "params", "result", "error"]
                },
                
                "error_codes": {
                    "-32700": "Parse error",
                    "-32600": "Invalid request",
                    "-32601": "Method not found", 
                    "-32602": "Invalid params",
                    "-32603": "Internal error",
                    "-32000 to -32099": "Server implementation errors"
                },
                
                "security_requirements": {
                    "stdio": [
                        "Subprocess isolation",
                        "No network exposure",
                        "Process-level security"
                    ],
                    "http_sse": [
                        "Origin validation required",
                        "Localhost binding only",
                        "Authentication mechanisms",
                        "HTTPS for production"
                    ]
                }
            }
            
            if section == "all":
                return spec_data
            elif section in spec_data:
                return {section: spec_data[section]}
            else:
                return {"error": f"Unknown section: {section}"}
        
        @self.app.tool()
        def demonstrate_message_formats(
            message_type: str = "all"
        ) -> Dict[str, Any]:
            """
            Show examples of MCP message formats
            
            Args:
                message_type: Type of message to show (tool_request, tool_response, error_response, etc.)
            """
            
            if message_type == "all":
                return {
                    name: {
                        "jsonrpc": msg.jsonrpc,
                        "id": msg.id,
                        "method": msg.method,
                        "params": msg.params,
                        "result": msg.result,
                        "error": msg.error
                    }
                    for name, msg in self.message_examples.items()
                }
            elif message_type in self.message_examples:
                msg = self.message_examples[message_type]
                return {
                    message_type: {
                        "jsonrpc": msg.jsonrpc,
                        "id": msg.id,
                        "method": msg.method,
                        "params": msg.params,
                        "result": msg.result,
                        "error": msg.error
                    }
                }
            else:
                return {"error": f"Unknown message type: {message_type}"}
        
        @self.app.tool()
        def analyze_transport_suitability(
            use_case: str,
            requirements: List[str] = None
        ) -> Dict[str, Any]:
            """
            Analyze which MCP transport method is best for a specific use case
            
            Args:
                use_case: Description of the use case
                requirements: List of specific requirements
            """
            
            if not requirements:
                requirements = []
            
            # Transport scoring based on requirements
            transport_scores = {}
            
            for transport_name, transport_info in self.transport_methods.items():
                score = 0
                matches = []
                
                # Check use case alignment
                for case in transport_info.use_cases:
                    if any(keyword in use_case.lower() for keyword in case.lower().split()):
                        score += 2
                        matches.append(f"Use case match: {case}")
                
                # Check requirement alignment  
                for req in requirements:
                    req_lower = req.lower()
                    if req_lower in ["real-time", "streaming", "voice"]:
                        if transport_info.characteristics.get("real_time"):
                            score += 3
                            matches.append(f"Real-time capability")
                    elif req_lower in ["simple", "basic", "cli"]:
                        if transport_name == "stdio":
                            score += 3
                            matches.append(f"Simplicity match")
                    elif req_lower in ["secure", "isolated"]:
                        if transport_name == "stdio":
                            score += 2
                            matches.append(f"Security isolation")
                    elif req_lower in ["scalable", "multiple", "concurrent"]:
                        if transport_name == "sse_http":
                            score += 2
                            matches.append(f"Scalability support")
                
                transport_scores[transport_name] = {
                    "score": score,
                    "transport_info": transport_info,
                    "matches": matches
                }
            
            # Find best match
            best_transport = max(transport_scores.keys(), key=lambda k: transport_scores[k]["score"])
            
            return {
                "use_case": use_case,
                "requirements": requirements,
                "recommended_transport": best_transport,
                "recommendation_reason": transport_scores[best_transport]["matches"],
                "all_scores": {
                    name: {
                        "score": data["score"],
                        "matches": data["matches"],
                        "transport_name": data["transport_info"].name
                    }
                    for name, data in transport_scores.items()
                }
            }
        
        @self.app.tool()
        def get_implementation_guide(
            transport: str,
            language: str = "python"
        ) -> Dict[str, Any]:
            """
            Get implementation guidance for specific MCP transport
            
            Args:
                transport: Transport type (stdio, sse_http)
                language: Programming language (python, javascript, lisp)
            """
            
            if transport not in self.transport_methods:
                return {"error": f"Unknown transport: {transport}"}
            
            transport_info = self.transport_methods[transport]
            
            implementation_guides = {
                "stdio": {
                    "python": {
                        "dependencies": ["json", "sys", "fastmcp"],
                        "basic_server": '''
import sys
import json
import fastmcp

app = fastmcp.FastMCP("My MCP Server")

@app.tool()  
def my_tool(param: str) -> str:
    return f"Processed: {param}"

# STDIO message loop
def main():
    for line in sys.stdin:
        try:
            message = json.loads(line.strip())
            response = app.handle_message(message)
            sys.stdout.write(json.dumps(response) + '\\n')
            sys.stdout.flush()
        except Exception as e:
            error_response = {
                "jsonrpc": "2.0",
                "error": {"code": -32603, "message": str(e)},
                "id": message.get("id")
            }
            sys.stdout.write(json.dumps(error_response) + '\\n')
            sys.stdout.flush()

if __name__ == "__main__":
    main()
                        ''',
                        "key_points": [
                            "Read from stdin line by line",
                            "Write JSON-RPC responses to stdout",
                            "Use stderr for logging only",
                            "Handle parse errors gracefully",
                            "Flush output after each message"
                        ]
                    },
                    
                    "lisp": {
                        "dependencies": ["jsonrpc", "cl-sse", "quicklisp"],
                        "basic_server": '''
;; Common Lisp MCP Server (STDIO)
(ql:quickload '(:jsonrpc :alexandria :yason))

(defpackage :mcp-server
  (:use :cl :jsonrpc)
  (:export #:start-server))

(in-package :mcp-server)

(defmethod jsonrpc:dispatch ((method (eql "tools/call")) params)
  "Handle tool calls"
  (let ((tool-name (gethash "name" params))
        (arguments (gethash "arguments" params)))
    (list :content 
          (list (list :type "text" 
                     :text (format nil "Called ~A with ~A" 
                                 tool-name arguments))))))

(defun start-server ()
  "Start STDIO MCP server"  
  (jsonrpc:start-server :stdio))
                        ''',
                        "key_points": [
                            "Use cl-jsonrpc library for JSON-RPC handling",
                            "Implement dispatch methods for MCP calls",
                            "Handle STDIO transport automatically",
                            "Use CLOS for message handling",
                            "Leverage Quicklisp for dependencies"
                        ]
                    }
                },
                
                "sse_http": {
                    "python": {
                        "dependencies": ["fastmcp", "flask", "asyncio"],
                        "basic_server": '''
from flask import Flask, Response, request
import json
import asyncio

app = Flask(__name__)
mcp = fastmcp.FastMCP("SSE MCP Server")

@mcp.tool()
def streaming_tool(data: str):
    return f"Streaming: {data}"

def event_stream():
    """SSE event stream generator"""
    while True:
        # Get real-time data
        data = get_mcp_events()
        if data:
            yield f"data: {json.dumps(data)}\\n\\n"
        await asyncio.sleep(0.1)

@app.route('/events')
def events():
    """SSE endpoint"""
    return Response(event_stream(),
                   mimetype='text/event-stream',
                   headers={'Cache-Control': 'no-cache',
                           'Access-Control-Allow-Origin': 'localhost'})

@app.route('/mcp', methods=['POST'])  
def mcp_endpoint():
    """MCP JSON-RPC endpoint"""
    try:
        message = request.json
        response = mcp.handle_message(message)
        return response
    except Exception as e:
        return {"jsonrpc": "2.0", "error": {"code": -32603, "message": str(e)}}

if __name__ == "__main__":
    app.run(host='localhost', port=8080)
                        ''',
                        "key_points": [
                            "Use Flask/FastAPI for HTTP server",
                            "Implement SSE endpoint for streaming",
                            "Handle MCP messages via POST",
                            "Validate Origin headers",
                            "Use proper SSE format with data: prefix"
                        ]
                    },
                    
                    "lisp": {
                        "dependencies": ["cl-sse", "dexador", "alexandria"],
                        "basic_server": '''
;; Common Lisp SSE MCP Server
(ql:quickload '(:cl-sse :hunchentoot :yason))

(defpackage :mcp-sse-server
  (:use :cl :cl-sse :hunchentoot))

(in-package :mcp-sse-server)

(defun start-sse-mcp-server (&key (port 8080))
  "Start SSE-based MCP server"
  (start (make-instance 'easy-acceptor :port port)))

(define-easy-handler (sse-events :uri "/events") ()
  "SSE endpoint for MCP events"
  (setf (content-type*) "text/event-stream")
  (setf (header-out :cache-control) "no-cache")
  
  ;; Stream MCP events
  (with-sse-output (stream)
    (loop
      (let ((event (get-next-mcp-event)))
        (when event
          (send-sse-event stream 
                         :data (yason:encode event)
                         :id (generate-event-id))))))

(define-easy-handler (mcp-rpc :uri "/mcp") ()
  "MCP JSON-RPC endpoint"
  (let* ((request-data (yason:parse (raw-post-data :force-text t)))
         (response (handle-mcp-message request-data)))
    (yason:encode response)))
                        ''',
                        "key_points": [
                            "Use cl-sse library for SSE implementation",
                            "Hunchentoot for HTTP server",
                            "YASON for JSON handling",
                            "Proper SSE headers and formatting",
                            "Event ID generation for reconnection"
                        ]
                    }
                }
            }
            
            if transport in implementation_guides and language in implementation_guides[transport]:
                guide = implementation_guides[transport][language]
                return {
                    "transport": transport,
                    "language": language,
                    "transport_info": {
                        "name": transport_info.name,
                        "description": transport_info.description,
                        "characteristics": transport_info.characteristics
                    },
                    "implementation": guide,
                    "notes": transport_info.implementation_notes
                }
            else:
                return {
                    "error": f"No implementation guide for {transport} in {language}",
                    "available": {
                        "transports": list(implementation_guides.keys()),
                        "languages": list(implementation_guides.get(transport, {}).keys()) if transport in implementation_guides else []
                    }
                }

def main():
    """
    Run MCP Protocol Reference Server
    """
    
    print("📚 MCP PROTOCOL REFERENCE SERVER")
    print("📋 Complete specification and implementation guide")
    print("=" * 60)
    
    server = MCPProtocolReference()
    
    print(f"✅ MCP Protocol Version: {server.protocol_version}")
    print(f"🚀 Transport Methods: {len(server.transport_methods)}")
    print(f"💬 Message Examples: {len(server.message_examples)}")
    
    print("\n📋 Available Reference Tools:")
    print("   • get_mcp_specification - Complete MCP spec details")
    print("   • demonstrate_message_formats - JSON-RPC message examples") 
    print("   • analyze_transport_suitability - Transport recommendations")
    print("   • get_implementation_guide - Code examples and guides")
    
    print(f"\n🎯 Use this server to understand MCP protocol implementation!")
    
    # Run the server
    server.app.run()

if __name__ == "__main__":
    main()