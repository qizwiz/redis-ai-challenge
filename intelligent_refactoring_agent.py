#!/usr/bin/env python3
"""
Intelligent Refactoring Agent - Actually refactor code and commit changes

This agent can:
1. Analyze entire codebase for dead code and refactoring opportunities
2. Make intelligent refactoring decisions
3. Execute the refactoring safely
4. Commit changes with meaningful messages
"""

import os
import ast
import git
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Set
from dataclasses import dataclass
import redis
import json
import time


@dataclass
class RefactoringOpportunity:
    """A refactoring opportunity"""

    file_path: str
    opportunity_type: (
        str  # "dead_code", "duplicate_function", "unused_import", "long_function"
    )
    description: str
    line_start: int
    line_end: int
    confidence: float
    estimated_savings: int  # lines of code
    code_snippet: str


class IntelligentRefactoringAgent:
    """Agent that can actually refactor code intelligently"""

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.repo = None
        try:
            self.repo = git.Repo(os.getcwd())
        except:
            print("Warning: Not in a git repository")

        self.dead_code_patterns = []
        self.refactoring_opportunities = []

    def analyze_codebase_for_refactoring(
        self, project_path: str = "."
    ) -> List[RefactoringOpportunity]:
        """Analyze entire codebase for refactoring opportunities"""

        opportunities = []
        python_files = list(Path(project_path).rglob("*.py"))

        print(
            f"🔍 Analyzing {len(python_files)} Python files for refactoring opportunities..."
        )

        # Track all function definitions and their usage
        all_functions = {}
        all_imports = {}

        # First pass - collect all functions and imports
        for py_file in python_files:
            if self._should_skip_file(py_file):
                continue

            try:
                with open(py_file, "r", encoding="utf-8") as f:
                    content = f.read()

                tree = ast.parse(content)

                # Collect function definitions
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        func_key = f"{py_file}:{node.name}"
                        all_functions[func_key] = {
                            "file": str(py_file),
                            "name": node.name,
                            "line_start": node.lineno,
                            "line_end": node.end_lineno,
                            "is_private": node.name.startswith("_"),
                            "calls": [],
                            "complexity": self._calculate_complexity(node),
                            "length": node.end_lineno - node.lineno,
                        }

                    elif isinstance(node, (ast.Import, ast.ImportFrom)):
                        import_key = f"{py_file}:{ast.unparse(node)}"
                        all_imports[import_key] = {
                            "file": str(py_file),
                            "line": node.lineno,
                            "statement": ast.unparse(node),
                            "used": False,
                        }

            except Exception as e:
                print(f"Error analyzing {py_file}: {e}")
                continue

        # Second pass - find function calls and import usage
        for py_file in python_files:
            if self._should_skip_file(py_file):
                continue

            try:
                with open(py_file, "r", encoding="utf-8") as f:
                    content = f.read()

                tree = ast.parse(content)

                for node in ast.walk(tree):
                    if isinstance(node, ast.Call):
                        # Track function calls
                        if isinstance(node.func, ast.Name):
                            func_name = node.func.id
                            # Mark functions as used
                            for func_key, func_info in all_functions.items():
                                if func_info["name"] == func_name:
                                    func_info["calls"].append(str(py_file))

                    elif isinstance(node, ast.Name):
                        # Track name usage for imports
                        name = node.id
                        for import_key, import_info in all_imports.items():
                            if name in import_info["statement"]:
                                import_info["used"] = True

            except Exception as e:
                continue

        # Find dead code opportunities
        opportunities.extend(self._find_dead_functions(all_functions))
        opportunities.extend(self._find_unused_imports(all_imports))
        opportunities.extend(self._find_duplicate_code(python_files))
        opportunities.extend(self._find_long_functions(all_functions))

        print(f"✅ Found {len(opportunities)} refactoring opportunities")
        return opportunities

    def _find_dead_functions(
        self, all_functions: Dict[str, Any]
    ) -> List[RefactoringOpportunity]:
        """Find functions that are defined but never called"""

        opportunities = []

        for func_key, func_info in all_functions.items():
            # Skip if function has external calls or is a special method
            if (
                not func_info["calls"]
                and func_info["is_private"]
                and not func_info["name"].startswith("__")
                and func_info["name"] not in ["main", "test_", "setUp", "tearDown"]
            ):

                try:
                    with open(func_info["file"], "r") as f:
                        lines = f.readlines()

                    code_snippet = "".join(
                        lines[func_info["line_start"] - 1 : func_info["line_end"]]
                    )

                    opportunities.append(
                        RefactoringOpportunity(
                            file_path=func_info["file"],
                            opportunity_type="dead_code",
                            description=f"Dead function '{func_info['name']}' - never called",
                            line_start=func_info["line_start"],
                            line_end=func_info["line_end"],
                            confidence=0.8,
                            estimated_savings=func_info["length"],
                            code_snippet=code_snippet[:200],  # First 200 chars
                        )
                    )
                except:
                    continue

        return opportunities

    def _find_duplicate_code(
        self, python_files: List[Path]
    ) -> List[RefactoringOpportunity]:
        """Find duplicate code blocks"""

        opportunities = []

        # Simple duplicate detection - look for identical function bodies
        function_bodies = {}

        for py_file in python_files:
            if self._should_skip_file(py_file):
                continue

            try:
                with open(py_file, "r", encoding="utf-8") as f:
                    content = f.read()

                tree = ast.parse(content)

                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        # Get function body as string
                        lines = content.split("\n")
                        body_lines = lines[
                            node.lineno : node.end_lineno - 1
                        ]  # Skip def line
                        body = "\n".join(body_lines).strip()

                        if len(body) > 100:  # Only check substantial functions
                            body_hash = hash(body)

                            if body_hash in function_bodies:
                                # Found duplicate
                                original = function_bodies[body_hash]
                                opportunities.append(
                                    RefactoringOpportunity(
                                        file_path=str(py_file),
                                        opportunity_type="duplicate_function",
                                        description=f"Duplicate of {original['name']} in {Path(original['file']).name}",
                                        line_start=node.lineno,
                                        line_end=node.end_lineno,
                                        confidence=0.7,
                                        estimated_savings=node.end_lineno - node.lineno,
                                        code_snippet=body[:200],
                                    )
                                )
                            else:
                                function_bodies[body_hash] = {
                                    "file": str(py_file),
                                    "name": node.name,
                                    "line_start": node.lineno,
                                }

            except Exception as e:
                continue

        return opportunities

    def _find_long_functions(
        self, all_functions: Dict[str, Any]
    ) -> List[RefactoringOpportunity]:
        """Find functions that are too long and should be refactored"""

        opportunities = []

        for func_key, func_info in all_functions.items():
            if func_info["length"] > 50 or func_info["complexity"] > 10:
                try:
                    with open(func_info["file"], "r") as f:
                        lines = f.readlines()

                    code_snippet = "".join(
                        lines[func_info["line_start"] - 1 : func_info["line_start"] + 5]
                    )

                    opportunities.append(
                        RefactoringOpportunity(
                            file_path=func_info["file"],
                            opportunity_type="long_function",
                            description=f"Long function '{func_info['name']}' ({func_info['length']} lines, complexity {func_info['complexity']})",
                            line_start=func_info["line_start"],
                            line_end=func_info["line_end"],
                            confidence=0.6,
                            estimated_savings=0,  # Refactoring, not removal
                            code_snippet=code_snippet[:200],
                        )
                    )
                except:
                    continue

        return opportunities

    def execute_refactoring(
        self, opportunities: List[RefactoringOpportunity]
    ) -> Dict[str, Any]:
        """Execute refactoring changes"""

        results = {
            "success": True,
            "changes_made": [],
            "errors": [],
            "files_modified": set(),
            "lines_removed": 0,
        }

        print(f"🔧 Executing {len(opportunities)} refactoring changes...")

        # Group opportunities by file for efficient processing
        by_file = {}
        for opp in opportunities:
            if opp.file_path not in by_file:
                by_file[opp.file_path] = []
            by_file[opp.file_path].append(opp)

        # Process each file
        for file_path, file_opportunities in by_file.items():
            try:
                # Sort by line number (reverse order to avoid line shifting)
                file_opportunities.sort(key=lambda x: x.line_start, reverse=True)

                with open(file_path, "r") as f:
                    lines = f.readlines()

                original_lines = len(lines)

                for opp in file_opportunities:
                    if opp.opportunity_type == "dead_code":
                        # Remove dead function
                        if self._safe_to_remove_function(opp, lines):
                            del lines[opp.line_start - 1 : opp.line_end]
                            results["changes_made"].append(
                                f"Removed dead function {opp.description}"
                            )
                            results["lines_removed"] += opp.estimated_savings

                    elif opp.opportunity_type == "unused_import":
                        # Remove unused import
                        if opp.line_start <= len(lines):
                            removed_line = lines[opp.line_start - 1].strip()
                            del lines[opp.line_start - 1 : opp.line_start]
                            results["changes_made"].append(
                                f"Removed unused import: {removed_line}"
                            )
                            results["lines_removed"] += 1

                # Write back if changes were made
                if len(lines) != original_lines:
                    with open(file_path, "w") as f:
                        f.writelines(lines)
                    results["files_modified"].add(file_path)

            except Exception as e:
                results["errors"].append(f"Error processing {file_path}: {e}")
                results["success"] = False

        print(
            f"✅ Refactoring complete: {len(results['changes_made'])} changes, {results['lines_removed']} lines removed"
        )
        return results

    def _safe_to_remove_function(
        self, opp: RefactoringOpportunity, lines: List[str]
    ) -> bool:
        """Check if it's safe to remove this function"""

        # Basic safety checks
        func_lines = lines[opp.line_start - 1 : opp.line_end]
        func_content = "".join(func_lines)

        # Don't remove if it contains TODO or FIXME
        if any(
            keyword in func_content.upper() for keyword in ["TODO", "FIXME", "HACK"]
        ):
            return False

        # Don't remove if it's a test function
        if "def test_" in func_content or "def setUp" in func_content:
            return False

        # Don't remove if it's very short (might be important)
        if opp.line_end - opp.line_start < 3:
            return False

        return True

    def commit_refactoring_changes(self, results: Dict[str, Any]) -> bool:
        """Commit refactoring changes to git"""

        if not self.repo or not results["files_modified"]:
            print("❌ No git repo or no files to commit")
            return False

        try:
            # Stage modified files
            for file_path in results["files_modified"]:
                self.repo.index.add([file_path])

            # Create detailed commit message
            commit_message = self._generate_commit_message(results)

            # Commit changes
            commit = self.repo.index.commit(commit_message)

            print(f"✅ Committed refactoring changes: {commit.hexsha[:8]}")
            print(f"📝 Commit message:\n{commit_message}")

            return True

        except Exception as e:
            print(f"❌ Failed to commit changes: {e}")
            return False

    def _generate_commit_message(self, results: Dict[str, Any]) -> str:
        """Generate intelligent commit message"""

        summary_parts = []

        dead_code_count = len(
            [c for c in results["changes_made"] if "dead function" in c]
        )
        unused_import_count = len(
            [c for c in results["changes_made"] if "unused import" in c]
        )

        if dead_code_count > 0:
            summary_parts.append(f"remove {dead_code_count} dead functions")
        if unused_import_count > 0:
            summary_parts.append(f"remove {unused_import_count} unused imports")

        summary = "refactor: " + ", ".join(summary_parts)

        details = []
        details.append(f"• {len(results['files_modified'])} files modified")
        details.append(f"• {results['lines_removed']} lines removed")
        details.append("")
        details.append("Changes made:")

        for change in results["changes_made"][:10]:  # Limit to first 10
            details.append(f"• {change}")

        if len(results["changes_made"]) > 10:
            details.append(
                f"• ... and {len(results['changes_made']) - 10} more changes"
            )

        details.append("")
        details.append("🤖 Generated with [Claude Code](https://claude.ai/code)")
        details.append("")
        details.append("Co-Authored-By: Claude <noreply@anthropic.com>")

        return f"{summary}\n\n" + "\n".join(details)


