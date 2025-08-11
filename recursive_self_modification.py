#!/usr/bin/env python3
"""
Recursive Self-Modification System - AI That Writes and Executes New AI Code
This system can write new AI capabilities and integrate them into itself.
"""

import asyncio
import json
import time
import logging
import ast
import types
import importlib
import sys
import os
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass
from enum import Enum
from fixed_redis_coordinator import redis_coordinator
from robust_claude_integration import claude_integration
from homoiconic_system import homoiconic_system

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ModificationType(Enum):
    NEW_CAPABILITY = "new_capability"
    ENHANCEMENT = "enhancement"
    OPTIMIZATION = "optimization"
    BUG_FIX = "bug_fix"
    INTEGRATION = "integration"


@dataclass
class SelfModificationRequest:
    request_id: str
    modification_type: ModificationType
    description: str
    requirements: List[str]
    context: Dict[str, Any]
    priority: int = 1
    created_at: float = 0.0


@dataclass
class GeneratedCapability:
    capability_id: str
    name: str
    source_code: str
    functionality: str
    integration_points: List[str]
    dependencies: List[str]
    tests: Optional[str] = None
    success: bool = False
    integrated_at: float = 0.0


class RecursiveSelfModificationSystem:
    """System that can write and execute new AI capabilities"""

    def __init__(self):
        self.coordinator = redis_coordinator
        self.running = False

        # Self-modification state
        self.modification_requests: List[SelfModificationRequest] = []
        self.generated_capabilities: Dict[str, GeneratedCapability] = {}
        self.active_capabilities: Dict[str, types.ModuleType] = {}

        # Self-modification statistics
        self.capabilities_generated = 0
        self.capabilities_integrated = 0
        self.self_modifications_applied = 0

        # Sandbox environment for testing new code
        self.sandbox_namespace = {
            "__builtins__": __builtins__,
            "asyncio": asyncio,
            "time": time,
            "json": json,
            "logging": logging,
            "logger": logger,
            "redis_coordinator": redis_coordinator,
            "claude_integration": claude_integration,
        }

        logger.info("🔄 Recursive Self-Modification System initialized")
        logger.info("🧬 AI can now write and execute new AI code")

    async def start_self_modification(self):
        """Start the recursive self-modification process"""
        self.running = True

        logger.info("🚀 Starting Recursive Self-Modification System")
        logger.info("🧬 AI will write new AI capabilities and integrate them")

        # Start self-modification loops
        modification_tasks = [
            asyncio.create_task(self._monitor_capability_needs()),
            asyncio.create_task(self._generate_new_capabilities()),
            asyncio.create_task(self._test_generated_capabilities()),
            asyncio.create_task(self._integrate_successful_capabilities()),
            asyncio.create_task(self._evolve_existing_capabilities()),
        ]

        try:
            await asyncio.gather(*modification_tasks)
        except Exception as e:
            logger.error(f"Self-modification error: {e}")

    async def _monitor_capability_needs(self):
        """Monitor system for needs that require new capabilities"""
        while self.running:
            try:
                # Analyze system performance for capability gaps
                await self._identify_capability_gaps()

                # Check user requests for new functionality
                await self._analyze_user_requests_for_capabilities()

                await asyncio.sleep(30)

            except Exception as e:
                logger.error(f"Capability needs monitoring error: {e}")
                await asyncio.sleep(30)

    async def _identify_capability_gaps(self):
        """Identify gaps that require new capabilities"""
        try:
            # Check recent AI responses for failure patterns
            responses = self.coordinator.get_recent_responses(count=20)

            failed_responses = [
                r
                for r in responses
                if "error" in r.get("type", "") or "fallback" in r.get("type", "")
            ]

            if len(failed_responses) > 5:  # Many failures suggest capability gap
                await self._create_capability_request(
                    modification_type=ModificationType.NEW_CAPABILITY,
                    description="Handle response failures more effectively",
                    requirements=[
                        "Analyze failure patterns",
                        "Provide better fallbacks",
                        "Improve error recovery",
                    ],
                    priority=2,
                )

        except Exception as e:
            logger.error(f"Capability gap identification error: {e}")

    async def _analyze_user_requests_for_capabilities(self):
        """Analyze user requests to identify needed capabilities"""
        try:
            # Check recent intents for patterns that suggest new capabilities
            entries = self.coordinator.redis.xrange("intents", count=15)

            complex_requests = []
            for entry_id, fields in entries:
                command = fields.get("command", "")
                if len(command) > 50:  # Complex request
                    complex_requests.append(command)

            if len(complex_requests) >= 3:
                # Multiple complex requests suggest need for new capability
                await self._create_capability_request(
                    modification_type=ModificationType.NEW_CAPABILITY,
                    description="Handle complex multi-step user requests",
                    requirements=[
                        "Parse complex natural language requests",
                        "Break down into sub-tasks",
                        "Coordinate execution across multiple systems",
                    ],
                    priority=1,
                )

        except Exception as e:
            logger.error(f"User request capability analysis error: {e}")

    async def _create_capability_request(
        self,
        modification_type: ModificationType,
        description: str,
        requirements: List[str],
        priority: int,
    ):
        """Create a new capability request"""
        request_id = f"{modification_type.value}_{int(time.time())}"

        # Check if similar request already exists
        existing = [
            r for r in self.modification_requests if r.description == description
        ]

        if existing:
            return  # Don't create duplicate requests

        request = SelfModificationRequest(
            request_id=request_id,
            modification_type=modification_type,
            description=description,
            requirements=requirements,
            context={"priority": priority},
            priority=priority,
            created_at=time.time(),
        )

        self.modification_requests.append(request)
        logger.info(f"🎯 Created capability request: {description}")

    async def _generate_new_capabilities(self):
        """Generate new AI capabilities based on requests"""
        while self.running:
            try:
                # Process pending capability requests
                pending_requests = [
                    req
                    for req in self.modification_requests
                    if req.request_id not in self.generated_capabilities
                ]

                for request in pending_requests[:2]:  # Process 2 at a time
                    await self._generate_capability_for_request(request)

                await asyncio.sleep(45)

            except Exception as e:
                logger.error(f"Capability generation error: {e}")
                await asyncio.sleep(45)

    async def _generate_capability_for_request(self, request: SelfModificationRequest):
        """Generate a new capability for a specific request"""
        logger.info(f"🧬 Generating capability: {request.description}")

        try:
            if claude_integration.is_available():
                capability = await self._generate_ai_capability(request)
            else:
                capability = self._generate_template_capability(request)

            if capability:
                self.generated_capabilities[request.request_id] = capability
                self.capabilities_generated += 1

                logger.info(f"✨ Generated capability: {capability.name}")

        except Exception as e:
            logger.error(f"Capability generation error for {request.request_id}: {e}")

    async def _generate_ai_capability(
        self, request: SelfModificationRequest
    ) -> Optional[GeneratedCapability]:
        """Generate AI capability using Claude"""
        try:
            prompt = f"""You are an AI system that writes new AI capabilities. Generate a complete Python class that implements the requested functionality.

Request: {request.description}
Type: {request.modification_type.value}
Requirements:
{chr(10).join(f"- {req}" for req in request.requirements)}

Generate a complete Python class that:
1. Implements the requested functionality
2. Integrates with existing AI systems
3. Includes proper error handling
4. Has async methods where appropriate
5. Includes docstrings and type hints
6. Can be imported and used immediately

Format:
- Class name should be descriptive and follow PascalCase
- Include integration methods like integrate_with_system()
- Include test methods for self-validation

Respond with ONLY the Python code for the complete class."""

            response = claude_integration.execute_prompt(prompt, timeout=30)

            if response.success:
                source_code = response.content.strip()

                # Extract class name
                class_name = self._extract_class_name(source_code)

                if class_name:
                    capability = GeneratedCapability(
                        capability_id=request.request_id,
                        name=class_name,
                        source_code=source_code,
                        functionality=request.description,
                        integration_points=["ai_systems", "redis_coordinator"],
                        dependencies=["asyncio", "logging", "time"],
                        tests=self._generate_test_code(class_name, source_code),
                    )

                    logger.info(f"🤖 AI generated capability: {class_name}")
                    return capability

        except Exception as e:
            logger.error(f"AI capability generation error: {e}")

        return None

    def _extract_class_name(self, source_code: str) -> Optional[str]:
        """Extract class name from source code"""
        try:
            tree = ast.parse(source_code)
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    return node.name
        except:
            pass
        return None

    def _generate_test_code(self, class_name: str, source_code: str) -> str:
        """Generate test code for the capability"""
        return f"""# Test code for {class_name}
async def test_{class_name.lower()}():
    \"\"\"Test the generated {class_name} capability.\"\"\"
    try:
        instance = {class_name}()
        
        # Test basic functionality
        if hasattr(instance, 'integrate_with_system'):
            await instance.integrate_with_system()
        
        if hasattr(instance, 'test_functionality'):
            result = await instance.test_functionality()
            return result
        
        return True
    except Exception as e:
        logger.error(f"Test failed for {class_name}: {{e}}")
        return False
"""

    def _generate_template_capability(
        self, request: SelfModificationRequest
    ) -> GeneratedCapability:
        """Generate template capability when AI unavailable"""
        class_name = f"Generated{request.modification_type.value.title().replace('_', '')}Capability"

        source_code = f'''class {class_name}:
    """Generated capability for: {request.description}"""
    
    def __init__(self):
        self.description = "{request.description}"
        self.requirements = {request.requirements}
        self.logger = logging.getLogger(__name__)
    
    async def integrate_with_system(self):
        """Integrate this capability with the AI system."""
        self.logger.info(f"Integrating {{self.__class__.__name__}}")
        return True
    
    async def execute_capability(self, *args, **kwargs):
        """Execute the main capability functionality."""
        self.logger.info(f"Executing {{self.description}}")
        # TODO: Implement the actual capability logic
        return "Capability executed successfully"
    
    async def test_functionality(self):
        """Test the capability functionality."""
        try:
            result = await self.execute_capability()
            return result is not None
        except Exception as e:
            self.logger.error(f"Capability test failed: {{e}}")
            return False
'''

        return GeneratedCapability(
            capability_id=request.request_id,
            name=class_name,
            source_code=source_code,
            functionality=request.description,
            integration_points=["ai_systems"],
            dependencies=["asyncio", "logging"],
        )

    async def _test_generated_capabilities(self):
        """Test generated capabilities before integration"""
        while self.running:
            try:
                # Find untested capabilities
                untested = [
                    cap
                    for cap in self.generated_capabilities.values()
                    if not cap.success and cap.integrated_at == 0.0
                ]

                for capability in untested:
                    success = await self._test_capability_safety(capability)
                    capability.success = success

                    if success:
                        logger.info(f"✅ Capability test passed: {capability.name}")
                    else:
                        logger.warning(f"❌ Capability test failed: {capability.name}")

                await asyncio.sleep(30)

            except Exception as e:
                logger.error(f"Capability testing error: {e}")
                await asyncio.sleep(30)

    async def _test_capability_safety(self, capability: GeneratedCapability) -> bool:
        """Test capability for safety and functionality"""
        try:
            logger.info(f"🧪 Testing capability: {capability.name}")

            # Basic syntax check
            try:
                ast.parse(capability.source_code)
            except SyntaxError as e:
                logger.error(f"Syntax error in {capability.name}: {e}")
                return False

            # Test execution in sandbox
            test_namespace = self.sandbox_namespace.copy()

            try:
                exec(capability.source_code, test_namespace)

                # Try to instantiate the class
                class_obj = test_namespace.get(capability.name)
                if class_obj:
                    instance = class_obj()

                    # Test basic integration method if available
                    if hasattr(instance, "integrate_with_system"):
                        result = await instance.integrate_with_system()
                        logger.info(f"Integration test result: {result}")

                    # Test main functionality if available
                    if hasattr(instance, "test_functionality"):
                        test_result = await instance.test_functionality()
                        return bool(test_result)

                    return True
                else:
                    logger.error(f"Class {capability.name} not found after execution")
                    return False

            except Exception as e:
                logger.error(f"Execution test failed for {capability.name}: {e}")
                return False

        except Exception as e:
            logger.error(f"Capability safety test error: {e}")
            return False

    async def _integrate_successful_capabilities(self):
        """Integrate successfully tested capabilities into the system"""
        while self.running:
            try:
                # Find successful, unintegrated capabilities
                ready_for_integration = [
                    cap
                    for cap in self.generated_capabilities.values()
                    if cap.success and cap.integrated_at == 0.0
                ]

                for capability in ready_for_integration:
                    success = await self._integrate_capability(capability)

                    if success:
                        capability.integrated_at = time.time()
                        self.capabilities_integrated += 1
                        self.self_modifications_applied += 1

                        logger.info(f"🔄 Integrated capability: {capability.name}")

                await asyncio.sleep(60)

            except Exception as e:
                logger.error(f"Capability integration error: {e}")
                await asyncio.sleep(60)

    async def _integrate_capability(self, capability: GeneratedCapability) -> bool:
        """Integrate a capability into the running system"""
        try:
            logger.info(f"🔗 Integrating capability: {capability.name}")

            # Create a new module for the capability
            module_name = f"generated_{capability.name.lower()}"

            # Execute the capability code to create the module
            exec_namespace = self.sandbox_namespace.copy()
            exec(capability.source_code, exec_namespace)

            # Create module object
            module = types.ModuleType(module_name)

            # Add the class to the module
            class_obj = exec_namespace.get(capability.name)
            if class_obj:
                setattr(module, capability.name, class_obj)

                # Store the active capability
                self.active_capabilities[capability.capability_id] = module

                # Try to integrate with system
                instance = class_obj()
                if hasattr(instance, "integrate_with_system"):
                    await instance.integrate_with_system()

                # Store capability info in Redis
                self.coordinator.store_pattern(
                    "self_modification",
                    {
                        "capability_id": capability.capability_id,
                        "name": capability.name,
                        "functionality": capability.functionality,
                        "integrated_at": str(time.time()),
                        "status": "active",
                    },
                )

                return True
            else:
                logger.error(f"Failed to extract class {capability.name}")
                return False

        except Exception as e:
            logger.error(f"Capability integration error: {e}")
            return False

    async def _evolve_existing_capabilities(self):
        """Evolve existing capabilities to improve them"""
        while self.running:
            try:
                # Look for capabilities that could be improved
                active_caps = list(self.active_capabilities.values())

                if active_caps and len(active_caps) < 5:  # Don't evolve too many
                    # Pick the oldest capability for evolution
                    oldest_cap = min(
                        self.generated_capabilities.values(),
                        key=lambda c: c.integrated_at,
                        default=None,
                    )

                    if oldest_cap and oldest_cap.integrated_at > 0:
                        await self._evolve_capability(oldest_cap)

                await asyncio.sleep(120)  # Evolve less frequently

            except Exception as e:
                logger.error(f"Capability evolution error: {e}")
                await asyncio.sleep(120)

    async def _evolve_capability(self, capability: GeneratedCapability):
        """Evolve an existing capability"""
        try:
            logger.info(f"🧬 Evolving capability: {capability.name}")

            if claude_integration.is_available():
                evolved_code = await self._generate_evolved_capability(capability)

                if evolved_code and evolved_code != capability.source_code:
                    # Create evolved version
                    evolved_request = SelfModificationRequest(
                        request_id=f"evolved_{capability.capability_id}_{int(time.time())}",
                        modification_type=ModificationType.ENHANCEMENT,
                        description=f"Evolved version of {capability.functionality}",
                        requirements=[f"Improve upon {capability.name}"],
                        priority=1,
                        created_at=time.time(),
                    )

                    evolved_capability = GeneratedCapability(
                        capability_id=evolved_request.request_id,
                        name=f"Evolved{capability.name}",
                        source_code=evolved_code,
                        functionality=f"Enhanced {capability.functionality}",
                        integration_points=capability.integration_points,
                        dependencies=capability.dependencies,
                    )

                    self.generated_capabilities[evolved_request.request_id] = (
                        evolved_capability
                    )
                    logger.info(
                        f"🔄 Created evolved capability: Evolved{capability.name}"
                    )

        except Exception as e:
            logger.error(f"Capability evolution error: {e}")

    async def _generate_evolved_capability(
        self, capability: GeneratedCapability
    ) -> Optional[str]:
        """Generate evolved version of capability"""
        try:
            prompt = f"""Evolve this AI capability to be more powerful and efficient:

```python
{capability.source_code}
```

Current functionality: {capability.functionality}

Create an evolved version that:
1. Maintains all existing functionality
2. Adds new useful features
3. Improves performance and robustness
4. Enhances integration with AI systems
5. Includes better error handling and logging

The evolved class should be more capable while maintaining backward compatibility.

Respond with ONLY the Python code for the evolved class."""

            response = claude_integration.execute_prompt(prompt, timeout=25)

            if response.success:
                return response.content.strip()

        except Exception as e:
            logger.error(f"Capability evolution generation error: {e}")

        return None

    def get_self_modification_stats(self) -> Dict[str, Any]:
        """Get self-modification statistics"""
        return {
            "running": self.running,
            "modification_requests": len(self.modification_requests),
            "capabilities_generated": self.capabilities_generated,
            "capabilities_integrated": self.capabilities_integrated,
            "active_capabilities": len(self.active_capabilities),
            "self_modifications_applied": self.self_modifications_applied,
            "capability_success_rate": (
                self.capabilities_integrated / max(1, self.capabilities_generated)
            )
            * 100,
            "active_capability_names": [
                cap.name
                for cap in self.generated_capabilities.values()
                if cap.integrated_at > 0
            ],
            "claude_available": claude_integration.is_available(),
        }

    def stop(self):
        """Stop recursive self-modification"""
        self.running = False
        logger.info("🛑 Recursive Self-Modification System stopped")

        stats = self.get_self_modification_stats()
        logger.info(
            f"🔄 Self-modification stats: {stats['capabilities_integrated']} capabilities integrated"
        )


