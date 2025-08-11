#!/usr/bin/env python3
"""
Semantic Code Analyzer - Deep understanding of code structure and intent

This goes beyond syntax to understand what the user is building, the architecture
patterns, dependencies, and development intent. It provides the AI with rich
semantic context for truly intelligent assistance.
"""

import ast
import os
import json
import subprocess
import re
import time
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from pathlib import Path
from collections import defaultdict


@dataclass
class CodeEntity:
    """A code entity (function, class, variable, etc.)"""

    name: str
    entity_type: str  # function, class, variable, import, etc.
    file_path: str
    line_number: int
    signature: Optional[str] = None
    docstring: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    usage_patterns: List[str] = field(default_factory=list)
    complexity_score: float = 0.0
    semantic_tags: List[str] = field(default_factory=list)


@dataclass
class ProjectArchitecture:
    """High-level project architecture understanding"""

    project_type: str  # web_api, cli_tool, library, etc.
    architecture_pattern: str  # mvc, microservices, monolith, etc.
    frameworks: List[str] = field(default_factory=list)
    key_modules: Dict[str, str] = field(default_factory=dict)
    data_flow: List[Tuple[str, str]] = field(default_factory=list)
    external_dependencies: List[str] = field(default_factory=list)
    test_coverage: float = 0.0
    documentation_coverage: float = 0.0


@dataclass
class DevelopmentIntent:
    """Inferred development intent from recent changes"""

    intent_type: str  # feature_development, bug_fix, refactoring, testing
    confidence: float
    evidence: List[str] = field(default_factory=list)
    affected_modules: List[str] = field(default_factory=list)
    suggested_next_steps: List[str] = field(default_factory=list)
    potential_issues: List[str] = field(default_factory=list)


class PythonAnalyzer:
    """Analyze Python code for semantic understanding"""

    def __init__(self):
        self.entities = {}
        self.imports = {}
        self.call_graph = defaultdict(set)

    def analyze_file(self, file_path: str) -> List[CodeEntity]:
        """Analyze a Python file for semantic entities"""
        entities = []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            tree = ast.parse(content)

            for node in ast.walk(tree):
                entity = self._analyze_node(node, file_path, content)
                if entity:
                    entities.append(entity)

            return entities

        except Exception as e:
            print(f"⚠️ Error analyzing {file_path}: {e}")
            return []

    def _analyze_function(
        self, node: ast.FunctionDef, file_path: str, content: str
    ) -> CodeEntity:
        """Analyze function definition"""

        # Extract signature
        args = [arg.arg for arg in node.args.args]
        signature = f"{node.name}({', '.join(args)})"

        # Extract docstring
        docstring = ast.get_docstring(node)

        # Calculate complexity (simplified)
        complexity = self._calculate_function_complexity(node)

        # Semantic tagging
        semantic_tags = self._tag_function(node, content)

        # Extract dependencies (function calls)
        dependencies = self._extract_function_dependencies(node)

        return CodeEntity(
            name=node.name,
            entity_type="function",
            file_path=file_path,
            line_number=node.lineno,
            signature=signature,
            docstring=docstring,
            dependencies=dependencies,
            complexity_score=complexity,
            semantic_tags=semantic_tags,
        )

    def _analyze_class(
        self, node: ast.ClassDef, file_path: str, content: str
    ) -> CodeEntity:
        """Analyze class definition"""

        # Extract inheritance
        bases = [self._get_name(base) for base in node.bases]
        signature = (
            f"class {node.name}({', '.join(bases)})" if bases else f"class {node.name}"
        )

        # Extract docstring
        docstring = ast.get_docstring(node)

        # Semantic tagging for classes
        semantic_tags = self._tag_class(node, content)

        return CodeEntity(
            name=node.name,
            entity_type="class",
            file_path=file_path,
            line_number=node.lineno,
            signature=signature,
            docstring=docstring,
            semantic_tags=semantic_tags,
        )

    def _tag_function(self, node: ast.FunctionDef, content: str) -> List[str]:
        """Tag function with semantic meaning"""
        tags = []

        name = node.name.lower()

        # API/HTTP tags
        if any(http in name for http in ["get", "post", "put", "delete", "patch"]):
            tags.append("http_handler")
        if "api" in name or "endpoint" in name:
            tags.append("api")

        # Database tags
        if any(
            db in name for db in ["save", "create", "update", "delete", "find", "query"]
        ):
            tags.append("database")
        if "model" in name or "schema" in name:
            tags.append("data_model")

        # Utility tags
        if name.startswith("_"):
            tags.append("private")
        if name.startswith("test_"):
            tags.append("test")
        if "validate" in name or "check" in name:
            tags.append("validation")
        if "parse" in name or "format" in name:
            tags.append("data_processing")

        # Authentication/Security
        if any(
            auth in name for auth in ["auth", "login", "token", "verify", "permission"]
        ):
            tags.append("authentication")

        # Error handling
        if any(err in name for err in ["error", "exception", "handle", "catch"]):
            tags.append("error_handling")

        return tags

    def _tag_class(self, node: ast.ClassDef, content: str) -> List[str]:
        """Tag class with semantic meaning"""
        tags = []

        name = node.name.lower()

        # Design patterns
        if name.endswith("factory"):
            tags.append("factory_pattern")
        if name.endswith("builder"):
            tags.append("builder_pattern")
        if name.endswith("manager") or name.endswith("service"):
            tags.append("service_class")
        if name.endswith("model") or name.endswith("entity"):
            tags.append("data_model")
        if name.endswith("controller") or name.endswith("handler"):
            tags.append("controller")
        if name.endswith("view") or name.endswith("template"):
            tags.append("view")
        if name.endswith("config") or name.endswith("settings"):
            tags.append("configuration")
        if name.startswith("test") or name.endswith("test"):
            tags.append("test_class")

        # Framework patterns
        if any(
            base.endswith("Model") for base in [self._get_name(b) for b in node.bases]
        ):
            tags.append("orm_model")
        if any(
            base.endswith("View") for base in [self._get_name(b) for b in node.bases]
        ):
            tags.append("web_view")

        return tags


