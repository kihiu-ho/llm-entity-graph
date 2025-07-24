"""
Enhanced staging models for comprehensive entity and relationship management.
Supports approval workflows, edit history, validation, and conflict detection.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import uuid
import json


class EntityStatus(Enum):
    """Status of an entity in the approval workflow."""
    PENDING = "pending"
    APPROVED = "approved" 
    REJECTED = "rejected"
    EDITED = "edited"
    CONFLICTED = "conflicted"


class ApprovalStage(Enum):
    """Stage of approval process."""
    INITIAL = "initial"
    FINAL = "final"


class WorkflowStage(Enum):
    """Overall workflow stage."""
    EXTRACTION = "extraction"
    REVIEW = "review"
    APPROVAL = "approval"
    INGESTION = "ingestion"
    COMPLETED = "completed"


class SessionStatus(Enum):
    """Status of a staging session."""
    PENDING_REVIEW = "pending_review"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    INGESTED = "ingested"
    ARCHIVED = "archived"


@dataclass
class AuditEntry:
    """Represents an audit trail entry."""
    timestamp: str
    user: str
    action: str  # created, edited, approved, rejected, deleted
    changes: Dict[str, Any]
    comment: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp,
            'user': self.user,
            'action': self.action,
            'changes': self.changes,
            'comment': self.comment
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AuditEntry':
        return cls(
            timestamp=data['timestamp'],
            user=data['user'],
            action=data['action'],
            changes=data['changes'],
            comment=data.get('comment')
        )


@dataclass
class ValidationResult:
    """Represents validation results for an entity or relationship."""
    is_valid: bool
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'is_valid': self.is_valid,
            'warnings': self.warnings,
            'errors': self.errors
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ValidationResult':
        return cls(
            is_valid=data['is_valid'],
            warnings=data.get('warnings', []),
            errors=data.get('errors', [])
        )


@dataclass
class EnhancedEntity:
    """Enhanced entity model with approval workflow and audit trail."""
    id: str
    name: str
    type: str
    attributes: Dict[str, Any] = field(default_factory=dict)
    status: EntityStatus = EntityStatus.PENDING
    approval_stage: ApprovalStage = ApprovalStage.INITIAL
    edit_history: List[AuditEntry] = field(default_factory=list)
    validation_results: Optional[ValidationResult] = None
    conflicts: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    source_text: Optional[str] = None
    confidence: float = 0.0
    
    def __post_init__(self):
        if isinstance(self.status, str):
            self.status = EntityStatus(self.status)
        if isinstance(self.approval_stage, str):
            self.approval_stage = ApprovalStage(self.approval_stage)
    
    def add_audit_entry(self, user: str, action: str, changes: Dict[str, Any], comment: Optional[str] = None):
        """Add an audit trail entry."""
        entry = AuditEntry(
            timestamp=datetime.now().isoformat(),
            user=user,
            action=action,
            changes=changes,
            comment=comment
        )
        self.edit_history.append(entry)
        self.updated_at = datetime.now().isoformat()
    
    def update_attributes(self, new_attributes: Dict[str, Any], user: str, comment: Optional[str] = None):
        """Update entity attributes with audit trail."""
        old_attributes = self.attributes.copy()
        self.attributes.update(new_attributes)
        
        changes = {
            'old_attributes': old_attributes,
            'new_attributes': self.attributes
        }
        
        self.add_audit_entry(user, 'edited', changes, comment)
        self.status = EntityStatus.EDITED
    
    def approve(self, user: str, stage: ApprovalStage = ApprovalStage.FINAL, comment: Optional[str] = None):
        """Approve the entity."""
        old_status = self.status.value
        self.status = EntityStatus.APPROVED
        self.approval_stage = stage
        
        changes = {
            'old_status': old_status,
            'new_status': self.status.value,
            'approval_stage': stage.value
        }
        
        self.add_audit_entry(user, 'approved', changes, comment)
    
    def reject(self, user: str, comment: Optional[str] = None):
        """Reject the entity."""
        old_status = self.status.value
        self.status = EntityStatus.REJECTED
        
        changes = {
            'old_status': old_status,
            'new_status': self.status.value
        }
        
        self.add_audit_entry(user, 'rejected', changes, comment)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type,
            'attributes': self.attributes,
            'status': self.status.value,
            'approval_stage': self.approval_stage.value,
            'edit_history': [entry.to_dict() for entry in self.edit_history],
            'validation_results': self.validation_results.to_dict() if self.validation_results else None,
            'conflicts': self.conflicts,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'source_text': self.source_text,
            'confidence': self.confidence
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EnhancedEntity':
        entity = cls(
            id=data['id'],
            name=data['name'],
            type=data['type'],
            attributes=data.get('attributes', {}),
            status=EntityStatus(data.get('status', 'pending')),
            approval_stage=ApprovalStage(data.get('approval_stage', 'initial')),
            conflicts=data.get('conflicts', []),
            created_at=data.get('created_at', datetime.now().isoformat()),
            updated_at=data.get('updated_at', datetime.now().isoformat()),
            source_text=data.get('source_text'),
            confidence=data.get('confidence', 0.0)
        )
        
        # Load edit history
        if 'edit_history' in data:
            entity.edit_history = [AuditEntry.from_dict(entry) for entry in data['edit_history']]
        
        # Load validation results
        if data.get('validation_results'):
            entity.validation_results = ValidationResult.from_dict(data['validation_results'])
        
        return entity


@dataclass
class EnhancedRelationship:
    """Enhanced relationship model with approval workflow and audit trail."""
    id: str
    source_entity_id: str
    target_entity_id: str
    relationship_type: str
    attributes: Dict[str, Any] = field(default_factory=dict)
    status: EntityStatus = EntityStatus.PENDING
    approval_stage: ApprovalStage = ApprovalStage.INITIAL
    edit_history: List[AuditEntry] = field(default_factory=list)
    validation_results: Optional[ValidationResult] = None
    conflicts: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    source_text: Optional[str] = None
    confidence: float = 0.0

    def __post_init__(self):
        if isinstance(self.status, str):
            self.status = EntityStatus(self.status)
        if isinstance(self.approval_stage, str):
            self.approval_stage = ApprovalStage(self.approval_stage)

    def add_audit_entry(self, user: str, action: str, changes: Dict[str, Any], comment: Optional[str] = None):
        """Add an audit trail entry."""
        entry = AuditEntry(
            timestamp=datetime.now().isoformat(),
            user=user,
            action=action,
            changes=changes,
            comment=comment
        )
        self.edit_history.append(entry)
        self.updated_at = datetime.now().isoformat()

    def update_attributes(self, new_attributes: Dict[str, Any], user: str, comment: Optional[str] = None):
        """Update relationship attributes with audit trail."""
        old_attributes = self.attributes.copy()
        self.attributes.update(new_attributes)

        changes = {
            'old_attributes': old_attributes,
            'new_attributes': self.attributes
        }

        self.add_audit_entry(user, 'edited', changes, comment)
        self.status = EntityStatus.EDITED

    def approve(self, user: str, stage: ApprovalStage = ApprovalStage.FINAL, comment: Optional[str] = None):
        """Approve the relationship."""
        old_status = self.status.value
        self.status = EntityStatus.APPROVED
        self.approval_stage = stage

        changes = {
            'old_status': old_status,
            'new_status': self.status.value,
            'approval_stage': stage.value
        }

        self.add_audit_entry(user, 'approved', changes, comment)

    def reject(self, user: str, comment: Optional[str] = None):
        """Reject the relationship."""
        old_status = self.status.value
        self.status = EntityStatus.REJECTED

        changes = {
            'old_status': old_status,
            'new_status': self.status.value
        }

        self.add_audit_entry(user, 'rejected', changes, comment)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'source_entity_id': self.source_entity_id,
            'target_entity_id': self.target_entity_id,
            'relationship_type': self.relationship_type,
            'attributes': self.attributes,
            'status': self.status.value,
            'approval_stage': self.approval_stage.value,
            'edit_history': [entry.to_dict() for entry in self.edit_history],
            'validation_results': self.validation_results.to_dict() if self.validation_results else None,
            'conflicts': self.conflicts,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'source_text': self.source_text,
            'confidence': self.confidence
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EnhancedRelationship':
        relationship = cls(
            id=data['id'],
            source_entity_id=data['source_entity_id'],
            target_entity_id=data['target_entity_id'],
            relationship_type=data['relationship_type'],
            attributes=data.get('attributes', {}),
            status=EntityStatus(data.get('status', 'pending')),
            approval_stage=ApprovalStage(data.get('approval_stage', 'initial')),
            conflicts=data.get('conflicts', []),
            created_at=data.get('created_at', datetime.now().isoformat()),
            updated_at=data.get('updated_at', datetime.now().isoformat()),
            source_text=data.get('source_text'),
            confidence=data.get('confidence', 0.0)
        )

        # Load edit history
        if 'edit_history' in data:
            relationship.edit_history = [AuditEntry.from_dict(entry) for entry in data['edit_history']]

        # Load validation results
        if data.get('validation_results'):
            relationship.validation_results = ValidationResult.from_dict(data['validation_results'])

        return relationship


@dataclass
class SessionStatistics:
    """Statistics for a staging session."""
    total_entities: int = 0
    total_relationships: int = 0
    approved_entities: int = 0
    approved_relationships: int = 0
    rejected_entities: int = 0
    rejected_relationships: int = 0
    pending_entities: int = 0
    pending_relationships: int = 0
    edited_entities: int = 0
    edited_relationships: int = 0
    conflicted_entities: int = 0
    conflicted_relationships: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            'total_entities': self.total_entities,
            'total_relationships': self.total_relationships,
            'approved_entities': self.approved_entities,
            'approved_relationships': self.approved_relationships,
            'rejected_entities': self.rejected_entities,
            'rejected_relationships': self.rejected_relationships,
            'pending_entities': self.pending_entities,
            'pending_relationships': self.pending_relationships,
            'edited_entities': self.edited_entities,
            'edited_relationships': self.edited_relationships,
            'conflicted_entities': self.conflicted_entities,
            'conflicted_relationships': self.conflicted_relationships
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SessionStatistics':
        return cls(
            total_entities=data.get('total_entities', 0),
            total_relationships=data.get('total_relationships', 0),
            approved_entities=data.get('approved_entities', 0),
            approved_relationships=data.get('approved_relationships', 0),
            rejected_entities=data.get('rejected_entities', 0),
            rejected_relationships=data.get('rejected_relationships', 0),
            pending_entities=data.get('pending_entities', 0),
            pending_relationships=data.get('pending_relationships', 0),
            edited_entities=data.get('edited_entities', 0),
            edited_relationships=data.get('edited_relationships', 0),
            conflicted_entities=data.get('conflicted_entities', 0),
            conflicted_relationships=data.get('conflicted_relationships', 0)
        )


@dataclass
class EnhancedStagingSession:
    """Enhanced staging session with comprehensive workflow support."""
    session_id: str
    document_title: str
    document_source: str
    status: SessionStatus = SessionStatus.PENDING_REVIEW
    workflow_stage: WorkflowStage = WorkflowStage.EXTRACTION
    entities: List[EnhancedEntity] = field(default_factory=list)
    relationships: List[EnhancedRelationship] = field(default_factory=list)
    statistics: SessionStatistics = field(default_factory=SessionStatistics)
    metadata: Dict[str, Any] = field(default_factory=dict)
    audit_trail: List[AuditEntry] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def __post_init__(self):
        if isinstance(self.status, str):
            self.status = SessionStatus(self.status)
        if isinstance(self.workflow_stage, str):
            self.workflow_stage = WorkflowStage(self.workflow_stage)

    def add_audit_entry(self, user: str, action: str, changes: Dict[str, Any], comment: Optional[str] = None):
        """Add an audit trail entry to the session."""
        entry = AuditEntry(
            timestamp=datetime.now().isoformat(),
            user=user,
            action=action,
            changes=changes,
            comment=comment
        )
        self.audit_trail.append(entry)
        self.updated_at = datetime.now().isoformat()

    def update_statistics(self):
        """Update session statistics based on current entities and relationships."""
        stats = SessionStatistics()

        # Count entities by status
        for entity in self.entities:
            stats.total_entities += 1
            if entity.status == EntityStatus.APPROVED:
                stats.approved_entities += 1
            elif entity.status == EntityStatus.REJECTED:
                stats.rejected_entities += 1
            elif entity.status == EntityStatus.EDITED:
                stats.edited_entities += 1
            elif entity.status == EntityStatus.CONFLICTED:
                stats.conflicted_entities += 1
            else:
                stats.pending_entities += 1

        # Count relationships by status
        for relationship in self.relationships:
            stats.total_relationships += 1
            if relationship.status == EntityStatus.APPROVED:
                stats.approved_relationships += 1
            elif relationship.status == EntityStatus.REJECTED:
                stats.rejected_relationships += 1
            elif relationship.status == EntityStatus.EDITED:
                stats.edited_relationships += 1
            elif relationship.status == EntityStatus.CONFLICTED:
                stats.conflicted_relationships += 1
            else:
                stats.pending_relationships += 1

        self.statistics = stats

    def get_entity_by_id(self, entity_id: str) -> Optional[EnhancedEntity]:
        """Get entity by ID."""
        for entity in self.entities:
            if entity.id == entity_id:
                return entity
        return None

    def get_relationship_by_id(self, relationship_id: str) -> Optional[EnhancedRelationship]:
        """Get relationship by ID."""
        for relationship in self.relationships:
            if relationship.id == relationship_id:
                return relationship
        return None

    def add_entity(self, entity: EnhancedEntity, user: str):
        """Add a new entity to the session."""
        self.entities.append(entity)
        self.add_audit_entry(user, 'entity_added', {'entity_id': entity.id, 'entity_name': entity.name})
        self.update_statistics()

    def add_relationship(self, relationship: EnhancedRelationship, user: str):
        """Add a new relationship to the session."""
        self.relationships.append(relationship)
        self.add_audit_entry(user, 'relationship_added', {
            'relationship_id': relationship.id,
            'source_entity_id': relationship.source_entity_id,
            'target_entity_id': relationship.target_entity_id,
            'relationship_type': relationship.relationship_type
        })
        self.update_statistics()

    def remove_entity(self, entity_id: str, user: str):
        """Remove an entity from the session."""
        entity = self.get_entity_by_id(entity_id)
        if entity:
            self.entities = [e for e in self.entities if e.id != entity_id]
            self.add_audit_entry(user, 'entity_removed', {'entity_id': entity_id, 'entity_name': entity.name})
            self.update_statistics()

    def remove_relationship(self, relationship_id: str, user: str):
        """Remove a relationship from the session."""
        relationship = self.get_relationship_by_id(relationship_id)
        if relationship:
            self.relationships = [r for r in self.relationships if r.id != relationship_id]
            self.add_audit_entry(user, 'relationship_removed', {'relationship_id': relationship_id})
            self.update_statistics()

    def to_dict(self) -> Dict[str, Any]:
        return {
            'session_id': self.session_id,
            'document_title': self.document_title,
            'document_source': self.document_source,
            'status': self.status.value,
            'workflow_stage': self.workflow_stage.value,
            'entities': [entity.to_dict() for entity in self.entities],
            'relationships': [relationship.to_dict() for relationship in self.relationships],
            'statistics': self.statistics.to_dict(),
            'metadata': self.metadata,
            'audit_trail': [entry.to_dict() for entry in self.audit_trail],
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EnhancedStagingSession':
        session = cls(
            session_id=data['session_id'],
            document_title=data['document_title'],
            document_source=data['document_source'],
            status=SessionStatus(data.get('status', 'pending_review')),
            workflow_stage=WorkflowStage(data.get('workflow_stage', 'extraction')),
            metadata=data.get('metadata', {}),
            created_at=data.get('created_at', datetime.now().isoformat()),
            updated_at=data.get('updated_at', datetime.now().isoformat())
        )

        # Load entities
        if 'entities' in data:
            session.entities = [EnhancedEntity.from_dict(entity_data) for entity_data in data['entities']]

        # Load relationships
        if 'relationships' in data:
            session.relationships = [EnhancedRelationship.from_dict(rel_data) for rel_data in data['relationships']]

        # Load statistics
        if 'statistics' in data:
            session.statistics = SessionStatistics.from_dict(data['statistics'])

        # Load audit trail
        if 'audit_trail' in data:
            session.audit_trail = [AuditEntry.from_dict(entry) for entry in data['audit_trail']]

        return session
