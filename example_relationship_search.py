#!/usr/bin/env python3
"""
Example script demonstrating enhanced relationship search capabilities.
This script shows how to use the agent to find relationships between entities.
"""

import asyncio
import logging
from typing import Dict, Any

from agent.agent import rag_agent, AgentDependencies
from agent.graph_utils import initialize_graph, close_graph
from agent.db_utils import initialize_db, close_db

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def demonstrate_relationship_search():
    """Demonstrate the enhanced relationship search functionality."""
    
    logger.info("🔍 Demonstrating Enhanced Relationship Search")
    logger.info("=" * 60)
    
    # Initialize dependencies
    deps = AgentDependencies(session_id="demo_session")
    
    # Example 1: Direct relationship query
    logger.info("\n📋 Example 1: Direct Relationship Query")
    logger.info("-" * 40)
    
    query1 = "what is relation between Michael T H Lee and HKJC"
    logger.info(f"Query: {query1}")
    
    try:
        # This will automatically use the enhanced relationship search
        result1 = await rag_agent.run(query1, deps=deps)
        logger.info(f"Result: {result1.data}")
    except Exception as e:
        logger.error(f"Query 1 failed: {e}")
    
    # Example 2: Using the specialized relationship tool
    logger.info("\n📋 Example 2: Specialized Relationship Tool")
    logger.info("-" * 40)
    
    try:
        from agent.agent import find_relationship_between_entities
        
        # Create a mock context
        class MockContext:
            def __init__(self, deps):
                self.deps = deps
        
        ctx = MockContext(deps)
        
        result2 = await find_relationship_between_entities(
            ctx=ctx,
            entity1="Michael T H Lee",
            entity2="Hong Kong Jockey Club",
            search_depth=2
        )
        
        logger.info("Specialized relationship search results:")
        logger.info(f"  Entity 1: {result2.get('entity1')}")
        logger.info(f"  Entity 2: {result2.get('entity2')}")
        logger.info(f"  Direct relationships: {len(result2.get('direct_relationships', []))}")
        logger.info(f"  Connection strength: {result2.get('connection_strength', 0):.2f}")
        logger.info(f"  Summary: {result2.get('summary', 'N/A')}")
        
        # Show relationship details
        direct_rels = result2.get('direct_relationships', [])
        if direct_rels:
            logger.info("  Relationship details:")
            for i, rel in enumerate(direct_rels[:3], 1):
                logger.info(f"    {i}. {rel.get('fact', 'N/A')}")
                logger.info(f"       Relevance: {rel.get('relevance_score', 0):.2f}")
        
    except Exception as e:
        logger.error(f"Specialized tool failed: {e}")
    
    # Example 3: Enhanced graph search
    logger.info("\n📋 Example 3: Enhanced Graph Search")
    logger.info("-" * 40)
    
    try:
        from agent.tools import graph_search_tool, GraphSearchInput
        
        query3 = "C Y Tam Hong Kong Jockey Club"
        logger.info(f"Query: {query3}")
        
        input_data = GraphSearchInput(query=query3)
        result3 = await graph_search_tool(input_data)
        
        logger.info(f"Found {len(result3)} graph results")
        
        for i, result in enumerate(result3[:3], 1):
            logger.info(f"  Result {i}:")
            logger.info(f"    Fact: {result.fact}")
            logger.info(f"    Search variation: {getattr(result, 'search_variation', 'direct')}")
            logger.info(f"    UUID: {result.uuid}")
        
    except Exception as e:
        logger.error(f"Enhanced graph search failed: {e}")
    
    # Example 4: Multiple relationship queries
    logger.info("\n📋 Example 4: Multiple Relationship Queries")
    logger.info("-" * 40)
    
    test_queries = [
        "relationship between C Y Tam and HKJC",
        "how is Michael T H Lee connected to Hong Kong Jockey Club",
        "connection between directors and Hong Kong Jockey Club",
        "facts about Michael T H Lee and HKJC"
    ]
    
    for i, query in enumerate(test_queries, 1):
        logger.info(f"\nQuery {i}: {query}")
        
        try:
            result = await rag_agent.run(query, deps=deps)
            # Extract key information from the result
            if hasattr(result, 'data') and result.data:
                logger.info(f"  Response: {str(result.data)[:200]}...")
            else:
                logger.info("  No specific response data")
        except Exception as e:
            logger.error(f"  Query failed: {e}")


async def demonstrate_query_parsing():
    """Demonstrate query parsing capabilities."""
    
    logger.info("\n🔧 Query Parsing Demonstration")
    logger.info("=" * 40)
    
    from agent.agent import _is_relationship_query, _extract_entities_from_relationship_query, _clean_entity_name
    
    test_queries = [
        "what is relation between Michael T H Lee and HKJC",
        "relationship between John Smith and TechCorp",
        "how is Alice connected to DataCorp",
        "connection between CEO and company",
        "Michael T H Lee works with Hong Kong Jockey Club",
        "facts about Michael T H Lee",  # Not a relationship query
        "search for companies"  # Not a relationship query
    ]
    
    for query in test_queries:
        is_rel_query = _is_relationship_query(query)
        entities = _extract_entities_from_relationship_query(query)
        
        logger.info(f"Query: '{query}'")
        logger.info(f"  Is relationship query: {is_rel_query}")
        
        if entities:
            cleaned_entities = [_clean_entity_name(e) for e in entities]
            logger.info(f"  Extracted entities: {entities}")
            logger.info(f"  Cleaned entities: {cleaned_entities}")
        else:
            logger.info(f"  No entities extracted")
        
        logger.info("")


async def main():
    """Main demonstration function."""
    
    logger.info("🚀 Starting Enhanced Relationship Search Demonstration")
    
    try:
        # Initialize connections
        await initialize_db()
        await initialize_graph()
        
        # Run demonstrations
        await demonstrate_query_parsing()
        await demonstrate_relationship_search()
        
        logger.info("\n✅ Demonstration completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Demonstration failed: {e}")
        return 1
    
    finally:
        # Clean up connections
        await close_db()
        await close_graph()
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main()))
