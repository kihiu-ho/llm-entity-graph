#!/usr/bin/env python3
"""
Test minimal ingestion to isolate the exact error location.
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

async def test_minimal_ingestion():
    """Test the most minimal ingestion possible."""
    
    print("="*80)
    print("TESTING MINIMAL INGESTION TO ISOLATE ERROR")
    print("="*80)
    
    try:
        # Create test document
        temp_dir = tempfile.mkdtemp()
        test_file = os.path.join(temp_dir, "minimal_test.md")
        
        with open(test_file, 'w') as f:
            f.write("# Minimal Test\n\nThis is a minimal test document.")
        
        print(f"✅ Created minimal test document: {test_file}")
        
        # Test 1: Just chunking
        print(f"\n🔄 Test 1: Testing chunking only...")
        try:
            from ingestion.chunker import DocumentChunker
            from agent.models import IngestionConfig
            
            config = IngestionConfig(
                chunk_size=1000,
                chunk_overlap=100,
                use_semantic_chunking=False,  # Disable semantic chunking
                extract_entities=False,
                skip_graph_building=True
            )
            
            chunker = DocumentChunker(config)
            
            with open(test_file, 'r') as f:
                content = f.read()
            
            chunks = await chunker.chunk_document(
                content=content,
                title="Minimal Test",
                source=test_file
            )
            
            print(f"✅ Chunking successful: {len(chunks)} chunks created")
            
        except Exception as e:
            print(f"❌ Chunking failed: {e}")
            if "object list can't be used in 'await' expression" in str(e):
                print(f"🎯 FOUND THE ERROR IN CHUNKING!")
                import traceback
                traceback.print_exc()
                return False
        
        # Test 2: Just embedding
        print(f"\n🔄 Test 2: Testing embedding only...")
        try:
            from ingestion.embedder import DocumentEmbedder
            from agent.models import DocumentChunk
            
            embedder = DocumentEmbedder()
            
            # Create a simple chunk
            test_chunk = DocumentChunk(
                content="This is a test chunk",
                index=0,
                start_char=0,
                end_char=20,
                metadata={"test": True},
                token_count=5
            )
            
            embedded_chunks = await embedder.embed_chunks([test_chunk])
            
            print(f"✅ Embedding successful: {len(embedded_chunks)} chunks embedded")
            
        except Exception as e:
            print(f"❌ Embedding failed: {e}")
            if "object list can't be used in 'await' expression" in str(e):
                print(f"🎯 FOUND THE ERROR IN EMBEDDING!")
                import traceback
                traceback.print_exc()
                return False
        
        # Test 3: Just database save
        print(f"\n🔄 Test 3: Testing database save only...")
        try:
            from ingestion.ingest import DocumentIngestionPipeline
            
            config = IngestionConfig(
                chunk_size=1000,
                chunk_overlap=100,
                use_semantic_chunking=False,
                extract_entities=False,
                skip_graph_building=True
            )
            
            pipeline = DocumentIngestionPipeline(
                config=config,
                documents_folder=temp_dir,
                clean_before_ingest=False
            )
            
            # Test just the database save part
            test_chunk = DocumentChunk(
                content="This is a test chunk",
                index=0,
                start_char=0,
                end_char=20,
                metadata={"test": True},
                token_count=5
            )
            
            # Add embedding
            test_chunk.embedding = [0.1, 0.2, 0.3] * 100  # Simple embedding
            
            document_id = await pipeline._save_to_postgres(
                title="Test Document",
                source=test_file,
                content="Test content",
                chunks=[test_chunk],
                metadata={"test": True}
            )
            
            print(f"✅ Database save successful: document_id = {document_id}")
            
        except Exception as e:
            print(f"❌ Database save failed: {e}")
            if "object list can't be used in 'await' expression" in str(e):
                print(f"🎯 FOUND THE ERROR IN DATABASE SAVE!")
                import traceback
                traceback.print_exc()
                return False
        
        # Test 4: Full minimal pipeline
        print(f"\n🔄 Test 4: Testing full minimal pipeline...")
        try:
            config = IngestionConfig(
                chunk_size=1000,
                chunk_overlap=100,
                use_semantic_chunking=False,
                extract_entities=False,
                skip_graph_building=True
            )
            
            pipeline = DocumentIngestionPipeline(
                config=config,
                documents_folder=temp_dir,
                clean_before_ingest=False
            )
            
            results = await pipeline.ingest_documents()
            
            print(f"✅ Full pipeline successful: {len(results)} results")
            if results:
                result = results[0]
                print(f"   Chunks: {result.chunks_created}")
                print(f"   Entities: {result.entities_extracted}")
                print(f"   Relationships: {result.relationships_created}")
                print(f"   Errors: {result.errors}")
            
            await pipeline.close()
            
        except Exception as e:
            print(f"❌ Full pipeline failed: {e}")
            if "object list can't be used in 'await' expression" in str(e):
                print(f"🎯 FOUND THE ERROR IN FULL PIPELINE!")
                import traceback
                traceback.print_exc()
                return False
        
        print(f"\n🎉 ALL MINIMAL TESTS PASSED!")
        print(f"   The error is not in the basic components")
        print(f"   The issue might be in a specific combination or configuration")
        return True
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Clean up
        try:
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
        except:
            pass

if __name__ == "__main__":
    success = asyncio.run(test_minimal_ingestion())
    
    print(f"\n🎯 MINIMAL TEST RESULT: {'SUCCESS' if success else 'FAILED'}")
    
    if success:
        print("✅ All basic components work correctly")
        print("✅ The error is likely in a specific configuration or interaction")
    else:
        print("❌ Found the specific component causing the error")
        print("❌ Check the error details above")
