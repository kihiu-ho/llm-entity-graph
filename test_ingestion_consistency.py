#!/usr/bin/env python3
"""
Test script to verify that relationship extraction is consistent with ingestion format.
"""

import asyncio
import logging
import sys
import os
from typing import List, Dict, Any

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_ingestion_format_extraction():
    """Test extraction with the exact format used during ingestion."""
    
    logger.info("Testing relationship extraction with ingestion format...")
    
    try:
        # Import the extraction function
        from agent.tools import _extract_relationships_from_graphiti_fact, _parse_ingestion_relationship_line
        
        # Test the exact format created by _create_relationship_episode_content
        ingestion_format_facts = [
            # Direct relationship format from ingestion
            """Relationship: John Chen Executive_OF TechCorp Holdings
Description: John Chen serves as Executive Director
Strength: 1.0
Active: True""",
            
            # Entity format from ingestion
            """PERSON: Sarah Chen
Entity Type: Person
Current company: TechCorp Inc
Current position: CEO
Full name: Sarah Chen""",
            
            # Company format from ingestion
            """COMPANY: DataFlow Systems
Entity Type: Company
Industry: Data Analytics
Key executives: Michael Wong, Lisa Tan
Headquarters: Singapore""",
            
            # Multiple relationship format
            """Relationship: TechCorp Holdings Shareholder_OF DataFlow Systems
Description: TechCorp Holdings owns 25% stake in DataFlow Systems
Strength: 0.8
Active: True""",
            
            # Employment relationship
            """Relationship: Sarah Chen Employee_OF TechCorp Inc
Description: Sarah Chen works as CEO at TechCorp Inc
Started: 2022-03-01T00:00:00
Active: True"""
        ]
        
        test_entities = ["John Chen", "Sarah Chen", "TechCorp Holdings", "TechCorp Inc", "DataFlow Systems", "Michael Wong"]
        
        for i, fact in enumerate(ingestion_format_facts, 1):
            logger.info(f"\n--- Testing Ingestion Fact {i} ---")
            logger.info(f"Fact:\n{fact}")
            
            for entity in test_entities:
                relationships = _extract_relationships_from_graphiti_fact(fact, entity, f"test-uuid-{i}")
                if relationships:
                    logger.info(f"\n  Entity '{entity}' relationships:")
                    for rel in relationships:
                        logger.info(f"    ✅ {rel.get('source_entity')} {rel.get('relationship_type')} {rel.get('target_entity')}")
                        logger.info(f"       Direction: {rel.get('direction')}, Method: {rel.get('extraction_method')}")
                        if 'details' in rel:
                            logger.info(f"       Details: {rel['details']}")
        
        # Test relationship line parsing
        logger.info(f"\n--- Testing Relationship Line Parsing ---")
        relationship_lines = [
            "John Chen Executive_OF TechCorp Holdings",
            "Sarah Chen Employee_OF TechCorp Inc",
            "TechCorp Holdings Shareholder_OF DataFlow Systems",
            "Michael Wong Director_OF DataFlow Systems"
        ]
        
        for line in relationship_lines:
            logger.info(f"\nTesting line: '{line}'")
            for entity in ["John Chen", "TechCorp Holdings", "Sarah Chen"]:
                result = _parse_ingestion_relationship_line(line, entity)
                if result:
                    logger.info(f"  Entity '{entity}': {result}")
        
        logger.info(f"\n✅ Ingestion format extraction testing completed!")
        
    except Exception as e:
        logger.error(f"Error testing ingestion format extraction: {e}")
        import traceback
        traceback.print_exc()


