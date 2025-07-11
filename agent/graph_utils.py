"""
Graph utilities for Neo4j/Graphiti integration.
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional, Tuple, Union
from datetime import datetime, timezone
from contextlib import asynccontextmanager
import asyncio

from graphiti_core import Graphiti
from graphiti_core.utils.maintenance.graph_data_operations import clear_data
from graphiti_core.llm_client.config import LLMConfig
from .enhanced_openai_client import EnhancedOpenAIClient
from graphiti_core.embedder.openai import OpenAIEmbedderConfig
from .custom_embedder import TokenLimitedOpenAIEmbedder
from graphiti_core.cross_encoder.openai_reranker_client import OpenAIRerankerClient
from dotenv import load_dotenv

from .entity_models import (
    Person, Company, BaseEntity, Relationship, EntityGraph,
    EntityType, PersonType, CompanyType, RelationshipType
)

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Help from this PR for setting up the custom clients: https://github.com/getzep/graphiti/pull/601/files
class GraphitiClient:
    """Manages Graphiti knowledge graph operations."""
    
    def __init__(
        self,
        neo4j_uri: Optional[str] = None,
        neo4j_user: Optional[str] = None,
        neo4j_password: Optional[str] = None
    ):
        """
        Initialize Graphiti client.
        
        Args:
            neo4j_uri: Neo4j connection URI
            neo4j_user: Neo4j username
            neo4j_password: Neo4j password
        """
        # Neo4j configuration
        self.neo4j_uri = neo4j_uri or os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.neo4j_user = neo4j_user or os.getenv("NEO4J_USER", "neo4j")
        self.neo4j_password = neo4j_password or os.getenv("NEO4J_PASSWORD")
        
        if not self.neo4j_password:
            raise ValueError("NEO4J_PASSWORD environment variable not set")
        
        # LLM configuration
        self.llm_base_url = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
        self.llm_api_key = os.getenv("LLM_API_KEY")
        self.llm_choice = os.getenv("LLM_CHOICE", "gpt-4.1-mini")
        
        if not self.llm_api_key:
            raise ValueError("LLM_API_KEY environment variable not set")
        
        # Embedding configuration
        self.embedding_base_url = os.getenv("EMBEDDING_BASE_URL", "https://api.openai.com/v1")
        self.embedding_api_key = os.getenv("EMBEDDING_API_KEY")
        self.embedding_model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
        self.embedding_dimensions = int(os.getenv("VECTOR_DIMENSION", "1536"))
        
        if not self.embedding_api_key:
            raise ValueError("EMBEDDING_API_KEY environment variable not set")
        
        self.graphiti: Optional[Graphiti] = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize Graphiti client."""
        if self._initialized:
            return
        
        try:
            # Create LLMConfig
            llm_config = LLMConfig(
                api_key=self.llm_api_key,
                model=self.llm_choice,
                small_model=self.llm_choice,  # Can be the same as main model
                base_url=self.llm_base_url
            )
            
            # Create Enhanced OpenAI LLM client with robust JSON parsing
            llm_client = EnhancedOpenAIClient(config=llm_config)
            
            # Create token-limited OpenAI embedder
            embedder = TokenLimitedOpenAIEmbedder(
                config=OpenAIEmbedderConfig(
                    api_key=self.embedding_api_key,
                    embedding_model=self.embedding_model,
                    embedding_dim=self.embedding_dimensions,
                    base_url=self.embedding_base_url
                )
            )
            
            # Initialize Graphiti with custom clients
            self.graphiti = Graphiti(
                self.neo4j_uri,
                self.neo4j_user,
                self.neo4j_password,
                llm_client=llm_client,
                embedder=embedder,
                cross_encoder=OpenAIRerankerClient(client=llm_client, config=llm_config)
            )
            
            # Build indices and constraints
            await self.graphiti.build_indices_and_constraints()
            
            self._initialized = True
            logger.info(f"Graphiti client initialized successfully with LLM: {self.llm_choice} and embedder: {self.embedding_model}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Graphiti: {e}")
            raise
    
    async def close(self):
        """Close Graphiti connection."""
        if self.graphiti:
            await self.graphiti.close()
            self.graphiti = None
            self._initialized = False
            logger.info("Graphiti client closed")
    
    async def add_episode(
        self,
        episode_id: str,
        content: str,
        source: str,
        timestamp: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None,
        entity_types: Optional[Dict[str, Any]] = None,
        edge_types: Optional[Dict[str, Any]] = None,
        edge_type_map: Optional[Dict[Tuple[str, str], List[str]]] = None
    ):
        """
        Add an episode to the knowledge graph with custom entity types.

        Args:
            episode_id: Unique episode identifier
            content: Episode content
            source: Source of the content
            timestamp: Episode timestamp
            metadata: Additional metadata
            entity_types: Custom entity types (e.g., {"Person": Person, "Company": Company})
            edge_types: Custom edge types (e.g., {"Employment": Employment})
            edge_type_map: Mapping of entity pairs to edge types
        """
        if not self._initialized:
            await self.initialize()

        episode_timestamp = timestamp or datetime.now(timezone.utc)

        # Import EpisodeType for proper source handling
        from graphiti_core.nodes import EpisodeType

        # Prepare arguments for add_episode
        episode_args = {
            "name": episode_id,
            "episode_body": content,
            "source_description": source,
            "reference_time": episode_timestamp
        }

        # Add custom entity types if provided
        if entity_types:
            episode_args["entity_types"] = entity_types
            logger.debug(f"Using custom entity types: {list(entity_types.keys())}")

        # Add custom edge types if provided
        if edge_types:
            episode_args["edge_types"] = edge_types
            logger.debug(f"Using custom edge types: {list(edge_types.keys())}")

        # Add edge type mapping if provided
        if edge_type_map:
            episode_args["edge_type_map"] = edge_type_map
            logger.debug(f"Using edge type mapping with {len(edge_type_map)} mappings")

        await self.graphiti.add_episode(**episode_args)
        
        logger.info(f"Added episode {episode_id} to knowledge graph")

    async def add_entity(
        self,
        entity: Union[Person, Company, BaseEntity],
        source_document: Optional[str] = None
    ) -> str:
        """
        Add a structured node to the knowledge graph.

        Args:
            entity: Node to add (Person, Company, or BaseEntity)
            source_document: Source document ID

        Returns:
            Episode ID for the node
        """
        if not self._initialized:
            await self.initialize()

        # Create episode content from entity
        episode_content = self._create_entity_episode_content(entity)
        episode_id = f"entity_{entity.entity_type.value}_{entity.name}_{datetime.now().timestamp()}"

        # Add entity metadata
        entity_metadata = {
            "entity_type": entity.entity_type.value,
            "entity_name": entity.name,
            "entity_aliases": entity.aliases,
            "source_document": source_document,
            **entity.metadata
        }

        # Add specific metadata based on entity type
        if isinstance(entity, Person):
            entity_metadata.update({
                "person_type": entity.person_type.value if entity.person_type else None,
                "full_name": entity.full_name,
                "current_company": entity.current_company,
                "current_position": entity.current_position
            })
        elif isinstance(entity, Company):
            entity_metadata.update({
                "company_type": entity.company_type.value if entity.company_type else None,
                "legal_name": entity.legal_name,
                "ticker_symbol": entity.ticker_symbol,
                "industry": entity.industry,
                "headquarters": entity.headquarters
            })

        await self.add_episode(
            episode_id=episode_id,
            content=episode_content,
            source=f"entity_extraction_{entity.entity_type.value}",
            timestamp=datetime.now(timezone.utc),
            metadata=entity_metadata
        )

        logger.info(f"Added {entity.entity_type.value} node: {entity.name}")
        return episode_id

    async def add_relationship(
        self,
        relationship: Relationship,
        source_document: Optional[str] = None
    ) -> str:
        """
        Add a relationship to the knowledge graph.

        Args:
            relationship: Relationship to add
            source_document: Source document ID

        Returns:
            Episode ID for the relationship
        """
        if not self._initialized:
            await self.initialize()

        # Create episode content from relationship
        episode_content = self._create_relationship_episode_content(relationship)
        episode_id = f"relationship_{relationship.relationship_type}_{datetime.now().timestamp()}"

        # Add relationship metadata
        relationship_metadata = {
            "relationship_type": relationship.relationship_type,
            "source_entity_id": relationship.source_entity_id,
            "target_entity_id": relationship.target_entity_id,
            "strength": relationship.strength,
            "is_active": relationship.is_active,
            "source_document": source_document,
            **relationship.metadata
        }

        await self.add_episode(
            episode_id=episode_id,
            content=episode_content,
            source="relationship_extraction",
            timestamp=datetime.now(timezone.utc),
            metadata=relationship_metadata
        )

        logger.info(f"Added relationship: {relationship.relationship_type}")
        return episode_id

    def _create_entity_episode_content(self, entity: Union[Person, Company, BaseEntity]) -> str:
        """Create episode content for a node with explicit type information for Graphiti."""
        content_parts = []

        # Add explicit node type declaration for Graphiti to recognize
        if isinstance(entity, Person):
            content_parts.append(f"PERSON: {entity.name}")
            content_parts.append(f"Entity Type: Person")
        elif isinstance(entity, Company):
            content_parts.append(f"COMPANY: {entity.name}")
            content_parts.append(f"Entity Type: Company")
        else:
            content_parts.append(f"Entity: {entity.name}")
            content_parts.append(f"Entity Type: {entity.entity_type.value}")

        if entity.description:
            content_parts.append(f"Description: {entity.description}")

        if entity.aliases:
            content_parts.append(f"Also known as: {', '.join(entity.aliases)}")

        if isinstance(entity, Person):
            if entity.full_name:
                content_parts.append(f"Full name: {entity.full_name}")
            if entity.current_company:
                content_parts.append(f"Current company: {entity.current_company}")
            if entity.current_position:
                content_parts.append(f"Current position: {entity.current_position}")
            if entity.education:
                content_parts.append(f"Education: {', '.join(entity.education)}")
            if entity.skills:
                content_parts.append(f"Skills: {', '.join(entity.skills)}")

        elif isinstance(entity, Company):
            if entity.legal_name:
                content_parts.append(f"Legal name: {entity.legal_name}")
            if entity.industry:
                content_parts.append(f"Industry: {entity.industry}")
            if entity.headquarters:
                content_parts.append(f"Headquarters: {entity.headquarters}")
            if entity.products:
                content_parts.append(f"Products/Services: {', '.join(entity.products)}")
            if entity.key_executives:
                content_parts.append(f"Key executives: {', '.join(entity.key_executives)}")

        return "\n".join(content_parts)

    def _create_relationship_episode_content(self, relationship: Relationship) -> str:
        """Create episode content for a relationship."""
        content_parts = [
            f"Relationship: {relationship.source_entity_id} {relationship.relationship_type} {relationship.target_entity_id}"
        ]

        if relationship.description:
            content_parts.append(f"Description: {relationship.description}")

        if relationship.strength:
            content_parts.append(f"Strength: {relationship.strength}")

        if relationship.start_date:
            content_parts.append(f"Started: {relationship.start_date.isoformat()}")

        if relationship.end_date:
            content_parts.append(f"Ended: {relationship.end_date.isoformat()}")

        content_parts.append(f"Active: {relationship.is_active}")

        return "\n".join(content_parts)

    async def search(
        self,
        query: str,
        center_node_distance: int = 2,
        use_hybrid_search: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Search the knowledge graph.
        
        Args:
            query: Search query
            center_node_distance: Distance from center nodes
            use_hybrid_search: Whether to use hybrid search
        
        Returns:
            Search results
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            # Use Graphiti's search method (simplified parameters)
            results = await self.graphiti.search(query)
            
            # Convert results to dictionaries
            return [
                {
                    "fact": result.fact,
                    "uuid": str(result.uuid),
                    "valid_at": str(result.valid_at) if hasattr(result, 'valid_at') and result.valid_at else None,
                    "invalid_at": str(result.invalid_at) if hasattr(result, 'invalid_at') and result.invalid_at else None,
                    "source_node_uuid": str(result.source_node_uuid) if hasattr(result, 'source_node_uuid') and result.source_node_uuid else None
                }
                for result in results
            ]
            
        except Exception as e:
            logger.error(f"Graph search failed: {e}")
            return []

    async def search_entities(
        self,
        entity_type: Optional[EntityType] = None,
        name_query: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search for nodes in the knowledge graph.

        Args:
            entity_type: Filter by node type
            name_query: Search by node name
            limit: Maximum number of results

        Returns:
            List of node search results
        """
        if not self._initialized:
            await self.initialize()

        # Build search query
        query_parts = []
        if entity_type:
            query_parts.append(f"node type {entity_type.value}")
        if name_query:
            query_parts.append(f"node named {name_query}")

        query = " ".join(query_parts) if query_parts else "nodes"

        try:
            results = await self.graphiti.search(query)

            # Filter and format results
            node_results = []
            for result in results[:limit]:
                # Check if this is a node episode
                if hasattr(result, 'source_node_uuid') and result.source_node_uuid:
                    # Try to extract node information from the fact
                    node_info = self._extract_entity_from_fact(result.fact)
                    if node_info:
                        node_results.append({
                            "node_name": node_info.get("name"),
                            "node_type": node_info.get("type"),
                            "fact": result.fact,
                            "uuid": str(result.uuid),
                            "source_node_uuid": str(result.source_node_uuid)
                        })

            return node_results

        except Exception as e:
            logger.error(f"Entity search failed: {e}")
            return []

    async def get_entity_relationships(
        self,
        entity_name: str,
        relationship_types: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get relationships for a specific node.

        Args:
            entity_name: Name of the node
            relationship_types: Filter by relationship types

        Returns:
            List of relationships
        """
        if not self._initialized:
            await self.initialize()

        # Search for relationships involving this node
        query = f"relationships involving {entity_name}"
        if relationship_types:
            query += f" of type {', '.join(relationship_types)}"

        try:
            results = await self.graphiti.search(query)

            relationships = []
            for result in results:
                # Extract relationship information from the fact
                rel_info = self._extract_relationship_from_fact(result.fact, entity_name)
                if rel_info:
                    relationships.append({
                        "relationship_type": rel_info.get("type"),
                        "related_node": rel_info.get("related_entity"),
                        "direction": rel_info.get("direction"),  # "outgoing" or "incoming"
                        "fact": result.fact,
                        "uuid": str(result.uuid)
                    })

            return relationships

        except Exception as e:
            logger.error(f"Relationship search failed: {e}")
            return []

    def _extract_entity_from_fact(self, fact: str) -> Optional[Dict[str, Any]]:
        """Extract node information from a fact string."""
        try:
            # Simple pattern matching for node facts
            if fact.startswith("Node:"):
                lines = fact.split("\n")
                node_info = {}

                for line in lines:
                    if line.startswith("Node:"):
                        node_info["name"] = line.replace("Node:", "").strip()
                    elif line.startswith("Type:"):
                        node_info["type"] = line.replace("Type:", "").strip()
                    elif line.startswith("Description:"):
                        node_info["description"] = line.replace("Description:", "").strip()

                return node_info if node_info else None

            return None

        except Exception as e:
            logger.error(f"Failed to extract node from fact: {e}")
            return None

    def _extract_relationship_from_fact(self, fact: str, entity_name: str) -> Optional[Dict[str, Any]]:
        """Extract relationship information from a fact string."""
        try:
            # Simple pattern matching for relationship facts
            if fact.startswith("Relationship:"):
                lines = fact.split("\n")
                rel_line = lines[0].replace("Relationship:", "").strip()

                # Parse relationship pattern: "NodeA relationship_type NodeB"
                parts = rel_line.split()
                if len(parts) >= 3:
                    source_node = parts[0]
                    rel_type = parts[1]
                    target_node = " ".join(parts[2:])

                    # Determine direction relative to the queried node
                    if source_node.lower() == entity_name.lower():
                        return {
                            "type": rel_type,
                            "related_entity": target_node,
                            "direction": "outgoing"
                        }
                    elif target_node.lower() == entity_name.lower():
                        return {
                            "type": rel_type,
                            "related_entity": source_node,
                            "direction": "incoming"
                        }

            return None

        except Exception as e:
            logger.error(f"Failed to extract relationship from fact: {e}")
            return None

    async def get_related_entities(
        self,
        entity_name: str,
        relationship_types: Optional[List[str]] = None,
        depth: int = 1
    ) -> Dict[str, Any]:
        """
        Get entities related to a given entity using Graphiti search.
        
        Args:
            entity_name: Name of the entity
            relationship_types: Types of relationships to follow (not used with Graphiti)
            depth: Maximum depth to traverse (not used with Graphiti)
        
        Returns:
            Related entities and relationships
        """
        if not self._initialized:
            await self.initialize()
        
        # Use Graphiti search to find related information about the entity
        results = await self.graphiti.search(f"relationships involving {entity_name}")
        
        # Extract entity information from the search results
        related_entities = set()
        facts = []
        
        for result in results:
            facts.append({
                "fact": result.fact,
                "uuid": str(result.uuid),
                "valid_at": str(result.valid_at) if hasattr(result, 'valid_at') and result.valid_at else None
            })
            
            # Simple entity extraction from fact text (could be enhanced)
            if entity_name.lower() in result.fact.lower():
                related_entities.add(entity_name)
        
        return {
            "central_entity": entity_name,
            "related_facts": facts,
            "search_method": "graphiti_semantic_search"
        }
    
    async def get_entity_timeline(
        self,
        entity_name: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Get timeline of facts for an entity using Graphiti.
        
        Args:
            entity_name: Name of the entity
            start_date: Start of time range (not currently used)
            end_date: End of time range (not currently used)
        
        Returns:
            Timeline of facts
        """
        if not self._initialized:
            await self.initialize()
        
        # Search for temporal information about the entity
        results = await self.graphiti.search(f"timeline history of {entity_name}")
        
        timeline = []
        for result in results:
            timeline.append({
                "fact": result.fact,
                "uuid": str(result.uuid),
                "valid_at": str(result.valid_at) if hasattr(result, 'valid_at') and result.valid_at else None,
                "invalid_at": str(result.invalid_at) if hasattr(result, 'invalid_at') and result.invalid_at else None
            })
        
        # Sort by valid_at if available
        timeline.sort(key=lambda x: x.get('valid_at') or '', reverse=True)
        
        return timeline
    
    async def get_graph_statistics(self) -> Dict[str, Any]:
        """
        Get basic statistics about the knowledge graph.
        
        Returns:
            Graph statistics
        """
        if not self._initialized:
            await self.initialize()
        
        # For now, return a simple search to verify the graph is working
        # More detailed statistics would require direct Neo4j access
        try:
            test_results = await self.graphiti.search("test")
            return {
                "graphiti_initialized": True,
                "sample_search_results": len(test_results),
                "note": "Detailed statistics require direct Neo4j access"
            }
        except Exception as e:
            return {
                "graphiti_initialized": False,
                "error": str(e)
            }
    
    async def clear_graph(self):
        """Clear all data from the graph (USE WITH CAUTION)."""
        if not self._initialized:
            await self.initialize()
        
        try:
            # Use Graphiti's proper clear_data function with the driver
            await clear_data(self.graphiti.driver)
            logger.warning("Cleared all data from knowledge graph")
        except Exception as e:
            logger.error(f"Failed to clear graph using clear_data: {e}")
            # Fallback: Close and reinitialize (this will create fresh indices)
            if self.graphiti:
                await self.graphiti.close()
            
            # Create OpenAI-compatible clients for reinitialization
            llm_config = LLMConfig(
                api_key=self.llm_api_key,
                model=self.llm_choice,
                small_model=self.llm_choice,
                base_url=self.llm_base_url
            )
            
            llm_client = EnhancedOpenAIClient(config=llm_config)
            
            embedder = TokenLimitedOpenAIEmbedder(
                config=OpenAIEmbedderConfig(
                    api_key=self.embedding_api_key,
                    embedding_model=self.embedding_model,
                    embedding_dim=self.embedding_dimensions,
                    base_url=self.embedding_base_url
                )
            )
            
            self.graphiti = Graphiti(
                self.neo4j_uri,
                self.neo4j_user,
                self.neo4j_password,
                llm_client=llm_client,
                embedder=embedder,
                cross_encoder=OpenAIRerankerClient(client=llm_client, config=llm_config)
            )
            await self.graphiti.build_indices_and_constraints()
            
            logger.warning("Reinitialized Graphiti client (fresh indices created)")


# Global Graphiti client instance
graph_client = GraphitiClient()


async def initialize_graph():
    """Initialize graph client."""
    await graph_client.initialize()


async def close_graph():
    """Close graph client."""
    await graph_client.close()


# Convenience functions for common operations
async def add_to_knowledge_graph(
    content: str,
    source: str,
    episode_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Add content to the knowledge graph.
    
    Args:
        content: Content to add
        source: Source of the content
        episode_id: Optional episode ID
        metadata: Optional metadata
    
    Returns:
        Episode ID
    """
    if not episode_id:
        episode_id = f"episode_{datetime.now(timezone.utc).isoformat()}"
    
    await graph_client.add_episode(
        episode_id=episode_id,
        content=content,
        source=source,
        metadata=metadata
    )
    
    return episode_id


async def search_knowledge_graph(
    query: str
) -> List[Dict[str, Any]]:
    """
    Search the knowledge graph.
    
    Args:
        query: Search query
    
    Returns:
        Search results
    """
    return await graph_client.search(query)


async def get_entity_relationships(
    entity: str,
    depth: int = 2
) -> Dict[str, Any]:
    """
    Get relationships for an entity.
    
    Args:
        entity: Entity name
        depth: Maximum traversal depth
    
    Returns:
        Entity relationships
    """
    return await graph_client.get_related_entities(entity, depth=depth)


async def add_person_to_graph(
    name: str,
    person_type: Optional[PersonType] = None,
    current_company: Optional[str] = None,
    current_position: Optional[str] = None,
    source_document: Optional[str] = None,
    **kwargs
) -> str:
    """
    Add a person node to the knowledge graph.

    Args:
        name: Person's name
        person_type: Type of person
        current_company: Current employer
        current_position: Current job title
        source_document: Source document ID
        **kwargs: Additional person attributes

    Returns:
        Episode ID
    """
    person = Person(
        name=name,
        person_type=person_type,
        current_company=current_company,
        current_position=current_position,
        **kwargs
    )

    return await graph_client.add_entity(person, source_document)


async def add_company_to_graph(
    name: str,
    company_type: Optional[CompanyType] = None,
    industry: Optional[str] = None,
    headquarters: Optional[str] = None,
    source_document: Optional[str] = None,
    **kwargs
) -> str:
    """
    Add a company node to the knowledge graph.

    Args:
        name: Company name
        company_type: Type of company
        industry: Primary industry
        headquarters: Headquarters location
        source_document: Source document ID
        **kwargs: Additional company attributes

    Returns:
        Episode ID
    """
    company = Company(
        name=name,
        company_type=company_type,
        industry=industry,
        headquarters=headquarters,
        **kwargs
    )

    return await graph_client.add_entity(company, source_document)


async def add_relationship_to_graph(
    source_entity: str,
    target_entity: str,
    relationship_type: str,
    description: Optional[str] = None,
    strength: Optional[float] = None,
    source_document: Optional[str] = None,
    **kwargs
) -> str:
    """
    Add a relationship to the knowledge graph.

    Args:
        source_entity: Source entity name/ID
        target_entity: Target entity name/ID
        relationship_type: Type of relationship
        description: Relationship description
        strength: Relationship strength (0.0-1.0)
        source_document: Source document ID
        **kwargs: Additional relationship attributes

    Returns:
        Episode ID
    """
    relationship = Relationship(
        source_entity_id=source_entity,
        target_entity_id=target_entity,
        relationship_type=relationship_type,
        description=description,
        strength=strength,
        **kwargs
    )

    return await graph_client.add_relationship(relationship, source_document)


async def search_people(
    name_query: Optional[str] = None,
    company: Optional[str] = None,
    position: Optional[str] = None,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Search for people in the knowledge graph.

    Args:
        name_query: Search by name
        company: Filter by company
        position: Filter by position
        limit: Maximum number of results

    Returns:
        List of person search results
    """
    # Build search query
    query_parts = ["person"]
    if name_query:
        query_parts.append(f"named {name_query}")
    if company:
        query_parts.append(f"at {company}")
    if position:
        query_parts.append(f"with position {position}")

    query = " ".join(query_parts)

    try:
        results = await graph_client.search(query)
        return results[:limit]
    except Exception as e:
        logger.error(f"Person search failed: {e}")
        return []


async def search_companies(
    name_query: Optional[str] = None,
    industry: Optional[str] = None,
    location: Optional[str] = None,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Search for companies in the knowledge graph.

    Args:
        name_query: Search by name
        industry: Filter by industry
        location: Filter by location
        limit: Maximum number of results

    Returns:
        List of company search results
    """
    # Build search query
    query_parts = ["company"]
    if name_query:
        query_parts.append(f"named {name_query}")
    if industry:
        query_parts.append(f"in {industry}")
    if location:
        query_parts.append(f"located in {location}")

    query = " ".join(query_parts)

    try:
        results = await graph_client.search(query)
        return results[:limit]
    except Exception as e:
        logger.error(f"Company search failed: {e}")
        return []


async def get_person_relationships(
    person_name: str,
    relationship_types: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    Get relationships for a person.

    Args:
        person_name: Name of the person
        relationship_types: Filter by relationship types

    Returns:
        List of relationships
    """
    return await graph_client.get_entity_relationships(person_name, relationship_types)


async def get_company_relationships(
    company_name: str,
    relationship_types: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    Get relationships for a company.

    Args:
        company_name: Name of the company
        relationship_types: Filter by relationship types

    Returns:
        List of relationships
    """
    return await graph_client.get_entity_relationships(company_name, relationship_types)


async def test_graph_connection() -> bool:
    """
    Test graph database connection.

    Returns:
        True if connection successful
    """
    try:
        await graph_client.initialize()
        stats = await graph_client.get_graph_statistics()
        logger.info(f"Graph connection successful. Stats: {stats}")
        return True
    except Exception as e:
        logger.error(f"Graph connection test failed: {e}")
        return False