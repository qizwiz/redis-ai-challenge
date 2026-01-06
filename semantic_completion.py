#!/usr/bin/env python3
"""
SEMANTIC COMPLETION - Built with Rupert's guidance
Starting with the smallest working thing, as Rupert suggested
"""

from semantic_project_indexer import ProjectSemanticIndexer
import subprocess

class SemanticCompletion:
    """Semantic-aware code completion using our project knowledge"""
    
    def __init__(self):
        self.indexer = ProjectSemanticIndexer()
        print("🧠 SEMANTIC COMPLETION: Using our project intelligence")
    
    def suggest_from_codebase(self, partial_text):
        """Suggest completions from our actual codebase"""
        
        # Rupert said: Start with the smallest working thing
        results = self.indexer.semantic_search(partial_text, limit=3)
        
        suggestions = []
        for result in results:
            if result['type'] == 'file':
                # Get actual code from the file  
                try:
                    file_path = f"/Users/jonathanhill/src/redis-ai-challenge/{result['name']}"
                    with open(file_path, 'r') as f:
                        content = f.read()
                    
                    # Find relevant lines containing the search terms
                    lines = content.split('\n')
                    relevant_lines = [line.strip() for line in lines if any(word in line.lower() for word in partial_text.lower().split())]
                    
                    if relevant_lines:
                        suggestions.append(f"From {result['name']}: {relevant_lines[0][:80]}")
                    else:
                        suggestions.append(f"From {result['name']}: (contains '{partial_text}')")
                        
                except:
                    suggestions.append(f"From {result['name']}: (file read error)")
        
        return suggestions

# Following Rupert's advice: Test it immediately
if __name__ == "__main__":
    completion = SemanticCompletion()
    
    # Test with something from our codebase
    test_suggestions = completion.suggest_from_codebase("redis coordination")
    
    print("🎯 SEMANTIC SUGGESTIONS:")
    for suggestion in test_suggestions:
        print(f"  • {suggestion}")