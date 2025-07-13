#!/usr/bin/env python3
"""
Test script to verify relationship extraction from the knowledge graph.
"""

import asyncio
import logging
import sys
import os
from typing import List, Dict, Any

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent.tools import get_enhanced_entity_relationships
from agent.graph_utils import get_graph_client, initialize_graph

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_relationship_extraction():
    """Test relationship extraction for various entities."""
    
    try:
        # Initialize the graph client
        logger.info("Initializing graph client...")
        await initialize_graph()
        
        # Test entities to search for
        test_entities = [
            {"name": "John Chen", "type": "person"},
            {"name": "Sarah Chen", "type": "person"},
            {"name": "TechCorp Holdings", "type": "company"},
            {"name": "TechCorp Inc", "type": "company"},
            {"name": "DataFlow Systems", "type": "company"}
        ]
        
        for entity in test_entities:
            logger.info(f"\n{'='*60}")
            logger.info(f"Testing relationship extraction for: {entity['name']} ({entity['type']})")
            logger.info(f"{'='*60}")
            
            try:
                # Test enhanced relationship extraction
                relationships = await get_enhanced_entity_relationships(
                    entity_name=entity["name"],
                    entity_type=entity["type"],
                    limit=20
                )
                
                if relationships:
                    logger.info(f"Found {len(relationships)} relationships:")
                    for i, rel in enumerate(relationships, 1):
                        logger.info(f"\n  Relationship {i}:")
                        logger.info(f"    Source: {rel.get('source_entity', 'Unknown')}")
                        logger.info(f"    Target: {rel.get('target_entity', 'Unknown')}")
                        logger.info(f"    Type: {rel.get('relationship_type', 'Unknown')}")
                        logger.info(f"    Direction: {rel.get('direction', 'unknown')}")
                        logger.info(f"    Method: {rel.get('extraction_method', 'unknown')}")
                        if 'details' in rel:
                            logger.info(f"    Details: {rel['details']}")
                        logger.info(f"    Fact: {rel.get('fact', '')[:100]}...")
                else:
                    logger.warning(f"No relationships found for {entity['name']}")
                    
                    # Try a basic graph search to see what facts exist
                    logger.info("Trying basic graph search...")
                    basic_results = await graph_client.search(f"facts about {entity['name']}")
                    if basic_results:
                        logger.info(f"Found {len(basic_results)} basic facts:")
                        for fact in basic_results[:3]:  # Show first 3 facts
                            logger.info(f"  - {fact.fact[:150]}...")
                    else:
                        logger.warning(f"No facts found for {entity['name']} in basic search")
                        
            except Exception as e:
                logger.error(f"Error testing {entity['name']}: {e}")
                
        # Test some specific relationship type filtering
        logger.info(f"\n{'='*60}")
        logger.info("Testing relationship type filtering...")
        logger.info(f"{'='*60}")
        
        try:
            filtered_relationships = await get_enhanced_entity_relationships(
                entity_name="John Chen",
                entity_type="person",
                relationship_types=["Executive_OF", "Chairman_OF", "CEO_OF"],
                limit=10
            )
            
            logger.info(f"Found {len(filtered_relationships)} executive relationships for John Chen:")
            for rel in filtered_relationships:
                logger.info(f"  - {rel.get('relationship_type')}: {rel.get('source_entity')} -> {rel.get('target_entity')}")
                
        except Exception as e:
            logger.error(f"Error testing filtered relationships: {e}")
            
    except Exception as e:
        logger.error(f"Test failed: {e}")
        raise
    finally:
        # Close the graph client
        try:
            await graph_client.close()
            logger.info("Graph client closed")
        except Exception as e:
            logger.warning(f"Error closing graph client: {e}")


async def test_fact_extraction_patterns():
    """Test the fact extraction patterns with sample facts."""
    
    logger.info(f"\n{'='*60}")
    logger.info("Testing fact extraction patterns...")
    logger.info(f"{'='*60}")
    
    # Import the extraction function
    from agent.tools import _extract_relationships_from_fact_enhanced
    
    # Sample facts to test
    sample_facts = [
        "Relationship: John Chen Executive_OF TechCorp Holdings\nDescription: John Chen serves as Executive Director",
        "PERSON: Sarah Chen\nEntity Type: Person\nCurrent company: TechCorp Inc\nCurrent position: CEO",
        "COMPANY: DataFlow Systems\nEntity Type: Company\nIndustry: Data Analytics\nKey executives: Michael Wong, Lisa Tan",
        "John Chen is the CEO of TechCorp Holdings and has been with the company since 2020.",
        "TechCorp Holdings employs Sarah Chen as Chief Technology Officer.",
        "Michael Wong works at DataFlow Systems as a Senior Director."
    ]
    
    for i, fact in enumerate(sample_facts, 1):
        logger.info(f"\nTesting fact {i}:")
        logger.info(f"Fact: {fact}")
        
        # Test extraction for different entities
        test_entities = ["John Chen", "Sarah Chen", "TechCorp Holdings", "TechCorp Inc", "DataFlow Systems", "Michael Wong"]
        
        for entity in test_entities:
            relationships = _extract_relationships_from_fact_enhanced(fact, entity, f"test-uuid-{i}")
            if relationships:
                logger.info(f"  Entity '{entity}' relationships:")
                for rel in relationships:
                    logger.info(f"    - {rel.get('source_entity')} {rel.get('relationship_type')} {rel.get('target_entity')} ({rel.get('extraction_method')})")


if __name__ == "__main__":
    # Run the tests
    asyncio.run(test_relationship_extraction())
    asyncio.run(test_fact_extraction_patterns())
