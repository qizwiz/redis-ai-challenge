#!/usr/bin/env python3
"""
Context Manager Agent with Memory Persistence
Manages context across sessions, preserves relevant information, and provides contextual assistance
"""

import redis
import json
import time
import hashlib
from typing import Dict, List, Optional, Tuple, Set, Any
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import re
import os
from pathlib import Path
import fastmcp


@dataclass
class ContextEntry:
    entry_id: str
    content: str
    context_type: str  # 'conversation', 'code', 'error', 'breakthrough', 'workflow'
    importance: float  # 0.0 to 1.0
    timestamp: float
    session_id: str
    access_count: int
    last_accessed: float
    tags: Set[str]
    related_entries: Set[str]  # IDs of related context entries


@dataclass
class ContextSummary:
    session_id: str
    total_entries: int
    important_entries: int
    context_types: Dict[str, int]
    time_span: Tuple[float, float]  # start, end timestamps
    key_topics: List[str]


class ContextAnalyzer:
    def __init__(self):
        self.importance_keywords = {
            "breakthrough": 0.9,
            "critical": 0.9,
            "error": 0.8,
            "important": 0.7,
            "success": 0.7,
            "working": 0.6,
            "failed": 0.6,
            "redis": 0.4,
            "mcp": 0.4,
            "emacs": 0.3,
            "code": 0.3,
        }

    def analyze_content(
        self, content: str, context_type: str
    ) -> Tuple[float, Set[str]]:
        """Analyze content to determine importance and extract tags"""
        content_lower = content.lower()

        # Base importance by type
        type_importance = {
            "breakthrough": 0.8,
            "error": 0.7,
            "code": 0.5,
            "conversation": 0.4,
            "workflow": 0.6,
        }

        base_importance = type_importance.get(context_type, 0.4)

        # Keyword-based importance boost
        keyword_boost = 0.0
        found_keywords = set()

        for keyword, boost in self.importance_keywords.items():
            if keyword in content_lower:
                keyword_boost += boost * 0.1  # Scale down the boost
                found_keywords.add(keyword)

        # Length factor (longer content often more important)
        length_factor = min(0.2, len(content) / 1000)

        # Code pattern detection
        code_patterns = [
            "def ",
            "class ",
            "import ",
            "#!/usr/bin",
            "function",
            "const ",
            "let ",
        ]
        if any(pattern in content for pattern in code_patterns):
            found_keywords.add("code")

        # Final importance score
        importance = min(1.0, base_importance + keyword_boost + length_factor)

        # Extract additional tags
        tags = found_keywords.copy()

        # Technology tags
        tech_tags = {
            "python": ["def ", "import ", "class ", "python"],
            "elisp": ["defun", "setq", "progn", "elisp"],
            "redis": ["redis", "xadd", "xrange", "stream"],
            "mcp": ["mcp", "fastmcp", "tool", "server"],
            "emacs": ["emacs", "buffer", "point", "window"],
        }

        for tag, patterns in tech_tags.items():
            if any(pattern in content_lower for pattern in patterns):
                tags.add(tag)

        return importance, tags

    def find_related_content(
        self, content: str, tags: Set[str], existing_entries: List[ContextEntry]
    ) -> Set[str]:
        """Find related context entries based on content similarity and tags"""
        related = set()
        content_words = set(content.lower().split())

        for entry in existing_entries:
            # Tag overlap
            tag_overlap = len(tags & entry.tags) / max(len(tags | entry.tags), 1)

            # Content similarity (simple word overlap)
            entry_words = set(entry.content.lower().split())
            word_overlap = len(content_words & entry_words) / max(
                len(content_words | entry_words), 1
            )

            # Time proximity (recent entries more likely related)
            time_diff = abs(time.time() - entry.timestamp)
            time_factor = max(0, 1 - time_diff / (24 * 3600))  # Decay over 24 hours

            # Combined similarity score
            similarity = tag_overlap * 0.4 + word_overlap * 0.4 + time_factor * 0.2

            if similarity > 0.3:  # Threshold for relatedness
                related.add(entry.entry_id)

        return related


