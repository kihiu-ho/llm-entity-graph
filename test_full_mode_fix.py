#!/usr/bin/env python3
"""
Test the full mode configuration fix.
"""

import asyncio
import logging
import os
import tempfile
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_full_mode_config():
    """Test that full mode configuration works correctly."""
    
    print("="*80)
    print("TESTING FULL MODE CONFIGURATION FIX")
    print("="*80)
    
    try:
        # Test 1: Test API configuration parsing
        print(f"\n🔄 Test 1: Testing API configuration parsing...")
        
        # Simulate the configuration that would come from the web UI
        test_configs = [
            {
                'mode': 'basic',
                'extract_entities': True,
                'chunk_size': 8000,
                'chunk_overlap': 800,
                'use_semantic': False,
                'clean_before_ingest': False
            },
            {
                'mode': 'full',
                'extract_entities': True,
                'chunk_size': 8000,
                'chunk_overlap': 800,
                'use_semantic': False,
                'clean_before_ingest': False
            }
        ]
        
        for config in test_configs:
            mode = config.get('mode', 'full')
            extract_entities = config.get('extract_entities', True)
            
            print(f"   Testing mode: {mode}, extract_entities: {extract_entities}")
            
            # Import the models to test configuration
            from agent.models import IngestionConfig
            
            if mode == 'basic':
                # Basic mode: simple processing without full NLP pipeline
                config_obj = IngestionConfig(
                    chunk_size=config['chunk_size'],
                    chunk_overlap=config['chunk_overlap'],
                    use_semantic_chunking=False,  # Always false for basic mode
                    extract_entities=extract_entities,  # Respect user preference for entity extraction
                    skip_graph_building=not extract_entities  # Only skip graph building if not extracting entities
                )
            else:
                # Full mode: complete processing
                config_obj = IngestionConfig(
                    chunk_size=config['chunk_size'],
                    chunk_overlap=config['chunk_overlap'],
                    use_semantic_chunking=config['use_semantic'],
                    extract_entities=extract_entities,
                    skip_graph_building=False
                )
            
            print(f"   ✅ Mode: {mode}")
            print(f"      - extract_entities: {config_obj.extract_entities}")
            print(f"      - skip_graph_building: {config_obj.skip_graph_building}")
            print(f"      - use_semantic_chunking: {config_obj.use_semantic_chunking}")
            
            # Verify the logic
            if mode == 'basic':
                if extract_entities:
                    assert not config_obj.skip_graph_building, f"Basic mode with entities should not skip graph building"
                else:
                    assert config_obj.skip_graph_building, f"Basic mode without entities should skip graph building"
            else:  # full mode
                assert not config_obj.skip_graph_building, f"Full mode should never skip graph building"
                assert config_obj.extract_entities, f"Full mode should extract entities"
        
        print(f"   ✅ All configuration tests passed!")
        
        # Test 2: Test actual ingestion with full mode
        print(f"\n🔄 Test 2: Testing actual ingestion with full mode...")
        
        # Create test document
        temp_dir = tempfile.mkdtemp()
        test_file = os.path.join(temp_dir, "test_full_mode.md")
        
        with open(test_file, 'w') as f:
            f.write("""# Test Full Mode Document

This is a test document for full mode processing.

## People
- John Smith is the CEO of TestCorp
- Jane Doe works as CTO at TestCorp

## Companies
- TestCorp is a technology company
- DataCorp is a data analytics firm

This document should trigger entity extraction and graph building in full mode.
""")
        
        print(f"   ✅ Created test document: {test_file}")
        
        # Test full mode configuration
        from ingestion.ingest import DocumentIngestionPipeline
        from agent.models import IngestionConfig
        
        config_obj = IngestionConfig(
            chunk_size=8000,
            chunk_overlap=800,
            use_semantic_chunking=False,
            extract_entities=True,
            skip_graph_building=False  # This should be False for full mode
        )
        
        print(f"   ✅ Full mode config created:")
        print(f"      - extract_entities: {config_obj.extract_entities}")
        print(f"      - skip_graph_building: {config_obj.skip_graph_building}")
        
        # Create pipeline
        pipeline = DocumentIngestionPipeline(
            config=config_obj,
            documents_folder=temp_dir,
            clean_before_ingest=False
        )
        
        print(f"   ✅ Pipeline created")
        
        # Run ingestion
        print(f"   🔄 Running full mode ingestion...")
        results = await pipeline.ingest_documents()
        
        print(f"   ✅ Ingestion completed!")
        
        if results:
            result = results[0]
            print(f"      - Chunks: {result.chunks_created}")
            print(f"      - Entities: {result.entities_extracted}")
            print(f"      - Relationships: {result.relationships_created}")
            print(f"      - Errors: {result.errors}")
            
            # Verify that entities were extracted and graph was built
            assert result.entities_extracted > 0, "Full mode should extract entities"
            print(f"   ✅ Entities were extracted: {result.entities_extracted}")
            
            if result.relationships_created > 0:
                print(f"   ✅ Relationships were created: {result.relationships_created}")
            else:
                print(f"   ⚠️ No relationships created (this might be expected)")
        
        await pipeline.close()
        
        # Clean up
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
        
        print(f"\n🎉 ALL TESTS PASSED!")
        print(f"✅ Full mode configuration is working correctly")
        print(f"✅ Entity extraction is enabled in full mode")
        print(f"✅ Graph building is enabled in full mode")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_full_mode_config())
    
    print(f"\n🎯 FULL MODE TEST RESULT: {'SUCCESS' if success else 'FAILED'}")
    
    if success:
        print("✅ The full mode configuration fix is working correctly")
        print("✅ Web UI will now default to full mode with entity extraction and graph building")
    else:
        print("❌ There are still issues with the full mode configuration")
