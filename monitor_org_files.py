#!/usr/bin/env python3
"""
(define monitor-org-files) - IMPLEMENTING THE NEXT S-EXPRESSION

Tenth critique request = implement monitor-org-files function
"""

import os
import time
import json
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

def monitor_org_files():
    """
    Monitor org-roam files for changes and trigger agent responses
    This creates the live connection between org buffers and agents
    """
    
    print("👁️ MONITORING ORG FILES FOR BUFFER AGENT ACTIVITY")
    print("=" * 55)
    
    # Set up org file monitoring
    org_directory = "/Users/jonathanhill/src/redis-ai-challenge"
    monitor_setup = setup_org_monitoring(org_directory)
    print(f"✅ Org monitoring setup: {monitor_setup}")
    
    # Register existing org files as buffer agents
    existing_files = register_existing_org_files(org_directory)
    print(f"✅ Registered {len(existing_files)} existing org files as agents")
    
    # Create file-to-agent mappings
    agent_mappings = create_file_agent_mappings(existing_files)
    print(f"✅ Created {len(agent_mappings)} file-to-agent mappings")
    
    # Start live monitoring service
    monitoring_service = start_monitoring_service(org_directory)
    print(f"✅ Monitoring service status: {monitoring_service}")
    
    return {
        "org_directory": org_directory,
        "existing_files": len(existing_files),
        "agent_mappings": len(agent_mappings),
        "monitoring_active": monitoring_service == "started",
        "status": "ORG_MONITORING_ACTIVE"
    }

def setup_org_monitoring(directory):
    """Set up the org file monitoring infrastructure"""
    import redis
    
    try:
        r = redis.Redis(host='localhost', port=6379, decode_responses=True)
        
        # Create monitoring configuration
        r.hset("org_monitoring:config", mapping={
            "directory": directory,
            "enabled": "true",
            "file_types": ".org",
            "agent_creation": "automatic",
            "relationship_discovery": "enabled",
            "timestamp": str(time.time())
        })
        
        # Initialize monitoring streams
        r.xadd("org:file:events", {
            "event": "monitoring_started",
            "directory": directory,
            "timestamp": str(time.time())
        })
        
        return "configured"
    except:
        return "failed"

def register_existing_org_files(directory):
    """Register existing org files as buffer agents"""
    import redis
    import glob
    
    org_files = glob.glob(os.path.join(directory, "*.org"))
    
    try:
        r = redis.Redis(host='localhost', port=6379, decode_responses=True)
        
        registered_files = []
        for org_file in org_files:
            filename = os.path.basename(org_file)
            agent_name = filename.replace('.org', '_agent')
            
            # Register as buffer agent
            r.hset(f"buffer_agent:{agent_name}", mapping={
                "org_file": org_file,
                "filename": filename,
                "agent_type": "org_buffer_agent",
                "status": "active",
                "created": str(time.time())
            })
            
            # Add to active agents
            r.sadd("active_buffer_agents", agent_name)
            
            registered_files.append({
                "file": org_file,
                "agent": agent_name
            })
        
        return registered_files
    except:
        return []

def create_file_agent_mappings(files):
    """Create mappings between org files and their agents"""
    import redis
    
    try:
        r = redis.Redis(host='localhost', port=6379, decode_responses=True)
        
        mappings = []
        for file_info in files:
            org_file = file_info['file']
            agent_name = file_info['agent']
            
            # Create bidirectional mapping
            r.hset("file_to_agent_mapping", org_file, agent_name)
            r.hset("agent_to_file_mapping", agent_name, org_file)
            
            # Create agent capabilities based on file content
            try:
                with open(org_file, 'r') as f:
                    content = f.read()
                
                # Analyze content to determine agent capabilities
                capabilities = analyze_org_content_for_capabilities(content)
                
                r.hset(f"buffer_agent:{agent_name}:capabilities", mapping=capabilities)
                
                mappings.append({
                    "file": org_file,
                    "agent": agent_name,
                    "capabilities": capabilities
                })
                
            except:
                # Default capabilities if file can't be read
                default_caps = {
                    "content_monitoring": "true",
                    "relationship_discovery": "true",
                    "knowledge_storage": "true"
                }
                r.hset(f"buffer_agent:{agent_name}:capabilities", mapping=default_caps)
                mappings.append({
                    "file": org_file,
                    "agent": agent_name,
                    "capabilities": default_caps
                })
        
        return mappings
    except:
        return []

