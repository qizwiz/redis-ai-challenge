#!/usr/bin/env python3
"""
SEMANTIC PROJECT INDEXER
Building complete semantic understanding of our entire project

ML Concepts We're Learning:
- Embeddings: Converting text to meaning vectors
- Semantic search: Finding concepts, not just keywords  
- Vector databases: Storing high-dimensional semantic data
- Knowledge graphs: Mapping relationships between ideas
"""

import os
import redis
import json
import time
from pathlib import Path
from typing import List, Dict, Any
import hashlib
import ast
import re

# We'll start with basic semantic analysis and build up to embeddings
class ProjectSemanticIndexer:
    """Indexes every token and concept in our project for semantic understanding"""
    
    def __init__(self, project_dir="/Users/jonathanhill/src/redis-ai-challenge"):
        self.project_dir = Path(project_dir)
        self.r = redis.Redis(host='localhost', port=6379, decode_responses=True)
        
        print("🧠 BUILDING SEMANTIC PROJECT UNDERSTANDING")
        print("=" * 50)
        print("📚 ML Concepts: embeddings, semantic search, vector DB, knowledge graphs")
        print()
    
    def index_entire_project(self):
        """Build comprehensive semantic index of everything"""
        
        print("🔍 Phase 1: Indexing all files and tokens...")
        file_stats = self.index_all_files()
        
        print("🔗 Phase 2: Extracting concepts and relationships...")  
        concepts = self.extract_concepts()
        
        print("📊 Phase 3: Building knowledge graph...")
        knowledge_graph = self.build_knowledge_graph()
        
        print("🎯 Phase 4: Creating semantic navigation system...")
        navigation = self.create_semantic_navigation()
        
        return {
            "files_indexed": file_stats,
            "concepts_extracted": len(concepts),
            "knowledge_graph": knowledge_graph,
            "navigation": navigation
        }
    
    def index_all_files(self):
        """Index every file, every token, every line"""
        
        # Get all relevant files
        file_patterns = ['*.py', '*.org', '*.md', '*.txt', '*.json', '*.toml']
        all_files = []
        
        for pattern in file_patterns:
            all_files.extend(list(self.project_dir.glob(pattern)))
        
        print(f"📁 Found {len(all_files)} files to index")
        
        total_tokens = 0
        total_lines = 0
        
        for file_path in all_files:
            if file_path.name.startswith('.'):
                continue  # Skip hidden files
                
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Basic tokenization (we'll improve this)
                tokens = re.findall(r'\b\w+\b', content.lower())
                lines = content.split('\n')
                
                # Store file metadata
                file_info = {
                    "path": str(file_path),
                    "size": len(content),
                    "lines": len(lines),
                    "tokens": len(tokens),
                    "type": file_path.suffix,
                    "indexed_at": str(time.time())
                }
                
                self.r.hset(f"file:{file_path.name}", mapping=file_info)
                
                # Store content for semantic analysis
                self.r.set(f"content:{file_path.name}", content)
                
                # Index unique tokens
                unique_tokens = set(tokens)
                for token in unique_tokens:
                    self.r.sadd(f"token:{token}", file_path.name)
                    self.r.sadd("all_tokens", token)
                
                # Index lines for context
                for i, line in enumerate(lines):
                    if line.strip():  # Only non-empty lines
                        self.r.hset(f"line:{file_path.name}:{i}", mapping={
                            "content": line,
                            "line_number": i,
                            "file": file_path.name
                        })
                
                total_tokens += len(tokens)
                total_lines += len(lines)
                
                print(f"  ✅ {file_path.name}: {len(tokens)} tokens, {len(lines)} lines")
                
            except Exception as e:
                print(f"  ❌ Error indexing {file_path.name}: {e}")
        
        stats = {
            "files": len(all_files),
            "total_tokens": total_tokens,
            "total_lines": total_lines,
            "unique_tokens": self.r.scard("all_tokens")
        }
        
        self.r.hset("project:stats", mapping=stats)
        print(f"📊 Indexed {stats['files']} files, {stats['total_tokens']} tokens, {stats['unique_tokens']} unique")
        
        return stats
    
    def extract_concepts(self):
        """Extract high-level concepts from our codebase"""
        
        # Key concepts we've been working with (we can expand this)
        concept_patterns = {
            "redis_patterns": [r"redis", r"xadd", r"xread", r"hset", r"stream"],
            "emacs_integration": [r"emacs", r"elisp", r"buffer", r"daemon", r"emacsclient"],
            "ai_agents": [r"agent", r"living", r"organism", r"intelligence", r"coordination"],
            "homoiconic": [r"homoiconic", r"s.?expression", r"lisp", r"lambda", r"eval"],
            "org_mode": [r"org.?roam", r"org.?file", r"buffer.?agent", r"org.?mode"],
            "mcp_servers": [r"mcp", r"fastmcp", r"server", r"tool", r"protocol"],
            "knowledge_graph": [r"knowledge", r"graph", r"relationship", r"node", r"edge"],
            "self_modification": [r"self.?modifying", r"evolve", r"mutation", r"generation"],
            "redis_ai_challenge": [r"redis.?ai", r"challenge", r"submission", r"standing.?giants"],
            "semantic_understanding": [r"semantic", r"embedding", r"vector", r"similarity"]
        }
        
        print("🔍 Extracting concepts from codebase...")
        
        all_files = list(self.r.keys("content:*"))
        concepts = {}
        
        for concept, patterns in concept_patterns.items():
            concepts[concept] = {"files": [], "mentions": 0}
            
            for file_key in all_files:
                content = self.r.get(file_key)
                if not content:
                    continue
                    
                file_name = file_key.replace("content:", "")
                content_lower = content.lower()
                
                mentions_in_file = 0
                for pattern in patterns:
                    mentions = len(re.findall(pattern, content_lower))
                    mentions_in_file += mentions
                
                if mentions_in_file > 0:
                    concepts[concept]["files"].append(file_name)
                    concepts[concept]["mentions"] += mentions_in_file
        
        # Store concepts in Redis
        for concept, data in concepts.items():
            self.r.hset(f"concept:{concept}", mapping={
                "mentions": data["mentions"],
                "files": json.dumps(data["files"]),
                "strength": min(data["mentions"] / 10, 1.0)  # Normalized strength
            })
            
            print(f"  📝 {concept}: {data['mentions']} mentions in {len(data['files'])} files")
        
        self.r.sadd("all_concepts", *concepts.keys())
        print(f"✅ Extracted {len(concepts)} major concepts")
        
        return concepts
    
    def build_knowledge_graph(self):
        """Build relationships between concepts, files, and tokens"""
        
        print("🔗 Building knowledge graph...")
        
        # Get all concepts and files
        concepts = list(self.r.smembers("all_concepts"))
        files = list(self.r.keys("file:*"))
        
        relationships = []
        
        # Build concept-to-file relationships
        for concept in concepts:
            concept_data = self.r.hget(f"concept:{concept}", "files")
            if concept_data:
                concept_files = json.loads(concept_data)
                for file_name in concept_files:
                    relationships.append({
                        "from": concept,
                        "to": file_name,
                        "type": "appears_in",
                        "strength": float(self.r.hget(f"concept:{concept}", "strength") or 0)
                    })
        
        # Build co-occurrence relationships (concepts that appear in same files)
        for i, concept1 in enumerate(concepts):
            for concept2 in concepts[i+1:]:
                concept1_files = set(json.loads(self.r.hget(f"concept:{concept1}", "files") or "[]"))
                concept2_files = set(json.loads(self.r.hget(f"concept:{concept2}", "files") or "[]"))
                
                shared_files = concept1_files & concept2_files
                if shared_files:
                    strength = len(shared_files) / min(len(concept1_files), len(concept2_files))
                    relationships.append({
                        "from": concept1,
                        "to": concept2,
                        "type": "co_occurs_with",
                        "strength": strength,
                        "shared_files": list(shared_files)
                    })
        
        # Store relationships
        for i, rel in enumerate(relationships):
            self.r.hset(f"relationship:{i}", mapping={
                "from": rel["from"],
                "to": rel["to"],
                "type": rel["type"],
                "strength": str(rel["strength"]),
                "data": json.dumps(rel.get("shared_files", []))
            })
        
        print(f"✅ Built knowledge graph with {len(relationships)} relationships")
        
        # Store graph metadata
        graph_stats = {
            "concepts": len(concepts),
            "files": len(files),
            "relationships": len(relationships),
            "built_at": str(time.time())
        }
        
        self.r.hset("knowledge_graph:stats", mapping=graph_stats)
        
        return graph_stats
    
    def create_semantic_navigation(self):
        """Create navigation system for semantic exploration"""
        
        print("🧭 Creating semantic navigation system...")
        
        # Create concept index for quick lookup
        concepts = list(self.r.smembers("all_concepts"))
        
        navigation_features = {
            "concept_search": f"Search among {len(concepts)} concepts",
            "file_exploration": f"Navigate {self.r.scard('all_tokens')} unique tokens",
            "relationship_traversal": f"Follow {self.r.scard('relationship:*')} relationships",
            "semantic_similarity": "Find conceptually related items"
        }
        
        # Store navigation capabilities
        self.r.hset("navigation:capabilities", mapping=navigation_features)
        
        print("✅ Semantic navigation system ready")
        
        return navigation_features
    
    def semantic_search(self, query: str, limit: int = 10):
        """Simple semantic search (we'll improve this with embeddings later)"""
        
        print(f"🔍 Searching for: '{query}'")
        
        query_tokens = re.findall(r'\b\w+\b', query.lower())
        results = []
        
        # Search in concepts
        concepts = list(self.r.smembers("all_concepts"))
        for concept in concepts:
            concept_lower = concept.lower()
            matches = sum(1 for token in query_tokens if token in concept_lower)
            if matches > 0:
                results.append({
                    "type": "concept",
                    "name": concept,
                    "relevance": matches / len(query_tokens),
                    "mentions": int(self.r.hget(f"concept:{concept}", "mentions") or 0)
                })
        
        # Search in files
        files = list(self.r.keys("content:*"))
        for file_key in files:
            content = self.r.get(file_key)
            if not content:
                continue
                
            file_name = file_key.replace("content:", "")
            content_lower = content.lower()
            
            matches = sum(content_lower.count(token) for token in query_tokens)
            if matches > 0:
                results.append({
                    "type": "file",
                    "name": file_name,
                    "relevance": min(matches / 10, 1.0),  # Normalize
                    "matches": matches
                })
        
        # Sort by relevance
        results.sort(key=lambda x: x["relevance"], reverse=True)
        
        return results[:limit]
    
    def get_project_overview(self):
        """Get comprehensive overview of our project"""
        
        stats = self.r.hgetall("project:stats")
        concepts = list(self.r.smembers("all_concepts"))
        graph_stats = self.r.hgetall("knowledge_graph:stats")
        
        overview = {
            "project_stats": stats,
            "key_concepts": concepts[:10],  # Top concepts
            "knowledge_graph": graph_stats,
            "total_understanding": "Comprehensive semantic index ready"
        }
        
        return overview

def demonstrate_semantic_understanding():
    """Show off our semantic understanding capabilities"""
    
    indexer = ProjectSemanticIndexer()
    
    # Build the semantic index
    results = indexer.index_entire_project()
    
    print("\n" + "="*60)
    print("🧠 SEMANTIC UNDERSTANDING DEMONSTRATION")
    print("="*60)
    
    # Show project overview
    overview = indexer.get_project_overview()
    print(f"📊 Project Stats:")
    for key, value in overview["project_stats"].items():
        print(f"  • {key}: {value}")
    
    print(f"\n🎯 Key Concepts Found:")
    for concept in overview["key_concepts"]:
        concept_data = indexer.r.hgetall(f"concept:{concept}")
        print(f"  • {concept}: {concept_data.get('mentions', 0)} mentions")
    
    # Demonstrate semantic search
    print(f"\n🔍 SEMANTIC SEARCH EXAMPLES:")
    
    searches = ["redis ai", "emacs control", "living agents", "homoiconic programming"]
    
    for query in searches:
        print(f"\nSearching: '{query}'")
        results = indexer.semantic_search(query, limit=3)
        for result in results:
            print(f"  📄 {result['type']}: {result['name']} (relevance: {result['relevance']:.2f})")
    
    return indexer

if __name__ == "__main__":
    # Let's build comprehensive semantic understanding!
    indexer = demonstrate_semantic_understanding()
    
    print("\n" + "="*60)
    print("✅ SEMANTIC PROJECT UNDERSTANDING COMPLETE")
    print("🎯 You now have comprehensive semantic navigation of ALL our work")
    print("🧠 Every token, concept, and relationship is indexed and searchable")
    print("="*60)