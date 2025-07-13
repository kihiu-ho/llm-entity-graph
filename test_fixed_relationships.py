#!/usr/bin/env python3
"""
Test script to verify the fixed relationship extraction from the knowledge graph.
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


async def test_agent_relationship_extraction():
    """Test the fixed agent relationship extraction tools."""
    
    logger.info("Testing fixed agent relationship extraction...")
    
    try:
        # Import the agent tools
        from agent.tools import (
            get_entity_relationships_tool,
            EntityRelationshipSearchInput
        )
        
        # Test cases with different entity types
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
            },
            {
                "entity_name": "DataFlow Systems",
                "entity_type": "company",
                "description": "Testing another company"
            }
        ]
        
        for test_case in test_cases:
            logger.info(f"\n{'='*60}")
            logger.info(f"{test_case['description']}: {test_case['entity_name']}")
            logger.info(f"{'='*60}")
            
            try:
                # Test the enhanced entity relationships tool
                input_data = EntityRelationshipSearchInput(
                    entity_name=test_case["entity_name"],
                    entity_type=test_case["entity_type"],
                    limit=15
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
                        
                        # Show a snippet of the original fact
                        fact = rel.get('fact', '')
                        if fact:
                            fact_snippet = fact.replace('\n', ' ')[:100]
                            logger.info(f"    Fact: {fact_snippet}...")
                else:
                    logger.warning(f"❌ No relationships found for {test_case['entity_name']}")
                    
                    # Try a basic search to see if there are any facts at all
                    logger.info("Checking if any facts exist for this entity...")
                    from agent.graph_utils import get_graph_client
                    client = get_graph_client()
                    await client.initialize()
                    
                    basic_results = await graph_client.search(f"{test_case['entity_name']}")
                    if basic_results:
                        logger.info(f"Found {len(basic_results)} basic facts (but no relationships extracted)")
                        for i, result in enumerate(basic_results[:2], 1):
                            logger.info(f"  Fact {i}: {result.fact[:100]}...")
                    else:
                        logger.warning(f"No facts found at all for {test_case['entity_name']}")
                        
            except Exception as e:
                logger.error(f"Error testing {test_case['entity_name']}: {e}")
                import traceback
                traceback.print_exc()
        
        # Test relationship type filtering
        logger.info(f"\n{'='*60}")
        logger.info("Testing relationship type filtering...")
        logger.info(f"{'='*60}")
        
        try:
            # Test with specific relationship types
            input_data = EntityRelationshipSearchInput(
                entity_name="John Chen",
                entity_type="person",
                relationship_types=["Executive_OF", "CEO_OF", "Chairman_OF", "Employee_OF"],
                limit=10
            )
            
            filtered_relationships = await get_entity_relationships_tool(input_data)
            
            if filtered_relationships:
                logger.info(f"✅ Found {len(filtered_relationships)} filtered relationships:")
                for rel in filtered_relationships:
                    logger.info(f"  - {rel.get('relationship_type')}: {rel.get('source_entity')} -> {rel.get('target_entity')}")
            else:
                logger.warning("❌ No filtered relationships found")
                
        except Exception as e:
            logger.error(f"Error testing relationship filtering: {e}")
            
    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()


async def test_fact_extraction_patterns():
    """Test the enhanced fact extraction patterns with sample facts."""
    
    logger.info(f"\n{'='*60}")
    logger.info("Testing enhanced fact extraction patterns...")
    logger.info(f"{'='*60}")
    
    try:
        # Import the extraction function
        from agent.tools import _extract_relationships_from_fact_enhanced
        
        # Sample facts that match the format used during ingestion
        sample_facts = [
            # Direct relationship format
            "Relationship: John Chen Executive_OF TechCorp Holdings\nDescription: John Chen serves as Executive Director\nStrength: 1.0\nActive: True",
            
            # Structured entity format (Person)
            "PERSON: Sarah Chen\nEntity Type: Person\nCurrent company: TechCorp Inc\nCurrent position: CEO\nFull name: Sarah Chen",
            
            # Structured entity format (Company)
            "COMPANY: DataFlow Systems\nEntity Type: Company\nIndustry: Data Analytics\nKey executives: Michael Wong, Lisa Tan\nHeadquarters: Singapore",
            
            # Natural language format
            "John Chen is the CEO of TechCorp Holdings and has been with the company since 2020. He previously worked at DataFlow Systems as a Senior Director.",
            
            # Employment format
            "TechCorp Holdings employs Sarah Chen as Chief Technology Officer. She joined the company in 2022.",
            
            # Multiple relationships
            "Michael Wong works at DataFlow Systems as a Senior Director. The company is a subsidiary of TechCorp Holdings."
        ]
        
        test_entities = ["John Chen", "Sarah Chen", "TechCorp Holdings", "TechCorp Inc", "DataFlow Systems", "Michael Wong"]
        
        for i, fact in enumerate(sample_facts, 1):
            logger.info(f"\n--- Testing Fact {i} ---")
            logger.info(f"Fact: {fact}")
            
            for entity in test_entities:
                relationships = _extract_relationships_from_fact_enhanced(fact, entity, f"test-uuid-{i}")
                if relationships:
                    logger.info(f"\n  Entity '{entity}' relationships:")
                    for rel in relationships:
                        logger.info(f"    ✅ {rel.get('source_entity')} {rel.get('relationship_type')} {rel.get('target_entity')} ({rel.get('extraction_method')})")
                        if 'details' in rel:
                            logger.info(f"       Details: {rel['details']}")
        
        logger.info(f"\n✅ Fact extraction pattern testing completed!")
        
    except Exception as e:
        logger.error(f"Error testing fact extraction patterns: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    async def run_all_tests():
        await test_fact_extraction_patterns()
        await test_agent_relationship_extraction()
    
    asyncio.run(run_all_tests())