class ProjectAnalyzer:
    """Analyze entire project for architectural understanding"""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.python_analyzer = PythonAnalyzer()

    def analyze_project(self) -> ProjectArchitecture:
        """Analyze entire project architecture"""

        # Find all Python files
        python_files = list(self.project_root.rglob("*.py"))

        # Analyze each file
        all_entities = []
        for file_path in python_files:
            entities = self.python_analyzer.analyze_file(str(file_path))
            all_entities.extend(entities)

        # Infer project architecture
        architecture = self._infer_architecture(all_entities, python_files)

        return architecture

    def _infer_architecture(
        self, entities: List[CodeEntity], files: List[Path]
    ) -> ProjectArchitecture:
        """Infer project architecture from code entities"""

        # Collect frameworks
        frameworks = self._identify_frameworks(entities)

        # Identify project type
        project_type = self._identify_project_type(entities, frameworks)

        # Identify architecture pattern
        arch_pattern = self._identify_architecture_pattern(entities, files)

        # Find key modules
        key_modules = self._identify_key_modules(entities, files)

        # Get external dependencies
        external_deps = self._get_external_dependencies()

        return ProjectArchitecture(
            project_type=project_type,
            architecture_pattern=arch_pattern,
            frameworks=frameworks,
            key_modules=key_modules,
            external_dependencies=external_deps,
            test_coverage=self._estimate_test_coverage(entities),
            documentation_coverage=self._estimate_doc_coverage(entities),
        )

    def _identify_frameworks(self, entities: List[CodeEntity]) -> List[str]:
        """Identify frameworks used in project"""
        frameworks = set()

        for entity in entities:
            if entity.entity_type == "import":
                for tag in entity.semantic_tags:
                    if tag == "web_framework":
                        if "flask" in entity.name.lower():
                            frameworks.add("Flask")
                        elif "django" in entity.name.lower():
                            frameworks.add("Django")
                        elif "fastapi" in entity.name.lower():
                            frameworks.add("FastAPI")
                    elif tag == "database_orm":
                        if "sqlalchemy" in entity.name.lower():
                            frameworks.add("SQLAlchemy")
                        elif "django.db" in entity.name.lower():
                            frameworks.add("Django ORM")
                    elif tag == "testing_framework":
                        if "pytest" in entity.name.lower():
                            frameworks.add("pytest")

        return list(frameworks)

    def _identify_project_type(
        self, entities: List[CodeEntity], frameworks: List[str]
    ) -> str:
        """Identify what type of project this is"""

        # Count entity types
        api_handlers = sum(1 for e in entities if "http_handler" in e.semantic_tags)
        models = sum(1 for e in entities if "data_model" in e.semantic_tags)
        tests = sum(1 for e in entities if "test" in e.semantic_tags)

        # Check for web frameworks
        if any(fw in frameworks for fw in ["Flask", "Django", "FastAPI"]):
            if api_handlers > 3:
                return "web_api"
            else:
                return "web_application"

        # Check for CLI patterns
        if any("main" in e.name.lower() or "cli" in e.name.lower() for e in entities):
            return "cli_tool"

        # Check for library patterns
        if any("__init__" in e.file_path for e in entities) and models > tests:
            return "library"

        # Default
        return "application"

    def _identify_key_modules(
        self, entities: List[CodeEntity], files: List[Path]
    ) -> Dict[str, str]:
        """Identify key modules and their purposes"""

        modules = {}

        # Group entities by file
        file_entities = defaultdict(list)
        for entity in entities:
            file_entities[entity.file_path].append(entity)

        # Analyze each file
        for file_path, file_entities_list in file_entities.items():
            file_name = Path(file_path).stem

            # Analyze semantic tags to determine module purpose
            all_tags = []
            for entity in file_entities_list:
                all_tags.extend(entity.semantic_tags)

            # Determine module purpose
            if "http_handler" in all_tags or "api" in all_tags:
                modules[file_name] = "API handlers"
            elif "data_model" in all_tags or "orm_model" in all_tags:
                modules[file_name] = "Data models"
            elif "test" in all_tags:
                modules[file_name] = "Tests"
            elif "authentication" in all_tags:
                modules[file_name] = "Authentication"
            elif "database" in all_tags:
                modules[file_name] = "Database operations"
            elif "configuration" in all_tags:
                modules[file_name] = "Configuration"

        return modules


