#!/usr/bin/env python3
"""
Test the JSON serialization fix for IngestionResult objects.
"""

import json
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_json_serialization_fix():
    """Test the JSON serialization fix."""
    
    try:
        # Import the models and conversion function
        from agent.models import IngestionResult
        import sys
        sys.path.append('web_ui')
        from web_ui.app import convert_ingestion_results_to_dict
        
        print("="*80)
        print("TESTING JSON SERIALIZATION FIX FOR INGESTIONRESULT")
        print("="*80)
        
        # Create test IngestionResult objects
        result1 = IngestionResult(
            document_id="doc-123",
            title="Test Document 1",
            chunks_created=10,
            entities_extracted=25,
            relationships_created=8,
            processing_time_ms=1500.0,
            errors=["Warning: Large document"]
        )
        
        result2 = IngestionResult(
            document_id="doc-456",
            title="Test Document 2",
            chunks_created=5,
            entities_extracted=12,
            relationships_created=3,
            processing_time_ms=750.0,
            errors=[]
        )
        
        ingestion_results = [result1, result2]
        
        print(f"✅ Created test IngestionResult objects:")
        print(f"   Result 1: {result1.title} - {result1.chunks_created} chunks")
        print(f"   Result 2: {result2.title} - {result2.chunks_created} chunks")
        
        # Test 1: Try to serialize IngestionResult objects directly (should fail)
        print(f"\n🧪 Test 1: Direct JSON serialization of IngestionResult objects")
        try:
            json_str = json.dumps(ingestion_results)
            print(f"❌ Unexpected success: {json_str[:100]}...")
        except TypeError as e:
            print(f"✅ Expected failure: {e}")
        
        # Test 2: Use conversion function (should work)
        print(f"\n🧪 Test 2: JSON serialization after conversion to dict")
        try:
            converted_results = convert_ingestion_results_to_dict(ingestion_results)
            print(f"✅ Conversion successful: {len(converted_results)} results converted")
            
            # Test JSON serialization
            json_str = json.dumps(converted_results, indent=2)
            print(f"✅ JSON serialization successful!")
            print(f"   JSON length: {len(json_str)} characters")
            
            # Verify the structure
            parsed_back = json.loads(json_str)
            print(f"✅ JSON parsing successful: {len(parsed_back)} results")
            
            # Check first result
            first_result = parsed_back[0]
            expected_keys = ['document_id', 'title', 'chunks_created', 'entities_extracted', 
                           'relationships_created', 'processing_time_ms', 'errors']
            
            print(f"\n📋 First result structure:")
            for key in expected_keys:
                if key in first_result:
                    print(f"   ✅ {key}: {first_result[key]}")
                else:
                    print(f"   ❌ Missing key: {key}")
            
        except Exception as e:
            print(f"❌ Conversion failed: {e}")
            import traceback
            traceback.print_exc()
        
        # Test 3: Test single IngestionResult conversion
        print(f"\n🧪 Test 3: Single IngestionResult conversion")
        try:
            single_converted = convert_ingestion_results_to_dict(result1)
            single_json = json.dumps(single_converted, indent=2)
            print(f"✅ Single result conversion successful!")
            print(f"   Result: {single_converted[0]['title']}")
            
        except Exception as e:
            print(f"❌ Single conversion failed: {e}")
        
        # Test 4: Test the complete results structure that would be sent to web UI
        print(f"\n🧪 Test 4: Complete results structure (as used in web UI)")
        try:
            # Simulate the complete results structure from the web UI
            complete_results = {
                'type': 'complete',
                'message': 'Ingestion completed successfully!',
                'details': {
                    'files_processed': 2,
                    'file_names': ['test1.md', 'test2.md'],
                    'chunk_size': 8000,
                    'chunk_overlap': 800,
                    'use_semantic': True,
                    'extract_entities': True,
                    'clean_before_ingest': False,
                    'total_chunks': 15,
                    'total_entities': 37,
                    'total_relationships': 11,
                    'total_errors': 1,
                    'processing_time': '2250.0ms',
                    'ingestion_details': convert_ingestion_results_to_dict(ingestion_results),
                    'cleanup_details': {'person_nodes_fixed': 25, 'company_nodes_fixed': 1, 'total_nodes_fixed': 26}
                }
            }
            
            # Test JSON serialization of complete structure
            complete_json = json.dumps(complete_results, indent=2)
            print(f"✅ Complete results structure serialization successful!")
            print(f"   JSON length: {len(complete_json)} characters")
            
            # Verify it can be parsed back
            parsed_complete = json.loads(complete_json)
            ingestion_details = parsed_complete['details']['ingestion_details']
            print(f"✅ Complete structure parsing successful!")
            print(f"   Ingestion details: {len(ingestion_details)} results")
            print(f"   First result title: {ingestion_details[0]['title']}")
            
        except Exception as e:
            print(f"❌ Complete structure test failed: {e}")
            import traceback
            traceback.print_exc()
        
        # Test 5: Test edge cases
        print(f"\n🧪 Test 5: Edge cases")
        
        # Empty list
        try:
            empty_converted = convert_ingestion_results_to_dict([])
            empty_json = json.dumps(empty_converted)
            print(f"✅ Empty list conversion: {empty_json}")
        except Exception as e:
            print(f"❌ Empty list failed: {e}")
        
        # None value
        try:
            none_converted = convert_ingestion_results_to_dict(None)
            none_json = json.dumps(none_converted)
            print(f"✅ None value conversion: {none_json}")
        except Exception as e:
            print(f"❌ None value failed: {e}")
        
        print(f"\n🎉 JSON serialization fix test completed!")
        print(f"✅ The web UI should now be able to serialize IngestionResult objects properly")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_json_serialization_fix()
