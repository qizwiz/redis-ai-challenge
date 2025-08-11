#!/usr/bin/env python3
"""
Docstring Synthesis Engine
Mine Emacs docstrings to synthesize utterances, intents, and entities
Pre-compose semantic mappings for zero-delay prediction
"""

import re
import redis
import subprocess
import json
from typing import Dict, List, Set, Tuple
from collections import defaultdict, Counter
from dataclasses import dataclass
import networkx as nx


@dataclass
class SemanticMapping:
    canonical_command: str
    docstring: str
    synthesized_utterances: List[str]
    extracted_entities: Set[str]
    intent_category: str
    related_commands: List[str]
    confidence: float


class DocstringSynthesisEngine:
    def __init__(self):
        self.redis_client = redis.Redis(decode_responses=True)
        self.semantic_graph = nx.DiGraph()

        # Entity extraction patterns from docstrings
        self.entity_patterns = {
            "BUFFER": r"\bbuffer\b|\bfile\b",
            "POSITION": r"\bpoint\b|\bline\b|\bcolumn\b|\bcharacter\b",
            "TEXT": r"\btext\b|\bstring\b|\bword\b|\bregion\b",
            "WINDOW": r"\bwindow\b|\bframe\b|\bsplit\b",
            "DIRECTION": r"\bforward\b|\bbackward\b|\bnext\b|\bprevious\b|\bup\b|\bdown\b|\bleft\b|\bright\b",
            "ACTION": r"\bmove\b|\bgo\b|\bjump\b|\bdelete\b|\binsert\b|\bkill\b|\byank\b|\bundo\b|\bsearch\b",
        }

        # Intent categories based on action verbs
        self.intent_categories = {
            "NAVIGATION": [
                "move",
                "go",
                "jump",
                "forward",
                "backward",
                "next",
                "previous",
            ],
            "EDITING": ["insert", "delete", "kill", "yank", "replace", "change"],
            "BUFFER": ["switch", "open", "close", "save", "revert"],
            "WINDOW": ["split", "delete", "resize", "switch"],
            "SEARCH": ["search", "find", "replace", "query"],
            "UNDO": ["undo", "redo", "revert"],
        }

    def harvest_emacs_docstrings(self) -> Dict[str, str]:
        """Harvest docstrings from live Emacs instance"""

        print("🔍 Harvesting Emacs docstrings...")

        # Get list of interesting functions
        elisp_query = """
(let ((functions '()))
  (mapatoms 
   (lambda (symbol)
     (when (and (fboundp symbol)
                (not (eq (car-safe (symbol-function symbol)) 'autoload))
                (documentation symbol))
       (push (list (symbol-name symbol) 
                   (documentation symbol)) functions))))
  (json-encode (seq-take functions 500)))  ; Limit for performance
"""

        try:
            result = subprocess.run(
                ["emacsclient", "--eval", elisp_query],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0:
                # Parse JSON result
                functions_data = json.loads(
                    result.stdout.strip().strip('"').replace('\\"', '"')
                )

                docstrings = {}
                for func_name, docstring in functions_data:
                    if docstring and len(docstring) > 20:  # Skip tiny docs
                        docstrings[func_name] = docstring

                print(f"✅ Harvested {len(docstrings)} docstrings")
                return docstrings

        except Exception as e:
            print(f"❌ Error harvesting docstrings: {e}")

        return {}

    def synthesize_utterances_from_docstring(
        self, command: str, docstring: str
    ) -> List[str]:
        """Generate natural language utterances from docstring"""

        utterances = []
        doc_lower = docstring.lower()

        # Extract the main action description (usually first sentence)
        first_sentence = docstring.split(".")[0].strip()

        # Direct mapping from docstring
        if first_sentence:
            utterances.append(first_sentence.lower())

        # Generate variations based on patterns
        variations = []

        # "Move point to..." → "go to...", "move to...", "jump to..."
        if "move point to" in doc_lower:
            target = re.search(r"move point to (.+?)(?:\.|$)", doc_lower)
            if target:
                location = target.group(1).strip()
                variations.extend(
                    [
                        f"go to {location}",
                        f"move to {location}",
                        f"jump to {location}",
                        f"navigate to {location}",
                    ]
                )

        # "Delete..." → "remove...", "kill...", "erase..."
        if "delete" in doc_lower:
            delete_match = re.search(r"delete (.+?)(?:\.|$)", doc_lower)
            if delete_match:
                target = delete_match.group(1).strip()
                variations.extend(
                    [
                        f"remove {target}",
                        f"kill {target}",
                        f"erase {target}",
                        f"delete {target}",
                    ]
                )

        # "Insert..." → "add...", "type...", "put..."
        if "insert" in doc_lower:
            insert_match = re.search(r"insert (.+?)(?:\.|$)", doc_lower)
            if insert_match:
                target = insert_match.group(1).strip()
                variations.extend(
                    [
                        f"add {target}",
                        f"type {target}",
                        f"put {target}",
                        f"insert {target}",
                    ]
                )

        # Command-specific shortcuts
        shortcuts = self._generate_command_shortcuts(command, doc_lower)
        variations.extend(shortcuts)

        utterances.extend(variations)

        # Clean and deduplicate
        cleaned = []
        for utterance in utterances:
            cleaned_utterance = re.sub(r"\s+", " ", utterance.strip())
            if cleaned_utterance and len(cleaned_utterance) > 3:
                cleaned.append(cleaned_utterance)

        return list(set(cleaned))  # Remove duplicates

    def _generate_command_shortcuts(self, command: str, docstring: str) -> List[str]:
        """Generate common shortcuts and slang for commands"""

        shortcuts = []

        # Map common commands to casual expressions
        casual_mappings = {
            "end-of-line": ["control e", "ctrl e", "c-e", "end of line", "eol"],
            "beginning-of-line": ["control a", "ctrl a", "c-a", "start of line", "bol"],
            "undo": ["undo that", "ctrl underscore", "c-underscore", "revert that"],
            "switch-to-buffer": ["switch buffer", "go to buffer", "open buffer"],
            "kill-line": ["kill line", "ctrl k", "c-k", "delete line"],
            "yank": ["paste", "ctrl y", "c-y", "yank that"],
            "search-forward": ["search", "find", "ctrl s", "c-s"],
            "goto-line": ["go to line", "jump to line", "line number"],
            "split-window-right": ["split right", "vertical split", "divide window"],
            "delete-other-windows": ["only window", "lone window", "single window"],
        }

        if command in casual_mappings:
            shortcuts.extend(casual_mappings[command])

        # Generate based on key bindings if available
        if "C-" in docstring:
            keybinding = re.search(r"C-[a-zA-Z]", docstring)
            if keybinding:
                key = keybinding.group()
                shortcuts.append(f"control {key[-1]}")
                shortcuts.append(f"ctrl {key[-1]}")

        return shortcuts

    def extract_entities_from_docstring(self, docstring: str) -> Set[str]:
        """Extract semantic entities from docstring"""

        entities = set()
        doc_lower = docstring.lower()

        for entity_type, pattern in self.entity_patterns.items():
            matches = re.findall(pattern, doc_lower)
            for match in matches:
                entities.add(f"{entity_type}:{match}")

        return entities

    def classify_intent(self, command: str, docstring: str) -> str:
        """Classify the intent category of a command"""

        doc_lower = docstring.lower()

        # Score each intent category
        scores = defaultdict(int)

        for intent, keywords in self.intent_categories.items():
            for keyword in keywords:
                if keyword in doc_lower:
                    scores[intent] += 1
                if keyword in command.lower():
                    scores[intent] += 2  # Command name is stronger signal

        # Return highest scoring intent, or GENERAL if tie
        if scores:
            return max(scores.items(), key=lambda x: x[1])[0]

        return "GENERAL"

    def find_related_commands(
        self, command: str, docstring: str, all_docstrings: Dict[str, str]
    ) -> List[str]:
        """Find semantically related commands based on docstring similarity"""

        related = []
        doc_lower = docstring.lower()

        # Extract key concepts from this docstring
        key_concepts = set()
        for entity_type, pattern in self.entity_patterns.items():
            matches = re.findall(pattern, doc_lower)
            key_concepts.update(matches)

        # Find other commands with overlapping concepts
        for other_command, other_doc in all_docstrings.items():
            if other_command == command:
                continue

            other_doc_lower = other_doc.lower()

            # Count concept overlap
            overlap = 0
            for concept in key_concepts:
                if concept in other_doc_lower:
                    overlap += 1

            # If significant overlap, consider related
            if overlap >= 2:
                related.append(other_command)

        return related[:5]  # Top 5 most related

    def build_semantic_mappings(self) -> List[SemanticMapping]:
        """Build complete semantic mappings from docstrings"""

        print("🧠 Building semantic mappings from docstrings...")

        # Harvest docstrings
        docstrings = self.harvest_emacs_docstrings()

        if not docstrings:
            print("❌ No docstrings harvested")
            return []

        mappings = []

        for command, docstring in docstrings.items():
            # Synthesize utterances
            utterances = self.synthesize_utterances_from_docstring(command, docstring)

            # Extract entities
            entities = self.extract_entities_from_docstring(docstring)

            # Classify intent
            intent = self.classify_intent(command, docstring)

            # Find related commands
            related = self.find_related_commands(command, docstring, docstrings)

            # Calculate confidence based on utterance count and docstring quality
            confidence = min(len(utterances) * 0.1 + len(docstring) * 0.001, 1.0)

            mapping = SemanticMapping(
                canonical_command=command,
                docstring=docstring,
                synthesized_utterances=utterances,
                extracted_entities=entities,
                intent_category=intent,
                related_commands=related,
                confidence=confidence,
            )

            mappings.append(mapping)

        print(f"✅ Built {len(mappings)} semantic mappings")
        return mappings

    def store_mappings_in_redis(self, mappings: List[SemanticMapping]):
        """Store semantic mappings in Redis for fast lookup"""

        print("💾 Storing semantic mappings in Redis...")

        # Clear existing mappings
        self.redis_client.delete("emacs:semantic:mappings")
        self.redis_client.delete("emacs:utterance:lookup")

        for mapping in mappings:
            # Store complete mapping
            mapping_key = f"emacs:semantic:mappings:{mapping.canonical_command}"
            self.redis_client.hset(
                mapping_key,
                mapping={
                    "docstring": mapping.docstring,
                    "utterances": json.dumps(mapping.synthesized_utterances),
                    "entities": json.dumps(list(mapping.extracted_entities)),
                    "intent": mapping.intent_category,
                    "related": json.dumps(mapping.related_commands),
                    "confidence": mapping.confidence,
                },
            )

            # Create reverse lookup: utterance → command
            for utterance in mapping.synthesized_utterances:
                self.redis_client.hset(
                    "emacs:utterance:lookup", utterance, mapping.canonical_command
                )

        print(f"✅ Stored {len(mappings)} mappings in Redis")

    def predict_next_actions(self, current_command: str) -> List[Tuple[str, float]]:
        """Predict likely next actions based on semantic relationships"""

        # Get related commands from Redis
        mapping_key = f"emacs:semantic:mappings:{current_command}"
        mapping_data = self.redis_client.hgetall(mapping_key)

        if not mapping_data:
            return []

        related_commands = json.loads(mapping_data.get("related", "[]"))

        # Score predictions based on semantic similarity and usage patterns
        predictions = []
        for related_cmd in related_commands:
            # Simple scoring for now - could be much more sophisticated
            score = 0.8 if related_cmd else 0.0
            predictions.append((related_cmd, score))

        return sorted(predictions, key=lambda x: x[1], reverse=True)

    def lookup_utterance(self, natural_language: str) -> str:
        """Fast lookup: natural language → canonical command"""

        # Direct lookup first
        canonical = self.redis_client.hget(
            "emacs:utterance:lookup", natural_language.lower()
        )

        if canonical:
            return canonical

        # Fuzzy matching for partial matches
        all_utterances = self.redis_client.hgetall("emacs:utterance:lookup")

        nl_lower = natural_language.lower()

        # Find best partial match
        best_match = None
        best_score = 0

        for utterance, command in all_utterances.items():
            # Simple word overlap scoring
            nl_words = set(nl_lower.split())
            utterance_words = set(utterance.split())

            overlap = len(nl_words & utterance_words)
            total = len(nl_words | utterance_words)

            if total > 0:
                score = overlap / total
                if score > best_score and score > 0.5:  # At least 50% word overlap
                    best_score = score
                    best_match = command

        return best_match


# Usage example
if __name__ == "__main__":
    engine = DocstringSynthesisEngine()

    print("🚀 **DOCSTRING SYNTHESIS ENGINE**")
    print("Mining Emacs docstrings for semantic intelligence...")

    # Build mappings from docstrings
    mappings = engine.build_semantic_mappings()

    # Store in Redis for fast lookup
    engine.store_mappings_in_redis(mappings)

    # Test utterance lookup
    test_utterances = [
        "move to end of line",
        "control e",
        "go to beginning",
        "undo that",
        "switch buffer",
    ]

    print(f"\n🧪 **TESTING UTTERANCE LOOKUP**:")
    for utterance in test_utterances:
        canonical = engine.lookup_utterance(utterance)
        print(f"  '{utterance}' → {canonical}")

    # Test prediction
    print(f"\n🔮 **PREDICTION TESTING**:")
    current = "end-of-line"
    predictions = engine.predict_next_actions(current)
    print(f"After '{current}', likely next actions:")
    for action, score in predictions[:3]:
        print(f"  {action}: {score:.2%}")

    print(f"\n📊 **SUMMARY:**")
    print(f"  Mappings created: {len(mappings)}")

    # Show sample mapping
    if mappings:
        sample = mappings[0]
        print(f"\n📝 **SAMPLE MAPPING**:")
        print(f"Command: {sample.canonical_command}")
        print(f"Intent: {sample.intent_category}")
        print(f"Utterances: {sample.synthesized_utterances[:3]}...")
        print(f"Related: {sample.related_commands[:3]}")
