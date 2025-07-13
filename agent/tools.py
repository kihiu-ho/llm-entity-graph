"""
Tools for the Pydantic AI agent.
"""

import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio

from pydantic import BaseModel, Field
from dotenv import load_dotenv

from .db_utils import (
    vector_search,
    hybrid_search,
    get_document,
    list_documents,
    get_document_chunks
)
from .graph_utils import (
    search_knowledge_graph,
    get_entity_relationships,
    search_people,
    search_companies,
    get_person_relationships,
    get_company_relationships,
    graph_client
)
from .entity_models import EntityType, PersonType, CompanyType
from .models import ChunkResult, GraphSearchResult, DocumentMetadata
from .providers import get_embedding_client, get_embedding_model

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Initialize embedding client with flexible provider
embedding_client = get_embedding_client()
EMBEDDING_MODEL = get_embedding_model()


async def generate_embedding(text: str) -> List[float]:
    """
    Generate embedding for text using OpenAI with proper token limiting.

    Args:
        text: Text to embed

    Returns:
        Embedding vector
    """
    try:
        # Import here to avoid circular imports
        from ..ingestion.embedder import EmbeddingGenerator

        # Use the proper embedder with token limiting
        embedder = EmbeddingGenerator(model=EMBEDDING_MODEL)
        return await embedder.generate_embedding(text)

    except ImportError:
        # Fallback to direct API call with basic truncation
        logger.warning("Using fallback embedding generation without advanced token limiting")

        # Basic character-based truncation as fallback
        max_chars = 8191 * 4  # Rough estimation
        if len(text) > max_chars:
            text = text[:max_chars]
            logger.warning(f"Text truncated to {max_chars} characters for embedding")

        try:
            response = await embedding_client.embeddings.create(
                model=EMBEDDING_MODEL,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise
    except Exception as e:
        logger.error(f"Failed to generate embedding: {e}")
        raise


# Tool Input Models
class VectorSearchInput(BaseModel):
    """Input for vector search tool."""
    query: str = Field(..., description="Search query")
    limit: int = Field(default=10, description="Maximum number of results")


class GraphSearchInput(BaseModel):
    """Input for graph search tool."""
    query: str = Field(..., description="Search query")


class HybridSearchInput(BaseModel):
    """Input for hybrid search tool."""
    query: str = Field(..., description="Search query")
    limit: int = Field(default=10, description="Maximum number of results")
    text_weight: float = Field(default=0.3, description="Weight for text similarity (0-1)")


class EnhancedHybridSearchInput(BaseModel):
    """Input for enhanced hybrid search tool."""
    query: str = Field(..., description="Search query")
    limit: int = Field(default=10, description="Maximum number of results")
    text_weight: float = Field(default=0.3, description="Weight for text similarity (0-1)")
    enable_query_expansion: bool = Field(default=True, description="Enable query expansion")
    enable_semantic_reranking: bool = Field(default=True, description="Enable semantic reranking")
    enable_deduplication: bool = Field(default=True, description="Enable result deduplication")
    boost_recent_documents: bool = Field(default=False, description="Boost recent documents")


class DocumentInput(BaseModel):
    """Input for document retrieval."""
    document_id: str = Field(..., description="Document ID to retrieve")


class DocumentListInput(BaseModel):
    """Input for listing documents."""
    limit: int = Field(default=20, description="Maximum number of documents")
    offset: int = Field(default=0, description="Number of documents to skip")


class EntityRelationshipInput(BaseModel):
    """Input for entity relationship query."""
    entity_name: str = Field(..., description="Name of the entity")
    depth: int = Field(default=2, description="Maximum traversal depth")


class EntityTimelineInput(BaseModel):
    """Input for entity timeline query."""
    entity_name: str = Field(..., description="Name of the entity")
    start_date: Optional[str] = Field(None, description="Start date (ISO format)")
    end_date: Optional[str] = Field(None, description="End date (ISO format)")


class PersonSearchInput(BaseModel):
    """Input for person search."""
    name_query: Optional[str] = Field(None, description="Search by person name")
    company: Optional[str] = Field(None, description="Filter by company")
    position: Optional[str] = Field(None, description="Filter by position/title")
    limit: int = Field(default=10, description="Maximum number of results")


class CompanySearchInput(BaseModel):
    """Input for company search."""
    name_query: Optional[str] = Field(None, description="Search by company name")
    industry: Optional[str] = Field(None, description="Filter by industry")
    location: Optional[str] = Field(None, description="Filter by location")
    limit: int = Field(default=10, description="Maximum number of results")


class EntityRelationshipSearchInput(BaseModel):
    """Input for node relationship search."""
    entity_name: str = Field(..., description="Name of the node")
    entity_type: Optional[str] = Field(None, description="Type of node (person/company)")
    relationship_types: Optional[List[str]] = Field(None, description="Filter by relationship types")
    limit: int = Field(default=10, description="Maximum number of results")


# Tool Implementation Functions
async def vector_search_tool(input_data: VectorSearchInput) -> List[ChunkResult]:
    """
    Perform vector similarity search.
    
    Args:
        input_data: Search parameters
    
    Returns:
        List of matching chunks
    """
    try:
        # Generate embedding for the query
        embedding = await generate_embedding(input_data.query)
        
        # Perform vector search
        results = await vector_search(
            embedding=embedding,
            limit=input_data.limit
        )

        # Convert to ChunkResult models
        return [
            ChunkResult(
                chunk_id=str(r["chunk_id"]),
                document_id=str(r["document_id"]),
                content=r["content"],
                score=r["similarity"],
                metadata=r["metadata"],
                document_title=r["document_title"],
                document_source=r["document_source"]
            )
            for r in results
        ]
        
    except Exception as e:
        logger.error(f"Vector search failed: {e}")
        return []


async def graph_search_tool(input_data: GraphSearchInput) -> List[GraphSearchResult]:
    """
    Enhanced search of the knowledge graph with multiple search strategies.

    Args:
        input_data: Search parameters

    Returns:
        List of graph search results
    """
    try:
        # Use multiple search strategies for better coverage
        all_results = []
        seen_facts = set()

        # Strategy 1: Direct search
        try:
            results = await search_knowledge_graph(query=input_data.query)
            for r in results:
                fact = r.get("fact", "")
                if fact and fact not in seen_facts:
                    seen_facts.add(fact)
                    all_results.append(r)
        except Exception as e:
            logger.warning(f"Direct search failed: {e}")

        # Strategy 2: Enhanced search with variations
        query_variations = _generate_query_variations(input_data.query)
        for variation in query_variations:
            try:
                results = await search_knowledge_graph(query=variation)
                for r in results:
                    fact = r.get("fact", "")
                    if fact and fact not in seen_facts:
                        seen_facts.add(fact)
                        r["search_variation"] = variation
                        all_results.append(r)
            except Exception as e:
                logger.warning(f"Variation search '{variation}' failed: {e}")

        # Convert to GraphSearchResult models
        graph_results = []
        for r in all_results:
            graph_result = GraphSearchResult(
                fact=r["fact"],
                uuid=r["uuid"],
                valid_at=r.get("valid_at"),
                invalid_at=r.get("invalid_at"),
                source_node_uuid=r.get("source_node_uuid")
            )
            # Add search metadata
            graph_result.search_variation = r.get("search_variation")
            graph_results.append(graph_result)

        return graph_results

    except Exception as e:
        logger.error(f"Graph search failed: {e}")
        return []


def _generate_query_variations(query: str) -> List[str]:
    """Generate variations of the search query for better coverage."""
    variations = []

    # Add basic variations
    variations.append(f"facts about {query}")
    variations.append(f"information about {query}")
    variations.append(f"relationships involving {query}")

    # Handle entity name variations
    if " " in query:
        # Try with different word orders
        words = query.split()
        if len(words) == 2:
            variations.append(f"{words[1]} {words[0]}")

        # Try individual words
        for word in words:
            if len(word) > 2:  # Skip short words
                variations.append(word)

    # Handle common abbreviations and expansions
    abbreviation_map = {
        "HKJC": "Hong Kong Jockey Club",
        "Hong Kong Jockey Club": "HKJC",
        "CEO": "Chief Executive Officer",
        "CFO": "Chief Financial Officer",
        "CTO": "Chief Technology Officer"
    }

    query_upper = query.upper()
    for abbrev, expansion in abbreviation_map.items():
        if abbrev.upper() in query_upper:
            variations.append(query.replace(abbrev, expansion))
            variations.append(query.replace(abbrev.upper(), expansion))
        elif expansion.upper() in query_upper:
            variations.append(query.replace(expansion, abbrev))

    # Remove duplicates and return
    return list(set(variations))[:5]  # Limit to 5 variations


async def hybrid_search_tool(input_data: HybridSearchInput) -> List[ChunkResult]:
    """
    Perform hybrid search (vector + keyword).
    
    Args:
        input_data: Search parameters
    
    Returns:
        List of matching chunks
    """
    try:
        # Generate embedding for the query
        embedding = await generate_embedding(input_data.query)
        
        # Perform hybrid search
        results = await hybrid_search(
            embedding=embedding,
            query_text=input_data.query,
            limit=input_data.limit,
            text_weight=input_data.text_weight
        )
        
        # Convert to ChunkResult models
        return [
            ChunkResult(
                chunk_id=str(r["chunk_id"]),
                document_id=str(r["document_id"]),
                content=r["content"],
                score=r["combined_score"],
                metadata=r["metadata"],
                document_title=r["document_title"],
                document_source=r["document_source"]
            )
            for r in results
        ]
        
    except Exception as e:
        logger.error(f"Hybrid search failed: {e}")
        return []


async def enhanced_hybrid_search_tool(input_data: EnhancedHybridSearchInput) -> List[ChunkResult]:
    """
    Perform enhanced hybrid search with advanced features.

    Args:
        input_data: Enhanced search parameters

    Returns:
        List of matching chunks with enhanced scoring
    """
    try:
        # Step 1: Query preprocessing and expansion
        processed_query = input_data.query
        if input_data.enable_query_expansion:
            processed_query = await _expand_query(input_data.query)

        # Step 2: Generate embedding for the processed query
        embedding = await generate_embedding(processed_query)

        # Step 3: Perform enhanced hybrid search
        results = await enhanced_hybrid_search(
            embedding=embedding,
            query_text=processed_query,
            original_query=input_data.query,
            limit=input_data.limit,
            text_weight=input_data.text_weight,
            boost_recent_documents=input_data.boost_recent_documents
        )

        # Step 4: Apply semantic reranking if enabled
        if input_data.enable_semantic_reranking and len(results) > 1:
            results = await _apply_semantic_reranking(results, input_data.query)

        # Step 5: Apply deduplication if enabled
        if input_data.enable_deduplication and len(results) > 1:
            results = await _deduplicate_results(results)

        # Convert to ChunkResult models with enhanced metadata
        enhanced_results = []
        for r in results:
            chunk_result = ChunkResult(
                chunk_id=str(r["chunk_id"]),
                document_id=str(r["document_id"]),
                content=r["content"],
                score=r["enhanced_score"],
                metadata=r["metadata"],
                document_title=r["document_title"],
                document_source=r["document_source"]
            )

            # Add enhanced metadata
            chunk_result.vector_similarity = r.get("vector_similarity", 0.0)
            chunk_result.text_similarity = r.get("text_similarity", 0.0)
            chunk_result.relevance_factors = r.get("relevance_factors", {})

            enhanced_results.append(chunk_result)

        return enhanced_results

    except Exception as e:
        logger.error(f"Enhanced hybrid search failed: {e}")
        return []


async def get_document_tool(input_data: DocumentInput) -> Optional[Dict[str, Any]]:
    """
    Retrieve a complete document.
    
    Args:
        input_data: Document retrieval parameters
    
    Returns:
        Document data or None
    """
    try:
        document = await get_document(input_data.document_id)
        
        if document:
            # Also get all chunks for the document
            chunks = await get_document_chunks(input_data.document_id)
            document["chunks"] = chunks
        
        return document
        
    except Exception as e:
        logger.error(f"Document retrieval failed: {e}")
        return None


async def list_documents_tool(input_data: DocumentListInput) -> List[DocumentMetadata]:
    """
    List available documents.
    
    Args:
        input_data: Listing parameters
    
    Returns:
        List of document metadata
    """
    try:
        documents = await list_documents(
            limit=input_data.limit,
            offset=input_data.offset
        )
        
        # Convert to DocumentMetadata models
        return [
            DocumentMetadata(
                id=d["id"],
                title=d["title"],
                source=d["source"],
                metadata=d["metadata"],
                created_at=datetime.fromisoformat(d["created_at"]),
                updated_at=datetime.fromisoformat(d["updated_at"]),
                chunk_count=d.get("chunk_count")
            )
            for d in documents
        ]
        
    except Exception as e:
        logger.error(f"Document listing failed: {e}")
        return []


async def get_entity_relationships_tool(input_data: EntityRelationshipInput) -> Dict[str, Any]:
    """
    Get relationships for an entity.
    
    Args:
        input_data: Entity relationship parameters
    
    Returns:
        Entity relationships
    """
    try:
        return await get_entity_relationships(
            entity=input_data.entity_name,
            depth=input_data.depth
        )
        
    except Exception as e:
        logger.error(f"Entity relationship query failed: {e}")
        return {
            "central_entity": input_data.entity_name,
            "related_entities": [],
            "relationships": [],
            "depth": input_data.depth,
            "error": str(e)
        }


async def get_entity_timeline_tool(input_data: EntityTimelineInput) -> List[Dict[str, Any]]:
    """
    Get timeline of facts for an entity.

    Args:
        input_data: Timeline query parameters

    Returns:
        Timeline of facts
    """
    try:
        # Parse dates if provided
        start_date = None
        end_date = None

        if input_data.start_date:
            start_date = datetime.fromisoformat(input_data.start_date)
        if input_data.end_date:
            end_date = datetime.fromisoformat(input_data.end_date)

        # Get timeline from graph
        timeline = await graph_client.get_entity_timeline(
            entity_name=input_data.entity_name,
            start_date=start_date,
            end_date=end_date
        )

        return timeline

    except Exception as e:
        logger.error(f"Entity timeline query failed: {e}")
        return []


async def search_people_tool(input_data: PersonSearchInput) -> List[Dict[str, Any]]:
    """
    Search for people in the knowledge graph.

    Args:
        input_data: Person search parameters

    Returns:
        List of people matching the search criteria
    """
    try:
        results = await search_people(
            name_query=input_data.name_query,
            company=input_data.company,
            position=input_data.position,
            limit=input_data.limit
        )

        return results

    except Exception as e:
        logger.error(f"Person search failed: {e}")
        return []


async def search_companies_tool(input_data: CompanySearchInput) -> List[Dict[str, Any]]:
    """
    Search for companies in the knowledge graph.

    Args:
        input_data: Company search parameters

    Returns:
        List of companies matching the search criteria
    """
    try:
        results = await search_companies(
            name_query=input_data.name_query,
            industry=input_data.industry,
            location=input_data.location,
            limit=input_data.limit
        )

        return results

    except Exception as e:
        logger.error(f"Company search failed: {e}")
        return []


async def get_entity_relationships_tool(input_data: EntityRelationshipSearchInput) -> List[Dict[str, Any]]:
    """
    Get relationships for a node (person or company).
    This function is designed to work with the exact format used during ingestion.

    Args:
        input_data: Node relationship search parameters

    Returns:
        List of relationships for the node
    """
    try:
        logger.info(f"Searching for relationships for entity: {input_data.entity_name}, type: {input_data.entity_type}")

        # Use enhanced relationship search that handles Graphiti's actual format
        results = await get_enhanced_entity_relationships(
            entity_name=input_data.entity_name,
            entity_type=input_data.entity_type,
            relationship_types=input_data.relationship_types,
            limit=input_data.limit
        )

        logger.info(f"Found {len(results)} relationships for {input_data.entity_name}")

        # Log some details about the relationships found for debugging
        if results:
            logger.debug("Relationship details:")
            for i, rel in enumerate(results[:3], 1):  # Log first 3 relationships
                logger.debug(f"  {i}. {rel.get('source_entity')} {rel.get('relationship_type')} {rel.get('target_entity')} ({rel.get('extraction_method')})")
        else:
            logger.warning(f"No relationships found for {input_data.entity_name}. This may indicate:")
            logger.warning("  1. The entity doesn't exist in the knowledge graph")
            logger.warning("  2. The entity exists but has no relationships")
            logger.warning("  3. The relationships are in a format not handled by the extraction logic")

        return results

    except Exception as e:
        logger.error(f"Entity relationship search failed: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return []


async def get_enhanced_entity_relationships(
    entity_name: str,
    entity_type: Optional[str] = None,
    relationship_types: Optional[List[str]] = None,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Enhanced relationship search that handles Graphiti's actual fact format.
    This function is designed to work with the exact format used during ingestion.

    Args:
        entity_name: Name of the entity
        entity_type: Type of entity (person/company)
        relationship_types: Filter by relationship types
        limit: Maximum number of results

    Returns:
        List of relationships with enhanced extraction
    """
    try:
        # Import here to avoid circular imports
        from .graph_utils import graph_client

        # Initialize graph client
        await graph_client.initialize()

        # Build comprehensive search queries that match ingestion patterns
        search_queries = [
            # Direct relationship searches
            f"relationships involving {entity_name}",
            f"{entity_name} relationships",
            f"facts about {entity_name}",

            # Entity-specific searches
            f"{entity_name}",
            f"PERSON: {entity_name}" if entity_type == "person" else f"COMPANY: {entity_name}",

            # Employment and executive searches
            f"{entity_name} executive",
            f"{entity_name} employee",
            f"{entity_name} director",
            f"{entity_name} chairman",
            f"{entity_name} CEO",

            # Company-specific searches
            f"{entity_name} employs",
            f"{entity_name} executives",
            f"{entity_name} staff"
        ]

        # Add entity type specific queries
        if entity_type:
            if entity_type.lower() == "person":
                search_queries.extend([
                    f"person {entity_name}",
                    f"{entity_name} works at",
                    f"{entity_name} employed by",
                    f"{entity_name} position",
                    f"{entity_name} company"
                ])
            elif entity_type.lower() == "company":
                search_queries.extend([
                    f"company {entity_name}",
                    f"{entity_name} employees",
                    f"{entity_name} staff",
                    f"{entity_name} management"
                ])

        all_relationships = []
        seen_facts = set()

        # Search with multiple queries to get comprehensive results
        for query in search_queries:
            try:
                logger.debug(f"Searching with query: '{query}'")
                results = await graph_client.search(query)
                logger.debug(f"Query '{query}' returned {len(results)} results")

                for result in results:
                    # Handle both dict and object formats
                    if isinstance(result, dict):
                        fact = result.get("fact", "")
                        uuid = result.get("uuid", "")
                    else:
                        fact = getattr(result, "fact", "")
                        uuid = str(getattr(result, "uuid", ""))

                    # Skip empty facts or duplicates
                    if not fact or fact in seen_facts:
                        continue
                    seen_facts.add(fact)

                    # Only process facts that mention our entity
                    if entity_name.lower() not in fact.lower():
                        continue

                    logger.debug(f"Processing fact: {fact[:100]}...")

                    # Extract relationships using enhanced logic that matches ingestion format
                    relationships = _extract_relationships_from_graphiti_fact(
                        fact, entity_name, uuid
                    )

                    logger.debug(f"Extracted {len(relationships)} relationships from fact")

                    for rel in relationships:
                        # Filter by relationship types if specified
                        if relationship_types and rel.get("relationship_type") not in relationship_types:
                            logger.debug(f"Filtered out relationship type: {rel.get('relationship_type')}")
                            continue

                        all_relationships.append(rel)
                        logger.debug(f"Added relationship: {rel.get('source_entity')} {rel.get('relationship_type')} {rel.get('target_entity')}")

                        if len(all_relationships) >= limit * 2:  # Get more to allow for deduplication
                            break

                    if len(all_relationships) >= limit * 2:
                        break

            except Exception as e:
                logger.warning(f"Search query '{query}' failed: {e}")
                continue

        # Remove duplicates based on relationship content
        unique_relationships = []
        seen_relationships = set()

        for rel in all_relationships:
            # Create a more robust deduplication key
            source = rel.get('source_entity', '').strip().lower()
            target = rel.get('target_entity', '').strip().lower()
            rel_type = rel.get('relationship_type', '').strip()

            rel_key = f"{source}_{rel_type}_{target}"
            if rel_key not in seen_relationships and source and target and rel_type:
                seen_relationships.add(rel_key)
                unique_relationships.append(rel)

        logger.info(f"Found {len(unique_relationships)} unique relationships for {entity_name}")
        return unique_relationships[:limit]

    except Exception as e:
        logger.error(f"Enhanced relationship search failed: {e}")
        return []


def _extract_relationships_from_graphiti_fact(
    fact: str,
    entity_name: str,
    fact_uuid: str
) -> List[Dict[str, Any]]:
    """
    Extract relationships from Graphiti facts using the exact format from ingestion.
    This function is specifically designed to handle the format created by _create_relationship_episode_content
    and _create_entity_episode_content in graph_utils.py.

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

        # Clean up the fact text
        fact = fact.strip()
        if not fact:
            return relationships

        lines = fact.split('\n')
        fact_lower = fact.lower()
        entity_lower = entity_name.lower() if entity_name else ""

        # Skip if entity is not mentioned in the fact
        if entity_name and entity_lower not in fact_lower:
            return relationships

        logger.debug(f"Processing fact for entity '{entity_name}': {fact[:200]}...")

        # Pattern 1: Direct relationship format from ingestion
        # Format: "Relationship: source_entity relationship_type target_entity"
        for line in lines:
            line = line.strip()
            if line.startswith("Relationship:"):
                rel_line = line.replace("Relationship:", "").strip()
                logger.debug(f"Found relationship line: {rel_line}")

                # Parse the relationship line
                rel_info = _parse_ingestion_relationship_line(rel_line, entity_name)
                if rel_info:
                    rel_info.update({
                        "fact": fact,
                        "uuid": fact_uuid,
                        "extraction_method": "direct_relationship_ingestion"
                    })
                    relationships.append(rel_info)
                    logger.debug(f"Extracted direct relationship: {rel_info}")

        # Pattern 2: Structured entity facts from ingestion
        # Format: "PERSON: name" or "COMPANY: name" followed by attributes
        current_entity = None
        current_entity_type = None
        current_company = None
        current_position = None

        for line in lines:
            line = line.strip()
            if line.startswith("PERSON:"):
                current_entity = line.replace("PERSON:", "").strip()
                current_entity_type = "person"
                logger.debug(f"Found person entity: {current_entity}")
            elif line.startswith("COMPANY:"):
                current_entity = line.replace("COMPANY:", "").strip()
                current_entity_type = "company"
                logger.debug(f"Found company entity: {current_entity}")
            elif current_entity and ":" in line:
                key, value = line.split(":", 1)
                key = key.strip()
                value = value.strip()

                if key == "Current company":
                    current_company = value
                elif key == "Current position":
                    current_position = value
                elif key == "Key executives" and current_entity_type == "company":
                    # Extract executive relationships from company facts
                    executives = [exec.strip() for exec in value.split(",")]
                    for exec_name in executives:
                        if exec_name and len(exec_name) > 1:
                            # Create relationship for each executive
                            if entity_lower in exec_name.lower():
                                relationships.append({
                                    "source_entity": exec_name,
                                    "target_entity": current_entity,
                                    "relationship_type": "Executive_OF",
                                    "direction": "outgoing",
                                    "fact": fact,
                                    "uuid": fact_uuid,
                                    "extraction_method": "structured_executive_list"
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
                                    "extraction_method": "structured_executive_list"
                                })

        # Create employment relationship if we have person with company info
        if current_entity and current_entity_type == "person" and current_company:
            if entity_lower in current_entity.lower():
                # Determine relationship type based on position
                rel_type = "Employee_OF"
                if current_position:
                    exec_keywords = ["ceo", "cto", "cfo", "director", "executive", "chairman", "president", "chief"]
                    if any(keyword in current_position.lower() for keyword in exec_keywords):
                        rel_type = "Executive_OF"

                relationships.append({
                    "source_entity": current_entity,
                    "target_entity": current_company,
                    "relationship_type": rel_type,
                    "direction": "outgoing",
                    "details": current_position if current_position else None,
                    "fact": fact,
                    "uuid": fact_uuid,
                    "extraction_method": "structured_employment"
                })
            elif entity_lower in current_company.lower():
                relationships.append({
                    "source_entity": current_company,
                    "target_entity": current_entity,
                    "relationship_type": "Employs",
                    "direction": "incoming",
                    "details": current_position if current_position else None,
                    "fact": fact,
                    "uuid": fact_uuid,
                    "extraction_method": "structured_employment"
                })

        # Pattern 3: Natural language patterns that Graphiti might generate
        # These are patterns that Graphiti's LLM might create when processing episodes
        natural_patterns = [
            # Employment patterns
            (r"(\w+(?:\s+\w+)*)\s+(?:is|was|serves as|works as)\s+(?:the\s+)?([^.]+?)\s+(?:at|of|for)\s+([^.]+)", "employment"),
            (r"(\w+(?:\s+\w+)*)\s+(?:CEO|CTO|CFO|Director|Executive|Chairman|President)\s+(?:of|at)\s+([^.]+)", "executive"),
            (r"([^.]+?)\s+employs?\s+(\w+(?:\s+\w+)*)", "employment_reverse"),
            # Ownership patterns
            (r"(\w+(?:\s+\w+)*)\s+owns?\s+([^.]+)", "ownership"),
            (r"([^.]+?)\s+(?:is\s+)?owned\s+by\s+(\w+(?:\s+\w+)*)", "ownership_reverse"),
            # Corporate structure patterns
            (r"([^.]+?)\s+(?:is\s+a\s+)?subsidiary\s+of\s+([^.]+)", "subsidiary"),
            (r"([^.]+?)\s+(?:is\s+a\s+)?shareholder\s+(?:in|of)\s+([^.]+)", "shareholder")
        ]

        for pattern, rel_category in natural_patterns:
            matches = re.finditer(pattern, fact, re.IGNORECASE)
            for match in matches:
                groups = match.groups()
                if len(groups) >= 2:
                    entity1 = groups[0].strip()
                    entity2 = groups[1].strip() if len(groups) == 2 else groups[2].strip()
                    position = groups[1].strip() if len(groups) == 3 and rel_category == "employment" else None

                    # Clean up entity names
                    entity1 = re.sub(r'^(the\s+)', '', entity1, flags=re.IGNORECASE).strip()
                    entity2 = re.sub(r'^(the\s+)', '', entity2, flags=re.IGNORECASE).strip()

                    # Skip if entities are too short or generic
                    if len(entity1) < 2 or len(entity2) < 2:
                        continue

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
                            "extraction_method": f"natural_language_{rel_category}"
                        }

                        if position:
                            rel_data["details"] = position

                        relationships.append(rel_data)
                        logger.debug(f"Extracted natural language relationship: {rel_data}")

        logger.debug(f"Total relationships extracted: {len(relationships)}")
        return relationships

    except Exception as e:
        logger.error(f"Failed to extract relationships from Graphiti fact: {e}")
        return relationships


def _parse_ingestion_relationship_line(rel_line: str, entity_name: str) -> Optional[Dict[str, Any]]:
    """
    Parse a relationship line in the exact format used during ingestion.
    Format: "source_entity relationship_type target_entity"

    Args:
        rel_line: The relationship line text
        entity_name: The entity we're searching for

    Returns:
        Parsed relationship info or None
    """
    try:
        import re

        # Clean up the relationship line
        rel_line = rel_line.strip()
        if not rel_line:
            return None

        entity_lower = entity_name.lower() if entity_name else ""

        # Split the line into parts
        # Handle relationship types with underscores (e.g., "Executive_OF", "Employee_OF")
        parts = rel_line.split()
        if len(parts) < 3:
            return None

        # Find the relationship type (usually contains underscores or is a known type)
        rel_type_idx = -1
        for i, part in enumerate(parts[1:-1], 1):  # Skip first and last parts
            if ('_' in part or
                part.upper() in ['OF', 'BY', 'WITH', 'TO', 'FOR', 'AT', 'IN'] or
                any(rel_word in part.upper() for rel_word in ['EXECUTIVE', 'EMPLOYEE', 'DIRECTOR', 'CHAIRMAN', 'CEO', 'OWNS', 'SUBSIDIARY'])):
                rel_type_idx = i
                break

        if rel_type_idx > 0:
            source_entity = " ".join(parts[:rel_type_idx])
            relationship_type = parts[rel_type_idx]
            target_entity = " ".join(parts[rel_type_idx + 1:])
        else:
            # Fallback: assume middle part is relationship type
            if len(parts) == 3:
                source_entity = parts[0]
                relationship_type = parts[1]
                target_entity = parts[2]
            else:
                # For longer strings, try to find the relationship type
                source_entity = parts[0]
                relationship_type = parts[1]
                target_entity = " ".join(parts[2:])

        # Clean up entity names
        source_entity = source_entity.strip()
        target_entity = target_entity.strip()
        relationship_type = relationship_type.strip()

        # Determine direction relative to the queried entity
        if entity_name:
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
        else:
            # If no specific entity, return the relationship anyway
            return {
                "source_entity": source_entity,
                "target_entity": target_entity,
                "relationship_type": relationship_type,
                "direction": "unknown"
            }

        return None

    except Exception as e:
        logger.error(f"Failed to parse ingestion relationship line '{rel_line}': {e}")
        return None


def _extract_relationships_from_fact_enhanced(
    fact: str,
    entity_name: str,
    fact_uuid: str
) -> List[Dict[str, Any]]:
    """
    Enhanced relationship extraction that handles Graphiti's actual fact formats.

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
                rel_info = _parse_relationship_line(rel_line, entity_name)
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


def _parse_relationship_line(rel_line: str, entity_name: str) -> Optional[Dict[str, Any]]:
    """
    Parse a relationship line in format "Source relationship_type Target".
    Enhanced to handle the actual format used by Graphiti during ingestion.

    Args:
        rel_line: The relationship line text
        entity_name: The entity we're searching for

    Returns:
        Parsed relationship info or None
    """
    try:
        import re

        # Clean up the relationship line
        rel_line = rel_line.strip()
        if not rel_line:
            return None

        entity_lower = entity_name.lower() if entity_name else ""

        # Pattern 1: Standard format "Source relationship_type Target"
        # Handle relationship types with underscores (e.g., "Executive_OF", "Employee_OF")
        rel_pattern = r'^(.+?)\s+([A-Za-z_]+(?:_[A-Za-z]+)*)\s+(.+)$'
        match = re.match(rel_pattern, rel_line)

        if match:
            source_entity = match.group(1).strip()
            relationship_type = match.group(2).strip()
            target_entity = match.group(3).strip()

            # Determine direction relative to the queried entity
            if entity_name:
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
            else:
                # If no specific entity, return the relationship anyway
                return {
                    "source_entity": source_entity,
                    "target_entity": target_entity,
                    "relationship_type": relationship_type,
                    "direction": "unknown"
                }

        # Pattern 2: Fallback to simple space-based splitting
        parts = rel_line.split()
        if len(parts) >= 3:
            # Look for relationship type indicators (words with underscores or common relationship words)
            rel_type_idx = -1
            for i, part in enumerate(parts):
                if ('_' in part or
                    part.lower() in ['of', 'by', 'with', 'to', 'for', 'at', 'in'] or
                    any(rel_word in part.lower() for rel_word in ['executive', 'employee', 'director', 'chairman', 'ceo', 'owns', 'subsidiary'])):
                    rel_type_idx = i
                    break

            if rel_type_idx > 0 and rel_type_idx < len(parts) - 1:
                source_entity = " ".join(parts[:rel_type_idx])
                relationship_type = parts[rel_type_idx]
                target_entity = " ".join(parts[rel_type_idx + 1:])
            else:
                # Default fallback
                source_entity = parts[0]
                relationship_type = parts[1]
                target_entity = " ".join(parts[2:])

            # Determine direction
            if entity_name:
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
            else:
                return {
                    "source_entity": source_entity,
                    "target_entity": target_entity,
                    "relationship_type": relationship_type,
                    "direction": "unknown"
                }

        return None

    except Exception as e:
        logger.error(f"Failed to parse relationship line '{rel_line}': {e}")
        return None


# Combined search function for agent use
async def perform_comprehensive_search(
    query: str,
    use_vector: bool = True,
    use_graph: bool = True,
    limit: int = 10
) -> Dict[str, Any]:
    """
    Perform a comprehensive search using multiple methods.
    
    Args:
        query: Search query
        use_vector: Whether to use vector search
        use_graph: Whether to use graph search
        limit: Maximum results per search type (only applies to vector search)
    
    Returns:
        Combined search results
    """
    results = {
        "query": query,
        "vector_results": [],
        "graph_results": [],
        "total_results": 0
    }
    
    tasks = []
    
    if use_vector:
        tasks.append(vector_search_tool(VectorSearchInput(query=query, limit=limit)))
    
    if use_graph:
        tasks.append(graph_search_tool(GraphSearchInput(query=query)))
    
    if tasks:
        search_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        if use_vector and not isinstance(search_results[0], Exception):
            results["vector_results"] = search_results[0]
        
        if use_graph:
            graph_idx = 1 if use_vector else 0
            if not isinstance(search_results[graph_idx], Exception):
                results["graph_results"] = search_results[graph_idx]
    
    results["total_results"] = len(results["vector_results"]) + len(results["graph_results"])

    return results


# Enhanced Hybrid Search Helper Functions

async def _expand_query(query: str) -> str:
    """
    Expand query with synonyms and related terms for better coverage.

    Args:
        query: Original search query

    Returns:
        Expanded query string
    """
    try:
        # Simple query expansion - can be enhanced with more sophisticated methods
        expanded_terms = []

        # Add original query
        expanded_terms.append(query)

        # Add common business synonyms and variations
        business_synonyms = {
            "company": ["corporation", "business", "firm", "organization", "enterprise"],
            "ceo": ["chief executive officer", "president", "executive director"],
            "cfo": ["chief financial officer", "finance director"],
            "director": ["executive", "manager", "officer", "head"],
            "investment": ["funding", "capital", "financing", "stake"],
            "acquisition": ["purchase", "buyout", "merger", "takeover"],
            "partnership": ["collaboration", "alliance", "joint venture"],
            "revenue": ["income", "earnings", "sales", "turnover"],
            "profit": ["earnings", "income", "returns", "gains"]
        }

        # Expand query terms
        query_lower = query.lower()
        for term, synonyms in business_synonyms.items():
            if term in query_lower:
                expanded_terms.extend(synonyms[:2])  # Add top 2 synonyms

        # Join with OR for broader search
        expanded_query = " OR ".join(set(expanded_terms))

        logger.debug(f"Expanded query from '{query}' to '{expanded_query}'")
        return expanded_query

    except Exception as e:
        logger.warning(f"Query expansion failed: {e}")
        return query


async def _apply_semantic_reranking(results: List[Dict[str, Any]], original_query: str) -> List[Dict[str, Any]]:
    """
    Apply semantic reranking to improve result relevance.

    Args:
        results: Search results to rerank
        original_query: Original search query

    Returns:
        Reranked results
    """
    try:
        if len(results) <= 1:
            return results

        # Generate embedding for original query
        query_embedding = await generate_embedding(original_query)

        # Calculate semantic similarity for each result
        for result in results:
            try:
                # Generate embedding for result content
                content_embedding = await generate_embedding(result["content"][:500])  # Limit content length

                # Calculate cosine similarity
                similarity = _calculate_cosine_similarity(query_embedding, content_embedding)

                # Combine with existing score (weighted average)
                original_score = result.get("enhanced_score", result.get("combined_score", 0))
                semantic_boost = similarity * 0.3  # 30% weight for semantic similarity

                result["enhanced_score"] = original_score * 0.7 + semantic_boost
                result["semantic_similarity"] = similarity

                # Add relevance factors
                if "relevance_factors" not in result:
                    result["relevance_factors"] = {}
                result["relevance_factors"]["semantic_reranking"] = similarity

            except Exception as e:
                logger.warning(f"Semantic reranking failed for result: {e}")
                continue

        # Sort by enhanced score
        results.sort(key=lambda x: x.get("enhanced_score", 0), reverse=True)

        logger.debug(f"Applied semantic reranking to {len(results)} results")
        return results

    except Exception as e:
        logger.warning(f"Semantic reranking failed: {e}")
        return results


async def _deduplicate_results(results: List[Dict[str, Any]], similarity_threshold: float = 0.85) -> List[Dict[str, Any]]:
    """
    Remove duplicate or highly similar results.

    Args:
        results: Search results to deduplicate
        similarity_threshold: Threshold for considering results as duplicates

    Returns:
        Deduplicated results
    """
    try:
        if len(results) <= 1:
            return results

        deduplicated = []
        seen_content = []

        for result in results:
            content = result["content"]
            is_duplicate = False

            # Check against previously seen content
            for seen in seen_content:
                # Simple similarity check based on content overlap
                similarity = _calculate_text_similarity(content, seen)
                if similarity > similarity_threshold:
                    is_duplicate = True
                    break

            if not is_duplicate:
                deduplicated.append(result)
                seen_content.append(content)

                # Add relevance factor
                if "relevance_factors" not in result:
                    result["relevance_factors"] = {}
                result["relevance_factors"]["deduplication"] = "unique"

        logger.debug(f"Deduplicated {len(results)} results to {len(deduplicated)} unique results")
        return deduplicated

    except Exception as e:
        logger.warning(f"Deduplication failed: {e}")
        return results


def _calculate_cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Calculate cosine similarity between two vectors."""
    try:
        import math

        # Calculate dot product
        dot_product = sum(a * b for a, b in zip(vec1, vec2))

        # Calculate magnitudes
        magnitude1 = math.sqrt(sum(a * a for a in vec1))
        magnitude2 = math.sqrt(sum(a * a for a in vec2))

        # Avoid division by zero
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0

        return dot_product / (magnitude1 * magnitude2)

    except Exception:
        return 0.0


def _calculate_text_similarity(text1: str, text2: str) -> float:
    """Calculate text similarity using simple overlap metrics."""
    try:
        # Simple word-based similarity
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        return len(intersection) / len(union) if union else 0.0

    except Exception:
        return 0.0