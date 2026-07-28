#!/usr/bin/env python3
"""
Redis AI Challenge - Standing on Giants' Shoulders
Integrating proven patterns from StreamFlow AI, RedisAI, and MLQ
for Emacs-centric intelligent development environment

Based on research:
- StreamFlow AI: 100K+ events/second with Redis Streams
- RedisAI: Production model serving with tensor storage  
- MLQ: Async job queues with fault tolerance
- Our contribution: Emacs integration + homoiconic development
"""

import redis
import json
import time
import asyncio
import threading
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import uuid
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class JobStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing" 
    COMPLETED = "completed"
    FAILED = "failed"
    DEAD_LETTER = "dead_letter"

class StreamEventType(Enum):
    KEYSTROKE = "keystroke"
    AI_REQUEST = "ai_request"
    MODEL_INFERENCE = "model_inference"
    EMACS_COMMAND = "emacs_command"
    FEATURE_UPDATE = "feature_update"

@dataclass
class MLJob:
    """MLQ-inspired job structure with fault tolerance"""
    job_id: str
    event_type: StreamEventType
    payload: Dict[str, Any]
    priority: int = 0
    max_retries: int = 3
    retry_count: int = 0
    created_at: datetime = None
    processing_started_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)

@dataclass 
class StreamFlowFeature:
    """StreamFlow AI-inspired feature store entry"""
    feature_id: str
    feature_type: str
    value: Any
    confidence: float
    timestamp: datetime
    ttl_seconds: int = 300  # 5 minute default TTL

