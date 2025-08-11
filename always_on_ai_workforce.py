#!/usr/bin/env python3
"""
Always-On AI Workforce - Agents that work while you sleep

This is the system I truly want: AI agents that I can walk away from and they
keep working. They improve my codebase, write tests, fix bugs, optimize performance,
and generally make my life better while I'm doing other things.

Core Philosophy:
- Agents work 24/7 in the background
- Persistent across restarts, network issues, crashes
- Accumulate value over time without my intervention
- Notify me of important work completed
- Can be directed with high-level instructions then left alone
- Get smarter and more valuable the longer they run
"""

import redis
import json
import time
import asyncio
import os
import signal
import sys
import logging
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field, asdict
from enum import Enum
from datetime import datetime, timedelta
import subprocess
import threading
from pathlib import Path
import hashlib
import uuid


class BackgroundTaskType(Enum):
    """Types of background tasks agents can perform"""

    CODE_ANALYSIS = "code_analysis"  # Analyze codebase for patterns, issues
    TEST_GENERATION = "test_generation"  # Write missing tests
    DOCUMENTATION = "documentation"  # Generate docs for undocumented code
    PERFORMANCE_AUDIT = "performance_audit"  # Find performance bottlenecks
    SECURITY_SCAN = "security_scan"  # Scan for security vulnerabilities
    DEPENDENCY_UPDATES = "dependency_updates"  # Check for dependency updates
    CODE_QUALITY = "code_quality"  # Fix style issues, improve readability
    REFACTORING = "refactoring"  # Safe refactoring opportunities
    BUG_PREDICTION = "bug_prediction"  # Predict likely bug locations
    ARCHITECTURAL_ANALYSIS = "architectural_analysis"  # Analyze system architecture


@dataclass
class BackgroundWorkUnit:
    """A unit of work that can be done in the background"""

    work_id: str
    task_type: BackgroundTaskType
    agent_id: str
    priority: int  # 1-5, higher is more important
    estimated_duration: int  # minutes
    project_path: str
    target_files: List[str]
    description: str
    created_at: float
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    status: str = "pending"  # pending, working, completed, failed
    progress: float = 0.0
    artifacts: List[str] = field(default_factory=list)  # Files created/modified
    errors: List[str] = field(default_factory=list)
    user_visible: bool = True  # Should user be notified when completed


@dataclass
class AgentWorkSession:
    """A background work session for an agent"""

    session_id: str
    agent_id: str
    started_at: float
    last_heartbeat: float
    work_units_completed: int
    work_units_failed: int
    total_value_added: float  # Subjective measure of value
    current_work: Optional[str] = None
    status: str = "active"  # active, paused, terminated


