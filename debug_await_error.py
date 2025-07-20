#!/usr/bin/env python3
"""
Debug script to isolate the "object list can't be used in 'await' expression" error.
"""

import asyncio
import logging
import os
import tempfile
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def test_step_by_step():
    """Test each step of the ingestion process to isolate the error."""
    
    print("="*80)
    print("DEBUGGING 'object list can't be used in 'await' expression' ERROR")
    print("="*80)
    
    try:
        # Create test document
        temp_dir = tempfile.mkdtemp()
        test_file = os.path.join(temp_dir, "debug_test.md")
        
        with open(test_file, 'w') as f:
            f.write("""# Debug Test Document

John Smith is the CEO of TestCorp.
""")
        
        print(f"✅ Step 1: Created test document")
        
        # Test 1: Import modules
        try:
            from ingestion.ingest import DocumentIngestionPipeline
            from agent.models import IngestionConfig
            print(f"✅ Step 2: Imported modules successfully")
        except Exception as e:
            print(f"❌ Step 2 failed: {e}")
            return
        
        # Test 2: Create configuration
        try:
            config = IngestionConfig(
                chunk_size=8000,
                chunk_overlap=800,
                use_semantic_chunking=False,
                extract_entities=False,  # Disable entity extraction to isolate
                skip_graph_building=True
            )
            print(f"✅ Step 3: Created configuration")
        except Exception as e:
            print(f"❌ Step 3 failed: {e}")
            return
        
        # Test 3: Create pipeline
        try:
            pipeline = DocumentIngestionPipeline(
                config=config,
                documents_folder=temp_dir,
                clean_before_ingest=False
            )
            print(f"✅ Step 4: Created pipeline")
        except Exception as e:
            print(f"❌ Step 4 failed: {e}")
            return
        
        # Test 4: Initialize pipeline
        try:
            # Don't call initialize yet, just test basic functionality
            print(f"✅ Step 5: Pipeline created without initialization")
        except Exception as e:
            print(f"❌ Step 5 failed: {e}")
            return
        
        # Test 5: Try to run ingestion with minimal config
        try:
            print(f"🔄 Step 6: Running minimal ingestion...")
            results = await pipeline.ingest_documents()
            print(f"✅ Step 6: Ingestion completed without error")
            print(f"   Results type: {type(results)}")
            print(f"   Results length: {len(results) if isinstance(results, list) else 'N/A'}")
            
            if isinstance(results, list) and len(results) > 0:
                result = results[0]
                print(f"   First result: {result}")
                print(f"   Errors: {result.errors}")
            
        except Exception as e:
            print(f"❌ Step 6 failed: {e}")
            import traceback
            traceback.print_exc()
            
            # Check if it's the specific error
            if "object list can't be used in 'await' expression" in str(e):
                print(f"\n🎯 FOUND THE ERROR!")
                print(f"   This is the exact error we're looking for")
                
                # Try to get more details about where it occurred
                tb = traceback.format_exc()
                lines = tb.split('\n')
                for i, line in enumerate(lines):
                    if 'await' in line and ('list' in line or '[' in line):
                        print(f"   Suspicious line: {line.strip()}")
                        if i > 0:
                            print(f"   Previous line: {lines[i-1].strip()}")
                        if i < len(lines) - 1:
                            print(f"   Next line: {lines[i+1].strip()}")
            
            return
        
        # Test 6: Try with entity extraction enabled
        try:
            print(f"🔄 Step 7: Testing with entity extraction...")
            config.extract_entities = True
            
            pipeline2 = DocumentIngestionPipeline(
                config=config,
                documents_folder=temp_dir,
                clean_before_ingest=False
            )
            
            results2 = await pipeline2.ingest_documents()
            print(f"✅ Step 7: Entity extraction completed without error")
            
        except Exception as e:
            print(f"❌ Step 7 failed: {e}")
            
            if "object list can't be used in 'await' expression" in str(e):
                print(f"\n🎯 ERROR OCCURS WITH ENTITY EXTRACTION!")
                print(f"   The error is likely in the entity extraction process")
            
            import traceback
            traceback.print_exc()
            return
        
        # Test 7: Try with graph building enabled
        try:
            print(f"🔄 Step 8: Testing with graph building...")
            config.skip_graph_building = False
            
            pipeline3 = DocumentIngestionPipeline(
                config=config,
                documents_folder=temp_dir,
                clean_before_ingest=False
            )
            
            results3 = await pipeline3.ingest_documents()
            print(f"✅ Step 8: Graph building completed without error")
            
        except Exception as e:
            print(f"❌ Step 8 failed: {e}")
            
            if "object list can't be used in 'await' expression" in str(e):
                print(f"\n🎯 ERROR OCCURS WITH GRAPH BUILDING!")
                print(f"   The error is likely in the graph building process")
            
            import traceback
            traceback.print_exc()
            return
        
        print(f"\n🎉 All steps completed successfully!")
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up
        try:
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
        except:
            pass

if __name__ == "__main__":
    asyncio.run(test_step_by_step())
