#!/usr/bin/env python3
"""
Lisp Linguistic Analyzer
Sentence diagramming for Lisp expressions - discovering grammatical structure
"""

import re
import redis
from typing import Dict, List, Set, Tuple
from collections import defaultdict, Counter
from dataclasses import dataclass
import networkx as nx

@dataclass
class LispGrammarRule:
    pattern: str
    part_of_speech: str
    semantic_role: str
    starts_with: Set[str]  # What can start this pattern
    ends_with: Set[str]    # What can end this pattern
    frequency: int

@dataclass
class ExpressionDiagram:
    subject: str           # What is being acted upon
    verb: str             # The action/function
    objects: List[str]    # Arguments/parameters
    modifiers: List[str]  # Additional context
    syntactic_category: str

class LispLinguisticAnalyzer:
    def __init__(self):
        self.redis_client = redis.Redis(decode_responses=True)
        
        # Part-of-speech categories for Lisp functions
        self.function_pos = {
            # Verbs (actions)
            'VERB_NAVIGATION': {'goto-line', 'goto-char', 'move-to-column', 'forward-char', 'backward-char'},
            'VERB_BUFFER': {'switch-to-buffer', 'kill-buffer', 'save-buffer'},
            'VERB_TEXT': {'insert', 'delete-region', 'kill-line', 'yank'},
            'VERB_WINDOW': {'split-window', 'delete-window', 'delete-other-windows'},
            'VERB_SEARCH': {'search-forward', 'search-backward', 'helm-mini'},
            'VERB_STATE': {'undo', 'redo', 'winner-undo'},
            
            # Nouns (data/objects)  
            'NOUN_BUFFER': {'buffer-name', 'current-buffer', 'window-buffer'},
            'NOUN_POSITION': {'point', 'window-start', 'window-end', 'line-number-at-pos'},
            'NOUN_TEXT': {'buffer-substring', 'thing-at-point'},
            'NOUN_WINDOW': {'selected-window', 'window-list'},
            
            # Adjectives (modifiers)
            'ADJ_TEMPORAL': {'before-save-hook', 'after-change-functions'},
            'ADJ_CONDITIONAL': {'when', 'unless', 'if'},
            'ADJ_QUANTIFIER': {'length', 'count-lines'},
        }
        
        # Reverse mapping: function -> part of speech
        self.pos_lookup = {}
        for pos, functions in self.function_pos.items():
    """TODO: Document __init__ function"""
            for func in functions:
                self.pos_lookup[func] = pos
    
    def extract_expressions_from_redis(self) -> List[str]:
        """Extract Lisp expressions from Redis command logs"""
        
        expressions = []
        
        try:
            # Get from command streams
            streams = ["emacs:mcp:commands", "emacs:diffs:executed"]
            
            for stream in streams:
                entries = self.redis_client.xrange(stream, count=500)
                for entry_id, fields in entries:
                    if 'elisp' in fields:
                        elisp = fields['elisp']
                        # Extract individual expressions
                        parsed_exprs = self._parse_expressions(elisp)
                        expressions.extend(parsed_exprs)
                        
        except Exception as e:
            print(f"Error extracting from Redis: {e}")
            
        return expressions
    
    def _parse_expressions(self, elisp_text: str) -> List[str]:
        """Parse elisp text into individual expressions"""
        
        expressions = []
        
        # Find all balanced parentheses expressions
        i = 0
        while i < len(elisp_text):
            if elisp_text[i] == '(':
                # Find matching closing paren
                paren_count = 1
                j = i + 1
                
                while j < len(elisp_text) and paren_count > 0:
                    if elisp_text[j] == '(':
                        paren_count += 1
                    elif elisp_text[j] == ')':
                        paren_count -= 1
                    j += 1
                
                if paren_count == 0:
                    expr = elisp_text[i:j].strip()
                    if len(expr) > 3:  # Skip tiny expressions
                        expressions.append(expr)
                
                i = j
            else:
                i += 1
                
        return expressions
    
    def diagram_expression(self, expr: str) -> ExpressionDiagram:
        """Diagram a Lisp expression like sentence diagramming"""
        
        # Parse the expression structure
        tokens = self._tokenize_expression(expr)
        
        if not tokens:
            return ExpressionDiagram("", "", [], [], "INVALID")
        
        # First token is usually the verb (function)
        verb = tokens[0]
        
        # Determine part of speech
        verb_pos = self.pos_lookup.get(verb, "UNKNOWN")
        
        # Extract components based on grammatical analysis
        if verb_pos.startswith('VERB_BUFFER'):
            # Buffer operations: (switch-to-buffer "*scratch*")
            subject = "current-context"
            objects = tokens[1:] if len(tokens) > 1 else []
            syntactic_category = "BUFFER_TRANSFORMATION"
            
        elif verb_pos.startswith('VERB_NAVIGATION'):
            # Navigation: (goto-line 50)
            subject = "point"
            objects = tokens[1:] if len(tokens) > 1 else []
            syntactic_category = "POSITION_TRANSFORMATION"
            
        elif verb_pos.startswith('VERB_TEXT'):
            # Text operations: (insert "hello world")
            subject = "buffer-content"  
            objects = tokens[1:] if len(tokens) > 1 else []
            syntactic_category = "CONTENT_TRANSFORMATION"
            
        elif verb_pos.startswith('VERB_WINDOW'):
            # Window operations: (split-window-right)
            subject = "window-configuration"
            objects = tokens[1:] if len(tokens) > 1 else []
            syntactic_category = "LAYOUT_TRANSFORMATION"
            
        else:
            # General case
            subject = "emacs-state"
            objects = tokens[1:] if len(tokens) > 1 else []
            syntactic_category = "GENERAL_TRANSFORMATION"
        
        return ExpressionDiagram(
            subject=subject,
            verb=verb,
            objects=objects,
            modifiers=[],  # Could extract these too
            syntactic_category=syntactic_category
        )
    
    def _tokenize_expression(self, expr: str) -> List[str]:
        """Tokenize Lisp expression into components"""
        
        # Remove outer parentheses
        expr = expr.strip()
        if expr.startswith('(') and expr.endswith(')'):
            expr = expr[1:-1]
        
        # Simple tokenization (could be more sophisticated)
        tokens = []
        current_token = ""
        in_string = False
        
        for char in expr:
            if char == '"' and not in_string:
                in_string = True
                current_token += char
            elif char == '"' and in_string:
                in_string = False
                current_token += char
                tokens.append(current_token)
                current_token = ""
            elif char == ' ' and not in_string:
                if current_token:
                    tokens.append(current_token)
                    current_token = ""
            else:
                current_token += char
        
        if current_token:
            tokens.append(current_token)
            
        return tokens
    
    def find_expression_patterns(self, expressions: List[str]) -> Dict[str, LispGrammarRule]:
        """Find patterns like 'expressions that start with X' and 'expressions that end with Y'"""
        
        patterns = {}
        
        # Track what can start expressions
        start_patterns = defaultdict(list)
        end_patterns = defaultdict(list)
        
        for expr in expressions:
            diagram = self.diagram_expression(expr)
            
            # What starts this type of expression?
            start_key = diagram.verb
            start_patterns[start_key].append(expr)
            
            # What ends this type of expression?
            if diagram.objects:
                end_key = diagram.objects[-1]  # Last argument
                end_patterns[end_key].append(expr)
        
        # Create grammar rules
        for start_token, expr_list in start_patterns.items():
            if len(expr_list) >= 3:  # Only patterns that occur multiple times
                
                # Find what these expressions can end with
                end_tokens = set()
                for expr in expr_list:
                    diagram = self.diagram_expression(expr)
                    if diagram.objects:
                        end_tokens.add(diagram.objects[-1])
                
                # Determine semantic role
                pos = self.pos_lookup.get(start_token, "UNKNOWN")
                semantic_role = pos.split('_')[1] if '_' in pos else "GENERAL"
                
                patterns[start_token] = LispGrammarRule(
                    pattern=f"({start_token} ...)",
                    part_of_speech=pos,
                    semantic_role=semantic_role,
                    starts_with={start_token},
                    ends_with=end_tokens,
                    frequency=len(expr_list)
                )
        
        return patterns
    
    def generate_sentence_diagram(self, expr: str) -> str:
        """Generate ASCII sentence diagram for Lisp expression"""
        
        diagram = self.diagram_expression(expr)
        
        # Create ASCII diagram
        ascii_diagram = f"""
Expression: {expr}

         {diagram.verb}
         /     \\
    {diagram.subject}   {' + '.join(diagram.objects) if diagram.objects else 'ø'}
    (subject)  (objects)
    
Category: {diagram.syntactic_category}
POS: {self.pos_lookup.get(diagram.verb, 'UNKNOWN')}
"""
        
        return ascii_diagram
    
    def discover_linguistic_patterns(self) -> Dict[str, any]:
        """Discover complete linguistic taxonomy of Lisp expressions"""
        
        print("🔍 Extracting expressions from Redis...")
        expressions = self.extract_expressions_from_redis()
        
        print(f"📊 Analyzing {len(expressions)} expressions...")
        patterns = self.find_expression_patterns(expressions)
        
        # Grammar analysis
        grammar_stats = {
            'total_expressions': len(expressions),
            'unique_patterns': len(patterns),
            'part_of_speech_distribution': Counter(),  
            'syntactic_categories': Counter(),
            'start_tokens': Counter(),
            'end_tokens': Counter()
        }
        
        for expr in expressions:
            diagram = self.diagram_expression(expr)
            
            pos = self.pos_lookup.get(diagram.verb, 'UNKNOWN')
            grammar_stats['part_of_speech_distribution'][pos] += 1
            grammar_stats['syntactic_categories'][diagram.syntactic_category] += 1
            grammar_stats['start_tokens'][diagram.verb] += 1
            
            if diagram.objects:
                grammar_stats['end_tokens'][diagram.objects[-1]] += 1
        
        return {
            'patterns': patterns,
            'grammar_stats': grammar_stats,
            'sample_diagrams': [self.generate_sentence_diagram(expr) for expr in expressions[:3]]
        }