class ContextManagerAgent:
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis_client = redis_client or redis.Redis(decode_responses=True)
        self.analyzer = ContextAnalyzer()
        self.session_id = hashlib.md5(f"{time.time()}".encode()).hexdigest()[:12]
        self.context_cache = {}  # In-memory cache for recent entries
        self.max_cache_size = 100

    def add_context(
        self,
        content: str,
        context_type: str = "conversation",
        manual_importance: Optional[float] = None,
    ) -> str:
        """Add new context entry with automatic analysis"""

        # Generate unique ID
        entry_id = hashlib.md5(f"{content}{time.time()}".encode()).hexdigest()[:12]

        # Analyze content
        importance, tags = self.analyzer.analyze_content(content, context_type)
        if manual_importance is not None:
            importance = manual_importance

        # Get existing entries for relationship analysis
        existing_entries = self._get_recent_entries(limit=50)
        related_entries = self.analyzer.find_related_content(
            content, tags, existing_entries
        )

        # Create context entry
        entry = ContextEntry(
            entry_id=entry_id,
            content=content,
            context_type=context_type,
            importance=importance,
            timestamp=time.time(),
            session_id=self.session_id,
            access_count=1,
            last_accessed=time.time(),
            tags=tags,
            related_entries=related_entries,
        )

        # Store in Redis
        self._store_entry(entry)

        # Update cache
        self.context_cache[entry_id] = entry
        self._manage_cache_size()

        return entry_id

    def _store_entry(self, entry: ContextEntry):
        """Store context entry in Redis"""
        entry_data = {
            "content": entry.content,
            "context_type": entry.context_type,
            "importance": str(entry.importance),
            "timestamp": str(entry.timestamp),
            "session_id": entry.session_id,
            "access_count": str(entry.access_count),
            "last_accessed": str(entry.last_accessed),
            "tags": json.dumps(list(entry.tags)),
            "related_entries": json.dumps(list(entry.related_entries)),
        }

        # Store main entry
        self.redis_client.hset(f"context:entry:{entry.entry_id}", mapping=entry_data)

        # Add to indexes
        self.redis_client.zadd(
            "context:by_importance", {entry.entry_id: entry.importance}
        )
        self.redis_client.zadd("context:by_time", {entry.entry_id: entry.timestamp})
        self.redis_client.sadd(f"context:by_type:{entry.context_type}", entry.entry_id)

        for tag in entry.tags:
            self.redis_client.sadd(f"context:by_tag:{tag}", entry.entry_id)

        # Set expiration based on importance (important entries last longer)
        ttl = int(30 * 24 * 3600 * entry.importance)  # 1-30 days based on importance
        self.redis_client.expire(f"context:entry:{entry.entry_id}", ttl)

    def get_context(self, entry_id: str) -> Optional[ContextEntry]:
        """Retrieve context entry and update access statistics"""

        # Check cache first
        if entry_id in self.context_cache:
            entry = self.context_cache[entry_id]
            entry.access_count += 1
            entry.last_accessed = time.time()
            self._store_entry(entry)  # Update Redis
            return entry

        # Get from Redis
        entry_data = self.redis_client.hgetall(f"context:entry:{entry_id}")
        if not entry_data:
            return None

        # Reconstruct entry
        entry = ContextEntry(
            entry_id=entry_id,
            content=entry_data["content"],
            context_type=entry_data["context_type"],
            importance=float(entry_data["importance"]),
            timestamp=float(entry_data["timestamp"]),
            session_id=entry_data["session_id"],
            access_count=int(entry_data["access_count"]) + 1,
            last_accessed=time.time(),
            tags=set(json.loads(entry_data["tags"])),
            related_entries=set(json.loads(entry_data["related_entries"])),
        )

        # Update access stats
        self._store_entry(entry)
        self.context_cache[entry_id] = entry
        self._manage_cache_size()

        return entry

    def get_relevant_context(self, query: str, limit: int = 10) -> List[ContextEntry]:
        """Get context entries relevant to a query"""
        query_lower = query.lower()
        query_words = set(query_lower.split())

        # Get candidates from different sources
        candidates = set()

        # Get by importance
        important_ids = self.redis_client.zrevrange(
            "context:by_importance", 0, limit * 2
        )
        candidates.update(important_ids)

        # Get by tags (if query contains tag-like words)
        for word in query_words:
            if word in self.analyzer.importance_keywords:
                tag_ids = self.redis_client.smembers(f"context:by_tag:{word}")
                candidates.update(tag_ids)

        # Score and rank candidates
        scored_entries = []

        for entry_id in candidates:
            entry = self.get_context(entry_id)
            if not entry:
                continue

            # Calculate relevance score
            content_words = set(entry.content.lower().split())
            word_overlap = len(query_words & content_words) / max(len(query_words), 1)

            tag_match = len(query_words & entry.tags) / max(len(query_words), 1)

            # Combine scores
            relevance = (
                word_overlap * 0.4
                + tag_match * 0.3
                + entry.importance * 0.2
                + min(1.0, entry.access_count / 10) * 0.1
            )

            scored_entries.append((relevance, entry))

        # Sort by relevance and return top entries
        scored_entries.sort(key=lambda x: x[0], reverse=True)
        return [entry for _, entry in scored_entries[:limit]]

    def get_session_summary(self) -> ContextSummary:
        """Get summary of current session context"""
        # Get all entries for this session
        all_ids = self.redis_client.zrange("context:by_time", 0, -1)
        session_entries = []
        context_types = defaultdict(int)

        for entry_id in all_ids:
            entry = self.get_context(entry_id)
            if entry and entry.session_id == self.session_id:
                session_entries.append(entry)
                context_types[entry.context_type] += 1

        if not session_entries:
            return ContextSummary(
                session_id=self.session_id,
                total_entries=0,
                important_entries=0,
                context_types={},
                time_span=(0, 0),
                key_topics=[],
            )

        # Calculate metrics
        important_count = sum(1 for e in session_entries if e.importance > 0.7)
        timestamps = [e.timestamp for e in session_entries]
        time_span = (min(timestamps), max(timestamps))

        # Extract key topics from tags
        all_tags = set()
        for entry in session_entries:
            all_tags.update(entry.tags)

        # Sort tags by frequency across entries
        tag_counts = defaultdict(int)
        for entry in session_entries:
            for tag in entry.tags:
                tag_counts[tag] += 1

        key_topics = sorted(tag_counts.keys(), key=tag_counts.get, reverse=True)[:10]

        return ContextSummary(
            session_id=self.session_id,
            total_entries=len(session_entries),
            important_entries=important_count,
            context_types=dict(context_types),
            time_span=time_span,
            key_topics=key_topics,
        )

    def cleanup_old_context(self, max_age_days: int = 30) -> int:
        """Clean up old, unimportant context entries"""
        cutoff_time = time.time() - (max_age_days * 24 * 3600)

        # Get old entries
        old_ids = self.redis_client.zrangebyscore("context:by_time", 0, cutoff_time)

        removed_count = 0
        for entry_id in old_ids:
            entry = self.get_context(entry_id)
            if entry and entry.importance < 0.5:  # Only remove low-importance entries
                self._remove_entry(entry_id)
                removed_count += 1

        return removed_count

    def _remove_entry(self, entry_id: str):
        """Remove context entry from all indexes"""
        # Get entry data first
        entry_data = self.redis_client.hgetall(f"context:entry:{entry_id}")
        if entry_data:
            context_type = entry_data.get("context_type", "")
            tags = json.loads(entry_data.get("tags", "[]"))

            # Remove from indexes
            self.redis_client.zrem("context:by_importance", entry_id)
            self.redis_client.zrem("context:by_time", entry_id)
            self.redis_client.srem(f"context:by_type:{context_type}", entry_id)

            for tag in tags:
                self.redis_client.srem(f"context:by_tag:{tag}", entry_id)

        # Remove main entry
        self.redis_client.delete(f"context:entry:{entry_id}")

        # Remove from cache
        if entry_id in self.context_cache:
            del self.context_cache[entry_id]


