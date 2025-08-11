#!/usr/bin/env python3
"""
Proper NLP Architecture for Redis-Emacs MCP
Entities, Intents, Utterances with Spacemacs/Evil context
"""

import re
import spacy
from typing import Dict, List, Any
from dataclasses import dataclass


@dataclass
class Entity:
    type: str  # BUFFER, POSITION, COMMAND, OBJECT, ATTRIBUTE
    value: str  # "scratch", "line 50", "create", "aquarium", "physics"
    confidence: float


@dataclass
class Intent:
    action: str  # CREATE, MOVE, EDIT, ANIMATE, DEBUG, QUERY
    target: str  # BUFFER, TEXT, OBJECT, WINDOW
    confidence: float


@dataclass
class EmacsContext:
    editor: str  # "spacemacs" | "emacs"
    evil_mode: bool  # True/False
    current_buffer: str  # Buffer name
    current_mode: str  # major-mode
    position: tuple  # (line, column)
    window_config: dict  # Window layout


class RedisEmacsNLP:
    def __init__(self):
        # Load spaCy model for proper NLP
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            print(
                "⚠️  spaCy model not found. Install with: python -m spacy download en_core_web_sm"
            )
            self.nlp = None

        # Entity patterns for Emacs/development context
        self.entity_patterns = {
            "BUFFER": [r"\*\w+\*", r"scratch", r"buffer", r"\.el$", r"\.py$"],
            "POSITION": [r"line \d+", r"\d+:\d+", r"point \d+"],
            "COMMAND": [r"C-\w+", r"M-\w+", r"SPC", r"evil-\w+"],
            "OBJECT": ["aquarium", "container", "animation", "physics", "window"],
            "ACTION": ["create", "make", "build", "move", "edit", "delete", "animate"],
        }

        # Intent classification patterns
        self.intent_patterns = {
            "CREATE": ["create", "make", "build", "generate"],
            "MOVE": ["go", "move", "navigate", "jump", "switch"],
            "EDIT": ["edit", "change", "modify", "update", "insert"],
            "ANIMATE": ["animate", "move", "swim", "physics"],
            "DEBUG": ["fix", "debug", "error", "problem"],
            "QUERY": ["what", "where", "how", "show", "get"],
        }

    def extract_entities(self, text: str) -> List[Entity]:
        """Extract structured entities from natural language"""
        entities = []

        # Use spaCy if available
        if self.nlp:
            doc = self.nlp(text)
            for ent in doc.ents:
                entities.append(
                    Entity(
                        type=ent.label_,
                        value=ent.text,
                        confidence=0.8,  # spaCy confidence
                    )
                )

        # Custom Emacs/development patterns
        for entity_type, patterns in self.entity_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    entities.append(
                        Entity(
                            type=entity_type,
                            value=match.group(),
                            confidence=0.9,  # High confidence for exact patterns
                        )
                    )

        return entities

    def classify_intent(self, text: str, entities: List[Entity]) -> Intent:
        """Classify user intent based on text and entities"""

        text_lower = text.lower()

        # Score each intent
        intent_scores = {}
        for intent, keywords in self.intent_patterns.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)

            # Boost score based on entities
            if intent == "CREATE" and any(e.type == "OBJECT" for e in entities):
                score += 2
            elif intent == "MOVE" and any(e.type == "POSITION" for e in entities):
                score += 2
            elif intent == "EDIT" and any(e.type == "BUFFER" for e in entities):
                score += 1

            intent_scores[intent] = score

        # Return highest scoring intent
        best_intent = max(intent_scores.items(), key=lambda x: x[1])

        return Intent(
            action=best_intent[0],
            target="GENERAL",  # Could be more sophisticated
            confidence=min(best_intent[1] / 3.0, 1.0),  # Normalize
        )

    def parse_utterance(self, text: str, context: EmacsContext) -> Dict[str, Any]:
        """Parse complete utterance with context awareness"""

        entities = self.extract_entities(text)
        intent = self.classify_intent(text, entities)

        # Evil mode command mapping
        evil_commands = {}
        if context.evil_mode:
            evil_commands = {
                "create": "i",  # Insert mode for creation
                "move": (
                    "gg"
                    if "beginning" in text
                    else "G" if "end" in text else "j" if "down" in text else "k"
                ),
                "edit": "cw" if "word" in text else "cc" if "line" in text else "c",
            }

        return {
            "entities": entities,
            "intent": intent,
            "context": context,
            "evil_commands": evil_commands,
            "mcp_decomposition": self.suggest_mcp_calls(intent, entities),
            "confidence": intent.confidence,
        }

    def suggest_mcp_calls(self, intent: Intent, entities: List[Entity]) -> List[str]:
        """Suggest structured MCP tool calls"""

        if intent.action == "CREATE":
            objects = [e.value for e in entities if e.type == "OBJECT"]
            if "aquarium" in objects:
                return [
                    "redis-emacs: Create container with boundaries",
                    "redis-emacs: Initialize physics state in Redis",
                    "redis-emacs: Start animation loop",
                    "redis-emacs: Enable collision detection",
                ]

        return ["redis-emacs: Execute natural language command"]


# Example usage
if __name__ == "__main__":
    nlp = RedisEmacsNLP()

    context = EmacsContext(
        editor="spacemacs",
        evil_mode=True,
        current_buffer="*scratch*",
        current_mode="lisp-interaction-mode",
        position=(1, 1),
        window_config={},
    )

    result = nlp.parse_utterance("create a physics aquarium in scratch buffer", context)

    print("🧠 NLP Analysis:")
    print(
        f"Intent: {result['intent'].action} (confidence: {result['intent'].confidence:.2f})"
    )
    print(f"Entities: {[(e.type, e.value) for e in result['entities']]}")
    print(f"Evil mode commands: {result['evil_commands']}")
    print(f"MCP decomposition: {result['mcp_decomposition']}")
