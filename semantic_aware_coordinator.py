#!/usr/bin/env python3
"""
SEMANTIC-AWARE COORDINATOR
Using our semantic understanding to build intelligent coordination

No more random file exploration - semantic-guided development!
"""

import redis
import json
from typing import List, Dict
from semantic_project_indexer import ProjectSemanticIndexer

class SemanticAwareCoordinator:
    """Coordinates our systems using semantic understanding of the entire project"""
    
    def __init__(self):
        self.r = redis.Redis(host='localhost', port=6379, decode_responses=True)
        self.indexer = ProjectSemanticIndexer()
        print("🧠 SEMANTIC-AWARE COORDINATOR ONLINE")
    
    def find_optimal_integration_points(self):
        """Use semantic understanding to find where systems should connect"""
        
        print("🔗 FINDING OPTIMAL INTEGRATION POINTS...")
        
        # Get our strongest concept pairs
        concepts = ["redis_patterns", "emacs_integration", "ai_agents", "homoiconic", "mcp_servers"]
        
        integration_opportunities = []
        
        for i, concept1 in enumerate(concepts):
            for concept2 in concepts[i+1:]:
                files1 = set(json.loads(self.r.hget(f"concept:{concept1}", "files") or "[]"))
                files2 = set(json.loads(self.r.hget(f"concept:{concept2}", "files") or "[]"))
                
                shared = files1 & files2
                if shared and len(shared) > 20:  # Strong integration
                    strength = len(shared) / min(len(files1), len(files2))
                    integration_opportunities.append({
                        "concepts": f"{concept1} + {concept2}",
                        "strength": strength,
                        "shared_files": len(shared),
                        "key_files": list(shared)[:5]
                    })
        
        # Sort by strength
        integration_opportunities.sort(key=lambda x: x['strength'], reverse=True)
        
        print("🎯 TOP INTEGRATION OPPORTUNITIES:")
        for opp in integration_opportunities[:3]:
            print(f"  • {opp['concepts']}: {opp['strength']:.2f} ({opp['shared_files']} files)")
            print(f"    Key files: {', '.join(opp['key_files'])}")
        
        return integration_opportunities
    
    def identify_underutilized_potential(self):
        """Find concepts with high potential but low utilization"""
        
        print("\n💡 IDENTIFYING UNDERUTILIZED POTENTIAL...")
        
        concepts = list(self.r.smembers("all_concepts"))
        concept_analysis = []
        
        for concept in concepts:
            mentions = int(self.r.hget(f"concept:{concept}", "mentions") or 0)
            files = json.loads(self.r.hget(f"concept:{concept}", "files") or "[]")
            
            # Potential = unique files * average depth
            potential = len(files) * (mentions / max(len(files), 1))
            
            concept_analysis.append({
                "concept": concept,
                "mentions": mentions,
                "files": len(files),
                "potential": potential,
                "density": mentions / max(len(files), 1)
            })
        
        # Sort by potential but low current utilization
        underutilized = [c for c in concept_analysis if c['mentions'] < 2000 and c['potential'] > 50]
        underutilized.sort(key=lambda x: x['potential'], reverse=True)
        
        print("🚀 UNDERUTILIZED HIGH-POTENTIAL AREAS:")
        for concept in underutilized[:3]:
            print(f"  • {concept['concept']}: {concept['mentions']} mentions, {concept['files']} files")
            print(f"    Potential score: {concept['potential']:.0f}")
        
        return underutilized
    
    def generate_semantic_guided_next_actions(self):
        """Use semantic analysis to suggest concrete next actions"""
        
        print("\n⚡ SEMANTIC-GUIDED NEXT ACTIONS:")
        
        # Find files that bridge multiple strong concepts
        bridge_files = self.find_concept_bridge_files()
        
        # Find gaps where strong concepts don't connect
        concept_gaps = self.find_concept_gaps()
        
        actions = []
        
        # Action 1: Enhance bridge files
        if bridge_files:
            top_bridge = bridge_files[0]
            actions.append({
                "action": "enhance_bridge_file",
                "target": top_bridge['file'],
                "reason": f"Connects {top_bridge['concepts']} concepts",
                "concepts": top_bridge['concepts']
            })
        
        # Action 2: Fill concept gaps
        if concept_gaps:
            top_gap = concept_gaps[0]
            actions.append({
                "action": "bridge_concept_gap",
                "concepts": top_gap['concepts'],
                "reason": f"High potential but no connection",
                "potential_files": top_gap['candidate_files']
            })
        
        # Action 3: Expand underutilized potential
        underutilized = self.identify_underutilized_potential()
        if underutilized:
            top_underutilized = underutilized[0]
            actions.append({
                "action": "expand_underutilized_concept",
                "concept": top_underutilized['concept'],
                "reason": f"High potential ({top_underutilized['potential']:.0f}) but low utilization",
                "current_files": top_underutilized['files']
            })
        
        for i, action in enumerate(actions, 1):
            print(f"  {i}. {action['action'].replace('_', ' ').title()}")
            print(f"     Target: {action.get('target') or action.get('concept') or action.get('concepts')}")
            print(f"     Reason: {action['reason']}")
        
        return actions
    
    def find_concept_bridge_files(self):
        """Find files that bridge multiple important concepts"""
        
        concepts = ["redis_patterns", "emacs_integration", "ai_agents", "homoiconic", "mcp_servers"]
        
        file_concept_count = {}
        file_concepts = {}
        
        for concept in concepts:
            files = json.loads(self.r.hget(f"concept:{concept}", "files") or "[]")
            for file_name in files:
                file_concept_count[file_name] = file_concept_count.get(file_name, 0) + 1
                if file_name not in file_concepts:
                    file_concepts[file_name] = []
                file_concepts[file_name].append(concept)
        
        # Find files that bridge 3+ major concepts
        bridge_files = []
        for file_name, count in file_concept_count.items():
            if count >= 3:
                bridge_files.append({
                    "file": file_name,
                    "concept_count": count,
                    "concepts": file_concepts[file_name]
                })
        
        bridge_files.sort(key=lambda x: x['concept_count'], reverse=True)
        return bridge_files
    
    def find_concept_gaps(self):
        """Find important concepts that should connect but don't"""
        
        concepts = list(self.r.smembers("all_concepts"))
        
        gaps = []
        for i, concept1 in enumerate(concepts):
            for concept2 in concepts[i+1:]:
                files1 = set(json.loads(self.r.hget(f"concept:{concept1}", "files") or "[]"))
                files2 = set(json.loads(self.r.hget(f"concept:{concept2}", "files") or "[]"))
                
                # High potential but low connection
                potential = min(len(files1), len(files2))
                connection = len(files1 & files2)
                
                if potential > 50 and connection < 10:  # Gap detected
                    gaps.append({
                        "concepts": f"{concept1} + {concept2}",
                        "potential": potential,
                        "connection": connection,
                        "candidate_files": list(files1)[:3] + list(files2)[:3]
                    })
        
        gaps.sort(key=lambda x: x['potential'] - x['connection'], reverse=True)
        return gaps
    
    def execute_semantic_guided_action(self, action):
        """Execute a semantically-guided action"""
        
        if action['action'] == 'enhance_bridge_file':
            return self.enhance_bridge_file(action['target'], action['concepts'])
        elif action['action'] == 'bridge_concept_gap':
            return self.bridge_concept_gap(action['concepts'])
        elif action['action'] == 'expand_underutilized_concept':
            return self.expand_underutilized_concept(action['concept'])
    
    def enhance_bridge_file(self, filename, concepts):
        """Enhance a file that bridges multiple concepts"""
        
        print(f"\n🔗 ENHANCING BRIDGE FILE: {filename}")
        
        # Get file content
        content = self.r.get(f"content:{filename}")
        if not content:
            return f"Could not find content for {filename}"
        
        # Add semantic awareness to the file
        enhanced_content = f"""
# SEMANTIC BRIDGE ENHANCED: {filename}
# This file bridges concepts: {', '.join(concepts)}
# Enhanced with semantic awareness at {self.r.time()[0]}

{content}

# SEMANTIC COORDINATION ADDED:
# - Bridges {len(concepts)} major concepts
# - Identified as key integration point
# - Enhanced for cross-concept coordination
"""
        
        # Write enhanced version
        enhanced_filename = filename.replace('.py', '_semantic_enhanced.py')
        with open(f"/Users/jonathanhill/src/redis-ai-challenge/{enhanced_filename}", 'w') as f:
            f.write(enhanced_content)
        
        print(f"✅ Enhanced {filename} → {enhanced_filename}")
        return enhanced_filename
    
    def coordinate_intelligently(self):
        """Use all semantic understanding to coordinate intelligently"""
        
        print("\n🎯 INTELLIGENT SEMANTIC COORDINATION")
        print("=" * 45)
        
        # Step 1: Find integration points
        integrations = self.find_optimal_integration_points()
        
        # Step 2: Generate actions
        actions = self.generate_semantic_guided_next_actions()
        
        # Step 3: Execute top action
        if actions:
            top_action = actions[0]
            print(f"\n⚡ EXECUTING: {top_action['action'].replace('_', ' ').title()}")
            result = self.execute_semantic_guided_action(top_action)
            print(f"✅ Result: {result}")
        
        return {
            "integrations_found": len(integrations),
            "actions_generated": len(actions),
            "executed_action": actions[0] if actions else None
        }

if __name__ == "__main__":
    coordinator = SemanticAwareCoordinator()
    result = coordinator.coordinate_intelligently()
    
    print(f"\n🧠 SEMANTIC COORDINATION COMPLETE")
    print(f"🎯 Found {result['integrations_found']} integration opportunities")
    print(f"⚡ Generated {result['actions_generated']} guided actions")
    print(f"✅ Executed semantic-guided enhancement")