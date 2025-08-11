#!/usr/bin/env python3
"""
Persistent Memory System - Remembers Everything Across Sessions
This system creates permanent memory that survives restarts and builds deep understanding over time.
"""

import asyncio
import json
import time
import logging
import pickle
import hashlib
import sqlite3
import os
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime, timedelta
from fixed_redis_coordinator import redis_coordinator
from robust_claude_integration import claude_integration

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MemoryType(Enum):
    PATTERN = "pattern"
    WORKFLOW = "workflow"
    USER_PREFERENCE = "user_preference"
    SEMANTIC_MAPPING = "semantic_mapping"
    CAPABILITY = "capability"
    EXPERIENCE = "experience"
    RELATIONSHIP = "relationship"
    CONCEPT = "concept"


@dataclass
class MemoryFragment:
    id: str
    memory_type: MemoryType
    content: str
    context: Dict[str, Any]
    importance: float
    confidence: float
    created_at: float
    last_accessed: float
    access_count: int
    related_fragments: List[str]
    embeddings: Optional[List[float]] = None


@dataclass
class LongTermMemory:
    concept_id: str
    name: str
    description: str
    associated_patterns: List[str]
    strength: float
    created_sessions_ago: int
    reinforcement_events: int


class PersistentMemorySystem:
    """System that maintains persistent memory across all sessions"""

    def __init__(self, memory_db_path: str = "revolutionary_memory.db"):
        self.coordinator = redis_coordinator
        self.running = False
        self.memory_db_path = memory_db_path

        # In-memory caches
        self.active_memories: Dict[str, MemoryFragment] = {}
        self.long_term_concepts: Dict[str, LongTermMemory] = {}
        self.session_memories: List[MemoryFragment] = []

        # Memory management
        self.memory_consolidation_threshold = 100
        self.importance_decay_rate = 0.95
        self.max_active_memories = 1000

        # Session tracking
        self.session_id = f"session_{int(time.time())}"
        self.session_start_time = time.time()
        self.memories_created_this_session = 0
        self.memories_recalled_this_session = 0

        # Initialize database
        self._initialize_memory_database()

        logger.info("🧠 Persistent Memory System initialized")
        logger.info(f"💾 Memory database: {memory_db_path}")
        logger.info(f"🔍 Session: {self.session_id}")

    def _initialize_memory_database(self):
        """Initialize SQLite database for persistent memory"""
        try:
            self.db_connection = sqlite3.connect(
                self.memory_db_path, check_same_thread=False
            )
            cursor = self.db_connection.cursor()

            # Create memory fragments table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS memory_fragments (
                    id TEXT PRIMARY KEY,
                    memory_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    context TEXT NOT NULL,
                    importance REAL NOT NULL,
                    confidence REAL NOT NULL,
                    created_at REAL NOT NULL,
                    last_accessed REAL NOT NULL,
                    access_count INTEGER NOT NULL,
                    related_fragments TEXT,
                    embeddings BLOB
                )
            """
            )

            # Create long term concepts table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS long_term_concepts (
                    concept_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT NOT NULL,
                    associated_patterns TEXT NOT NULL,
                    strength REAL NOT NULL,
                    created_sessions_ago INTEGER NOT NULL,
                    reinforcement_events INTEGER NOT NULL
                )
            """
            )

            # Create session history table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS session_history (
                    session_id TEXT PRIMARY KEY,
                    start_time REAL NOT NULL,
                    end_time REAL,
                    memories_created INTEGER NOT NULL,
                    memories_recalled INTEGER NOT NULL,
                    major_insights TEXT,
                    user_patterns TEXT
                )
            """
            )

            self.db_connection.commit()

            # Load existing memories into cache
            self._load_recent_memories()

            logger.info("💾 Memory database initialized")

        except Exception as e:
            logger.error(f"Memory database initialization error: {e}")

    def _load_recent_memories(self):
        """Load recent memories into active cache"""
        try:
            cursor = self.db_connection.cursor()

            # Load memories from last 7 days
            week_ago = time.time() - (7 * 24 * 3600)
            cursor.execute(
                """
                SELECT * FROM memory_fragments 
                WHERE last_accessed > ? 
                ORDER BY importance DESC, last_accessed DESC
                LIMIT ?
            """,
                (week_ago, self.max_active_memories),
            )

            rows = cursor.fetchall()

            for row in rows:
                memory = MemoryFragment(
                    id=row[0],
                    memory_type=MemoryType(row[1]),
                    content=row[2],
                    context=json.loads(row[3]),
                    importance=row[4],
                    confidence=row[5],
                    created_at=row[6],
                    last_accessed=row[7],
                    access_count=row[8],
                    related_fragments=json.loads(row[9]) if row[9] else [],
                    embeddings=pickle.loads(row[10]) if row[10] else None,
                )

                self.active_memories[memory.id] = memory

            logger.info(f"🧠 Loaded {len(self.active_memories)} recent memories")

        except Exception as e:
            logger.error(f"Memory loading error: {e}")

    async def start_persistent_memory(self):
        """Start persistent memory operations"""
        self.running = True

        logger.info("🚀 Starting Persistent Memory System")
        logger.info("🧠 Building continuous memory across sessions")

        # Start memory tasks
        memory_tasks = [
            asyncio.create_task(self._monitor_new_experiences()),
            asyncio.create_task(self._consolidate_memories()),
            asyncio.create_task(self._update_memory_strengths()),
            asyncio.create_task(self._discover_long_term_patterns()),
            asyncio.create_task(self._maintain_memory_database()),
        ]

        try:
            await asyncio.gather(*memory_tasks)
        except Exception as e:
            logger.error(f"Persistent memory error: {e}")

    async def _monitor_new_experiences(self):
        """Monitor for new experiences to remember"""
        while self.running:
            try:
                # Monitor Redis streams for experiences to remember
                await self._capture_keystroke_patterns()
                await self._capture_ai_interactions()
                await self._capture_user_preferences()

                await asyncio.sleep(10)

            except Exception as e:
                logger.error(f"Experience monitoring error: {e}")
                await asyncio.sleep(10)

    async def _capture_keystroke_patterns(self):
        """Capture meaningful keystroke patterns for memory"""
        try:
            keystrokes = self.coordinator.get_recent_keystrokes(count=20)

            if len(keystrokes) >= 10:
                # Look for repeated patterns
                pattern_signature = self._extract_pattern_signature(keystrokes)

                if pattern_signature:
                    memory_id = self._create_memory(
                        memory_type=MemoryType.PATTERN,
                        content=f"Keystroke pattern: {pattern_signature}",
                        context={
                            "pattern_type": "keystroke_sequence",
                            "frequency": 1,
                            "keystrokes": [ks.get("key", "") for ks in keystrokes[-5:]],
                        },
                        importance=0.3,
                    )

                    logger.debug(f"🧠 Captured keystroke pattern: {memory_id}")

        except Exception as e:
            logger.error(f"Keystroke pattern capture error: {e}")

    def _extract_pattern_signature(
        self, keystrokes: List[Dict[str, Any]]
    ) -> Optional[str]:
        """Extract a signature from keystroke patterns"""
        try:
            keys = [ks.get("key", "") for ks in keystrokes[-10:]]
            commands = [ks.get("command", "") for ks in keystrokes[-10:]]

            # Look for repeated sequences
            key_string = "".join(keys)
            command_string = "→".join(commands)

            # Simple pattern detection
            if len(set(keys)) < len(keys) * 0.7:  # Some repetition
                return f"keys:{key_string[:20]}"

            if "self-insert-command" in commands and len(set(commands)) > 2:
                return f"editing:{command_string[:50]}"

            return None

        except Exception:
            return None

    async def _capture_ai_interactions(self):
        """Capture meaningful AI interactions"""
        try:
            responses = self.coordinator.get_recent_responses(count=10)

            for response in responses:
                response_type = response.get("type", "")

                if response_type in ["completion_suggestion", "command_response"]:
                    # Remember successful AI interactions
                    memory_id = self._create_memory(
                        memory_type=MemoryType.EXPERIENCE,
                        content=f"AI interaction: {response_type}",
                        context={
                            "response_type": response_type,
                            "success": True,
                            "content": response.get(
                                "suggestion", response.get("response", "")
                            )[:100],
                        },
                        importance=0.4,
                    )

                    logger.debug(f"🤖 Captured AI interaction: {memory_id}")

        except Exception as e:
            logger.error(f"AI interaction capture error: {e}")

    async def _capture_user_preferences(self):
        """Capture and remember user preferences"""
        try:
            # Infer preferences from usage patterns
            keystrokes = self.coordinator.get_recent_keystrokes(count=50)

            if keystrokes:
                # Analyze buffer preferences
                buffer_usage = {}
                for ks in keystrokes:
                    buffer_name = ks.get("buffer", "unknown")
                    buffer_usage[buffer_name] = buffer_usage.get(buffer_name, 0) + 1

                # Find most used buffer
                if buffer_usage:
                    preferred_buffer = max(buffer_usage, key=buffer_usage.get)

                    if (
                        preferred_buffer != "unknown"
                        and buffer_usage[preferred_buffer] > 10
                    ):
                        memory_id = self._create_memory(
                            memory_type=MemoryType.USER_PREFERENCE,
                            content=f"Preferred buffer: {preferred_buffer}",
                            context={
                                "preference_type": "buffer_usage",
                                "buffer_name": preferred_buffer,
                                "usage_count": buffer_usage[preferred_buffer],
                            },
                            importance=0.6,
                        )

        except Exception as e:
            logger.error(f"User preference capture error: {e}")

    def _create_memory(
        self,
        memory_type: MemoryType,
        content: str,
        context: Dict[str, Any],
        importance: float,
    ) -> str:
        """Create a new memory fragment"""
        try:
            memory_id = (
                f"{memory_type.value}_{int(time.time())}_{len(self.active_memories)}"
            )

            memory = MemoryFragment(
                id=memory_id,
                memory_type=memory_type,
                content=content,
                context=context,
                importance=importance,
                confidence=0.8,
                created_at=time.time(),
                last_accessed=time.time(),
                access_count=1,
                related_fragments=[],
            )

            # Add to active memory
            self.active_memories[memory_id] = memory
            self.session_memories.append(memory)
            self.memories_created_this_session += 1

            # Store in database
            self._persist_memory(memory)

            return memory_id

        except Exception as e:
            logger.error(f"Memory creation error: {e}")
            return ""

    def _persist_memory(self, memory: MemoryFragment):
        """Persist memory to database"""
        try:
            cursor = self.db_connection.cursor()

            cursor.execute(
                """
                INSERT OR REPLACE INTO memory_fragments 
                (id, memory_type, content, context, importance, confidence, 
                 created_at, last_accessed, access_count, related_fragments, embeddings)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    memory.id,
                    memory.memory_type.value,
                    memory.content,
                    json.dumps(memory.context),
                    memory.importance,
                    memory.confidence,
                    memory.created_at,
                    memory.last_accessed,
                    memory.access_count,
                    json.dumps(memory.related_fragments),
                    pickle.dumps(memory.embeddings) if memory.embeddings else None,
                ),
            )

            self.db_connection.commit()

        except Exception as e:
            logger.error(f"Memory persistence error: {e}")

    async def _consolidate_memories(self):
        """Consolidate memories for long-term storage"""
        while self.running:
            try:
                if len(self.session_memories) >= self.memory_consolidation_threshold:
                    await self._perform_memory_consolidation()

                await asyncio.sleep(300)  # Consolidate every 5 minutes

            except Exception as e:
                logger.error(f"Memory consolidation error: {e}")
                await asyncio.sleep(300)

    async def _perform_memory_consolidation(self):
        """Perform actual memory consolidation"""
        try:
            logger.info("🧠 Performing memory consolidation")

            # Group related memories
            memory_clusters = self._cluster_related_memories()

            # Create long-term concepts from clusters
            for cluster in memory_clusters:
                if len(cluster) >= 3:  # Significant cluster
                    await self._create_long_term_concept(cluster)

            # Clear session memories
            self.session_memories = []

            logger.info(f"✅ Memory consolidation complete")

        except Exception as e:
            logger.error(f"Memory consolidation error: {e}")

    def _cluster_related_memories(self) -> List[List[MemoryFragment]]:
        """Cluster related memories together"""
        clusters = []
        used_memories = set()

        for memory in self.session_memories:
            if memory.id in used_memories:
                continue

            # Find related memories
            cluster = [memory]
            used_memories.add(memory.id)

            for other_memory in self.session_memories:
                if other_memory.id not in used_memories and self._are_memories_related(
                    memory, other_memory
                ):
                    cluster.append(other_memory)
                    used_memories.add(other_memory.id)

            clusters.append(cluster)

        return clusters

    def _are_memories_related(
        self, memory1: MemoryFragment, memory2: MemoryFragment
    ) -> bool:
        """Determine if two memories are related"""
        # Same type
        if memory1.memory_type == memory2.memory_type:
            return True

        # Similar context
        context1_keys = set(memory1.context.keys())
        context2_keys = set(memory2.context.keys())

        if len(context1_keys.intersection(context2_keys)) > 0:
            return True

        # Similar content (simple string matching)
        if memory1.content and memory2.content:
            words1 = set(memory1.content.lower().split())
            words2 = set(memory2.content.lower().split())

            if len(words1.intersection(words2)) > 0:
                return True

        return False

    async def _create_long_term_concept(self, memory_cluster: List[MemoryFragment]):
        """Create long-term concept from memory cluster"""
        try:
            # Generate concept from cluster
            concept_id = f"concept_{int(time.time())}_{len(self.long_term_concepts)}"

            # Extract common themes
            all_content = " ".join([m.content for m in memory_cluster])
            all_context_keys = set()
            for m in memory_cluster:
                all_context_keys.update(m.context.keys())

            # Simple concept naming
            if "keystroke" in all_content:
                concept_name = "Keystroke Pattern"
            elif "completion" in all_content:
                concept_name = "AI Completion Pattern"
            elif "buffer" in all_content:
                concept_name = "Buffer Usage Pattern"
            else:
                concept_name = "General Usage Pattern"

            concept = LongTermMemory(
                concept_id=concept_id,
                name=concept_name,
                description=f"Concept derived from {len(memory_cluster)} related memories",
                associated_patterns=[m.id for m in memory_cluster],
                strength=sum(m.importance for m in memory_cluster)
                / len(memory_cluster),
                created_sessions_ago=0,
                reinforcement_events=1,
            )

            self.long_term_concepts[concept_id] = concept

            # Persist to database
            cursor = self.db_connection.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO long_term_concepts
                (concept_id, name, description, associated_patterns, strength, 
                 created_sessions_ago, reinforcement_events)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    concept.concept_id,
                    concept.name,
                    concept.description,
                    json.dumps(concept.associated_patterns),
                    concept.strength,
                    concept.created_sessions_ago,
                    concept.reinforcement_events,
                ),
            )

            self.db_connection.commit()

            logger.info(f"🧠 Created long-term concept: {concept_name}")

        except Exception as e:
            logger.error(f"Long-term concept creation error: {e}")

    async def _update_memory_strengths(self):
        """Update memory strengths based on usage"""
        while self.running:
            try:
                # Decay unused memories
                current_time = time.time()

                for memory in list(self.active_memories.values()):
                    days_since_access = (current_time - memory.last_accessed) / (
                        24 * 3600
                    )

                    if days_since_access > 1:
                        memory.importance *= self.importance_decay_rate

                        # Remove very weak memories from active cache
                        if memory.importance < 0.1:
                            del self.active_memories[memory.id]

                await asyncio.sleep(3600)  # Update hourly

            except Exception as e:
                logger.error(f"Memory strength update error: {e}")
                await asyncio.sleep(3600)

    async def _discover_long_term_patterns(self):
        """Discover patterns in long-term memory"""
        while self.running:
            try:
                if len(self.long_term_concepts) > 0:
                    # Analyze concepts for meta-patterns
                    await self._analyze_concept_relationships()

                await asyncio.sleep(1800)  # Analyze every 30 minutes

            except Exception as e:
                logger.error(f"Long-term pattern discovery error: {e}")
                await asyncio.sleep(1800)

    async def _analyze_concept_relationships(self):
        """Analyze relationships between long-term concepts"""
        try:
            # Simple relationship analysis
            for concept1 in self.long_term_concepts.values():
                for concept2 in self.long_term_concepts.values():
                    if concept1.concept_id != concept2.concept_id:
                        # Check for related patterns
                        shared_patterns = set(
                            concept1.associated_patterns
                        ).intersection(set(concept2.associated_patterns))

                        if shared_patterns:
                            logger.info(
                                f"🔗 Found relationship: {concept1.name} ↔ {concept2.name}"
                            )

        except Exception as e:
            logger.error(f"Concept relationship analysis error: {e}")

    async def _maintain_memory_database(self):
        """Maintain and optimize memory database"""
        while self.running:
            try:
                # Clean old, unimportant memories
                self._cleanup_old_memories()

                # Update session history
                self._update_session_history()

                await asyncio.sleep(7200)  # Maintain every 2 hours

            except Exception as e:
                logger.error(f"Memory database maintenance error: {e}")
                await asyncio.sleep(7200)

    def _cleanup_old_memories(self):
        """Clean up old, unimportant memories"""
        try:
            cursor = self.db_connection.cursor()

            # Remove memories older than 30 days with low importance
            thirty_days_ago = time.time() - (30 * 24 * 3600)

            cursor.execute(
                """
                DELETE FROM memory_fragments 
                WHERE created_at < ? AND importance < 0.2
            """,
                (thirty_days_ago,),
            )

            deleted_count = cursor.rowcount

            if deleted_count > 0:
                logger.info(f"🧹 Cleaned up {deleted_count} old memories")
                self.db_connection.commit()

        except Exception as e:
            logger.error(f"Memory cleanup error: {e}")

    def _update_session_history(self):
        """Update current session history"""
        try:
            cursor = self.db_connection.cursor()

            cursor.execute(
                """
                INSERT OR REPLACE INTO session_history
                (session_id, start_time, end_time, memories_created, memories_recalled, major_insights, user_patterns)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    self.session_id,
                    self.session_start_time,
                    None,  # End time not set until session ends
                    self.memories_created_this_session,
                    self.memories_recalled_this_session,
                    json.dumps(
                        [concept.name for concept in self.long_term_concepts.values()]
                    ),
                    json.dumps([]),  # User patterns would be analyzed here
                ),
            )

            self.db_connection.commit()

        except Exception as e:
            logger.error(f"Session history update error: {e}")

    def recall_memories(
        self, query: str, memory_type: Optional[MemoryType] = None
    ) -> List[MemoryFragment]:
        """Recall memories based on query"""
        try:
            relevant_memories = []

            query_words = set(query.lower().split())

            for memory in self.active_memories.values():
                if memory_type and memory.memory_type != memory_type:
                    continue

                # Simple content matching
                memory_words = set(memory.content.lower().split())

                if query_words.intersection(memory_words):
                    memory.last_accessed = time.time()
                    memory.access_count += 1
                    relevant_memories.append(memory)
                    self.memories_recalled_this_session += 1

            # Sort by importance and recency
            relevant_memories.sort(
                key=lambda m: (m.importance, m.last_accessed), reverse=True
            )

            return relevant_memories[:10]  # Return top 10

        except Exception as e:
            logger.error(f"Memory recall error: {e}")
            return []

    def get_memory_stats(self) -> Dict[str, Any]:
        """Get persistent memory system statistics"""
        return {
            "running": self.running,
            "session_id": self.session_id,
            "session_uptime": time.time() - self.session_start_time,
            "active_memories": len(self.active_memories),
            "long_term_concepts": len(self.long_term_concepts),
            "memories_created_this_session": self.memories_created_this_session,
            "memories_recalled_this_session": self.memories_recalled_this_session,
            "memory_types": {
                memory_type.value: sum(
                    1
                    for m in self.active_memories.values()
                    if m.memory_type == memory_type
                )
                for memory_type in MemoryType
            },
            "database_path": self.memory_db_path,
        }

    def stop(self):
        """Stop persistent memory system"""
        self.running = False

        # Update final session history
        self._update_session_history()

        # Close database
        if hasattr(self, "db_connection"):
            self.db_connection.close()

        logger.info("🛑 Persistent Memory System stopped")

        stats = self.get_memory_stats()
        logger.info(
            f"🧠 Memory stats: {stats['memories_created_this_session']} memories created, {stats['long_term_concepts']} concepts formed"
        )


# Global persistent memory system
persistent_memory_system = PersistentMemorySystem()


async def main():
    """Demo the Persistent Memory System"""
    print("🧠 PERSISTENT MEMORY SYSTEM")
    print("=" * 60)
    print("Building permanent memory across all sessions")
    print("=" * 60)

    # Start persistent memory
    memory_task = asyncio.create_task(
        persistent_memory_system.start_persistent_memory()
    )

    print("✅ Persistent memory started")
    print("💾 SQLite database storing all memories")
    print("🧠 Memories survive system restarts")
    print("🔗 Long-term concepts formed from memory clusters")
    print("📈 Memory strength updated based on usage")
    print("🛑 Press Ctrl+C to stop")

    try:
        while True:
            await asyncio.sleep(60)

            # Show memory stats
            stats = persistent_memory_system.get_memory_stats()
            print(
                f"🧠 Memory: {stats['active_memories']} active, "
                f"{stats['long_term_concepts']} concepts, "
                f"{stats['memories_created_this_session']} created this session"
            )

            # Test memory recall
            if stats["active_memories"] > 0:
                memories = persistent_memory_system.recall_memories("keystroke pattern")
                if memories:
                    print(
                        f"🔍 Recalled {len(memories)} memories about keystroke patterns"
                    )

    except KeyboardInterrupt:
        print("\n🛑 Stopping Persistent Memory System...")
        persistent_memory_system.stop()
        await memory_task
        print("✅ Persistent Memory System stopped")


if __name__ == "__main__":
    asyncio.run(main())
