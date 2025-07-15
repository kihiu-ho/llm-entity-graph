#!/usr/bin/env python3
"""
Test script to debug entity extraction for Henri Pouret and other IFHA entities.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent))

from ingestion.graph_builder import GraphBuilder

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_entity_extraction():
    """Test entity extraction with IFHA content."""
    
    # Sample IFHA content that should contain Henri Pouret
    test_content = """
    International Federation of Horseracing Authorities
    
    Executive Council
    
    Winfried Engelbrecht Bresges
    Chair
    
    Henri Pouret
    Vice-Chair, Europe
    
    Masayuki Goto
    Vice-Chair, Asia
    
    Jim Gagliano
    Vice-Chair, Americas
    
    EUROPE France (1 vote) Great Britain (1 vote) Ireland (1 vote)
    
    Henri Pouret
    France Galop
    
    Brant Dunshea
    British Horseracing Authority
    
    Darragh O'Loughlin
    Irish Horseracing Regulatory Board
    """
    
    logger.info("Starting entity extraction test...")
    
    try:
        # Initialize graph builder
        graph_builder = GraphBuilder()
        
        # Test the preprocessing function
        logger.info("Testing content preprocessing...")
        processed_content = graph_builder._preprocess_organizational_content(test_content)
        logger.info(f"Processed content length: {len(processed_content)} chars")
        logger.info(f"Processed content preview: {processed_content[:200]}...")
        
        # Test LLM entity extraction
        logger.info("Testing LLM entity extraction...")
        entities = await graph_builder._extract_entities_with_llm(
            test_content,
            extract_companies=True,
            extract_people=True,
            extract_corporate_roles=True,
            extract_personal_connections=True
        )
        
        logger.info(f"Extraction completed. Found categories: {list(entities.keys())}")
        
        # Check for Henri Pouret specifically
        people = entities.get('people', [])
        logger.info(f"People extracted: {people}")
        
        if 'Henri Pouret' in people:
            logger.info("✅ Henri Pouret found in people entities!")
        else:
            logger.warning("❌ Henri Pouret NOT found in people entities")
            logger.info("Checking if Henri Pouret appears in any category...")
            
            for category, items in entities.items():
                if isinstance(items, list):
                    if any('Henri' in str(item) for item in items):
                        logger.info(f"Found Henri in {category}: {[item for item in items if 'Henri' in str(item)]}")
                elif isinstance(items, dict):
                    for subcategory, subitems in items.items():
                        if isinstance(subitems, list):
                            if any('Henri' in str(item) for item in subitems):
                                logger.info(f"Found Henri in {category}.{subcategory}: {[item for item in subitems if 'Henri' in str(item)]}")
        
        # Check companies
        companies = entities.get('companies', [])
        logger.info(f"Companies extracted: {companies}")
        
        # Check corporate roles
        corporate_roles = entities.get('corporate_roles', {})
        logger.info(f"Corporate roles extracted: {corporate_roles}")
        
        return entities
        
    except Exception as e:
        logger.error(f"Entity extraction test failed: {e}")
        import traceback
        traceback.print_exc()
        return None

async def test_person_classification():
    """Test the person classification logic specifically."""
    
    logger.info("Testing person classification logic...")
    
    graph_builder = GraphBuilder()
    
    # Test names that should be classified as people
    test_names = [
        "Henri Pouret",
        "Winfried Engelbrecht Bresges", 
        "Masayuki Goto",
        "Jim Gagliano",
        "Brant Dunshea",
        "Darragh O'Loughlin"
    ]
    
    person_indicators = {
        'titles': ['mr', 'mrs', 'ms', 'dr', 'prof', 'sir', 'dame', 'lord', 'lady'],
        'suffixes': ['jr', 'sr', 'ii', 'iii', 'iv', 'phd', 'md', 'esq'],
        'roles': ['ceo', 'cfo', 'cto', 'chairman', 'director', 'president', 'manager', 'officer']
    }
    
    for name in test_names:
        is_person = graph_builder._is_person_entity(name, person_indicators)
        logger.info(f"'{name}' classified as person: {is_person}")

async def main():
    """Main test function."""
    logger.info("🧪 Starting entity extraction debugging...")
    
    # Test person classification
    await test_person_classification()
    
    print("\n" + "="*50 + "\n")
    
    # Test full entity extraction
    entities = await test_entity_extraction()
    
    if entities:
        logger.info("✅ Entity extraction test completed successfully")
    else:
        logger.error("❌ Entity extraction test failed")

if __name__ == "__main__":
    asyncio.run(main())
