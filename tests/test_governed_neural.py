#!/usr/bin/env python3
"""
Tests for Governed Neural Coordination System
"""

import pytest
import time
import redis
import numpy as np
from unittest.mock import Mock, patch

# Import our new modules
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from neural_coordination import FANNCoordinator, Agent, CoordinationTask, CoordinationNetworkType
from crypto_commitment import CryptoCommitmentAgent, CryptoEscrowAgent, CommitmentStatus
from governed_neural_system import GovernedNeuralCoordinator

class TestNeuralCoordination:
    """Test neural coordination functionality"""
    
    @pytest.fixture
    def redis_client(self):
        """Mock Redis client for testing"""
        mock_redis = Mock()
        mock_redis.ping.return_value = True
        mock_redis.hset.return_value = True
        mock_redis.get.return_value = None
        mock_redis.setex.return_value = True
        return mock_redis
    
    @pytest.fixture
    def coordinator(self, redis_client):
        """Create FANN coordinator for testing"""
        return FANNCoordinator(redis_client)
    
    @pytest.fixture
    def sample_agents(self):
        """Create sample agents for testing"""
        return [
            Agent("alice", ["coding", "testing"], 0.2, True, [0.9, 0.8, 0.9]),
            Agent("bob", ["security", "review"], 0.3, True, [0.8, 0.9, 0.8]),
            Agent("charlie", ["deployment", "docs"], 0.1, True, [0.7, 0.8, 0.9])
        ]
    
    @pytest.fixture
    def sample_task(self):
        """Create sample coordination task"""
        return CoordinationTask(
            task_id="test_task_001",
            requirements=["coding", "security", "testing"],
            priority=0.8,
            estimated_effort=6.0
        )
    
    def test_coordinator_initialization(self, coordinator):
        """Test coordinator initializes correctly"""
        assert coordinator.r is not None
        assert coordinator.coordination_networks == {}
        assert coordinator.performance_cache == {}
    
    def test_create_coordination_network(self, coordinator):
        """Test neural network creation"""
        network_id = coordinator.create_coordination_network(
            CoordinationNetworkType.SIMPLE_ALLOCATION, 
            input_size=5, 
            output_size=3
        )
        
        assert network_id in coordinator.coordination_networks
        network_data = coordinator.coordination_networks[network_id]
        assert network_data['type'] == CoordinationNetworkType.SIMPLE_ALLOCATION
        assert network_data['input_size'] == 5
        assert network_data['output_size'] == 3
        assert network_data['uses'] == 0
    
    def test_coordination_inputs_preparation(self, coordinator, sample_task, sample_agents):
        """Test input preparation for neural network"""
        inputs = coordinator._prepare_coordination_inputs(sample_task, sample_agents)
        
        # Should have task features + agent features
        expected_length = 4 + len(sample_agents)  # 4 task features + 1 per agent
        assert len(inputs) == expected_length
        
        # All inputs should be normalized [0,1]
        for inp in inputs:
            assert 0.0 <= inp <= 1.0
    
    def test_network_type_selection(self, coordinator, sample_task, sample_agents):
        """Test network type selection logic"""
        # High priority task should use priority routing
        high_priority_task = CoordinationTask("test", ["coding"], 0.9, 4.0)
        network_type = coordinator._select_network_type(high_priority_task, sample_agents)
        assert network_type == CoordinationNetworkType.PRIORITY_ROUTING
        
        # Many agents should use load balancing
        many_agents = sample_agents * 4  # 12 agents
        network_type = coordinator._select_network_type(sample_task, many_agents)
        assert network_type == CoordinationNetworkType.LOAD_BALANCING
        
        # Unavailable agents should use fault recovery
        unavailable_agents = [Agent("test", ["coding"], 0.1, False, [0.8])]
        network_type = coordinator._select_network_type(sample_task, unavailable_agents)
        assert network_type == CoordinationNetworkType.FAULT_RECOVERY
    
    def test_fast_coordination(self, coordinator, sample_task, sample_agents):
        """Test complete fast coordination workflow"""
        result = coordinator.coordinate_agents_fast(sample_task, sample_agents)
        
        assert 'assignment' in result
        assert 'coordination_time_ms' in result
        assert 'confidence' in result
        assert result['task_id'] == sample_task.task_id
        
        # Should be fast (under 1000ms for test)
        assert result['coordination_time_ms'] < 1000
        
        # Should assign to available agents only
        for agent_id in result['assignment']:
            assigned_agent = next(a for a in sample_agents if a.id == agent_id)
            assert assigned_agent.availability
    
    def test_assignment_generation(self, coordinator, sample_agents):
        """Test assignment generation from neural scores"""
        scores = [0.8, 0.6, 0.4]
        task = CoordinationTask("test", ["coding", "security"], 0.7, 4.0)
        
        assignment = coordinator._generate_assignment(sample_agents, scores, task)
        
        # Should assign best scoring agents
        assert len(assignment) <= len(task.requirements)
        
        # Check assignment structure
        for agent_id, assign_data in assignment.items():
            assert 'score' in assign_data
            assert 'role' in assign_data
            assert 'estimated_effort' in assign_data
    
    def test_confidence_calculation(self, coordinator):
        """Test confidence calculation"""
        # High variance scores should give high confidence
        high_variance = [0.9, 0.1, 0.5]
        confidence = coordinator._calculate_confidence(high_variance)
        assert confidence > 0.5
        
        # Low variance scores should give lower confidence
        low_variance = [0.5, 0.51, 0.49]
        confidence = coordinator._calculate_confidence(low_variance)
        assert confidence < 0.8

