"""
Neo4j Schema Manager for creating specific Person and Company nodes.
This bypasses Graphiti's generic Entity creation to ensure proper node types.
"""

import logging
import os
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
import uuid
from dotenv import load_dotenv

try:
    from neo4j import AsyncGraphDatabase, AsyncDriver
except ImportError:
    # Fallback for environments without neo4j driver
    AsyncGraphDatabase = None
    AsyncDriver = None

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class Neo4jSchemaManager:
    """
    Direct Neo4j schema manager for creating specific Person and Company nodes.
    This ensures that entities are created with proper labels instead of generic Entity nodes.
    """
    
    def __init__(self, uri: Optional[str] = None, user: Optional[str] = None, password: Optional[str] = None):
        """
        Initialize the Neo4j schema manager.

        Args:
            uri: Neo4j connection URI (defaults to NEO4J_URI env var)
            user: Neo4j username (defaults to NEO4J_USER env var)
            password: Neo4j password (defaults to NEO4J_PASSWORD env var)
        """
        self.uri = uri or os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.user = user or os.getenv("NEO4J_USER", "neo4j")
        self.password = password or os.getenv("NEO4J_PASSWORD", "password")
        self.driver: Optional[AsyncDriver] = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize the Neo4j driver connection."""
        if AsyncGraphDatabase is None:
            raise ImportError("neo4j driver not available. Install with: pip install neo4j")
        
        try:
            self.driver = AsyncGraphDatabase.driver(self.uri, auth=(self.user, self.password))
            # Test the connection
            await self.driver.verify_connectivity()
            self._initialized = True
            logger.info("Neo4j schema manager initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Neo4j schema manager: {e}")
            raise
    
    async def close(self):
        """Close the Neo4j driver connection."""
        if self.driver:
            await self.driver.close()
            self._initialized = False
            logger.debug("Neo4j schema manager connection closed")
    
    async def create_person_node(
        self,
        name: str,
        properties: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create a Person node in Neo4j with specific Person label.
        
        Args:
            name: Person's name
            properties: Additional properties for the node
        
        Returns:
            UUID of the created node
        """
        if not self._initialized:
            await self.initialize()
        
        node_uuid = str(uuid.uuid4())
        node_properties = {
            "uuid": node_uuid,
            "name": name,
            "entity_type": "person",
            "created_at": datetime.now(timezone.utc).isoformat(),
            **(properties or {})
        }
        
        # Cypher query to create Person node
        cypher_query = """
        MERGE (p:Person {name: $name})
        ON CREATE SET p += $properties, p.uuid = $uuid
        ON MATCH SET p += $properties
        RETURN p.uuid as uuid
        """
        
        async with self.driver.session() as session:
            try:
                result = await session.run(
                    cypher_query,
                    name=name,
                    uuid=node_uuid,
                    properties=node_properties
                )
                record = await result.single()
                created_uuid = record["uuid"] if record else node_uuid
                
                logger.debug(f"Created Person node: {name} (UUID: {created_uuid})")
                return created_uuid
                
            except Exception as e:
                logger.error(f"Failed to create Person node for {name}: {e}")
                raise
    
    async def create_company_node(
        self,
        name: str,
        properties: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create a Company node in Neo4j with specific Company label.
        
        Args:
            name: Company's name
            properties: Additional properties for the node
        
        Returns:
            UUID of the created node
        """
        if not self._initialized:
            await self.initialize()
        
        node_uuid = str(uuid.uuid4())
        node_properties = {
            "uuid": node_uuid,
            "name": name,
            "entity_type": "company",
            "created_at": datetime.now(timezone.utc).isoformat(),
            **(properties or {})
        }
        
        # Cypher query to create Company node
        cypher_query = """
        MERGE (c:Company {name: $name})
        ON CREATE SET c += $properties, c.uuid = $uuid
        ON MATCH SET c += $properties
        RETURN c.uuid as uuid
        """
        
        async with self.driver.session() as session:
            try:
                result = await session.run(
                    cypher_query,
                    name=name,
                    uuid=node_uuid,
                    properties=node_properties
                )
                record = await result.single()
                created_uuid = record["uuid"] if record else node_uuid
                
                logger.debug(f"Created Company node: {name} (UUID: {created_uuid})")
                return created_uuid
                
            except Exception as e:
                logger.error(f"Failed to create Company node for {name}: {e}")
                raise
    
    async def create_relationship(
        self,
        source_name: str,
        source_type: str,
        target_name: str,
        target_type: str,
        relationship_type: str,
        properties: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Create a relationship between two nodes.
        
        Args:
            source_name: Name of the source node
            source_type: Type of source node (Person or Company)
            target_name: Name of the target node
            target_type: Type of target node (Person or Company)
            relationship_type: Type of relationship
            properties: Additional properties for the relationship
        
        Returns:
            True if relationship was created successfully
        """
        if not self._initialized:
            await self.initialize()
        
        # Map types to labels
        source_label = "Person" if source_type.lower() == "person" else "Company"
        target_label = "Person" if target_type.lower() == "person" else "Company"
        
        rel_properties = {
            "created_at": datetime.now(timezone.utc).isoformat(),
            **(properties or {})
        }
        
        # Cypher query to create relationship
        cypher_query = f"""
        MATCH (source:{source_label} {{name: $source_name}})
        MATCH (target:{target_label} {{name: $target_name}})
        MERGE (source)-[r:{relationship_type}]->(target)
        ON CREATE SET r += $properties
        RETURN r
        """
        
        async with self.driver.session() as session:
            try:
                result = await session.run(
                    cypher_query,
                    source_name=source_name,
                    target_name=target_name,
                    properties=rel_properties
                )
                record = await result.single()
                
                if record:
                    logger.debug(f"Created relationship: {source_name} -{relationship_type}-> {target_name}")
                    return True
                else:
                    logger.warning(f"Failed to create relationship: {source_name} -{relationship_type}-> {target_name}")
                    return False
                
            except Exception as e:
                logger.error(f"Failed to create relationship {source_name} -{relationship_type}-> {target_name}: {e}")
                raise
    
    async def get_node_counts(self) -> Dict[str, int]:
        """
        Get counts of Person and Company nodes.
        
        Returns:
            Dictionary with node counts
        """
        if not self._initialized:
            await self.initialize()
        
        cypher_query = """
        RETURN 
            size((:Person)) as person_count,
            size((:Company)) as company_count,
            size((:Entity)) as entity_count
        """
        
        async with self.driver.session() as session:
            try:
                result = await session.run(cypher_query)
                record = await result.single()
                
                if record:
                    return {
                        "person_nodes": record["person_count"],
                        "company_nodes": record["company_count"],
                        "entity_nodes": record["entity_count"]
                    }
                else:
                    return {"person_nodes": 0, "company_nodes": 0, "entity_nodes": 0}
                
            except Exception as e:
                logger.error(f"Failed to get node counts: {e}")
                return {"person_nodes": 0, "company_nodes": 0, "entity_nodes": 0}
    
    async def verify_node_types(self) -> Dict[str, List[str]]:
        """
        Verify that nodes have the correct labels.
        
        Returns:
            Dictionary with sample node names by type
        """
        if not self._initialized:
            await self.initialize()
        
        cypher_query = """
        RETURN 
            [p IN (MATCH (p:Person) RETURN p.name LIMIT 5) | p] as person_samples,
            [c IN (MATCH (c:Company) RETURN c.name LIMIT 5) | c] as company_samples,
            [e IN (MATCH (e:Entity) RETURN e.name LIMIT 5) | e] as entity_samples
        """
        
        async with self.driver.session() as session:
            try:
                result = await session.run(cypher_query)
                record = await result.single()
                
                if record:
                    return {
                        "person_samples": record["person_samples"] or [],
                        "company_samples": record["company_samples"] or [],
                        "entity_samples": record["entity_samples"] or []
                    }
                else:
                    return {"person_samples": [], "company_samples": [], "entity_samples": []}
                
            except Exception as e:
                logger.error(f"Failed to verify node types: {e}")
                return {"person_samples": [], "company_samples": [], "entity_samples": []}

    async def execute_query(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Execute a Cypher query and return results.

        Args:
            query: Cypher query to execute
            parameters: Optional query parameters

        Returns:
            List of result records as dictionaries
        """
        if not self._initialized:
            await self.initialize()

        async with self.driver.session() as session:
            try:
                result = await session.run(query, parameters or {})
                records = []
                async for record in result:
                    records.append(dict(record))
                return records
            except Exception as e:
                logger.error(f"Failed to execute query: {e}")
                raise
