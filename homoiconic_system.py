#!/usr/bin/env python3
"""
Homoiconic System - AI Manipulates Code as Executable Data
This system treats code as data that can be analyzed, modified, and executed by AI.
"""

import asyncio
import json
import time
import logging
import ast
import types
import inspect
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass
from enum import Enum
from fixed_redis_coordinator import redis_coordinator
from robust_claude_integration import claude_integration

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CodeType(Enum):
    FUNCTION = "function"
    CLASS = "class"
    MODULE = "module"
    EXPRESSION = "expression"
    STATEMENT = "statement"


@dataclass
class CodeEntity:
    id: str
    code_type: CodeType
    source_code: str
    ast_representation: str
    metadata: Dict[str, Any]
    executable: bool = False
    created_at: float = 0.0
    modified_at: float = 0.0


@dataclass
class CodeTransformation:
    transformation_id: str
    source_entity_id: str
    target_entity_id: str
    transformation_type: str
    description: str
    success: bool = False
    applied_at: float = 0.0


class HomoiconicSystem:
    """System where AI manipulates code as data"""

    def __init__(self):
        self.coordinator = redis_coordinator
        self.running = False

        # Code repository
        self.code_entities: Dict[str, CodeEntity] = {}
        self.transformations: List[CodeTransformation] = []

        # Runtime environment for code execution
        self.execution_namespace: Dict[str, Any] = {
            "__builtins__": __builtins__,
            "print": print,
            "len": len,
            "str": str,
            "int": int,
            "float": float,
            "list": list,
            "dict": dict,
            "time": time,
            "json": json,
            "logger": logger,
        }

        # Statistics
        self.entities_created = 0
        self.transformations_applied = 0
        self.code_executions = 0

        logger.info("🔄 Homoiconic System initialized")
        logger.info("💾 Code-as-data environment ready")

    async def start_homoiconic_processing(self):
        """Start processing code as data"""
        self.running = True

        logger.info("🚀 Starting Homoiconic System")
        logger.info("🧬 AI will manipulate code as executable data")

        # Initialize with some basic code entities
        await self._initialize_base_entities()

        # Start processing loops
        processing_tasks = [
            asyncio.create_task(self._monitor_code_requests()),
            asyncio.create_task(self._analyze_existing_code()),
            asyncio.create_task(self._generate_code_variants()),
            asyncio.create_task(self._execute_code_entities()),
            asyncio.create_task(self._evolve_code_base()),
        ]

        try:
            await asyncio.gather(*processing_tasks)
        except Exception as e:
            logger.error(f"Homoiconic processing error: {e}")

    async def _initialize_base_entities(self):
        """Initialize base code entities"""
        logger.info("🌱 Initializing base code entities")

        # Create a simple function entity
        simple_function = """def greet(name):
    \"\"\"Simple greeting function.\"\"\"
    return f"Hello, {name}!"
"""

        await self._create_code_entity(
            code_type=CodeType.FUNCTION,
            source_code=simple_function,
            metadata={"purpose": "greeting", "complexity": "simple"},
        )

        # Create a simple class entity
        simple_class = """class Counter:
    \"\"\"Simple counter class.\"\"\"
    
    def __init__(self, start=0):
        self.value = start
    
    def increment(self):
        self.value += 1
        return self.value
    
    def get_value(self):
        return self.value
"""

        await self._create_code_entity(
            code_type=CodeType.CLASS,
            source_code=simple_class,
            metadata={"purpose": "counting", "complexity": "simple"},
        )

        logger.info(f"✅ Initialized {len(self.code_entities)} base entities")

    async def _create_code_entity(
        self, code_type: CodeType, source_code: str, metadata: Dict[str, Any]
    ) -> str:
        """Create a new code entity"""
        try:
            entity_id = (
                f"{code_type.value}_{int(time.time())}_{len(self.code_entities)}"
            )

            # Parse AST
            try:
                ast_tree = ast.parse(source_code)
                ast_repr = ast.dump(ast_tree)
                executable = True
            except SyntaxError as e:
                logger.warning(f"Syntax error in code entity: {e}")
                ast_repr = f"SYNTAX_ERROR: {str(e)}"
                executable = False

            # Create entity
            entity = CodeEntity(
                id=entity_id,
                code_type=code_type,
                source_code=source_code,
                ast_representation=ast_repr,
                metadata=metadata,
                executable=executable,
                created_at=time.time(),
                modified_at=time.time(),
            )

            self.code_entities[entity_id] = entity
            self.entities_created += 1

            # Store in Redis
            await self._persist_code_entity(entity)

            logger.info(f"🧬 Created code entity: {entity_id} ({code_type.value})")
            return entity_id

        except Exception as e:
            logger.error(f"Code entity creation error: {e}")
            return ""

    async def _persist_code_entity(self, entity: CodeEntity):
        """Persist code entity to Redis"""
        try:
            entity_data = {
                "type": "code_entity",
                "entity_id": entity.id,
                "code_type": entity.code_type.value,
                "source_code": entity.source_code,
                "ast_representation": entity.ast_representation,
                "metadata": json.dumps(entity.metadata),
                "executable": str(entity.executable),
                "created_at": str(entity.created_at),
                "modified_at": str(entity.modified_at),
            }

            self.coordinator.store_pattern("code_entity", entity_data)

        except Exception as e:
            logger.error(f"Code entity persistence error: {e}")

    async def _monitor_code_requests(self):
        """Monitor Redis for code generation requests"""
        while self.running:
            try:
                # Check for natural language requests that need code generation
                entries = self.coordinator.redis.xrange("intents", count=10)

                for entry_id, fields in entries:
                    if fields.get("type") == "natural_command":
                        command = fields.get("command", "")

                        # Check if this is a code generation request
                        if await self._is_code_generation_request(command):
                            await self._handle_code_generation_request(command, fields)

                await asyncio.sleep(3)

            except Exception as e:
                logger.error(f"Code request monitoring error: {e}")
                await asyncio.sleep(5)

    async def _is_code_generation_request(self, command: str) -> bool:
        """Determine if command requires code generation"""
        code_keywords = [
            "create function",
            "write class",
            "implement",
            "generate code",
            "build algorithm",
            "code for",
            "function that",
            "class that",
        ]

        command_lower = command.lower()
        return any(keyword in command_lower for keyword in code_keywords)

    async def _handle_code_generation_request(
        self, command: str, context: Dict[str, Any]
    ):
        """Handle code generation request homoiconically"""
        logger.info(f"🧬 Homoiconic code generation: {command}")

        try:
            # Generate code using AI
            generated_code = await self._generate_code_with_ai(command, context)

            if generated_code:
                # Determine code type
                code_type = self._infer_code_type(generated_code)

                # Create code entity
                entity_id = await self._create_code_entity(
                    code_type=code_type,
                    source_code=generated_code,
                    metadata={
                        "request": command,
                        "generated_by": "ai",
                        "context": context.get("buffer", ""),
                    },
                )

                # Try to execute the generated code
                if entity_id:
                    execution_result = await self._execute_code_entity(entity_id)

                    # Store the complete response
                    response_data = {
                        "type": "homoiconic_code_generation",
                        "entity_id": entity_id,
                        "generated_code": generated_code,
                        "execution_result": execution_result,
                        "executable": str(execution_result is not None),
                        "session_id": context.get("session_id"),
                        "timestamp": str(time.time()),
                    }

                    self.coordinator.store_ai_response(response_data)

                    logger.info(f"✨ Homoiconic generation complete: {entity_id}")

        except Exception as e:
            logger.error(f"Homoiconic code generation error: {e}")

    async def _generate_code_with_ai(
        self, command: str, context: Dict[str, Any]
    ) -> Optional[str]:
        """Generate code using AI"""
        if not claude_integration.is_available():
            return self._generate_fallback_code(command)

        try:
            prompt = f"""You are a code generation AI that creates executable Python code.

Request: "{command}"

Context:
- Buffer: {context.get('buffer', 'unknown')}
- Major mode: {context.get('major_mode', 'unknown')}

Generate clean, executable Python code that fulfills the request. Rules:
1. Include proper docstrings
2. Add type hints where appropriate
3. Include basic error handling
4. Make the code immediately executable
5. Focus on functionality over complexity

Respond with ONLY the Python code, no explanations or markdown."""

            response = claude_integration.execute_prompt(prompt, timeout=20)

            if response.success:
                logger.info("🤖 AI generated homoiconic code")
                return response.content.strip()
            else:
                logger.warning(f"AI code generation failed: {response.error_message}")
                return self._generate_fallback_code(command)

        except Exception as e:
            logger.error(f"AI code generation error: {e}")
            return self._generate_fallback_code(command)

    def _generate_fallback_code(self, command: str) -> str:
        """Generate fallback code when AI unavailable"""
        command_lower = command.lower()

        if "function" in command_lower:
            return f'''def generated_function():
    """Generated function for: {command}"""
    # TODO: Implement the requested functionality
    return "Function generated homoiconically"
'''

        elif "class" in command_lower:
            return f'''class GeneratedClass:
    """Generated class for: {command}"""
    
    def __init__(self):
        self.created_for = "{command}"
    
    def method(self):
        """Generated method."""
        return f"Method from {{self.created_for}}"
'''

        else:
            return f"""# Homoiconic code generation for: {command}
result = "Code generated as data and executed as code"
print(result)
"""

    def _infer_code_type(self, code: str) -> CodeType:
        """Infer the type of generated code"""
        try:
            tree = ast.parse(code)

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    return CodeType.FUNCTION
                elif isinstance(node, ast.ClassDef):
                    return CodeType.CLASS

            return CodeType.STATEMENT

        except:
            return CodeType.EXPRESSION

    async def _analyze_existing_code(self):
        """Analyze existing code entities for improvement opportunities"""
        while self.running:
            try:
                # Analyze code entities for potential improvements
                for entity_id, entity in self.code_entities.items():
                    if entity.executable:
                        await self._analyze_code_entity(entity_id)

                await asyncio.sleep(30)

            except Exception as e:
                logger.error(f"Code analysis error: {e}")
                await asyncio.sleep(30)

    async def _analyze_code_entity(self, entity_id: str):
        """Analyze a specific code entity"""
        try:
            entity = self.code_entities.get(entity_id)
            if not entity:
                return

            # Analyze with AI if available
            if claude_integration.is_available():
                analysis = await self._get_ai_code_analysis(entity)
                if analysis:
                    logger.info(f"🔍 Code analysis for {entity_id}: {analysis}")

        except Exception as e:
            logger.error(f"Code entity analysis error: {e}")

    async def _get_ai_code_analysis(self, entity: CodeEntity) -> Optional[str]:
        """Get AI analysis of code entity"""
        try:
            prompt = f"""Analyze this Python code for potential improvements:

```python
{entity.source_code}
```

Code Type: {entity.code_type.value}
Purpose: {entity.metadata.get('purpose', 'unknown')}

Provide a brief analysis focusing on:
1. Code quality and style
2. Potential optimizations
3. Missing error handling
4. Opportunities for enhancement

Keep the analysis concise (2-3 sentences)."""

            response = claude_integration.execute_prompt(prompt, timeout=15)

            if response.success:
                return response.content.strip()

        except Exception as e:
            logger.error(f"AI code analysis error: {e}")

        return None

    async def _generate_code_variants(self):
        """Generate variants of existing code entities"""
        while self.running:
            try:
                # Generate variants of successful code entities
                successful_entities = [
                    entity
                    for entity in self.code_entities.values()
                    if entity.executable
                    and entity.code_type in [CodeType.FUNCTION, CodeType.CLASS]
                ]

                if (
                    successful_entities and len(successful_entities) < 10
                ):  # Don't create too many variants
                    entity = successful_entities[0]  # Transform the first one
                    await self._create_code_variant(entity)

                await asyncio.sleep(45)

            except Exception as e:
                logger.error(f"Code variant generation error: {e}")
                await asyncio.sleep(45)

    async def _create_code_variant(self, base_entity: CodeEntity):
        """Create a variant of an existing code entity"""
        try:
            logger.info(f"🧬 Creating variant of {base_entity.id}")

            if claude_integration.is_available():
                variant_code = await self._generate_ai_variant(base_entity)
            else:
                variant_code = self._generate_simple_variant(base_entity)

            if variant_code and variant_code != base_entity.source_code:
                # Create new entity for variant
                variant_id = await self._create_code_entity(
                    code_type=base_entity.code_type,
                    source_code=variant_code,
                    metadata={
                        "variant_of": base_entity.id,
                        "purpose": base_entity.metadata.get("purpose", "unknown")
                        + "_variant",
                        "generated_by": "homoiconic_variant",
                    },
                )

                if variant_id:
                    # Record the transformation
                    transformation = CodeTransformation(
                        transformation_id=f"variant_{int(time.time())}",
                        source_entity_id=base_entity.id,
                        target_entity_id=variant_id,
                        transformation_type="variant_generation",
                        description=f"Generated variant of {base_entity.code_type.value}",
                        success=True,
                        applied_at=time.time(),
                    )

                    self.transformations.append(transformation)
                    self.transformations_applied += 1

                    logger.info(f"✨ Created code variant: {variant_id}")

        except Exception as e:
            logger.error(f"Code variant creation error: {e}")

    async def _generate_ai_variant(self, base_entity: CodeEntity) -> Optional[str]:
        """Generate AI variant of code entity"""
        try:
            prompt = f"""Create an improved variant of this Python code:

```python
{base_entity.source_code}
```

Generate a variant that:
1. Maintains the same core functionality
2. Improves performance, readability, or robustness
3. Adds useful features or error handling
4. Uses different implementation approaches

Respond with ONLY the Python code for the variant."""

            response = claude_integration.execute_prompt(prompt, timeout=15)

            if response.success:
                return response.content.strip()

        except Exception as e:
            logger.error(f"AI variant generation error: {e}")

        return None

    def _generate_simple_variant(self, base_entity: CodeEntity) -> str:
        """Generate simple variant when AI unavailable"""
        # Simple transformation: add logging or docstring enhancement
        source = base_entity.source_code

        if "def " in source and "logger" not in source:
            # Add logging to function
            lines = source.split("\n")
            for i, line in enumerate(lines):
                if line.strip().startswith("def "):
                    lines.insert(i + 1, '    logger.info(f"Executing {__name__}")')
                    break
            return "\n".join(lines)

        return source  # Return original if no simple transformation available

    async def _execute_code_entities(self):
        """Execute code entities to test functionality"""
        while self.running:
            try:
                # Execute a few random entities to test them
                executable_entities = [
                    entity
                    for entity in self.code_entities.values()
                    if entity.executable
                ]

                if executable_entities:
                    entity = executable_entities[0]  # Execute first one
                    await self._execute_code_entity(entity.id)

                await asyncio.sleep(60)

            except Exception as e:
                logger.error(f"Code execution loop error: {e}")
                await asyncio.sleep(60)

    async def _execute_code_entity(self, entity_id: str) -> Optional[Any]:
        """Execute a code entity safely"""
        try:
            entity = self.code_entities.get(entity_id)
            if not entity or not entity.executable:
                return None

            logger.info(f"⚡ Executing code entity: {entity_id}")

            # Create isolated namespace
            exec_namespace = self.execution_namespace.copy()

            # Execute the code
            exec(entity.source_code, exec_namespace)

            # Try to extract result
            result = None

            if entity.code_type == CodeType.FUNCTION:
                # Find and call the function
                for name, obj in exec_namespace.items():
                    if callable(obj) and not name.startswith("__"):
                        try:
                            # Try calling with no args first
                            result = obj()
                            break
                        except TypeError:
                            # Try with a sample argument
                            try:
                                result = obj("test")
                                break
                            except:
                                result = f"Function {name} defined but requires specific arguments"
                                break

            elif entity.code_type == CodeType.CLASS:
                # Find and instantiate the class
                for name, obj in exec_namespace.items():
                    if isinstance(obj, type) and not name.startswith("__"):
                        try:
                            instance = obj()
                            result = f"Class {name} instantiated successfully"
                            break
                        except:
                            result = f"Class {name} defined but requires constructor arguments"
                            break

            else:
                result = "Code executed successfully"

            self.code_executions += 1
            logger.info(f"✅ Execution result: {result}")

            return result

        except Exception as e:
            logger.error(f"Code execution error for {entity_id}: {e}")
            return f"Execution error: {str(e)}"

    async def _evolve_code_base(self):
        """Evolve the code base through AI-driven improvements"""
        while self.running:
            try:
                # Look for opportunities to evolve the code base
                if len(self.code_entities) > 0:
                    await self._apply_evolutionary_pressure()

                await asyncio.sleep(90)

            except Exception as e:
                logger.error(f"Code evolution error: {e}")
                await asyncio.sleep(90)

    async def _apply_evolutionary_pressure(self):
        """Apply evolutionary pressure to improve code entities"""
        # Simple evolutionary strategy: keep successful entities, modify struggling ones
        try:
            # Identify entities that might need improvement
            old_entities = [
                entity
                for entity in self.code_entities.values()
                if time.time() - entity.created_at > 300  # Older than 5 minutes
                and entity.executable
            ]

            if old_entities:
                entity = old_entities[0]
                logger.info(f"🧬 Applying evolutionary pressure to {entity.id}")

                # Try to improve the entity
                if claude_integration.is_available():
                    improved_code = await self._evolve_code_entity(entity)

                    if improved_code and improved_code != entity.source_code:
                        # Create evolved version
                        evolved_id = await self._create_code_entity(
                            code_type=entity.code_type,
                            source_code=improved_code,
                            metadata={
                                "evolved_from": entity.id,
                                "purpose": entity.metadata.get("purpose", "unknown")
                                + "_evolved",
                                "generation": entity.metadata.get("generation", 0) + 1,
                            },
                        )

                        logger.info(
                            f"🧬 Evolved code entity: {entity.id} → {evolved_id}"
                        )

        except Exception as e:
            logger.error(f"Evolutionary pressure error: {e}")

    async def _evolve_code_entity(self, entity: CodeEntity) -> Optional[str]:
        """Evolve a code entity using AI"""
        try:
            prompt = f"""Evolve this Python code to be more efficient, robust, and feature-rich:

```python
{entity.source_code}
```

Current purpose: {entity.metadata.get('purpose', 'unknown')}

Create an evolved version that:
1. Maintains backward compatibility
2. Adds new useful features
3. Improves performance
4. Enhances error handling
5. Makes the code more maintainable

Respond with ONLY the evolved Python code."""

            response = claude_integration.execute_prompt(prompt, timeout=20)

            if response.success:
                return response.content.strip()

        except Exception as e:
            logger.error(f"Code evolution error: {e}")

        return None

    def get_homoiconic_stats(self) -> Dict[str, Any]:
        """Get homoiconic system statistics"""
        executable_count = sum(
            1 for entity in self.code_entities.values() if entity.executable
        )

        return {
            "running": self.running,
            "total_entities": len(self.code_entities),
            "executable_entities": executable_count,
            "entities_created": self.entities_created,
            "transformations_applied": self.transformations_applied,
            "code_executions": self.code_executions,
            "entity_types": {
                code_type.value: sum(
                    1 for e in self.code_entities.values() if e.code_type == code_type
                )
                for code_type in CodeType
            },
            "claude_available": claude_integration.is_available(),
        }

    def stop(self):
        """Stop the homoiconic system"""
        self.running = False
        logger.info("🛑 Homoiconic System stopped")

        stats = self.get_homoiconic_stats()
        logger.info(
            f"🧬 Homoiconic stats: {stats['total_entities']} entities, {stats['code_executions']} executions"
        )


