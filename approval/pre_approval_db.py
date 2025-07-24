"""
Pre-approval database for storing extracted entities before Neo4j ingestion.
Stores entities in PostgreSQL until they are reviewed and approved.
"""

import logging
import uuid
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
import asyncio
import threading

import asyncpg
from dotenv import load_dotenv
import os

load_dotenv()

logger = logging.getLogger(__name__)


class PreApprovalDatabase:
    """Database for storing entities before they are approved and moved to Neo4j."""
    
    def __init__(self, database_url: Optional[str] = None):
        """Initialize pre-approval database."""
        self.database_url = database_url or os.getenv('DATABASE_URL')
        if not self.database_url:
            raise ValueError("DATABASE_URL environment variable is required")
        
        self.pool = None
        self._initialized = False
        self._initialization_lock = threading.Lock()
    
    async def initialize(self):
        """Initialize database connection and create tables."""
        # Fast path: if already initialized, return immediately
        if self._initialized and self.pool:
            return
        
        # Use a simple flag-based approach to prevent concurrent initialization
        if hasattr(self, '_initializing') and self._initializing:
            # Wait for ongoing initialization to complete
            while self._initializing:
                await asyncio.sleep(0.1)
            return
        
        self._initializing = True
        
        try:
            # Double check after setting the flag
            if self._initialized and self.pool:
                return
            
            # Create connection pool with better configuration
            self.pool = await asyncpg.create_pool(
                self.database_url,
                min_size=1,
                max_size=10,
                command_timeout=60,
                server_settings={
                    'application_name': 'llm_entity_graph_preapproval',
                    'jit': 'off'  # Disable JIT for better stability
                }
            )
            
            # Create tables
            await self._create_tables()
            
            self._initialized = True
            logger.info("✅ Pre-approval database initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize pre-approval database: {e}")
            # Clean up on failure
            if hasattr(self, 'pool') and self.pool:
                try:
                    await self.pool.close()
                except Exception as cleanup_error:
                    logger.warning(f"⚠️ Error during pool cleanup: {cleanup_error}")
                self.pool = None
            self._initialized = False
            raise
        finally:
            self._initializing = False
    
    async def close(self):
        """Close database connections."""
        if self.pool:
            try:
                await self.pool.close()
                logger.info("✅ Pre-approval database connections closed")
            except Exception as e:
                logger.warning(f"⚠️ Error closing database pool: {e}")
            finally:
                self.pool = None
                self._initialized = False
    
    async def _create_tables(self):
        """Create pre-approval tables."""
        async with self.pool.acquire() as conn:
            # Create pre_approval_entities table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS pre_approval_entities (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    name VARCHAR(500) NOT NULL,
                    entity_type VARCHAR(100) NOT NULL,
                    properties JSONB NOT NULL DEFAULT '{}',
                    confidence_score FLOAT DEFAULT 0.8,
                    source_document VARCHAR(1000) NOT NULL,
                    extraction_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    approval_status VARCHAR(50) DEFAULT 'pending',
                    reviewer_id VARCHAR(100),
                    review_timestamp TIMESTAMP WITH TIME ZONE,
                    review_notes TEXT,
                    ingestion_batch_id VARCHAR(100),
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            """)
            
            # Create pre_approval_relationships table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS pre_approval_relationships (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    source_entity_id UUID REFERENCES pre_approval_entities(id) ON DELETE CASCADE,
                    target_entity_id UUID REFERENCES pre_approval_entities(id) ON DELETE CASCADE,
                    relationship_type VARCHAR(100) NOT NULL,
                    properties JSONB NOT NULL DEFAULT '{}',
                    confidence_score FLOAT DEFAULT 0.8,
                    source_document VARCHAR(1000) NOT NULL,
                    extraction_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    approval_status VARCHAR(50) DEFAULT 'pending',
                    reviewer_id VARCHAR(100),
                    review_timestamp TIMESTAMP WITH TIME ZONE,
                    review_notes TEXT,
                    ingestion_batch_id VARCHAR(100),
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            """)
            
            # Create indexes for performance
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_pre_entities_name ON pre_approval_entities(name);
                CREATE INDEX IF NOT EXISTS idx_pre_entities_type ON pre_approval_entities(entity_type);
                CREATE INDEX IF NOT EXISTS idx_pre_entities_status ON pre_approval_entities(approval_status);
                CREATE INDEX IF NOT EXISTS idx_pre_entities_source ON pre_approval_entities(source_document);
                CREATE INDEX IF NOT EXISTS idx_pre_entities_batch ON pre_approval_entities(ingestion_batch_id);
                CREATE INDEX IF NOT EXISTS idx_pre_relationships_type ON pre_approval_relationships(relationship_type);
                CREATE INDEX IF NOT EXISTS idx_pre_relationships_status ON pre_approval_relationships(approval_status);
            """)
            
            # Create trigger to update updated_at timestamp
            await conn.execute("""
                CREATE OR REPLACE FUNCTION update_updated_at()
                RETURNS TRIGGER AS $$
                BEGIN
                    NEW.updated_at = NOW();
                    RETURN NEW;
                END;
                $$ LANGUAGE plpgsql;
            """)
            
            await conn.execute("""
                DROP TRIGGER IF EXISTS update_pre_entities_updated_at ON pre_approval_entities;
                CREATE TRIGGER update_pre_entities_updated_at
                    BEFORE UPDATE ON pre_approval_entities
                    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
            """)
            
            await conn.execute("""
                DROP TRIGGER IF EXISTS update_pre_relationships_updated_at ON pre_approval_relationships;
                CREATE TRIGGER update_pre_relationships_updated_at
                    BEFORE UPDATE ON pre_approval_relationships
                    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
            """)
            
            logger.info("✅ Pre-approval database tables created")
    
    async def store_entity(self, 
                          name: str,
                          entity_type: str,
                          properties: Dict[str, Any],
                          confidence_score: float = 0.8,
                          source_document: str = "",
                          ingestion_batch_id: Optional[str] = None) -> str:
        """Store an entity in pre-approval database."""
        if not self._initialized:
            await self.initialize()
        
        async with self.pool.acquire() as conn:
            entity_id = await conn.fetchval("""
                INSERT INTO pre_approval_entities 
                (name, entity_type, properties, confidence_score, source_document, ingestion_batch_id)
                VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING id
            """, name, entity_type, json.dumps(properties), confidence_score, source_document, ingestion_batch_id)
            
            logger.debug(f"📦 Stored entity '{name}' with ID {entity_id}")
            return str(entity_id)
    
    async def store_relationship(self,
                               source_entity_id: str,
                               target_entity_id: str,
                               relationship_type: str,
                               properties: Dict[str, Any],
                               confidence_score: float = 0.8,
                               source_document: str = "",
                               ingestion_batch_id: Optional[str] = None) -> str:
        """Store a relationship in pre-approval database."""
        if not self._initialized:
            await self.initialize()
        
        async with self.pool.acquire() as conn:
            relationship_id = await conn.fetchval("""
                INSERT INTO pre_approval_relationships 
                (source_entity_id, target_entity_id, relationship_type, properties, 
                 confidence_score, source_document, ingestion_batch_id)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING id
            """, source_entity_id, target_entity_id, relationship_type, 
                json.dumps(properties), confidence_score, source_document, ingestion_batch_id)
            
            logger.debug(f"🔗 Stored relationship '{relationship_type}' with ID {relationship_id}")
            return str(relationship_id)
    
    async def get_entities(self, 
                          status_filter: str = "pending",
                          entity_types: Optional[List[str]] = None,
                          source_document: Optional[str] = None,
                          limit: int = 100) -> List[Dict[str, Any]]:
        """Get entities from pre-approval database."""
        if not self._initialized:
            await self.initialize()
        
        if not self.pool:
            raise RuntimeError("Database connection pool is not available")
        
        # Build query conditions
        conditions = ["approval_status = $1"]
        params = [status_filter]
        param_count = 1
        
        if entity_types:
            param_count += 1
            conditions.append(f"entity_type = ANY(${param_count})")
            params.append(entity_types)
        
        if source_document:
            param_count += 1
            conditions.append(f"source_document = ${param_count}")
            params.append(source_document)
        
        param_count += 1
        params.append(limit)
        
        query = f"""
            SELECT id, name, entity_type, properties, confidence_score, 
                   source_document, extraction_timestamp, approval_status,
                   reviewer_id, review_timestamp, review_notes, ingestion_batch_id
            FROM pre_approval_entities
            WHERE {' AND '.join(conditions)}
            ORDER BY extraction_timestamp DESC
            LIMIT ${param_count}
        """
        
        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(query, *params)
                
                entities = []
                for row in rows:
                    properties = json.loads(row['properties']) if row['properties'] else {}
                    entity = {
                        "entity_id": str(row['id']),
                        "name": row['name'],
                        "entity_type": row['entity_type'],
                        "properties": properties,
                        "confidence": row['confidence_score'],
                        "status": row['approval_status'],
                        "source_document": row['source_document'],
                        "extraction_timestamp": row['extraction_timestamp'].isoformat() if row['extraction_timestamp'] else None,
                        "reviewer_id": row['reviewer_id'],
                        "review_timestamp": row['review_timestamp'].isoformat() if row['review_timestamp'] else None,
                        "review_notes": row['review_notes'],
                        "ingestion_batch_id": row['ingestion_batch_id']
                    }
                    entities.append(entity)
                
                logger.info(f"📋 Retrieved {len(entities)} entities from pre-approval DB")
                return entities
        except Exception as e:
            logger.error(f"❌ Error getting entities: {e}")
            # Try to reinitialize if connection was lost
            if "connection" in str(e).lower() or "pool" in str(e).lower():
                logger.info("🔄 Attempting to reinitialize database connection...")
                self._initialized = False
                self.pool = None
                await self.initialize()
                # Retry once
                async with self.pool.acquire() as conn:
                    rows = await conn.fetch(query, *params)
                    
                    entities = []
                    for row in rows:
                        properties = json.loads(row['properties']) if row['properties'] else {}
                        entity = {
                            "entity_id": str(row['id']),
                            "name": row['name'],
                            "entity_type": row['entity_type'],
                            "properties": properties,
                            "confidence": row['confidence_score'],
                            "status": row['approval_status'],
                            "source_document": row['source_document'],
                            "extraction_timestamp": row['extraction_timestamp'].isoformat() if row['extraction_timestamp'] else None,
                            "reviewer_id": row['reviewer_id'],
                            "review_timestamp": row['review_timestamp'].isoformat() if row['review_timestamp'] else None,
                            "review_notes": row['review_notes'],
                            "ingestion_batch_id": row['ingestion_batch_id']
                        }
                        entities.append(entity)
                    
                    logger.info(f"📋 Retrieved {len(entities)} entities from pre-approval DB (after retry)")
                    return entities
            else:
                raise
    
    async def approve_entity(self, 
                           entity_id: str,
                           reviewer_id: str,
                           review_notes: Optional[str] = None) -> bool:
        """Approve an entity for Neo4j ingestion."""
        if not self._initialized:
            await self.initialize()
        
        async with self.pool.acquire() as conn:
            result = await conn.execute("""
                UPDATE pre_approval_entities
                SET approval_status = 'approved',
                    reviewer_id = $2,
                    review_timestamp = NOW(),
                    review_notes = $3
                WHERE id = $1 AND approval_status = 'pending'
            """, entity_id, reviewer_id, review_notes)
            
            success = result == "UPDATE 1"
            if success:
                logger.info(f"✅ Approved entity {entity_id}")
            else:
                logger.warning(f"⚠️ Failed to approve entity {entity_id}")
            
            return success
    
    async def reject_entity(self,
                          entity_id: str,
                          reviewer_id: str,
                          review_notes: str) -> bool:
        """Reject an entity."""
        if not self._initialized:
            await self.initialize()
        
        async with self.pool.acquire() as conn:
            result = await conn.execute("""
                UPDATE pre_approval_entities
                SET approval_status = 'rejected',
                    reviewer_id = $2,
                    review_timestamp = NOW(),
                    review_notes = $3
                WHERE id = $1 AND approval_status = 'pending'
            """, entity_id, reviewer_id, review_notes)
            
            success = result == "UPDATE 1"
            if success:
                logger.info(f"❌ Rejected entity {entity_id}")
            else:
                logger.warning(f"⚠️ Failed to reject entity {entity_id}")
            
            return success
    
    async def get_approved_entities(self) -> List[Dict[str, Any]]:
        """Get approved entities ready for Neo4j ingestion."""
        return await self.get_entities(status_filter="approved")
    
    async def get_relationships(self, 
                              status_filter: str = "pending",
                              source_document: Optional[str] = None,
                              limit: int = 100) -> List[Dict[str, Any]]:
        """Get relationships from pre-approval database."""
        if not self._initialized:
            await self.initialize()
        
        # Build query conditions
        conditions = ["approval_status = $1"]
        params = [status_filter]
        param_count = 1
        
        if source_document:
            param_count += 1
            conditions.append(f"source_document = ${param_count}")
            params.append(source_document)
        
        param_count += 1
        params.append(limit)
        
        query = f"""
            SELECT id, source_entity_id, target_entity_id, relationship_type, 
                   properties, confidence_score, source_document, 
                   extraction_timestamp, approval_status,
                   reviewer_id, review_timestamp, review_notes, ingestion_batch_id
            FROM pre_approval_relationships
            WHERE {' AND '.join(conditions)}
            ORDER BY extraction_timestamp DESC
            LIMIT ${param_count}
        """
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
            
            relationships = []
            for row in rows:
                properties = json.loads(row['properties']) if row['properties'] else {}
                relationship = {
                    "relationship_id": str(row['id']),
                    "source_entity_id": str(row['source_entity_id']),
                    "target_entity_id": str(row['target_entity_id']),
                    "relationship_type": row['relationship_type'],
                    "properties": properties,
                    "confidence": row['confidence_score'],
                    "status": row['approval_status'],
                    "source_document": row['source_document'],
                    "extraction_timestamp": row['extraction_timestamp'].isoformat() if row['extraction_timestamp'] else None,
                    "reviewer_id": row['reviewer_id'],
                    "review_timestamp": row['review_timestamp'].isoformat() if row['review_timestamp'] else None,
                    "review_notes": row['review_notes'],
                    "ingestion_batch_id": row['ingestion_batch_id']
                }
                relationships.append(relationship)
            
            logger.info(f"📋 Retrieved {len(relationships)} relationships from pre-approval DB")
            return relationships
    
    async def approve_relationship(self, 
                                 relationship_id: str,
                                 reviewer_id: str,
                                 review_notes: Optional[str] = None) -> bool:
        """Approve a relationship for Neo4j ingestion."""
        if not self._initialized:
            await self.initialize()
        
        async with self.pool.acquire() as conn:
            result = await conn.execute("""
                UPDATE pre_approval_relationships
                SET approval_status = 'approved',
                    reviewer_id = $2,
                    review_timestamp = NOW(),
                    review_notes = $3
                WHERE id = $1 AND approval_status = 'pending'
            """, relationship_id, reviewer_id, review_notes)
            
            success = result == "UPDATE 1"
            if success:
                logger.info(f"✅ Approved relationship {relationship_id}")
            else:
                logger.warning(f"⚠️ Failed to approve relationship {relationship_id}")
            
            return success
    
    async def reject_relationship(self,
                                relationship_id: str,
                                reviewer_id: str,
                                review_notes: str) -> bool:
        """Reject a relationship."""
        if not self._initialized:
            await self.initialize()
        
        async with self.pool.acquire() as conn:
            result = await conn.execute("""
                UPDATE pre_approval_relationships
                SET approval_status = 'rejected',
                    reviewer_id = $2,
                    review_timestamp = NOW(),
                    review_notes = $3
                WHERE id = $1 AND approval_status = 'pending'
            """, relationship_id, reviewer_id, review_notes)
            
            success = result == "UPDATE 1"
            if success:
                logger.info(f"❌ Rejected relationship {relationship_id}")
            else:
                logger.warning(f"⚠️ Failed to reject relationship {relationship_id}")
            
            return success
    
    async def get_approved_relationships(self) -> List[Dict[str, Any]]:
        """Get approved relationships ready for Neo4j ingestion."""
        return await self.get_relationships(status_filter="approved")
    
    async def mark_relationship_ingested(self, relationship_id: str) -> bool:
        """Mark a relationship as ingested into Neo4j."""
        if not self._initialized:
            await self.initialize()
        
        async with self.pool.acquire() as conn:
            result = await conn.execute("""
                UPDATE pre_approval_relationships
                SET approval_status = 'ingested'
                WHERE id = $1 AND approval_status = 'approved'
            """, relationship_id)
            
            return result == "UPDATE 1"
    
    async def mark_entity_ingested(self, entity_id: str) -> bool:
        """Mark an entity as ingested into Neo4j."""
        if not self._initialized:
            await self.initialize()
        
        async with self.pool.acquire() as conn:
            result = await conn.execute("""
                UPDATE pre_approval_entities
                SET approval_status = 'ingested'
                WHERE id = $1 AND approval_status = 'approved'
            """, entity_id)
            
            return result == "UPDATE 1"
    
    async def cleanup_ingested_entities(self, older_than_days: int = 30):
        """Clean up old ingested entities."""
        if not self._initialized:
            await self.initialize()
        
        async with self.pool.acquire() as conn:
            result = await conn.execute("""
                DELETE FROM pre_approval_entities
                WHERE approval_status = 'ingested' 
                AND review_timestamp < NOW() - INTERVAL '%s days'
            """, older_than_days)
            
            logger.info(f"🧹 Cleaned up old ingested entities: {result}")
    
    async def clean_pending_entities(self) -> int:
        """Delete all pending entities from pre-approval database."""
        if not self._initialized:
            await self.initialize()
        
        async with self.pool.acquire() as conn:
            # First, delete any relationships referencing pending entities
            await conn.execute("""
                DELETE FROM pre_approval_relationships
                WHERE source_entity_id IN (
                    SELECT id FROM pre_approval_entities WHERE approval_status = 'pending'
                ) OR target_entity_id IN (
                    SELECT id FROM pre_approval_entities WHERE approval_status = 'pending'
                )
            """)
            
            # Then delete the pending entities
            result = await conn.execute("""
                DELETE FROM pre_approval_entities
                WHERE approval_status = 'pending'
            """)
            
            # Extract the count from the result string
            deleted_count = int(result.split()[1]) if result.startswith("DELETE") else 0
            
            logger.info(f"🧹 Cleaned up {deleted_count} pending entities")
            return deleted_count
    
    async def approve_all_pending_entities(self, reviewer_id: str, review_notes: str = None) -> int:
        """Approve all pending entities in the pre-approval database."""
        if not self._initialized:
            await self.initialize()
        
        async with self.pool.acquire() as conn:
            result = await conn.execute("""
                UPDATE pre_approval_entities
                SET approval_status = 'approved',
                    reviewer_id = $1,
                    review_timestamp = NOW(),
                    review_notes = $2
                WHERE approval_status = 'pending'
            """, reviewer_id, review_notes or 'Bulk approval - all pending entities')
            
            # Extract the count from the result string
            approved_count = int(result.split()[1]) if result.startswith("UPDATE") else 0
            
            logger.info(f"✅ Bulk approved {approved_count} pending entities")
            return approved_count
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get pre-approval database statistics."""
        if not self._initialized:
            await self.initialize()
        
        if not self.pool:
            raise RuntimeError("Database connection pool is not available")
        
        try:
            async with self.pool.acquire() as conn:
                # Entity statistics
                entity_stats = await conn.fetchrow("""
                    SELECT 
                        COUNT(*) as total,
                        COUNT(CASE WHEN approval_status = 'pending' THEN 1 END) as pending,
                        COUNT(CASE WHEN approval_status = 'approved' THEN 1 END) as approved,
                        COUNT(CASE WHEN approval_status = 'rejected' THEN 1 END) as rejected,
                        COUNT(CASE WHEN approval_status = 'ingested' THEN 1 END) as ingested
                    FROM pre_approval_entities
                """)
                
                # Relationship statistics
                rel_stats = await conn.fetchrow("""
                    SELECT 
                        COUNT(*) as total,
                        COUNT(CASE WHEN approval_status = 'pending' THEN 1 END) as pending,
                        COUNT(CASE WHEN approval_status = 'approved' THEN 1 END) as approved,
                        COUNT(CASE WHEN approval_status = 'rejected' THEN 1 END) as rejected
                    FROM pre_approval_relationships
                """)
                
                return {
                    "entities": dict(entity_stats),
                    "relationships": dict(rel_stats)
                }
        except Exception as e:
            logger.error(f"❌ Error getting statistics: {e}")
            # Try to reinitialize if connection was lost
            if "connection" in str(e).lower() or "pool" in str(e).lower():
                logger.info("🔄 Attempting to reinitialize database connection...")
                self._initialized = False
                self.pool = None
                await self.initialize()
                # Retry once
                async with self.pool.acquire() as conn:
                    entity_stats = await conn.fetchrow("""
                        SELECT 
                            COUNT(*) as total,
                            COUNT(CASE WHEN approval_status = 'pending' THEN 1 END) as pending,
                            COUNT(CASE WHEN approval_status = 'approved' THEN 1 END) as approved,
                            COUNT(CASE WHEN approval_status = 'rejected' THEN 1 END) as rejected,
                            COUNT(CASE WHEN approval_status = 'ingested' THEN 1 END) as ingested
                        FROM pre_approval_entities
                    """)
                    
                    rel_stats = await conn.fetchrow("""
                        SELECT 
                            COUNT(*) as total,
                            COUNT(CASE WHEN approval_status = 'pending' THEN 1 END) as pending,
                            COUNT(CASE WHEN approval_status = 'approved' THEN 1 END) as approved,
                            COUNT(CASE WHEN approval_status = 'rejected' THEN 1 END) as rejected
                        FROM pre_approval_relationships
                    """)
                    
                    return {
                        "entities": dict(entity_stats),
                        "relationships": dict(rel_stats)
                    }
            else:
                raise


# Factory function
def create_pre_approval_database(database_url: Optional[str] = None) -> PreApprovalDatabase:
    """Create a pre-approval database instance."""
    return PreApprovalDatabase(database_url)


# Example usage for testing
async def main():
    """Test the pre-approval database."""
    db = create_pre_approval_database()
    
    try:
        await db.initialize()
        
        # Store a test entity
        entity_id = await db.store_entity(
            name="John Doe",
            entity_type="Person",
            properties={"occupation": "Software Engineer", "location": "San Francisco"},
            source_document="test_document.md"
        )
        
        print(f"Stored entity with ID: {entity_id}")
        
        # Get entities
        entities = await db.get_entities()
        print(f"Retrieved {len(entities)} entities")
        
        # Get statistics
        stats = await db.get_statistics()
        print(f"Statistics: {stats}")
        
    finally:
        await db.close()


if __name__ == "__main__":
    asyncio.run(main())