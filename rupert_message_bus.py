#!/usr/bin/env python3
"""
RUPERT MESSAGE BUS - Clean Architecture Pattern
Send message → Rupert acknowledges → Monitor progress → Receive completion
Simple, reliable, scalable autonomous development coordination
"""

import asyncio
import time
import redis
import json
import uuid
from enum import Enum
from typing import Dict, Any, Optional, AsyncIterable

class TaskStatus(Enum):
    QUEUED = "queued"
    ACKNOWLEDGED = "acknowledged" 
    IN_PROGRESS = "in_progress"
    COMPLETE = "complete"
    FAILED = "failed"

class RupertMessageBus:
    """Message bus for coordinating with Rupert"""
    
    def __init__(self):
        self.r = redis.Redis(host='localhost', port=6379, decode_responses=True)
        self.running = True
        
        print("📨 RUPERT MESSAGE BUS ACTIVE")
        print("🔄 Clean architecture: Message → Acknowledge → Progress → Complete")
    
    def send_task(self, task_description: str, priority: int = 5) -> str:
        """Send a task to Rupert and get task ID"""
        
        task_id = str(uuid.uuid4())
        
        task_message = {
            'task_id': task_id,
            'description': task_description,
            'priority': priority,
            'status': TaskStatus.QUEUED.value,
            'created_at': str(time.time()),
            'requester': 'claude'
        }
        
        # Send to Rupert's task queue
        self.r.xadd('rupert:task_queue', task_message)
        
        # Initialize task tracking
        self.r.hset(f'rupert:task:{task_id}', mapping={
            'status': TaskStatus.QUEUED.value,
            'description': task_description,
            'created_at': str(time.time()),
            'last_update': str(time.time())
        })
        
        print(f"📤 SENT TASK: {task_id}")
        print(f"   Description: {task_description}")
        print(f"   Priority: {priority}")
        
        return task_id
    
    async def wait_for_acknowledgment(self, task_id: str, timeout: float = 30.0) -> bool:
        """Wait for Rupert to acknowledge the task"""
        
        print(f"⏳ WAITING FOR ACKNOWLEDGMENT: {task_id}")
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            task_data = self.r.hgetall(f'rupert:task:{task_id}')
            
            if task_data.get('status') == TaskStatus.ACKNOWLEDGED.value:
                print(f"✅ TASK ACKNOWLEDGED: {task_id}")
                return True
            
            await asyncio.sleep(0.5)  # Check every 500ms
        
        print(f"⏰ ACKNOWLEDGMENT TIMEOUT: {task_id}")
        return False
    
    async def monitor_progress(self, task_id: str) -> AsyncIterable[Dict[str, Any]]:
        """Monitor task progress with real-time updates"""
        
        print(f"👁️ MONITORING PROGRESS: {task_id}")
        
        last_update_time = 0
        
        while True:
            task_data = self.r.hgetall(f'rupert:task:{task_id}')
            
            if not task_data:
                break
            
            current_status = task_data.get('status')
            update_time = float(task_data.get('last_update', 0))
            
            # Yield progress updates
            if update_time > last_update_time:
                progress_update = {
                    'task_id': task_id,
                    'status': current_status,
                    'progress': task_data.get('progress', 'No progress info'),
                    'timestamp': update_time,
                    'details': task_data.get('details', '')
                }
                
                print(f"📊 PROGRESS UPDATE: {current_status}")
                if task_data.get('progress'):
                    print(f"   Progress: {task_data.get('progress')}")
                
                yield progress_update
                last_update_time = update_time
            
            # Check for completion
            if current_status in [TaskStatus.COMPLETE.value, TaskStatus.FAILED.value]:
                break
            
            await asyncio.sleep(1)  # Check every second
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get current task status"""
        
        task_data = self.r.hgetall(f'rupert:task:{task_id}')
        
        if not task_data:
            return None
        
        return {
            'task_id': task_id,
            'status': task_data.get('status'),
            'description': task_data.get('description'),
            'progress': task_data.get('progress'),
            'created_at': float(task_data.get('created_at', 0)),
            'last_update': float(task_data.get('last_update', 0)),
            'details': task_data.get('details', ''),
            'result': task_data.get('result', '')
        }
    
    async def complete_task_workflow(self, task_description: str, timeout: float = 300.0) -> Dict[str, Any]:
        """Complete workflow: send → acknowledge → monitor → complete"""
        
        print(f"🚀 STARTING COMPLETE WORKFLOW")
        print(f"   Task: {task_description}")
        
        # Step 1: Send task
        task_id = self.send_task(task_description)
        
        # Step 2: Wait for acknowledgment
        acknowledged = await self.wait_for_acknowledgment(task_id)
        
        if not acknowledged:
            return {
                'task_id': task_id,
                'success': False,
                'error': 'Task not acknowledged by Rupert'
            }
        
        # Step 3: Monitor progress
        final_status = None
        progress_log = []
        
        async for progress in self.monitor_progress(task_id):
            progress_log.append(progress)
            
            if progress['status'] in [TaskStatus.COMPLETE.value, TaskStatus.FAILED.value]:
                final_status = progress
                break
        
        # Step 4: Return completion result
        final_task_data = self.get_task_status(task_id)
        
        workflow_result = {
            'task_id': task_id,
            'success': final_status['status'] == TaskStatus.COMPLETE.value if final_status else False,
            'final_status': final_status,
            'progress_log': progress_log,
            'task_data': final_task_data,
            'total_time': time.time() - float(final_task_data['created_at']) if final_task_data else 0
        }
        
        if workflow_result['success']:
            print(f"✅ WORKFLOW COMPLETE: {task_id}")
            print(f"   Result: {final_task_data.get('result', 'No result data')}")
        else:
            print(f"❌ WORKFLOW FAILED: {task_id}")
        
        return workflow_result

class RupertTaskHandler:
    """Rupert's side of the message bus - handles incoming tasks"""
    
    def __init__(self):
        self.r = redis.Redis(host='localhost', port=6379, decode_responses=True)
        self.running = True
        
        print("🤖 RUPERT TASK HANDLER ACTIVE")
        print("📥 Listening for tasks on message bus")
    
    async def listen_for_tasks(self):
        """Listen for incoming tasks and process them"""
        
        while self.running:
            try:
                # Listen for new tasks
                tasks = self.r.xread({'rupert:task_queue': '$'}, block=1000, count=1)
                
                for stream, messages in tasks:
                    for task_id, task_data in messages:
                        await self.handle_task(task_data['task_id'], task_data)
                        
            except Exception as e:
                if "timeout" not in str(e):
                    print(f"❌ Task handler error: {e}")
                await asyncio.sleep(1)
    
    async def handle_task(self, task_id: str, task_data: Dict[str, Any]):
        """Handle a specific task through the complete workflow"""
        
        description = task_data['description']
        
        print(f"📥 RECEIVED TASK: {task_id}")
        print(f"   Description: {description}")
        
        # Step 1: Acknowledge task
        await self.acknowledge_task(task_id)
        
        # Step 2: Execute task with progress updates
        success = await self.execute_task_with_progress(task_id, description)
        
        # Step 3: Report completion
        await self.complete_task(task_id, success)
    
    async def acknowledge_task(self, task_id: str):
        """Acknowledge that we received and will process the task"""
        
        self.r.hset(f'rupert:task:{task_id}', mapping={
            'status': TaskStatus.ACKNOWLEDGED.value,
            'last_update': str(time.time()),
            'progress': 'Task acknowledged by Rupert'
        })
        
        print(f"✅ ACKNOWLEDGED: {task_id}")
    
    async def execute_task_with_progress(self, task_id: str, description: str) -> bool:
        """Execute task with real-time progress updates"""
        
        print(f"🔧 EXECUTING TASK: {task_id}")
        
        # Update status to in progress
        self.r.hset(f'rupert:task:{task_id}', mapping={
            'status': TaskStatus.IN_PROGRESS.value,
            'last_update': str(time.time()),
            'progress': 'Starting task execution'
        })
        
        try:
            # Simulate task execution with progress updates
            execution_steps = [
                "Analyzing task requirements",
                "Planning implementation approach", 
                "Executing core functionality",
                "Testing and validation",
                "Finalizing results"
            ]
            
            for i, step in enumerate(execution_steps):
                # Update progress
                progress_percent = int((i + 1) / len(execution_steps) * 100)
                
                self.r.hset(f'rupert:task:{task_id}', mapping={
                    'progress': f"{progress_percent}% - {step}",
                    'last_update': str(time.time()),
                    'details': f'Step {i+1}/{len(execution_steps)}: {step}'
                })
                
                print(f"   📊 {progress_percent}% - {step}")
                
                # Simulate work time
                await asyncio.sleep(2)
            
            # Task completed successfully
            return True
            
        except Exception as e:
            # Task failed
            self.r.hset(f'rupert:task:{task_id}', mapping={
                'status': TaskStatus.FAILED.value,
                'last_update': str(time.time()),
                'progress': f'Task failed: {str(e)}',
                'error': str(e)
            })
            
            print(f"❌ TASK FAILED: {task_id} - {e}")
            return False
    
    async def complete_task(self, task_id: str, success: bool):
        """Mark task as complete and report results"""
        
        if success:
            result_data = f"Task completed successfully - {task_id}"
            status = TaskStatus.COMPLETE.value
            print(f"✅ TASK COMPLETE: {task_id}")
        else:
            result_data = f"Task failed - {task_id}"
            status = TaskStatus.FAILED.value
            print(f"❌ TASK FAILED: {task_id}")
        
        # Final status update
        self.r.hset(f'rupert:task:{task_id}', mapping={
            'status': status,
            'last_update': str(time.time()),
            'progress': '100% - Complete',
            'result': result_data
        })
        
        # Send completion notification
        self.r.xadd('rupert:task_completions', {
            'task_id': task_id,
            'status': status,
            'result': result_data,
            'completed_at': str(time.time())
        })
    
    async def run_task_handler(self):
        """Run the complete task handler system"""
        
        print("🤖 RUPERT TASK HANDLER RUNNING")
        print("📥 Ready to receive and process tasks")
        
        await self.listen_for_tasks()

