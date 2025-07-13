#!/usr/bin/env python3
"""
Test script for relationship search functionality between entities.
"""

import asyncio
import logging
from typing import Dict, Any

from agent.graph_utils import initialize_graph, close_graph
from agent.db_utils import initialize_db, close_db

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_relationship_query_parsing():
    """Test parsing of relationship queries."""
    logger.info("Testing relationship query parsing...")
    
    from agent.agent import _is_relationship_query, _extract_entities_from_relationship_query
    
    test_queries = [
        "what is relation between Michael T H Lee and HKJC",
        "relationship between John Smith and TechCorp",
        "how is Alice connected to DataCorp",
        "connection between CEO and company",
        "Michael T H Lee works with Hong Kong Jockey Club"
    ]
    
    for query in test_queries:
        is_rel_query = _is_relationship_query(query)
        entities = _extract_entities_from_relationship_query(query)
        
        logger.info(f"Query: '{query}'")
        logger.info(f"  Is relationship query: {is_rel_query}")
        logger.info(f"  Extracted entities: {entities}")
        logger.info("")
    
    return True


async def test_entity_relationship_search():
    """Test searching for relationships between specific entities."""
    logger.info("Testing entity relationship search...")
    
    try:
        from agent.agent import _search_entity_relationships
        
        # Test with sample entities
        test_pairs = [
            ("Michael T H Lee", "HKJC"),
            ("Michael T H Lee", "Hong Kong Jockey Club"),
            ("C Y Tam", "Hong Kong Jockey Club"),
            ("John Chen", "TechCorp")  # This might not exist but tests the function
        ]
        
        for entity1, entity2 in test_pairs:
            logger.info(f"Searching for relationships between '{entity1}' and '{entity2}'...")
            
            results = await _search_entity_relationships(entity1, entity2)
            
            logger.info(f"Found {len(results)} potential relationships")
            
            for i, result in enumerate(results[:3], 1):  # Show top 3
                logger.info(f"  Result {i}:")
                logger.info(f"    Fact: {result.get('fact', 'N/A')}")
                logger.info(f"    Relevance: {result.get('relevance_score', 0)}")
                logger.info(f"    Query: {result.get('search_query', 'N/A')}")
            
            logger.info("")
        
        return True
        
    except Exception as e:
        logger.error(f"Entity relationship search test failed: {e}")
        return False


async def test_comprehensive_relationship_search():
    """Test comprehensive relationship search."""
    logger.info("Testing comprehensive relationship search...")
    
    try:
        from agent.agent import _comprehensive_relationship_search
        
        # Test with known entities
        entity1 = "Michael T H Lee"
        entity2 = "Hong Kong Jockey Club"
        
        logger.info(f"Performing comprehensive search between '{entity1}' and '{entity2}'...")
        
        result = await _comprehensive_relationship_search(entity1, entity2, search_depth=2)
        
        logger.info("Comprehensive search results:")
        logger.info(f"  Entity 1: {result.get('entity1')}")
        logger.info(f"  Entity 2: {result.get('entity2')}")
        logger.info(f"  Direct relationships found: {len(result.get('direct_relationships', []))}")
        logger.info(f"  Connection strength: {result.get('connection_strength', 0):.2f}")
        logger.info(f"  Summary: {result.get('summary', 'N/A')}")
        
        # Show some direct relationships if found
        direct_rels = result.get('direct_relationships', [])
        if direct_rels:
            logger.info("  Top direct relationships:")
            for i, rel in enumerate(direct_rels[:3], 1):
                logger.info(f"    {i}. {rel.get('fact', 'N/A')} (relevance: {rel.get('relevance_score', 0)})")
        
        # Show entity info
        entity1_info = result.get('entity1_info', {})
        if entity1_info.get('relationships'):
            logger.info(f"  {entity1} has {entity1_info.get('total_relationships', 0)} total relationships")
        
        entity2_info = result.get('entity2_info', {})
        if entity2_info.get('relationships'):
            logger.info(f"  {entity2} has {entity2_info.get('total_relationships', 0)} total relationships")
        
        return True
        
    except Exception as e:
        logger.error(f"Comprehensive relationship search test failed: {e}")
        return False


async def test_graph_search_with_relationship_query():
    """Test the enhanced graph search with relationship queries."""
    logger.info("Testing graph search with relationship queries...")
    
    try:
        from agent.tools import graph_search_tool, GraphSearchInput
        
        # Test relationship queries
        test_queries = [
            "Michael T H Lee HKJC",
            "relationship Michael T H Lee Hong Kong Jockey Club",
            "C Y Tam Hong Kong Jockey Club director",
            "facts about Michael T H Lee"
        ]
        
        for query in test_queries:
            logger.info(f"Testing graph search with query: '{query}'")
            
            input_data = GraphSearchInput(query=query)
            results = await graph_search_tool(input_data)
            
            logger.info(f"Found {len(results)} graph results")
            
            for i, result in enumerate(results[:2], 1):  # Show top 2
                logger.info(f"  Result {i}:")
                logger.info(f"    Fact: {result.fact}")
                logger.info(f"    UUID: {result.uuid}")
            
            logger.info("")
        
        return True
        
    except Exception as e:
        logger.error(f"Graph search test failed: {e}")
        return False


async def run_all_tests():
    """Run all relationship search tests."""
    logger.info("🚀 Starting relationship search tests")
    
    try:
        # Initialize connections
        await initialize_db()
        await initialize_graph()
        
        # Run tests
        test_results = []
        
        # Test 1: Query parsing
        result1 = await test_relationship_query_parsing()
        test_results.append(("Query Parsing", result1))
        
        # Test 2: Entity relationship search
        result2 = await test_entity_relationship_search()
        test_results.append(("Entity Relationship Search", result2))
        
        # Test 3: Comprehensive relationship search
        result3 = await test_comprehensive_relationship_search()
        test_results.append(("Comprehensive Relationship Search", result3))
        
        # Test 4: Graph search with relationship queries
        result4 = await test_graph_search_with_relationship_query()
        test_results.append(("Graph Search with Relationship Queries", result4))
        
        # Print summary
        logger.info("\n" + "="*60)
        logger.info("RELATIONSHIP SEARCH TEST SUMMARY")
        logger.info("="*60)
        
        passed = 0
        for test_name, result in test_results:
            status = "✅ PASSED" if result else "❌ FAILED"
            logger.info(f"{test_name}: {status}")
            if result:
                passed += 1
        
        logger.info(f"\nOverall: {passed}/{len(test_results)} tests passed")
        
        if passed == len(test_results):
            logger.info("🎉 All relationship search tests passed!")
        else:
            logger.warning("⚠️  Some tests failed - review implementation")
        
        return passed == len(test_results)
        
    except Exception as e:
        logger.error(f"❌ Test suite failed: {e}")
        return False
    
    finally:
        # Clean up connections
        await close_db()
        await close_graph()


async def main():
    """Main test function."""
    success = await run_all_tests()
    return 0 if success else 1


if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main()))