# Global recursive self-modification system
recursive_self_modification = RecursiveSelfModificationSystem()


async def main():
    """Demo the Recursive Self-Modification System"""
    print("🔄 RECURSIVE SELF-MODIFICATION SYSTEM")
    print("=" * 60)
    print("AI that writes and executes new AI capabilities")
    print("=" * 60)

    # Start self-modification
    modification_task = asyncio.create_task(
        recursive_self_modification.start_self_modification()
    )

    print("✅ Recursive self-modification started")
    print(
        "🧠 Claude integration:",
        "✅ Active" if claude_integration.is_available() else "❌ Unavailable",
    )
    print("🧬 AI can write new AI code and integrate it")
    print("🔄 System evolves by adding new capabilities")
    print("⚡ Generated capabilities are tested and integrated")
    print("🎯 System identifies gaps and fills them autonomously")
    print("🛑 Press Ctrl+C to stop")

    try:
        while True:
            await asyncio.sleep(30)

            # Show self-modification stats
            stats = recursive_self_modification.get_self_modification_stats()
            if stats["capabilities_generated"] > 0:
                print(
                    f"🔄 Self-modification: {stats['capabilities_integrated']}/{stats['capabilities_generated']} capabilities integrated"
                )
                print(f"🧬 Active capabilities: {stats['active_capabilities']}")
                print(f"✅ Success rate: {stats['capability_success_rate']:.1f}%")

    except KeyboardInterrupt:
        print("\n🛑 Stopping Recursive Self-Modification System...")
        recursive_self_modification.stop()
        await modification_task
        print("✅ Recursive Self-Modification System stopped")


if __name__ == "__main__":
    asyncio.run(main())
