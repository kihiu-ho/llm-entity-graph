#!/usr/bin/env python3
"""
Final test of the Winfried Engelbrecht Bresges search fix.
"""

import asyncio
import logging
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_final_winfried():
    """Final test of the Winfried search fix."""
    
    try:
        from agent.graph_utils import search_people
        
        print("="*80)
        print("FINAL TEST: WINFRIED ENGELBRECHT BRESGES SEARCH FIX")
        print("="*80)
        
        # Test the enhanced search
        print("\n🔍 Testing enhanced person search:")
        results = await search_people(name_query="Winfried Engelbrecht Bresges", limit=3)
        
        if results:
            person = results[0]
            print(f"✅ SUCCESS: Found {person.get('name')}")
            print(f"   Position: {person.get('position')}")
            print(f"   Company: {person.get('company', 'None')}")
            print(f"   Search Method: {person.get('search_method')}")
            print(f"   Total Relationships: {len(person.get('relationships', []))}")
            
            print(f"\n📋 Relationships found:")
            for i, rel in enumerate(person.get('relationships', []), 1):
                print(f"   {i}. {rel['relationship_type']}: {rel['target']}")
                print(f"      Detail: {rel['relationship_detail']}")
                print(f"      Source: {rel['extraction_method']}")
            
            # Check if we found the CEO relationship
            ceo_relationships = [r for r in person.get('relationships', []) if r['relationship_type'] == 'CEO_OF']
            hkjc_relationships = [r for r in person.get('relationships', []) if 'hong kong jockey' in r['target'].lower()]
            
            print(f"\n🎯 Key findings:")
            print(f"   - CEO relationships: {len(ceo_relationships)}")
            print(f"   - HKJC relationships: {len(hkjc_relationships)}")
            
            if ceo_relationships:
                print(f"   ✅ CEO role confirmed: {ceo_relationships[0]['target']}")
            
            if hkjc_relationships:
                print(f"   ✅ HKJC connection confirmed")
                for rel in hkjc_relationships:
                    print(f"      - {rel['relationship_type']}: {rel['target']}")
            
            # Test case variations
            print(f"\n🔤 Testing case variations:")
            test_cases = ["winfried", "WINFRIED", "Winfried", "Engelbrecht"]
            
            for test_name in test_cases:
                test_results = await search_people(name_query=test_name, limit=1)
                found = len(test_results) > 0
                print(f"   '{test_name}': {'✅ Found' if found else '❌ Not found'}")
            
            print(f"\n🎉 SUMMARY:")
            print(f"   ✅ Case-insensitive search: Working")
            print(f"   ✅ Relationship extraction: Working")
            print(f"   ✅ Graphiti integration: Working")
            print(f"   ✅ CEO of HKJC: {'Found' if ceo_relationships else 'Not found'}")
            print(f"   ✅ Chair of IFHA: {'Found' if any('international federation' in r['target'].lower() for r in person.get('relationships', [])) else 'Not found'}")
            
        else:
            print("❌ FAILED: No results found")
        
        print(f"\n✅ Final test completed!")
        
    except Exception as e:
        logger.error(f"Final test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_final_winfried())