# FastMCP Server
mcp = fastmcp.FastMCP("context-manager")
agent = ContextManagerAgent()


@mcp.tool()
def add_context(args_json: str) -> str:
    """Add new context with automatic importance analysis"""
    args = json.loads(args_json)
    content = args.get("content")
    context_type = args.get("context_type", "conversation")
    importance = args.get("importance")
    entry_id = agent.add_context(content, context_type, importance)
    entry = agent.get_context(entry_id)

    result = f"✅ **CONTEXT ADDED: {entry_id}**\n\n"
    result += f"**Type:** {entry.context_type}\n"
    result += f"**Importance:** {entry.importance:.2f}\n"
    result += f"**Tags:** {', '.join(sorted(entry.tags))}\n"

    if entry.related_entries:
        result += f"**Related Entries:** {len(entry.related_entries)}\n"

    return result


@mcp.tool()
def get_relevant_context(args_json: str) -> str:
    """Get context entries relevant to a query"""
    args = json.loads(args_json)
    query = args.get("query")
    limit = args.get("limit", 5)
    entries = agent.get_relevant_context(query, limit)

    if not entries:
        return f"🔍 No relevant context found for: '{query}'"

    result = f"🔍 **RELEVANT CONTEXT for '{query}'**\n\n"

    for i, entry in enumerate(entries, 1):
        result += f"**{i}. [{entry.context_type}] {entry.entry_id}**\n"
        result += f"   Importance: {entry.importance:.2f}\n"
        result += f"   Tags: {', '.join(sorted(entry.tags))}\n"

        # Show first 100 chars of content
        content_preview = entry.content[:100]
        if len(entry.content) > 100:
            content_preview += "..."
        result += f"   Content: {content_preview}\n\n"

    return result


