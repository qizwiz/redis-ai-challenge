#!/usr/bin/env python3
"""
Context Pruning Engine for Subagent Memory Management
Intelligent context management to prevent memory bloat while preserving critical information
"""

import redis
import json
import time
import hashlib
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, asdict
from collections import defaultdict
import re


@dataclass
class ContextEntry:
    content: str
    timestamp: float
    importance_score: float
    access_count: int
    last_accessed: float
    context_type: str  # 'code', 'conversation', 'error', 'breakthrough', 'workflow'
    dependencies: Set[str]  # Hash IDs of related entries


class ContextPruningEngine:
    def __init__(self, max_context_size: int = 50000, retention_days: int = 7):
        self.redis_client = redis.Redis(decode_responses=True)
        self.max_context_size = max_context_size
        self.retention_days = retention_days
        self.importance_weights = {
            "breakthrough": 0.9,  # Revolutionary discoveries - keep longest
            "error": 0.8,  # Error patterns - important for learning
            "workflow": 0.7,  # Successful workflows - reusable patterns
            "conversation": 0.5,  # General conversation - moderate importance
            "code": 0.6,  # Code snippets - useful but replaceable
        }

    def add_context(
        self,
        content: str,
        context_type: str = "conversation",
        dependencies: Optional[Set[str]] = None,
    ) -> str:
        """Add new context entry with automatic importance scoring"""

        entry_id = hashlib.md5(f"{content}{time.time()}".encode()).hexdigest()[:12]

        importance_score = self._calculate_importance(content, context_type)

        entry = ContextEntry(
            content=content,
            timestamp=time.time(),
            importance_score=importance_score,
            access_count=1,
            last_accessed=time.time(),
            context_type=context_type,
            dependencies=dependencies or set(),
        )

        # Store in Redis with expiration based on importance
        ttl = int(self.retention_days * 24 * 3600 * importance_score)

        self.redis_client.hset(
            f"context:{entry_id}",
            mapping={
                "content": entry.content,
                "timestamp": str(entry.timestamp),
                "importance_score": str(entry.importance_score),
                "access_count": str(entry.access_count),
                "last_accessed": str(entry.last_accessed),
                "context_type": entry.context_type,
                "dependencies": json.dumps(list(entry.dependencies)),
            },
        )

        self.redis_client.expire(f"context:{entry_id}", ttl)

        # Add to type-specific indexes
        self.redis_client.sadd(f"context:type:{context_type}", entry_id)
        self.redis_client.zadd("context:importance", {entry_id: importance_score})
        self.redis_client.zadd("context:recency", {entry_id: entry.timestamp})

        return entry_id

    def _calculate_importance(self, content: str, context_type: str) -> float:
        """Calculate importance score based on content analysis"""

        base_score = self.importance_weights.get(context_type, 0.5)

        # Boost score for certain keywords
        importance_keywords = {
            "breakthrough": 0.15,
            "revolutionary": 0.12,
            "working": 0.08,
            "success": 0.08,
            "error": 0.10,
            "failed": 0.10,
            "learning": 0.05,
            "pattern": 0.05,
            "redis": 0.03,
            "emacs": 0.03,
        }

        content_lower = content.lower()
        keyword_boost = sum(
            boost
            for keyword, boost in importance_keywords.items()
            if keyword in content_lower
        )

        # Length penalty for very short content (likely less important)
        length_factor = min(1.0, len(content) / 100)

        # Recency boost for very recent content
        recency_boost = 0.1 if time.time() - time.time() < 3600 else 0

        final_score = (
            min(1.0, base_score + keyword_boost + recency_boost) * length_factor
        )
        return final_score

    def access_context(self, entry_id: str) -> Optional[ContextEntry]:
        """Access context entry and update access statistics"""

        entry_data = self.redis_client.hgetall(f"context:{entry_id}")
        if not entry_data:
            return None

        # Update access statistics
        access_count = int(entry_data.get("access_count", 0)) + 1
        current_time = time.time()

        self.redis_client.hset(
            f"context:{entry_id}",
            mapping={
                "access_count": str(access_count),
                "last_accessed": str(current_time),
            },
        )

        # Update recency index
        self.redis_client.zadd("context:recency", {entry_id: current_time})

        # Reconstruct ContextEntry
        return ContextEntry(
            content=entry_data["content"],
            timestamp=float(entry_data["timestamp"]),
            importance_score=float(entry_data["importance_score"]),
            access_count=access_count,
            last_accessed=current_time,
            context_type=entry_data["context_type"],
            dependencies=set(json.loads(entry_data.get("dependencies", "[]"))),
        )

    def prune_context(self, target_size: Optional[int] = None) -> Dict[str, int]:
        """Intelligent context pruning to manage memory"""

        target_size = target_size or self.max_context_size
        current_size = self._calculate_total_context_size()

        if current_size <= target_size:
            return {"pruned": 0, "kept": len(self.redis_client.keys("context:*"))}

        # Get all context entries sorted by pruning priority
        pruning_candidates = self._get_pruning_candidates()

        pruned_count = 0
        current_reduction = 0

        for entry_id, pruning_score in pruning_candidates:
            if current_size - current_reduction <= target_size:
                break

            entry_data = self.redis_client.hgetall(f"context:{entry_id}")
            if entry_data:
                entry_size = len(entry_data.get("content", ""))

                # Check if entry has dependents (don't prune if other entries depend on it)
                if not self._has_dependents(entry_id):
                    self._remove_context_entry(entry_id)
                    current_reduction += entry_size
                    pruned_count += 1

        return {
            "pruned": pruned_count,
            "kept": len(self.redis_client.keys("context:*"))
            // 2,  # Approximate (keys include indexes)
            "size_reduction": current_reduction,
            "final_size": current_size - current_reduction,
        }

    def _get_pruning_candidates(self) -> List[Tuple[str, float]]:
        """Get entries sorted by pruning priority (lower score = prune first)"""

        candidates = []

        for key in self.redis_client.keys("context:*"):
            if (
                key.startswith("context:") and not ":" in key[8:]
            ):  # Actual context entries
                entry_id = key.split(":")[1]
                entry_data = self.redis_client.hgetall(key)

                if entry_data:
                    # Calculate pruning score (lower = more likely to prune)
                    importance = float(entry_data.get("importance_score", 0.5))
                    access_count = int(entry_data.get("access_count", 1))
                    last_accessed = float(entry_data.get("last_accessed", 0))
                    age = time.time() - float(entry_data.get("timestamp", time.time()))

                    # Recency factor (recent access protects from pruning)
                    recency_factor = max(
                        0.1, 1.0 - (time.time() - last_accessed) / (7 * 24 * 3600)
                    )

                    # Access frequency factor
                    frequency_factor = min(2.0, 1.0 + access_count * 0.1)

                    # Age penalty (older entries more likely to prune)
                    age_penalty = min(0.5, age / (30 * 24 * 3600))

                    pruning_score = (
                        importance * recency_factor * frequency_factor - age_penalty
                    )
                    candidates.append((entry_id, pruning_score))

        # Sort by pruning score (ascending - lowest scores pruned first)
        return sorted(candidates, key=lambda x: x[1])

    def get_context_summary(self) -> Dict[str, any]:
        """Get comprehensive context management statistics"""

        total_entries = len(
            [
                k
                for k in self.redis_client.keys("context:*")
                if k.startswith("context:") and not ":" in k[8:]
            ]
        )
        total_size = self._calculate_total_context_size()

        # Get type distribution
        type_distribution = {}
        for context_type in [
            "breakthrough",
            "error",
            "workflow",
            "conversation",
            "code",
        ]:
            count = self.redis_client.scard(f"context:type:{context_type}")
            if count > 0:
                type_distribution[context_type] = count

        # Get importance distribution
        high_importance = len(
            self.redis_client.zrangebyscore("context:importance", 0.8, 1.0)
        )
        medium_importance = len(
            self.redis_client.zrangebyscore("context:importance", 0.5, 0.8)
        )
        low_importance = len(
            self.redis_client.zrangebyscore("context:importance", 0.0, 0.5)
        )

        return {
            "total_entries": total_entries,
            "total_size_chars": total_size,
            "size_utilization": f"{(total_size / self.max_context_size) * 100:.1f}%",
            "type_distribution": type_distribution,
            "importance_distribution": {
                "high": high_importance,
                "medium": medium_importance,
                "low": low_importance,
            },
            "retention_policy": f"{self.retention_days} days base retention",
            "max_context_size": self.max_context_size,
        }


