"""
Main Pydantic AI agent for agentic RAG with knowledge graph.
"""

import os
import logging
import re
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from pydantic_ai import Agent, RunContext
from dotenv import load_dotenv

from .prompts import SYSTEM_PROMPT
from .providers import get_llm_model
from .tools import (
    vector_search_tool,
    graph_search_tool,
    hybrid_search_tool,
    enhanced_hybrid_search_tool,
    get_document_tool,
    list_documents_tool,
    get_entity_relationships_tool,
    get_entity_timeline_tool,
    search_people_tool,
    search_companies_tool,
    get_entity_relationships_tool as get_structured_entity_relationships_tool,
    VectorSearchInput,
    GraphSearchInput,
    HybridSearchInput,
    EnhancedHybridSearchInput,
    DocumentInput,
    DocumentListInput,
    EntityRelationshipInput,
    EntityTimelineInput,
    PersonSearchInput,
    CompanySearchInput,
    EntityRelationshipSearchInput
)

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


@dataclass
class AgentDependencies:
    """Dependencies for the agent."""
    session_id: str
    user_id: Optional[str] = None
    search_preferences: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.search_preferences is None:
            self.search_preferences = {
                "use_vector": True,
                "use_graph": True,
                "default_limit": 10
            }


# Initialize the agent with flexible model configuration
rag_agent = Agent(
    get_llm_model(),
    deps_type=AgentDependencies,
    system_prompt=SYSTEM_PROMPT
)


