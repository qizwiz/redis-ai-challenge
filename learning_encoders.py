#!/usr/bin/env python3
"""
Learning Encoders - Different ways to encode and store AI learning
"""

import json
import time
import hashlib
import redis
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import pickle
import base64


@dataclass
class LearningExperience:
    """Structured representation of a learning experience"""

    command: str
    intent: str
    confidence: float
    method: str
    outcome: str
    key_binding: Optional[str]
    timestamp: float
    context: Dict[str, Any]
    feedback: Optional[str] = None

    def to_hash(self) -> str:
        """Create unique hash for this experience"""
        content = f"{self.command}:{self.intent}:{self.outcome}"
        return hashlib.md5(content.encode()).hexdigest()


class JSONEncoder:
    """Store learning as JSON in Redis"""

    def __init__(self, redis_client):
        self.redis = redis_client

    def store_experience(self, experience: LearningExperience) -> str:
        """Store experience as JSON"""
        exp_id = f"exp_{experience.to_hash()}"

        json_data = {
            "command": experience.command,
            "intent": experience.intent,
            "confidence": experience.confidence,
            "method": experience.method,
            "outcome": experience.outcome,
            "key_binding": experience.key_binding,
            "timestamp": experience.timestamp,
            "context": experience.context,
            "feedback": experience.feedback,
        }

        self.redis.set(exp_id, json.dumps(json_data))
        return exp_id

    def retrieve_experience(self, exp_id: str) -> Optional[LearningExperience]:
        """Retrieve experience from JSON"""
        json_str = self.redis.get(exp_id)
        if not json_str:
            return None

        data = json.loads(json_str)
        return LearningExperience(**data)

    def find_similar(self, command: str, intent: str) -> List[LearningExperience]:
        """Find similar experiences using pattern matching"""
        pattern = f"exp_*"
        experiences = []

        for key in self.redis.scan_iter(match=pattern):
            exp = self.retrieve_experience(key)
            if exp and (command.lower() in exp.command.lower() or exp.intent == intent):
                experiences.append(exp)

        return sorted(experiences, key=lambda x: x.timestamp, reverse=True)


