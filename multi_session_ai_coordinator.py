#!/usr/bin/env python3
import redis
import json
import time
import asyncio
import aiohttp
from typing import Dict, List, Optional

class MultiSessionAICoordinator:
    def __init__(self):
        self.redis_client = redis.Redis(decode_responses=True)
        self.active_sessions = {}
        self.task_queue = 'ai:coordinator:tasks'
        
    async def create_ai_session(self, session_type: str, purpose: str) -> Dict:
        """Create new AI session for specific purpose"""
        session_id = f"{session_type}_{int(time.time())}"
        
        session_config = {
            'session_id': session_id,
            'type': session_type,
            'purpose': purpose,
            'status': 'active',
            'created': int(time.time()),
            'last_activity': int(time.time())
        }
        
        self.active_sessions[session_id] = session_config
        self.redis_client.hset(f'ai:sessions:{session_id}', mapping=session_config)
        
        print(f"Created AI session: {session_id} for {purpose}")
        return session_config
    
    async def delegate_task(self, task: Dict, preferred_session: Optional[str] = None):
        """Delegate task to appropriate AI session"""
        task_id = f"task_{int(time.time())}"
        
        # Determine best session for task
        if preferred_session and preferred_session in self.active_sessions:
            target_session = preferred_session
        else:
            target_session = self._select_best_session(task)
        
        task_data = {
            'task_id': task_id,
            'assigned_session': target_session,
            'task_type': task.get('type', 'general'),
            'description': task.get('description', ''),
            'priority': task.get('priority', 5),
            'status': 'pending',
            'created': int(time.time())
        }
        
        # Add to task queue
        self.redis_client.xadd(self.task_queue, '*', 
            'task_id', task_id,
            'session', target_session,
            'type', task_data['task_type'],
            'description', task_data['description'],
            'priority', task_data['priority']
        )
        
        print(f"Delegated task {task_id} to session {target_session}")
        return task_data
    
    def _select_best_session(self, task: Dict) -> str:
        """Select best AI session for task based on specialization"""
        task_type = task.get('type', 'general')
        
        # Session specialization mapping
        specializations = {
            'chat': ['human-ai', 'conversation', 'support'],
            'automation': ['desktop', 'window', 'input', 'control'],
            'coordination': ['multi-task', 'planning', 'orchestration'],
            'analysis': ['data', 'monitoring', 'reporting']
        }
        
        # Find best match
        for session_id, session in self.active_sessions.items():
            session_purpose = session.get('purpose', '').lower()
            for spec_type, keywords in specializations.items():
                if any(keyword in session_purpose for keyword in keywords):
                    if task_type in keywords or spec_type == task_type:
                        return session_id
        
        # Default to first available session
        return list(self.active_sessions.keys())[0] if self.active_sessions else 'default'
    
    async def coordinate_sessions(self):
        """Coordinate between multiple AI sessions"""
        while True:
            try:
                # Check for coordination requests
                coord_requests = self.redis_client.xread({
                    'ai:coordination:requests': '$'
                }, count=10, block=1000)
                
                for stream, messages in coord_requests:
                    for message_id, fields in messages:
                        await self._process_coordination_request(dict(fields))
                
            except Exception as e:
                print(f"Coordination error: {e}")
                await asyncio.sleep(1)
    
    async def _process_coordination_request(self, request: Dict):
        """Process coordination request between sessions"""
        request_type = request.get('type', 'sync')
        
        if request_type == 'sync':
            # Synchronize state between sessions
            await self._sync_sessions()
        elif request_type == 'delegate':
            # Delegate task between sessions
            await self.delegate_task(request)
        elif request_type == 'merge':
            # Merge results from multiple sessions
            await self._merge_session_results(request)
    
    async def _sync_sessions(self):
        """Synchronize state between all active sessions"""
        sync_data = {
            'timestamp': int(time.time()),
            'active_sessions': len(self.active_sessions),
            'total_tasks': self.redis_client.xlen(self.task_queue)
        }
        
        self.redis_client.hset('ai:coordination:sync', mapping=sync_data)
        print(f"Synchronized {len(self.active_sessions)} AI sessions")
    
    async def _merge_session_results(self, request: Dict):
        """Merge results from multiple sessions"""
        session_ids = request.get('sessions', [])
        results = {}
        
        for session_id in session_ids:
            session_results = self.redis_client.hgetall(f'ai:results:{session_id}')
            results[session_id] = session_results
        
        # Store merged results
        merged_id = f"merged_{int(time.time())}"
        self.redis_client.hset(f'ai:results:merged:{merged_id}', mapping={
            'merged_from': ','.join(session_ids),
            'result_count': len(results),
            'timestamp': int(time.time())
        })
        
        print(f"Merged results from {len(session_ids)} sessions")

if __name__ == "__main__":
    coordinator = MultiSessionAICoordinator()
    
    # Create initial sessions
    asyncio.run(coordinator.create_ai_session('chat', 'human-ai conversation'))
    asyncio.run(coordinator.create_ai_session('automation', 'desktop control'))
    asyncio.run(coordinator.create_ai_session('coordination', 'task orchestration'))
    
    print("Multi-session AI coordinator initialized")
