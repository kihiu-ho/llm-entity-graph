#!/usr/bin/env python3
"""
Test the enhanced search for Winfried Engelbrecht Bresges.
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

async def test_winfried_search():
    """Test the enhanced search for Winfried."""
    
    try:
        # Import the enhanced search function
        from agent.graph_utils import search_people
        
        print("="*80)
        print("TESTING ENHANCED SEARCH FOR WINFRIED ENGELBRECHT BRESGES")
        print("="*80)
        
        # Test 1: Search with exact name (case-sensitive issue)
        print("\n1. Testing exact name search:")
        results = await search_people(name_query="Winfried Engelbrecht Bresges", limit=5)
        print(f"   Found {len(results)} results for 'Winfried Engelbrecht Bresges'")
        
        for i, result in enumerate(results):
            print(f"   Result {i+1}:")
            print(f"     Name: {result.get('name')}")
            print(f"     Company: {result.get('company')}")
            print(f"     Position: {result.get('position')}")
            print(f"     Search Method: {result.get('search_method')}")
            print(f"     Relationships: {len(result.get('relationships', []))}")
            
            # Print relationships
            for rel in result.get('relationships', []):
                print(f"       - {rel['relationship_type']}: {rel['target']} ({rel['extraction_method']})")
        
        # Test 2: Search with partial name
        print("\n2. Testing partial name search:")
        results = await search_people(name_query="Winfried", limit=5)
        print(f"   Found {len(results)} results for 'Winfried'")
        
        for i, result in enumerate(results):
            print(f"   Result {i+1}:")
            print(f"     Name: {result.get('name')}")
            print(f"     Company: {result.get('company')}")
            print(f"     Position: {result.get('position')}")
            print(f"     Summary: {result.get('summary', '')[:100]}...")
        
        # Test 3: Search with case variations
        print("\n3. Testing case variations:")
        test_names = ["WINFRIED", "winfried", "Winfried Bresges", "Engelbrecht"]
        
        for name in test_names:
            results = await search_people(name_query=name, limit=3)
            print(f"   '{name}': {len(results)} results")
        
        # Test 4: Test the agent's graph search
        print("\n4. Testing agent's graph search:")
        from agent.agent import rag_agent
        from agent.agent import AgentDependencies
        
        # Create dependencies
        deps = AgentDependencies(session_id="test_session")
        
        # Test "who is" query
        query = 'who is "Winfried Engelbrecht Bresges"'
        print(f"   Query: {query}")
        
        # This would normally be called through the agent, but let's test the function directly
        from agent.agent import graph_search
        from pydantic_ai import RunContext
        
        ctx = RunContext(deps=deps)
        results = await graph_search(ctx, query)
        
        print(f"   Agent search found {len(results)} results")
        for i, result in enumerate(results):
            print(f"   Result {i+1}:")
            print(f"     Fact: {result.get('fact', '')[:200]}...")
            print(f"     Search Method: {result.get('search_method')}")
        
        print("\n✅ Test completed!")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_winfried_search())
