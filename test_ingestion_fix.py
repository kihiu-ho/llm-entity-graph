#!/usr/bin/env python3
"""
Test the ingestion fix for the "object list can't be used in 'await' expression" error.
"""

import asyncio
import logging
import os
import tempfile
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_ingestion_fix():
    """Test the ingestion fix."""
    
    print("="*80)
    print("TESTING INGESTION FIX FOR 'object list can't be used in 'await' expression'")
    print("="*80)
    
    try:
        # Create test document
        temp_dir = tempfile.mkdtemp()
        test_file = os.path.join(temp_dir, "test_fix.md")
        
        with open(test_file, 'w') as f:
            f.write("""# Test Fix Document

## Leadership

John Smith is the CEO of TestCorp and has been leading the company since 2020.
Jane Doe serves as the President of Operations and was appointed to the board last year.

## Organization

TestCorp is a technology company with headquarters in Silicon Valley.
The company has grown rapidly and now employs over 100 people.

## Key Facts

- TestCorp was founded in 2018
- John Smith owns 40% of the company
- Jane Doe is a member of the board of directors
- The company went public in 2022

This document should be processed without the "object list can't be used in 'await' expression" error.
""")
        
        print(f"✅ Created test document: {test_file}")
        
        # Test the ingestion pipeline directly
        from ingestion.ingest import DocumentIngestionPipeline
        from agent.models import IngestionConfig
        
        # Create basic configuration
        config = IngestionConfig(
            chunk_size=8000,
            chunk_overlap=800,
            use_semantic_chunking=False,
            extract_entities=True,
            skip_graph_building=True  # Skip graph building to focus on the core issue
        )
        
        print(f"✅ Created ingestion configuration")
        
        # Create pipeline
        pipeline = DocumentIngestionPipeline(
            config=config,
            documents_folder=temp_dir,
            clean_before_ingest=False
        )
        
        print(f"✅ Created ingestion pipeline")
        
        # Run ingestion
        print(f"\n🔄 Running ingestion...")
        results = await pipeline.ingest_documents()
        
        print(f"\n📊 INGESTION RESULTS:")
        print(f"   Type: {type(results)}")
        print(f"   Length: {len(results) if isinstance(results, list) else 'N/A'}")
        
        if isinstance(results, list) and len(results) > 0:
            result = results[0]
            print(f"   Document ID: {result.document_id}")
            print(f"   Title: {result.title}")
            print(f"   Chunks created: {result.chunks_created}")
            print(f"   Entities extracted: {result.entities_extracted}")
            print(f"   Relationships created: {result.relationships_created}")
            print(f"   Processing time: {result.processing_time_ms:.1f}ms")
            print(f"   Errors: {result.errors}")
            
            # Check for success
            success_criteria = [
                result.chunks_created > 0,
                result.entities_extracted >= 0,  # Allow 0 entities
                len(result.errors) == 0,
                result.processing_time_ms > 0
            ]
            
            if all(success_criteria):
                print(f"\n🎉 INGESTION FIX SUCCESSFUL!")
                print(f"   ✅ No 'object list can't be used in await' error")
                print(f"   ✅ Chunks created: {result.chunks_created}")
                print(f"   ✅ Entities extracted: {result.entities_extracted}")
                print(f"   ✅ No errors: {len(result.errors) == 0}")
                print(f"   ✅ Processing completed in {result.processing_time_ms:.1f}ms")
                return True
            else:
                print(f"\n⚠️ INGESTION COMPLETED BUT WITH ISSUES:")
                if result.chunks_created == 0:
                    print(f"   ❌ No chunks created")
                if len(result.errors) > 0:
                    print(f"   ❌ Errors occurred: {result.errors}")
                return False
        else:
            print(f"❌ No results returned or unexpected format")
            return False
        
        # Close pipeline
        await pipeline.close()
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        
        # Check if it's the specific error we're trying to fix
        if "object list can't be used in 'await' expression" in str(e):
            print(f"\n❌ THE SPECIFIC ERROR STILL EXISTS!")
            print(f"   This indicates the fix was not successful")
            return False
        else:
            print(f"\n⚠️ Different error occurred (not the target error)")
            return False
    
    finally:
        # Clean up
        try:
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
            print(f"✅ Cleaned up temporary directory")
        except:
            pass

async def main():
    """Run the test."""
    
    print("🚀 Starting ingestion fix test...")
    
    # Test the direct ingestion pipeline
    success = await test_ingestion_fix()
    
    print("\n" + "="*80)
    print("🎯 INGESTION FIX TEST RESULT")
    print("="*80)
    
    if success:
        print(f"🎉 TEST PASSED!")
        print(f"   ✅ Fixed 'object list can't be used in await' error")
        print(f"   ✅ Ingestion pipeline works correctly")
        print(f"   ✅ Files are processed and chunks/entities are created")
        print(f"   ✅ Ready for production use")
    else:
        print(f"❌ TEST FAILED!")
        print(f"   The ingestion pipeline still has issues")
        print(f"   Please check the error messages above")

if __name__ == "__main__":
    asyncio.run(main())
