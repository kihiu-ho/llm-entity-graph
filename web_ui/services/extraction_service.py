"""
Service for extracting entities without immediately ingesting to Graphiti.
"""
import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime

from web_ui.database import get_db_session
from web_ui.models.pending_extractions import PendingDocument, PendingEntity, PendingRelationship
from ingestion.graph_builder import GraphBuilder
from ingestion.chunker import ChunkingConfig, create_chunker

logger = logging.getLogger(__name__)


class ExtractionService:
    """Service for extracting entities and storing them for review."""
    
    def __init__(self):
        self.graph_builder = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize the extraction service."""
        if not self._initialized:
            self.graph_builder = GraphBuilder()
            await self.graph_builder.initialize()
            self._initialized = True
            logger.info("✅ Extraction service initialized")
    
    async def close(self):
        """Close the extraction service."""
        if self._initialized and self.graph_builder:
            await self.graph_builder.close()
            self._initialized = False
    
    async def extract_entities_from_file(
        self,
        filename: str,
        content: str,
        chunk_size: int = 8000,
        chunk_overlap: int = 800,
        use_semantic: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Extract entities from a file and store them for review.
        
        Args:
            filename: Name of the file
            content: File content
            chunk_size: Size of chunks for processing
            chunk_overlap: Overlap between chunks
            use_semantic: Whether to use semantic chunking
            metadata: Additional metadata
            
        Returns:
            Document ID of the stored extraction
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            logger.info(f"🔍 Starting entity extraction for file: {filename}")
            
            # Create chunks
            chunker_config = ChunkingConfig(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                use_semantic_splitting=use_semantic
            )
            chunker = create_chunker(chunker_config)
            chunks = await chunker.chunk_text(content, filename)
            
            logger.info(f"📄 Created {len(chunks)} chunks for processing")
            
            # Extract entities using GraphBuilder
            enriched_chunks = await self.graph_builder.extract_entities_from_document(
                chunks,
                extract_companies=True,
                extract_people=True,
                extract_financial_entities=True,
                extract_corporate_roles=True,
                extract_ownership=True,
                extract_transactions=True,
                extract_personal_connections=True,
                use_llm=True,
                use_llm_for_companies=True,
                use_llm_for_people=True,
                use_llm_for_financial_entities=True,
                use_llm_for_corporate_roles=True,
                use_llm_for_ownership=True,
                use_llm_for_transactions=True,
                use_llm_for_personal_connections=True
            )
            
            # Combine entities from all chunks (they should be the same due to document-level extraction)
            combined_entities = {}
            if enriched_chunks:
                # Get entities from the first chunk (all chunks have the same entities)
                chunk_metadata = enriched_chunks[0].metadata
                if 'entities' in chunk_metadata:
                    combined_entities = chunk_metadata['entities']
            
            logger.info(f"🎯 Extracted entities: {self._count_entities(combined_entities)}")
            
            # Store in database for review
            document_id = await self._store_extraction(filename, content, combined_entities, metadata)
            
            logger.info(f"💾 Stored extraction with document ID: {document_id}")
            return document_id
            
        except Exception as e:
            logger.error(f"❌ Failed to extract entities from {filename}: {e}")
            raise
    
    def _count_entities(self, entities: Dict[str, Any]) -> Dict[str, int]:
        """Count entities by type."""
        counts = {}
        for entity_type, entity_list in entities.items():
            if isinstance(entity_list, list):
                counts[entity_type] = len(entity_list)
            elif isinstance(entity_list, dict):
                # Handle nested structures like corporate_roles
                if entity_type == 'corporate_roles':
                    total = 0
                    for role_category, roles in entity_list.items():
                        if isinstance(roles, list):
                            total += len(roles)
                    counts[entity_type] = total
                else:
                    counts[entity_type] = len(entity_list)
            else:
                counts[entity_type] = 1 if entity_list else 0
        return counts
    
    async def _store_extraction(
        self,
        filename: str,
        content: str,
        entities: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """Store extracted entities in the database for review."""
        try:
            with get_db_session() as session:
                # Create document record
                document = PendingDocument(
                    filename=filename,
                    content=content,
                    metadata=metadata or {},
                    extraction_date=datetime.utcnow(),
                    status='pending'
                )
                session.add(document)
                session.flush()  # Get the document ID
                
                # Store entities
                await self._store_entities(session, document.id, entities)
                
                # Store relationships
                await self._store_relationships(session, document.id, entities)
                
                session.commit()
                return document.id
                
        except Exception as e:
            logger.error(f"Failed to store extraction: {e}")
            raise
    
    async def _store_entities(self, session, document_id: int, entities: Dict[str, Any]):
        """Store individual entities."""
        # Store companies
        if 'companies' in entities:
            for company in entities['companies']:
                if isinstance(company, dict):
                    entity = PendingEntity(
                        document_id=document_id,
                        entity_type='Company',
                        name=company.get('name', ''),
                        properties=company
                    )
                else:
                    entity = PendingEntity(
                        document_id=document_id,
                        entity_type='Company',
                        name=str(company),
                        properties={}
                    )
                session.add(entity)
        
        # Store people
        if 'people' in entities:
            for person in entities['people']:
                if isinstance(person, dict):
                    entity = PendingEntity(
                        document_id=document_id,
                        entity_type='Person',
                        name=person.get('name', ''),
                        properties=person
                    )
                else:
                    entity = PendingEntity(
                        document_id=document_id,
                        entity_type='Person',
                        name=str(person),
                        properties={}
                    )
                session.add(entity)
        
        # Store corporate roles
        if 'corporate_roles' in entities:
            roles_data = entities['corporate_roles']
            if isinstance(roles_data, dict):
                for role_category, roles in roles_data.items():
                    if isinstance(roles, list):
                        for role in roles:
                            if isinstance(role, dict):
                                entity = PendingEntity(
                                    document_id=document_id,
                                    entity_type='Role',
                                    name=role.get('name', ''),
                                    properties={
                                        **role,
                                        'role_category': role_category
                                    }
                                )
                                session.add(entity)
    
    async def _store_relationships(self, session, document_id: int, entities: Dict[str, Any]):
        """Store relationships between entities."""
        # Store ownership relationships
        if 'ownership' in entities:
            for ownership in entities['ownership']:
                if isinstance(ownership, dict):
                    relationship = PendingRelationship(
                        document_id=document_id,
                        source_entity=ownership.get('owner', ''),
                        target_entity=ownership.get('owned', ''),
                        relationship_type='OWNS',
                        properties=ownership
                    )
                    session.add(relationship)
        
        # Store transactions
        if 'transactions' in entities:
            for transaction in entities['transactions']:
                if isinstance(transaction, dict):
                    relationship = PendingRelationship(
                        document_id=document_id,
                        source_entity=transaction.get('from', ''),
                        target_entity=transaction.get('to', ''),
                        relationship_type='TRANSACTION',
                        properties=transaction
                    )
                    session.add(relationship)
        
        # Store personal connections
        if 'personal_connections' in entities:
            for connection in entities['personal_connections']:
                if isinstance(connection, dict):
                    relationship = PendingRelationship(
                        document_id=document_id,
                        source_entity=connection.get('person1', ''),
                        target_entity=connection.get('person2', ''),
                        relationship_type=connection.get('relationship_type', 'CONNECTED_TO'),
                        properties=connection
                    )
                    session.add(relationship)


# Global service instance
extraction_service = ExtractionService()
