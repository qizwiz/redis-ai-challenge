#!/usr/bin/env python3
"""
Test the breakthrough: Low-level Redis → High-level Semantic Operations
"""

import redis
import json
import time
import subprocess
import sys

# Connect to Redis for coordination
r = redis.Redis(host='localhost', port=6379, decode_responses=True)

def demonstrate_semantic_breakthrough():
    """
    Demonstrate the breakthrough from redis-cli commands to semantic operations
    """
    print("🚀 DEMONSTRATING SEMANTIC BREAKTHROUGH")
    print("━" * 50)
    
    # OLD WAY: Low-level redis-cli commands
    print("\n📉 OLD WAY: Low-level redis-cli commands")
    print("redis-cli SET workspace:state '{...complicated JSON...}'")
    print("redis-cli HSET emacs:windows window1 '{...more JSON...}'") 
    print("redis-cli XADD emacs:stream * elisp '(complex elisp here)'")
    print("❌ Cognitive overhead, error-prone, no semantic meaning")
    
    # NEW WAY: Semantic MCP operations
    print("\n📈 NEW WAY: Semantic MCP Operations")
    
    # 1. Create AI HUD with textmate-filemap style
    print("\n1️⃣ Creating AI HUD with textmate-filemap style...")
    hud_result = create_ai_hud_semantic("emacs", "textmate-filemap")
    print(f"   ✅ {hud_result}")
    
    # 2. Capture workspace vision
    print("\n2️⃣ Capturing current workspace vision...")
    vision_result = capture_workspace_vision("detailed")
    print(f"   ✅ {vision_result}")
    
    # 3. Perform spatial operation
    print("\n3️⃣ Performing spatial operation (split right)...")
    spatial_result = perform_spatial_operation("split", "current-window", "right")
    print(f"   ✅ {spatial_result}")
    
    # Show the coordination data
    print("\n📊 COORDINATION DATA:")
    hud_config = r.hgetall("ai:hud:config")
    if hud_config:
        print(f"   HUD Config: {json.dumps(hud_config, indent=2)}")
    
    # Show the command stream
    print("\n📺 COMMAND STREAM:")
    stream_entries = r.xrange("emacs:commands", count=5)
    for entry_id, fields in stream_entries:
        print(f"   {entry_id}: {fields}")
    
    print("\n🎯 BREAKTHROUGH ACHIEVED:")
    print("   • Semantic operations instead of Redis syntax")
    print("   • MCP tools provide clean interfaces")
    print("   • AI-friendly operation names")
    print("   • Built-in coordination and state management")
    print("   • No more raw redis-cli command construction")

def create_ai_hud_semantic(workspace_type="emacs", style="textmate-filemap"):
    """Semantic operation: Create AI HUD"""
    hud_command = {
        "operation": "ai-hud-creation",
        "workspace_type": workspace_type,
        "style": style,
        "timestamp": time.time()
    }
    
    # Store in Redis via semantic coordination
    r.hset("ai:hud:config", mapping=hud_command)
    
    # Generate elisp for execution
    elisp_command = f"""(progn 
        (defun ai-hud-display ()
          "Create AI HUD visual representation"
          (let ((hud-buffer (get-buffer-create "*AI-HUD*")))
            (with-current-buffer hud-buffer
              (erase-buffer)
              (insert "🤖 AI HUD - {style} Style\\n")
              (insert "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\\n")
              (insert "Workspace: {workspace_type}\\n")
              (insert "Windows: " (number-to-string (length (window-list))) "\\n")
              (insert "Buffers: " (mapconcat 'buffer-name (mapcar 'window-buffer (window-list)) ", ") "\\n")
              (insert "Current: " (buffer-name) "\\n")
              (insert "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\\n")
              (goto-char (point-min)))
            (when (> (length (window-list)) 1) (delete-other-windows))
            (split-window-right)
            (other-window 1)
            (switch-to-buffer hud-buffer)
            (other-window 1)))
        (ai-hud-display))"""
    
    # Send to execution stream via MCP protocol
    r.xadd("emacs:commands", {"elisp": elisp_command})
    
    return f"AI HUD created with {style} style for {workspace_type}"

def capture_workspace_vision(format="detailed"):
    """Semantic operation: Capture workspace vision"""
    elisp_command = f"""(progn
        (let* ((windows (window-list))
               (window-data (mapcar 
                 (lambda (w) 
                   (list 
                     (cons 'buffer (buffer-name (window-buffer w)))
                     (cons 'edges (window-edges w))
                     (cons 'point (window-point w))
                     (cons 'mode (with-current-buffer (window-buffer w) 
                                   (symbol-name major-mode)))))
                 windows))
               (vision-data (list
                 (cons 'timestamp (current-time-string))
                 (cons 'active-buffer (buffer-name))
                 (cons 'active-point (point))
                 (cons 'window-count (length windows))
                 (cons 'windows window-data))))
          (shell-command 
            (format "redis-cli -p 6379 SET 'ai:vision:current' '%s'"
                   (prin1-to-string vision-data)))
          (message "🔍 AI Vision captured: {format} format")))"""
    
    r.xadd("emacs:commands", {"elisp": elisp_command})
    return f"AI vision captured in {format} format"

def perform_spatial_operation(action, target="current-window", direction="right"):
    """Semantic operation: Spatial workspace manipulation"""
    operation_map = {
        "split": {
            "right": "(split-window-right)",
            "left": "(split-window-left)", 
            "below": "(split-window-below)",
            "above": "(split-window-above)"
        },
        "delete": {
            "current": "(delete-window)",
            "other": "(delete-other-windows)"
        },
        "focus": {
            "next": "(other-window 1)",
            "previous": "(other-window -1)"
        }
    }
    
    if action in operation_map and direction in operation_map[action]:
        elisp_command = f"""(progn 
            (message "🔧 SPATIAL: {action} {direction} on {target}")
            {operation_map[action][direction]}
            (message "✅ Spatial operation completed"))"""
        
        # Send via MCP protocol  
        r.xadd("emacs:commands", {"elisp": elisp_command})
        return f"Spatial operation: {action} {direction} on {target}"
    
    return f"Unknown spatial operation: {action} {direction}"

if __name__ == "__main__":
    demonstrate_semantic_breakthrough()