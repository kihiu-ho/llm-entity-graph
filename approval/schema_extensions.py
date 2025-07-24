"""
Neo4j schema extensions for the approval system.
Extends the existing Person/Company entity system with approval state management.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone

from neo4j import GraphDatabase
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ApprovalState(BaseModel):
    """Represents the approval state of an entity or relationship."""
    entity_id: str = Field(..., description="Unique identifier for the entity")
    entity_type: str = Field(..., description="Type: Person, Company, Relationship")
    status: str = Field(..., description="pending, approved, rejected, modified")
    reviewer_id: Optional[str] = Field(None, description="ID of the reviewing user")
    review_timestamp: Optional[datetime] = Field(None, description="When reviewed")
    original_data: Dict[str, Any] = Field(..., description="Original extracted data")
    modified_data: Optional[Dict[str, Any]] = Field(None, description="Modified data if changed")
    confidence_score: Optional[float] = Field(None, description="AI confidence (0-1)")
    review_notes: Optional[str] = Field(None, description="Reviewer's notes")
    source_document: str = Field(..., description="Source document reference")
    extraction_timestamp: datetime = Field(..., description="When entity was extracted")


class ApprovalSession(BaseModel):
    """Represents a document approval session."""
    session_id: str = Field(..., description="Unique session identifier")
    document_title: str = Field(..., description="Document being reviewed")
    document_source: str = Field(..., description="Document source identifier")
    status: str = Field(..., description="in_progress, completed, cancelled")
    created_timestamp: datetime = Field(..., description="Session creation time")
    completed_timestamp: Optional[datetime] = Field(None, description="Session completion time")
    reviewer_id: Optional[str] = Field(None, description="Primary reviewer ID")
    total_entities: int = Field(0, description="Total entities to review")
    approved_entities: int = Field(0, description="Number of approved entities")
    rejected_entities: int = Field(0, description="Number of rejected entities")
    modified_entities: int = Field(0, description="Number of modified entities")


class User(BaseModel):
    """Represents a system user for approval tracking."""
    user_id: str = Field(..., description="Unique user identifier")
    username: str = Field(..., description="Display username")
    email: Optional[str] = Field(None, description="User email")
    role: str = Field(..., description="reviewer, admin, viewer")
    created_timestamp: datetime = Field(..., description="Account creation time")
    last_active: Optional[datetime] = Field(None, description="Last activity timestamp")


class ApprovalSchemaManager:
    """Manages Neo4j schema extensions for the approval system."""
    
    def __init__(self, neo4j_uri: str = "neo4j://localhost:7687", 
                 neo4j_user: str = "neo4j", neo4j_password: str = "password"):
        """Initialize schema manager with Neo4j connection."""
        self.neo4j_uri = neo4j_uri
        self.neo4j_user = neo4j_user
        self.neo4j_password = neo4j_password
        self.driver = None
    
    async def initialize(self):
        """Initialize Neo4j connection and create approval schema."""
        try:
            self.driver = GraphDatabase.driver(
                self.neo4j_uri, 
                auth=(self.neo4j_user, self.neo4j_password)
            )
            
            # Test connection
            await self._test_connection()
            
            # Create approval system schema
            await self._create_approval_schema()
            
            logger.info("✅ Approval system schema initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize approval schema: {e}")
            raise
    
    async def get_latest_entities(self, limit: int = 100,
                                entity_types: Optional[List[str]] = None,
                                status_filter: str = "pending") -> List[Dict[str, Any]]:
        """Get most recently ingested entities without session requirement."""
        with self.driver.session() as session:
            # Build filter conditions
            type_filter = ""
            if entity_types:
                type_labels = ":".join(entity_types)
                type_filter = f" AND (n:{type_labels})"
            
            query = f"""
            MATCH (n)
            WHERE n.approval_status = $status {type_filter}
            RETURN n,
                   labels(n) as entity_type,
                   n.name as name,
                   n.approval_status as status,
                   n.confidence_score as confidence,
                   n.source_document as document_source,
                   n.extraction_timestamp as extracted_at,
                   properties(n) as properties
            ORDER BY n.extraction_timestamp DESC
            LIMIT $limit
            """
            
            result = session.run(query, status=status_filter, limit=limit)
            
            entities = []
            for record in result:
                # Handle datetime serialization
                extracted_at = record["extracted_at"]
                if extracted_at:
                    extracted_at = extracted_at.isoformat() if hasattr(extracted_at, 'isoformat') else str(extracted_at)
                
                # Handle properties that might contain datetime objects
                properties = record["properties"] or {}
                serializable_properties = {}
                for key, value in properties.items():
                    if hasattr(value, 'isoformat'):
                        serializable_properties[key] = value.isoformat()
                    else:
                        serializable_properties[key] = value
                
                entity_data = {
                    "entity_id": record["n"].element_id,
                    "entity_type": record["entity_type"][0] if record["entity_type"] else "Unknown",
                    "name": record["name"],
                    "status": record["status"],
                    "confidence": record["confidence"],
                    "document_source": record["document_source"],
                    "extracted_at": extracted_at,
                    "properties": serializable_properties
                }
                entities.append(entity_data)
            
            return entities
    
    async def _test_connection(self):
        """Test Neo4j connection."""
        with self.driver.session() as session:
            result = session.run("RETURN 1 as test")
            test_value = result.single()["test"]
            if test_value != 1:
                raise Exception("Neo4j connection test failed")
            logger.info("✅ Neo4j connection test passed")
    
    async def _create_approval_schema(self):
        """Create Neo4j schema for approval system."""
        with self.driver.session() as session:
            
            # Create constraints for unique identifiers
            constraints = [
                "CREATE CONSTRAINT approval_state_entity_id IF NOT EXISTS FOR (a:ApprovalState) REQUIRE a.entity_id IS UNIQUE",
                "CREATE CONSTRAINT approval_session_id IF NOT EXISTS FOR (s:ApprovalSession) REQUIRE s.session_id IS UNIQUE", 
                "CREATE CONSTRAINT user_id IF NOT EXISTS FOR (u:User) REQUIRE u.user_id IS UNIQUE",
                
                # Ensure existing Person/Company constraints exist
                "CREATE CONSTRAINT person_name IF NOT EXISTS FOR (p:Person) REQUIRE p.name IS UNIQUE",
                "CREATE CONSTRAINT company_name IF NOT EXISTS FOR (c:Company) REQUIRE c.name IS UNIQUE"
            ]
            
            for constraint in constraints:
                try:
                    session.run(constraint)
                    logger.debug(f"✅ Created constraint: {constraint.split('FOR')[1].split('REQUIRE')[0].strip()}")
                except Exception as e:
                    # Constraint might already exist
                    logger.debug(f"Constraint creation skipped (likely exists): {e}")
            
            # Create indexes for performance
            indexes = [
                "CREATE INDEX approval_status_idx IF NOT EXISTS FOR (a:ApprovalState) ON (a.status)",
                "CREATE INDEX approval_timestamp_idx IF NOT EXISTS FOR (a:ApprovalState) ON (a.review_timestamp)",
                "CREATE INDEX session_status_idx IF NOT EXISTS FOR (s:ApprovalSession) ON (s.status)",
                "CREATE INDEX user_role_idx IF NOT EXISTS FOR (u:User) ON (u.role)",
                
                # Indexes for existing entity types
                "CREATE INDEX person_source_idx IF NOT EXISTS FOR (p:Person) ON (p.source_document)",
                "CREATE INDEX company_source_idx IF NOT EXISTS FOR (c:Company) ON (c.source_document)"
            ]
            
            for index in indexes:
                try:
                    session.run(index)
                    logger.debug(f"✅ Created index: {index.split('FOR')[1].split('ON')[0].strip()}")
                except Exception as e:
                    logger.debug(f"Index creation skipped (likely exists): {e}")
            
            # Add approval properties to existing Person nodes
            session.run("""
                MATCH (p:Person)
                WHERE p.approval_status IS NULL
                SET p.approval_status = 'pending',
                    p.needs_review = true,
                    p.extraction_timestamp = datetime()
            """)
            
            # Add approval properties to existing Company nodes  
            session.run("""
                MATCH (c:Company)
                WHERE c.approval_status IS NULL
                SET c.approval_status = 'pending',
                    c.needs_review = true,
                    c.extraction_timestamp = datetime()
            """)
            
            # Add approval properties to existing relationships
            session.run("""
                MATCH ()-[r]->()
                WHERE r.approval_status IS NULL
                SET r.approval_status = 'pending',
                    r.needs_review = true,
                    r.extraction_timestamp = datetime()
            """)
            
            logger.info("✅ Neo4j approval schema created successfully")
    
    async def create_approval_state(self, approval_state: ApprovalState) -> str:
        """Create a new approval state record."""
        with self.driver.session() as session:
            result = session.run("""
                CREATE (a:ApprovalState {
                    entity_id: $entity_id,
                    entity_type: $entity_type,
                    status: $status,
                    reviewer_id: $reviewer_id,
                    review_timestamp: $review_timestamp,
                    original_data: $original_data,
                    modified_data: $modified_data,
                    confidence_score: $confidence_score,
                    review_notes: $review_notes,
                    source_document: $source_document,
                    extraction_timestamp: $extraction_timestamp,
                    created_timestamp: datetime()
                })
                RETURN a.entity_id as entity_id
            """, 
                entity_id=approval_state.entity_id,
                entity_type=approval_state.entity_type,
                status=approval_state.status,
                reviewer_id=approval_state.reviewer_id,
                review_timestamp=approval_state.review_timestamp,
                original_data=approval_state.original_data,
                modified_data=approval_state.modified_data,
                confidence_score=approval_state.confidence_score,
                review_notes=approval_state.review_notes,
                source_document=approval_state.source_document,
                extraction_timestamp=approval_state.extraction_timestamp
            )
            
            record = result.single()
            if not record:
                raise Exception("Failed to create approval state")
            
            logger.info(f"✅ Created approval state for entity: {approval_state.entity_id}")
            return record["entity_id"]
    
    async def create_approval_session(self, session: ApprovalSession) -> str:
        """Create a new approval session."""
        with self.driver.session() as session_db:
            result = session_db.run("""
                CREATE (s:ApprovalSession {
                    session_id: $session_id,
                    document_title: $document_title,
                    document_source: $document_source,
                    status: $status,
                    created_timestamp: $created_timestamp,
                    completed_timestamp: $completed_timestamp,
                    reviewer_id: $reviewer_id,
                    total_entities: $total_entities,
                    approved_entities: $approved_entities,
                    rejected_entities: $rejected_entities,
                    modified_entities: $modified_entities
                })
                RETURN s.session_id as session_id
            """,
                session_id=session.session_id,
                document_title=session.document_title,
                document_source=session.document_source,
                status=session.status,
                created_timestamp=session.created_timestamp,
                completed_timestamp=session.completed_timestamp,
                reviewer_id=session.reviewer_id,
                total_entities=session.total_entities,
                approved_entities=session.approved_entities,
                rejected_entities=session.rejected_entities,
                modified_entities=session.modified_entities
            )
            
            record = result.single()
            if not record:
                raise Exception("Failed to create approval session")
            
            logger.info(f"✅ Created approval session: {session.session_id}")
            return record["session_id"]
    
    async def create_user(self, user: User) -> str:
        """Create a new user."""
        with self.driver.session() as session:
            result = session.run("""
                CREATE (u:User {
                    user_id: $user_id,
                    username: $username,
                    email: $email,
                    role: $role,
                    created_timestamp: $created_timestamp,
                    last_active: $last_active
                })
                RETURN u.user_id as user_id
            """,
                user_id=user.user_id,
                username=user.username,
                email=user.email,
                role=user.role,
                created_timestamp=user.created_timestamp,
                last_active=user.last_active
            )
            
            record = result.single()
            if not record:
                raise Exception("Failed to create user")
            
            logger.info(f"✅ Created user: {user.username}")
            return record["user_id"]
    
    async def get_pending_entities(self, document_source: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all entities pending approval."""
        with self.driver.session() as session:
            query = """
                MATCH (n)
                WHERE n.approval_status = 'pending' OR n.needs_review = true
            """
            
            if document_source:
                query += " AND n.source_document = $source_document"
            
            query += """
                RETURN labels(n) as entity_type, 
                       n.name as name,
                       n.source_document as source_document,
                       n.extraction_timestamp as extraction_timestamp,
                       n.approval_status as approval_status,
                       properties(n) as properties
                ORDER BY n.extraction_timestamp DESC
            """
            
            params = {"source_document": document_source} if document_source else {}
            result = session.run(query, params)
            
            entities = []
            for record in result:
                entities.append({
                    "entity_type": record["entity_type"][0] if record["entity_type"] else "Unknown",
                    "name": record["name"],
                    "source_document": record["source_document"],
                    "extraction_timestamp": record["extraction_timestamp"],
                    "approval_status": record["approval_status"],
                    "properties": record["properties"]
                })
            
            logger.info(f"Retrieved {len(entities)} pending entities")
            return entities
    
    async def update_entity_approval_status(self, entity_id: str, status: str, 
                                          reviewer_id: str, review_notes: Optional[str] = None,
                                          modified_data: Optional[Dict[str, Any]] = None) -> bool:
        """Update the approval status of an entity."""
        with self.driver.session() as session:
            # Try multiple methods to find the entity
            # Method 1: Try by element ID (internal Neo4j ID)
            result = session.run("""
                MATCH (n)
                WHERE elementId(n) = $entity_id
                SET n.approval_status = $status,
                    n.reviewer_id = $reviewer_id,
                    n.review_timestamp = datetime(),
                    n.review_notes = $review_notes,
                    n.needs_review = false
                RETURN count(n) as updated_count
            """,
                entity_id=entity_id,
                status=status,
                reviewer_id=reviewer_id,
                review_notes=review_notes
            )
            
            record = result.single()
            updated_count = record["updated_count"] if record else 0
            
            # Method 2: If element ID didn't work, try by name property
            if updated_count == 0:
                result = session.run("""
                    MATCH (n)
                    WHERE n.name = $entity_name OR n.entity_id = $entity_id
                    SET n.approval_status = $status,
                        n.reviewer_id = $reviewer_id,
                        n.review_timestamp = datetime(),
                        n.review_notes = $review_notes,
                        n.needs_review = false
                    RETURN count(n) as updated_count
                """,
                    entity_name=entity_id,
                    entity_id=entity_id,
                    status=status,
                    reviewer_id=reviewer_id,
                    review_notes=review_notes
                )
                
                record = result.single()
                updated_count = record["updated_count"] if record else 0
            
            if updated_count > 0:
                logger.info(f"✅ Updated approval status for {entity_id}: {status}")
                
                # If entity was modified, update with new data
                if modified_data and status == "approved":
                    await self._apply_entity_modifications(entity_id, modified_data)
                
                return True
            else:
                logger.warning(f"No entity found with ID: {entity_id}")
                return False
    
    async def _apply_entity_modifications(self, entity_id: str, modified_data: Dict[str, Any]):
        """Apply modifications to an approved entity."""
        with self.driver.session() as session:
            # Build dynamic SET clause for modified properties
            set_clauses = []
            params = {"entity_id": entity_id}
            
            for key, value in modified_data.items():
                if key not in ["name", "entity_id"]:  # Preserve core identifiers
                    param_name = f"mod_{key}"
                    set_clauses.append(f"n.{key} = ${param_name}")
                    params[param_name] = value
            
            if set_clauses:
                query = f"""
                    MATCH (n {{name: $entity_id}})
                    SET {', '.join(set_clauses)},
                        n.modified_timestamp = datetime(),
                        n.modification_applied = true
                    RETURN count(n) as updated_count
                """
                
                result = session.run(query, params)
                record = result.single()
                
                if record and record["updated_count"] > 0:
                    logger.info(f"✅ Applied modifications to entity: {entity_id}")
                else:
                    logger.warning(f"Failed to apply modifications to entity: {entity_id}")
    
    async def get_approval_session_stats(self, session_id: str) -> Dict[str, Any]:
        """Get statistics for an approval session."""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (s:ApprovalSession {session_id: $session_id})
                OPTIONAL MATCH (n) WHERE n.source_document = s.document_source
                RETURN s.session_id as session_id,
                       s.document_title as document_title,
                       s.status as status,
                       s.created_timestamp as created_timestamp,
                       count(n) as total_entities,
                       count(CASE WHEN n.approval_status = 'approved' THEN 1 END) as approved_count,
                       count(CASE WHEN n.approval_status = 'rejected' THEN 1 END) as rejected_count,
                       count(CASE WHEN n.approval_status = 'pending' THEN 1 END) as pending_count
            """, session_id=session_id)
            
            record = result.single()
            if not record:
                return {}
            
            return {
                "session_id": record["session_id"],
                "document_title": record["document_title"],
                "status": record["status"],
                "created_timestamp": record["created_timestamp"],
                "total_entities": record["total_entities"],
                "approved_count": record["approved_count"],
                "rejected_count": record["rejected_count"],
                "pending_count": record["pending_count"],
                "completion_percentage": (
                    (record["approved_count"] + record["rejected_count"]) / record["total_entities"] * 100
                    if record["total_entities"] > 0 else 0
                )
            }
    
    async def close(self):
        """Close Neo4j connection."""
        if self.driver:
            self.driver.close()
            logger.info("Neo4j connection closed")


# Factory function
def create_approval_schema_manager(neo4j_uri: str = "neo4j://localhost:7687",
                                 neo4j_user: str = "neo4j", 
                                 neo4j_password: str = "password") -> ApprovalSchemaManager:
    """Create approval schema manager instance."""
    return ApprovalSchemaManager(neo4j_uri, neo4j_user, neo4j_password)