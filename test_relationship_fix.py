#!/usr/bin/env python3
"""
Test the relationship query fix for Winfried and HKJC.
"""

import asyncio
import logging
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_relationship_fix():
    """Test the relationship query fix."""
    
    try:
        # Add project root to path
        project_root = os.path.dirname(os.path.abspath(__file__))
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
        
        # Import the functions
        sys.path.append('web_ui')
        from web_ui.app import generate_natural_language_answer, search_person_to_entity_relationship_sync
        
        print("="*80)
        print("TESTING RELATIONSHIP QUERY FIX")
        print("="*80)
        
        # Test 1: Direct relationship search
        print("\n1. Testing direct relationship search:")
        relationships = search_person_to_entity_relationship_sync("Winfried Engelbrecht Bresges", "HKJC")
        print(f"   Found {len(relationships)} relationships")
        
        for i, rel in enumerate(relationships):
            print(f"   Relationship {i+1}:")
            print(f"     Source: {rel.get('source')}")
            print(f"     Target: {rel.get('target')}")
            print(f"     Type: {rel.get('relationship_type')}")
            print(f"     Detail: {rel.get('relationship_detail')}")
            print(f"     Method: {rel.get('extraction_method')}")
        
        # Test 2: Natural language answer
        print("\n2. Testing natural language answer:")
        queries = [
            "what is the relation between 'Winfried Engelbrecht Bresges' and hkjc",
            "what is the relationship between Winfried and Hong Kong Jockey Club",
            "how is Winfried Engelbrecht Bresges connected to HKJC"
        ]
        
        for query in queries:
            print(f"\n   Query: {query}")
            answer = generate_natural_language_answer(query)
            print(f"   Answer: {answer}")
            
            # Check if answer contains key information
            answer_lower = answer.lower()
            
            print(f"   Analysis:")
            print(f"     Contains 'CEO': {'✅' if 'ceo' in answer_lower else '❌'}")
            print(f"     Contains 'Chairman': {'✅' if 'chairman' in answer_lower else '❌'}")
            print(f"     Contains relationship info: {'✅' if any(word in answer_lower for word in ['ceo', 'chairman', 'director', 'executive']) else '❌'}")
            print(f"     Not generic: {'✅' if 'could not find any direct relationships' not in answer_lower else '❌'}")
        
        # Test 3: Reverse direction
        print("\n3. Testing reverse direction:")
        relationships_reverse = search_person_to_entity_relationship_sync("HKJC", "Winfried Engelbrecht Bresges")
        print(f"   Found {len(relationships_reverse)} relationships (reverse)")
        
        # Test 4: Variations
        print("\n4. Testing entity variations:")
        test_cases = [
            ("Winfried", "Hong Kong Jockey Club"),
            ("WINFRIED Engelbrecht Bresges", "hkjc"),
            ("winfried engelbrecht bresges", "Hong Kong Jockey Club")
        ]
        
        for entity1, entity2 in test_cases:
            rels = search_person_to_entity_relationship_sync(entity1, entity2)
            print(f"   '{entity1}' + '{entity2}': {len(rels)} relationships")
        
        print(f"\n✅ Relationship query test completed!")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_relationship_fix())
