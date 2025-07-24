"""
Approval system for entity and relationship management.
Provides web-based approval workflows for LLM-extracted entities.
"""

from .schema_extensions import (
    ApprovalSchemaManager,
    ApprovalState,
    ApprovalSession,
    User,
    create_approval_schema_manager
)

from .approval_service import (
    EntityApprovalService,
    create_entity_approval_service
)

__version__ = "1.0.0"

__all__ = [
    "ApprovalSchemaManager",
    "ApprovalState", 
    "ApprovalSession",
    "User",
    "create_approval_schema_manager",
    "EntityApprovalService",
    "create_entity_approval_service"
]