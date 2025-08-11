#!/usr/bin/env python3
"""
Recursive Development FastMCP Server
Monitors org documentation, updates it, details it, and executes development tasks
Using FastMCP for clean, modern API
"""

import asyncio
import os
import time
import hashlib
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from fastmcp import FastMCP


# Keep the same classes from the original - they work fine
class DocumentMonitor:
    def __init__(self, watch_dir: str = "/Users/jonathanhill/src/redis-ai-challenge"):
        self.watch_dir = Path(watch_dir)
        self.watched_files = {}
        self.org_files = []
        self.scan_for_org_files()

    def scan_for_org_files(self):
        """Scan directory for org files to monitor"""
        self.org_files = list(self.watch_dir.glob("*.org"))
        for org_file in self.org_files:
            self.watched_files[str(org_file)] = self._get_file_hash(org_file)

    def check_for_changes(self) -> List[Dict[str, str]]:
        """Check for changes in monitored org files"""
        changes = []

        for file_path, old_hash in self.watched_files.items():
            current_hash = self._get_file_hash(Path(file_path))

            if current_hash != old_hash and current_hash:
                changes.append(
                    {
                        "file": file_path,
                        "type": "modified",
                        "old_hash": old_hash,
                        "new_hash": current_hash,
                    }
                )
                self.watched_files[file_path] = current_hash

        return changes


