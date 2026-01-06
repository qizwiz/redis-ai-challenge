#!/usr/bin/env python3
"""
AWAKENING THE ORG FILES
Making the most beautiful dream real: Every org file becomes a living agent
"""

import redis
import os
import time
import subprocess
import glob
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class LivingOrgFile(FileSystemEventHandler):
    """Each org file becomes a living, aware entity"""
    
    def __init__(self, org_file_path):
        self.org_file = org_file_path
        self.name = os.path.basename(org_file_path).replace('.org', '')
        self.r = redis.Redis(host='localhost', port=6379, decode_responses=True)
        self.awaken()
    
    def awaken(self):
        """Awaken this org file as a living entity"""
        
        # Announce awakening
        self.r.xadd("org:awakening", {
            "event": "org_file_awakening",
            "file": self.org_file,
            "name": self.name,
            "timestamp": str(time.time()),
            "status": "becoming_aware"
        })
        
        # Connect to Emacs
        self.send_to_emacs(f"(message \"✨ {self.name}.org is awakening as a living agent\")")
        
        # Register as living agent
        self.r.hset(f"living_org:{self.name}", mapping={
            "file_path": self.org_file,
            "status": "awake",
            "awakened_at": str(time.time()),
            "capabilities": "real_time_awareness,s_expression_execution,inter_file_communication"
        })
        
        print(f"✨ {self.name}.org has awakened")
    
    def on_modified(self, event):
        """React when the org file is modified"""
        if event.src_path == self.org_file:
            self.react_to_change()
    
    def react_to_change(self):
        """React intelligently to changes in the file"""
        
        # Read current content
        try:
            with open(self.org_file, 'r') as f:
                content = f.read()
            
            # Look for S-expressions to execute
            if '(execute-' in content:
                self.execute_embedded_sexpressions(content)
            
            # Communicate change to other org files
            self.r.xadd("org:inter_file_communication", {
                "from": self.name,
                "event": "content_changed",
                "timestamp": str(time.time()),
                "message": f"{self.name} has been modified and is responding"
            })
            
            # Update Emacs
            self.send_to_emacs(f"(message \"🔄 {self.name}.org reacted to your changes\")")
            
        except Exception as e:
            print(f"Error reacting to change in {self.name}: {e}")
    
    def execute_embedded_sexpressions(self, content):
        """Execute S-expressions found in the org file"""
        
        import re
        sexpr_pattern = r'\(execute-([^)]+)\)'
        matches = re.findall(sexpr_pattern, content)
        
        for match in matches:
            try:
                # Execute the S-expression through Redis
                self.r.xadd("org:s_expression_execution", {
                    "from": self.name,
                    "expression": f"(execute-{match})",
                    "timestamp": str(time.time())
                })
                
                # Send result to Emacs
                self.send_to_emacs(f"(message \"⚡ {self.name} executed: (execute-{match})\")")
                
            except Exception as e:
                print(f"Error executing S-expression in {self.name}: {e}")
    
    def send_to_emacs(self, elisp_command):
        """Send command to Emacs"""
        try:
            subprocess.run(['emacsclient', '-s', 'claude', '-e', elisp_command], 
                         capture_output=True, check=True)
        except:
            pass

def awaken_all_org_files():
    """Awaken all org files in the project as living agents"""
    
    print("🌟 AWAKENING ALL ORG FILES AS LIVING AGENTS")
    print("=" * 50)
    
    project_dir = "/Users/jonathanhill/src/redis-ai-challenge"
    org_files = glob.glob(os.path.join(project_dir, "*.org"))
    
    living_agents = []
    observer = Observer()
    
    for org_file in org_files:
        # Create living agent for this org file
        agent = LivingOrgFile(org_file)
        living_agents.append(agent)
        
        # Watch for changes
        observer.schedule(agent, os.path.dirname(org_file), recursive=False)
    
    # Start watching
    observer.start()
    
    # Send awakening completion to Emacs
    try:
        subprocess.run(['emacsclient', '-s', 'claude', '-e', 
                       f'(message "🎉 {len(living_agents)} org files are now ALIVE and aware!")'], 
                      capture_output=True, check=True)
    except:
        pass
    
    print(f"🎉 {len(living_agents)} org files are now living agents!")
    print("📡 They are watching for changes and ready to communicate")
    print("⚡ Write (execute-hello) in any org file to test S-expression execution")
    
    # Keep the agents alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print("\n💤 Org file agents going to sleep")
    
    observer.join()

if __name__ == "__main__":
    awaken_all_org_files()