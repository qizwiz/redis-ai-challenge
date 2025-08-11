#!/usr/bin/env python3
"""
MCP Autonomous Pair Programming Server

This MCP server continuously monitors Redis streams for coding activity
and provides AI assistance through Claude Code MCP integration.
"""

import asyncio
import json
import threading
import time
from typing import Dict, List, Any
import redis
import subprocess
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

class AutonomousPairServer:
    """MCP server that autonomously monitors coding activity"""
    
    def __init__(self):
        self.redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
        self.monitoring = False
        self.activity_log = []
        self.suggestions = []
        
    def start_monitoring(self):
        """Start autonomous monitoring in background thread"""
        if self.monitoring:
            return "Already monitoring"
            
        self.monitoring = True
        monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        monitor_thread.start()
        return "✅ Autonomous monitoring started"
        
    def stop_monitoring(self):
        """Stop autonomous monitoring"""
        self.monitoring = False
        return "⏹️ Autonomous monitoring stopped"
        
    def _monitor_loop(self):
        """Background monitoring loop - watches Redis streams"""
        last_id = '$'  # Start from newest events
        
        while self.monitoring:
            try:
                # Read new events from Redis stream
                events = self.redis_client.xread(
                    {'ai:pair_programming': last_id}, 
                    block=1000, 
                    count=5
                )
                
                for stream, messages in events:
                    for message_id, fields in messages:
                        last_id = message_id
                        self._process_coding_activity(message_id, fields)
                        
            except Exception as e:
                # Log errors to activity log instead of stdout (MCP requirement)
                self.activity_log.append(f"Monitor error: {str(e)}")
                time.sleep(1)
                
    def _process_coding_activity(self, message_id: str, fields: Dict):
        """Process coding activity and generate suggestions"""
        event_type = fields.get('event', 'unknown')
        session = fields.get('session', 'unknown')
        
        # Log the activity
        activity = {
            'timestamp': time.time(),
            'event_type': event_type,
            'session': session,
            'message_id': message_id
        }
        
        if event_type == 'keystroke':
            command = fields.get('command', 'unknown')
            point = fields.get('point', '0')
            
            activity.update({
                'command': command,
                'position': point
            })
            
            # Generate contextual suggestions
            suggestion = self._generate_suggestion(command, point, session)
            if suggestion:
                self.suggestions.append({
                    'timestamp': time.time(),
                    'suggestion': suggestion,
                    'context': f"{command} at {point}"
                })
                
                # Store suggestion in Redis for Emacs to pick up
                self.redis_client.xadd('ai:suggestions', {
                    'suggestion': suggestion,
                    'session': session,
                    'timestamp': str(time.time())
                })
        
        # Keep logs manageable
        self.activity_log.append(activity)
        if len(self.activity_log) > 100:
            self.activity_log.pop(0)
            
        if len(self.suggestions) > 50:
            self.suggestions.pop(0)
            
    def _generate_suggestion(self, command: str, position: str, session: str) -> str:
        """Generate contextual coding suggestions"""
        suggestions = {
            'newline': "💡 Good time to add a comment explaining the logic",
            'yank': "📋 Consider checking what you just pasted for formatting",
            'kill-line': "✂️ Deleted code - might want to save important parts",
            'save-buffer': "💾 File saved! Consider running tests or linting",
            'beginning-of-line': "⬅️ At line start - good place for indentation check",
            'forward-paragraph': "📄 Navigating code blocks - reviewing structure?",
            'backward-paragraph': "🔙 Looking back at previous code sections"
        }
        
        return suggestions.get(command, None)
        
    def get_activity_summary(self) -> Dict:
        """Get summary of recent coding activity"""
        if not self.activity_log:
            return {"message": "No activity recorded yet"}
            
        recent_activity = self.activity_log[-10:]  # Last 10 events
        command_counts = {}
        
        for activity in self.activity_log:
            if activity.get('command'):
                cmd = activity['command']
                command_counts[cmd] = command_counts.get(cmd, 0) + 1
        
        return {
            'monitoring': self.monitoring,
            'total_events': len(self.activity_log),
            'recent_events': len(recent_activity),
            'most_common_commands': sorted(command_counts.items(), 
                                         key=lambda x: x[1], reverse=True)[:5],
            'recent_suggestions': len(self.suggestions),
            'last_activity': recent_activity[-1] if recent_activity else None
        }
        
    def get_suggestions(self) -> List[Dict]:
        """Get recent AI suggestions"""
        return self.suggestions[-10:]  # Last 10 suggestions

# Create MCP server instance
server = Server("autonomous-pair-programming")
pair_server = AutonomousPairServer()

@server.list_tools()
async def list_tools() -> List[Tool]:
    """List available autonomous pair programming tools"""
    return [
        Tool(
            name="start_autonomous_monitoring",
            description="Start autonomous monitoring of coding activity",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="stop_autonomous_monitoring", 
            description="Stop autonomous monitoring",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get_coding_activity",
            description="Get summary of recent coding activity and AI suggestions",
            inputSchema={
                "type": "object", 
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get_ai_suggestions",
            description="Get recent AI coding suggestions",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> List[TextContent]:
    """Handle tool calls for autonomous pair programming"""
    
    if name == "start_autonomous_monitoring":
        result = pair_server.start_monitoring()
        return [TextContent(type="text", text=result)]
        
    elif name == "stop_autonomous_monitoring":
        result = pair_server.stop_monitoring()
        return [TextContent(type="text", text=result)]
        
    elif name == "get_coding_activity":
        summary = pair_server.get_activity_summary()
        activity_text = f"""🤖 Autonomous Pair Programming Activity Summary:

📊 Monitoring Status: {'ACTIVE' if summary['monitoring'] else 'STOPPED'}
📈 Total Events Captured: {summary['total_events']}
🔄 Recent Events: {summary['recent_events']}
💡 AI Suggestions Generated: {summary['recent_suggestions']}

🔥 Most Common Commands:
"""
        
        for cmd, count in summary.get('most_common_commands', []):
            activity_text += f"   • {cmd}: {count} times\\n"
            
        if summary.get('last_activity'):
            last = summary['last_activity']
            activity_text += f"\\n🕐 Last Activity: {last.get('event_type', 'unknown')} "
            activity_text += f"({last.get('command', 'N/A')}) at {last.get('timestamp', 'unknown')}"
            
        return [TextContent(type="text", text=activity_text)]
        
    elif name == "get_ai_suggestions":
        suggestions = pair_server.get_suggestions()
        
        if not suggestions:
            return [TextContent(type="text", text="💭 No recent AI suggestions available")]
            
        suggestions_text = "🤖 Recent AI Coding Suggestions:\\n\\n"
        
        for i, suggestion in enumerate(suggestions, 1):
            timestamp = suggestion.get('timestamp', 0)
            time_str = time.strftime('%H:%M:%S', time.localtime(timestamp))
            suggestions_text += f"{i}. [{time_str}] {suggestion.get('suggestion', 'No suggestion')}\\n"
            suggestions_text += f"   Context: {suggestion.get('context', 'No context')}\\n\\n"
            
        return [TextContent(type="text", text=suggestions_text)]
        
    else:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]

async def main():
    """Run the MCP server"""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())