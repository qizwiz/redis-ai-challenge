#!/usr/bin/env python3
"""
Document Monitor Agent with Org-Mode Integration
Monitors documentation changes, updates content, and manages living documents
"""

import redis
import json
import time
import hashlib
import re
import os
from typing import Dict, List, Optional, Tuple, Set, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import fastmcp


@dataclass
class DocumentChange:
    file_path: str
    change_type: str  # 'created', 'modified', 'deleted'
    timestamp: float
    old_hash: str
    new_hash: str
    size_change: int
    change_summary: str


@dataclass
class OrgSection:
    title: str
    level: int
    line_start: int
    line_end: int
    content: str
    todo_items: List[str]
    code_blocks: List[Dict[str, str]]
    properties: Dict[str, str]


@dataclass
class DocumentMetrics:
    total_lines: int
    todo_items: int
    completed_items: int
    code_blocks: int
    mermaid_diagrams: int
    sections: int
    last_modified: float
    word_count: int


class OrgModeParser:
    def __init__(self):
        self.heading_pattern = re.compile(r"^(\*+)\s+(.+)$", re.MULTILINE)
        self.todo_pattern = re.compile(
            r"^\s*-\s*\[\s*([xX\s])\s*\]\s*(.+)$", re.MULTILINE
        )
        self.code_block_pattern = re.compile(
            r"#\+BEGIN_SRC\s+(\w+).*?\n(.*?)\n#\+END_SRC", re.DOTALL
        )
        self.mermaid_pattern = re.compile(
            r"#\+BEGIN_SRC\s+mermaid.*?\n(.*?)\n#\+END_SRC", re.DOTALL
        )
        self.property_pattern = re.compile(r"^\s*:(\w+):\s*(.+)$", re.MULTILINE)

    def parse_document(self, content: str) -> Tuple[List[OrgSection], DocumentMetrics]:
        """Parse org-mode document into structured sections and metrics"""
        lines = content.split("\n")
        sections = []
        current_section = None

        # Find all headings first
        headings = []
        for i, line in enumerate(lines):
            match = self.heading_pattern.match(line)
            if match:
                level = len(match.group(1))
                title = match.group(2).strip()
                headings.append((i, level, title))

        # Process sections
        for i, (line_num, level, title) in enumerate(headings):
            # Determine section end
            if i + 1 < len(headings):
                next_line = headings[i + 1][0]
            else:
                next_line = len(lines)

            # Extract section content
            section_lines = lines[line_num:next_line]
            section_content = "\n".join(section_lines)

            # Parse section elements
            todo_items = self._extract_todos(section_content)
            code_blocks = self._extract_code_blocks(section_content)
            properties = self._extract_properties(section_content)

            section = OrgSection(
                title=title,
                level=level,
                line_start=line_num,
                line_end=next_line - 1,
                content=section_content,
                todo_items=todo_items,
                code_blocks=code_blocks,
                properties=properties,
            )
            sections.append(section)

        # Calculate metrics
        metrics = self._calculate_metrics(content)

        return sections, metrics

    def _extract_todos(self, content: str) -> List[str]:
        """Extract TODO items from content"""
        todos = []
        matches = self.todo_pattern.findall(content)
        for status, text in matches:
            completed = status.lower() == "x"
            todos.append(f"{'[DONE]' if completed else '[TODO]'} {text}")
        return todos

    def _calculate_metrics(self, content: str) -> DocumentMetrics:
        """Calculate document metrics"""
        lines = content.split("\n")

        # Count elements
        todo_matches = self.todo_pattern.findall(content)
        todo_items = len(todo_matches)
        completed_items = sum(1 for status, _ in todo_matches if status.lower() == "x")

        code_blocks = len(self.code_block_pattern.findall(content))
        mermaid_diagrams = len(self.mermaid_pattern.findall(content))
        sections = len(self.heading_pattern.findall(content))

        # Word count (approximate)
        words = re.findall(r"\b\w+\b", content)
        word_count = len(words)

        return DocumentMetrics(
            total_lines=len(lines),
            todo_items=todo_items,
            completed_items=completed_items,
            code_blocks=code_blocks,
            mermaid_diagrams=mermaid_diagrams,
            sections=sections,
            last_modified=time.time(),
            word_count=word_count,
        )