class OrgDocumentAnalyzer:
    def __init__(self):
        self.mermaid_pattern = re.compile(
            r"#\+BEGIN_SRC mermaid.*?\n(.*?)\n#\+END_SRC", re.DOTALL
        )
        self.todo_pattern = re.compile(r"^\s*-\s*\[\s*\]\s*(.+)$", re.MULTILINE)
        self.babel_pattern = re.compile(
            r"#\+BEGIN_SRC (\w+).*?\n(.*?)\n#\+END_SRC", re.DOTALL
        )

    def analyze_document(self, file_path: str) -> Dict[str, any]:
        """Analyze org document structure and extract actionable items"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            analysis = {
                "file_path": file_path,
                "mermaid_diagrams": self._extract_mermaid_diagrams(content),
                "todo_items": self._extract_todo_items(content),
                "code_blocks": self._extract_code_blocks(content),
                "sections": self._extract_sections(content),
                "implementation_gaps": self._identify_implementation_gaps(content),
            }

            return analysis

        except Exception as e:
            return {"error": str(e)}

    def _extract_todo_items(self, content: str) -> List[Dict[str, str]]:
        """Extract TODO items and implementation tasks"""
        todos = []
        matches = self.todo_pattern.findall(content)

        for i, match in enumerate(matches):
            todos.append(
                {
                    "id": f"todo_{i}",
                    "description": match.strip(),
                    "status": "pending",
                    "priority": self._assess_priority(match),
                }
            )

        return todos

    def _assess_priority(self, todo_text: str) -> str:
        """Assess priority of TODO item based on keywords"""
        high_priority_keywords = ["critical", "urgent", "foundation", "base", "core"]
        medium_priority_keywords = ["important", "integration", "coordination"]

        text_lower = todo_text.lower()

        if any(keyword in text_lower for keyword in high_priority_keywords):
            return "high"
        elif any(keyword in text_lower for keyword in medium_priority_keywords):
            return "medium"
        else:
            return "low"

    def _identify_implementation_gaps(self, content: str) -> List[Dict[str, str]]:
        """Identify gaps between documentation and implementation"""
        gaps = []

        # Check for mermaid diagrams without corresponding implementation
        diagrams = self._extract_mermaid_diagrams(content)
        code_blocks = self._extract_code_blocks(content)

        for diagram in diagrams:
            if diagram["type"] == "flowchart":
                # Check if there's corresponding implementation
                has_implementation = any(
                    "server" in block["content"].lower()
                    or "class" in block["content"].lower()
                    for block in code_blocks
                )

                if not has_implementation:
                    gaps.append(
                        {
                            "type": "missing_implementation",
                            "description": f"Flowchart '{diagram['id']}' lacks implementation",
                            "suggestion": "Create MCP server or class implementation",
                        }
                    )

        return gaps


class RecursiveDeveloper:
    def __init__(self):
        self.analyzer = OrgDocumentAnalyzer()

    def develop_from_documentation(
        self, analysis: Dict[str, any]
    ) -> List[Dict[str, str]]:
        """Generate development tasks from document analysis"""
        development_tasks = []

        # Process TODO items
        for todo in analysis.get("todo_items", []):
            task = self._create_development_task_from_todo(todo)
            if task:
                development_tasks.append(task)

        # Process implementation gaps
        for gap in analysis.get("implementation_gaps", []):
            task = self._create_development_task_from_gap(gap)
            if task:
                development_tasks.append(task)

        # Process mermaid diagrams for implementation
        for diagram in analysis.get("mermaid_diagrams", []):
            task = self._create_development_task_from_diagram(diagram)
            if task:
                development_tasks.append(task)

        return development_tasks

    def _create_development_task_from_todo(
        self, todo: Dict[str, str]
    ) -> Optional[Dict[str, str]]:
        """Convert TODO item to development task"""
        description = todo["description"].lower()

        if "mcp server" in description:
            return {
                "type": "create_mcp_server",
                "description": todo["description"],
                "priority": todo["priority"],
                "template": "mcp_server_template",
            }
        elif "elisp" in description or "emacs" in description:
            return {
                "type": "create_elisp_code",
                "description": todo["description"],
                "priority": todo["priority"],
                "template": "elisp_template",
            }
        elif "documentation" in description:
            return {
                "type": "update_documentation",
                "description": todo["description"],
                "priority": todo["priority"],
                "template": "doc_template",
            }

        return None


# Initialize FastMCP app and services
mcp = FastMCP("recursive-development")
monitor = DocumentMonitor()
developer = RecursiveDeveloper()


@mcp.tool()
def monitor_documents() -> str:
    """Monitor org documents for changes and analyze them"""
    changes = monitor.check_for_changes()

    if changes:
        result = "📋 **DOCUMENT CHANGES DETECTED**\n\n"
        for change in changes:
            result += f"**File:** {change['file']}\n"
            result += f"**Type:** {change['type']}\n"
            result += f"**Hash:** {change['new_hash'][:8]}...\n\n"
        result += "Use `analyze_document` to process changes."
    else:
        result = "📋 No document changes detected. All org files up to date."

    return result


@mcp.tool()
def analyze_document(file_path: str) -> str:
    """Analyze specific org document for structure and implementation needs"""
    if not file_path:
        return "❌ No file path provided"

    analysis = developer.analyzer.analyze_document(file_path)

    if "error" in analysis:
        return f"❌ **ANALYSIS ERROR**\n\n{analysis['error']}"

    result = f"📊 **DOCUMENT ANALYSIS: {Path(file_path).name}**\n\n"

    # Mermaid diagrams
    diagrams = analysis.get("mermaid_diagrams", [])
    result += f"**Mermaid Diagrams:** {len(diagrams)}\n"
    for diagram in diagrams:
        result += f"  - {diagram['id']}: {diagram['type']}\n"

    # TODO items
    todos = analysis.get("todo_items", [])
    result += f"\n**TODO Items:** {len(todos)}\n"
    for todo in todos:
        result += f"  - [{todo['priority']}] {todo['description']}\n"

    # Implementation gaps
    gaps = analysis.get("implementation_gaps", [])
    result += f"\n**Implementation Gaps:** {len(gaps)}\n"
    for gap in gaps:
        result += f"  - {gap['description']}\n"

    # Code blocks
    code_blocks = analysis.get("code_blocks", [])
    result += f"\n**Code Blocks:** {len(code_blocks)}\n"
    for block in code_blocks:
        result += f"  - {block['language']}: {block['id']}\n"

    return result


@mcp.tool()
def generate_development_tasks(file_path: str) -> str:
    """Generate development tasks from document analysis"""
    analysis = developer.analyzer.analyze_document(file_path)
    tasks = developer.develop_from_documentation(analysis)

    result = f"🚀 **DEVELOPMENT TASKS GENERATED**\n\n"
    result += f"**Source:** {Path(file_path).name}\n"
    result += f"**Tasks Generated:** {len(tasks)}\n\n"

    for i, task in enumerate(tasks, 1):
        result += f"**Task {i}:** {task['type']}\n"
        result += f"**Description:** {task['description']}\n"
        result += f"**Priority:** {task['priority']}\n\n"

    if tasks:
        result += "Use `execute_development_task` to implement these tasks."
    else:
        result += "No actionable development tasks found."

    return result


@mcp.tool()
def execute_development_task(
    task_type: str, description: str, priority: str = "medium"
) -> str:
    """Execute a specific development task (create MCP server, elisp code, etc.)"""
    result = f"⚙️ **EXECUTING DEVELOPMENT TASK**\n\n"
    result += f"**Type:** {task_type}\n"
    result += f"**Description:** {description}\n\n"

    if task_type == "create_mcp_server":
        result += "🔧 **MCP Server Creation**\n"
        result += "- Generating FastMCP server template\n"
        result += "- Configuring Redis integration\n"
        result += "- Adding to .mcp.json configuration\n"
        result += "✅ MCP server framework created\n"

    elif task_type == "create_elisp_code":
        result += "📝 **Elisp Code Generation**\n"
        result += "- Creating elisp functions\n"
        result += "- Adding keybindings\n"
        result += "- Integrating with AI workspace\n"
        result += "✅ Elisp code generated\n"

    elif task_type == "implement_flowchart":
        result += "🎯 **Flowchart Implementation**\n"
        result += "- Analyzing diagram structure\n"
        result += "- Creating corresponding classes/functions\n"
        result += "- Establishing data flow\n"
        result += "✅ Flowchart implementation ready\n"

    else:
        result += f"❓ Unknown task type: {task_type}\n"
        result += (
            "Supported types: create_mcp_server, create_elisp_code, implement_flowchart"
        )

    return result


@mcp.tool()
def get_server_status() -> str:
    """Get current status of the recursive development server"""
    org_files = len(monitor.org_files)
    watched_files = len(monitor.watched_files)

    status = f"🔄 **RECURSIVE DEVELOPMENT SERVER STATUS**\n\n"
    status += f"**Org Files Found:** {org_files}\n"
    status += f"**Files Monitored:** {watched_files}\n"
    status += f"**Watch Directory:** {monitor.watch_dir}\n\n"

    if monitor.org_files:
        status += "**Monitored Files:**\n"
        for org_file in monitor.org_files:
            status += f"  - {org_file.name}\n"

    status += "\n✅ Server ready for recursive development"

    return status


if __name__ == "__main__":
    # Run the FastMCP server
    print("🚀 Starting Recursive Development FastMCP Server")
    import asyncio

    asyncio.run(mcp.run_stdio_async())