# Example usage
if __name__ == "__main__":
    analyzer = LispLinguisticAnalyzer()
    
    print("🧠 **LISP LINGUISTIC ANALYSIS**")
    print("Applying sentence diagramming to Lisp expressions...")
    
    # Test with sample expressions
    sample_expressions = [
        "(switch-to-buffer \"*scratch*\")",
        "(goto-line 50)",
        "(insert \"hello world\")",
        "(split-window-right)",
        "(helm-mini)"
    ]
    
    print("\n📝 **SENTENCE DIAGRAMS**:")
    for expr in sample_expressions:
        print(analyzer.generate_sentence_diagram(expr))
        print("-" * 50)
    
    # Discover patterns from Redis
    print("\n🔍 **DISCOVERING PATTERNS FROM REDIS**:")
    analysis = analyzer.discover_linguistic_patterns()
    
    print(f"\n📊 **GRAMMAR STATISTICS**:")
    stats = analysis['grammar_stats']
    print(f"Total expressions analyzed: {stats['total_expressions']}")
    print(f"Unique patterns found: {stats['unique_patterns']}")
    
    print(f"\n🏷️  **PART-OF-SPEECH DISTRIBUTION**:")
    for pos, count in stats['part_of_speech_distribution'].most_common(5):
        print(f"  {pos}: {count}")
        
    print(f"\n🎯 **COMMON START TOKENS** (What expressions start with):")
    for token, count in stats['start_tokens'].most_common(5):
        print(f"  ({token} ...): {count} times")
        
    print(f"\n🎯 **COMMON END TOKENS** (What expressions end with):")  
    for token, count in stats['end_tokens'].most_common(5):
        print(f"  ... {token}): {count} times")
    
    print(f"\n🔄 **PATTERN RULES**:")
    for pattern_name, rule in analysis['patterns'].items():
        print(f"  {rule.pattern}")
        print(f"    POS: {rule.part_of_speech}")
        print(f"    Role: {rule.semantic_role}")
        print(f"    Can end with: {rule.ends_with}")
        print(f"    Frequency: {rule.frequency}")
        print()