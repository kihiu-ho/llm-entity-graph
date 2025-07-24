"""
Service for approving entities and ingesting them to Graphiti.
"""
import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime

from web_ui.database import get_db_session
from web_ui.models.pending_extractions import PendingDocument, PendingEntity, PendingRelationship
from ingestion.graph_builder import GraphBuilder
from ingestion.chunker import ChunkingConfig, create_chunker, DocumentChunk

logger = logging.getLogger(__name__)


class ApprovalService:
    """Service for approving entities and ingesting them to Graphiti."""
    
    def __init__(self):
        self.graph_builder = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize the approval service."""
        if not self._initialized:
            self.graph_builder = GraphBuilder()
            await self.graph_builder.initialize()
            self._initialized = True
            logger.info("✅ Approval service initialized")
    
    async def close(self):
        """Close the approval service."""
        if self._initialized and self.graph_builder:
            await self.graph_builder.close()
            self._initialized = False
    
    async def approve_document(self, document_id: int) -> Dict[str, Any]:
        """
        Approve a document and ingest approved entities to Graphiti.
        
        Args:
            document_id: ID of the document to approve
            
        Returns:
            Results of the ingestion process
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            logger.info(f"📋 Starting approval process for document ID: {document_id}")
            
            with get_db_session() as session:
                # Get document and its entities/relationships
                document = session.query(PendingDocument).filter(PendingDocument.id == document_id).first()
                if not document:
                    raise ValueError(f"Document with ID {document_id} not found")
                
                # Get approved entities and relationships
                approved_entities = session.query(PendingEntity).filter(
                    PendingEntity.document_id == document_id,
                    PendingEntity.approved == True
                ).all()
                
                approved_relationships = session.query(PendingRelationship).filter(
                    PendingRelationship.document_id == document_id,
                    PendingRelationship.approved == True
                ).all()
                
                logger.info(f"📊 Found {len(approved_entities)} approved entities and {len(approved_relationships)} approved relationships")
                
                # Convert to the format expected by GraphBuilder
                entities_dict = self._convert_to_entities_dict(approved_entities, approved_relationships)
                
                # Create chunks with the approved entities
                chunks = await self._create_chunks_with_entities(document, entities_dict)
                
                # Ingest to Graphiti
                results = await self.graph_builder.add_document_to_graph(
                    chunks=chunks,
                    document_title=document.filename,
                    document_source=f"approved_extraction_{document_id}",
                    document_metadata=document.metadata
                )
                
                # Update document status
                document.status = 'approved'
                document.updated_at = datetime.utcnow()
                session.commit()
                
                logger.info(f"✅ Successfully approved and ingested document: {document.filename}")
                
                return {
                    'success': True,
                    'document_id': document_id,
                    'filename': document.filename,
                    'approved_entities': len(approved_entities),
                    'approved_relationships': len(approved_relationships),
                    'graphiti_results': results
                }
                
        except Exception as e:
            logger.error(f"❌ Failed to approve document {document_id}: {e}")
            raise
    
    def _convert_to_entities_dict(self, entities: List[PendingEntity], relationships: List[PendingRelationship]) -> Dict[str, Any]:
        """Convert pending entities and relationships to the format expected by GraphBuilder."""
        entities_dict = {
            'companies': [],
            'people': [],
            'corporate_roles': {},
            'ownership': [],
            'transactions': [],
            'personal_connections': []
        }
        
        # Convert entities
        for entity in entities:
            if entity.entity_type == 'Company':
                entities_dict['companies'].append({
                    'name': entity.name,
                    **entity.properties
                })
            elif entity.entity_type == 'Person':
                entities_dict['people'].append({
                    'name': entity.name,
                    **entity.properties
                })
            elif entity.entity_type == 'Role':
                role_category = entity.properties.get('role_category', 'other_roles')
                if role_category not in entities_dict['corporate_roles']:
                    entities_dict['corporate_roles'][role_category] = []
                entities_dict['corporate_roles'][role_category].append({
                    'name': entity.name,
                    **entity.properties
                })
        
        # Convert relationships
        for relationship in relationships:
            if relationship.relationship_type == 'OWNS':
                entities_dict['ownership'].append({
                    'owner': relationship.source_entity,
                    'owned': relationship.target_entity,
                    **relationship.properties
                })
            elif relationship.relationship_type == 'TRANSACTION':
                entities_dict['transactions'].append({
                    'from': relationship.source_entity,
                    'to': relationship.target_entity,
                    **relationship.properties
                })
            elif relationship.relationship_type in ['CONNECTED_TO', 'RELATED_TO']:
                entities_dict['personal_connections'].append({
                    'person1': relationship.source_entity,
                    'person2': relationship.target_entity,
                    'relationship_type': relationship.relationship_type,
                    **relationship.properties
                })
        
        return entities_dict
    
    async def _create_chunks_with_entities(self, document: PendingDocument, entities_dict: Dict[str, Any]) -> List[DocumentChunk]:
        """Create document chunks with the approved entities."""
        # Create a single chunk with the document content and entities
        chunk = DocumentChunk(
            content=document.content,
            index=0,
            start_char=0,
            end_char=len(document.content),
            metadata={
                **document.metadata,
                'entities': entities_dict,
                'entity_extraction_date': datetime.now().isoformat(),
                'entity_extraction_scope': 'approved_review',
                'source_document_id': document.id
            },
            token_count=len(document.content.split())  # Rough token count
        )
        
        return [chunk]
    
    async def bulk_approve_entities(self, document_id: int, entity_ids: List[int]) -> Dict[str, Any]:
        """Bulk approve multiple entities."""
        try:
            with get_db_session() as session:
                updated_count = session.query(PendingEntity).filter(
                    PendingEntity.document_id == document_id,
                    PendingEntity.id.in_(entity_ids)
                ).update({'approved': True, 'updated_at': datetime.utcnow()})
                
                session.commit()
                
                logger.info(f"✅ Bulk approved {updated_count} entities for document {document_id}")
                
                return {
                    'success': True,
                    'updated_count': updated_count,
                    'entity_ids': entity_ids
                }
                
        except Exception as e:
            logger.error(f"❌ Failed to bulk approve entities: {e}")
            raise
    
    async def bulk_approve_relationships(self, document_id: int, relationship_ids: List[int]) -> Dict[str, Any]:
        """Bulk approve multiple relationships."""
        try:
            with get_db_session() as session:
                updated_count = session.query(PendingRelationship).filter(
                    PendingRelationship.document_id == document_id,
                    PendingRelationship.id.in_(relationship_ids)
                ).update({'approved': True, 'updated_at': datetime.utcnow()})
                
                session.commit()
                
                logger.info(f"✅ Bulk approved {updated_count} relationships for document {document_id}")
                
                return {
                    'success': True,
                    'updated_count': updated_count,
                    'relationship_ids': relationship_ids
                }
                
        except Exception as e:
            logger.error(f"❌ Failed to bulk approve relationships: {e}")
            raise


# Global service instance
approval_service = ApprovalService()