class IntentAnalyzer:
    """Analyze development intent from recent changes"""

    def __init__(self, project_root: str):
        self.project_root = project_root

    def analyze_recent_changes(
        self, architecture: ProjectArchitecture
    ) -> DevelopmentIntent:
        """Analyze recent git changes to infer development intent"""

        try:
            # Get recent commits
            result = subprocess.run(
                ["git", "-C", self.project_root, "log", "--oneline", "-10"],
                capture_output=True,
                text=True,
                timeout=5,
            )

            commits = result.stdout.strip().split("\n") if result.stdout else []

            # Get recent file changes
            result = subprocess.run(
                ["git", "-C", self.project_root, "diff", "--name-only", "HEAD~3..HEAD"],
                capture_output=True,
                text=True,
                timeout=5,
            )

            changed_files = result.stdout.strip().split("\n") if result.stdout else []

            return self._infer_intent(commits, changed_files, architecture)

        except Exception:
            return DevelopmentIntent(
                intent_type="unknown",
                confidence=0.0,
                evidence=["Unable to analyze git history"],
            )

    def _infer_intent(
        self,
        commits: List[str],
        changed_files: List[str],
        architecture: ProjectArchitecture,
    ) -> DevelopmentIntent:
        """Infer development intent from changes"""

        commit_text = " ".join(commits).lower()

        # Feature development
        if any(kw in commit_text for kw in ["add", "implement", "create", "new"]):
            return self._analyze_feature_development(
                commits, changed_files, architecture
            )

        # Bug fixing
        if any(kw in commit_text for kw in ["fix", "bug", "error", "issue"]):
            return self._analyze_bug_fix(commits, changed_files)

        # Refactoring
        if any(
            kw in commit_text for kw in ["refactor", "cleanup", "improve", "optimize"]
        ):
            return self._analyze_refactoring(commits, changed_files)

        # Testing
        if any(kw in commit_text for kw in ["test", "spec"]):
            return self._analyze_testing(commits, changed_files)

        # Default
        return DevelopmentIntent(
            intent_type="maintenance", confidence=0.5, evidence=commits[:3]
        )

    def _analyze_feature_development(
        self,
        commits: List[str],
        changed_files: List[str],
        architecture: ProjectArchitecture,
    ) -> DevelopmentIntent:
        """Analyze feature development intent"""

        evidence = []
        affected_modules = []
        next_steps = []

        # Analyze changed files
        for file_path in changed_files:
            if file_path.endswith(".py"):
                module_name = Path(file_path).stem
                if module_name in architecture.key_modules:
                    affected_modules.append(
                        f"{module_name} ({architecture.key_modules[module_name]})"
                    )

        # Suggest next steps based on architecture
        if architecture.project_type == "web_api":
            if any("model" in f for f in changed_files):
                next_steps.extend(
                    ["Create API endpoints", "Add validation", "Write tests"]
                )
            elif any("api" in f or "handler" in f for f in changed_files):
                next_steps.extend(
                    [
                        "Add error handling",
                        "Write integration tests",
                        "Update documentation",
                    ]
                )

        return DevelopmentIntent(
            intent_type="feature_development",
            confidence=0.8,
            evidence=commits[:2],
            affected_modules=affected_modules,
            suggested_next_steps=next_steps,
            potential_issues=["Consider adding tests", "Update documentation"],
        )


