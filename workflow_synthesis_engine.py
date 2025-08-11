#!/usr/bin/env python3
"""
Workflow Synthesis Engine
Unconscious command prediction through homoiconic pattern discovery
"""

import redis
import json
import numpy as np
from collections import defaultdict, Counter
from typing import Dict, List, Tuple, Set
from dataclasses import dataclass
import networkx as nx
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer


@dataclass
class CommandPattern:
    sequence: List[str]
    frequency: int
    context: Dict[str, str]  # buffer, mode, time_of_day, etc
    semantic_category: str


@dataclass
class WorkflowCategory:
    name: str
    morphisms: Set[str]  # Commands that belong to this category
    composition_rules: List[Tuple[str, str]]  # Which commands compose naturally
    invariants: Dict[str, str]  # What stays constant in this category


class WorkflowSynthesisEngine:
    def __init__(self):
        self.redis_client = redis.Redis(decode_responses=True)
        self.command_graph = nx.DiGraph()  # Command sequence graph
        self.semantic_clusters = {}
        self.workflow_categories = {}

    def discover_command_patterns(self) -> List[CommandPattern]:
        """Discover patterns from Redis command logs using category theory"""

        # Get all executed command sequences
        sequences = self._extract_command_sequences()

        # Build command transition graph (morphism composition)
        self._build_morphism_graph(sequences)

        # Find common subsequences (natural transformations)
        patterns = self._find_subsequence_patterns(sequences)

        # Cluster by semantic similarity (functors between contexts)
        semantic_patterns = self._cluster_semantic_categories(patterns)

        return semantic_patterns

    def _extract_command_sequences(self) -> List[List[str]]:
        """Extract command sequences from Redis logs"""

        sequences = []

        # Get from multiple Redis streams
        streams = [
            "emacs:mcp:commands",
            "emacs:diffs:executed",
            "emacs:state:transitions",
        ]

        for stream in streams:
            try:
                # Get recent command history
                entries = self.redis_client.xrange(stream, count=1000)

                session_commands = []
                for entry_id, fields in entries:
                    if "elisp" in fields:
                        # Parse elisp command into structural components
                        elisp = fields["elisp"]
                        parsed = self._parse_elisp_structure(elisp)
                        session_commands.extend(parsed)

                if session_commands:
                    sequences.append(session_commands)

            except Exception as e:
                print(f"Stream {stream} not found: {e}")

        return sequences

    def _parse_elisp_structure(self, elisp: str) -> List[str]:
        """Parse elisp into structural command components (homoiconic analysis)"""

        import re

        # Extract function calls from elisp
        function_pattern = r"\(([a-zA-Z-]+)"
        functions = re.findall(function_pattern, elisp)

        # Normalize to canonical forms
        canonical_map = {
            "switch-to-buffer": "BUFFER_SWITCH",
            "goto-line": "NAVIGATION",
            "goto-char": "NAVIGATION",
            "insert": "TEXT_INSERT",
            "delete-region": "TEXT_DELETE",
            "split-window": "WINDOW_SPLIT",
            "delete-other-windows": "WINDOW_ISOLATE",
            "helm-mini": "FUZZY_SEARCH",
            "winner-undo": "WINDOW_UNDO",
        }

        return [canonical_map.get(func, func.upper()) for func in functions]

    def _find_subsequence_patterns(
        self, sequences: List[List[str]]
    ) -> List[CommandPattern]:
        """Find common subsequences (natural transformations in workflow category)"""

        patterns = []
        subsequence_counts = defaultdict(int)

        # Find all subsequences of length 2-5
        for sequence in sequences:
            for length in range(2, min(6, len(sequence) + 1)):
                for i in range(len(sequence) - length + 1):
                    subseq = tuple(sequence[i : i + length])
                    subsequence_counts[subseq] += 1

        # Convert to CommandPattern objects
        for subseq, count in subsequence_counts.items():
            if count >= 3:  # Only patterns that occur multiple times
                patterns.append(
                    CommandPattern(
                        sequence=list(subseq),
                        frequency=count,
                        context={},  # Will be enriched later
                        semantic_category="",  # Will be assigned by clustering
                    )
                )

        return patterns

    def _cluster_semantic_categories(
        self, patterns: List[CommandPattern]
    ) -> List[CommandPattern]:
        """Cluster patterns by semantic similarity (category theory functors)"""

        if not patterns:
            return patterns

        # Create feature vectors from command sequences
        pattern_texts = [" ".join(p.sequence) for p in patterns]

        vectorizer = TfidfVectorizer()
        feature_matrix = vectorizer.fit_transform(pattern_texts)

        # Cluster into semantic categories
        n_clusters = min(8, len(patterns))  # Max 8 categories
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        cluster_labels = kmeans.fit_predict(feature_matrix.toarray())

        # Assign semantic category names
        category_names = [
            "NAVIGATION_WORKFLOWS",
            "TEXT_EDITING_WORKFLOWS",
            "WINDOW_MANAGEMENT_WORKFLOWS",
            "BUFFER_SWITCHING_WORKFLOWS",
            "SEARCH_WORKFLOWS",
            "UNDO_REDO_WORKFLOWS",
            "INSERTION_WORKFLOWS",
            "DELETION_WORKFLOWS",
        ]

        # Assign categories to patterns
        for i, pattern in enumerate(patterns):
            pattern.semantic_category = category_names[
                cluster_labels[i] % len(category_names)
            ]

        return patterns

    def predict_next_commands(
        self, current_sequence: List[str], context: Dict[str, str]
    ) -> List[Tuple[str, float]]:
        """Predict next likely commands using graph structure and patterns"""

        predictions = []

        if not current_sequence:
            return predictions

        last_command = current_sequence[-1]

        # Get direct successors from morphism graph
        if last_command in self.command_graph:
            successors = self.command_graph.successors(last_command)
            for successor in successors:
                weight = self.command_graph[last_command][successor]["weight"]
                # Normalize to probability
                total_weight = sum(
                    self.command_graph[last_command][s]["weight"]
                    for s in self.command_graph.successors(last_command)
                )
                probability = weight / total_weight if total_weight > 0 else 0
                predictions.append((successor, probability))

        # Sort by probability
        predictions.sort(key=lambda x: x[1], reverse=True)

        return predictions[:5]  # Top 5 predictions

    def synthesize_workflow(self, intent_description: str) -> List[str]:
        """Synthesize complete workflow from high-level intent"""

        # This is where the magic happens - unconscious synthesis
        # Map intent to workflow category, then synthesize command sequence

        intent_lower = intent_description.lower()

        # Intent category mapping (this could be learned)
        if "edit" in intent_lower and "text" in intent_lower:
            return self._synthesize_text_editing_workflow(intent_description)
        elif "navigate" in intent_lower or "go to" in intent_lower:
            return self._synthesize_navigation_workflow(intent_description)
        elif "window" in intent_lower or "split" in intent_lower:
            return self._synthesize_window_workflow(intent_description)
        else:
            return self._synthesize_general_workflow(intent_description)

    def _synthesize_navigation_workflow(self, intent: str) -> List[str]:
        """Synthesize navigation command sequence"""
        return ["BUFFER_SWITCH", "NAVIGATION"]

    def _synthesize_window_workflow(self, intent: str) -> List[str]:
        """Synthesize window management sequence"""
        return ["WINDOW_SPLIT", "BUFFER_SWITCH", "WINDOW_ISOLATE"]

    def _synthesize_general_workflow(self, intent: str) -> List[str]:
        """General workflow synthesis"""
        return ["BUFFER_SWITCH", "NAVIGATION"]

    def discover_workflow_categories(self) -> Dict[str, WorkflowCategory]:
        """Discover mathematical categories in workflow structure"""

        categories = {}

        # Navigation Category
        navigation_category = WorkflowCategory(
            name="NAVIGATION",
            morphisms={"NAVIGATION", "BUFFER_SWITCH", "FUZZY_SEARCH"},
            composition_rules=[
                ("BUFFER_SWITCH", "NAVIGATION"),  # Switch then navigate
                ("FUZZY_SEARCH", "BUFFER_SWITCH"),  # Search then switch
            ],
            invariants={"point_preservation": "navigation preserves buffer content"},
        )
        categories["NAVIGATION"] = navigation_category

        # Text Editing Category
        editing_category = WorkflowCategory(
            name="TEXT_EDITING",
            morphisms={"TEXT_INSERT", "TEXT_DELETE", "NAVIGATION"},
            composition_rules=[
                ("NAVIGATION", "TEXT_INSERT"),  # Navigate then insert
                ("TEXT_DELETE", "TEXT_INSERT"),  # Delete then insert
            ],
            invariants={"buffer_modification": "editing changes buffer content"},
        )
        categories["TEXT_EDITING"] = editing_category

        return categories

    def generate_unconscious_suggestions(
        self, current_context: Dict[str, str]
    ) -> List[str]:
        """Generate workflow suggestions unconsciously based on learned patterns"""

        # This is the holy grail - unconscious workflow synthesis
        patterns = self.discover_command_patterns()

        suggestions = []

        # Find patterns matching current context
        for pattern in patterns:
            if pattern.frequency >= 5:  # Only suggest well-established patterns
                # Convert back to natural language
                natural_suggestion = self._pattern_to_natural_language(pattern)
                suggestions.append(natural_suggestion)

        return suggestions[:3]  # Top 3 unconscious suggestions