def main():
    """Test context pruning engine"""

    engine = ContextPruningEngine(max_context_size=1000)  # Small size for testing

    print("🧠 Context Pruning Engine Test")
    print("=" * 40)

    # Add various types of content
    test_contexts = [
        ("This is a breakthrough discovery about Redis coordination!", "breakthrough"),
        ("Error: Connection failed to Redis server", "error"),
        ("Successful workflow: git commit → push → deploy", "workflow"),
        ("User asked about Python syntax", "conversation"),
        ("def hello_world(): print('Hello')", "code"),
        ("Another conversation about weather", "conversation"),
        ("Critical error in production system", "error"),
        ("Revolutionary AI self-testing capability proven", "breakthrough"),
    ]

    entry_ids = []
    for content, context_type in test_contexts:
        entry_id = engine.add_context(content, context_type)
        entry_ids.append(entry_id)
        print(f"✅ Added {context_type}: {entry_id}")

    # Show initial summary
    print("\n📊 Initial Context Summary:")
    summary = engine.get_context_summary()
    for key, value in summary.items():
        print(f"   {key}: {value}")

    # Access some entries to boost their retention
    print("\n🔍 Accessing some entries...")
    for i in range(3):
        entry = engine.access_context(entry_ids[i])
        if entry:
            print(
                f"   Accessed: {entry.context_type} (access count: {entry.access_count})"
            )

    # Force pruning
    print("\n✂️  Pruning context...")
    prune_results = engine.prune_context(target_size=500)
    print(f"   Pruned: {prune_results['pruned']} entries")
    print(f"   Kept: {prune_results['kept']} entries")
    print(f"   Size reduction: {prune_results.get('size_reduction', 0)} chars")

    # Show final summary
    print("\n📊 Final Context Summary:")
    final_summary = engine.get_context_summary()
    for key, value in final_summary.items():
        print(f"   {key}: {value}")


if __name__ == "__main__":
    main()
