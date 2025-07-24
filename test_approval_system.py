#!/usr/bin/env python3
"""
Test suite for the approval system functionality.
Tests the complete approval workflow including schema, service, and API endpoints.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
from typing import Dict, Any, List

# Import approval system components
from approval.schema_extensions import ApprovalSchemaManager, ApprovalState, ApprovalSession
from approval.approval_service import EntityApprovalService


class TestApprovalSchemaManager:
    """Test the ApprovalSchemaManager class."""
    
    def test_approval_state_creation(self):
        """Test ApprovalState model creation."""
        state = ApprovalState(
            entity_id="test-entity-123",
            entity_type="Person",
            status="pending",
            entity_name="John Doe",
            confidence=0.85,
            document_source="test.md"
        )
        
        assert state.entity_id == "test-entity-123"
        assert state.entity_type == "Person"
        assert state.status == "pending"
        assert state.confidence == 0.85
        assert state.document_source == "test.md"
    
    def test_approval_session_creation(self):
        """Test ApprovalSession model creation."""
        session = ApprovalSession(
            session_id="session-123",
            document_title="Test Document",
            document_source="test.md",
            reviewer_id="reviewer-1"
        )
        
        assert session.session_id == "session-123"
        assert session.document_title == "Test Document"
        assert session.reviewer_id == "reviewer-1"
        assert session.status == "active"
    
    @patch('approval.schema_extensions.Neo4jDriver')
    def test_schema_manager_initialization(self, mock_driver):
        """Test schema manager initialization."""
        mock_driver_instance = Mock()
        mock_driver.return_value = mock_driver_instance
        
        manager = ApprovalSchemaManager("bolt://localhost:7687", "neo4j", "password")
        
        assert manager.driver == mock_driver_instance
        mock_driver.assert_called_once_with("bolt://localhost:7687", auth=("neo4j", "password"))


class TestEntityApprovalService:
    """Test the EntityApprovalService class."""
    
    @pytest.fixture
    def mock_schema_manager(self):
        """Mock schema manager fixture."""
        with patch('approval.approval_service.ApprovalSchemaManager') as mock_manager_class:
            mock_manager = AsyncMock()
            mock_manager_class.return_value = mock_manager
            yield mock_manager
    
    @pytest.fixture
    def approval_service(self, mock_schema_manager):
        """Create approval service with mocked dependencies."""
        return EntityApprovalService(
            neo4j_uri="bolt://localhost:7687",
            neo4j_user="neo4j",
            neo4j_password="password"
        )
    
    @pytest.mark.asyncio
    async def test_create_approval_session(self, approval_service, mock_schema_manager):
        """Test creating an approval session."""
        mock_schema_manager.create_approval_session.return_value = "session-123"
        
        session_id = await approval_service.create_approval_session(
            document_title="Test Document",
            document_source="test.md",
            reviewer_id="reviewer-1"
        )
        
        assert session_id == "session-123"
        mock_schema_manager.create_approval_session.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_entities_for_approval(self, approval_service, mock_schema_manager):
        """Test getting entities for approval."""
        mock_entities = [
            {
                "entity_id": "entity-1",
                "entity_type": "Person",
                "name": "John Doe",
                "status": "pending",
                "confidence": 0.85,
                "properties": {"age": 30, "location": "NYC"}
            },
            {
                "entity_id": "entity-2", 
                "entity_type": "Company",
                "name": "Tech Corp",
                "status": "pending",
                "confidence": 0.92,
                "properties": {"industry": "Technology", "founded": 2010}
            }
        ]
        
        mock_schema_manager.get_entities_for_approval.return_value = mock_entities
        
        entities = await approval_service.get_entities_for_approval(
            document_source="test.md",
            entity_types=["Person", "Company"],
            status_filter="pending"
        )
        
        assert len(entities) == 2
        assert entities[0]["entity_type"] == "Person"
        assert entities[1]["entity_type"] == "Company"
        mock_schema_manager.get_entities_for_approval.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_approve_entity(self, approval_service, mock_schema_manager):
        """Test approving an entity."""
        mock_schema_manager.approve_entity.return_value = True
        
        result = await approval_service.approve_entity(
            entity_id="entity-1",
            reviewer_id="reviewer-1",
            review_notes="Looks good",
            modified_data={"age": 31}
        )
        
        assert result is True
        mock_schema_manager.approve_entity.assert_called_once_with(
            "entity-1", "reviewer-1", "Looks good", {"age": 31}
        )
    
    @pytest.mark.asyncio
    async def test_reject_entity(self, approval_service, mock_schema_manager):
        """Test rejecting an entity."""
        mock_schema_manager.reject_entity.return_value = True
        
        result = await approval_service.reject_entity(
            entity_id="entity-1",
            reviewer_id="reviewer-1",
            review_notes="Incorrect information"
        )
        
        assert result is True
        mock_schema_manager.reject_entity.assert_called_once_with(
            "entity-1", "reviewer-1", "Incorrect information"
        )
    
    @pytest.mark.asyncio
    async def test_bulk_approve_entities(self, approval_service, mock_schema_manager):
        """Test bulk approving entities."""
        entity_ids = ["entity-1", "entity-2", "entity-3"]
        mock_schema_manager.bulk_approve_entities.return_value = {
            "approved_count": 3,
            "failed_entities": []
        }
        
        result = await approval_service.bulk_approve_entities(
            entity_ids=entity_ids,
            reviewer_id="reviewer-1"
        )
        
        assert result["approved_count"] == 3
        assert len(result["failed_entities"]) == 0
        mock_schema_manager.bulk_approve_entities.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_approval_statistics(self, approval_service, mock_schema_manager):
        """Test getting approval statistics."""
        mock_stats = {
            "total_entities": 100,
            "approved": 45,
            "rejected": 15,
            "pending": 40,
            "by_type": {
                "Person": {"total": 60, "approved": 30, "rejected": 10, "pending": 20},
                "Company": {"total": 40, "approved": 15, "rejected": 5, "pending": 20}
            }
        }
        
        mock_schema_manager.get_approval_statistics.return_value = mock_stats
        
        stats = await approval_service.get_approval_statistics("test.md")
        
        assert stats["total_entities"] == 100
        assert stats["approved"] == 45
        assert "by_type" in stats
        mock_schema_manager.get_approval_statistics.assert_called_once()


class TestApprovalSystemIntegration:
    """Integration tests for the complete approval system."""
    
    @pytest.mark.asyncio
    async def test_complete_approval_workflow(self):
        """Test a complete approval workflow from creation to completion."""
        with patch('approval.schema_extensions.ApprovalSchemaManager') as mock_manager_class:
            mock_manager = AsyncMock()
            mock_manager_class.return_value = mock_manager
            
            # Mock workflow responses
            mock_manager.create_approval_session.return_value = "session-123"
            mock_manager.get_entities_for_approval.return_value = [
                {
                    "entity_id": "entity-1",
                    "entity_type": "Person", 
                    "name": "John Doe",
                    "status": "pending",
                    "confidence": 0.85,
                    "properties": {"age": 30}
                }
            ]
            mock_manager.approve_entity.return_value = True
            mock_manager.get_approval_statistics.return_value = {
                "total_entities": 1,
                "approved": 1,
                "rejected": 0,
                "pending": 0
            }
            
            # Create service
            service = EntityApprovalService(
                neo4j_uri="bolt://localhost:7687",
                neo4j_user="neo4j",
                neo4j_password="password"
            )
            
            # 1. Create session
            session_id = await service.create_approval_session(
                document_title="Test Doc",
                document_source="test.md",
                reviewer_id="reviewer-1"
            )
            assert session_id == "session-123"
            
            # 2. Get entities for approval
            entities = await service.get_entities_for_approval("test.md")
            assert len(entities) == 1
            assert entities[0]["status"] == "pending"
            
            # 3. Approve entity
            result = await service.approve_entity(
                entity_id="entity-1",
                reviewer_id="reviewer-1"
            )
            assert result is True
            
            # 4. Check final statistics
            stats = await service.get_approval_statistics("test.md")
            assert stats["approved"] == 1
            assert stats["pending"] == 0


def test_approval_models_validation():
    """Test validation of approval system models."""
    # Test invalid status
    with pytest.raises(ValueError):
        ApprovalState(
            entity_id="test",
            entity_type="Person",
            status="invalid_status",  # Invalid status
            entity_name="Test",
            confidence=0.5,
            document_source="test.md"
        )
    
    # Test invalid confidence
    with pytest.raises(ValueError):
        ApprovalState(
            entity_id="test",
            entity_type="Person", 
            status="pending",
            entity_name="Test",
            confidence=1.5,  # Invalid confidence > 1.0
            document_source="test.md"
        )


def test_approval_service_factory_function():
    """Test the factory function for creating approval service."""
    from approval import create_entity_approval_service
    
    with patch('approval.approval_service.EntityApprovalService') as mock_service_class:
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        
        service = create_entity_approval_service(
            neo4j_uri="bolt://localhost:7687",
            neo4j_user="neo4j",
            neo4j_password="password"
        )
        
        assert service == mock_service
        mock_service_class.assert_called_once_with(
            neo4j_uri="bolt://localhost:7687",
            neo4j_user="neo4j", 
            neo4j_password="password"
        )


if __name__ == "__main__":
    # Run tests when script is executed directly
    pytest.main([__file__, "-v"])