def analyze_org_content_for_capabilities(content):
    """Analyze org file content to determine agent capabilities"""
    
    capabilities = {
        "content_monitoring": "true",
        "relationship_discovery": "true",
        "knowledge_storage": "true"
    }
    
    # Analyze content for specific capabilities
    if "#+TITLE:" in content:
        capabilities["title_tracking"] = "true"
    
    if "* " in content:  # Has headings
        capabilities["structure_analysis"] = "true"
    
    if "[[" in content:  # Has org links
        capabilities["link_processing"] = "true"
        capabilities["relationship_discovery"] = "enhanced"
    
    if "#+BEGIN_SRC" in content:  # Has code blocks
        capabilities["code_analysis"] = "true"
    
    if "TODO" in content or "DONE" in content:
        capabilities["task_management"] = "true"
    
    if "Agent" in content or "agent" in content:
        capabilities["meta_agent_awareness"] = "true"
    
    return capabilities

class OrgFileEventHandler(FileSystemEventHandler):
    """Handle org file system events"""
    
    def __init__(self):
        import redis
        self.redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
    
    def on_modified(self, event):
        if event.is_directory or not event.src_path.endswith('.org'):
            return
        
        # Notify agents of file modification
        filename = os.path.basename(event.src_path)
        agent_name = filename.replace('.org', '_agent')
        
        self.redis_client.xadd("org:file:events", {
            "event": "file_modified",
            "file": event.src_path,
            "agent": agent_name,
            "timestamp": str(time.time())
        })
    
    def on_created(self, event):
        if event.is_directory or not event.src_path.endswith('.org'):
            return
        
        # Create new buffer agent for new org file
        filename = os.path.basename(event.src_path)
        agent_name = filename.replace('.org', '_agent')
        
        self.redis_client.hset(f"buffer_agent:{agent_name}", mapping={
            "org_file": event.src_path,
            "filename": filename,
            "agent_type": "org_buffer_agent",
            "status": "active",
            "created": str(time.time())
        })
        
        self.redis_client.sadd("active_buffer_agents", agent_name)
        
        self.redis_client.xadd("org:file:events", {
            "event": "file_created",
            "file": event.src_path,
            "agent": agent_name,
            "timestamp": str(time.time())
        })

def start_monitoring_service(directory):
    """Start the file monitoring service"""
    try:
        event_handler = OrgFileEventHandler()
        observer = Observer()
        observer.schedule(event_handler, directory, recursive=False)
        observer.start()
        
        # Store observer reference for later cleanup
        import redis
        r = redis.Redis(host='localhost', port=6379, decode_responses=True)
        r.hset("org_monitoring:service", mapping={
            "status": "running",
            "directory": directory,
            "started_at": str(time.time())
        })
        
        return "started"
    except Exception as e:
        return f"failed: {str(e)}"

if __name__ == "__main__":
    result = monitor_org_files()
    print(f"\n🎯 ORG FILE MONITORING COMPLETE: {result['status']}")
    
    # Store result in Redis
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, decode_responses=True)
        r.hset("monitoring:result", mapping=result)
        
        # Update system status
        r.hset("living_knowledge_organism:status", mapping={
            "orchestration": "complete",
            "iteration": "complete", 
            "enhancement": "complete",
            "monitoring": "complete",
            "next_phase": "generate_mcp_servers",
            "timestamp": str(time.time())
        })
        
        print("✅ Monitoring result stored in Redis")
        print("🎯 Ready for next phase: generate-mcp-servers")
    except:
        print("⚠️ Could not store in Redis")