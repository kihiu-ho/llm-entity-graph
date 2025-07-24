"""
Enhanced staging service for comprehensive entity and relationship management.
Provides CRUD operations, validation, conflict detection, and batch operations.
"""

import os
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import logging

from ..models.enhanced_staging_models import (
    EnhancedStagingSession, EnhancedEntity, EnhancedRelationship,
    EntityStatus, ApprovalStage, WorkflowStage, SessionStatus,
    ValidationResult, AuditEntry
)

logger = logging.getLogger(__name__)


class EnhancedStagingService:
    """Enhanced staging service with comprehensive workflow support."""
    
    def __init__(self, staging_dir: str = "staging/data"):
        self.staging_dir = Path(staging_dir)
        self.staging_dir.mkdir(parents=True, exist_ok=True)
        self._initialized = False
    
    async def initialize(self):
        """Initialize the staging service."""
        if not self._initialized:
            logger.info("Initializing Enhanced Staging Service")
            self._initialized = True
    
    # Session Management
    
    async def get_all_sessions(self, status_filter: Optional[str] = None, 
                              workflow_stage_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all staging sessions with optional filtering."""
        if not self._initialized:
            await self.initialize()
        
        sessions = []
        for session_file in self.staging_dir.glob("*.json"):
            try:
                with open(session_file, 'r', encoding='utf-8') as f:
                    session_data = json.load(f)
                
                # Apply filters
                if status_filter and session_data.get('status') != status_filter:
                    continue
                if workflow_stage_filter and session_data.get('workflow_stage') != workflow_stage_filter:
                    continue
                
                sessions.append(session_data)
            except Exception as e:
                logger.error(f"Error loading session file {session_file}: {e}")
        
        # Sort by creation date (newest first)
        sessions.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        return sessions
    
    async def get_session(self, session_id: str) -> Optional[EnhancedStagingSession]:
        """Get a specific staging session."""
        if not self._initialized:
            await self.initialize()
        
        session_file = self.staging_dir / f"{session_id}.json"
        if not session_file.exists():
            return None
        
        try:
            with open(session_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
            return EnhancedStagingSession.from_dict(session_data)
        except Exception as e:
            logger.error(f"Error loading session {session_id}: {e}")
            return None
    
    async def save_session(self, session: EnhancedStagingSession) -> bool:
        """Save a staging session."""
        if not self._initialized:
            await self.initialize()
        
        try:
            session.updated_at = datetime.now().isoformat()
            session.update_statistics()
            
            session_file = self.staging_dir / f"{session.session_id}.json"
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(session.to_dict(), f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved session {session.session_id}")
            return True
        except Exception as e:
            logger.error(f"Error saving session {session.session_id}: {e}")
            return False
    
    async def create_session(self, document_title: str, document_source: str, 
                           metadata: Optional[Dict[str, Any]] = None) -> str:
        """Create a new staging session."""
        if not self._initialized:
            await self.initialize()
        
        session_id = str(uuid.uuid4())
        session = EnhancedStagingSession(
            session_id=session_id,
            document_title=document_title,
            document_source=document_source,
            metadata=metadata or {}
        )
        
        await self.save_session(session)
        return session_id
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete a staging session."""
        if not self._initialized:
            await self.initialize()
        
        session_file = self.staging_dir / f"{session_id}.json"
        if session_file.exists():
            try:
                session_file.unlink()
                logger.info(f"Deleted session {session_id}")
                return True
            except Exception as e:
                logger.error(f"Error deleting session {session_id}: {e}")
        return False
    
    # Entity Management
    
    async def get_entities(self, session_id: str, status_filter: Optional[str] = None,
                          type_filter: Optional[str] = None, search_query: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get entities from a session with optional filtering."""
        session = await self.get_session(session_id)
        if not session:
            return []
        
        entities = []
        for entity in session.entities:
            # Apply filters
            if status_filter and entity.status.value != status_filter:
                continue
            if type_filter and entity.type != type_filter:
                continue
            if search_query and search_query.lower() not in entity.name.lower():
                continue
            
            entities.append(entity.to_dict())
        
        return entities
    
    async def get_entity(self, session_id: str, entity_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific entity."""
        session = await self.get_session(session_id)
        if not session:
            return None
        
        entity = session.get_entity_by_id(entity_id)
        return entity.to_dict() if entity else None
    
    async def update_entity(self, session_id: str, entity_id: str, updates: Dict[str, Any], 
                           user: str = "system", comment: Optional[str] = None) -> bool:
        """Update an entity."""
        session = await self.get_session(session_id)
        if not session:
            return False
        
        entity = session.get_entity_by_id(entity_id)
        if not entity:
            return False
        
        # Update entity attributes
        if 'name' in updates:
            entity.name = updates['name']
        if 'type' in updates:
            entity.type = updates['type']
        if 'attributes' in updates:
            entity.update_attributes(updates['attributes'], user, comment)
        
        # Update status if provided
        if 'status' in updates:
            if updates['status'] == 'approved':
                stage = ApprovalStage(updates.get('approval_stage', 'final'))
                entity.approve(user, stage, comment)
            elif updates['status'] == 'rejected':
                entity.reject(user, comment)
        
        return await self.save_session(session)
    
    async def add_entity(self, session_id: str, entity_data: Dict[str, Any], 
                        user: str = "system") -> Optional[str]:
        """Add a new entity to a session."""
        session = await self.get_session(session_id)
        if not session:
            return None
        
        entity_id = entity_data.get('id', str(uuid.uuid4()))
        entity = EnhancedEntity(
            id=entity_id,
            name=entity_data['name'],
            type=entity_data['type'],
            attributes=entity_data.get('attributes', {}),
            confidence=entity_data.get('confidence', 0.0),
            source_text=entity_data.get('source_text')
        )
        
        session.add_entity(entity, user)
        await self.save_session(session)
        return entity_id
    
    async def delete_entity(self, session_id: str, entity_id: str, user: str = "system") -> bool:
        """Delete an entity from a session."""
        session = await self.get_session(session_id)
        if not session:
            return False
        
        session.remove_entity(entity_id, user)
        return await self.save_session(session)
    
    # Relationship Management
    
    async def get_relationships(self, session_id: str, status_filter: Optional[str] = None,
                               type_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get relationships from a session with optional filtering."""
        session = await self.get_session(session_id)
        if not session:
            return []
        
        relationships = []
        for relationship in session.relationships:
            # Apply filters
            if status_filter and relationship.status.value != status_filter:
                continue
            if type_filter and relationship.relationship_type != type_filter:
                continue
            
            relationships.append(relationship.to_dict())
        
        return relationships
    
    async def get_relationship(self, session_id: str, relationship_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific relationship."""
        session = await self.get_session(session_id)
        if not session:
            return None
        
        relationship = session.get_relationship_by_id(relationship_id)
        return relationship.to_dict() if relationship else None
    
    async def update_relationship(self, session_id: str, relationship_id: str, updates: Dict[str, Any],
                                 user: str = "system", comment: Optional[str] = None) -> bool:
        """Update a relationship."""
        session = await self.get_session(session_id)
        if not session:
            return False
        
        relationship = session.get_relationship_by_id(relationship_id)
        if not relationship:
            return False
        
        # Update relationship attributes
        if 'relationship_type' in updates:
            relationship.relationship_type = updates['relationship_type']
        if 'attributes' in updates:
            relationship.update_attributes(updates['attributes'], user, comment)
        
        # Update status if provided
        if 'status' in updates:
            if updates['status'] == 'approved':
                stage = ApprovalStage(updates.get('approval_stage', 'final'))
                relationship.approve(user, stage, comment)
            elif updates['status'] == 'rejected':
                relationship.reject(user, comment)
        
        return await self.save_session(session)
    
    async def add_relationship(self, session_id: str, relationship_data: Dict[str, Any],
                              user: str = "system") -> Optional[str]:
        """Add a new relationship to a session."""
        session = await self.get_session(session_id)
        if not session:
            return None
        
        relationship_id = relationship_data.get('id', str(uuid.uuid4()))
        relationship = EnhancedRelationship(
            id=relationship_id,
            source_entity_id=relationship_data['source_entity_id'],
            target_entity_id=relationship_data['target_entity_id'],
            relationship_type=relationship_data['relationship_type'],
            attributes=relationship_data.get('attributes', {}),
            confidence=relationship_data.get('confidence', 0.0),
            source_text=relationship_data.get('source_text')
        )
        
        session.add_relationship(relationship, user)
        await self.save_session(session)
        return relationship_id
    
    async def delete_relationship(self, session_id: str, relationship_id: str, user: str = "system") -> bool:
        """Delete a relationship from a session."""
        session = await self.get_session(session_id)
        if not session:
            return False
        
        session.remove_relationship(relationship_id, user)
        return await self.save_session(session)


    # Batch Operations

    async def batch_approve_entities(self, session_id: str, entity_ids: List[str],
                                   user: str = "system", comment: Optional[str] = None) -> Dict[str, Any]:
        """Batch approve multiple entities."""
        session = await self.get_session(session_id)
        if not session:
            return {"success": False, "error": "Session not found"}

        approved_count = 0
        failed_ids = []

        for entity_id in entity_ids:
            entity = session.get_entity_by_id(entity_id)
            if entity:
                entity.approve(user, ApprovalStage.FINAL, comment)
                approved_count += 1
            else:
                failed_ids.append(entity_id)

        await self.save_session(session)

        return {
            "success": True,
            "approved_count": approved_count,
            "failed_ids": failed_ids,
            "total_requested": len(entity_ids)
        }

    async def batch_reject_entities(self, session_id: str, entity_ids: List[str],
                                  user: str = "system", comment: Optional[str] = None) -> Dict[str, Any]:
        """Batch reject multiple entities."""
        session = await self.get_session(session_id)
        if not session:
            return {"success": False, "error": "Session not found"}

        rejected_count = 0
        failed_ids = []

        for entity_id in entity_ids:
            entity = session.get_entity_by_id(entity_id)
            if entity:
                entity.reject(user, comment)
                rejected_count += 1
            else:
                failed_ids.append(entity_id)

        await self.save_session(session)

        return {
            "success": True,
            "rejected_count": rejected_count,
            "failed_ids": failed_ids,
            "total_requested": len(entity_ids)
        }

    async def batch_approve_relationships(self, session_id: str, relationship_ids: List[str],
                                        user: str = "system", comment: Optional[str] = None) -> Dict[str, Any]:
        """Batch approve multiple relationships."""
        session = await self.get_session(session_id)
        if not session:
            return {"success": False, "error": "Session not found"}

        approved_count = 0
        failed_ids = []

        for relationship_id in relationship_ids:
            relationship = session.get_relationship_by_id(relationship_id)
            if relationship:
                relationship.approve(user, ApprovalStage.FINAL, comment)
                approved_count += 1
            else:
                failed_ids.append(relationship_id)

        await self.save_session(session)

        return {
            "success": True,
            "approved_count": approved_count,
            "failed_ids": failed_ids,
            "total_requested": len(relationship_ids)
        }

    async def batch_reject_relationships(self, session_id: str, relationship_ids: List[str],
                                       user: str = "system", comment: Optional[str] = None) -> Dict[str, Any]:
        """Batch reject multiple relationships."""
        session = await self.get_session(session_id)
        if not session:
            return {"success": False, "error": "Session not found"}

        rejected_count = 0
        failed_ids = []

        for relationship_id in relationship_ids:
            relationship = session.get_relationship_by_id(relationship_id)
            if relationship:
                relationship.reject(user, comment)
                rejected_count += 1
            else:
                failed_ids.append(relationship_id)

        await self.save_session(session)

        return {
            "success": True,
            "rejected_count": rejected_count,
            "failed_ids": failed_ids,
            "total_requested": len(relationship_ids)
        }

    # Validation and Conflict Detection

    async def validate_session(self, session_id: str) -> Dict[str, Any]:
        """Validate all entities and relationships in a session."""
        session = await self.get_session(session_id)
        if not session:
            return {"success": False, "error": "Session not found"}

        validation_results = {
            "session_id": session_id,
            "entities": [],
            "relationships": [],
            "summary": {
                "total_entities": len(session.entities),
                "total_relationships": len(session.relationships),
                "valid_entities": 0,
                "valid_relationships": 0,
                "entities_with_warnings": 0,
                "relationships_with_warnings": 0,
                "entities_with_errors": 0,
                "relationships_with_errors": 0
            }
        }

        # Validate entities
        for entity in session.entities:
            result = self._validate_entity(entity, session)
            validation_results["entities"].append({
                "entity_id": entity.id,
                "entity_name": entity.name,
                "validation": result.to_dict()
            })

            if result.is_valid:
                validation_results["summary"]["valid_entities"] += 1
            if result.warnings:
                validation_results["summary"]["entities_with_warnings"] += 1
            if result.errors:
                validation_results["summary"]["entities_with_errors"] += 1

        # Validate relationships
        for relationship in session.relationships:
            result = self._validate_relationship(relationship, session)
            validation_results["relationships"].append({
                "relationship_id": relationship.id,
                "relationship_type": relationship.relationship_type,
                "validation": result.to_dict()
            })

            if result.is_valid:
                validation_results["summary"]["valid_relationships"] += 1
            if result.warnings:
                validation_results["summary"]["relationships_with_warnings"] += 1
            if result.errors:
                validation_results["summary"]["relationships_with_errors"] += 1

        return {"success": True, "validation_results": validation_results}

    def _validate_entity(self, entity: EnhancedEntity, session: EnhancedStagingSession) -> ValidationResult:
        """Validate a single entity."""
        warnings = []
        errors = []

        # Check for empty name
        if not entity.name or not entity.name.strip():
            errors.append("Entity name cannot be empty")

        # Check for very short names
        if len(entity.name.strip()) < 2:
            warnings.append("Entity name is very short")

        # Check for duplicate names
        duplicates = [e for e in session.entities if e.id != entity.id and e.name.lower() == entity.name.lower()]
        if duplicates:
            warnings.append(f"Duplicate entity name found: {len(duplicates)} other entities with same name")

        # Check confidence score
        if entity.confidence < 0.3:
            warnings.append(f"Low confidence score: {entity.confidence}")

        # Check for missing type
        if not entity.type:
            errors.append("Entity type is required")

        is_valid = len(errors) == 0
        return ValidationResult(is_valid=is_valid, warnings=warnings, errors=errors)

    def _validate_relationship(self, relationship: EnhancedRelationship,
                              session: EnhancedStagingSession) -> ValidationResult:
        """Validate a single relationship."""
        warnings = []
        errors = []

        # Check if source and target entities exist
        source_entity = session.get_entity_by_id(relationship.source_entity_id)
        target_entity = session.get_entity_by_id(relationship.target_entity_id)

        if not source_entity:
            errors.append(f"Source entity not found: {relationship.source_entity_id}")
        if not target_entity:
            errors.append(f"Target entity not found: {relationship.target_entity_id}")

        # Check for self-relationships
        if relationship.source_entity_id == relationship.target_entity_id:
            warnings.append("Self-relationship detected")

        # Check for empty relationship type
        if not relationship.relationship_type or not relationship.relationship_type.strip():
            errors.append("Relationship type cannot be empty")

        # Check confidence score
        if relationship.confidence < 0.3:
            warnings.append(f"Low confidence score: {relationship.confidence}")

        # Check for duplicate relationships
        duplicates = [r for r in session.relationships
                     if r.id != relationship.id
                     and r.source_entity_id == relationship.source_entity_id
                     and r.target_entity_id == relationship.target_entity_id
                     and r.relationship_type == relationship.relationship_type]
        if duplicates:
            warnings.append(f"Duplicate relationship found: {len(duplicates)} similar relationships")

        is_valid = len(errors) == 0
        return ValidationResult(is_valid=is_valid, warnings=warnings, errors=errors)


# Global service instance
enhanced_staging_service = EnhancedStagingService()
