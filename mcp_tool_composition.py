#!/usr/bin/env python3
"""
MCP Tool Composition System - Replace bash command sequences with structured MCP tools
Implements the design principle: "If you CAN mcp it, mcp it"
"""

import json
import asyncio
import subprocess
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from pathlib import Path
import redis
import logging
from abc import ABC, abstractmethod


@dataclass
class ToolCall:
    """Structured representation of an MCP tool call"""

    server: str
    tool: str
    arguments: Dict[str, Any]
    id: str
    description: str


@dataclass
class ToolResult:
    """Result from an MCP tool call"""

    call_id: str
    success: bool
    content: str
    error: Optional[str] = None
    artifacts: List[str] = None


@dataclass
class ToolComposition:
    """A composition of multiple MCP tool calls"""

    name: str
    description: str
    tools: List[ToolCall]
    dependencies: Dict[str, List[str]]  # tool_id -> [dependent_tool_ids]
    parallel_groups: List[List[str]]  # Groups of tools that can run in parallel


class MCPToolExecutor:
    """Execute MCP tool calls and compositions"""

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.logger = logging.getLogger(__name__)

        # Registry of available MCP servers
        self.mcp_servers = {
            "redis-lisp": {
                "command": ["python", "mcp_redis_lisp_server.py"],
                "tools": [
                    "execute_lisp",
                    "execute_stored_lisp",
                    "store_lisp_code",
                    "list_lisp_programs",
                    "redis_lisp_demo",
                ],
            },
            "redis-emacs": {
                "command": ["python", "redis_emacs_mcp_server.py"],
                "tools": [
                    "natural_command",
                    "emacs_eval",
                    "buffer_operations",
                    "file_operations",
                ],
            },
            "workflow-synthesis": {
                "command": ["python", "workflow_synthesis_engine.py"],
                "tools": [
                    "analyze_patterns",
                    "synthesize_workflow",
                    "predict_completion",
                ],
            },
        }

        # Registry of common tool compositions
        self.compositions = {}
        self._setup_default_compositions()

    def _setup_default_compositions(self):
        """Setup default tool compositions that replace common bash sequences"""

        # Replace: git status && git diff && git log --oneline -10
        self.register_composition(
            ToolComposition(
                name="git_status_overview",
                description="Get comprehensive git repository status",
                tools=[
                    ToolCall("system", "git_status", {}, "git_1", "Check git status"),
                    ToolCall("system", "git_diff", {}, "git_2", "Show changes"),
                    ToolCall(
                        "system",
                        "git_log",
                        {"args": ["--oneline", "-10"]},
                        "git_3",
                        "Recent commits",
                    ),
                ],
                dependencies={},
                parallel_groups=[["git_1", "git_2", "git_3"]],  # Can run in parallel
            )
        )

        # Replace: find . -name "*.py" | head -10 && wc -l *.py
        self.register_composition(
            ToolComposition(
                name="python_project_analysis",
                description="Analyze Python project structure and size",
                tools=[
                    ToolCall(
                        "filesystem",
                        "find_files",
                        {"pattern": "*.py", "limit": 10},
                        "find_1",
                        "Find Python files",
                    ),
                    ToolCall(
                        "filesystem",
                        "count_lines",
                        {"pattern": "*.py"},
                        "count_1",
                        "Count lines in Python files",
                    ),
                    ToolCall(
                        "redis-lisp",
                        "execute_lisp",
                        {"code": '["redis-set", "analysis_timestamp", "now"]'},
                        "timestamp_1",
                        "Record analysis time",
                    ),
                ],
                dependencies={
                    "count_1": ["find_1"],  # count_1 depends on find_1
                    "timestamp_1": ["find_1", "count_1"],  # timestamp_1 depends on both
                },
                parallel_groups=[],
            )
        )

        # Replace: ps aux | grep python && top -n 1 | head -20
        self.register_composition(
            ToolComposition(
                name="python_process_monitoring",
                description="Monitor Python processes and system resources",
                tools=[
                    ToolCall(
                        "system",
                        "list_processes",
                        {"filter": "python"},
                        "ps_1",
                        "List Python processes",
                    ),
                    ToolCall(
                        "system",
                        "system_resources",
                        {"limit": 20},
                        "top_1",
                        "System resource usage",
                    ),
                    ToolCall(
                        "redis-lisp",
                        "execute_lisp",
                        {
                            "code": '["redis-lpush", "process_log", "monitoring_complete"]'
                        },
                        "log_1",
                        "Log monitoring event",
                    ),
                ],
                dependencies={"log_1": ["ps_1", "top_1"]},
                parallel_groups=[["ps_1", "top_1"]],
            )
        )

        # Replace: npm test && npm run lint && npm run build
        self.register_composition(
            ToolComposition(
                name="frontend_ci_pipeline",
                description="Run complete frontend CI pipeline",
                tools=[
                    ToolCall("nodejs", "run_tests", {}, "test_1", "Run test suite"),
                    ToolCall("nodejs", "run_lint", {}, "lint_1", "Run linter"),
                    ToolCall("nodejs", "run_build", {}, "build_1", "Build project"),
                ],
                dependencies={
                    "lint_1": ["test_1"],  # lint after tests
                    "build_1": ["test_1", "lint_1"],  # build after both
                },
                parallel_groups=[],
            )
        )

        # Replace: pytest && flake8 && mypy
        self.register_composition(
            ToolComposition(
                name="python_quality_check",
                description="Run comprehensive Python quality checks",
                tools=[
                    ToolCall("python", "run_pytest", {}, "pytest_1", "Run pytest"),
                    ToolCall(
                        "python", "run_flake8", {}, "flake8_1", "Check code style"
                    ),
                    ToolCall("python", "run_mypy", {}, "mypy_1", "Type checking"),
                    ToolCall(
                        "redis-lisp",
                        "execute_lisp",
                        {
                            "code": '["assign-work", "test_agent_01", "Review quality check results", ["."]]'
                        },
                        "ai_review",
                        "AI review of results",
                    ),
                ],
                dependencies={"ai_review": ["pytest_1", "flake8_1", "mypy_1"]},
                parallel_groups=[["pytest_1", "flake8_1", "mypy_1"]],
            )
        )

        # Replace: docker build && docker run && docker logs
        self.register_composition(
            ToolComposition(
                name="docker_development_cycle",
                description="Complete Docker development cycle",
                tools=[
                    ToolCall(
                        "docker",
                        "build_image",
                        {"tag": "dev-build"},
                        "build_1",
                        "Build Docker image",
                    ),
                    ToolCall(
                        "docker",
                        "run_container",
                        {"image": "dev-build", "detach": True},
                        "run_1",
                        "Run container",
                    ),
                    ToolCall(
                        "docker",
                        "get_logs",
                        {"container_ref": "dev-build"},
                        "logs_1",
                        "Get container logs",
                    ),
                    ToolCall(
                        "redis-lisp",
                        "execute_lisp",
                        {"code": '["redis-set", "docker_status", "complete"]'},
                        "status_1",
                        "Update status",
                    ),
                ],
                dependencies={
                    "run_1": ["build_1"],
                    "logs_1": ["run_1"],
                    "status_1": ["logs_1"],
                },
                parallel_groups=[],
            )
        )

    def register_composition(self, composition: ToolComposition):
        """Register a new tool composition"""
        self.compositions[composition.name] = composition
        self.logger.info(f"Registered tool composition: {composition.name}")

    async def execute_composition(
        self, composition_name: str, context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Execute a tool composition"""

        if composition_name not in self.compositions:
            return {
                "success": False,
                "error": f"Unknown composition: {composition_name}",
                "results": [],
            }

        composition = self.compositions[composition_name]
        context = context or {}

        self.logger.info(f"🚀 Executing composition: {composition.name}")

        results = {
            "success": True,
            "composition": composition.name,
            "description": composition.description,
            "results": [],
            "errors": [],
            "artifacts": [],
        }

        try:
            # Execute tools according to dependencies and parallelism
            tool_results = {}
            completed_tools = set()

            # Execute parallel groups first
            for parallel_group in composition.parallel_groups:
                if parallel_group:
                    group_tasks = []
                    for tool_id in parallel_group:
                        tool = self._find_tool_by_id(composition.tools, tool_id)
                        if tool and self._dependencies_satisfied(
                            tool_id, composition.dependencies, completed_tools
                        ):
                            task = self._execute_single_tool(tool, context)
                            group_tasks.append((tool_id, task))

                    # Wait for all parallel tasks to complete
                    if group_tasks:
                        group_results = await asyncio.gather(
                            *[task for _, task in group_tasks], return_exceptions=True
                        )

                        for (tool_id, _), result in zip(group_tasks, group_results):
                            if isinstance(result, Exception):
                                results["errors"].append(
                                    f"Tool {tool_id} failed: {str(result)}"
                                )
                                results["success"] = False
                            else:
                                tool_results[tool_id] = result
                                completed_tools.add(tool_id)
                                results["results"].append(result)
                                if result.artifacts:
                                    results["artifacts"].extend(result.artifacts)

            # Execute remaining tools in dependency order
            remaining_tools = [
                t for t in composition.tools if t.id not in completed_tools
            ]

            while remaining_tools:
                ready_tools = []

                for tool in remaining_tools:
                    if self._dependencies_satisfied(
                        tool.id, composition.dependencies, completed_tools
                    ):
                        ready_tools.append(tool)

                if not ready_tools:
                    # Check for circular dependencies
                    remaining_ids = [t.id for t in remaining_tools]
                    results["errors"].append(
                        f"Circular dependency detected in tools: {remaining_ids}"
                    )
                    results["success"] = False
                    break

                # Execute ready tools
                for tool in ready_tools:
                    try:
                        result = await self._execute_single_tool(tool, context)
                        tool_results[tool.id] = result
                        completed_tools.add(tool.id)
                        results["results"].append(result)

                        if result.artifacts:
                            results["artifacts"].extend(result.artifacts)

                        if not result.success:
                            results["errors"].append(
                                f"Tool {tool.id} failed: {result.error}"
                            )

                    except Exception as e:
                        results["errors"].append(f"Tool {tool.id} exception: {str(e)}")
                        results["success"] = False

                # Remove completed tools
                remaining_tools = [
                    t for t in remaining_tools if t.id not in completed_tools
                ]

            # Log completion to Redis
            completion_log = {
                "composition": composition.name,
                "success": results["success"],
                "tool_count": len(composition.tools),
                "artifact_count": len(results["artifacts"]),
                "error_count": len(results["errors"]),
                "timestamp": asyncio.get_event_loop().time(),
            }

            self.redis.lpush("mcp_composition_log", json.dumps(completion_log))

            if results["success"]:
                self.logger.info(
                    f"✅ Composition {composition.name} completed successfully"
                )
            else:
                self.logger.error(
                    f"❌ Composition {composition.name} failed with {len(results['errors'])} errors"
                )

            return results

        except Exception as e:
            self.logger.error(f"Composition execution error: {e}")
            return {
                "success": False,
                "error": f"Composition execution failed: {str(e)}",
                "results": [],
            }

    def _find_tool_by_id(
        self, tools: List[ToolCall], tool_id: str
    ) -> Optional[ToolCall]:
        """Find a tool by its ID"""
        for tool in tools:
            if tool.id == tool_id:
                return tool
        return None

    def _dependencies_satisfied(
        self, tool_id: str, dependencies: Dict[str, List[str]], completed: set
    ) -> bool:
        """Check if all dependencies for a tool are satisfied"""
        if tool_id not in dependencies:
            return True

        for dep_id in dependencies[tool_id]:
            if dep_id not in completed:
                return False

        return True

    async def _execute_single_tool(
        self, tool: ToolCall, context: Dict[str, Any]
    ) -> ToolResult:
        """Execute a single MCP tool call"""

        try:
            if tool.server == "redis-lisp":
                return await self._execute_redis_lisp_tool(tool, context)
            elif tool.server == "system":
                return await self._execute_system_tool(tool, context)
            elif tool.server == "filesystem":
                return await self._execute_filesystem_tool(tool, context)
            elif tool.server == "python":
                return await self._execute_python_tool(tool, context)
            elif tool.server == "nodejs":
                return await self._execute_nodejs_tool(tool, context)
            elif tool.server == "docker":
                return await self._execute_docker_tool(tool, context)
            else:
                # Try to execute via MCP server
                return await self._execute_mcp_server_tool(tool, context)

        except Exception as e:
            return ToolResult(
                call_id=tool.id,
                success=False,
                content="",
                error=f"Tool execution failed: {str(e)}",
            )

    async def _execute_redis_lisp_tool(
        self, tool: ToolCall, context: Dict[str, Any]
    ) -> ToolResult:
        """Execute a Redis Lisp MCP tool"""

        try:
            # Store the tool call in Redis for the MCP server to process
            mcp_request = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {"name": tool.tool, "arguments": tool.arguments},
                "id": tool.id,
            }

            self.redis.lpush("mcp_requests", json.dumps(mcp_request))

            # Wait for result (simplified - in production would use proper async waiting)
            result_key = f"mcp_result:{tool.id}"

            for _ in range(100):  # 10 second timeout
                result = self.redis.get(result_key)
                if result:
                    self.redis.delete(result_key)
                    response = json.loads(result)

                    return ToolResult(
                        call_id=tool.id,
                        success=True,
                        content=response.get("result", ""),
                        artifacts=response.get("artifacts", []),
                    )

                await asyncio.sleep(0.1)

            return ToolResult(
                call_id=tool.id,
                success=False,
                content="",
                error="Timeout waiting for MCP server response",
            )

        except Exception as e:
            return ToolResult(
                call_id=tool.id,
                success=False,
                content="",
                error=f"Redis Lisp tool error: {str(e)}",
            )

    async def _execute_system_tool(
        self, tool: ToolCall, context: Dict[str, Any]
    ) -> ToolResult:
        """Execute system tools (replacing bash commands)"""

        commands = {
            "git_status": ["git", "status", "--porcelain"],
            "git_diff": ["git", "diff"],
            "git_log": ["git", "log"] + tool.arguments.get("args", []),
            "list_processes": ["ps", "aux"],
            "system_resources": ["top", "-n", "1"],
        }

        command = commands.get(tool.tool, ["echo", f"Unknown tool: {tool.tool}"])

        try:
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=context.get("working_directory", "."),
            )

            stdout, stderr = await process.communicate()

            success = process.returncode == 0
            content = stdout.decode("utf-8") if success else stderr.decode("utf-8")

            # Apply filters
            if tool.tool == "list_processes" and "filter" in tool.arguments:
                filter_term = tool.arguments["filter"]
                lines = content.split("\n")
                filtered_lines = [line for line in lines if filter_term in line]
                content = "\n".join(filtered_lines)

            if "limit" in tool.arguments:
                lines = content.split("\n")
                limit = tool.arguments["limit"]
                content = "\n".join(lines[:limit])

            return ToolResult(
                call_id=tool.id,
                success=success,
                content=content,
                error=None if success else f"Command failed: {stderr.decode('utf-8')}",
            )

        except Exception as e:
            return ToolResult(
                call_id=tool.id,
                success=False,
                content="",
                error=f"System tool error: {str(e)}",
            )

    async def _execute_filesystem_tool(
        self, tool: ToolCall, context: Dict[str, Any]
    ) -> ToolResult:
        """Execute filesystem tools"""

        try:
            if tool.tool == "find_files":
                pattern = tool.arguments.get("pattern", "*")
                limit = tool.arguments.get("limit", 100)

                # Use pathlib for file finding
                cwd = Path(context.get("working_directory", "."))
                files = list(cwd.rglob(pattern))

                if limit:
                    files = files[:limit]

                content = "\n".join(str(f) for f in files)

                return ToolResult(
                    call_id=tool.id,
                    success=True,
                    content=content,
                    artifacts=[str(f) for f in files],
                )

            elif tool.tool == "count_lines":
                pattern = tool.arguments.get("pattern", "*.py")
                cwd = Path(context.get("working_directory", "."))
                files = list(cwd.rglob(pattern))

                total_lines = 0
                file_counts = []

                for file_path in files:
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            lines = len(f.readlines())
                            total_lines += lines
                            file_counts.append(f"{file_path}: {lines}")
                    except:
                        continue

                content = "\n".join(file_counts) + f"\n\nTotal: {total_lines} lines"

                return ToolResult(call_id=tool.id, success=True, content=content)

            else:
                return ToolResult(
                    call_id=tool.id,
                    success=False,
                    content="",
                    error=f"Unknown filesystem tool: {tool.tool}",
                )

        except Exception as e:
            return ToolResult(
                call_id=tool.id,
                success=False,
                content="",
                error=f"Filesystem tool error: {str(e)}",
            )

    async def _execute_python_tool(
        self, tool: ToolCall, context: Dict[str, Any]
    ) -> ToolResult:
        """Execute Python development tools"""

        commands = {
            "run_pytest": ["python", "-m", "pytest", "-v"],
            "run_flake8": ["python", "-m", "flake8", "."],
            "run_mypy": ["python", "-m", "mypy", "."],
        }

        command = commands.get(tool.tool)
        if not command:
            return ToolResult(
                call_id=tool.id,
                success=False,
                content="",
                error=f"Unknown Python tool: {tool.tool}",
            )

        try:
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=context.get("working_directory", "."),
            )

            stdout, stderr = await process.communicate()

            success = process.returncode == 0
            content = stdout.decode("utf-8")
            error_content = stderr.decode("utf-8")

            return ToolResult(
                call_id=tool.id,
                success=success,
                content=content,
                error=error_content if not success else None,
            )

        except Exception as e:
            return ToolResult(
                call_id=tool.id,
                success=False,
                content="",
                error=f"Python tool error: {str(e)}",
            )

    async def _execute_nodejs_tool(
        self, tool: ToolCall, context: Dict[str, Any]
    ) -> ToolResult:
        """Execute Node.js development tools"""

        commands = {
            "run_tests": ["npm", "test"],
            "run_lint": ["npm", "run", "lint"],
            "run_build": ["npm", "run", "build"],
        }

        command = commands.get(tool.tool)
        if not command:
            return ToolResult(
                call_id=tool.id,
                success=False,
                content="",
                error=f"Unknown Node.js tool: {tool.tool}",
            )

        try:
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=context.get("working_directory", "."),
            )

            stdout, stderr = await process.communicate()

            success = process.returncode == 0
            content = stdout.decode("utf-8")
            error_content = stderr.decode("utf-8")

            return ToolResult(
                call_id=tool.id,
                success=success,
                content=content,
                error=error_content if not success else None,
            )

        except Exception as e:
            return ToolResult(
                call_id=tool.id,
                success=False,
                content="",
                error=f"Node.js tool error: {str(e)}",
            )

    async def _execute_docker_tool(
        self, tool: ToolCall, context: Dict[str, Any]
    ) -> ToolResult:
        """Execute Docker tools"""

        try:
            if tool.tool == "build_image":
                tag = tool.arguments.get("tag", "latest")
                command = ["docker", "build", "-t", tag, "."]

            elif tool.tool == "run_container":
                image = tool.arguments.get("image", "latest")
                detach = tool.arguments.get("detach", False)
                command = ["docker", "run"]
                if detach:
                    command.append("-d")
                command.append(image)

            elif tool.tool == "get_logs":
                container = tool.arguments.get("container_ref", "latest")
                command = ["docker", "logs", container]

            else:
                return ToolResult(
                    call_id=tool.id,
                    success=False,
                    content="",
                    error=f"Unknown Docker tool: {tool.tool}",
                )

            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=context.get("working_directory", "."),
            )

            stdout, stderr = await process.communicate()

            success = process.returncode == 0
            content = stdout.decode("utf-8")
            error_content = stderr.decode("utf-8")

            return ToolResult(
                call_id=tool.id,
                success=success,
                content=content,
                error=error_content if not success else None,
            )

        except Exception as e:
            return ToolResult(
                call_id=tool.id,
                success=False,
                content="",
                error=f"Docker tool error: {str(e)}",
            )

    async def _execute_mcp_server_tool(
        self, tool: ToolCall, context: Dict[str, Any]
    ) -> ToolResult:
        """Execute tool via external MCP server"""

        # This would implement the full MCP protocol
        # For now, return a placeholder
        return ToolResult(
            call_id=tool.id,
            success=False,
            content="",
            error=f"External MCP server execution not implemented for {tool.server}",
        )

    def list_compositions(self) -> List[Dict[str, Any]]:
        """List all available tool compositions"""

        compositions = []
        for name, comp in self.compositions.items():
            compositions.append(
                {
                    "name": name,
                    "description": comp.description,
                    "tool_count": len(comp.tools),
                    "has_parallel": len(comp.parallel_groups) > 0,
                    "has_dependencies": len(comp.dependencies) > 0,
                }
            )

        return compositions

    def get_composition_details(self, name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a composition"""

        if name not in self.compositions:
            return None

        comp = self.compositions[name]
        return {
            "name": comp.name,
            "description": comp.description,
            "tools": [asdict(tool) for tool in comp.tools],
            "dependencies": comp.dependencies,
            "parallel_groups": comp.parallel_groups,
        }


# CLI interface for testing and demonstration
async def main():
    """Demonstrate the MCP tool composition system"""

    print("🔧 MCP Tool Composition System Demo")
    print("=" * 50)

    # Setup Redis connection
    redis_client = redis.Redis(host="localhost", port=6379, decode_responses=True)

    # Create executor
    executor = MCPToolExecutor(redis_client)

    # List available compositions
    compositions = executor.list_compositions()
    print(f"\n📋 Available Compositions ({len(compositions)}):")
    for comp in compositions:
        print(f"  • {comp['name']}: {comp['description']}")
        print(
            f"    Tools: {comp['tool_count']}, Parallel: {comp['has_parallel']}, Dependencies: {comp['has_dependencies']}"
        )

    # Demonstrate a composition
    print(f"\n🚀 Executing 'python_project_analysis' composition...")

    context = {"working_directory": ".", "project_name": "redis-ai-challenge"}

    result = await executor.execute_composition("python_project_analysis", context)

    print(f"\n📊 Composition Results:")
    print(f"  Success: {result['success']}")
    print(f"  Tool Results: {len(result['results'])}")
    print(f"  Artifacts: {len(result['artifacts'])}")
    print(f"  Errors: {len(result['errors'])}")

    if result["errors"]:
        print(f"\n⚠️ Errors:")
        for error in result["errors"]:
            print(f"    • {error}")

    if result["artifacts"]:
        print(f"\n📄 Artifacts:")
        for artifact in result["artifacts"][:5]:  # Show first 5
            print(f"    • {artifact}")

    print(f"\n✅ MCP Tool Composition System demonstrated!")
    print(
        f"   This replaces bash command sequences with structured, composable MCP tools"
    )
    print(
        f"   Benefits: Better error handling, parallelism, dependency management, and integration"
    )


if __name__ == "__main__":
    asyncio.run(main())