async def test_agent_tools_with_real_data():
    """Test the agent tools with real data from the knowledge graph."""
    
    logger.info("\n" + "="*60)
    logger.info("Testing agent tools with real knowledge graph data...")
    logger.info("="*60)
    
    try:
        # Import the agent tools
        from agent.tools import (
            get_entity_relationships_tool,
            EntityRelationshipSearchInput
        )
        
        # Test cases - these should match entities that exist in your knowledge graph
        test_cases = [
            {
                "entity_name": "John Chen",
                "entity_type": "person",
                "description": "Testing person relationships"
            },
            {
                "entity_name": "TechCorp Holdings", 
                "entity_type": "company",
                "description": "Testing company relationships"
            },
            {
                "entity_name": "Sarah Chen",
                "entity_type": "person", 
                "description": "Testing another person"
            }
        ]
        
        for test_case in test_cases:
            logger.info(f"\n{'-'*50}")
            logger.info(f"{test_case['description']}: {test_case['entity_name']}")
            logger.info(f"{'-'*50}")
            
            try:
                # Test the enhanced entity relationships tool
                input_data = EntityRelationshipSearchInput(
                    entity_name=test_case["entity_name"],
                    entity_type=test_case["entity_type"],
                    limit=10
                )
                
                relationships = await get_entity_relationships_tool(input_data)
                
                if relationships:
                    logger.info(f"✅ Found {len(relationships)} relationships:")
                    for i, rel in enumerate(relationships, 1):
                        logger.info(f"\n  Relationship {i}:")
                        logger.info(f"    Source: {rel.get('source_entity', 'Unknown')}")
                        logger.info(f"    Target: {rel.get('target_entity', 'Unknown')}")
                        logger.info(f"    Type: {rel.get('relationship_type', 'Unknown')}")
                        logger.info(f"    Direction: {rel.get('direction', 'unknown')}")
                        logger.info(f"    Method: {rel.get('extraction_method', 'unknown')}")
                        if 'details' in rel:
                            logger.info(f"    Details: {rel['details']}")
                else:
                    logger.warning(f"❌ No relationships found for {test_case['entity_name']}")
                    
                    # Try a basic search to see if there are any facts at all
                    logger.info("Checking if any facts exist for this entity...")
                    from agent.graph_utils import graph_client
                    await graph_client.initialize()
                    
                    basic_results = await graph_client.search(f"{test_case['entity_name']}")
                    if basic_results:
                        logger.info(f"Found {len(basic_results)} basic facts:")
                        for i, result in enumerate(basic_results[:2], 1):
                            logger.info(f"  Fact {i}: {result.fact[:150]}...")
                    else:
                        logger.warning(f"No facts found at all for {test_case['entity_name']}")
                        
            except Exception as e:
                logger.error(f"Error testing {test_case['entity_name']}: {e}")
                import traceback
                traceback.print_exc()
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()


async def test_graph_search_tool():
    """Test the graph search tool with relationship queries."""
    
    logger.info(f"\n{'='*60}")
    logger.info("Testing graph search tool for relationships...")
    logger.info(f"{'='*60}")
    
    try:
        from agent.tools import graph_search_tool, GraphSearchInput
        
        # Test queries that should find relationships
        test_queries = [
            "relationships involving John Chen",
            "John Chen executive",
            "TechCorp Holdings employees",
            "Sarah Chen CEO",
            "facts about John Chen"
        ]
        
        for query in test_queries:
            logger.info(f"\nTesting query: '{query}'")
            
            try:
                input_data = GraphSearchInput(query=query)
                results = await graph_search_tool(input_data)
                
                if results:
                    logger.info(f"Found {len(results)} results:")
                    for i, result in enumerate(results[:2], 1):  # Show first 2 results
                        logger.info(f"\n  Result {i}:")
                        logger.info(f"    Fact: {result.fact[:100]}...")
                        logger.info(f"    UUID: {result.uuid}")
                        
                        # Test relationship extraction on this fact
                        from agent.tools import _extract_relationships_from_graphiti_fact
                        relationships = _extract_relationships_from_graphiti_fact(result.fact, "", result.uuid)
                        if relationships:
                            logger.info(f"    Extracted {len(relationships)} relationships:")
                            for rel in relationships:
                                logger.info(f"      - {rel.get('source_entity')} {rel.get('relationship_type')} {rel.get('target_entity')}")
                else:
                    logger.warning(f"No results found for query: '{query}'")
                    
            except Exception as e:
                logger.error(f"Error with query '{query}': {e}")
        
    except Exception as e:
        logger.error(f"Graph search test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    async def run_all_tests():
        await test_ingestion_format_extraction()
        await test_agent_tools_with_real_data()
        await test_graph_search_tool()
    
    asyncio.run(run_all_tests())
