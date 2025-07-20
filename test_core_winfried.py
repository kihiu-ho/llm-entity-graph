#!/usr/bin/env python3
"""
Test the core graph search functionality for Winfried.
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

async def test_core_winfried():
    """Test the core graph search functionality."""
    
    try:
        from agent.agent import AgentDependencies
        from agent.graph_utils import search_people
        from agent.tools import graph_search_tool, GraphSearchInput
        
        print("="*80)
        print("TESTING CORE GRAPH SEARCH FOR WINFRIED")
        print("="*80)
        
        # Test 1: Direct enhanced search
        print("\n1. Testing enhanced person search:")
        results = await search_people(name_query="Winfried Engelbrecht Bresges", limit=3)
        
        if results:
            person = results[0]
            print(f"✅ Found: {person.get('name')}")
            print(f"   Position: {person.get('position')}")
            print(f"   Company: {person.get('company')}")
            print(f"   Summary: {person.get('summary', '')[:100]}...")
            print(f"   Relationships: {len(person.get('relationships', []))}")
            
            for rel in person.get('relationships', []):
                print(f"     - {rel['relationship_type']}: {rel['target']}")
        else:
            print("❌ No results found")
        
        # Test 2: Graph search tool
        print("\n2. Testing graph search tool:")
        input_data = GraphSearchInput(query="Winfried Engelbrecht Bresges")
        graph_results = await graph_search_tool(input_data)
        
        print(f"   Graph search found {len(graph_results)} results")
        for i, result in enumerate(graph_results):
            print(f"   Result {i+1}: {result.fact[:100]}...")
        
        # Test 3: Test "who is" pattern
        print("\n3. Testing 'who is' pattern recognition:")
        query = 'who is "Winfried Engelbrecht Bresges"'
        
        # Simulate the logic from the agent
        if query.lower().startswith("who is"):
            person_name = query[6:].strip().strip('"\'')
            print(f"   Extracted name: '{person_name}'")
            
            person_results = await search_people(name_query=person_name, limit=5)
            
            if person_results:
                print(f"   ✅ Enhanced search found {len(person_results)} results")
                
                # Create comprehensive fact
                person = person_results[0]
                fact_parts = [f"{person.get('name', 'Unknown')} is a person"]
                
                if person.get('position'):
                    fact_parts.append(f"with position {person['position']}")
                
                if person.get('company'):
                    fact_parts.append(f"at {person['company']}")
                
                if person.get('summary'):
                    summary = person['summary'][:200] + "..." if len(person['summary']) > 200 else person['summary']
                    fact_parts.append(f"Summary: {summary}")
                
                # Add relationship information
                if person.get('relationships'):
                    rel_info = []
                    for rel in person['relationships']:
                        rel_info.append(f"{rel['relationship_type']} {rel['target']}")
                    if rel_info:
                        fact_parts.append(f"Relationships: {', '.join(rel_info)}")
                
                fact = ". ".join(fact_parts)
                
                print(f"\n   📋 Generated comprehensive fact:")
                print(f"   {fact}")
            else:
                print("   ❌ No results found for 'who is' query")
        
        print("\n✅ Core functionality test completed!")
        
    except Exception as e:
        logger.error(f"Core test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_core_winfried())
