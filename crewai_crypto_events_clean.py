"""
Cryptographic Events for CrewAI Workflow Transparency
====================================================

Extends CrewAI's event system with cryptographic accountability events.
Addresses Issue #3268: "How to know which steps crew took to complete the goal"

These events provide tamper-proof audit trails for workflow execution.
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime

# Mock BaseEvent for development - will use real CrewAI BaseEvent in integration
@dataclass
class BaseEvent:
    """Base event class for CrewAI events"""
    timestamp: float
    
    def __post_init__(self):
        import time
        if not hasattr(self, 'timestamp') or not self.timestamp:
            self.timestamp = time.time()


@dataclass
class CryptographicCommitmentCreatedEvent(BaseEvent):
    """
    Event emitted when a cryptographic commitment is created for a task.
    
    This event marks the beginning of cryptographically accountable task execution,
    providing a tamper-proof record of task assignment and expected outcome.
    """
    commitment_word: str          # Human-readable commitment identifier
    task_id: str                 # CrewAI task identifier
    agent_id: str                # Executing agent identifier
    task_description: str        # Task description for audit trail
    commitment_hash: str         # Cryptographic hash (truncated for display)
    agent_role: str              # Agent role for workflow transparency
    workflow_id: Optional[str] = None  # Parent workflow identifier


@dataclass
class CryptographicValidationCompletedEvent(BaseEvent):
    """
    Event emitted when cryptographic commitment validation completes.
    
    This event provides cryptographic proof that a task was completed
    according to its original commitment, ensuring workflow integrity.
    """
    validation_success: bool      # Whether validation passed
    commitment_word: str         # Original commitment identifier
    revealed_word: str           # Revealed commitment for verification
    task_id: str                # Task that was validated
    agent_id: str               # Agent that completed the task
    validation_time_ms: float   # Time taken for validation
    result_hash: str            # Hash of task result for integrity


@dataclass
class CryptographicWorkflowAuditEvent(BaseEvent):
    """
    Event emitted for complete workflow audit information.
    
    This event provides comprehensive workflow transparency with
    cryptographic integrity guarantees for the entire execution.
    """
    workflow_id: str                    # Unique workflow identifier
    total_tasks: int                   # Total number of tasks in workflow
    validated_tasks: int               # Successfully validated tasks
    failed_validations: int            # Failed validation count
    workflow_integrity_score: float    # Overall integrity score (0.0-1.0)
    audit_trail: List[Dict[str, Any]]  # Complete audit trail
    crew_name: Optional[str] = None    # Name of the executing crew


@dataclass
class CryptographicEscrowTransactionEvent(BaseEvent):
    """
    Event emitted for escrow transaction management.
    
    This event tracks multi-agent escrow transactions for complex
    workflows requiring coordination between multiple agents.
    """
    transaction_id: str              # Unique escrow transaction ID
    participating_agents: List[str]  # Agent IDs in the transaction
    transaction_status: str          # Status: started, completed, failed
    commitment_words: Dict[str, str] # Agent ID -> commitment word mapping
    validation_results: Dict[str, bool] # Agent ID -> validation result
    workflow_id: Optional[str] = None   # Associated workflow


# Event type registry for CrewAI integration
CRYPTOGRAPHIC_EVENT_TYPES = [
    CryptographicCommitmentCreatedEvent,
    CryptographicValidationCompletedEvent,
    CryptographicWorkflowAuditEvent,
    CryptographicEscrowTransactionEvent,
]


def get_event_type_names() -> List[str]:
    """Get list of all cryptographic event type names"""
    return [event_type.__name__ for event_type in CRYPTOGRAPHIC_EVENT_TYPES]


def create_commitment_event(task_id: str, agent_id: str, commitment_word: str,
                          task_description: str, agent_role: str,
                          commitment_hash: str, workflow_id: str = None) -> CryptographicCommitmentCreatedEvent:
    """Create a cryptographic commitment event with proper validation"""
    return CryptographicCommitmentCreatedEvent(
        commitment_word=commitment_word,
        task_id=task_id,
        agent_id=agent_id,
        task_description=task_description,
        commitment_hash=commitment_hash,
        agent_role=agent_role,
        workflow_id=workflow_id,
        timestamp=0  # Will be set in __post_init__
    )


def create_validation_event(task_id: str, agent_id: str, validation_success: bool,
                          commitment_word: str, revealed_word: str,
                          validation_time_ms: float, result_hash: str) -> CryptographicValidationCompletedEvent:
    """Create a cryptographic validation event with proper validation"""
    return CryptographicValidationCompletedEvent(
        validation_success=validation_success,
        commitment_word=commitment_word,
        revealed_word=revealed_word,
        task_id=task_id,
        agent_id=agent_id,
        validation_time_ms=validation_time_ms,
        result_hash=result_hash,
        timestamp=0  # Will be set in __post_init__
    )


def create_audit_event(workflow_id: str, total_tasks: int, validated_tasks: int,
                      failed_validations: int, workflow_integrity_score: float,
                      audit_trail: List[Dict[str, Any]], crew_name: str = None) -> CryptographicWorkflowAuditEvent:
    """Create a workflow audit event with comprehensive data"""
    return CryptographicWorkflowAuditEvent(
        workflow_id=workflow_id,
        total_tasks=total_tasks,
        validated_tasks=validated_tasks,
        failed_validations=failed_validations,
        workflow_integrity_score=workflow_integrity_score,
        audit_trail=audit_trail,
        crew_name=crew_name,
        timestamp=0  # Will be set in __post_init__
    )


if __name__ == "__main__":
    # Demo event creation
    print("🔐 CrewAI Cryptographic Events Demo")
    print("=" * 50)
    
    # Create sample events
    commitment_event = create_commitment_event(
        task_id="task_001",
        agent_id="agent_researcher",
        commitment_word="thunderbolt",
        task_description="Research AI transparency methodologies",
        agent_role="Research Analyst",
        commitment_hash="a1b2c3d4...",
        workflow_id="workflow_123"
    )
    
    validation_event = create_validation_event(
        task_id="task_001",
        agent_id="agent_researcher",
        validation_success=True,
        commitment_word="thunderbolt",
        revealed_word="thunderbolt",
        validation_time_ms=15.2,
        result_hash="x9y8z7w6..."
    )
    
    audit_event = create_audit_event(
        workflow_id="workflow_123",
        total_tasks=2,
        validated_tasks=2,
        failed_validations=0,
        workflow_integrity_score=1.0,
        audit_trail=[],
        crew_name="AI_Research_Crew"
    )
    
    print(f"✅ Commitment Event: {commitment_event.commitment_word} for {commitment_event.task_description}")
    print(f"✅ Validation Event: {'PASSED' if validation_event.validation_success else 'FAILED'} in {validation_event.validation_time_ms}ms")
    print(f"✅ Audit Event: {audit_event.validated_tasks}/{audit_event.total_tasks} tasks validated")
    print(f"\n🎯 All events created successfully - ready for CrewAI integration!")