#!/usr/bin/env python3
"""
Test script for enhanced hybrid search and ingestion alignment validation.
"""

import asyncio
import logging
from typing import Dict, Any

from agent.tools import (
    enhanced_hybrid_search_tool,
    EnhancedHybridSearchInput,
    search_people_tool,
    search_companies_tool,
    PersonSearchInput,
    CompanySearchInput
)
from agent.graph_utils import initialize_graph, close_graph
from agent.db_utils import initialize_db, close_db

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_enhanced_hybrid_search():
    """Test the enhanced hybrid search functionality."""
    logger.info("Testing enhanced hybrid search...")
    
    try:
        # Test query
        test_query = "CEO executive director company leadership"
        
        # Test with different configurations
        test_configs = [
            {
                "name": "Basic Enhanced Search",
                "config": EnhancedHybridSearchInput(
                    query=test_query,
                    limit=5,
                    enable_query_expansion=False,
                    enable_semantic_reranking=False,
                    enable_deduplication=False
                )
            },
            {
                "name": "Full Enhanced Search",
                "config": EnhancedHybridSearchInput(
                    query=test_query,
                    limit=5,
                    enable_query_expansion=True,
                    enable_semantic_reranking=True,
                    enable_deduplication=True,
                    boost_recent_documents=True
                )
            }
        ]
        
        for test_config in test_configs:
            logger.info(f"\n--- {test_config['name']} ---")
            
            results = await enhanced_hybrid_search_tool(test_config['config'])
            
            logger.info(f"Found {len(results)} results")
            
            for i, result in enumerate(results[:3], 1):
                logger.info(f"Result {i}:")
                logger.info(f"  Score: {result.score:.3f}")
                logger.info(f"  Title: {result.document_title}")
                logger.info(f"  Content: {result.content[:100]}...")
                
                # Check for enhanced metadata
                if hasattr(result, 'vector_similarity'):
                    logger.info(f"  Vector Similarity: {result.vector_similarity:.3f}")
                if hasattr(result, 'text_similarity'):
                    logger.info(f"  Text Similarity: {result.text_similarity:.3f}")
                if hasattr(result, 'relevance_factors'):
                    logger.info(f"  Relevance Factors: {result.relevance_factors}")
        
        logger.info("✅ Enhanced hybrid search test completed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Enhanced hybrid search test failed: {e}")
        return False


async def test_entity_search_alignment():
    """Test entity search alignment with ingested data."""
    logger.info("Testing entity search alignment...")
    
    try:
        # Test person search
        logger.info("Testing person search...")
        person_input = PersonSearchInput(name_query="", limit=5)
        people_results = await search_people_tool(person_input)
        
        logger.info(f"Found {len(people_results)} people")
        for person in people_results[:3]:
            logger.info(f"  - {person}")
        
        # Test company search
        logger.info("Testing company search...")
        company_input = CompanySearchInput(name_query="", limit=5)
        company_results = await search_companies_tool(company_input)
        
        logger.info(f"Found {len(company_results)} companies")
        for company in company_results[:3]:
            logger.info(f"  - {company}")
        
        # Calculate alignment score
        alignment_score = 0.0
        if len(people_results) > 0:
            alignment_score += 0.5
        if len(company_results) > 0:
            alignment_score += 0.5
        
        logger.info(f"Entity search alignment score: {alignment_score:.2f}")
        
        if alignment_score >= 0.8:
            logger.info("✅ Entity search alignment test passed")
            return True
        else:
            logger.warning("⚠️  Entity search alignment score is low")
            return False
        
    except Exception as e:
        logger.error(f"❌ Entity search alignment test failed: {e}")
        return False


async def test_query_expansion():
    """Test query expansion functionality."""
    logger.info("Testing query expansion...")
    
    try:
        from agent.tools import _expand_query
        
        test_queries = [
            "CEO company",
            "investment funding",
            "director executive",
            "acquisition merger"
        ]
        
        for query in test_queries:
            expanded = await _expand_query(query)
            logger.info(f"Original: '{query}'")
            logger.info(f"Expanded: '{expanded}'")
            logger.info("")
        
        logger.info("✅ Query expansion test completed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Query expansion test failed: {e}")
        return False


async def run_comprehensive_tests():
    """Run all enhancement tests."""
    logger.info("🚀 Starting comprehensive enhancement tests")
    
    try:
        # Initialize connections
        await initialize_db()
        await initialize_graph()
        
        # Run tests
        test_results = []
        
        # Test 1: Enhanced hybrid search
        result1 = await test_enhanced_hybrid_search()
        test_results.append(("Enhanced Hybrid Search", result1))
        
        # Test 2: Entity search alignment
        result2 = await test_entity_search_alignment()
        test_results.append(("Entity Search Alignment", result2))
        
        # Test 3: Query expansion
        result3 = await test_query_expansion()
        test_results.append(("Query Expansion", result3))
        
        # Print summary
        logger.info("\n" + "="*50)
        logger.info("TEST SUMMARY")
        logger.info("="*50)
        
        passed = 0
        for test_name, result in test_results:
            status = "✅ PASSED" if result else "❌ FAILED"
            logger.info(f"{test_name}: {status}")
            if result:
                passed += 1
        
        logger.info(f"\nOverall: {passed}/{len(test_results)} tests passed")
        
        if passed == len(test_results):
            logger.info("🎉 All enhancement tests passed!")
        else:
            logger.warning("⚠️  Some tests failed - review implementation")
        
        return passed == len(test_results)
        
    except Exception as e:
        logger.error(f"❌ Comprehensive test failed: {e}")
        return False
    
    finally:
        # Clean up connections
        await close_db()
        await close_graph()


async def main():
    """Main test function."""
    success = await run_comprehensive_tests()
    return 0 if success else 1


if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main()))
