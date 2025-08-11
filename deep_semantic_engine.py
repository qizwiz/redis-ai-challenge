#!/usr/bin/env python3
"""
Deep Semantic Engine - Real understanding using embeddings + reasoning
"""

import json
import time
import numpy as np
import redis
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import requests
import hashlib
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
import torch


@dataclass
class SemanticConcept:
    """A concept with semantic embeddings"""

    name: str
    definition: str
    embedding: np.ndarray
    examples: List[str]
    example_embeddings: List[np.ndarray]
    confidence: float
    relationships: Dict[str, List[str]]
    usage_count: int
    last_updated: float


class DeepSemanticEngine:
    """Real semantic understanding using embeddings and reasoning"""

    def __init__(self):
        self.redis_client = redis.Redis(decode_responses=True)
        self.session_id = f"deep_semantic_{int(time.time())}"

        # Load semantic model
        print("🧠 Loading sentence transformer model...")
        self.model = SentenceTransformer("all-MiniLM-L6-v2")  # Fast, good quality
        print("✅ Semantic model loaded")

        # Semantic similarity thresholds
        self.concept_threshold = 0.7
        self.example_threshold = 0.6
        self.reasoning_threshold = 0.5

        # Initialize semantic concepts
        self._initialize_semantic_concepts()

        print(f"🧠 Deep Semantic Engine initialized (session: {self.session_id})")

    def _initialize_semantic_concepts(self):
        """Initialize concepts with semantic embeddings"""

        base_concepts = {
            "cursor_navigation": {
                "definition": "Moving the text cursor to different positions in a document",
                "examples": [
                    "move cursor forward",
                    "go to next line",
                    "jump to beginning of line",
                    "navigate to end of file",
                    "cursor backward one word",
                ],
            },
            "file_management": {
                "definition": "Operations for saving, opening, and managing files and documents",
                "examples": [
                    "save the current file",
                    "open a new document",
                    "close this buffer",
                    "create a new file",
                    "backup important data",
                ],
            },
            "version_control": {
                "definition": "Git and version control operations for tracking code changes",
                "examples": [
                    "commit these changes",
                    "show git status",
                    "push to repository",
                    "check commit history",
                    "merge branch",
                ],
            },
            "text_editing": {
                "definition": "Modifying, inserting, or deleting text content",
                "examples": [
                    "delete this word",
                    "insert new text here",
                    "replace selected text",
                    "cut and paste",
                    "undo last change",
                ],
            },
            "code_analysis": {
                "definition": "Understanding, debugging, and analyzing source code",
                "examples": [
                    "find function definition",
                    "debug this error",
                    "analyze code structure",
                    "check syntax errors",
                    "refactor this function",
                ],
            },
        }

        print("🧠 Creating semantic embeddings for concepts...")

        for concept_name, concept_data in base_concepts.items():
            # Create embeddings for definition and examples
            definition = concept_data["definition"]
            examples = concept_data["examples"]

            definition_embedding = self.model.encode(definition)
            example_embeddings = [self.model.encode(example) for example in examples]

            concept = SemanticConcept(
                name=concept_name,
                definition=definition,
                embedding=definition_embedding,
                examples=examples,
                example_embeddings=example_embeddings,
                confidence=0.9,
                relationships={},
                usage_count=0,
                last_updated=time.time(),
            )

            self._store_semantic_concept(concept)

        print(f"✅ Initialized {len(base_concepts)} semantic concepts with embeddings")

    def understand_text(
        self, text: str, context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Deep semantic understanding of text"""

        print(f"🧠 Deep understanding: '{text}'")

        # Create embedding for input text
        text_embedding = self.model.encode(text)

        # Find semantic matches
        concept_matches = self._find_semantic_concepts(text, text_embedding)

        # Reason about intent
        reasoning = self._semantic_reasoning(
            text, text_embedding, concept_matches, context or {}
        )

        # Extract semantic entities
        entities = self._extract_semantic_entities(text, text_embedding)

        # Build comprehensive understanding
        understanding = {
            "text": text,
            "embedding": text_embedding.tolist(),  # Store for future similarity
            "concept_matches": concept_matches,
            "semantic_reasoning": reasoning,
            "entities": entities,
            "confidence": reasoning.get("confidence", 0.8),
            "understanding_method": "deep_semantic_embeddings",
            "context": context,
            "timestamp": time.time(),
            "session": self.session_id,
        }

        # Store understanding
        self._store_understanding(understanding)

        # Learn from this interaction
        self._semantic_learning(text, text_embedding, understanding)

        return understanding

    def _find_semantic_concepts(
        self, text: str, text_embedding: np.ndarray
    ) -> List[Dict[str, Any]]:
        """Find semantically similar concepts using embeddings"""

        concept_matches = []

        # Load all stored concepts
        concept_keys = self.redis_client.keys("deep_semantic:concept:*")

        for concept_key in concept_keys:
            concept_data = self.redis_client.get(concept_key)
            if not concept_data:
                continue

            concept_info = json.loads(concept_data)

            # Get concept embedding
            concept_embedding = np.array(concept_info["embedding"])

            # Calculate similarity with definition
            definition_similarity = cosine_similarity(
                text_embedding.reshape(1, -1), concept_embedding.reshape(1, -1)
            )[0][0]

            # Calculate similarity with examples
            example_similarities = []
            for example_embedding_list in concept_info["example_embeddings"]:
                example_embedding = np.array(example_embedding_list)
                example_sim = cosine_similarity(
                    text_embedding.reshape(1, -1), example_embedding.reshape(1, -1)
                )[0][0]
                example_similarities.append(example_sim)

            max_example_similarity = (
                max(example_similarities) if example_similarities else 0
            )
            best_example_idx = (
                example_similarities.index(max_example_similarity)
                if example_similarities
                else -1
            )

            # Overall semantic similarity
            overall_similarity = max(definition_similarity, max_example_similarity)

            if overall_similarity > self.concept_threshold:
                match = {
                    "concept": concept_info["name"],
                    "definition_similarity": float(definition_similarity),
                    "best_example_similarity": float(max_example_similarity),
                    "overall_similarity": float(overall_similarity),
                    "best_example": (
                        concept_info["examples"][best_example_idx]
                        if best_example_idx >= 0
                        else None
                    ),
                    "confidence": float(
                        overall_similarity * concept_info["confidence"]
                    ),
                }
                concept_matches.append(match)

        # Sort by similarity
        concept_matches.sort(key=lambda x: x["overall_similarity"], reverse=True)

        print(f"   🎯 Found {len(concept_matches)} semantic concept matches")
        for match in concept_matches[:3]:
            print(f"      • {match['concept']}: {match['overall_similarity']:.3f}")

        return concept_matches

    def _semantic_reasoning(
        self,
        text: str,
        text_embedding: np.ndarray,
        concept_matches: List[Dict],
        context: Dict,
    ) -> Dict[str, Any]:
        """Perform semantic reasoning about the text"""

        reasoning = {
            "primary_intent": None,
            "confidence": 0.0,
            "reasoning_chain": [],
            "contextual_inferences": [],
            "semantic_categories": [],
        }

        if not concept_matches:
            reasoning["primary_intent"] = "unknown"
            reasoning["confidence"] = 0.1
            reasoning["reasoning_chain"] = ["No semantic matches found"]
            return reasoning

        # Primary intent from best match
        best_match = concept_matches[0]
        reasoning["primary_intent"] = best_match["concept"]
        reasoning["confidence"] = best_match["confidence"]

        # Build reasoning chain
        reasoning["reasoning_chain"] = [
            f"Text most similar to concept '{best_match['concept']}'",
            f"Similarity score: {best_match['overall_similarity']:.3f}",
            f"Best matching example: '{best_match['best_example']}'",
        ]

        # Multiple concept reasoning
        if len(concept_matches) > 1:
            secondary_concepts = [m["concept"] for m in concept_matches[1:3]]
            reasoning["reasoning_chain"].append(
                f"Also relates to: {secondary_concepts}"
            )

        # Contextual inferences
        if context.get("current_file"):
            file_ext = (
                context["current_file"].split(".")[-1]
                if "." in context["current_file"]
                else ""
            )
            if file_ext in ["py", "js", "java", "cpp"]:
                reasoning["contextual_inferences"].append(
                    f"Working in {file_ext} code file"
                )
                if best_match["concept"] in ["cursor_navigation", "text_editing"]:
                    reasoning["contextual_inferences"].append(
                        "Likely code editing task"
                    )

        if context.get("cursor_line"):
            reasoning["contextual_inferences"].append(
                f"Currently at line {context['cursor_line']}"
            )

        # Semantic categories
        for match in concept_matches:
            if match["overall_similarity"] > 0.6:
                reasoning["semantic_categories"].append(match["concept"])

        return reasoning

    def _extract_semantic_entities(
        self, text: str, text_embedding: np.ndarray
    ) -> List[Dict[str, Any]]:
        """Extract entities using semantic understanding"""

        entities = []

        # Semantic entity patterns with embeddings
        entity_patterns = {
            "file_reference": ["file", "document", "buffer", "script", "code"],
            "direction": [
                "forward",
                "backward",
                "up",
                "down",
                "left",
                "right",
                "next",
                "previous",
            ],
            "action": [
                "move",
                "save",
                "open",
                "close",
                "delete",
                "edit",
                "show",
                "commit",
                "push",
            ],
            "location": ["beginning", "end", "start", "finish", "top", "bottom"],
            "quantity": ["word", "line", "character", "paragraph", "section"],
        }

        for entity_type, keywords in entity_patterns.items():
            for keyword in keywords:
                if keyword.lower() in text.lower():
                    # Create embedding for keyword to verify semantic relevance
                    keyword_embedding = self.model.encode(keyword)

                    # Calculate semantic similarity
                    similarity = cosine_similarity(
                        text_embedding.reshape(1, -1), keyword_embedding.reshape(1, -1)
                    )[0][0]

                    if similarity > 0.3:  # Lower threshold for entity extraction
                        entities.append(
                            {
                                "text": keyword,
                                "type": entity_type,
                                "semantic_similarity": float(similarity),
                                "extraction_method": "semantic_embedding",
                            }
                        )

        return entities

    def _semantic_learning(
        self, text: str, text_embedding: np.ndarray, understanding: Dict[str, Any]
    ):
        """Learn from semantic understanding"""

        concept_matches = understanding["concept_matches"]

        for match in concept_matches[:2]:  # Learn from top 2 matches
            concept_name = match["concept"]
            concept_key = f"deep_semantic:concept:{concept_name}"

            concept_data = self.redis_client.get(concept_key)
            if concept_data:
                concept_info = json.loads(concept_data)

                # Update usage count
                concept_info["usage_count"] += 1

                # Add this text as example if similarity is high enough
                if match["overall_similarity"] > 0.8:
                    if text not in concept_info["examples"]:
                        concept_info["examples"].append(text)
                        concept_info["example_embeddings"].append(
                            text_embedding.tolist()
                        )

                        # Keep only recent examples (limit memory)
                        if len(concept_info["examples"]) > 20:
                            concept_info["examples"] = concept_info["examples"][-20:]
                            concept_info["example_embeddings"] = concept_info[
                                "example_embeddings"
                            ][-20:]

                # Update confidence based on usage
                usage_boost = min(0.05, concept_info["usage_count"] * 0.001)
                concept_info["confidence"] = min(
                    0.99, concept_info["confidence"] + usage_boost
                )

                concept_info["last_updated"] = time.time()

                self.redis_client.set(concept_key, json.dumps(concept_info))

        print(f"📚 Semantic learning: Updated {len(concept_matches)} concepts")

    def find_similar_texts(self, text: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Find semantically similar texts from history"""

        text_embedding = self.model.encode(text)

        # Get all stored embeddings
        stored_texts = self.redis_client.hgetall("deep_semantic:text_embeddings")

        similarities = []

        for text_hash, stored_data in stored_texts.items():
            try:
                stored_understanding = json.loads(stored_data)
                stored_embedding = np.array(stored_understanding["embedding"])

                similarity = cosine_similarity(
                    text_embedding.reshape(1, -1), stored_embedding.reshape(1, -1)
                )[0][0]

                if similarity > 0.5:  # Only include reasonably similar texts
                    similarities.append(
                        {
                            "text": stored_understanding["text"],
                            "similarity": float(similarity),
                            "primary_intent": stored_understanding[
                                "semantic_reasoning"
                            ]["primary_intent"],
                            "confidence": stored_understanding["confidence"],
                            "timestamp": stored_understanding["timestamp"],
                        }
                    )

            except (json.JSONDecodeError, KeyError):
                continue

        # Sort by similarity and return top results
        similarities.sort(key=lambda x: x["similarity"], reverse=True)
        return similarities[:limit]

    def get_semantic_stats(self) -> Dict[str, Any]:
        """Get semantic engine statistics"""

        concept_keys = self.redis_client.keys("deep_semantic:concept:*")
        understanding_count = self.redis_client.xlen("deep_semantic:understandings")
        embedding_count = self.redis_client.hlen("deep_semantic:text_embeddings")

        return {
            "concepts": len(concept_keys),
            "understandings": understanding_count,
            "text_embeddings": embedding_count,
            "model": "sentence-transformers/all-MiniLM-L6-v2",
            "session": self.session_id,
        }


def main():
    """Demonstrate deep semantic understanding"""

    print("🧠 DEEP SEMANTIC ENGINE DEMO")
    print("=" * 50)

    # Initialize engine
    engine = DeepSemanticEngine()

    # Test texts with subtle semantic differences
    test_texts = [
        "move the cursor to the next word",
        "navigate forward in the document",
        "I need to save this file immediately",
        "please backup the current document",
        "show me the git repository status",
        "check the version control state",
        "delete the selected text",
        "remove this paragraph",
        "find the function definition",
        "locate where this method is declared",
    ]

    print(f"\n🎯 Testing deep semantic understanding:")

    for i, text in enumerate(test_texts, 1):
        print(f"\n{i}. '{text}'")
        print("-" * 50)

        context = {
            "current_file": "semantic_engine.py" if i % 2 == 0 else "README.md",
            "cursor_line": 100 + i,
            "project": "redis-ai-challenge",
        }

        understanding = engine.understand_text(text, context)

        print(
            f"   🎯 Primary Intent: {understanding['semantic_reasoning']['primary_intent']}"
        )
        print(f"   📊 Confidence: {understanding['confidence']:.3f}")
        print(
            f"   🧠 Reasoning: {understanding['semantic_reasoning']['reasoning_chain'][0]}"
        )

        if understanding["semantic_reasoning"]["contextual_inferences"]:
            print(
                f"   🔍 Context: {understanding['semantic_reasoning']['contextual_inferences'][0]}"
            )

        if understanding["entities"]:
            entities = [e["text"] for e in understanding["entities"][:3]]
            print(f"   📝 Entities: {entities}")

        time.sleep(0.3)

    # Test semantic similarity
    print(f"\n" + "=" * 50)
    print("🔍 SEMANTIC SIMILARITY TEST")
    print("=" * 50)

    query_text = "help me navigate to the start of the line"
    print(f"Query: '{query_text}'")

    similar_texts = engine.find_similar_texts(query_text)

    print(f"Found {len(similar_texts)} semantically similar texts:")
    for sim in similar_texts:
        print(f"   • '{sim['text']}' (similarity: {sim['similarity']:.3f})")

    # Final stats
    print(f"\n" + "=" * 50)
    print("📊 SEMANTIC ENGINE STATISTICS")
    print("=" * 50)

    stats = engine.get_semantic_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")

    print(f"\n✅ DEEP SEMANTIC UNDERSTANDING DEMONSTRATED")
    print("🧠 Real embeddings, similarity matching, and semantic reasoning!")


if __name__ == "__main__":
    main()