class SemanticCodeAnalyzer:
    """Main semantic code analyzer that coordinates all analysis"""

    def __init__(self):
        self.project_cache = {}
        self.cache_ttl = 300  # 5 minutes

    def analyze_project_context(self, project_root: str) -> Dict[str, Any]:
        """Analyze complete project context"""

        # Check cache
        cache_key = f"project:{project_root}"
        cached = self.project_cache.get(cache_key)

        if cached and time.time() - cached["timestamp"] < self.cache_ttl:
            return cached["data"]

        # Perform analysis
        project_analyzer = ProjectAnalyzer(project_root)
        intent_analyzer = IntentAnalyzer(project_root)

        # Get architecture
        architecture = project_analyzer.analyze_project()

        # Get development intent
        intent = intent_analyzer.analyze_recent_changes(architecture)

        # Build complete context
        context = {
            "architecture": {
                "project_type": architecture.project_type,
                "architecture_pattern": architecture.architecture_pattern,
                "frameworks": architecture.frameworks,
                "key_modules": architecture.key_modules,
                "external_dependencies": architecture.external_dependencies,
                "test_coverage": architecture.test_coverage,
                "documentation_coverage": architecture.documentation_coverage,
            },
            "development_intent": {
                "intent_type": intent.intent_type,
                "confidence": intent.confidence,
                "evidence": intent.evidence,
                "affected_modules": intent.affected_modules,
                "suggested_next_steps": intent.suggested_next_steps,
                "potential_issues": intent.potential_issues,
            },
            "analysis_timestamp": time.time(),
        }

        # Cache result
        self.project_cache[cache_key] = {"timestamp": time.time(), "data": context}

        return context


def demo_semantic_analysis():
    """Demo semantic code analysis"""
    print("🔍 SEMANTIC CODE ANALYSIS DEMO")
    print("=" * 40)

    # Use current project as example
    project_root = os.getcwd()

    analyzer = SemanticCodeAnalyzer()
    context = analyzer.analyze_project_context(project_root)

    print(f"📊 PROJECT ANALYSIS:")
    arch = context["architecture"]
    print(f"   Type: {arch['project_type']}")
    print(f"   Pattern: {arch['architecture_pattern']}")
    print(f"   Frameworks: {', '.join(arch['frameworks']) or 'None detected'}")
    print(f"   Test Coverage: {arch['test_coverage']:.1%}")
    print(f"   Doc Coverage: {arch['documentation_coverage']:.1%}")

    print(f"\n🎯 DEVELOPMENT INTENT:")
    intent = context["development_intent"]
    print(
        f"   Intent: {intent['intent_type']} (confidence: {intent['confidence']:.1%})"
    )
    print(f"   Evidence: {', '.join(intent['evidence'][:2])}")

    if intent["affected_modules"]:
        print(f"   Affected: {', '.join(intent['affected_modules'])}")

    if intent["suggested_next_steps"]:
        print(f"\n💡 SUGGESTED NEXT STEPS:")
        for step in intent["suggested_next_steps"][:3]:
            print(f"      • {step}")

    print(f"\n✨ This provides the AI with:")
    print(f"   • Deep understanding of project architecture")
    print(f"   • Knowledge of frameworks and patterns in use")
    print(f"   • Awareness of current development phase")
    print(f"   • Context-specific suggestions")
    print(f"   • Project health metrics (test/doc coverage)")


if __name__ == "__main__":
    demo_semantic_analysis()