def intelligent_refactoring_command():
    """Execute intelligent refactoring on the codebase"""

    print("🤖 INTELLIGENT REFACTORING AGENT")
    print("=" * 50)
    print("Analyzing codebase for dead code and refactoring opportunities...")
    print()

    # Initialize agent
    redis_client = redis.Redis(host="localhost", port=6379, decode_responses=True)
    agent = IntelligentRefactoringAgent(redis_client)

    # Analyze codebase
    opportunities = agent.analyze_codebase_for_refactoring()

    if not opportunities:
        print("✅ No refactoring opportunities found - codebase is clean!")
        return

    # Show what will be refactored
    print("🎯 REFACTORING OPPORTUNITIES FOUND:")
    print("-" * 40)

    by_type = {}
    for opp in opportunities:
        if opp.opportunity_type not in by_type:
            by_type[opp.opportunity_type] = []
        by_type[opp.opportunity_type].append(opp)

    for opp_type, opps in by_type.items():
        print(f"\n{opp_type.replace('_', ' ').title()}: {len(opps)} opportunities")
        for opp in opps[:5]:  # Show first 5
            print(
                f"   • {Path(opp.file_path).name}:{opp.line_start} - {opp.description}"
            )
            if opp.estimated_savings > 0:
                print(f"     Saves {opp.estimated_savings} lines")

    total_savings = sum(opp.estimated_savings for opp in opportunities)
    print(f"\n💰 Total potential savings: {total_savings} lines of code")

    # Ask for confirmation
    response = input(
        f"\n🤔 Execute refactoring for {len(opportunities)} opportunities? (y/N): "
    )

    if response.lower() != "y":
        print("❌ Refactoring cancelled")
        return

    # Execute refactoring
    print("\n🔧 Executing intelligent refactoring...")
    results = agent.execute_refactoring(opportunities)

    if not results["success"]:
        print("❌ Refactoring failed:")
        for error in results["errors"]:
            print(f"   • {error}")
        return

    if not results["changes_made"]:
        print("ℹ️  No changes were made (safety checks prevented modifications)")
        return

    # Show results
    print("\n✅ REFACTORING COMPLETED:")
    print(f"   📁 Files modified: {len(results['files_modified'])}")
    print(f"   📝 Changes made: {len(results['changes_made'])}")
    print(f"   🗑️  Lines removed: {results['lines_removed']}")

    print("\n📋 Changes made:")
    for change in results["changes_made"]:
        print(f"   • {change}")

    # Commit changes
    print("\n📤 Committing changes to git...")
    commit_success = agent.commit_refactoring_changes(results)

    if commit_success:
        print("🎉 Intelligent refactoring completed and committed!")
    else:
        print(
            "⚠️  Refactoring completed but not committed (no git repo or commit failed)"
        )

    print("\n🚀 Your codebase has been intelligently refactored!")


if __name__ == "__main__":
    intelligent_refactoring_command()
