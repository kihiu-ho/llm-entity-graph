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

# Import edge types for Graphiti registration
from .edge_models import Employment, Leadership, Investment, Partnership, Ownership

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
        self.neo4j_database = os.getenv("NEO4J_DATABASE", "neo4j")  # Default database name

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

        # Define custom entity types for Graphiti
        self.entity_types = {
            "Person": Person,
            "Company": Company
        }

        # Define custom edge types for Graphiti
        self.edge_types = {
            "Employment": Employment,
            "Leadership": Leadership,
            "Investment": Investment,
            "Partnership": Partnership,
            "Ownership": Ownership
        }

        # Define edge type mapping for relationships
        self.edge_type_map = {
            ("Person", "Company"): ["Employment", "Leadership"],
            ("Company", "Company"): ["Partnership", "Investment", "Ownership"],
            ("Person", "Person"): ["Partnership"],
            ("Entity", "Entity"): ["Investment", "Partnership"]  # Fallback for any entity type
        }
    
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

        # Use Graphiti's add_episode with custom entity types
        await self.graphiti.add_episode(
            name=episode_id,
            episode_body=episode_content,
            source_description=f"entity_extraction_{entity.entity_type.value}",
            reference_time=datetime.now(timezone.utc),
            entity_types=self.entity_types,
            edge_types=self.edge_types,
            edge_type_map=self.edge_type_map,
            metadata=entity_metadata
        )

        logger.info(f"✓ Added {entity.entity_type.value} entity with custom types: {entity.name}")
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
            
            # Convert results to dictionaries, handling both dict and object formats
            converted_results = []
            for result in results:
                if isinstance(result, dict):
                    # Already a dictionary
                    converted_results.append(result)
                else:
                    # Object format, convert to dictionary
                    converted_results.append({
                        "fact": getattr(result, "fact", ""),
                        "uuid": str(getattr(result, "uuid", "")),
                        "valid_at": str(result.valid_at) if hasattr(result, 'valid_at') and result.valid_at else None,
                        "invalid_at": str(result.invalid_at) if hasattr(result, 'invalid_at') and result.invalid_at else None,
                        "source_node_uuid": str(result.source_node_uuid) if hasattr(result, 'source_node_uuid') and result.source_node_uuid else None
                    })

            return converted_results
            
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
                # Handle both dict and object formats
                if isinstance(result, dict):
                    fact = result.get("fact", "")
                    uuid = result.get("uuid", "")
                    source_node_uuid = result.get("source_node_uuid", "")
                else:
                    fact = getattr(result, "fact", "")
                    uuid = str(getattr(result, "uuid", ""))
                    source_node_uuid = str(getattr(result, "source_node_uuid", ""))

                # Check if this is a node episode
                if source_node_uuid:
                    # Try to extract node information from the fact
                    node_info = self._extract_entity_from_fact(fact)
                    if node_info:
                        node_results.append({
                            "node_name": node_info.get("name"),
                            "node_type": node_info.get("type"),
                            "fact": fact,
                            "uuid": uuid,
                            "source_node_uuid": source_node_uuid
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
        Get relationships for a specific node with enhanced extraction.

        Args:
            entity_name: Name of the node
            relationship_types: Filter by relationship types

        Returns:
            List of relationships
        """
        if not self._initialized:
            await self.initialize()

        # Use multiple search strategies for better coverage
        search_queries = [
            f"relationships involving {entity_name}",
            f"connections of {entity_name}",
            f"{entity_name} relationships",
            f"facts about {entity_name}",
            f"{entity_name} works at",
            f"{entity_name} employed by",
            f"{entity_name} executive of",
            f"{entity_name} director of"
        ]

        try:
            all_relationships = []
            seen_facts = set()

            for query in search_queries:
                try:
                    results = await self.graphiti.search(query)

                    for result in results:
                        # Handle both dict and object formats
                        if isinstance(result, dict):
                            fact = result.get("fact", "")
                            uuid = result.get("uuid", "")
                        else:
                            fact = getattr(result, "fact", "")
                            uuid = str(getattr(result, "uuid", ""))

                        # Skip duplicate facts
                        if fact in seen_facts:
                            continue
                        seen_facts.add(fact)

                        # Use enhanced extraction
                        relationships = self._extract_relationships_enhanced(fact, entity_name, uuid)

                        for rel in relationships:
                            # Filter by relationship types if specified
                            if relationship_types and rel.get("relationship_type") not in relationship_types:
                                continue
                            all_relationships.append(rel)

                except Exception as e:
                    logger.warning(f"Search query '{query}' failed: {e}")
                    continue

            # Remove duplicates
            unique_relationships = []
            seen_rels = set()

            for rel in all_relationships:
                rel_key = f"{rel.get('source_entity', '')}_{rel.get('relationship_type', '')}_{rel.get('target_entity', '')}"
                if rel_key not in seen_rels:
                    seen_rels.add(rel_key)
                    unique_relationships.append(rel)

            logger.info(f"Found {len(unique_relationships)} unique relationships for {entity_name}")
            return unique_relationships

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
        """Extract relationship information from a fact string (legacy method)."""
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

    def _extract_relationships_enhanced(self, fact: str, entity_name: str, fact_uuid: str) -> List[Dict[str, Any]]:
        """
        Enhanced relationship extraction that handles multiple fact formats.
        Uses the same logic as the tools module for consistency with ingestion format.

        Args:
            fact: The fact text from Graphiti
            entity_name: The entity we're searching for
            fact_uuid: UUID of the fact

        Returns:
            List of extracted relationships
        """
        try:
            # Import the Graphiti-specific extraction function from tools module for consistency
            from ..agent.tools import _extract_relationships_from_graphiti_fact
            return _extract_relationships_from_graphiti_fact(fact, entity_name, fact_uuid)
        except ImportError:
            # Fallback to local implementation if import fails
            logger.warning("Could not import extraction function from tools module, using local implementation")
            return self._extract_relationships_enhanced_local(fact, entity_name, fact_uuid)

    def _extract_relationships_enhanced_local(self, fact: str, entity_name: str, fact_uuid: str) -> List[Dict[str, Any]]:
        """
        Local implementation of enhanced relationship extraction.

        Args:
            fact: The fact text from Graphiti
            entity_name: The entity we're searching for
            fact_uuid: UUID of the fact

        Returns:
            List of extracted relationships
        """
        relationships = []

        try:
            import re

            # Split fact into lines for analysis
            lines = fact.split('\n')
            fact_lower = fact.lower()
            entity_lower = entity_name.lower()

            # Skip if entity is not mentioned in the fact
            if entity_name and entity_lower not in fact_lower:
                return relationships

            # Pattern 1: Direct relationship format "Relationship: A rel_type B"
            for line in lines:
                if line.startswith("Relationship:"):
                    rel_line = line.replace("Relationship:", "").strip()
                    rel_info = self._parse_relationship_line_enhanced(rel_line, entity_name)
                    if rel_info:
                        rel_info.update({
                            "fact": fact,
                            "uuid": fact_uuid,
                            "extraction_method": "direct_relationship"
                        })
                        relationships.append(rel_info)

            # Pattern 2: Structured entity facts (PERSON:/COMPANY: format)
            current_entity = None
            current_entity_type = None

            for line in lines:
                line = line.strip()
                if line.startswith("PERSON:"):
                    current_entity = line.replace("PERSON:", "").strip()
                    current_entity_type = "person"
                elif line.startswith("COMPANY:"):
                    current_entity = line.replace("COMPANY:", "").strip()
                    current_entity_type = "company"
                elif current_entity and ":" in line:
                    # Extract structured information
                    key, value = line.split(":", 1)
                    key = key.strip()
                    value = value.strip()

                    # Handle employment relationships
                    if key == "Current company" and current_entity_type == "person":
                        if entity_lower in current_entity.lower():
                            relationships.append({
                                "source_entity": current_entity,
                                "target_entity": value,
                                "relationship_type": "Employee_OF",
                                "direction": "outgoing",
                                "fact": fact,
                                "uuid": fact_uuid,
                                "extraction_method": "structured_entity"
                            })
                        elif entity_lower in value.lower():
                            relationships.append({
                                "source_entity": value,
                                "target_entity": current_entity,
                                "relationship_type": "Employs",
                                "direction": "incoming",
                                "fact": fact,
                                "uuid": fact_uuid,
                                "extraction_method": "structured_entity"
                            })

                    elif key == "Current position" and current_entity_type == "person":
                        # Determine executive level from position
                        exec_keywords = ["ceo", "cto", "cfo", "director", "executive", "chairman", "president", "chief"]
                        is_executive = any(keyword in value.lower() for keyword in exec_keywords)

                        if entity_lower in current_entity.lower() and is_executive:
                            relationships.append({
                                "source_entity": current_entity,
                                "target_entity": "Unknown Company",
                                "relationship_type": "Executive_OF",
                                "direction": "outgoing",
                                "details": value,
                                "fact": fact,
                                "uuid": fact_uuid,
                                "extraction_method": "position_based"
                            })

                    elif key == "Key executives" and current_entity_type == "company":
                        # Extract executive relationships from company facts
                        executives = [exec.strip() for exec in value.split(",")]
                        for exec_name in executives:
                            if entity_lower in exec_name.lower():
                                relationships.append({
                                    "source_entity": exec_name,
                                    "target_entity": current_entity,
                                    "relationship_type": "Executive_OF",
                                    "direction": "outgoing",
                                    "fact": fact,
                                    "uuid": fact_uuid,
                                    "extraction_method": "executive_list"
                                })
                            elif entity_lower in current_entity.lower():
                                relationships.append({
                                    "source_entity": current_entity,
                                    "target_entity": exec_name,
                                    "relationship_type": "Employs",
                                    "direction": "incoming",
                                    "details": "Executive",
                                    "fact": fact,
                                    "uuid": fact_uuid,
                                    "extraction_method": "executive_list"
                                })

            # Pattern 3: Natural language relationship patterns
            relationship_patterns = [
                # Employment patterns
                (r"(\w+(?:\s+\w+)*)\s+(?:is|was|serves as|works as)\s+(?:the\s+)?([^.]+?)\s+(?:at|of|for)\s+([^.]+)", "employment"),
                (r"(\w+(?:\s+\w+)*)\s+(?:CEO|CTO|CFO|Director|Executive|Chairman|President)\s+(?:of|at)\s+([^.]+)", "executive"),
                (r"([^.]+?)\s+employs?\s+(\w+(?:\s+\w+)*)\s+as\s+([^.]+)", "employment_reverse"),
                # Ownership patterns
                (r"(\w+(?:\s+\w+)*)\s+owns?\s+([^.]+)", "ownership"),
                (r"([^.]+?)\s+(?:is\s+)?owned\s+by\s+(\w+(?:\s+\w+)*)", "ownership_reverse"),
                # Corporate structure patterns
                (r"([^.]+?)\s+(?:is\s+a\s+)?subsidiary\s+of\s+([^.]+)", "subsidiary"),
                (r"([^.]+?)\s+(?:is\s+a\s+)?shareholder\s+(?:in|of)\s+([^.]+)", "shareholder")
            ]

            for pattern, rel_category in relationship_patterns:
                matches = re.finditer(pattern, fact, re.IGNORECASE)
                for match in matches:
                    groups = match.groups()
                    if len(groups) >= 2:
                        entity1 = groups[0].strip()
                        entity2 = groups[1].strip() if len(groups) == 2 else groups[2].strip()
                        position = groups[1].strip() if len(groups) == 3 and rel_category == "employment" else None

                        # Determine relationship type based on category
                        if rel_category == "employment":
                            rel_type = "Executive_OF" if position and any(exec_word in position.lower() for exec_word in ["ceo", "cto", "cfo", "director", "executive", "chairman", "president"]) else "Employee_OF"
                        elif rel_category == "executive":
                            rel_type = "Executive_OF"
                        elif rel_category == "employment_reverse":
                            rel_type = "Employs"
                            entity1, entity2 = entity2, entity1  # Swap for correct direction
                        elif rel_category == "ownership":
                            rel_type = "Owns"
                        elif rel_category == "ownership_reverse":
                            rel_type = "Owned_BY"
                        elif rel_category == "subsidiary":
                            rel_type = "Subsidiary_OF"
                        elif rel_category == "shareholder":
                            rel_type = "Shareholder_OF"
                        else:
                            rel_type = "Related_TO"

                        # Check if this involves our entity
                        if (entity_lower in entity1.lower() or entity_lower in entity2.lower()):
                            if entity_lower in entity1.lower():
                                direction = "outgoing"
                            else:
                                direction = "incoming"

                            rel_data = {
                                "source_entity": entity1,
                                "target_entity": entity2,
                                "relationship_type": rel_type,
                                "direction": direction,
                                "fact": fact,
                                "uuid": fact_uuid,
                                "extraction_method": f"pattern_{rel_category}"
                            }

                            if position:
                                rel_data["details"] = position

                            relationships.append(rel_data)

            # Pattern 4: Simple keyword-based extraction as fallback
            if not relationships and entity_name:  # Only if no other patterns matched
                keyword_patterns = {
                    "works at": "Employee_OF",
                    "employed by": "Employee_OF",
                    "ceo of": "CEO_OF",
                    "director of": "Director_OF",
                    "chairman of": "Chairman_OF",
                    "president of": "President_OF",
                    "executive of": "Executive_OF"
                }

                for keyword, rel_type in keyword_patterns.items():
                    if keyword in fact_lower:
                        # Try to extract the related entity
                        keyword_pos = fact_lower.find(keyword)
                        entity_pos = fact_lower.find(entity_lower)

                        if entity_pos < keyword_pos:
                            # Entity comes before keyword
                            after_keyword = fact[keyword_pos + len(keyword):].strip()
                            target = after_keyword.split('.')[0].split(',')[0].split('\n')[0].strip()
                            if target and len(target) > 1:
                                relationships.append({
                                    "source_entity": entity_name,
                                    "target_entity": target,
                                    "relationship_type": rel_type,
                                    "direction": "outgoing",
                                    "fact": fact,
                                    "uuid": fact_uuid,
                                    "extraction_method": "keyword_fallback"
                                })

        except Exception as e:
            logger.error(f"Failed to extract relationships from fact: {e}")

        return relationships

    def _parse_relationship_line_enhanced(self, rel_line: str, entity_name: str) -> Optional[Dict[str, Any]]:
        """
        Enhanced parsing of relationship line in format "Source relationship_type Target".

        Args:
            rel_line: The relationship line text
            entity_name: The entity we're searching for

        Returns:
            Parsed relationship info or None
        """
        try:
            # Split on common relationship patterns
            parts = rel_line.split()
            if len(parts) < 3:
                return None

            # Try to identify source, relationship, target
            # Handle multi-word entity names better
            entity_lower = entity_name.lower()

            # Find the relationship type (usually in the middle)
            # Look for common relationship patterns
            rel_type_candidates = []
            for i, part in enumerate(parts):
                if any(rel_word in part.lower() for rel_word in ["_of", "_by", "_with", "_to", "_for"]):
                    rel_type_candidates.append((i, part))

            if rel_type_candidates:
                # Use the first relationship type found
                rel_idx, relationship_type = rel_type_candidates[0]
                source_entity = " ".join(parts[:rel_idx])
                target_entity = " ".join(parts[rel_idx + 1:])
            else:
                # Fallback to simple parsing
                source_entity = parts[0]
                relationship_type = parts[1]
                target_entity = " ".join(parts[2:])

            # Determine direction relative to the queried entity
            if entity_lower in source_entity.lower():
                return {
                    "source_entity": source_entity,
                    "target_entity": target_entity,
                    "relationship_type": relationship_type,
                    "direction": "outgoing"
                }
            elif entity_lower in target_entity.lower():
                return {
                    "source_entity": source_entity,
                    "target_entity": target_entity,
                    "relationship_type": relationship_type,
                    "direction": "incoming"
                }

            return None

        except Exception as e:
            logger.error(f"Failed to parse relationship line '{rel_line}': {e}")
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
            # Handle both dict and object formats
            if isinstance(result, dict):
                fact = result.get("fact", "")
                uuid = result.get("uuid", "")
                valid_at = result.get("valid_at")
            else:
                fact = getattr(result, "fact", "")
                uuid = str(getattr(result, "uuid", ""))
                valid_at = str(result.valid_at) if hasattr(result, 'valid_at') and result.valid_at else None

            facts.append({
                "fact": fact,
                "uuid": uuid,
                "valid_at": valid_at
            })

            # Simple entity extraction from fact text (could be enhanced)
            if entity_name.lower() in fact.lower():
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
            # Handle both dict and object formats
            if isinstance(result, dict):
                fact = result.get("fact", "")
                uuid = result.get("uuid", "")
                valid_at = result.get("valid_at")
                invalid_at = result.get("invalid_at")
            else:
                fact = getattr(result, "fact", "")
                uuid = str(getattr(result, "uuid", ""))
                valid_at = str(result.valid_at) if hasattr(result, 'valid_at') and result.valid_at else None
                invalid_at = str(result.invalid_at) if hasattr(result, 'invalid_at') and result.invalid_at else None

            timeline.append({
                "fact": fact,
                "uuid": uuid,
                "valid_at": valid_at,
                "invalid_at": invalid_at
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


# Global Graphiti client instance (lazy initialization)
graph_client: Optional[GraphitiClient] = None


def get_graph_client() -> GraphitiClient:
    """Get or create the global graph client instance."""
    global graph_client
    if graph_client is None:
        graph_client = GraphitiClient()
    return graph_client


async def get_neo4j_driver():
    """
    Get the Neo4j driver from the Graphiti client.

    Returns:
        Neo4j driver instance
    """
    client = get_graph_client()
    if not client._initialized:
        await client.initialize()
    return client.graphiti.driver


def get_neo4j_database():
    """
    Get the Neo4j database name.

    Returns:
        Neo4j database name
    """
    client = get_graph_client()
    return client.neo4j_database


async def get_neo4j_session():
    """
    Get a Neo4j session with the correct database.

    Returns:
        Neo4j session instance
    """
    driver = await get_neo4j_driver()
    database = get_neo4j_database()
    return driver.session(database=database)


def get_neo4j_driver_sync():
    """
    Get a synchronous Neo4j driver (for use in non-async contexts).

    Returns:
        Synchronous Neo4j driver instance
    """
    from neo4j import GraphDatabase

    # Get Neo4j configuration
    client = get_graph_client()

    # Create a new synchronous driver directly
    return GraphDatabase.driver(
        client.neo4j_uri,
        auth=(client.neo4j_user, client.neo4j_password)
    )


def get_neo4j_session_sync():
    """
    Get a Neo4j session synchronously with the correct database.

    Returns:
        Synchronous Neo4j session instance
    """
    from neo4j import GraphDatabase

    # Get Neo4j configuration
    client = get_graph_client()

    # Create a new synchronous driver directly
    sync_driver = GraphDatabase.driver(
        client.neo4j_uri,
        auth=(client.neo4j_user, client.neo4j_password)
    )

    # Create a synchronous session
    return sync_driver.session(database=client.neo4j_database)


async def initialize_graph():
    """Initialize graph client."""
    client = get_graph_client()
    await client.initialize()


async def close_graph():
    """Close graph client."""
    client = get_graph_client()
    await client.close()


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
    
    await get_graph_client().add_episode(
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
    return await get_graph_client().search(query)


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
    return await get_graph_client().get_related_entities(entity, depth=depth)


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
    Creates both a Graphiti episode and a direct Neo4j Person node.

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
    # Create Person entity for Graphiti
    person = Person(
        name=name,
        person_type=person_type,
        current_company=current_company,
        current_position=current_position,
        **kwargs
    )

    # Add to Graphiti for episode tracking
    episode_id = await get_graph_client().add_entity(person, source_document)

    # Also create direct Neo4j Person node with proper label
    try:
        from agent.neo4j_schema_manager import Neo4jSchemaManager
        schema_manager = Neo4jSchemaManager()
        await schema_manager.initialize()

        # Prepare properties for Neo4j node
        node_properties = {
            "person_type": person_type.value if person_type else None,
            "current_company": current_company,
            "current_position": current_position,
            "source_document": source_document,
            **kwargs
        }

        # Create Person node with proper label
        node_uuid = await schema_manager.create_person_node(name, node_properties)
        logger.info(f"✓ Created Person node in Neo4j: {name} (UUID: {node_uuid})")

    except Exception as e:
        logger.warning(f"Failed to create direct Neo4j Person node for {name}: {e}")

    return episode_id


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
    Creates both a Graphiti episode and a direct Neo4j Company node.

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
    # Create Company entity for Graphiti
    company = Company(
        name=name,
        company_type=company_type,
        industry=industry,
        headquarters=headquarters,
        **kwargs
    )

    # Add to Graphiti for episode tracking
    episode_id = await get_graph_client().add_entity(company, source_document)

    # Also create direct Neo4j Company node with proper label
    try:
        from agent.neo4j_schema_manager import Neo4jSchemaManager
        schema_manager = Neo4jSchemaManager()
        await schema_manager.initialize()

        # Prepare properties for Neo4j node
        node_properties = {
            "company_type": company_type.value if company_type else None,
            "industry": industry,
            "headquarters": headquarters,
            "source_document": source_document,
            **kwargs
        }

        # Create Company node with proper label
        node_uuid = await schema_manager.create_company_node(name, node_properties)
        logger.info(f"✓ Created Company node in Neo4j: {name} (UUID: {node_uuid})")

    except Exception as e:
        logger.warning(f"Failed to create direct Neo4j Company node for {name}: {e}")

    return episode_id


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
    Creates both a Graphiti episode and a direct Neo4j relationship.

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
    # Create Relationship entity for Graphiti
    relationship = Relationship(
        source_entity_id=source_entity,
        target_entity_id=target_entity,
        relationship_type=relationship_type,
        description=description,
        strength=strength,
        **kwargs
    )

    # Add to Graphiti for episode tracking
    episode_id = await get_graph_client().add_relationship(relationship, source_document)

    # Also create direct Neo4j relationship
    try:
        from agent.neo4j_schema_manager import Neo4jSchemaManager
        schema_manager = Neo4jSchemaManager()
        await schema_manager.initialize()

        # Determine source and target types (simplified logic)
        # In a real implementation, you'd want to query the database to determine types
        source_type = "Person"  # Default assumption
        target_type = "Company"  # Default assumption

        # Create relationship with properties
        rel_properties = {
            "description": description,
            "strength": strength,
            "source_document": source_document,
            **kwargs
        }

        # Create relationship in Neo4j
        success = await schema_manager.create_relationship(
            source_entity, source_type,
            target_entity, target_type,
            relationship_type, rel_properties
        )

        if success:
            logger.info(f"✓ Created relationship in Neo4j: {source_entity} -{relationship_type}-> {target_entity}")

    except Exception as e:
        logger.warning(f"Failed to create direct Neo4j relationship: {e}")

    return episode_id


async def search_people(
    name_query: Optional[str] = None,
    company: Optional[str] = None,
    position: Optional[str] = None,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Enhanced search for people in the knowledge graph with case-insensitive matching.

    Args:
        name_query: Search by name (case-insensitive, partial matches allowed)
        company: Filter by company (case-insensitive)
        position: Filter by position (case-insensitive)
        limit: Maximum number of results

    Returns:
        List of person search results with enhanced relationship information
    """
    try:
        # First try enhanced Neo4j search for better results
        enhanced_results = await _enhanced_person_search_neo4j(
            name_query=name_query,
            company=company,
            position=position,
            limit=limit
        )

        if enhanced_results:
            logger.info(f"Enhanced Neo4j search found {len(enhanced_results)} results")
            return enhanced_results

        # Fallback to Graphiti search
        logger.info("Falling back to Graphiti search")
        query_parts = ["person"]
        if name_query:
            query_parts.append(f"named {name_query}")
        if company:
            query_parts.append(f"at {company}")
        if position:
            query_parts.append(f"with position {position}")

        query = " ".join(query_parts)
        results = await get_graph_client().search(query)
        return results[:limit]

    except Exception as e:
        logger.error(f"Person search failed: {e}")
        return []


async def _enhanced_person_search_neo4j(
    name_query: Optional[str] = None,
    company: Optional[str] = None,
    position: Optional[str] = None,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Enhanced person search using direct Neo4j queries with case-insensitive matching.

    Args:
        name_query: Search by name (case-insensitive)
        company: Filter by company (case-insensitive)
        position: Filter by position (case-insensitive)
        limit: Maximum number of results

    Returns:
        List of person search results with relationship information
    """
    try:
        from neo4j import GraphDatabase
        import os

        # Get Neo4j configuration
        neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        neo4j_user = os.getenv("NEO4J_USERNAME", os.getenv("NEO4J_USER", "neo4j"))
        neo4j_password = os.getenv("NEO4J_PASSWORD")
        neo4j_database = os.getenv("NEO4J_DATABASE", "neo4j")

        if not neo4j_password:
            logger.warning("Neo4j password not found, skipping enhanced search")
            return []

        # Create driver and session
        driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
        session = driver.session(database=neo4j_database)

        # Build WHERE conditions
        where_conditions = []
        params = {}

        if name_query:
            # Case-insensitive name search
            where_conditions.append("toLower(p.name) CONTAINS toLower($name_query)")
            params["name_query"] = name_query

        if company:
            # Case-insensitive company search
            where_conditions.append("toLower(p.company) CONTAINS toLower($company)")
            params["company"] = company

        if position:
            # Case-insensitive position search
            where_conditions.append("toLower(p.position) CONTAINS toLower($position)")
            params["position"] = position

        # Build the query
        where_clause = " AND ".join(where_conditions) if where_conditions else "true"

        cypher_query = f"""
        MATCH (p:Person)
        WHERE {where_clause}
        RETURN p.name as name,
               p.company as company,
               p.position as position,
               p.summary as summary,
               p.uuid as uuid,
               labels(p) as labels,
               p as person_node
        ORDER BY p.name
        LIMIT $limit
        """

        params["limit"] = limit

        logger.info(f"Executing enhanced person search: {cypher_query}")
        logger.info(f"Parameters: {params}")

        result = session.run(cypher_query, **params)
        records = list(result)

        enhanced_results = []
        for record in records:
            person_data = {
                "name": record.get("name"),
                "company": record.get("company"),
                "position": record.get("position"),
                "summary": record.get("summary", ""),
                "uuid": record.get("uuid"),
                "labels": record.get("labels", []),
                "search_method": "enhanced_neo4j",
                "relationships": []
            }

            # Extract relationships from summary and properties
            relationships = _extract_relationships_from_person(person_data)

            # Also search Graphiti for additional relationship information
            try:
                graphiti_relationships = await _extract_graphiti_relationships(person_data["name"])
                relationships.extend(graphiti_relationships)
            except Exception as e:
                logger.warning(f"Failed to extract Graphiti relationships for {person_data['name']}: {e}")

            # Remove duplicates based on relationship type and target
            seen = set()
            unique_relationships = []
            for rel in relationships:
                key = (rel["relationship_type"], rel["target"].lower())
                if key not in seen:
                    seen.add(key)
                    unique_relationships.append(rel)

            person_data["relationships"] = unique_relationships
            enhanced_results.append(person_data)

        session.close()
        driver.close()

        logger.info(f"Enhanced Neo4j search found {len(enhanced_results)} results")
        return enhanced_results

    except Exception as e:
        logger.error(f"Enhanced Neo4j person search failed: {e}")
        return []


def _extract_relationships_from_person(person_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract relationships from person data including summary text.

    Args:
        person_data: Person node data

    Returns:
        List of extracted relationships
    """
    relationships = []
    name = person_data.get("name", "")
    company = person_data.get("company")
    position = person_data.get("position", "")
    summary = person_data.get("summary", "")

    # Extract from company property
    if company:
        rel_type = "WORKS_AT"
        if position:
            if "ceo" in position.lower():
                rel_type = "CEO_OF"
            elif "chair" in position.lower() or "chairman" in position.lower():
                rel_type = "CHAIRMAN_OF"
            elif "director" in position.lower():
                rel_type = "DIRECTOR_OF"
            elif "executive" in position.lower():
                rel_type = "EXECUTIVE_OF"

        relationships.append({
            "source": name,
            "target": company,
            "relationship_type": rel_type,
            "relationship_detail": position,
            "extraction_method": "property_based"
        })

    # Extract from summary text
    if summary:
        # Look for CEO relationships
        if "ceo" in summary.lower():
            import re
            # Pattern to find "CEO of [Company]"
            ceo_pattern = r'(?:ceo|chief executive officer)\s+(?:of|at)\s+([^,.]+)'
            matches = re.findall(ceo_pattern, summary.lower())
            for match in matches:
                company_name = match.strip()
                if company_name and len(company_name) > 2:
                    relationships.append({
                        "source": name,
                        "target": company_name.title(),
                        "relationship_type": "CEO_OF",
                        "relationship_detail": "CEO",
                        "extraction_method": "summary_text"
                    })

        # Look for Chair relationships
        if "chair" in summary.lower():
            import re
            chair_pattern = r'(?:chair|chairman)\s+(?:of|at)\s+([^,.]+)'
            matches = re.findall(chair_pattern, summary.lower())
            for match in matches:
                company_name = match.strip()
                if company_name and len(company_name) > 2:
                    relationships.append({
                        "source": name,
                        "target": company_name.title(),
                        "relationship_type": "CHAIRMAN_OF",
                        "relationship_detail": "Chair",
                        "extraction_method": "summary_text"
                    })

    return relationships


async def _extract_graphiti_relationships(person_name: str) -> List[Dict[str, Any]]:
    """
    Extract additional relationships from Graphiti knowledge graph.

    Args:
        person_name: Name of the person

    Returns:
        List of relationships found in Graphiti
    """
    relationships = []

    try:
        # Search Graphiti for facts about this person
        from .tools import graph_search_tool, GraphSearchInput

        input_data = GraphSearchInput(query=person_name)
        graphiti_results = await graph_search_tool(input_data)

        for result in graphiti_results:
            fact = result.fact.lower()

            # Look for CEO relationships
            if "chief executive officer" in fact or "ceo" in fact:
                import re
                # Pattern to find "CEO of [Company]" or "Chief Executive Officer of [Company]"
                ceo_patterns = [
                    r'(?:ceo|chief executive officer)\s+of\s+([^,.]+)',
                    r'is\s+the\s+(?:ceo|chief executive officer)\s+of\s+([^,.]+)'
                ]

                for pattern in ceo_patterns:
                    matches = re.findall(pattern, fact)
                    for match in matches:
                        company_name = match.strip()
                        if company_name and len(company_name) > 2:
                            relationships.append({
                                "source": person_name,
                                "target": company_name.title(),
                                "relationship_type": "CEO_OF",
                                "relationship_detail": "Chief Executive Officer",
                                "extraction_method": "graphiti_fact"
                            })

            # Look for Chair relationships
            if "chair" in fact:
                import re
                chair_patterns = [
                    r'(?:chair|chairman)\s+of\s+([^,.]+)',
                    r'is\s+the\s+(?:chair|chairman)\s+of\s+([^,.]+)'
                ]

                for pattern in chair_patterns:
                    matches = re.findall(pattern, fact)
                    for match in matches:
                        company_name = match.strip()
                        if company_name and len(company_name) > 2:
                            relationships.append({
                                "source": person_name,
                                "target": company_name.title(),
                                "relationship_type": "CHAIRMAN_OF",
                                "relationship_detail": "Chair",
                                "extraction_method": "graphiti_fact"
                            })

        # Remove duplicates based on relationship type and target
        seen = set()
        unique_relationships = []
        for rel in relationships:
            key = (rel["relationship_type"], rel["target"].lower())
            if key not in seen:
                seen.add(key)
                unique_relationships.append(rel)

        logger.info(f"Extracted {len(unique_relationships)} unique relationships from Graphiti for {person_name}")
        return unique_relationships

    except Exception as e:
        logger.error(f"Failed to extract Graphiti relationships for {person_name}: {e}")
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
        results = await get_graph_client().search(query)
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
    return await get_graph_client().get_entity_relationships(person_name, relationship_types)


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
    return await get_graph_client().get_entity_relationships(company_name, relationship_types)


async def test_graph_connection() -> bool:
    """
    Test graph database connection.

    Returns:
        True if connection successful
    """
    try:
        client = get_graph_client()
        await client.initialize()
        stats = await client.get_graph_statistics()
        logger.info(f"Graph connection successful. Stats: {stats}")
        return True
    except Exception as e:
        logger.error(f"Graph connection test failed: {e}")
        return False