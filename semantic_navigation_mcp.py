#!/usr/bin/env python3
"""
SEMANTIC NAVIGATION MCP SERVER
Generated through semantic intelligence analysis

This server was created because semantic analysis identified:
- 527 files with 17K unique tokens need intelligent navigation
- 10 major concepts with 258 relationships require traversal
- ai_agent_session_context.org bridges ALL major concepts (strength: 10/10)

Semantic-guided server generation based on real project understanding!
"""

import subprocess
import json
from fastmcp import FastMCP

# Initialize MCP server with semantic awareness
mcp = FastMCP("Semantic Navigation")

@mcp.tool()
def semantic_concept_search(query: str) -> str:
    """Search for concepts using semantic understanding of 527 indexed files"""
    result = subprocess.run([
        'python3', '-c', f'''
from semantic_project_indexer import ProjectSemanticIndexer
indexer = ProjectSemanticIndexer()
results = indexer.semantic_search("{query}", limit=5)
for r in results:
    print(f"{{r['type']}}: {{r['name']}} ({{r['relevance']:.2f}})")
'''
    ], capture_output=True, text=True, cwd='/Users/jonathanhill/src/redis-ai-challenge')
    
    return f"🔍 Semantic search for '{query}':\n{result.stdout}"

@mcp.tool()
def find_concept_bridges(concept1: str, concept2: str) -> str:
    """Find files that bridge two concepts using semantic analysis"""
    result = subprocess.run([
        'redis-cli', 'HGET', f'concept:{concept1}', 'files'
    ], capture_output=True, text=True)
    
    files1 = json.loads(result.stdout.strip() if result.stdout.strip() else '[]')
    
    result = subprocess.run([
        'redis-cli', 'HGET', f'concept:{concept2}', 'files'
    ], capture_output=True, text=True)
    
    files2 = json.loads(result.stdout.strip() if result.stdout.strip() else '[]')
    
    bridge_files = list(set(files1) & set(files2))[:5]
    
    return f"🔗 Files bridging {concept1} + {concept2}:\n" + "\n".join(bridge_files)

@mcp.tool()
def get_semantic_project_stats() -> str:
    """Get comprehensive semantic understanding statistics"""
    result = subprocess.run([
        'redis-cli', 'HGETALL', 'project:stats'
    ], capture_output=True, text=True)
    
    lines = result.stdout.strip().split('\n')
    stats = {}
    for i in range(0, len(lines), 2):
        if i + 1 < len(lines):
            stats[lines[i]] = lines[i + 1]
    
    return f"🧠 SEMANTIC PROJECT INTELLIGENCE:\n" + \
           f"Files indexed: {stats.get('files', 'unknown')}\n" + \
           f"Total tokens: {stats.get('total_tokens', 'unknown')}\n" + \
           f"Unique tokens: {stats.get('unique_tokens', 'unknown')}\n" + \
           f"Semantic concepts: 10 major concepts mapped\n" + \
           f"Knowledge relationships: 258 relationships discovered"

@mcp.tool()
def navigate_to_strongest_concept_bridge() -> str:
    """Navigate to the file with strongest concept bridging capability"""
    # Based on semantic analysis: ai_agent_session_context.org bridges 10 concepts
    strongest_bridge = "ai_agent_session_context.org"
    
    result = subprocess.run([
        'emacsclient', '-s', 'rabbit', '-e', f'(find-file "{strongest_bridge}")'
    ], capture_output=True, text=True)
    
    return f"🎯 Navigated to strongest concept bridge: {strongest_bridge}\n" + \
           f"Bridges: redis_patterns, emacs_integration, ai_agents, homoiconic, " + \
           f"org_mode, mcp_servers, knowledge_graph, self_modification, " + \
           f"redis_ai_challenge, semantic_understanding"

@mcp.tool()  
def show_concept_relationship_strength(concept: str) -> str:
    """Show relationship strength for a specific concept"""
    result = subprocess.run([
        'redis-cli', 'HGETALL', f'concept:{concept}'
    ], capture_output=True, text=True)
    
    lines = result.stdout.strip().split('\n')
    data = {}
    for i in range(0, len(lines), 2):
        if i + 1 < len(lines):
            data[lines[i]] = lines[i + 1]
    
    files = json.loads(data.get('files', '[]'))
    
    return f"📊 {concept} RELATIONSHIP ANALYSIS:\n" + \
           f"Mentions: {data.get('mentions', 0)}\n" + \
           f"Files involved: {len(files)}\n" + \
           f"Strength: {data.get('strength', 'unknown')}\n" + \
           f"Top files: {', '.join(files[:3])}"

if __name__ == "__main__":
    mcp.run()