@mcp.tool()
def get_session_summary(args_json: str = "{}") -> str:
    """Get summary of current session context"""
    args = json.loads(args_json)
    summary = agent.get_session_summary()

    result = f"📊 **SESSION CONTEXT SUMMARY**\n\n"
    result += f"**Session ID:** {summary.session_id}\n"
    result += f"**Total Entries:** {summary.total_entries}\n"
    result += f"**Important Entries:** {summary.important_entries}\n\n"

    if summary.context_types:
        result += "**Context Types:**\n"
        for ctx_type, count in summary.context_types.items():
            result += f"  - {ctx_type}: {count}\n"
        result += "\n"

    if summary.key_topics:
        result += f"**Key Topics:** {', '.join(summary.key_topics[:5])}\n\n"

    if summary.total_entries > 0:
        duration = summary.time_span[1] - summary.time_span[0]
        result += f"**Session Duration:** {duration/3600:.1f} hours\n"

    return result


@mcp.tool()
def search_context_by_tag(args_json: str) -> str:
    """Search context entries by tag"""
    args = json.loads(args_json)
    tag = args.get("tag")
    entry_ids = agent.redis_client.smembers(f"context:by_tag:{tag}")

    if not entry_ids:
        return f"🏷️ No context entries found with tag: '{tag}'"

    result = f"🏷️ **CONTEXT ENTRIES with tag '{tag}'**\n\n"

    entries = []
    for entry_id in entry_ids:
        entry = agent.get_context(entry_id)
        if entry:
            entries.append(entry)

    # Sort by importance
    entries.sort(key=lambda e: e.importance, reverse=True)

    for i, entry in enumerate(entries[:10], 1):  # Show top 10
        result += f"**{i}. {entry.entry_id}** ({entry.context_type})\n"
        result += f"   Importance: {entry.importance:.2f}\n"
        result += f"   Access count: {entry.access_count}\n\n"

    if len(entries) > 10:
        result += f"... and {len(entries) - 10} more entries\n"

    return result


@mcp.tool()
def cleanup_old_context(args_json: str = "{}") -> str:
    """Clean up old, unimportant context entries"""
    args = json.loads(args_json)
    max_age_days = args.get("max_age_days", 30)
    removed_count = agent.cleanup_old_context(max_age_days)
    return f"🧹 Cleaned up {removed_count} old context entries (older than {max_age_days} days)"


@mcp.tool()
def get_context_stats(args_json: str = "{}") -> str:
    """Get comprehensive context management statistics"""
    args = json.loads(args_json)
    # Get total counts
    total_entries = agent.redis_client.zcard("context:by_time")
    important_entries = agent.redis_client.zcount("context:by_importance", 0.7, 1.0)

    # Get type distribution
    types = ["conversation", "code", "error", "breakthrough", "workflow"]
    type_counts = {}
    for ctx_type in types:
        count = agent.redis_client.scard(f"context:by_type:{ctx_type}")
        if count > 0:
            type_counts[ctx_type] = count

    # Get popular tags
    tag_keys = agent.redis_client.keys("context:by_tag:*")
    tag_counts = {}
    for key in tag_keys[:20]:  # Limit to avoid too many keys
        tag = key.split(":")[-1]
        count = agent.redis_client.scard(key)
        if count > 1:  # Only show tags with multiple entries
            tag_counts[tag] = count

    # Sort tags by count
    sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)

    result = f"📈 **CONTEXT MANAGEMENT STATISTICS**\n\n"
    result += f"**Total Entries:** {total_entries}\n"
    result += f"**Important Entries:** {important_entries} ({important_entries/max(total_entries,1)*100:.1f}%)\n\n"

    if type_counts:
        result += "**Context Types:**\n"
        for ctx_type, count in type_counts.items():
            result += f"  - {ctx_type}: {count}\n"
        result += "\n"

    if sorted_tags:
        result += "**Popular Tags:**\n"
        for tag, count in sorted_tags[:10]:
            result += f"  - {tag}: {count}\n"

    return result


if __name__ == "__main__":
    print("🧠 Starting Context Manager Agent FastMCP Server")
    mcp.run()