async def demo_message_bus():
    """Demonstrate the complete message bus architecture"""
    
    print("🎬 DEMONSTRATING RUPERT MESSAGE BUS ARCHITECTURE")
    print("="*60)
    
    # Start Rupert's task handler in background
    task_handler = RupertTaskHandler()
    handler_task = asyncio.create_task(task_handler.run_task_handler())
    
    # Give handler time to start
    await asyncio.sleep(1)
    
    # Create message bus client
    message_bus = RupertMessageBus()
    
    # Demonstrate complete workflow
    tasks = [
        "Analyze the current codebase structure",
        "Create a simple Redis integration function",
        "Test the function and report results"
    ]
    
    for task_desc in tasks:
        print(f"\n{'='*60}")
        result = await message_bus.complete_task_workflow(task_desc, timeout=30)
        
        print(f"🎯 WORKFLOW RESULT:")
        print(f"   Success: {result['success']}")
        print(f"   Total time: {result['total_time']:.1f}s")
        print(f"   Progress updates: {len(result['progress_log'])}")
    
    print(f"\n✅ MESSAGE BUS DEMONSTRATION COMPLETE")
    
    # Clean shutdown
    task_handler.running = False
    handler_task.cancel()

if __name__ == "__main__":
    asyncio.run(demo_message_bus())