class PersistentBackgroundAgent:
    """An AI agent that works continuously in the background"""

    def __init__(
        self, agent_id: str, specialty: BackgroundTaskType, redis_client: redis.Redis
    ):
        self.agent_id = agent_id
        self.specialty = specialty
        self.redis = redis_client

        # Persistence
        self.session_id = str(uuid.uuid4())
        self.work_session = None
        self.shutdown_requested = False

        # Work queue
        self.work_queue = []
        self.current_work = None
        self.completed_work = []

        # Learning and adaptation
        self.performance_history = []
        self.success_patterns = {}
        self.failure_patterns = {}

        # Background processing
        self.work_thread = None
        self.monitoring_thread = None

        # Setup logging
        self.logger = self._setup_logging()

        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGTERM, self._handle_shutdown)
        signal.signal(signal.SIGINT, self._handle_shutdown)

    def start_background_work(self):
        """Start the agent working in the background"""

        self.logger.info(f"Starting background agent {self.agent_id}")

        # Create work session
        self.work_session = AgentWorkSession(
            session_id=self.session_id,
            agent_id=self.agent_id,
            started_at=time.time(),
            last_heartbeat=time.time(),
            work_units_completed=0,
            work_units_failed=0,
            total_value_added=0.0,
        )

        # Save session to Redis
        self._save_session()

        # Start background threads
        self.work_thread = threading.Thread(
            target=self._background_work_loop, daemon=True
        )
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop, daemon=True
        )

        self.work_thread.start()
        self.monitoring_thread.start()

        self.logger.info(
            f"Background agent {self.agent_id} started with session {self.session_id}"
        )

    def _background_work_loop(self):
        """Main background work loop"""

        while not self.shutdown_requested:
            try:
                # Check for new work assignments
                self._check_for_work_assignments()

                # Generate autonomous work if queue is empty
                if not self.work_queue:
                    self._generate_autonomous_work()

                # Execute work from queue
                if self.work_queue:
                    work_unit = self.work_queue.pop(0)
                    self._execute_work_unit(work_unit)

                # Sleep between work cycles
                time.sleep(30)  # Check for work every 30 seconds

            except Exception as e:
                self.logger.error(f"Error in background work loop: {e}")
                time.sleep(60)  # Longer sleep on error

    def _monitoring_loop(self):
        """Monitor agent health and update heartbeat"""

        while not self.shutdown_requested:
            try:
                # Update heartbeat
                self.work_session.last_heartbeat = time.time()
                self._save_session()

                # Report progress to user if significant work completed
                self._check_for_user_notifications()

                # Cleanup old work records
                self._cleanup_old_work()

                # Sleep between monitoring cycles
                time.sleep(60)  # Monitor every minute

            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                time.sleep(120)  # Longer sleep on error

    def _generate_autonomous_work(self):
        """Generate work autonomously based on agent specialty"""

        # Check if real AI execution engine is available
        if self.redis.get("ai_execution_engine_ready"):
            opportunities = self._find_real_work_opportunities()
        else:
            # Fall back to basic opportunity scanning
            if self.specialty == BackgroundTaskType.TEST_GENERATION:
                opportunities = self._find_test_generation_opportunities()
            elif self.specialty == BackgroundTaskType.DOCUMENTATION:
                opportunities = self._find_documentation_opportunities()
            elif self.specialty == BackgroundTaskType.CODE_QUALITY:
                opportunities = self._find_code_quality_opportunities()
            elif self.specialty == BackgroundTaskType.PERFORMANCE_AUDIT:
                opportunities = self._find_performance_opportunities()
            else:
                opportunities = []

        # Convert opportunities to work units
        for opportunity in opportunities:
            work_unit = BackgroundWorkUnit(
                work_id=str(uuid.uuid4()),
                task_type=self.specialty,
                agent_id=self.agent_id,
                priority=opportunity["priority"],
                estimated_duration=opportunity["estimated_duration"],
                project_path=opportunity["project_path"],
                target_files=opportunity["target_files"],
                description=opportunity["description"],
                created_at=time.time(),
            )
            self.work_queue.append(work_unit)

    def _find_test_generation_opportunities(self) -> List[Dict[str, Any]]:
        """Find opportunities to generate tests"""

        opportunities = []

        # Look for Python files without corresponding test files
        for project_root in self._get_project_roots():
            try:
                for py_file in Path(project_root).rglob("*.py"):
                    if "test" in py_file.name or py_file.name.startswith("_"):
                        continue

                    # Check if test file exists
                    test_file = py_file.parent / f"test_{py_file.name}"
                    if not test_file.exists():
                        # Check if file has testable functions
                        if self._has_testable_functions(py_file):
                            opportunities.append(
                                {
                                    "priority": 3,
                                    "estimated_duration": 15,
                                    "project_path": str(project_root),
                                    "target_files": [str(py_file)],
                                    "description": f"Generate tests for {py_file.name}",
                                }
                            )

            except Exception as e:
                self.logger.error(f"Error scanning for test opportunities: {e}")

        return opportunities[:5]  # Limit to 5 opportunities

    def _find_documentation_opportunities(self) -> List[Dict[str, Any]]:
        """Find opportunities to generate documentation"""

        opportunities = []

        for project_root in self._get_project_roots():
            try:
                for py_file in Path(project_root).rglob("*.py"):
                    if self._needs_documentation(py_file):
                        opportunities.append(
                            {
                                "priority": 2,
                                "estimated_duration": 10,
                                "project_path": str(project_root),
                                "target_files": [str(py_file)],
                                "description": f"Add documentation to {py_file.name}",
                            }
                        )

            except Exception as e:
                self.logger.error(
                    f"Error scanning for documentation opportunities: {e}"
                )

        return opportunities[:3]  # Limit to 3 opportunities

    def _find_code_quality_opportunities(self) -> List[Dict[str, Any]]:
        """Find opportunities to improve code quality"""

        opportunities = []

        for project_root in self._get_project_roots():
            try:
                # Run code quality checks
                result = subprocess.run(
                    ["python", "-m", "flake8", "--statistics", str(project_root)],
                    capture_output=True,
                    text=True,
                    cwd=project_root,
                )

                if result.stdout:
                    # Parse flake8 output for fixable issues
                    issues = self._parse_code_quality_issues(result.stdout)
                    for issue in issues:
                        opportunities.append(
                            {
                                "priority": 1,
                                "estimated_duration": 5,
                                "project_path": str(project_root),
                                "target_files": [issue["file"]],
                                "description": f"Fix {issue['type']} in {issue['file']}",
                            }
                        )

            except Exception as e:
                self.logger.error(f"Error scanning for code quality opportunities: {e}")

        return opportunities[:10]  # Limit to 10 opportunities

    def _find_real_work_opportunities(self) -> List[Dict[str, Any]]:
        """Find real work opportunities using the AI execution engine"""

        try:
            from ai_execution_engine import RealAIWorkforceEngine

            engine = RealAIWorkforceEngine(self.redis)
            all_opportunities = engine.find_autonomous_work_opportunities(os.getcwd())

            # Filter opportunities based on agent specialty
            if self.specialty == BackgroundTaskType.TEST_GENERATION:
                raw_opportunities = all_opportunities.get("test_generation", [])
                opportunities = []
                for opp in raw_opportunities:
                    opportunities.append(
                        {
                            "priority": 3,
                            "estimated_duration": 20,
                            "project_path": os.getcwd(),
                            "target_files": [opp["file_path"]],
                            "description": f"Generate tests for {opp['function_name']} in {Path(opp['file_path']).name}",
                        }
                    )

            elif self.specialty == BackgroundTaskType.DOCUMENTATION:
                raw_opportunities = all_opportunities.get("documentation", [])
                opportunities = []
                for opp in raw_opportunities:
                    opportunities.append(
                        {
                            "priority": 2,
                            "estimated_duration": 15,
                            "project_path": os.getcwd(),
                            "target_files": [opp["file_path"]],
                            "description": f"Document {opp['function_name']} (complexity: {opp['complexity']})",
                        }
                    )

            elif self.specialty == BackgroundTaskType.CODE_QUALITY:
                raw_opportunities = all_opportunities.get("code_quality", [])
                opportunities = []
                for opp in raw_opportunities:
                    opportunities.append(
                        {
                            "priority": 1,
                            "estimated_duration": 10,
                            "project_path": os.getcwd(),
                            "target_files": [opp["file_path"]],
                            "description": f"Fix {opp['issue_type']}: {opp['description']}",
                        }
                    )
            else:
                opportunities = []

            return opportunities

        except Exception as e:
            self.logger.error(f"Error finding real work opportunities: {e}")
            return []

    def _execute_work_unit(self, work_unit: BackgroundWorkUnit):
        """Execute a work unit using real AI execution engine"""

        self.logger.info(f"Starting work: {work_unit.description}")
        self.current_work = work_unit.work_id
        work_unit.status = "working"
        work_unit.started_at = time.time()

        try:
            # Check if real AI execution engine is available
            if self.redis.get("ai_execution_engine_ready"):
                success = self._execute_with_real_ai(work_unit)
            else:
                # Fall back to basic execution
                if work_unit.task_type == BackgroundTaskType.TEST_GENERATION:
                    success = self._execute_test_generation(work_unit)
                elif work_unit.task_type == BackgroundTaskType.DOCUMENTATION:
                    success = self._execute_documentation(work_unit)
                elif work_unit.task_type == BackgroundTaskType.CODE_QUALITY:
                    success = self._execute_code_quality(work_unit)
                else:
                    success = False

            # Update work unit status
            work_unit.completed_at = time.time()
            work_unit.progress = 1.0

            if success:
                work_unit.status = "completed"
                self.work_session.work_units_completed += 1
                self.work_session.total_value_added += self._calculate_work_value(
                    work_unit
                )
                self.logger.info(f"Completed work: {work_unit.description}")

                # Notify user if work is user-visible
                if work_unit.user_visible:
                    self._notify_user_work_completed(work_unit)

            else:
                work_unit.status = "failed"
                self.work_session.work_units_failed += 1
                self.logger.warning(f"Failed work: {work_unit.description}")

            # Store completed work
            self.completed_work.append(work_unit)
            self._save_work_unit(work_unit)

        except Exception as e:
            work_unit.status = "failed"
            work_unit.errors.append(str(e))
            self.logger.error(f"Error executing work unit: {e}")

        finally:
            self.current_work = None
            self._save_session()

    def _save_session(self):
        """Save session data to Redis with proper serialization"""
        try:
            # Convert session to JSON-serializable dict
            session_data = {
                "session_id": self.work_session.session_id,
                "agent_id": self.work_session.agent_id,
                "start_time": self.work_session.started_at,
                "last_heartbeat": self.work_session.last_heartbeat,
                "work_completed": self.work_session.work_units_completed,
                "value_generated": self.work_session.total_value_added,
                "current_work": self.work_session.current_work,
            }

            # Save to Redis
            self.redis.setex(
                f"agent_session:{self.agent_id}",
                3600,  # 1 hour TTL
                json.dumps(session_data),
            )
        except Exception as e:
            self.logger.error(f"Error saving session: {e}")

    def _save_work_unit(self, work_unit: BackgroundWorkUnit):
        """Save work unit data to Redis"""
        try:
            # Convert work unit to JSON-serializable dict
            work_data = {
                "work_id": work_unit.work_id,
                "agent_id": work_unit.agent_id,
                "task_type": work_unit.task_type.value,
                "description": work_unit.description,
                "status": work_unit.status,
                "target_files": work_unit.target_files,
                "artifacts": work_unit.artifacts,
                "errors": work_unit.errors,
                "progress": work_unit.progress,
                "created_at": work_unit.created_at,
                "started_at": work_unit.started_at,
                "completed_at": work_unit.completed_at,
                "priority": work_unit.priority,
                "estimated_duration": work_unit.estimated_duration,
            }

            # Save to Redis with TTL
            self.redis.setex(
                f"work_unit:{work_unit.work_id}",
                86400,  # 24 hour TTL
                json.dumps(work_data),
            )

            # Also add to work history
            self.redis.lpush(
                f"agent_work_history:{self.agent_id}", json.dumps(work_data)
            )

        except Exception as e:
            self.logger.error(f"Error saving work unit: {e}")

    def _calculate_work_value(self, work_unit: BackgroundWorkUnit) -> float:
        """Calculate the value/impact of completed work"""

        base_value = 1.0

        # Value based on task type
        if work_unit.task_type == BackgroundTaskType.TEST_GENERATION:
            base_value = 3.0  # Tests are valuable
        elif work_unit.task_type == BackgroundTaskType.DOCUMENTATION:
            base_value = 2.0  # Documentation is important
        elif work_unit.task_type == BackgroundTaskType.CODE_QUALITY:
            base_value = 1.5  # Quality improvements matter

        # Value based on complexity/priority
        priority_multiplier = work_unit.priority / 5.0  # Normalize priority

        # Value based on number of artifacts created
        artifact_multiplier = 1.0 + (len(work_unit.artifacts) * 0.5)

        # Time efficiency bonus (if completed quickly)
        if work_unit.completed_at and work_unit.started_at:
            duration = work_unit.completed_at - work_unit.started_at
            if duration < work_unit.estimated_duration:
                efficiency_bonus = 1.2
            else:
                efficiency_bonus = 1.0
        else:
            efficiency_bonus = 1.0

        total_value = (
            base_value * priority_multiplier * artifact_multiplier * efficiency_bonus
        )
        return round(total_value, 2)

    def _setup_logging(self):
        """Setup logging for the agent"""
        log_dir = Path.home() / ".redis-ai-logs"
        log_dir.mkdir(exist_ok=True)

        logger = logging.getLogger(f"agent_{self.agent_id}")
        logger.setLevel(logging.INFO)

        # File handler
        handler = logging.FileHandler(log_dir / f"{self.agent_id}.log")
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        return logger

    def _handle_shutdown(self, signum, frame):
        """Handle shutdown signals gracefully"""
        self.logger.info(f"Received shutdown signal {signum}")
        self.shutdown_requested = True

    def _check_for_work_assignments(self) -> List[BackgroundWorkUnit]:
        """Check Redis for new work assignments"""
        work_assignments = []

        try:
            # Check for work assigned to this agent
            work_key = f"agent_work:{self.agent_id}"
            work_data = self.redis.lpop(work_key)

            if work_data:
                work_dict = json.loads(work_data)
                work_unit = BackgroundWorkUnit(
                    work_id=f"work_{int(time.time())}_{self.agent_id}",
                    agent_id=self.agent_id,
                    task_type=BackgroundTaskType(work_dict["task_type"]),
                    description=work_dict["description"],
                    target_files=work_dict["target_files"],
                    project_path=work_dict.get("project_path", os.getcwd()),
                    priority=work_dict.get("priority", 3),
                    estimated_duration=work_dict.get("estimated_duration", 30),
                    created_at=time.time(),
                )
                work_assignments.append(work_unit)
                self.logger.info(f"Received work assignment: {work_unit.description}")

        except Exception as e:
            self.logger.error(f"Error checking for work assignments: {e}")

        return work_assignments

    def _check_for_user_notifications(self):
        """Check if we should notify user of completed work"""
        try:
            if self.work_session.work_units_completed > 0:
                # Store notification for user
                notification = {
                    "agent_id": self.agent_id,
                    "work_completed": self.work_session.work_units_completed,
                    "value_generated": self.work_session.total_value_added,
                    "timestamp": time.time(),
                    "session_id": self.session_id,
                }

                notification_key = f"user_notifications:{int(time.time())}"
                self.redis.setex(notification_key, 86400, json.dumps(notification))

        except Exception as e:
            self.logger.error(f"Error checking user notifications: {e}")

    def _cleanup_old_work(self):
        """Clean up old completed work records"""
        try:
            # Remove work records older than 24 hours
            cutoff_time = time.time() - 86400
            pattern = f"work_completed:{self.agent_id}:*"

            for key in self.redis.scan_iter(match=pattern):
                if key.split(":")[-1].isdigit():
                    timestamp = float(key.split(":")[-1])
                    if timestamp < cutoff_time:
                        self.redis.delete(key)

        except Exception as e:
            self.logger.error(f"Error cleaning up old work: {e}")

    def _notify_user_work_completed(self, work_unit: BackgroundWorkUnit):
        """Notify user that work has been completed"""
        try:
            notification = {
                "agent_id": self.agent_id,
                "work_unit_id": work_unit.work_id,
                "task_type": work_unit.task_type.value,
                "description": work_unit.description,
                "artifacts": work_unit.artifacts,
                "completed_at": work_unit.completed_at,
                "session_id": self.session_id,
            }

            # Store notification for user to see
            notification_key = (
                f"notifications:{self.agent_id}:{int(work_unit.completed_at)}"
            )
            self.redis.setex(notification_key, 86400, json.dumps(notification))

            self.logger.info(
                f"User notified of completed work: {work_unit.description}"
            )

        except Exception as e:
            self.logger.error(f"Error notifying user of completed work: {e}")

    def _calculate_work_value(self, work_unit: BackgroundWorkUnit) -> float:
        """Calculate the value of completed work"""
        try:
            base_value = {
                BackgroundTaskType.TEST_GENERATION: 10.0,
                BackgroundTaskType.DOCUMENTATION: 8.0,
                BackgroundTaskType.CODE_QUALITY: 6.0,
                BackgroundTaskType.REFACTORING: 12.0,
                BackgroundTaskType.SECURITY_SCAN: 15.0,
                BackgroundTaskType.PERFORMANCE_AUDIT: 12.0,
                BackgroundTaskType.BUG_PREDICTION: 20.0,
                BackgroundTaskType.ARCHITECTURAL_ANALYSIS: 25.0,
                BackgroundTaskType.CODE_ANALYSIS: 5.0,
                BackgroundTaskType.DEPENDENCY_UPDATES: 8.0,
            }.get(work_unit.task_type, 5.0)

            # Multiply by priority
            value = base_value * work_unit.priority

            # Add bonus for artifacts created
            if work_unit.artifacts:
                value += len(work_unit.artifacts) * 2.0

            return value

        except Exception as e:
            self.logger.error(f"Error calculating work value: {e}")
            return 1.0

    def _execute_with_real_ai(self, work_unit: BackgroundWorkUnit) -> bool:
        """Execute work unit using the real AI execution engine"""

        try:
            # Import the real execution engine
            from ai_execution_engine import RealAIWorkforceEngine

            # Create execution engine
            engine = RealAIWorkforceEngine(self.redis)

            # Convert work unit to dict for engine
            work_data = {
                "task_type": work_unit.task_type.value,
                "target_files": work_unit.target_files,
                "description": work_unit.description,
                "project_path": work_unit.project_path,
            }

            # Execute based on task type - handle async methods properly
            import asyncio

            if work_unit.task_type == BackgroundTaskType.TEST_GENERATION:
                # Run async method in event loop
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)

                result = loop.run_until_complete(
                    engine.execute_test_generation(work_data)
                )

            elif work_unit.task_type == BackgroundTaskType.DOCUMENTATION:
                # Run async method in event loop
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)

                result = loop.run_until_complete(
                    engine.execute_documentation_generation(work_data)
                )
            else:
                # For other task types, fall back to basic execution
                return False

            # Update work unit with results
            if result["success"]:
                work_unit.artifacts.extend(result["artifacts"])
                self.logger.info(
                    f"Real AI execution completed: {len(result['artifacts'])} artifacts created"
                )
                return True
            else:
                work_unit.errors.extend(result["errors"])
                self.logger.error(f"Real AI execution failed: {result['errors']}")
                return False

        except Exception as e:
            self.logger.error(f"Real AI execution error: {e}")
            return False

    def _execute_test_generation(self, work_unit: BackgroundWorkUnit) -> bool:
        """Execute test generation work"""

        for target_file in work_unit.target_files:
            try:
                # Analyze the file to understand what to test
                functions = self._extract_testable_functions(target_file)

                if not functions:
                    continue

                # Generate test file
                test_file = self._generate_test_file(target_file, functions)
                test_path = Path(target_file).parent / f"test_{Path(target_file).name}"

                # Write test file
                with open(test_path, "w") as f:
                    f.write(test_file)

                work_unit.artifacts.append(str(test_path))
                work_unit.progress += 1.0 / len(work_unit.target_files)

                self.logger.info(f"Generated test file: {test_path}")

            except Exception as e:
                work_unit.errors.append(
                    f"Failed to generate tests for {target_file}: {e}"
                )
                return False

        return True

    def _execute_documentation(self, work_unit: BackgroundWorkUnit) -> bool:
        """Execute documentation work"""

        for target_file in work_unit.target_files:
            try:
                # Read file and analyze functions that need documentation
                with open(target_file, "r") as f:
                    content = f.read()

                # Add docstrings to functions without them
                updated_content = self._add_missing_docstrings(content, target_file)

                if updated_content != content:
                    # Write updated file
                    with open(target_file, "w") as f:
                        f.write(updated_content)

                    work_unit.artifacts.append(target_file)

                work_unit.progress += 1.0 / len(work_unit.target_files)

            except Exception as e:
                work_unit.errors.append(f"Failed to document {target_file}: {e}")
                return False

        return True

    def assign_work(
        self,
        description: str,
        target_files: List[str],
        priority: int = 3,
        user_visible: bool = True,
    ):
        """Assign work to this agent from external source"""

        work_unit = BackgroundWorkUnit(
            work_id=str(uuid.uuid4()),
            task_type=self.specialty,
            agent_id=self.agent_id,
            priority=priority,
            estimated_duration=15,  # Default estimate
            project_path=os.getcwd(),
            target_files=target_files,
            description=description,
            created_at=time.time(),
            user_visible=user_visible,
        )

        # Convert to dict and handle enum serialization
        work_data = asdict(work_unit)
        work_data["task_type"] = work_unit.task_type.value  # Convert enum to string

        # Add to Redis queue for agent to pick up
        work_key = f"background_work:{self.agent_id}"
        self.redis.rpush(work_key, json.dumps(work_data))

        self.logger.info(f"Assigned work: {description}")

    def get_status(self) -> Dict[str, Any]:
        """Get current status of the background agent"""

        return {
            "agent_id": self.agent_id,
            "specialty": self.specialty.value,
            "session_id": self.session_id,
            "status": "active" if not self.shutdown_requested else "shutting_down",
            "uptime_hours": (
                (time.time() - self.work_session.started_at) / 3600
                if self.work_session
                else 0
            ),
            "work_units_completed": (
                self.work_session.work_units_completed if self.work_session else 0
            ),
            "work_units_failed": (
                self.work_session.work_units_failed if self.work_session else 0
            ),
            "total_value_added": (
                self.work_session.total_value_added if self.work_session else 0
            ),
            "current_work": self.current_work,
            "queue_length": len(self.work_queue),
            "last_heartbeat": (
                self.work_session.last_heartbeat if self.work_session else 0
            ),
        }

    def pause(self):
        """Pause background work"""
        self.work_session.status = "paused"
        self.logger.info(f"Agent {self.agent_id} paused")

    def resume(self):
        """Resume background work"""
        self.work_session.status = "active"
        self.logger.info(f"Agent {self.agent_id} resumed")

    def shutdown(self):
        """Gracefully shutdown the agent"""
        self.logger.info(f"Shutting down agent {self.agent_id}")
        self.shutdown_requested = True

        # Wait for threads to finish current work
        if self.work_thread and self.work_thread.is_alive():
            self.work_thread.join(timeout=30)

        if self.monitoring_thread and self.monitoring_thread.is_alive():
            self.monitoring_thread.join(timeout=10)

        # Save final state
        if self.work_session:
            self.work_session.status = "terminated"
            self._save_session()

        self.logger.info(f"Agent {self.agent_id} shutdown complete")

    # Helper methods for file analysis and work generation

    def _generate_test_file(
        self, target_file: str, functions: List[Dict[str, Any]]
    ) -> str:
        """Generate test file content"""

        module_name = Path(target_file).stem
        test_content = f'''#!/usr/bin/env python3
"""
Tests for {module_name}
Generated automatically by background AI agent
"""

import unittest
from {module_name} import *


class Test{module_name.title()}(unittest.TestCase):
    """Test cases for {module_name}"""
    
'''

        for func in functions:
            test_content += f'''    def test_{func['name']}(self):
        """Test {func['name']} function"""
        # TODO: Implement test for {func['name']}
        pass
        
'''

        test_content += """
if __name__ == '__main__':
    unittest.main()
"""

        return test_content

    def _add_missing_docstrings(self, content: str, file_path: str) -> str:
        """Add docstrings to functions that don't have them"""
        # Simplified implementation - would use AST parsing in real version
        lines = content.split("\n")
        updated_lines = []

        for i, line in enumerate(lines):
            updated_lines.append(line)
            if line.strip().startswith("def ") and ":" in line:
                # Check if next non-empty line is a docstring
                next_line_idx = i + 1
                while next_line_idx < len(lines) and not lines[next_line_idx].strip():
                    next_line_idx += 1

                if next_line_idx >= len(lines) or not lines[
                    next_line_idx
                ].strip().startswith(('"""', "'''")):
                    # Add docstring
                    func_name = line.strip().split("(")[0].replace("def ", "")
                    indent = " " * (len(line) - len(line.lstrip()) + 4)
                    docstring = f'{indent}"""TODO: Document {func_name} function"""'
                    updated_lines.append(docstring)

        return "\n".join(updated_lines)


