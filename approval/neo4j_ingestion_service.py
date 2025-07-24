"""
Neo4j ingestion service for approved entities.
Moves approved entities from pre-approval database to Neo4j.
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone

from dotenv import load_dotenv
import os
import neo4j

from .pre_approval_db import create_pre_approval_database

load_dotenv()

logger = logging.getLogger(__name__)


class Neo4jIngestionService:
    """Service for ingesting approved entities into Neo4j."""
    
    def __init__(self, 
                 neo4j_uri: str = None,
                 neo4j_user: str = None,
                 neo4j_password: str = None):
        """Initialize Neo4j ingestion service."""
        self.neo4j_uri = neo4j_uri or os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.neo4j_user = neo4j_user or os.getenv("NEO4J_USER", "neo4j")
        self.neo4j_password = neo4j_password or os.getenv("NEO4J_PASSWORD", "password")
        
        self.driver = None
        self.pre_db = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize the ingestion service."""
        if self._initialized:
            return
        
        try:
            # Initialize Neo4j driver
            self.driver = neo4j.GraphDatabase.driver(
                self.neo4j_uri,
                auth=(self.neo4j_user, self.neo4j_password)
            )
            
            # Test connection
            with self.driver.session() as session:
                session.run("RETURN 1")
            
            # Initialize pre-approval database
            self.pre_db = create_pre_approval_database()
            await self.pre_db.initialize()
            
            self._initialized = True
            logger.info("✅ Neo4j ingestion service initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Neo4j ingestion service: {e}")
            raise
    
    async def close(self):
        """Close the ingestion service."""
        if self.driver:
            self.driver.close()
        if self.pre_db:
            await self.pre_db.close()
        self._initialized = False
        logger.info("✅ Neo4j ingestion service closed")
    
    async def ingest_approved_entities(self, batch_size: int = 100) -> Dict[str, Any]:
        """Ingest approved entities from pre-approval database to Neo4j."""
        if not self._initialized:
            await self.initialize()
        
        try:
            # Get approved entities
            approved_entities = await self.pre_db.get_approved_entities()
            
            if not approved_entities:
                logger.info("ℹ️ No approved entities to ingest")
                return {
                    "entities_processed": 0,
                    "entities_ingested": 0,
                    "entities_failed": 0,
                    "errors": []
                }
            
            logger.info(f"📥 Processing {len(approved_entities)} approved entities")
            
            entities_ingested = 0
            entities_failed = 0
            errors = []
            
            # Process entities in batches
            for i in range(0, len(approved_entities), batch_size):
                batch = approved_entities[i:i + batch_size]
                
                for entity in batch:
                    try:
                        success = await self._ingest_single_entity(entity)
                        if success:
                            entities_ingested += 1
                            # Mark as ingested in pre-approval database
                            await self.pre_db.mark_entity_ingested(entity["entity_id"])
                        else:
                            entities_failed += 1
                            errors.append(f"Failed to ingest entity: {entity['name']}")
                            
                    except Exception as e:
                        entities_failed += 1
                        error_msg = f"Error ingesting entity {entity['name']}: {str(e)}"
                        errors.append(error_msg)
                        logger.error(error_msg)
            
            result = {
                "entities_processed": len(approved_entities),
                "entities_ingested": entities_ingested,
                "entities_failed": entities_failed,
                "errors": errors
            }
            
            logger.info(f"✅ Ingested {entities_ingested}/{len(approved_entities)} entities to Neo4j")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Failed to ingest approved entities: {e}")
            raise
    
    async def _ingest_single_entity(self, entity: Dict[str, Any]) -> bool:
        """Ingest a single entity into Neo4j."""
        try:
            entity_type = entity["entity_type"]
            entity_name = entity["name"]
            properties = entity["properties"]
            
            # Prepare properties for Neo4j
            neo4j_properties = {
                "name": entity_name,
                "approval_status": "approved",
                "ingestion_timestamp": datetime.now(timezone.utc).isoformat(),
                "source_document": entity.get("source_document", ""),
                "confidence_score": properties.get("confidence_score", 0.8),
                "extraction_timestamp": entity.get("extraction_timestamp", ""),
                "reviewer_id": entity.get("reviewer_id", ""),
                "review_timestamp": entity.get("review_timestamp", ""),
                "review_notes": entity.get("review_notes", "")
            }
            
            # Add custom properties from entity
            for key, value in properties.items():
                if key not in ["confidence_score"]:  # Skip internal properties
                    neo4j_properties[key] = value
            
            # Create Cypher query based on entity type
            with self.driver.session() as session:
                # Use MERGE to avoid duplicates
                cypher_query = f"""
                MERGE (n:{entity_type} {{name: $name}})
                SET n += $properties
                RETURN n.name as name
                """
                
                result = session.run(cypher_query, name=entity_name, properties=neo4j_properties)
                record = result.single()
                
                if record:
                    logger.debug(f"✅ Ingested {entity_type}: {entity_name}")
                    return True
                else:
                    logger.warning(f"⚠️ Failed to ingest {entity_type}: {entity_name}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Error ingesting entity {entity.get('name', 'unknown')}: {e}")
            return False
    
    async def ingest_approved_relationships(self, batch_size: int = 100) -> Dict[str, Any]:
        """Ingest approved relationships from pre-approval database to Neo4j."""
        if not self._initialized:
            await self.initialize()
        
        try:
            # Get approved relationships
            approved_relationships = await self.pre_db.get_entities(status_filter="approved")
            # Filter for relationships (this would need to be implemented in pre_approval_db)
            
            # For now, return empty result as relationship approval isn't fully implemented
            logger.info("ℹ️ Relationship ingestion not yet implemented")
            return {
                "relationships_processed": 0,
                "relationships_ingested": 0,
                "relationships_failed": 0,
                "errors": []
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to ingest approved relationships: {e}")
            raise
    
    async def get_ingestion_statistics(self) -> Dict[str, Any]:
        """Get ingestion statistics."""
        if not self._initialized:
            await self.initialize()
        
        try:
            pre_stats = await self.pre_db.get_statistics()
            
            # Get Neo4j statistics
            with self.driver.session() as session:
                result = session.run("""
                    MATCH (n)
                    WHERE n.approval_status = 'approved'
                    RETURN count(n) as total_approved_in_neo4j,
                           count(CASE WHEN n.ingestion_timestamp IS NOT NULL THEN 1 END) as recently_ingested
                """)
                record = result.single()
                neo4j_stats = {
                    "total_approved_in_neo4j": record["total_approved_in_neo4j"] if record else 0,
                    "recently_ingested": record["recently_ingested"] if record else 0
                }
            
            return {
                "pre_approval_stats": pre_stats,
                "neo4j_stats": neo4j_stats,
                "ingestion_ready": pre_stats["entities"]["approved"]
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get ingestion statistics: {e}")
            return {}
    
    async def auto_ingest_approved_entities(self) -> Dict[str, Any]:
        """Automatically ingest all approved entities that haven't been ingested yet."""
        if not self._initialized:
            await self.initialize()
        
        logger.info("🚀 Starting automatic ingestion of approved entities")
        
        try:
            result = await self.ingest_approved_entities()
            
            if result["entities_ingested"] > 0:
                logger.info(f"✅ Auto-ingestion completed: {result['entities_ingested']} entities added to Neo4j")
            else:
                logger.info("ℹ️ Auto-ingestion completed: No new entities to ingest")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Auto-ingestion failed: {e}")
            raise


# Factory function
def create_neo4j_ingestion_service(neo4j_uri: str = None,
                                 neo4j_user: str = None,
                                 neo4j_password: str = None) -> Neo4jIngestionService:
    """Create Neo4j ingestion service instance."""
    return Neo4jIngestionService(neo4j_uri, neo4j_user, neo4j_password)


# CLI for testing
async def main():
    """Test the Neo4j ingestion service."""
    service = create_neo4j_ingestion_service()
    
    try:
        await service.initialize()
        
        # Get statistics
        stats = await service.get_ingestion_statistics()
        print(f"Ingestion Statistics: {stats}")
        
        # Auto-ingest approved entities
        result = await service.auto_ingest_approved_entities()
        print(f"Ingestion Result: {result}")
        
    finally:
        await service.close()


if __name__ == "__main__":
    asyncio.run(main())