class VectorEncoder:
    """Store learning as vector embeddings for semantic similarity"""

    def __init__(self, redis_client):
        self.redis = redis_client

    def store_experience(self, experience: LearningExperience) -> str:
        """Store experience with semantic embedding"""
        exp_id = f"vec_{experience.to_hash()}"

        # Create embedding
        embedding = self._simple_embedding(experience.command)

        # Store both the experience and its embedding
        exp_data = asdict(experience)
        exp_data["embedding"] = embedding

        self.redis.hset(
            exp_id,
            mapping={"data": json.dumps(exp_data), "embedding": json.dumps(embedding)},
        )

        return exp_id

    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between vectors"""
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = sum(a * a for a in vec1) ** 0.5
        magnitude2 = sum(b * b for b in vec2) ** 0.5

        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0

        return dot_product / (magnitude1 * magnitude2)

    def find_similar(self, command: str, threshold: float = 0.5) -> List[tuple]:
        """Find semantically similar experiences"""
        query_embedding = self._simple_embedding(command)

        similar = []
        pattern = "vec_*"

        for key in self.redis.scan_iter(match=pattern):
            stored_data = self.redis.hgetall(key)
            if "embedding" in stored_data:
                stored_embedding = json.loads(stored_data["embedding"])
                similarity = self.cosine_similarity(query_embedding, stored_embedding)

                if similarity > threshold:
                    exp_data = json.loads(stored_data["data"])
                    experience = LearningExperience(
                        **{k: v for k, v in exp_data.items() if k != "embedding"}
                    )
                    similar.append((experience, similarity))

        return sorted(similar, key=lambda x: x[1], reverse=True)


class GraphEncoder:
    """Store learning as a knowledge graph"""

    def __init__(self, redis_client):
        self.redis = redis_client

    def store_experience(self, experience: LearningExperience) -> str:
        """Store experience as graph nodes and relationships"""
        exp_id = f"graph_{experience.to_hash()}"

        # Create nodes
        command_node = f"cmd:{hashlib.md5(experience.command.encode()).hexdigest()[:8]}"
        intent_node = f"intent:{experience.intent}"
        outcome_node = f"outcome:{experience.outcome}"

        # Store nodes
        self.redis.hset(
            command_node,
            mapping={
                "type": "command",
                "text": experience.command,
                "timestamp": str(experience.timestamp),
            },
        )

        self.redis.hset(
            intent_node,
            mapping={
                "type": "intent",
                "name": experience.intent,
                "confidence": str(experience.confidence),
            },
        )

        self.redis.hset(
            outcome_node,
            mapping={
                "type": "outcome",
                "result": experience.outcome,
                "key_binding": experience.key_binding or "",
            },
        )

        # Store relationships
        self.redis.sadd(f"rel:{command_node}:HAS_INTENT", intent_node)
        self.redis.sadd(f"rel:{intent_node}:PRODUCES", outcome_node)
        self.redis.sadd(f"rel:{outcome_node}:FROM_COMMAND", command_node)

        # Store experience metadata
        self.redis.hset(
            exp_id,
            mapping={
                "command_node": command_node,
                "intent_node": intent_node,
                "outcome_node": outcome_node,
                "experience_data": json.dumps(asdict(experience)),
            },
        )

        return exp_id

    def find_patterns(self, intent: str) -> List[Dict]:
        """Find command patterns for a given intent"""
        intent_node = f"intent:{intent}"

        # Find all outcomes for this intent
        outcomes = self.redis.smembers(f"rel:{intent_node}:PRODUCES")

        patterns = []
        for outcome_node in outcomes:
            outcome_data = self.redis.hgetall(outcome_node)

            # Find commands that led to this outcome
            commands = self.redis.smembers(f"rel:{outcome_node}:FROM_COMMAND")

            pattern = {
                "intent": intent,
                "outcome": outcome_data.get("result"),
                "key_binding": outcome_data.get("key_binding"),
                "example_commands": [],
            }

            for cmd_node in commands:
                cmd_data = self.redis.hgetall(cmd_node)
                if cmd_data:
                    pattern["example_commands"].append(cmd_data.get("text"))

            patterns.append(pattern)

        return patterns


class HomoiconicEncoder:
    """Store learning as executable Lisp-like structures"""

    def __init__(self, redis_client):
        self.redis = redis_client

    def store_experience(self, experience: LearningExperience) -> str:
        """Store experience as executable code"""
        exp_id = f"lisp_{experience.to_hash()}"

        # Encode as Lisp-like structure
        lisp_structure = [
            "learn",
            ["command", experience.command],
            ["intent", experience.intent],
            ["confidence", experience.confidence],
            ["outcome", experience.outcome],
            ["key-binding", experience.key_binding or "nil"],
            ["timestamp", experience.timestamp],
            [
                "if",
                ["successful?", experience.outcome],
                ["strengthen-confidence", experience.intent],
                ["weaken-confidence", experience.intent],
            ],
        ]

        # Store as executable code
        self.redis.set(exp_id, json.dumps(lisp_structure))

        # Add to executable patterns
        if experience.outcome == "success":
            pattern_key = f"pattern:{experience.intent}"
            pattern = [
                "define-pattern",
                experience.intent,
                ["match", experience.command],
                ["execute", experience.key_binding],
                ["confidence", experience.confidence],
            ]
            self.redis.sadd(pattern_key, json.dumps(pattern))

        return exp_id

    def execute_pattern(self, command: str, intent: str) -> Optional[str]:
        """Find and execute a pattern"""
        pattern_key = f"pattern:{intent}"
        patterns = self.redis.smembers(pattern_key)

        for pattern_json in patterns:
            pattern = json.loads(pattern_json)

            # Simple pattern matching (could be much more sophisticated)
            if len(pattern) >= 4 and pattern[2][0] == "match":
                pattern_command = pattern[2][1]
                if any(
                    word in command.lower() for word in pattern_command.lower().split()
                ):
                    # Found a match, return the key binding
                    if len(pattern) >= 4 and pattern[3][0] == "execute":
                        return pattern[3][1]

        return None


def demonstrate_encoders():
    """Demonstrate different learning encoding approaches"""

    print("🧠 LEARNING ENCODING DEMONSTRATIONS")
    print("=" * 50)

    redis_client = redis.Redis(decode_responses=True)

    # Sample experience
    experience = LearningExperience(
        command="move cursor forward",
        intent="navigation",
        confidence=0.95,
        method="smart_local",
        outcome="success",
        key_binding="C-f",
        timestamp=time.time(),
        context={"file": "test.py", "line": 10},
    )

    print("📚 Sample Experience:")
    print(f"   Command: {experience.command}")
    print(f"   Intent: {experience.intent}")
    print(f"   Outcome: {experience.outcome}")
    print(f"   Key Binding: {experience.key_binding}")
    print()

    # 1. JSON Encoding
    print("1. 📄 JSON Encoding:")
    json_encoder = JSONEncoder(redis_client)
    json_id = json_encoder.store_experience(experience)
    retrieved = json_encoder.retrieve_experience(json_id)
    print(f"   Stored: {json_id}")
    print(f"   Retrieved: {retrieved.command if retrieved else 'None'}")

    # 2. Vector Encoding
    print("\n2. 🔢 Vector Encoding:")
    vector_encoder = VectorEncoder(redis_client)
    vector_id = vector_encoder.store_experience(experience)
    similar = vector_encoder.find_similar("go forward", threshold=0.3)
    print(f"   Stored: {vector_id}")
    print(f"   Similar commands found: {len(similar)}")
    for exp, similarity in similar[:2]:
        print(f"      • {exp.command} (similarity: {similarity:.2f})")

    # 3. Graph Encoding
    print("\n3. 🕸️  Graph Encoding:")
    graph_encoder = GraphEncoder(redis_client)
    graph_id = graph_encoder.store_experience(experience)
    patterns = graph_encoder.find_patterns("navigation")
    print(f"   Stored: {graph_id}")
    print(f"   Navigation patterns found: {len(patterns)}")
    for pattern in patterns[:2]:
        print(f"      • {pattern['outcome']} → {pattern['key_binding']}")

    # 4. Homoiconic Encoding
    print("\n4. 🎭 Homoiconic Encoding:")
    homoiconic_encoder = HomoiconicEncoder(redis_client)
    lisp_id = homoiconic_encoder.store_experience(experience)
    executable = homoiconic_encoder.execute_pattern("move forward", "navigation")
    print(f"   Stored: {lisp_id}")
    print(f"   Executable result: {executable}")

    print(f"\n" + "=" * 50)
    print("🎯 ENCODING COMPARISON:")
    print("📄 JSON: Fast, readable, simple queries")
    print("🔢 Vector: Semantic similarity, ML-friendly")
    print("🕸️  Graph: Complex relationships, pattern discovery")
    print("🎭 Homoiconic: Executable code, self-modifying")


if __name__ == "__main__":
    demonstrate_encoders()
