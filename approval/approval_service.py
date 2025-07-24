"""
Core approval service for entity and relationship management.
Integrates with the existing graph builder to provide approval workflows.
"""

import logging
import uuid
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timezone

from .schema_extensions import (
    ApprovalSchemaManager, ApprovalState, ApprovalSession, User,
    create_approval_schema_manager
)

logger = logging.getLogger(__name__)


class EntityApprovalService:
    """Service for managing entity and relationship approval workflows."""
    
    def __init__(self, neo4j_uri: str = "neo4j://localhost:7687",
                 neo4j_user: str = "neo4j", neo4j_password: str = "password"):
        """Initialize approval service."""
        self.schema_manager = create_approval_schema_manager(
            neo4j_uri, neo4j_user, neo4j_password
        )
        self._initialized = False
    
    async def initialize(self):
        """Initialize the approval service."""
        if not self._initialized:
            await self.schema_manager.initialize()
            self._initialized = True
            logger.info("✅ Entity approval service initialized")
    
    async def close(self):
        """Close the approval service."""
        if self._initialized:
            await self.schema_manager.close()
            self._initialized = False
    
    async def create_approval_session(self, document_title: str, 
                                    document_source: str,
                                    reviewer_id: Optional[str] = None,
                                    auto_created: bool = False) -> str:
        """Create a new approval session for a document."""
        if not self._initialized:
            await self.initialize()
        
        session_id = str(uuid.uuid4())
        
        # Count total entities needing approval
        pending_entities = await self.schema_manager.get_pending_entities(document_source)
        total_entities = len(pending_entities)
        
        session = ApprovalSession(
            session_id=session_id,
            document_title=document_title,
            document_source=document_source,
            status="in_progress",
            created_timestamp=datetime.now(timezone.utc),
            reviewer_id=reviewer_id,
            total_entities=total_entities,
            approved_entities=0,
            rejected_entities=0,
            modified_entities=0
        )
        
        await self.schema_manager.create_approval_session(session)
        
        logger.info(f"✅ Created approval session {session_id} for document: {document_title}")
        logger.info(f"   Total entities to review: {total_entities}")
        
        return session_id
    
    async def get_entities_for_approval(self, document_source: str, 
                                      entity_types: Optional[List[str]] = None,
                                      status_filter: str = "pending") -> List[Dict[str, Any]]:
        """Get entities that need approval for a document."""
        if not self._initialized:
            await self.initialize()
        
        # Get all pending entities from the document
        entities = await self.schema_manager.get_pending_entities(document_source)
        
        # Filter by entity type if specified
        if entity_types:
            entities = [e for e in entities if e["entity_type"] in entity_types]
        
        # Filter by status
        if status_filter != "all":
            entities = [e for e in entities if e.get("approval_status") == status_filter]
        
        # Enrich entities with approval context
        enriched_entities = []
        for entity in entities:
            enriched_entity = {
                **entity,
                "entity_id": entity["name"],  # Use name as entity_id for now
                "display_name": entity["name"],
                "confidence_score": entity["properties"].get("confidence_score", 0.8),
                "extracted_properties": self._format_entity_properties(entity["properties"]),
                "needs_review": entity["properties"].get("needs_review", True),
                "review_priority": self._calculate_review_priority(entity)
            }
            enriched_entities.append(enriched_entity)
        
        # Sort by review priority and extraction timestamp
        enriched_entities.sort(
            key=lambda x: (x["review_priority"], x["extraction_timestamp"]), 
            reverse=True
        )
        
        logger.info(f"Retrieved {len(enriched_entities)} entities for approval from {document_source}")
        return enriched_entities
    
    async def get_relationships_for_approval(self, document_source: str,
                                           status_filter: str = "pending") -> List[Dict[str, Any]]:
        """Get relationships that need approval for a document."""
        if not self._initialized:
            await self.initialize()
        
        # Query Neo4j for relationships from the document
        with self.schema_manager.driver.session() as session:
            result = session.run("""
                MATCH (source)-[r]->(target)
                WHERE r.source_document = $document_source
                  AND (r.approval_status = $status_filter OR $status_filter = 'all')
                RETURN type(r) as relationship_type,
                       source.name as source_name,
                       target.name as target_name,
                       labels(source) as source_type,
                       labels(target) as target_type,
                       r.source_document as source_document,
                       r.extraction_timestamp as extraction_timestamp,
                       r.approval_status as approval_status,
                       properties(r) as properties
                ORDER BY r.extraction_timestamp DESC
            """, document_source=document_source, status_filter=status_filter)
            
            relationships = []
            for record in result:
                relationship = {
                    "relationship_id": f"{record['source_name']}-{record['relationship_type']}-{record['target_name']}",
                    "relationship_type": record["relationship_type"],
                    "source_entity": {
                        "name": record["source_name"],
                        "type": record["source_type"][0] if record["source_type"] else "Unknown"
                    },
                    "target_entity": {
                        "name": record["target_name"],
                        "type": record["target_type"][0] if record["target_type"] else "Unknown"
                    },
                    "source_document": record["source_document"],
                    "extraction_timestamp": record["extraction_timestamp"],
                    "approval_status": record["approval_status"],
                    "properties": record["properties"],
                    "confidence_score": record["properties"].get("confidence_score", 0.8),
                    "needs_review": record["properties"].get("needs_review", True)
                }
                relationships.append(relationship)
        
        logger.info(f"Retrieved {len(relationships)} relationships for approval from {document_source}")
        return relationships
    
    async def approve_entity(self, entity_id: str, reviewer_id: str,
                           review_notes: Optional[str] = None,
                           modified_data: Optional[Dict[str, Any]] = None) -> bool:
        """Approve an entity, optionally with modifications."""
        if not self._initialized:
            await self.initialize()
        
        status = "approved" if not modified_data else "modified"
        
        success = await self.schema_manager.update_entity_approval_status(
            entity_id=entity_id,
            status=status,
            reviewer_id=reviewer_id,
            review_notes=review_notes,
            modified_data=modified_data
        )
        
        if success:
            # Create approval state record
            approval_state = ApprovalState(
                entity_id=entity_id,
                entity_type="Entity",  # Will be determined from Neo4j
                status=status,
                reviewer_id=reviewer_id,
                review_timestamp=datetime.now(timezone.utc),
                original_data={},  # Will be populated from Neo4j
                modified_data=modified_data,
                review_notes=review_notes,
                source_document="",  # Will be populated from Neo4j
                extraction_timestamp=datetime.now(timezone.utc)
            )
            
            try:
                await self.schema_manager.create_approval_state(approval_state)
            except Exception as e:
                logger.warning(f"Failed to create approval state record: {e}")
        
        return success
    
    async def reject_entity(self, entity_id: str, reviewer_id: str,
                          review_notes: str) -> bool:
        """Reject an entity with reasoning."""
        if not self._initialized:
            await self.initialize()
        
        success = await self.schema_manager.update_entity_approval_status(
            entity_id=entity_id,
            status="rejected",
            reviewer_id=reviewer_id,
            review_notes=review_notes
        )
        
        if success:
            logger.info(f"✅ Rejected entity: {entity_id}")
        
        return success
    
    async def get_latest_entities(self, limit: int = 100, 
                                entity_types: Optional[List[str]] = None,
                                status_filter: str = "pending") -> List[Dict[str, Any]]:
        """Get most recently ingested entities without session requirement."""
        if not self._initialized:
            await self.initialize()
        
        try:
            entities = await self.schema_manager.get_latest_entities(
                limit=limit,
                entity_types=entity_types,
                status_filter=status_filter
            )
            logger.info(f"📋 Retrieved {len(entities)} latest entities")
            return entities
        except Exception as e:
            logger.error(f"❌ Failed to get latest entities: {e}")
            return []
    
    async def auto_create_session_from_ingestion(self, 
                                               document_sources: List[str],
                                               ingestion_batch_id: str) -> Optional[str]:
        """Auto-create approval session from ingestion completion."""
        if not self._initialized:
            await self.initialize()
        
        try:
            # Create session for the most recently processed document
            primary_source = document_sources[0] if document_sources else "batch_" + ingestion_batch_id
            
            session_id = await self.create_approval_session(
                document_title=f"Auto-generated from ingestion {ingestion_batch_id}",
                document_source=primary_source,
                reviewer_id="system",
                auto_created=True
            )
            
            logger.info(f"🤖 Auto-created approval session: {session_id}")
            return session_id
            
        except Exception as e:
            logger.error(f"❌ Failed to auto-create approval session: {e}")
            return None
    
    async def approve_relationship(self, relationship_id: str, reviewer_id: str,
                                 review_notes: Optional[str] = None) -> bool:
        """Approve a relationship."""
        if not self._initialized:
            await self.initialize()
        
        # Parse relationship ID to get source, type, target
        parts = relationship_id.split("-", 2)
        if len(parts) != 3:
            logger.error(f"Invalid relationship ID format: {relationship_id}")
            return False
        
        source_name, rel_type, target_name = parts
        
        with self.schema_manager.driver.session() as session:
            result = session.run("""
                MATCH (source {name: $source_name})-[r:`{}`]->(target {name: $target_name})
                SET r.approval_status = 'approved',
                    r.reviewer_id = $reviewer_id,
                    r.review_timestamp = datetime(),
                    r.review_notes = $review_notes,
                    r.needs_review = false
                RETURN count(r) as updated_count
            """.replace('`{}`', f'`{rel_type}`'),
                source_name=source_name,
                target_name=target_name,
                reviewer_id=reviewer_id,
                review_notes=review_notes
            )
            
            record = result.single()
            updated_count = record["updated_count"] if record else 0
            
            if updated_count > 0:
                logger.info(f"✅ Approved relationship: {relationship_id}")
                return True
            else:
                logger.warning(f"No relationship found with ID: {relationship_id}")
                return False
    
    async def reject_relationship(self, relationship_id: str, reviewer_id: str,
                                review_notes: str) -> bool:
        """Reject a relationship with reasoning."""
        if not self._initialized:
            await self.initialize()
        
        # Parse relationship ID to get source, type, target
        parts = relationship_id.split("-", 2)
        if len(parts) != 3:
            logger.error(f"Invalid relationship ID format: {relationship_id}")
            return False
        
        source_name, rel_type, target_name = parts
        
        with self.schema_manager.driver.session() as session:
            result = session.run("""
                MATCH (source {name: $source_name})-[r:`{}`]->(target {name: $target_name})
                SET r.approval_status = 'rejected',
                    r.reviewer_id = $reviewer_id,
                    r.review_timestamp = datetime(),
                    r.review_notes = $review_notes,
                    r.needs_review = false
                RETURN count(r) as updated_count
            """.replace('`{}`', f'`{rel_type}`'),
                source_name=source_name,
                target_name=target_name,
                reviewer_id=reviewer_id,
                review_notes=review_notes
            )
            
            record = result.single()
            updated_count = record["updated_count"] if record else 0
            
            if updated_count > 0:
                logger.info(f"❌ Rejected relationship: {relationship_id}")
                return True
            else:
                logger.warning(f"No relationship found with ID: {relationship_id}")
                return False
    
    async def bulk_approve_entities(self, entity_ids: List[str], reviewer_id: str,
                                  review_notes: Optional[str] = None) -> Dict[str, bool]:
        """Bulk approve multiple entities."""
        if not self._initialized:
            await self.initialize()
        
        results = {}
        for entity_id in entity_ids:
            try:
                success = await self.approve_entity(
                    entity_id=entity_id,
                    reviewer_id=reviewer_id,
                    review_notes=review_notes
                )
                results[entity_id] = success
            except Exception as e:
                logger.error(f"Failed to approve entity {entity_id}: {e}")
                results[entity_id] = False
        
        successful_count = sum(1 for success in results.values() if success)
        logger.info(f"✅ Bulk approved {successful_count}/{len(entity_ids)} entities")
        
        return results
    
    async def get_approval_session_status(self, session_id: str) -> Dict[str, Any]:
        """Get the current status of an approval session."""
        if not self._initialized:
            await self.initialize()
        
        stats = await self.schema_manager.get_approval_session_stats(session_id)
        
        if not stats:
            logger.warning(f"No approval session found with ID: {session_id}")
            return {}
        
        # Add progress indicators
        stats["progress_percentage"] = stats.get("completion_percentage", 0)
        stats["remaining_entities"] = stats["pending_count"]
        stats["is_complete"] = stats["pending_count"] == 0
        
        return stats
    
    async def search_entities(self, document_source: str, search_query: str,
                            entity_types: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Search entities by name or properties."""
        if not self._initialized:
            await self.initialize()
        
        # Build search query
        type_filter = ""
        if entity_types:
            type_filter = "AND (" + " OR ".join([f"'{t}' IN labels(n)" for t in entity_types]) + ")"
        
        with self.schema_manager.driver.session() as session:
            result = session.run(f"""
                MATCH (n)
                WHERE n.source_document = $document_source
                  AND (n.name CONTAINS $search_query 
                       OR any(prop IN keys(n) WHERE toString(n[prop]) CONTAINS $search_query))
                  {type_filter}
                RETURN labels(n) as entity_type,
                       n.name as name,
                       n.approval_status as approval_status,
                       properties(n) as properties
                ORDER BY n.name
                LIMIT 50
            """, document_source=document_source, search_query=search_query)
            
            entities = []
            for record in result:
                entity = {
                    "entity_type": record["entity_type"][0] if record["entity_type"] else "Unknown",
                    "name": record["name"],
                    "approval_status": record["approval_status"],
                    "properties": record["properties"]
                }
                entities.append(entity)
        
        logger.info(f"Found {len(entities)} entities matching search: {search_query}")
        return entities
    
    async def get_approval_statistics(self, document_source: Optional[str] = None) -> Dict[str, Any]:
        """Get overall approval statistics."""
        if not self._initialized:
            await self.initialize()
        
        with self.schema_manager.driver.session() as session:
            # Build query based on whether document_source is provided
            base_query = "MATCH (n)"
            params = {}
            
            if document_source:
                base_query += " WHERE n.source_document = $document_source"
                params["document_source"] = document_source
            
            result = session.run(f"""
                {base_query}
                RETURN count(n) as total_entities,
                       count(CASE WHEN n.approval_status = 'approved' THEN 1 END) as approved_count,
                       count(CASE WHEN n.approval_status = 'rejected' THEN 1 END) as rejected_count,
                       count(CASE WHEN n.approval_status = 'pending' THEN 1 END) as pending_count,
                       count(CASE WHEN n.approval_status = 'modified' THEN 1 END) as modified_count
            """, params)
            
            record = result.single()
            if not record:
                return {}
            
            total = record["total_entities"]
            approved = record["approved_count"]
            rejected = record["rejected_count"]
            pending = record["pending_count"]
            modified = record["modified_count"]
            
            return {
                "total_entities": total,
                "approved_count": approved,
                "rejected_count": rejected,
                "pending_count": pending,
                "modified_count": modified,
                "completion_percentage": ((approved + rejected + modified) / total * 100) if total > 0 else 0,
                "approval_rate": (approved / (approved + rejected) * 100) if (approved + rejected) > 0 else 0
            }
    
    def _format_entity_properties(self, properties: Dict[str, Any]) -> Dict[str, Any]:
        """Format entity properties for display."""
        formatted = {}
        
        # Skip internal properties
        skip_props = {"approval_status", "needs_review", "reviewer_id", "review_timestamp", 
                     "review_notes", "extraction_timestamp", "source_document"}
        
        for key, value in properties.items():
            if key not in skip_props and value is not None:
                formatted[key] = value
        
        return formatted
    
    def _calculate_review_priority(self, entity: Dict[str, Any]) -> int:
        """Calculate review priority for an entity (higher = more important)."""
        priority = 0
        
        # Higher priority for lower confidence scores
        confidence = entity["properties"].get("confidence_score", 0.8)
        if confidence < 0.5:
            priority += 3
        elif confidence < 0.7:
            priority += 2
        elif confidence < 0.9:
            priority += 1
        
        # Higher priority for certain entity types
        if entity["entity_type"] == "Person":
            priority += 2
        elif entity["entity_type"] == "Company":
            priority += 1
        
        # Higher priority for entities with more properties (likely more important)
        prop_count = len(entity["properties"])
        if prop_count > 5:
            priority += 2
        elif prop_count > 3:
            priority += 1
        
        return priority


# Factory function
def create_entity_approval_service(neo4j_uri: str = "neo4j://localhost:7687",
                                 neo4j_user: str = "neo4j", 
                                 neo4j_password: str = "password") -> EntityApprovalService:
    """Create entity approval service instance."""
    return EntityApprovalService(neo4j_uri, neo4j_user, neo4j_password)