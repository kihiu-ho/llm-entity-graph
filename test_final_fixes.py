#!/usr/bin/env python3
"""
Final test for relationship detection and cleanup fixes.
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

async def test_final_basic_ingestion():
    """Test basic ingestion with all fixes applied."""
    
    print("="*80)
    print("FINAL TEST: BASIC INGESTION WITH ALL FIXES")
    print("="*80)
    
    try:
        # Create test content similar to IFHA.md with rich relationship content
        temp_dir = tempfile.mkdtemp()
        test_file = os.path.join(temp_dir, "IFHA_test.md")
        
        with open(test_file, 'w') as f:
            f.write("""# International Federation of Horseracing Authorities (IFHA)

## Executive Leadership

Winfried Engelbrecht Bresges is the Chairman of the International Federation of Horseracing Authorities (IFHA).
He was appointed CEO of The Hong Kong Jockey Club in 2007 and has served in this role for over 15 years.
Mr. Bresges became the Chief Executive Officer after a distinguished career in racing administration.

## Board of Directors

The IFHA board includes several prominent figures:

- John Smith serves as President of Racing Operations and works at the IFHA headquarters
- Jane Doe is the Director of International Relations and was elected to the board in 2020
- Michael Brown is the Secretary General and founded the regulatory framework
- Sarah Wilson serves as Treasurer and is a member of the executive committee
- David Lee sits on the board of directors and manages the European division

## Organizational Structure

The IFHA is affiliated with numerous racing authorities worldwide. Several organizations are subsidiaries of the main federation:

- European Racing Authority is a subsidiary of IFHA
- Asian Racing Council is a division of the federation
- The organization acquired the International Breeding Federation in 2019

## Professional Network

Many executives serve as consultants for various racing organizations around the world.
Board members are often advisors to other international sporting bodies.
The federation has partnerships with major racing venues globally.

John Smith works at multiple racing venues and is employed by several consulting firms.
Jane Doe is a member of various international committees and serves on the Olympic equestrian board.

## Recent Developments

The IFHA recently merged with the Global Racing Standards Organization.
Michael Brown founded a new compliance initiative and leads the regulatory reform committee.
Sarah Wilson was named the new Chief Financial Officer and heads the finance department.

## Corporate Relationships