# Register tools with proper docstrings (no description parameter)
@rag_agent.tool
async def vector_search(
    ctx: RunContext[AgentDependencies],
    query: str,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Search for relevant information using semantic similarity.
    
    This tool performs vector similarity search across document chunks
    to find semantically related content. Returns the most relevant results
    regardless of similarity score.
    
    Args:
        query: Search query to find similar content
        limit: Maximum number of results to return (1-50)
    
    Returns:
        List of matching chunks ordered by similarity (best first)
    """
    input_data = VectorSearchInput(
        query=query,
        limit=limit
    )
    
    results = await vector_search_tool(input_data)
    
    # Convert results to dict for agent
    return [
        {
            "content": r.content,
            "score": r.score,
            "document_title": r.document_title,
            "document_source": r.document_source,
            "chunk_id": r.chunk_id
        }
        for r in results
    ]


@rag_agent.tool
async def graph_search(
    ctx: RunContext[AgentDependencies],
    query: str
) -> List[Dict[str, Any]]:
    """
    Search the knowledge graph for facts and relationships.

    This tool queries the knowledge graph to find specific facts, relationships
    between entities, and temporal information. Best for finding specific facts,
    relationships between companies/people/technologies, and time-based information.
    Enhanced to extract relationships from facts automatically.

    Args:
        query: Search query to find facts and relationships

    Returns:
        List of facts with associated episodes, temporal data, and extracted relationships
    """
    # Check if this is a relationship query between two entities
    if _is_relationship_query(query):
        entities = _extract_entities_from_relationship_query(query)
        if len(entities) >= 2:
            # Use specialized relationship search
            return await _search_entity_relationships(entities[0], entities[1])

    input_data = GraphSearchInput(query=query)
    results = await graph_search_tool(input_data)

    # Convert results to dict for agent with enhanced relationship extraction
    enhanced_results = []
    for r in results:
        result_dict = {
            "fact": r.fact,
            "uuid": r.uuid,
            "valid_at": r.valid_at,
            "invalid_at": r.invalid_at,
            "source_node_uuid": r.source_node_uuid
        }

        # Try to extract relationships from the fact using the improved extraction
        try:
            # Import the enhanced extraction function that matches ingestion format
            from .tools import _extract_relationships_from_graphiti_fact

            # Extract any relationships mentioned in this fact
            relationships = _extract_relationships_from_graphiti_fact(r.fact, "", r.uuid)
            if relationships:
                result_dict["extracted_relationships"] = relationships
                result_dict["relationship_count"] = len(relationships)

                # Add a summary of relationship types found
                rel_types = list(set(rel.get("relationship_type", "Unknown") for rel in relationships))
                result_dict["relationship_types_found"] = rel_types
            else:
                result_dict["extracted_relationships"] = []
                result_dict["relationship_count"] = 0
                result_dict["relationship_types_found"] = []

        except Exception as e:
            logger.warning(f"Failed to extract relationships from fact: {e}")
            result_dict["extracted_relationships"] = []
            result_dict["relationship_count"] = 0
            result_dict["relationship_types_found"] = []

        enhanced_results.append(result_dict)

    return enhanced_results


@rag_agent.tool
async def find_relationship_between_entities(
    ctx: RunContext[AgentDependencies],
    entity1: str,
    entity2: str,
    search_depth: int = 2
) -> Dict[str, Any]:
    """
    Find relationships between two specific entities in the knowledge graph.

    This tool searches for direct and indirect connections between two entities
    (people, companies, or other entities). It explores multiple relationship
    paths and provides detailed information about how the entities are connected.

    Args:
        entity1: First entity name (e.g., "Michael T H Lee")
        entity2: Second entity name (e.g., "HKJC" or "Hong Kong Jockey Club")
        search_depth: Maximum depth to search for connections (1-3)

    Returns:
        Detailed relationship information including:
        - direct_relationships: Direct connections between the entities
        - indirect_relationships: Multi-hop connections
        - entity1_info: Information about the first entity
        - entity2_info: Information about the second entity
        - connection_strength: Overall strength of connection
    """
    try:
        logger.info(f"Searching for relationships between '{entity1}' and '{entity2}'")

        # Search for relationships using multiple strategies
        relationship_data = await _comprehensive_relationship_search(entity1, entity2, search_depth)

        return relationship_data

    except Exception as e:
        logger.error(f"Relationship search failed: {e}")
        return {
            "entity1": entity1,
            "entity2": entity2,
            "direct_relationships": [],
            "indirect_relationships": [],
            "entity1_info": {},
            "entity2_info": {},
            "connection_strength": 0.0,
            "error": str(e)
        }


@rag_agent.tool
async def hybrid_search(
    ctx: RunContext[AgentDependencies],
    query: str,
    limit: int = 10,
    text_weight: float = 0.3,
    enable_query_expansion: bool = True,
    enable_semantic_reranking: bool = True,
    enable_deduplication: bool = True,
    boost_recent_documents: bool = False
) -> List[Dict[str, Any]]:
    """
    Enhanced hybrid search combining vector similarity, keyword matching, and advanced features.

    This tool provides comprehensive search capabilities with:
    - Semantic similarity search using embeddings
    - Keyword matching with full-text search
    - Query expansion for better coverage
    - Semantic reranking for improved relevance
    - Result deduplication and clustering
    - Optional recency boosting

    Args:
        query: Search query for hybrid search
        limit: Maximum number of results to return (1-50)
        text_weight: Weight for text similarity vs vector similarity (0.0-1.0)
        enable_query_expansion: Whether to expand query with synonyms and related terms
        enable_semantic_reranking: Whether to apply semantic reranking to results
        enable_deduplication: Whether to remove duplicate or highly similar results
        boost_recent_documents: Whether to boost scores for more recent documents

    Returns:
        List of chunks ranked by enhanced relevance score with metadata
    """
    # Use enhanced hybrid search tool
    input_data = EnhancedHybridSearchInput(
        query=query,
        limit=limit * 2 if enable_deduplication else limit,  # Get more results for deduplication
        text_weight=text_weight,
        enable_query_expansion=enable_query_expansion,
        enable_semantic_reranking=enable_semantic_reranking,
        enable_deduplication=enable_deduplication,
        boost_recent_documents=boost_recent_documents
    )

    results = await enhanced_hybrid_search_tool(input_data)

    # Apply final limit after processing
    final_results = results[:limit]

    # Convert results to dict for agent with enhanced metadata
    return [
        {
            "content": r.content,
            "score": r.score,
            "document_title": r.document_title,
            "document_source": r.document_source,
            "chunk_id": r.chunk_id,
            "vector_similarity": getattr(r, 'vector_similarity', None),
            "text_similarity": getattr(r, 'text_similarity', None),
            "relevance_factors": getattr(r, 'relevance_factors', {}),
            "search_method": "enhanced_hybrid"
        }
        for r in final_results
    ]


@rag_agent.tool
async def comprehensive_search(
    ctx: RunContext[AgentDependencies],
    query: str,
    search_type: str = "auto",
    limit: int = 10,
    include_graph_facts: bool = True,
    include_entity_search: bool = True
) -> Dict[str, Any]:
    """
    Perform comprehensive search using multiple methods intelligently.

    This tool automatically selects the best search strategy based on the query
    and combines results from vector search, hybrid search, graph search, and
    entity-specific searches for maximum coverage and relevance.

    Args:
        query: Search query
        search_type: Search strategy ("auto", "semantic", "hybrid", "graph", "entities")
        limit: Maximum number of results per search type
        include_graph_facts: Whether to include knowledge graph facts
        include_entity_search: Whether to search for specific entities

    Returns:
        Comprehensive search results with metadata about search methods used
    """
    search_results = {
        "query": query,
        "search_strategy": search_type,
        "vector_results": [],
        "hybrid_results": [],
        "graph_results": [],
        "entity_results": {"people": [], "companies": []},
        "total_results": 0,
        "search_methods_used": [],
        "relevance_score": 0.0
    }

    try:
        # Determine search strategy
        if search_type == "auto":
            search_type = _determine_optimal_search_strategy(query)

        search_results["search_strategy"] = search_type

        # Execute searches based on strategy
        if search_type in ["semantic", "hybrid", "auto"]:
            # Enhanced hybrid search for comprehensive coverage
            hybrid_input = EnhancedHybridSearchInput(
                query=query,
                limit=limit,
                enable_query_expansion=True,
                enable_semantic_reranking=True,
                enable_deduplication=True
            )
            hybrid_results = await enhanced_hybrid_search_tool(hybrid_input)
            search_results["hybrid_results"] = [
                {
                    "content": r.content,
                    "score": r.score,
                    "document_title": r.document_title,
                    "document_source": r.document_source,
                    "chunk_id": r.chunk_id,
                    "search_method": "enhanced_hybrid"
                }
                for r in hybrid_results
            ]
            search_results["search_methods_used"].append("enhanced_hybrid")

        if search_type in ["graph", "auto"] and include_graph_facts:
            # Graph search for relationships and facts
            graph_input = GraphSearchInput(query=query)
            graph_results = await graph_search_tool(graph_input)
            search_results["graph_results"] = [
                {
                    "fact": r.fact,
                    "uuid": r.uuid,
                    "valid_at": r.valid_at,
                    "invalid_at": r.invalid_at,
                    "search_method": "knowledge_graph"
                }
                for r in graph_results
            ]
            search_results["search_methods_used"].append("knowledge_graph")

        if search_type in ["entities", "auto"] and include_entity_search:
            # Entity-specific searches
            if _contains_person_indicators(query):
                person_input = PersonSearchInput(name_query=query, limit=limit//2)
                people_results = await search_people_tool(person_input)
                search_results["entity_results"]["people"] = people_results
                search_results["search_methods_used"].append("person_search")

            if _contains_company_indicators(query):
                company_input = CompanySearchInput(name_query=query, limit=limit//2)
                company_results = await search_companies_tool(company_input)
                search_results["entity_results"]["companies"] = company_results
                search_results["search_methods_used"].append("company_search")

        # Calculate total results and relevance score
        total_results = (
            len(search_results["hybrid_results"]) +
            len(search_results["graph_results"]) +
            len(search_results["entity_results"]["people"]) +
            len(search_results["entity_results"]["companies"])
        )

        search_results["total_results"] = total_results
        search_results["relevance_score"] = _calculate_overall_relevance_score(search_results)

        return search_results

    except Exception as e:
        logger.error(f"Comprehensive search failed: {e}")
        search_results["error"] = str(e)
        return search_results


def _determine_optimal_search_strategy(query: str) -> str:
    """Determine the optimal search strategy based on query characteristics."""
    query_lower = query.lower()

    # Graph search indicators
    graph_indicators = ["relationship", "connection", "works at", "employed by", "partnership",
                       "acquisition", "merger", "investment", "funding", "board", "director"]

    # Entity search indicators
    entity_indicators = ["person", "people", "company", "companies", "ceo", "cfo", "executive"]

    # Semantic search indicators
    semantic_indicators = ["similar", "like", "about", "regarding", "concerning", "related to"]

    if any(indicator in query_lower for indicator in graph_indicators):
        return "graph"
    elif any(indicator in query_lower for indicator in entity_indicators):
        return "entities"
    elif any(indicator in query_lower for indicator in semantic_indicators):
        return "semantic"
    else:
        return "hybrid"


def _contains_person_indicators(query: str) -> bool:
    """Check if query contains person-related indicators."""
    person_indicators = ["person", "people", "ceo", "cfo", "cto", "director", "executive",
                        "manager", "president", "chairman", "officer", "employee"]
    return any(indicator in query.lower() for indicator in person_indicators)


def _contains_company_indicators(query: str) -> bool:
    """Check if query contains company-related indicators."""
    company_indicators = ["company", "companies", "corporation", "firm", "business",
                         "organization", "enterprise", "startup", "inc", "ltd", "corp"]
    return any(indicator in query.lower() for indicator in company_indicators)


def _calculate_overall_relevance_score(search_results: Dict[str, Any]) -> float:
    """Calculate overall relevance score based on search results."""
    try:
        total_results = search_results["total_results"]
        if total_results == 0:
            return 0.0

        # Weight different search methods
        score = 0.0

        # Hybrid search results (highest weight)
        hybrid_count = len(search_results["hybrid_results"])
        if hybrid_count > 0:
            avg_hybrid_score = sum(r.get("score", 0) for r in search_results["hybrid_results"]) / hybrid_count
            score += avg_hybrid_score * 0.5

        # Graph results (medium weight)
        graph_count = len(search_results["graph_results"])
        if graph_count > 0:
            score += min(graph_count / 5.0, 1.0) * 0.3  # Normalize to max 1.0

        # Entity results (lower weight)
        entity_count = len(search_results["entity_results"]["people"]) + len(search_results["entity_results"]["companies"])
        if entity_count > 0:
            score += min(entity_count / 5.0, 1.0) * 0.2  # Normalize to max 1.0

        return min(score, 1.0)  # Cap at 1.0

    except Exception:
        return 0.0


@rag_agent.tool
async def get_document(
    ctx: RunContext[AgentDependencies],
    document_id: str
) -> Optional[Dict[str, Any]]:
    """
    Retrieve the complete content of a specific document.
    
    This tool fetches the full document content along with all its chunks
    and metadata. Best for getting comprehensive information from a specific
    source when you need the complete context.
    
    Args:
        document_id: UUID of the document to retrieve
    
    Returns:
        Complete document data with content and metadata, or None if not found
    """
    input_data = DocumentInput(document_id=document_id)
    
    document = await get_document_tool(input_data)
    
    if document:
        # Format for agent consumption
        return {
            "id": document["id"],
            "title": document["title"],
            "source": document["source"],
            "content": document["content"],
            "chunk_count": len(document.get("chunks", [])),
            "created_at": document["created_at"]
        }
    
    return None


@rag_agent.tool
async def list_documents(
    ctx: RunContext[AgentDependencies],
    limit: int = 20,
    offset: int = 0
) -> List[Dict[str, Any]]:
    """
    List available documents with their metadata.
    
    This tool provides an overview of all documents in the knowledge base,
    including titles, sources, and chunk counts. Best for understanding
    what information sources are available.
    
    Args:
        limit: Maximum number of documents to return (1-100)
        offset: Number of documents to skip for pagination
    
    Returns:
        List of documents with metadata and chunk counts
    """
    input_data = DocumentListInput(limit=limit, offset=offset)
    
    documents = await list_documents_tool(input_data)
    
    # Convert to dict for agent
    return [
        {
            "id": d.id,
            "title": d.title,
            "source": d.source,
            "chunk_count": d.chunk_count,
            "created_at": d.created_at.isoformat()
        }
        for d in documents
    ]


@rag_agent.tool
async def get_entity_relationships(
    ctx: RunContext[AgentDependencies],
    entity_name: str,
    depth: int = 2
) -> Dict[str, Any]:
    """
    Get all relationships for a specific entity in the knowledge graph.
    
    This tool explores the knowledge graph to find how a specific entity
    (company, person, technology) relates to other entities. Best for
    understanding how companies or technologies relate to each other.
    
    Args:
        entity_name: Name of the entity to explore (e.g., "Google", "OpenAI")
        depth: Maximum traversal depth for relationships (1-5)
    
    Returns:
        Entity relationships and connected entities with relationship types
    """
    input_data = EntityRelationshipInput(
        entity_name=entity_name,
        depth=depth
    )
    
    return await get_entity_relationships_tool(input_data)


@rag_agent.tool
async def get_entity_timeline(
    ctx: RunContext[AgentDependencies],
    entity_name: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Get the timeline of facts for a specific entity.
    
    This tool retrieves chronological information about an entity,
    showing how information has evolved over time. Best for understanding
    how information about an entity has developed or changed.
    
    Args:
        entity_name: Name of the entity (e.g., "Microsoft", "AI")
        start_date: Start date in ISO format (YYYY-MM-DD), optional
        end_date: End date in ISO format (YYYY-MM-DD), optional
    
    Returns:
        Chronological list of facts about the entity with timestamps
    """
    input_data = EntityTimelineInput(
        entity_name=entity_name,
        start_date=start_date,
        end_date=end_date
    )
    
    return await get_entity_timeline_tool(input_data)


@rag_agent.tool
async def search_people(
    ctx: RunContext[AgentDependencies],
    name_query: Optional[str] = None,
    company: Optional[str] = None,
    position: Optional[str] = None,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Search for person nodes in the knowledge graph.

    This tool searches for individuals based on their name, company affiliation,
    or job position. Best for finding specific people or people with certain roles.

    Args:
        name_query: Search by person's name (partial matches allowed)
        company: Filter by company name
        position: Filter by job title or position
        limit: Maximum number of results to return (1-50)

    Returns:
        List of person nodes matching the search criteria with their details
    """
    input_data = PersonSearchInput(
        name_query=name_query,
        company=company,
        position=position,
        limit=limit
    )

    return await search_people_tool(input_data)


@rag_agent.tool
async def search_companies(
    ctx: RunContext[AgentDependencies],
    name_query: Optional[str] = None,
    industry: Optional[str] = None,
    location: Optional[str] = None,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Search for company nodes in the knowledge graph.

    This tool searches for companies based on their name, industry,
    or location. Best for finding specific companies or companies in certain sectors.

    Args:
        name_query: Search by company name (partial matches allowed)
        industry: Filter by industry or sector
        location: Filter by headquarters or operating location
        limit: Maximum number of results to return (1-50)

    Returns:
        List of company nodes matching the search criteria with their details
    """
    input_data = CompanySearchInput(
        name_query=name_query,
        industry=industry,
        location=location,
        limit=limit
    )

    return await search_companies_tool(input_data)


@rag_agent.tool
async def get_structured_entity_relationships(
    ctx: RunContext[AgentDependencies],
    entity_name: str,
    entity_type: Optional[str] = None,
    relationship_types: Optional[List[str]] = None,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Get structured relationships for a specific node (person or company).

    This tool finds detailed relationships for nodes with specific relationship
    types and directions. Best for understanding professional connections,
    corporate structures, and business relationships. Uses enhanced extraction
    to handle various fact formats from the knowledge graph.

    Args:
        entity_name: Name of the node to explore
        entity_type: Type of node ("person" or "company")
        relationship_types: Filter by specific relationship types
        limit: Maximum number of results to return (1-50)

    Returns:
        List of structured relationships with detailed metadata including:
        - source_entity: The source entity in the relationship
        - target_entity: The target entity in the relationship
        - relationship_type: Type of relationship (e.g., "Executive_OF", "Employee_OF")
        - direction: "outgoing" or "incoming" relative to the queried entity
        - fact: The original fact text from the knowledge graph
        - uuid: Unique identifier for the fact
        - extraction_method: Method used to extract the relationship
        - details: Additional details about the relationship (if available)
    """
    input_data = EntityRelationshipSearchInput(
        entity_name=entity_name,
        entity_type=entity_type,
        relationship_types=relationship_types,
        limit=limit
    )

    results = await get_entity_relationships_tool(input_data)

    # Format results for better agent consumption
    formatted_results = []
    for result in results:
        formatted_result = {
            "source_entity": result.get("source_entity", "Unknown"),
            "target_entity": result.get("target_entity", "Unknown"),
            "relationship_type": result.get("relationship_type", "Unknown"),
            "direction": result.get("direction", "unknown"),
            "fact_uuid": result.get("uuid", ""),
            "extraction_method": result.get("extraction_method", "standard"),
            "original_fact": result.get("fact", "")
        }

        # Add details if available
        if "details" in result:
            formatted_result["details"] = result["details"]

        # Add relationship summary for easy reading
        if result.get("direction") == "outgoing":
            formatted_result["relationship_summary"] = f"{entity_name} {result.get('relationship_type', 'relates to')} {result.get('target_entity', 'Unknown')}"
        else:
            formatted_result["relationship_summary"] = f"{result.get('source_entity', 'Unknown')} {result.get('relationship_type', 'relates to')} {entity_name}"

        formatted_results.append(formatted_result)

    return formatted_results


# Helper functions for relationship search

def _is_relationship_query(query: str) -> bool:
    """Check if query is asking about relationships between entities."""
    relationship_indicators = [
        "relation between", "relationship between", "connection between",
        "how is", "connected to", "related to", "works with",
        "associated with", "link between", "ties between"
    ]
    query_lower = query.lower()
    return any(indicator in query_lower for indicator in relationship_indicators)


def _extract_entities_from_relationship_query(query: str) -> List[str]:
    """Extract entity names from a relationship query."""
    import re

    # Common patterns for relationship queries
    patterns = [
        r"relation(?:ship)?\s+between\s+(.+?)\s+and\s+(.+?)(?:\s|$|\?)",
        r"connection\s+between\s+(.+?)\s+and\s+(.+?)(?:\s|$|\?)",
        r"how\s+is\s+(.+?)\s+(?:related\s+to|connected\s+to)\s+(.+?)(?:\s|$|\?)",
        r"(.+?)\s+(?:related\s+to|connected\s+to|works\s+with)\s+(.+?)(?:\s|$|\?)"
    ]

    query_lower = query.lower().strip()

    for pattern in patterns:
        match = re.search(pattern, query_lower)
        if match:
            entity1 = match.group(1).strip()
            entity2 = match.group(2).strip()

            # Clean up entity names
            entity1 = _clean_entity_name(entity1)
            entity2 = _clean_entity_name(entity2)

            return [entity1, entity2]

    return []


def _clean_entity_name(name: str) -> str:
    """Clean and normalize entity names."""
    # Remove common words and punctuation
    name = name.strip()

    # Remove question marks and other punctuation
    name = re.sub(r'[?!.,;]', '', name)

    # Handle common abbreviations and variations
    name_mapping = {
        "hkjc": "Hong Kong Jockey Club",
        "hong kong jockey club": "Hong Kong Jockey Club",
        "the hong kong jockey club": "Hong Kong Jockey Club"
    }

    name_lower = name.lower()
    if name_lower in name_mapping:
        return name_mapping[name_lower]

    return name.title()  # Capitalize properly


async def _search_entity_relationships(entity1: str, entity2: str) -> List[Dict[str, Any]]:
    """Search for relationships between two specific entities."""
    try:
        # Import here to avoid circular imports
        from .graph_utils import search_knowledge_graph

        # Multiple search strategies for finding relationships
        search_queries = [
            f"{entity1} {entity2}",
            f"{entity1} and {entity2}",
            f"relationship {entity1} {entity2}",
            f"{entity1} works at {entity2}",
            f"{entity1} employed by {entity2}",
            f"{entity1} director of {entity2}",
            f"{entity1} executive of {entity2}",
            f"{entity2} {entity1}",
            f"facts about {entity1} {entity2}"
        ]

        all_results = []
        seen_facts = set()

        for query in search_queries:
            try:
                results = await search_knowledge_graph(query)

                for result in results:
                    fact = result.get("fact", "")
                    if fact and fact not in seen_facts:
                        seen_facts.add(fact)

                        # Check if both entities are mentioned in the fact
                        fact_lower = fact.lower()
                        entity1_lower = entity1.lower()
                        entity2_lower = entity2.lower()

                        if entity1_lower in fact_lower and entity2_lower in fact_lower:
                            result["relevance_score"] = 1.0
                            result["search_query"] = query
                            all_results.append(result)
                        elif entity1_lower in fact_lower or entity2_lower in fact_lower:
                            result["relevance_score"] = 0.5
                            result["search_query"] = query
                            all_results.append(result)

            except Exception as e:
                logger.warning(f"Search query '{query}' failed: {e}")
                continue

        # Sort by relevance score
        all_results.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)

        return all_results

    except Exception as e:
        logger.error(f"Entity relationship search failed: {e}")
        return []


async def _comprehensive_relationship_search(entity1: str, entity2: str, search_depth: int = 2) -> Dict[str, Any]:
    """Perform comprehensive relationship search between two entities."""
    try:
        # Import here to avoid circular imports
        from .tools import get_enhanced_entity_relationships

        result = {
            "entity1": entity1,
            "entity2": entity2,
            "direct_relationships": [],
            "indirect_relationships": [],
            "entity1_info": {},
            "entity2_info": {},
            "connection_strength": 0.0,
            "search_method": "comprehensive_graphiti_search"
        }

        # 1. Search for direct relationships
        direct_results = await _search_entity_relationships(entity1, entity2)
        result["direct_relationships"] = direct_results

        # 2. Get information about each entity individually
        try:
            entity1_relationships = await get_enhanced_entity_relationships(
                entity_name=entity1,
                entity_type="person",  # Try person first
                limit=10
            )
            result["entity1_info"] = {
                "name": entity1,
                "relationships": entity1_relationships[:5],  # Top 5 relationships
                "total_relationships": len(entity1_relationships)
            }
        except Exception as e:
            logger.warning(f"Failed to get entity1 info: {e}")

        try:
            entity2_relationships = await get_enhanced_entity_relationships(
                entity_name=entity2,
                entity_type="company",  # Try company first
                limit=10
            )
            result["entity2_info"] = {
                "name": entity2,
                "relationships": entity2_relationships[:5],  # Top 5 relationships
                "total_relationships": len(entity2_relationships)
            }
        except Exception as e:
            logger.warning(f"Failed to get entity2 info: {e}")

        # 3. Calculate connection strength
        connection_strength = 0.0
        if direct_results:
            # Strong connection if direct relationships found
            high_relevance_count = sum(1 for r in direct_results if r.get("relevance_score", 0) >= 1.0)
            connection_strength = min(1.0, high_relevance_count * 0.3 + len(direct_results) * 0.1)

        result["connection_strength"] = connection_strength

        # 4. Add summary
        if direct_results:
            result["summary"] = f"Found {len(direct_results)} potential connections between {entity1} and {entity2}"
        else:
            result["summary"] = f"No direct connections found between {entity1} and {entity2} in the knowledge graph"

        return result

    except Exception as e:
        logger.error(f"Comprehensive relationship search failed: {e}")
        return {
            "entity1": entity1,
            "entity2": entity2,
            "direct_relationships": [],
            "indirect_relationships": [],
            "entity1_info": {},
            "entity2_info": {},
            "connection_strength": 0.0,
            "error": str(e)
        }