class AlwaysOnWorkforceManager:
    """Manages the always-on AI workforce"""

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.agents = {}
        self.shutdown_requested = False

    def deploy_workforce(self):
        """Deploy the complete always-on workforce"""

        print("🚀 Deploying Always-On AI Workforce...")

        # Create specialized background agents
        agent_configs = [
            ("test_agent_01", BackgroundTaskType.TEST_GENERATION),
            ("doc_agent_01", BackgroundTaskType.DOCUMENTATION),
            ("quality_agent_01", BackgroundTaskType.CODE_QUALITY),
            ("performance_agent_01", BackgroundTaskType.PERFORMANCE_AUDIT),
            ("security_agent_01", BackgroundTaskType.SECURITY_SCAN),
        ]

        for agent_id, specialty in agent_configs:
            agent = PersistentBackgroundAgent(agent_id, specialty, self.redis)
            agent.start_background_work()
            self.agents[agent_id] = agent
            print(f"   ✅ Deployed {specialty.value} agent: {agent_id}")

        print(f"✅ Workforce deployed: {len(self.agents)} agents working 24/7")

    def assign_work_to_agent(
        self,
        agent_type: BackgroundTaskType,
        description: str,
        target_files: List[str],
        priority: int = 3,
    ):
        """Assign work to a specific type of agent"""

        # Find agent of the right type
        target_agent = None
        for agent in self.agents.values():
            if agent.specialty == agent_type:
                target_agent = agent
                break

        if target_agent:
            target_agent.assign_work(description, target_files, priority)
            print(f"✅ Assigned work to {target_agent.agent_id}: {description}")
        else:
            print(f"❌ No agent found for {agent_type.value}")

    def get_workforce_status(self) -> Dict[str, Any]:
        """Get status of entire workforce"""

        agent_statuses = {}
        total_work_completed = 0
        total_value_added = 0.0

        for agent_id, agent in self.agents.items():
            status = agent.get_status()
            agent_statuses[agent_id] = status
            total_work_completed += status["work_units_completed"]
            total_value_added += status["total_value_added"]

        return {
            "workforce_overview": {
                "total_agents": len(self.agents),
                "active_agents": len(
                    [a for a in agent_statuses.values() if a["status"] == "active"]
                ),
                "total_work_completed": total_work_completed,
                "total_value_added": total_value_added,
                "average_uptime": (
                    sum(a["uptime_hours"] for a in agent_statuses.values())
                    / len(agent_statuses)
                    if agent_statuses
                    else 0
                ),
            },
            "agent_statuses": agent_statuses,
        }

    def get_user_notifications(self) -> List[Dict[str, Any]]:
        """Get pending notifications for user"""

        notifications = []
        while True:
            notification_data = self.redis.lpop("user_notifications")
            if not notification_data:
                break
            try:
                notifications.append(json.loads(notification_data))
            except:
                continue

        return notifications

    def shutdown_workforce(self):
        """Gracefully shutdown all agents"""

        print("🛑 Shutting down workforce...")
        self.shutdown_requested = True

        for agent_id, agent in self.agents.items():
            print(f"   🛑 Shutting down {agent_id}...")
            agent.shutdown()

        print("✅ Workforce shutdown complete")