# Example usage for unconscious workflow discovery
if __name__ == "__main__":
    engine = WorkflowSynthesisEngine()

    print("🧠 **DISCOVERING UNCONSCIOUS WORKFLOW PATTERNS**")

    # Discover patterns from Redis logs
    patterns = engine.discover_command_patterns()

    print(f"\n📊 Found {len(patterns)} workflow patterns")
    for pattern in patterns[:5]:
        print(
            f"Pattern: {' → '.join(pattern.sequence)} (frequency: {pattern.frequency})"
        )

    # Predict next commands
    current_sequence = ["BUFFER_SWITCH", "NAVIGATION"]
    predictions = engine.predict_next_commands(current_sequence, {})

    print(f"\n🔮 **UNCONSCIOUS PREDICTIONS** after {current_sequence}:")
    for cmd, prob in predictions:
        print(f"  {cmd}: {prob:.2%} likelihood")

    # Synthesize complete workflow
    intent = "I want to edit some text in a different buffer"
    synthesized = engine.synthesize_workflow(intent)

    print(f"\n⚡ **SYNTHESIZED WORKFLOW** for '{intent}':")
    print(f"  {' → '.join(synthesized)}")

    # Generate unconscious suggestions
    suggestions = engine.generate_unconscious_suggestions({"buffer": "*scratch*"})

    print(f"\n💭 **UNCONSCIOUS SUGGESTIONS**:")
    for suggestion in suggestions:
        print(f"  {suggestion}")