class TestCryptoCommitment:
    """Test cryptographic commitment functionality"""
    
    @pytest.fixture
    def redis_client(self):
        """Mock Redis client"""
        mock_redis = Mock()
        mock_redis.hset.return_value = True
        mock_redis.xadd.return_value = "test_id"
        return mock_redis
    
    @pytest.fixture
    def crypto_agent(self, redis_client):
        """Create crypto agent for testing"""
        return CryptoCommitmentAgent("test_agent", redis_client)
    
    @pytest.fixture
    def escrow_agent(self, redis_client):
        """Create escrow agent for testing"""
        return CryptoEscrowAgent(redis_client)
    
    def test_agent_initialization(self, crypto_agent):
        """Test crypto agent initialization"""
        assert crypto_agent.agent_id == "test_agent"
        assert crypto_agent.private_key is not None
        assert crypto_agent.public_key is not None
        assert len(crypto_agent.word_pool) > 0
    
    def test_commitment_word_generation(self, crypto_agent):
        """Test commitment word generation"""
        word = crypto_agent.generate_commitment_word()
        assert word in crypto_agent.word_pool
        assert len(word) >= 6  # All words should be 6+ characters
    
    def test_commitment_creation(self, crypto_agent):
        """Test commitment creation"""
        assignment_data = {"role": "coding", "effort": 4.0}
        commitment = crypto_agent.create_commitment("test_task", assignment_data)
        
        assert commitment.agent_id == "test_agent"
        assert commitment.task_id == "test_task"
        assert commitment.commitment_word is not None
        assert commitment.encrypted_commitment is not None
        assert commitment.status == CommitmentStatus.COMMITTED
        assert commitment.assignment_data == assignment_data
    
    def test_commitment_validation(self, redis_client):
        """Test commitment validation between agents"""
        # Create two agents
        agent1 = CryptoCommitmentAgent("agent1", redis_client)
        agent2 = CryptoCommitmentAgent("agent2", redis_client)
        
        # Agent1 creates commitment
        commitment = agent1.create_commitment("test", {"role": "test"})
        revealed_word = agent1.reveal_commitment(commitment)
        
        # Agent2 validates it
        is_valid = agent2.validate_other_commitment(commitment, revealed_word)
        assert is_valid
        
        # Invalid word should fail validation
        is_invalid = agent2.validate_other_commitment(commitment, "wrong_word")
        assert not is_invalid
    
    def test_escrow_transaction(self, escrow_agent):
        """Test escrow transaction management"""
        participants = ["alice", "bob", "charlie"]
        transaction_id = escrow_agent.start_transaction("test_task", participants)
        
        assert transaction_id in escrow_agent.active_transactions
        transaction = escrow_agent.active_transactions[transaction_id]
        assert transaction.task_id == "test_task"
        assert transaction.participants == participants
        assert len(transaction.commitments) == 0
    
    def test_escrow_validation(self, escrow_agent, redis_client):
        """Test complete escrow validation workflow"""
        # Setup transaction
        participants = ["alice", "bob"]
        transaction_id = escrow_agent.start_transaction("test_task", participants)
        
        # Create agents and commitments
        alice = CryptoCommitmentAgent("alice", redis_client)
        bob = CryptoCommitmentAgent("bob", redis_client)
        
        alice_commitment = alice.create_commitment("test_task", {"role": "coding"})
        bob_commitment = bob.create_commitment("test_task", {"role": "testing"})
        
        # Submit to escrow
        escrow_agent.receive_commitment(transaction_id, alice_commitment)
        escrow_agent.receive_commitment(transaction_id, bob_commitment)
        
        # Reveal words
        revealed_words = {
            "alice": alice.reveal_commitment(alice_commitment),
            "bob": bob.reveal_commitment(bob_commitment)
        }
        
        # Validate
        is_valid = escrow_agent.validate_transaction_completion(transaction_id, revealed_words)
        assert is_valid