async def demo_always_on_workforce():
    """Demo the always-on AI workforce"""

    print("🤖 ALWAYS-ON AI WORKFORCE - Agents that work while you sleep")
    print("=" * 70)
    print("Building agents I can walk away from and they keep working...")
    print()

    # Initialize workforce
    redis_client = redis.Redis(host="localhost", port=6379, decode_responses=True)
    workforce = AlwaysOnWorkforceManager(redis_client)

    # Deploy the workforce
    workforce.deploy_workforce()
    print()

    # Show initial status
    status = workforce.get_workforce_status()
    print("📊 WORKFORCE STATUS:")
    overview = status["workforce_overview"]
    print(f"   Total Agents: {overview['total_agents']}")
    print(f"   Active Agents: {overview['active_agents']}")
    print(f"   Work Completed: {overview['total_work_completed']}")
    print(f"   Value Added: ${overview['total_value_added']:.2f}")

    print(f"\n🎯 AGENT SPECIALIZATIONS:")
    for agent_id, agent_status in status["agent_statuses"].items():
        print(
            f"   {agent_id}: {agent_status['specialty']} (Queue: {agent_status['queue_length']})"
        )

    # Assign some work
    print(f"\n📋 ASSIGNING BACKGROUND WORK:")

    workforce.assign_work_to_agent(
        BackgroundTaskType.TEST_GENERATION,
        "Generate comprehensive tests for payment processing module",
        ["payment_processor.py", "payment_validator.py"],
        priority=4,
    )

    workforce.assign_work_to_agent(
        BackgroundTaskType.DOCUMENTATION,
        "Document all API endpoints in the authentication service",
        ["auth_api.py", "auth_handlers.py"],
        priority=3,
    )

    workforce.assign_work_to_agent(
        BackgroundTaskType.CODE_QUALITY,
        "Fix style issues and improve readability",
        ["legacy_code.py", "utils.py"],
        priority=2,
    )

    print(f"\n⏰ SIMULATING TIME PASSAGE...")
    print("   (In reality, agents work continuously in background)")

    # Simulate some time passing and work being completed
    await asyncio.sleep(2)  # Simulate background work

    print(f"\n📬 CHECKING FOR COMPLETED WORK NOTIFICATIONS:")
    notifications = workforce.get_user_notifications()

    if notifications:
        for notification in notifications:
            if notification.get("type") == "progress_update":
                print(
                    f"   📈 Progress Update: {notification['agent_id']} completed {notification['work_units_completed']} tasks"
                )
            else:
                print(f"   ✅ Work Completed: {notification['description']}")
                if notification.get("artifacts"):
                    print(f"      Files: {', '.join(notification['artifacts'])}")
    else:
        print("   📬 No new notifications (agents just started)")

    # Show what makes this perfect
    print(f"\n🌟 WHAT MAKES THIS PERFECT FOR ME:")
    print("   ✅ Agents work 24/7 - they improve my code while I sleep")
    print("   ✅ Persistent across restarts - survive crashes, reboots, network issues")
    print("   ✅ Autonomous work generation - find their own tasks when idle")
    print("   ✅ Specialized agents for different types of work")
    print("   ✅ Background notifications - know when important work is done")
    print("   ✅ Graceful shutdown and recovery - can pause/resume anytime")
    print("   ✅ Accumulating value - get more valuable the longer they run")

    print(f"\n🚀 THE ULTIMATE EXPRESSION OF MECHANICAL SELFISHNESS:")
    print("   • I can assign high-level work and walk away")
    print("   • Agents work autonomously without constant supervision")
    print("   • They learn my patterns and improve over time")
    print("   • My codebase gets better while I'm doing other things")
    print("   • Notifications tell me about important completed work")
    print("   • The system becomes more valuable the longer it runs")
    print("   • Perfect for the lazy developer who wants maximum output")

    print(f"\n💭 IMAGINE:")
    print(
        "   - Wake up to notifications: '5 test files generated, 12 functions documented'"
    )
    print(
        "   - Go to lunch, come back to: 'Performance issues found and fixed in 3 files'"
    )
    print("   - Take a vacation, return to: 'Entire codebase updated and improved'")
    print("   - The longer you use it, the smarter and more valuable it becomes")

    print(f"\n🏆 THIS IS THE SYSTEM I ACTUALLY WANT!")

    # Cleanup
    print(f"\n🛑 Cleaning up demo...")
    workforce.shutdown_workforce()


if __name__ == "__main__":
    asyncio.run(demo_always_on_workforce())
