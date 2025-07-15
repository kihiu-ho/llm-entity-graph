#!/usr/bin/env python3
"""
Debug script specifically for Henri Pouret entity extraction issue.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent))

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_simple_extraction():
    """Test simple entity extraction with minimal content."""
    
    # Simple test content with Henri Pouret
    test_content = """
    Henri Pouret is the Vice-Chair for Europe.
    Winfried Engelbrecht Bresges is the Chair.
    International Federation of Horseracing Authorities is the organization.
    """
    
    logger.info("Testing simple entity extraction...")
    logger.info(f"Test content: {test_content}")
    
    try:
        from ingestion.graph_builder import GraphBuilder
        
        graph_builder = GraphBuilder()
        
        # Test direct LLM extraction
        logger.info("Calling _extract_entities_with_llm...")
        entities = await graph_builder._extract_entities_with_llm(
            test_content,
            extract_people=True,
            extract_companies=True
        )
        
        logger.info(f"Raw entities returned: {entities}")
        
        # Check specifically for Henri Pouret
        people = entities.get('people', [])
        logger.info(f"People found: {people}")
        
        if 'Henri Pouret' in people:
            logger.info("✅ SUCCESS: Henri Pouret found!")
        else:
            logger.error("❌ FAILED: Henri Pouret not found")
            
            # Check if any variation exists
            for person in people:
                if 'henri' in person.lower() or 'pouret' in person.lower():
                    logger.info(f"Found similar name: {person}")
        
        return entities
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        return None

async def test_llm_connection():
    """Test if LLM connection is working."""
    
    logger.info("Testing LLM connection...")
    
    try:
        from agent.llm_client import LLMClient
        
        # Check environment variables
        api_key = os.getenv('LLM_API_KEY')
        if not api_key:
            logger.error("❌ LLM_API_KEY not set!")
            return False
        else:
            logger.info(f"✅ LLM_API_KEY is set (length: {len(api_key)})")
        
        # Test LLM client
        llm_client = LLMClient()
        
        # Simple test prompt
        test_prompt = "Extract the person name from this text: Henri Pouret is a person. Return only the name."
        
        response = await llm_client.generate_response(test_prompt)
        logger.info(f"LLM response: {response}")
        
        if 'henri' in response.lower() and 'pouret' in response.lower():
            logger.info("✅ LLM correctly identified Henri Pouret")
            return True
        else:
            logger.warning(f"⚠️ LLM response doesn't contain Henri Pouret: {response}")
            return False
            
    except Exception as e:
        logger.error(f"LLM connection test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_ingestion_pipeline():
    """Test the full ingestion pipeline with IFHA document."""
    
    logger.info("Testing full ingestion pipeline...")
    
    try:
        from ingestion.ingest import DocumentIngestion
        
        # Check if IFHA document exists
        ifha_path = "documents/test/IFHA.md"
        if not os.path.exists(ifha_path):
            logger.error(f"❌ IFHA document not found at {ifha_path}")
            return False
        
        logger.info(f"✅ IFHA document found at {ifha_path}")
        
        # Create ingestion instance
        ingestion = DocumentIngestion()
        
        # Process just the IFHA document
        logger.info("Starting ingestion...")
        results = await ingestion.ingest_documents([ifha_path])
        
        logger.info(f"Ingestion results: {results}")
        
        if results and len(results) > 0:
            result = results[0]
            logger.info(f"Entities extracted: {result.entities_extracted}")
            logger.info(f"Errors: {result.errors}")
            
            if result.entities_extracted > 0:
                logger.info("✅ Entities were extracted")
                return True
            else:
                logger.warning("⚠️ No entities extracted")
                return False
        else:
            logger.error("❌ No results from ingestion")
            return False
            
    except Exception as e:
        logger.error(f"Ingestion pipeline test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main debug function."""
    logger.info("🔍 Starting Henri Pouret debugging...")
    
    # Test 1: LLM connection
    logger.info("\n" + "="*50)
    logger.info("TEST 1: LLM Connection")
    logger.info("="*50)
    llm_ok = await test_llm_connection()
    
    if not llm_ok:
        logger.error("❌ LLM connection failed - stopping tests")
        return
    
    # Test 2: Simple extraction
    logger.info("\n" + "="*50)
    logger.info("TEST 2: Simple Entity Extraction")
    logger.info("="*50)
    entities = await test_simple_extraction()
    
    # Test 3: Full ingestion pipeline
    logger.info("\n" + "="*50)
    logger.info("TEST 3: Full Ingestion Pipeline")
    logger.info("="*50)
    pipeline_ok = await test_ingestion_pipeline()
    
    # Summary
    logger.info("\n" + "="*50)
    logger.info("SUMMARY")
    logger.info("="*50)
    logger.info(f"LLM Connection: {'✅ OK' if llm_ok else '❌ FAILED'}")
    logger.info(f"Simple Extraction: {'✅ OK' if entities else '❌ FAILED'}")
    logger.info(f"Full Pipeline: {'✅ OK' if pipeline_ok else '❌ FAILED'}")

if __name__ == "__main__":
    asyncio.run(main())