class RedisStreamFlowProcessor:
    """
    High-throughput ML coordination system combining proven patterns:
    - StreamFlow AI: High-throughput stream processing
    - MLQ: Fault-tolerant job queues  
    - RedisAI: Model serving patterns
    - Our innovation: Emacs-centric development workflow
    """
    
    def __init__(self, redis_host: str = 'localhost', redis_port: int = 6379):
        self.redis_client = redis.Redis(
            host=redis_host, 
            port=redis_port, 
            decode_responses=True,
            health_check_interval=30
        )
        
        # StreamFlow AI patterns
        self.feature_store_prefix = "features:"
        self.stream_prefix = "streams:"
        self.events_per_second = 0
        self.last_throughput_check = time.time()
        
        # MLQ patterns  
        self.job_queue = "mlq:jobs"
        self.processing_queue = "mlq:processing"
        self.dead_letter_queue = "mlq:dead_letter"
        self.reaper_interval = 30  # seconds
        
        # Our Emacs-specific streams
        self.emacs_keystrokes = f"{self.stream_prefix}emacs:keystrokes"
        self.ai_responses = f"{self.stream_prefix}ai:responses"
        self.model_inferences = f"{self.stream_prefix}ml:inferences"
        self.command_executions = f"{self.stream_prefix}emacs:commands"
        
        # Performance tracking (StreamFlow AI pattern)
        self.performance_metrics = {
            'events_processed': 0,
            'features_computed': 0,
            'predictions_made': 0,
            'avg_latency_ms': 0,
            'uptime_start': datetime.now(timezone.utc)
        }
        
        # Consumer groups for parallel processing
        self.consumer_groups = [
            "keystroke_processors",
            "ai_inference_engines", 
            "command_executors",
            "feature_engineers"
        ]
        
        self.running = False
        self.worker_threads = []
        
        logger.info("🚀 RedisStreamFlowProcessor initialized - standing on giants' shoulders!")
        
    async def initialize_streams_and_groups(self):
        """Initialize Redis streams and consumer groups (StreamFlow AI pattern)"""
        streams = [
            self.emacs_keystrokes,
            self.ai_responses, 
            self.model_inferences,
            self.command_executions
        ]
        
        for stream in streams:
            try:
                # Create stream if doesn't exist
                self.redis_client.xadd(stream, {"init": "stream_created"}, id="0-1")
                self.redis_client.xdel(stream, "0-1")
                
                # Create consumer groups
                for group in self.consumer_groups:
                    try:
                        self.redis_client.xgroup_create(stream, group, id="0", mkstream=True)
                        logger.info(f"✅ Created consumer group {group} for {stream}")
                    except redis.exceptions.ResponseError as e:
                        if "BUSYGROUP" in str(e):
                            logger.info(f"🔄 Consumer group {group} already exists for {stream}")
                        else:
                            logger.error(f"❌ Error creating consumer group: {e}")
                            
            except Exception as e:
                logger.error(f"❌ Error initializing stream {stream}: {e}")
                
    def add_feature_to_store(self, feature: StreamFlowFeature) -> bool:
        """Add feature to real-time feature store (StreamFlow AI pattern)"""
        try:
            feature_key = f"{self.feature_store_prefix}{feature.feature_id}"
            
            feature_data = {
                'type': feature.feature_type,
                'value': json.dumps(feature.value),
                'confidence': feature.confidence,
                'timestamp': feature.timestamp.isoformat(),
                'computed_at': datetime.now(timezone.utc).isoformat()
            }
            
            # Store with TTL for memory efficiency
            pipe = self.redis_client.pipeline()
            pipe.hset(feature_key, mapping=feature_data)
            pipe.expire(feature_key, feature.ttl_seconds)
            pipe.execute()
            
            self.performance_metrics['features_computed'] += 1
            return True
            
        except Exception as e:
            logger.error(f"❌ Error adding feature {feature.feature_id}: {e}")
            return False
            
    def get_feature_from_store(self, feature_id: str) -> Optional[StreamFlowFeature]:
        """Retrieve feature with microsecond latency (StreamFlow AI pattern)"""
        try:
            feature_key = f"{self.feature_store_prefix}{feature_id}"
            feature_data = self.redis_client.hgetall(feature_key)
            
            if not feature_data:
                return None
                
            return StreamFlowFeature(
                feature_id=feature_id,
                feature_type=feature_data['type'],
                value=json.loads(feature_data['value']),
                confidence=float(feature_data['confidence']),
                timestamp=datetime.fromisoformat(feature_data['timestamp'])
            )
            
        except Exception as e:
            logger.error(f"❌ Error retrieving feature {feature_id}: {e}")
            return None
            
    def enqueue_ml_job(self, job: MLJob) -> bool:
        """Enqueue ML job with fault tolerance (MLQ pattern)"""
        try:
            job_data = {
                'job_id': job.job_id,
                'event_type': job.event_type.value,
                'payload': json.dumps(job.payload),
                'priority': job.priority,
                'max_retries': job.max_retries,
                'retry_count': job.retry_count,
                'created_at': job.created_at.isoformat(),
                'status': JobStatus.PENDING.value
            }
            
            # Use sorted set for priority queue (MLQ pattern)
            score = job.priority * 1000000 + int(time.time())  # Priority + timestamp
            self.redis_client.zadd(self.job_queue, {json.dumps(job_data): score})
            
            logger.info(f"📤 Enqueued ML job {job.job_id} with priority {job.priority}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error enqueuing job {job.job_id}: {e}")
            return False
            
    def dequeue_ml_job(self) -> Optional[MLJob]:
        """Dequeue highest priority job (MLQ pattern)"""
        try:
            # Get highest priority job (lowest score)
            job_items = self.redis_client.zrange(self.job_queue, 0, 0, withscores=True)
            
            if not job_items:
                return None
                
            job_json, score = job_items[0]
            job_data = json.loads(job_json)
            
            # Atomically move from queue to processing
            pipe = self.redis_client.pipeline()
            pipe.zrem(self.job_queue, job_json)
            
            # Update status and move to processing queue
            job_data['status'] = JobStatus.PROCESSING.value
            job_data['processing_started_at'] = datetime.now(timezone.utc).isoformat()
            
            processing_key = f"{self.processing_queue}:{job_data['job_id']}"
            pipe.hset(processing_key, mapping=job_data)
            pipe.expire(processing_key, 300)  # 5 minute processing timeout
            
            pipe.execute()
            
            # Reconstruct MLJob object
            return MLJob(
                job_id=job_data['job_id'],
                event_type=StreamEventType(job_data['event_type']),
                payload=json.loads(job_data['payload']),
                priority=job_data['priority'],
                max_retries=job_data['max_retries'],
                retry_count=job_data['retry_count'],
                created_at=datetime.fromisoformat(job_data['created_at'])
            )
            
        except Exception as e:
            logger.error(f"❌ Error dequeuing job: {e}")
            return None
            
    def complete_ml_job(self, job_id: str, result: Dict[str, Any]) -> bool:
        """Mark job as completed and store result (MLQ pattern)"""
        try:
            processing_key = f"{self.processing_queue}:{job_id}"
            
            # Store completion result
            completion_data = {
                'job_id': job_id,
                'status': JobStatus.COMPLETED.value,
                'completed_at': datetime.now(timezone.utc).isoformat(),
                'result': json.dumps(result)
            }
            
            completion_key = f"mlq:completed:{job_id}"
            
            pipe = self.redis_client.pipeline()
            pipe.delete(processing_key)  # Remove from processing
            pipe.hset(completion_key, mapping=completion_data)
            pipe.expire(completion_key, 3600)  # Keep results for 1 hour
            pipe.execute()
            
            logger.info(f"✅ Completed ML job {job_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error completing job {job_id}: {e}")
            return False
            
    def fail_ml_job(self, job_id: str, error: str, retry: bool = True) -> bool:
        """Handle failed job with retry logic (MLQ pattern)"""
        try:
            processing_key = f"{self.processing_queue}:{job_id}"
            job_data = self.redis_client.hgetall(processing_key)
            
            if not job_data:
                logger.error(f"❌ Job {job_id} not found in processing queue")
                return False
                
            retry_count = int(job_data.get('retry_count', 0))
            max_retries = int(job_data.get('max_retries', 3))
            
            if retry and retry_count < max_retries:
                # Retry job
                job_data['retry_count'] = str(retry_count + 1)
                job_data['status'] = JobStatus.PENDING.value
                job_data['last_error'] = error
                
                # Re-enqueue with exponential backoff delay
                delay_score = int(time.time()) + (2 ** retry_count) * 10  # Exponential backoff
                
                pipe = self.redis_client.pipeline()
                pipe.delete(processing_key)
                pipe.zadd(self.job_queue, {json.dumps(job_data): delay_score})
                pipe.execute()
                
                logger.warning(f"🔄 Retrying job {job_id} (attempt {retry_count + 1}/{max_retries})")
                return True
                
            else:
                # Move to dead letter queue
                job_data['status'] = JobStatus.DEAD_LETTER.value
                job_data['final_error'] = error
                job_data['dead_lettered_at'] = datetime.now(timezone.utc).isoformat()
                
                dead_letter_key = f"{self.dead_letter_queue}:{job_id}"
                
                pipe = self.redis_client.pipeline()
                pipe.delete(processing_key)
                pipe.hset(dead_letter_key, mapping=job_data)
                pipe.execute()
                
                logger.error(f"💀 Job {job_id} moved to dead letter queue: {error}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error handling failed job {job_id}: {e}")
            return False
            
    def process_emacs_keystroke_event(self, keystroke_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process keystroke with real-time feature engineering (StreamFlow AI + our innovation)"""
        try:
            # Extract features from keystroke
            features = {
                'char_frequency': self.calculate_char_frequency(keystroke_data.get('char', '')),
                'typing_velocity': self.calculate_typing_velocity(keystroke_data),
                'buffer_context': self.analyze_buffer_context(keystroke_data),
                'command_prediction': self.predict_next_command(keystroke_data)
            }
            
            # Store features in real-time feature store
            for feature_name, feature_value in features.items():
                feature = StreamFlowFeature(
                    feature_id=f"keystroke_{keystroke_data.get('session_id', 'unknown')}_{feature_name}",
                    feature_type=feature_name,
                    value=feature_value,
                    confidence=0.85,
                    timestamp=datetime.now(timezone.utc)
                )
                self.add_feature_to_store(feature)
                
            # Update performance metrics
            self.performance_metrics['events_processed'] += 1
            
            return {
                'processed': True,
                'features_extracted': len(features),
                'requires_ai_inference': features['command_prediction']['confidence'] > 0.8
            }
            
        except Exception as e:
            logger.error(f"❌ Error processing keystroke event: {e}")
            return {'processed': False, 'error': str(e)}
            
    def calculate_char_frequency(self, char: str) -> Dict[str, float]:
        """Calculate character frequency for user profiling"""
        # Simplified - in real system would use sliding window
        return {
            'char': char,
            'frequency_score': 0.8,  # Mock calculation
            'is_common': char.isalnum()
        }
        
    def calculate_typing_velocity(self, keystroke_data: Dict[str, Any]) -> Dict[str, float]:
        """Calculate typing velocity for adaptive UI"""
        return {
            'chars_per_minute': 180.5,  # Mock calculation
            'velocity_trend': 'increasing',
            'confidence': 0.92
        }
        
    def analyze_buffer_context(self, keystroke_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze buffer context for intelligent suggestions"""
        buffer_name = keystroke_data.get('buffer', 'unknown')
        return {
            'buffer_type': 'code' if buffer_name.endswith(('.py', '.js', '.el')) else 'text',
            'context_complexity': 0.7,
            'semantic_hints': ['function_definition', 'variable_assignment']
        }
        
    def predict_next_command(self, keystroke_data: Dict[str, Any]) -> Dict[str, Any]:
        """Predict next Emacs command based on keystroke patterns"""
        # This would use ML model in real system
        return {
            'predicted_command': 'forward-char',
            'confidence': 0.87,
            'alternatives': [
                {'command': 'next-line', 'confidence': 0.12},
                {'command': 'save-buffer', 'confidence': 0.05}
            ]
        }
        
    async def start_processing(self):
        """Start high-throughput processing (StreamFlow AI pattern)"""
        self.running = True
        
        # Initialize streams and consumer groups
        await self.initialize_streams_and_groups()
        
        # Start worker threads for parallel processing
        workers = [
            ('keystroke_processor', self.keystroke_worker),
            ('ml_job_processor', self.ml_job_worker),
            ('reaper_process', self.reaper_worker),
            ('performance_monitor', self.performance_worker)
        ]
        
        for worker_name, worker_func in workers:
            thread = threading.Thread(target=worker_func, name=worker_name, daemon=True)
            thread.start()
            self.worker_threads.append(thread)
            logger.info(f"🚀 Started {worker_name} thread")
            
        logger.info("🎯 StreamFlow processing started - ready for high-throughput ML coordination!")
        
    def keystroke_worker(self):
        """Worker thread for processing keystrokes (StreamFlow AI pattern)"""
        consumer_name = f"keystroke_consumer_{uuid.uuid4().hex[:8]}"
        
        while self.running:
            try:
                # Read from keystroke stream with consumer group
                messages = self.redis_client.xreadgroup(
                    "keystroke_processors",
                    consumer_name,
                    {self.emacs_keystrokes: '>'},
                    count=10,  # Process in batches
                    block=1000  # 1 second timeout
                )
                
                for stream, msgs in messages:
                    for msg_id, fields in msgs:
                        try:
                            # Process keystroke event
                            result = self.process_emacs_keystroke_event(fields)
                            
                            # If requires AI inference, enqueue ML job
                            if result.get('requires_ai_inference'):
                                ml_job = MLJob(
                                    job_id=f"ai_inference_{uuid.uuid4().hex}",
                                    event_type=StreamEventType.AI_REQUEST,
                                    payload={
                                        'keystroke_data': fields,
                                        'processing_result': result
                                    },
                                    priority=1
                                )
                                self.enqueue_ml_job(ml_job)
                                
                            # Acknowledge message
                            self.redis_client.xack(self.emacs_keystrokes, "keystroke_processors", msg_id)
                            
                        except Exception as e:
                            logger.error(f"❌ Error processing keystroke message {msg_id}: {e}")
                            
            except Exception as e:
                if self.running:  # Only log if we're supposed to be running
                    logger.error(f"❌ Keystroke worker error: {e}")
                time.sleep(1)
                
    def ml_job_worker(self):
        """Worker thread for processing ML jobs (MLQ pattern)"""
        while self.running:
            try:
                job = self.dequeue_ml_job()
                
                if job is None:
                    time.sleep(0.1)  # Brief pause if no jobs
                    continue
                    
                # Process the ML job
                try:
                    result = self.process_ml_job(job)
                    self.complete_ml_job(job.job_id, result)
                    
                except Exception as e:
                    self.fail_ml_job(job.job_id, str(e))
                    
            except Exception as e:
                if self.running:
                    logger.error(f"❌ ML job worker error: {e}")
                time.sleep(1)
                
    def process_ml_job(self, job: MLJob) -> Dict[str, Any]:
        """Process ML job based on type"""
        if job.event_type == StreamEventType.AI_REQUEST:
            return self.handle_ai_inference_request(job.payload)
        elif job.event_type == StreamEventType.MODEL_INFERENCE:
            return self.handle_model_inference(job.payload)
        else:
            raise ValueError(f"Unknown job type: {job.event_type}")
            
    def handle_ai_inference_request(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle AI inference request (placeholder for real AI integration)"""
        # This would integrate with actual AI models
        keystroke_data = payload.get('keystroke_data', {})
        
        result = {
            'inference_type': 'command_prediction',
            'predicted_action': 'forward-char',
            'confidence': 0.92,
            'processing_time_ms': 15.3,
            'model_version': 'streamflow_v1.0'
        }
        
        self.performance_metrics['predictions_made'] += 1
        return result
        
    def handle_model_inference(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle model inference (RedisAI integration point)"""
        # This would integrate with RedisAI for tensor operations
        return {
            'inference_result': 'model_output',
            'tensor_shape': [1, 768],
            'processing_time_ms': 8.7
        }
        
    def reaper_worker(self):
        """Reaper thread for handling stalled jobs (MLQ pattern)"""
        while self.running:
            try:
                # Find jobs that have been processing too long
                current_time = int(time.time())
                processing_keys = self.redis_client.keys(f"{self.processing_queue}:*")
                
                for key in processing_keys:
                    job_data = self.redis_client.hgetall(key)
                    if not job_data:
                        continue
                        
                    processing_started = job_data.get('processing_started_at')
                    if processing_started:
                        started_time = datetime.fromisoformat(processing_started).timestamp()
                        if current_time - started_time > 300:  # 5 minutes timeout
                            job_id = job_data.get('job_id')
                            self.fail_ml_job(job_id, "Processing timeout - reaped by reaper", retry=True)
                            logger.warning(f"⚰️  Reaped stalled job {job_id}")
                            
                time.sleep(self.reaper_interval)
                
            except Exception as e:
                if self.running:
                    logger.error(f"❌ Reaper worker error: {e}")
                time.sleep(10)
                
    def performance_worker(self):
        """Performance monitoring worker (StreamFlow AI pattern)"""
        while self.running:
            try:
                current_time = time.time()
                
                # Calculate events per second
                time_diff = current_time - self.last_throughput_check
                if time_diff >= 1.0:  # Update every second
                    events_in_period = self.performance_metrics['events_processed']
                    self.events_per_second = events_in_period / time_diff
                    
                    # Log performance metrics
                    uptime = datetime.now(timezone.utc) - self.performance_metrics['uptime_start']
                    
                    logger.info(f"📊 Performance: {self.events_per_second:.1f} events/sec, "
                              f"{self.performance_metrics['predictions_made']} predictions, "
                              f"uptime: {uptime}")
                    
                    # Store metrics in Redis for monitoring
                    metrics_key = "streamflow:performance:current"
                    self.redis_client.hset(metrics_key, mapping={
                        'events_per_second': self.events_per_second,
                        'total_events': self.performance_metrics['events_processed'],
                        'total_predictions': self.performance_metrics['predictions_made'],
                        'uptime_seconds': uptime.total_seconds(),
                        'last_updated': datetime.now(timezone.utc).isoformat()
                    })
                    
                    self.last_throughput_check = current_time
                    
                time.sleep(1)
                
            except Exception as e:
                if self.running:
                    logger.error(f"❌ Performance worker error: {e}")
                time.sleep(5)
                
    def stop_processing(self):
        """Stop all processing threads"""
        logger.info("🛑 Stopping StreamFlow processing...")
        self.running = False
        
        # Wait for threads to finish
        for thread in self.worker_threads:
            thread.join(timeout=5)
            
        logger.info("✅ StreamFlow processing stopped")
        
    def demonstrate_integration(self):
        """Demonstrate integration of proven Redis AI patterns"""
        logger.info("🚀 REDIS AI CHALLENGE - STANDING ON GIANTS' SHOULDERS")
        logger.info("=" * 70)
        logger.info("Integrating StreamFlow AI + MLQ + RedisAI patterns for Emacs AI")
        
        # Simulate high-throughput keystroke processing
        logger.info("\n📊 Simulating high-throughput keystroke processing...")
        
        for i in range(100):
            keystroke_event = {
                'session_id': 'demo_session',
                'char': chr(97 + (i % 26)),  # a-z
                'buffer': 'test.py',
                'point': 1000 + i,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
            # Add to stream for processing
            self.redis_client.xadd(self.emacs_keystrokes, keystroke_event)
            
        logger.info(f"✅ Added 100 keystroke events to {self.emacs_keystrokes}")
        
        # Create some ML jobs
        logger.info("\n🤖 Creating ML inference jobs...")
        
        for i in range(10):
            job = MLJob(
                job_id=f"demo_job_{i}",
                event_type=StreamEventType.AI_REQUEST,
                payload={'demo_data': f'inference_request_{i}'},
                priority=i % 3  # Mix of priorities
            )
            self.enqueue_ml_job(job)
            
        logger.info("✅ Enqueued 10 ML jobs with varying priorities")
        
        # Show feature store usage
        logger.info("\n🏪 Demonstrating real-time feature store...")
        
        sample_feature = StreamFlowFeature(
            feature_id='emacs_demo_typing_velocity',
            feature_type='typing_metrics',
            value={'wpm': 85.5, 'accuracy': 0.97},
            confidence=0.94,
            timestamp=datetime.now(timezone.utc)
        )
        
        self.add_feature_to_store(sample_feature)
        retrieved_feature = self.get_feature_from_store('emacs_demo_typing_velocity')
        
        if retrieved_feature:
            logger.info(f"✅ Feature store working: {retrieved_feature.feature_id} = {retrieved_feature.value}")
        
        # Show queue status
        job_count = self.redis_client.zcard(self.job_queue)
        stream_length = self.redis_client.xlen(self.emacs_keystrokes)
        
        logger.info(f"\n📈 System Status:")
        logger.info(f"   Jobs in queue: {job_count}")
        logger.info(f"   Keystroke events: {stream_length}")
        logger.info(f"   Features computed: {self.performance_metrics['features_computed']}")
        
        logger.info(f"\n🎯 Innovation Summary:")
        logger.info("   • StreamFlow AI: High-throughput event processing ✅")
        logger.info("   • MLQ: Fault-tolerant job queues with retry logic ✅") 
        logger.info("   • RedisAI: Model serving integration points ✅")
        logger.info("   • Our contribution: Emacs-centric AI development workflow ✅")
        
        return {
            'jobs_queued': job_count,
            'events_streamed': stream_length,
            'features_stored': self.performance_metrics['features_computed'],
            'patterns_integrated': ['StreamFlow AI', 'MLQ', 'RedisAI', 'Emacs Integration']
        }

async def main():
    """Main demonstration"""
    processor = RedisStreamFlowProcessor()
    
    try:
        # Run demonstration
        result = processor.demonstrate_integration()
        
        # Optionally start full processing system
        print("\n🚀 Want to see the full system in action?")
        print("Uncomment the lines below to start high-throughput processing:")
        print("# await processor.start_processing()")
        print("# await asyncio.sleep(30)  # Run for 30 seconds")
        print("# processor.stop_processing()")
        
        return result
        
    except KeyboardInterrupt:
        logger.info("\n⏹️  Demo interrupted")
    except Exception as e:
        logger.error(f"\n❌ Demo error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        processor.stop_processing()

if __name__ == "__main__":
    result = asyncio.run(main())
    print(f"\n🎉 Integration complete: {result}")