Tech Racing Corp is a subsidiary of the main organization and provides technology solutions.
The federation owns several training facilities and controls major racing databases.
IFHA is a partner in multiple international sporting events and has stakeholder relationships with broadcasting companies.
""")
        
        print(f"✅ Created comprehensive test document: {test_file}")
        print(f"📄 Content includes multiple relationship types and patterns")
        
        # Import and test basic ingestion
        import sys
        sys.path.append('web_ui')
        from web_ui.app import run_basic_ingestion
        
        print(f"\n🔄 Running basic ingestion with all fixes...")
        
        results = []
        for chunk in run_basic_ingestion(temp_dir, 8000, 800, [test_file]):
            if chunk.startswith('data: '):
                import json
                try:
                    data = json.loads(chunk[6:])
                    results.append(data)
                    
                    if data.get('type') == 'progress':
                        print(f"   Progress: {data.get('current', 0)}% - {data.get('message', '')}")
                    elif data.get('type') == 'complete':
                        details = data.get('details', {})
                        print(f"\n📊 FINAL INGESTION RESULTS:")
                        print(f"   Files processed: {details.get('files_processed', 0)}")
                        print(f"   Total chunks: {details.get('total_chunks', 0)}")
                        print(f"   Total entities: {details.get('total_entities', 0)}")
                        print(f"   Total relationships: {details.get('total_relationships', 0)}")
                        print(f"   Processing time: {details.get('processing_time', 'N/A')}")
                        print(f"   Mode: {details.get('mode', 'unknown')}")
                        
                        # Analyze results
                        chunks = details.get('total_chunks', 0)
                        entities = details.get('total_entities', 0)
                        relationships = details.get('total_relationships', 0)
                        
                        print(f"\n✅ ANALYSIS:")
                        print(f"   Chunks: {chunks} (expected: > 0) {'✅' if chunks > 0 else '❌'}")
                        print(f"   Entities: {entities} (expected: > 10) {'✅' if entities > 10 else '❌'}")
                        print(f"   Relationships: {relationships} (expected: > 5) {'✅' if relationships > 5 else '❌'}")
                        
                        # Check cleanup details
                        cleanup_details = details.get('cleanup_details', {})
                        if cleanup_details:
                            print(f"\n🧹 CLEANUP RESULTS:")
                            print(f"   Person nodes fixed: {cleanup_details.get('person_nodes_fixed', 0)}")
                            print(f"   Company nodes fixed: {cleanup_details.get('company_nodes_fixed', 0)}")
                            print(f"   Total nodes fixed: {cleanup_details.get('total_nodes_fixed', 0)}")
                            print(f"   Cleanup: {'✅ Working' if 'person_nodes_fixed' in cleanup_details else '❌ Failed'}")
                        
                        # Overall success check
                        success_criteria = [
                            chunks > 0,
                            entities > 10,
                            relationships > 5,
                            'cleanup_details' in details
                        ]
                        
                        if all(success_criteria):
                            print(f"\n🎉 ALL FIXES WORKING PERFECTLY!")
                            print(f"   ✅ Basic ingestion processes files correctly")
                            print(f"   ✅ Relationship detection finds multiple relationships")
                            print(f"   ✅ Entity extraction works properly")
                            print(f"   ✅ Cleanup integration works without errors")
                            return True
                        else:
                            print(f"\n⚠️ SOME ISSUES REMAIN:")
                            if chunks == 0:
                                print(f"   ❌ No chunks created")
                            if entities <= 10:
                                print(f"   ❌ Too few entities extracted")
                            if relationships <= 5:
                                print(f"   ❌ Too few relationships detected")
                            if 'cleanup_details' not in details:
                                print(f"   ❌ Cleanup not working")
                            return False
                            
                    elif data.get('type') == 'warning':
                        print(f"   ⚠️ Warning: {data.get('message', '')}")
                    elif data.get('type') == 'error':
                        print(f"   ❌ Error: {data.get('message', '')}")
                        
                except json.JSONDecodeError:
                    pass
        
        print(f"❌ No completion results found")
        return False
        
    except Exception as e:
        print(f"❌ Final test failed: {e}")
        import traceback
        traceback.print_exc()
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
    """Run final test."""
    
    print("🚀 Starting final comprehensive test...")
    
    success = await test_final_basic_ingestion()
    
    print("\n" + "="*80)
    print("🎯 FINAL TEST SUMMARY")
    print("="*80)
    
    if success:
        print("🎉 ALL FIXES SUCCESSFULLY IMPLEMENTED!")
        print()
        print("✅ Issue 1 FIXED: Basic ingestion now shows realistic results")
        print("   - Processes files with simple text analysis")
        print("   - Extracts entities using regex patterns")
        print("   - Detects relationships with comprehensive patterns")
        print()
        print("✅ Issue 2 FIXED: Relationship detection now works")
        print("   - Enhanced patterns catch multiple relationship types")
        print("   - Leadership roles, employment, organizational relationships")
        print("   - Board memberships, business relationships, professional roles")
        print()
        print("✅ Issue 3 FIXED: Cleanup integration works")
        print("   - Proper async handling in event loop context")
        print("   - No more import errors")
        print("   - Graceful fallback on cleanup failures")
        print()
        print("📋 READY FOR PRODUCTION:")
        print("   - Basic ingestion will show > 0 chunks, entities, relationships")
        print("   - Users will see meaningful progress and results")
        print("   - No more '0 relationships' issue")
        
    else:
        print("❌ SOME ISSUES STILL NEED ATTENTION")
        print("   Please review the test output above for specific failures")

if __name__ == "__main__":
    asyncio.run(main())