class TestGovernedNeuralSystem:
    """Test complete governed neural coordination system"""
    
    @pytest.fixture
    def mock_redis(self):
        """Mock Redis for testing"""
        mock = Mock()
        mock.ping.return_value = True
        mock.hset.return_value = True
        mock.get.return_value = None
        mock.setex.return_value = True
        mock.xadd.return_value = "test_id"
        mock.keys.return_value = []
        return mock
    
    @pytest.fixture
    def governed_system(self, mock_redis):
        """Create governed system with mocked Redis"""
        with patch('governed_neural_system.redis.Redis', return_value=mock_redis):
            system = GovernedNeuralCoordinator()
            # Register test agents
            system.register_agent("alice", ["coding", "testing"])
            system.register_agent("bob", ["security", "review"])
            return system
    
    def test_system_initialization(self, governed_system):
        """Test system initialization"""
        assert governed_system.neural_coordinator is not None
        assert governed_system.crypto_escrow is not None
        assert governed_system.message_bus is not None
        assert len(governed_system.crypto_agents) == 2
        assert len(governed_system.agent_capabilities) == 2
    
    def test_agent_registration(self, governed_system):
        """Test agent registration"""
        governed_system.register_agent("charlie", ["deployment", "monitoring"])
        
        assert "charlie" in governed_system.crypto_agents
        assert "charlie" in governed_system.agent_capabilities
        assert governed_system.agent_capabilities["charlie"] == ["deployment", "monitoring"]
    
    def test_neural_agents_creation(self, governed_system):
        """Test conversion to neural agents"""
        neural_agents = governed_system.create_neural_agents()
        
        assert len(neural_agents) == 2
        agent_ids = [agent.id for agent in neural_agents]
        assert "alice" in agent_ids
        assert "bob" in agent_ids
        
        # Check agent properties
        for agent in neural_agents:
            assert agent.availability is True
            assert len(agent.capabilities) > 0
            assert 0.0 <= agent.current_load <= 1.0
    
    def test_performance_metrics(self, governed_system):
        """Test system performance metrics"""
        performance = governed_system.get_system_performance()
        
        assert 'neural_coordination' in performance
        assert 'crypto_transactions' in performance
        assert 'registered_agents' in performance
        assert 'system_status' in performance
        
        assert performance['registered_agents'] == 2
        assert performance['system_status'] == 'operational'

class TestIntegration:
    """Integration tests for the complete system"""
    
    @pytest.fixture
    def real_redis(self):
        """Real Redis connection for integration tests"""
        try:
            r = redis.Redis(host='localhost', port=6379, decode_responses=True)
            r.ping()
            return r
        except:
            pytest.skip("Redis not available for integration tests")
    
    def test_end_to_end_coordination(self, real_redis):
        """Test complete end-to-end coordination workflow"""
        # Create system components
        neural_coordinator = FANNCoordinator(real_redis)
        crypto_escrow = CryptoEscrowAgent(real_redis)
        
        # Create agents
        agents = [
            Agent("alice", ["coding", "testing"], 0.2, True, [0.9, 0.8, 0.9]),
            Agent("bob", ["security", "review"], 0.3, True, [0.8, 0.9, 0.8])
        ]
        
        crypto_agents = {
            agent.id: CryptoCommitmentAgent(agent.id, real_redis) for agent in agents
        }
        
        # Create task
        task = CoordinationTask(
            task_id="integration_test",
            requirements=["coding", "security"],
            priority=0.8,
            estimated_effort=4.0
        )
        
        # Neural coordination
        start_time = time.time()
        neural_result = neural_coordinator.coordinate_agents_fast(task, agents)
        neural_time = (time.time() - start_time) * 1000
        
        # Should be fast
        assert neural_time < 1000  # Under 1 second
        assert len(neural_result['assignment']) > 0
        
        # Crypto coordination
        assigned_agents = list(neural_result['assignment'].keys())
        transaction_id = crypto_escrow.start_transaction(task.task_id, assigned_agents)
        
        # Get commitments
        commitments = {}
        for agent_id, assignment in neural_result['assignment'].items():
            crypto_agent = crypto_agents[agent_id]
            commitment = crypto_agent.create_commitment(task.task_id, assignment)
            commitments[agent_id] = commitment
            crypto_escrow.receive_commitment(transaction_id, commitment)
        
        # Reveal and validate
        revealed_words = {}
        for agent_id, crypto_agent in crypto_agents.items():
            if agent_id in commitments:
                commitment = commitments[agent_id]
                revealed_word = crypto_agent.reveal_commitment(commitment)
                revealed_words[agent_id] = revealed_word
        
        validation_success = crypto_escrow.validate_transaction_completion(
            transaction_id, revealed_words
        )
        
        assert validation_success
        
        # Clean up test data
        real_redis.delete(f"crypto_escrow:transactions:{transaction_id}")
        for agent_id in assigned_agents:
            real_redis.delete(f"crypto_escrow:commitments:{transaction_id}:{agent_id}")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])