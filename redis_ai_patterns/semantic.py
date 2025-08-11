"""
Semantic Extraction - Extract semantic understanding from documentation
"""

import redis
import json
import subprocess
import re
import time
from typing import Dict, List, Set, Tuple, Any
from collections import defaultdict
from .core import RedisAIBase


class SemanticExtractor(RedisAIBase):
    """Extract semantic taxonomies and store in Redis"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._init_patterns()

    def _init_patterns(self):
        """Initialize semantic extraction patterns"""
        self.semantic_patterns = {
            "navigation": {
                "keywords": [
                    "forward",
                    "backward",
                    "up",
                    "down",
                    "next",
                    "previous",
                    "goto",
                    "move",
                    "forward-char",
                ],
                "patterns": [r"move.*cursor", r"go.*to", r"navigate.*to", r"jump.*to"],
            },
            "editing": {
                "keywords": [
                    "insert",
                    "delete",
                    "kill",
                    "yank",
                    "copy",
                    "cut",
                    "paste",
                    "replace",
                ],
                "patterns": [r"insert.*text", r"delete.*", r"kill.*", r"replace.*with"],
            },
            "file_operations": {
                "keywords": ["open", "save", "close", "find", "visit", "write", "load"],
                "patterns": [r"find.*file", r"save.*", r"open.*", r"visit.*file"],
            },
            "buffer_management": {
                "keywords": ["buffer", "switch", "select", "create", "kill-buffer"],
                "patterns": [r"switch.*buffer", r"create.*buffer", r"buffer.*"],
            },
            "search_replace": {
                "keywords": ["search", "replace", "query", "occur", "grep"],
                "patterns": [r"search.*for", r"replace.*", r"find.*replace"],
            },
        }

    def extract_from_help(self, help_topic: str) -> Dict[str, Any]:
        """Extract semantic information from Emacs help"""
        try:
            # Get help output from Emacs
            cmd = ["emacs", "--batch", "--eval", f"(describe-function '{help_topic})"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

            if result.returncode == 0:
                return self._parse_help_text(result.stdout, help_topic)

        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        return {"topic": help_topic, "categories": [], "confidence": 0.0}

    def _parse_help_text(self, help_text: str, topic: str) -> Dict[str, Any]:
        """Parse help text and extract semantic categories"""
        categories = []
        confidence_scores = []

        help_lower = help_text.lower()

        for category, patterns in self.semantic_patterns.items():
            category_score = 0

            # Check keywords
            for keyword in patterns["keywords"]:
                if keyword in help_lower:
                    category_score += 1

            # Check regex patterns
            for pattern in patterns["patterns"]:
                if re.search(pattern, help_lower):
                    category_score += 2

            if category_score > 0:
                categories.append(category)
                confidence_scores.append(category_score)

        overall_confidence = (
            sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
        )

        return {
            "topic": topic,
            "categories": categories,
            "confidence": min(overall_confidence / 10.0, 1.0),  # Normalize to 0-1
            "raw_text": help_text[:500],  # Store sample for analysis
        }

    def build_taxonomy(self, functions: List[str]) -> Dict[str, Any]:
        """Build complete semantic taxonomy from function list"""
        taxonomy = defaultdict(list)
        processed_count = 0

        for func in functions:
            semantic_info = self.extract_from_help(func)

            # Store in Redis
            self.store_json(f"semantic:{func}", semantic_info)

            # Build taxonomy
            for category in semantic_info["categories"]:
                taxonomy[category].append(
                    {"function": func, "confidence": semantic_info["confidence"]}
                )

            processed_count += 1

            if processed_count % 10 == 0:
                print(f"Processed {processed_count}/{len(functions)} functions")

        # Store complete taxonomy
        taxonomy_dict = dict(taxonomy)
        self.store_json("complete_taxonomy", taxonomy_dict)

        return taxonomy_dict

    def classify_intent(self, user_input: str) -> Dict[str, Any]:
        """Classify user intent based on semantic taxonomy"""
        user_lower = user_input.lower()
        intent_scores = defaultdict(float)

        for category, patterns in self.semantic_patterns.items():
            score = 0

            # Check direct keyword matches
            for keyword in patterns["keywords"]:
                if keyword in user_lower:
                    score += 1

            # Check pattern matches
            for pattern in patterns["patterns"]:
                if re.search(pattern, user_lower):
                    score += 2

            if score > 0:
                intent_scores[category] = score

        # Find best match
        if intent_scores:
            best_category = max(intent_scores.keys(), key=lambda k: intent_scores[k])
            confidence = min(intent_scores[best_category] / 5.0, 1.0)

            return {
                "intent": best_category,
                "confidence": confidence,
                "alternatives": dict(intent_scores),
            }
        else:
            return {"intent": "unknown", "confidence": 0.0, "alternatives": {}}

    def get_suggestions(self, category: str, limit: int = 5) -> List[Dict]:
        """Get function suggestions for a category"""
        taxonomy = self.get_json("complete_taxonomy")
        if not taxonomy or category not in taxonomy:
            return []

        # Sort by confidence and return top suggestions
        suggestions = taxonomy[category]
        suggestions.sort(key=lambda x: x["confidence"], reverse=True)

        return suggestions[:limit]

    def analyze_usage_patterns(self, session_id: str) -> Dict[str, Any]:
        """Analyze user's command usage patterns"""
        # Get recent commands from Redis streams
        try:
            events = self.redis_client.xrevrange(self.key("events:commands"), count=100)

            category_counts = defaultdict(int)
            command_counts = defaultdict(int)

            for event_id, fields in events:
                if "command" in fields:
                    command = fields["command"]
                    command_counts[command] += 1

                    # Classify command
                    intent_info = self.classify_intent(command)
                    if intent_info["confidence"] > 0.3:
                        category_counts[intent_info["intent"]] += 1

            return {
                "most_used_categories": dict(category_counts),
                "most_used_commands": dict(command_counts),
                "total_commands": len(events),
                "session_id": session_id,
            }

        except:
            return {"error": "Could not analyze usage patterns"}

    def suggest_workflow_improvements(self, usage_patterns: Dict) -> List[str]:
        """Suggest workflow improvements based on usage"""
        suggestions = []

        categories = usage_patterns.get("most_used_categories", {})

        if "navigation" in categories and categories["navigation"] > 10:
            suggestions.append(
                "Consider learning keyboard shortcuts for faster navigation"
            )

        if "file_operations" in categories and categories["file_operations"] > 5:
            suggestions.append(
                "Try using project-wide search tools like grep or projectile"
            )

        if "editing" in categories and categories["editing"] > 15:
            suggestions.append(
                "Consider using snippets or templates for repetitive editing"
            )

        return suggestions