class DocumentMonitorAgent:
    def __init__(
        self,
        watch_dir: str = "/Users/jonathanhill/src/redis-ai-challenge",
        redis_client: Optional[redis.Redis] = None,
    ):
        self.watch_dir = Path(watch_dir)
        self.redis_client = redis_client or redis.Redis(decode_responses=True)
        self.parser = OrgModeParser()
        self.watched_files = {}  # file_path -> file_hash
        self.scan_interval = 10  # seconds
        self.last_scan = 0

    def scan_documents(self) -> List[DocumentChange]:
        """Scan for document changes"""
        changes = []
        current_time = time.time()

        # Find all org files
        org_files = list(self.watch_dir.glob("**/*.org"))

        for file_path in org_files:
            file_str = str(file_path)
            old_hash = self.watched_files.get(file_str, "")

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                new_hash = hashlib.md5(content.encode()).hexdigest()

                if old_hash != new_hash:
                    # Determine change type
                    if old_hash == "":
                        change_type = "created"
                        size_change = len(content)
                        change_summary = (
                            f"New document with {len(content.split())} words"
                        )
                    else:
                        change_type = "modified"
                        # Estimate size change (rough)
                        old_size = self._get_cached_size(file_str)
                        size_change = len(content) - old_size
                        change_summary = self._analyze_change(file_str, content)

                    change = DocumentChange(
                        file_path=file_str,
                        change_type=change_type,
                        timestamp=current_time,
                        old_hash=old_hash,
                        new_hash=new_hash,
                        size_change=size_change,
                        change_summary=change_summary,
                    )
                    changes.append(change)

                    # Update tracking
                    self.watched_files[file_str] = new_hash
                    self._store_document_info(file_str, content)

            except Exception as e:
                # File might be deleted or inaccessible
                if old_hash != "":
                    change = DocumentChange(
                        file_path=file_str,
                        change_type="deleted",
                        timestamp=current_time,
                        old_hash=old_hash,
                        new_hash="",
                        size_change=0,
                        change_summary=f"Document deleted or inaccessible: {str(e)}",
                    )
                    changes.append(change)

                    # Remove from tracking
                    if file_str in self.watched_files:
                        del self.watched_files[file_str]

        self.last_scan = current_time

        # Store changes in Redis
        for change in changes:
            self._store_change(change)

        return changes

    def _analyze_change(self, file_path: str, new_content: str) -> str:
        """Analyze what changed in the document"""
        # Get previous analysis
        prev_data = self.redis_client.hgetall(
            f"doc:analysis:{hashlib.md5(file_path.encode()).hexdigest()}"
        )

        if not prev_data:
            return "Content modified (no previous analysis available)"

        # Parse new content
        sections, metrics = self.parser.parse_document(new_content)

        # Compare with previous metrics
        try:
            prev_todos = int(prev_data.get("todo_items", 0))
            prev_completed = int(prev_data.get("completed_items", 0))
            prev_sections = int(prev_data.get("sections", 0))
            prev_code_blocks = int(prev_data.get("code_blocks", 0))

            changes = []

            if metrics.todo_items != prev_todos:
                diff = metrics.todo_items - prev_todos
                changes.append(f"TODOs: {diff:+d}")

            if metrics.completed_items != prev_completed:
                diff = metrics.completed_items - prev_completed
                changes.append(f"Completed: {diff:+d}")

            if metrics.sections != prev_sections:
                diff = metrics.sections - prev_sections
                changes.append(f"Sections: {diff:+d}")

            if metrics.code_blocks != prev_code_blocks:
                diff = metrics.code_blocks - prev_code_blocks
                changes.append(f"Code blocks: {diff:+d}")

            if changes:
                return f"Changes: {', '.join(changes)}"
            else:
                return "Content modified (structure unchanged)"

        except (ValueError, KeyError):
            return "Content modified (analysis comparison failed)"

    def _store_document_info(self, file_path: str, content: str):
        """Store document analysis in Redis"""
        sections, metrics = self.parser.parse_document(content)

        # Store metrics
        file_key = hashlib.md5(file_path.encode()).hexdigest()
        metrics_data = {
            "file_path": file_path,
            "total_lines": str(metrics.total_lines),
            "todo_items": str(metrics.todo_items),
            "completed_items": str(metrics.completed_items),
            "code_blocks": str(metrics.code_blocks),
            "mermaid_diagrams": str(metrics.mermaid_diagrams),
            "sections": str(metrics.sections),
            "word_count": str(metrics.word_count),
            "last_analyzed": str(time.time()),
        }

        self.redis_client.hset(f"doc:analysis:{file_key}", mapping=metrics_data)

        # Store sections
        for i, section in enumerate(sections):
            section_data = {
                "title": section.title,
                "level": str(section.level),
                "line_start": str(section.line_start),
                "line_end": str(section.line_end),
                "todo_count": str(len(section.todo_items)),
                "code_block_count": str(len(section.code_blocks)),
                "properties": json.dumps(section.properties),
            }

            self.redis_client.hset(f"doc:section:{file_key}:{i}", mapping=section_data)

        # Set expiration (documents stay for 30 days)
        self.redis_client.expire(f"doc:analysis:{file_key}", 30 * 24 * 3600)

    def _store_change(self, change: DocumentChange):
        """Store document change in Redis"""
        change_data = asdict(change)
        change_id = hashlib.md5(
            f"{change.file_path}{change.timestamp}".encode()
        ).hexdigest()[:12]

        # Store in stream for real-time monitoring
        self.redis_client.xadd(
            "doc:changes",
            {
                "change_id": change_id,
                "file_path": change.file_path,
                "change_type": change.change_type,
                "timestamp": str(change.timestamp),
                "change_summary": change.change_summary,
                "size_change": str(change.size_change),
            },
        )

        # Store detailed change
        self.redis_client.hset(
            f"doc:change:{change_id}",
            mapping={key: str(value) for key, value in change_data.items()},
        )

        # Set expiration (changes kept for 7 days)
        self.redis_client.expire(f"doc:change:{change_id}", 7 * 24 * 3600)

    def get_document_summary(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Get comprehensive summary of a document"""
        file_key = hashlib.md5(file_path.encode()).hexdigest()

        # Get metrics
        metrics_data = self.redis_client.hgetall(f"doc:analysis:{file_key}")
        if not metrics_data:
            return None

        # Get sections
        section_keys = self.redis_client.keys(f"doc:section:{file_key}:*")
        sections = []

        for section_key in section_keys:
            section_data = self.redis_client.hgetall(section_key)
            if section_data:
                sections.append(
                    {
                        "title": section_data["title"],
                        "level": int(section_data["level"]),
                        "todo_count": int(section_data["todo_count"]),
                        "code_block_count": int(section_data["code_block_count"]),
                        "properties": json.loads(section_data.get("properties", "{}")),
                    }
                )

        # Sort sections by line number
        sections.sort(key=lambda s: s.get("line_start", 0))

        return {
            "file_path": file_path,
            "metrics": {
                k: int(v) if v.isdigit() else v for k, v in metrics_data.items()
            },
            "sections": sections,
            "last_analyzed": float(metrics_data.get("last_analyzed", 0)),
        }

    def get_recent_changes(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent document changes"""
        changes = self.redis_client.xrevrange("doc:changes", count=limit)

        result = []
        for change_id, fields in changes:
            result.append(
                {
                    "change_id": change_id,
                    "file_path": fields["file_path"],
                    "change_type": fields["change_type"],
                    "timestamp": float(fields["timestamp"]),
                    "change_summary": fields["change_summary"],
                    "size_change": int(fields["size_change"]),
                }
            )

        return result

    def update_document_todo(
        self, file_path: str, todo_text: str, completed: bool = False
    ) -> bool:
        """Update TODO item in document"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Find the TODO item
            if completed:
                # Mark as completed
                pattern = re.compile(
                    rf"(\s*-\s*\[\s*\]\s*){re.escape(todo_text)}", re.MULTILINE
                )
                new_content = pattern.sub(rf"\1[x] {todo_text}", content)
            else:
                # Mark as incomplete
                pattern = re.compile(
                    rf"(\s*-\s*\[\s*[xX]\s*\]\s*){re.escape(todo_text)}", re.MULTILINE
                )
                new_content = pattern.sub(rf"\1[ ] {todo_text}", content)

            if new_content != content:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(new_content)
                return True

        except Exception as e:
            print(f"Error updating TODO: {e}")

        return False


# FastMCP Server
mcp = fastmcp.FastMCP("document-monitor")
agent = DocumentMonitorAgent()


@mcp.tool()
def scan_documents() -> str:
    """Scan for document changes and analyze them"""
    changes = agent.scan_documents()

    if not changes:
        return "📄 No document changes detected since last scan"

    result = f"📄 **DOCUMENT CHANGES DETECTED: {len(changes)}**\n\n"

    for change in changes:
        result += f"**{change.change_type.upper()}: {Path(change.file_path).name}**\n"
        result += f"  Summary: {change.change_summary}\n"
        result += f"  Size change: {change.size_change:+d} chars\n"
        result += (
            f"  Time: {time.strftime('%H:%M:%S', time.localtime(change.timestamp))}\n\n"
        )

    return result


@mcp.tool()
def get_document_summary(file_path: str) -> str:
    """Get comprehensive summary of a document"""
    summary = agent.get_document_summary(file_path)

    if not summary:
        return f"❌ No analysis available for: {file_path}"

    metrics = summary["metrics"]
    sections = summary["sections"]

    result = f"📊 **DOCUMENT SUMMARY: {Path(file_path).name}**\n\n"

    # Metrics
    result += f"**Metrics:**\n"
    result += f"  Lines: {metrics.get('total_lines', 0)}\n"
    result += f"  Words: {metrics.get('word_count', 0)}\n"
    result += f"  Sections: {metrics.get('sections', 0)}\n"
    result += f"  TODO items: {metrics.get('todo_items', 0)}\n"
    result += f"  Completed: {metrics.get('completed_items', 0)}\n"
    result += f"  Code blocks: {metrics.get('code_blocks', 0)}\n"
    result += f"  Mermaid diagrams: {metrics.get('mermaid_diagrams', 0)}\n\n"

    # Progress
    if metrics.get("todo_items", 0) > 0:
        progress = (
            metrics.get("completed_items", 0) / metrics.get("todo_items", 1)
        ) * 100
        result += f"**Progress: {progress:.1f}% complete**\n\n"

    # Top sections
    if sections:
        result += "**Sections:**\n"
        for section in sections[:5]:  # Show top 5 sections
            level_indent = "  " * (section["level"] - 1)
            result += f"{level_indent}- {section['title']}"
            if section["todo_count"] > 0:
                result += f" ({section['todo_count']} TODOs)"
            result += "\n"

    return result


@mcp.tool()
def get_recent_changes(limit: int = 5) -> str:
    """Get recent document changes"""
    changes = agent.get_recent_changes(limit)

    if not changes:
        return "📄 No recent document changes"

    result = f"📄 **RECENT DOCUMENT CHANGES**\n\n"

    for change in changes:
        time_str = time.strftime("%m/%d %H:%M", time.localtime(change["timestamp"]))
        result += f"**{time_str}: {Path(change['file_path']).name}**\n"
        result += f"  {change['change_type']}: {change['change_summary']}\n\n"

    return result


@mcp.tool()
def update_todo_status(file_path: str, todo_text: str, completed: bool = True) -> str:
    """Update TODO item status in document"""
    success = agent.update_document_todo(file_path, todo_text, completed)

    if success:
        status = "completed" if completed else "reopened"
        return f"✅ TODO item {status}: {todo_text}"
    else:
        return f"❌ Failed to update TODO item: {todo_text}"


@mcp.tool()
def monitor_status() -> str:
    """Get document monitoring status"""
    watched_count = len(agent.watched_files)
    last_scan_time = (
        time.strftime("%H:%M:%S", time.localtime(agent.last_scan))
        if agent.last_scan
        else "Never"
    )

    result = f"👁️ **DOCUMENT MONITOR STATUS**\n\n"
    result += f"**Watched Files:** {watched_count}\n"
    result += f"**Watch Directory:** {agent.watch_dir}\n"
    result += f"**Last Scan:** {last_scan_time}\n"
    result += f"**Scan Interval:** {agent.scan_interval} seconds\n\n"

    if agent.watched_files:
        result += "**Monitored Files:**\n"
        for file_path in sorted(agent.watched_files.keys()):
            result += f"  - {Path(file_path).name}\n"

    return result


@mcp.tool()
def analyze_document_trends() -> str:
    """Analyze trends across all monitored documents"""
    # Get all document analyses
    analysis_keys = agent.redis_client.keys("doc:analysis:*")

    if not analysis_keys:
        return "📈 No documents analyzed yet"

    total_todos = 0
    total_completed = 0
    total_sections = 0
    total_code_blocks = 0
    documents = []

    for key in analysis_keys:
        data = agent.redis_client.hgetall(key)
        if data:
            todos = int(data.get("todo_items", 0))
            completed = int(data.get("completed_items", 0))
            sections = int(data.get("sections", 0))
            code_blocks = int(data.get("code_blocks", 0))

            total_todos += todos
            total_completed += completed
            total_sections += sections
            total_code_blocks += code_blocks

            documents.append(
                {
                    "file": Path(data["file_path"]).name,
                    "todos": todos,
                    "completed": completed,
                    "completion_rate": completed / max(todos, 1) * 100,
                }
            )

    result = f"📈 **DOCUMENT TREND ANALYSIS**\n\n"
    result += f"**Total Documents:** {len(documents)}\n"
    result += f"**Total TODO Items:** {total_todos}\n"
    result += f"**Total Completed:** {total_completed}\n"
    result += f"**Overall Progress:** {total_completed/max(total_todos,1)*100:.1f}%\n"
    result += f"**Total Sections:** {total_sections}\n"
    result += f"**Total Code Blocks:** {total_code_blocks}\n\n"

    # Sort by completion rate
    documents.sort(key=lambda d: d["completion_rate"], reverse=True)

    result += "**Document Progress:**\n"
    for doc in documents[:10]:  # Top 10
        result += f"  - {doc['file']}: {doc['completion_rate']:.1f}% ({doc['completed']}/{doc['todos']})\n"

    return result


if __name__ == "__main__":
    print("📄 Starting Document Monitor Agent FastMCP Server")
    mcp.run()
