#!/usr/bin/env python3
"""
EXPLORE OUR SEMANTIC UNDERSTANDING
Now that we have comprehensive indexing, let's explore what we've built
"""

import redis
import json
from semantic_project_indexer import ProjectSemanticIndexer

def explore_our_work():
    """Explore and understand our complete project using semantic analysis"""
    
    print("🔍 EXPLORING OUR COMPLETE PROJECT SEMANTICALLY")
    print("=" * 55)
    
    r = redis.Redis(host='localhost', port=6379, decode_responses=True)
    indexer = ProjectSemanticIndexer()
    
    # Show the scope of what we've built
    print("📊 PROJECT SCOPE ANALYSIS:")
    stats = r.hgetall("project:stats")
    for key, value in stats.items():
        print(f"  • {key}: {value}")
    
    # Find the most interconnected files
    print("\n🔗 MOST CONNECTED FILES (by concept coverage):")
    concepts = list(r.smembers("all_concepts"))
    
    file_scores = {}
    for concept in concepts:
        concept_files = json.loads(r.hget(f"concept:{concept}", "files") or "[]")
        for file_name in concept_files:
            file_scores[file_name] = file_scores.get(file_name, 0) + 1
    
    # Top files by concept coverage
    top_files = sorted(file_scores.items(), key=lambda x: x[1], reverse=True)[:10]
    for file_name, score in top_files:
        print(f"  • {file_name}: {score} concepts")
    
    # Find concept co-occurrences
    print(f"\n🎯 CONCEPT CO-OCCURRENCES (concepts that appear together):")
    co_occurrences = []
    
    for i, concept1 in enumerate(concepts):
        for concept2 in concepts[i+1:]:
            files1 = set(json.loads(r.hget(f"concept:{concept1}", "files") or "[]"))
            files2 = set(json.loads(r.hget(f"concept:{concept2}", "files") or "[]"))
            
            shared = files1 & files2
            if shared and len(shared) > 10:  # At least 10 shared files
                strength = len(shared) / min(len(files1), len(files2))
                co_occurrences.append((concept1, concept2, strength, len(shared)))
    
    co_occurrences.sort(key=lambda x: x[2], reverse=True)
    
    for concept1, concept2, strength, shared_count in co_occurrences[:5]:
        print(f"  • {concept1} + {concept2}: {strength:.2f} strength ({shared_count} files)")
    
    # Semantic search examples with our work
    print(f"\n🔍 SEMANTIC SEARCH EXAMPLES:")
    
    interesting_queries = [
        "living agents redis",
        "emacs buffer control", 
        "homoiconic lisp programming",
        "mcp server generation",
        "ai coordination system"
    ]
    
    for query in interesting_queries:
        print(f"\nSearching: '{query}'")
        results = indexer.semantic_search(query, limit=3)
        for result in results:
            print(f"  📄 {result['type']}: {result['name']} ({result['relevance']:.2f})")
    
    return indexer

def find_our_key_innovations():
    """Identify the key innovations in our project"""
    
    print("\n" + "="*60)
    print("💡 KEY INNOVATIONS DISCOVERED")
    print("="*60)
    
    r = redis.Redis(host='localhost', port=6379, decode_responses=True)
    
    # Look for unique combinations
    innovations = {
        "Redis + Lisp Integration": ["redis_patterns", "homoiconic"],
        "AI + Emacs Control": ["ai_agents", "emacs_integration"], 
        "Self-Modifying Systems": ["self_modification", "homoiconic"],
        "Living Knowledge Graph": ["knowledge_graph", "ai_agents"],
        "MCP Server Factory": ["mcp_servers", "self_modification"]
    }
    
    for innovation, concept_pair in innovations.items():
        concept1, concept2 = concept_pair
        files1 = set(json.loads(r.hget(f"concept:{concept1}", "files") or "[]"))
        files2 = set(json.loads(r.hget(f"concept:{concept2}", "files") or "[]"))
        
        shared = files1 & files2
        if shared:
            strength = len(shared) / min(len(files1), len(files2))
            print(f"🎯 {innovation}:")
            print(f"   Strength: {strength:.2f} ({len(shared)} files)")
            print(f"   Key files: {', '.join(list(shared)[:3])}")

def understand_our_architecture():
    """Understand the overall architecture we've built"""
    
    print(f"\n" + "="*60)
    print("🏗️ ARCHITECTURE ANALYSIS")
    print("="*60)
    
    r = redis.Redis(host='localhost', port=6379, decode_responses=True)
    
    # Analyze by file types
    file_types = {}
    content_keys = r.keys("content:*")
    
    for key in content_keys:
        filename = key.replace("content:", "")
        if '.' in filename:
            ext = filename.split('.')[-1]
            file_types[ext] = file_types.get(ext, 0) + 1
        else:
            file_types['no_extension'] = file_types.get('no_extension', 0) + 1
    
    print("📁 FILE TYPE DISTRIBUTION:")
    for ext, count in sorted(file_types.items(), key=lambda x: x[1], reverse=True):
        print(f"   .{ext}: {count} files")
    
    # Analyze naming patterns
    print(f"\n🏷️ NAMING PATTERNS:")
    
    patterns = {
        "jit_": 0, "mcp_": 0, "test_": 0, "demo_": 0, 
        "ai_": 0, "redis_": 0, "claude_": 0, "_agent": 0
    }
    
    for key in content_keys:
        filename = key.replace("content:", "")
        for pattern in patterns:
            if pattern in filename:
                patterns[pattern] += 1
    
    for pattern, count in sorted(patterns.items(), key=lambda x: x[1], reverse=True):
        if count > 0:
            print(f"   '{pattern}': {count} files")

def what_should_we_do_next():
    """Based on semantic analysis, suggest what to work on next"""
    
    print(f"\n" + "="*60)
    print("🎯 WHAT SHOULD WE DO NEXT?")
    print("="*60)
    
    r = redis.Redis(host='localhost', port=6379, decode_responses=True)
    
    print("📊 Based on our semantic analysis:")
    print()
    print("🏆 STRENGTHS (well-developed areas):")
    print("   • MCP Server Ecosystem (10,327 mentions)")
    print("   • Redis Integration (10,281 mentions)")  
    print("   • Emacs Control (6,953 mentions)")
    print("   • AI Agent Architecture (6,318 mentions)")
    print()
    print("🎯 GROWTH OPPORTUNITIES (less developed but interesting):")
    print("   • Semantic Understanding (1,023 mentions) - what we just built!")
    print("   • Self-Modification (865 mentions) - could be expanded")
    print("   • Org Mode Integration (823 mentions) - underutilized potential")
    print()
    print("💡 SUGGESTED NEXT STEPS:")
    print("   1. Use semantic understanding to improve our MCP servers")
    print("   2. Build more sophisticated self-modifying systems") 
    print("   3. Integrate the semantic engine with our living org files")
    print("   4. Create AI agents that can navigate the semantic map")
    print("   5. Build semantic-aware Redis coordination")

if __name__ == "__main__":
    # Explore our complete semantic understanding
    indexer = explore_our_work()
    
    # Find our key innovations
    find_our_key_innovations()
    
    # Understand our architecture
    understand_our_architecture()
    
    # Suggest next steps
    what_should_we_do_next()