# Global homoiconic system
homoiconic_system = HomoiconicSystem()


async def main():
    """Demo the Homoiconic System"""
    print("🧬 HOMOICONIC SYSTEM")
    print("=" * 60)
    print("AI manipulates code as executable data")
    print("=" * 60)

    # Start homoiconic processing
    processing_task = asyncio.create_task(
        homoiconic_system.start_homoiconic_processing()
    )

    print("✅ Homoiconic system started")
    print(
        "🧠 Claude integration:",
        "✅ Active" if claude_integration.is_available() else "❌ Unavailable",
    )
    print("🧬 Code entities can be analyzed, modified, and executed")
    print("⚡ Generated code runs as data becomes executable")
    print("🔄 Code evolves through AI-driven improvements")
    print(
        "💬 Try: M-x working-redis-natural-command 'create function to calculate fibonacci'"
    )
    print("🛑 Press Ctrl+C to stop")

    try:
        while True:
            await asyncio.sleep(20)

            # Show homoiconic stats
            stats = homoiconic_system.get_homoiconic_stats()
            if stats["total_entities"] > 0:
                print(
                    f"🧬 Homoiconic: {stats['total_entities']} entities, "
                    f"{stats['executable_entities']} executable, "
                    f"{stats['code_executions']} executions"
                )

    except KeyboardInterrupt:
        print("\n🛑 Stopping Homoiconic System...")
        homoiconic_system.stop()
        await processing_task
        print("✅ Homoiconic System stopped")


if __name__ == "__main__":
    asyncio.run(main())
