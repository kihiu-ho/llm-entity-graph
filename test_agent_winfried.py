#!/usr/bin/env python3
"""
Test the agent's response to Winfried query.
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

async def test_agent_winfried():
    """Test the agent's response to Winfried query."""
    
    try:
        from agent.api import create_agent_session, query_agent
        
        print("="*80)
        print("TESTING AGENT RESPONSE TO WINFRIED QUERY")
        print("="*80)
        
        # Create agent session
        session_id = await create_agent_session()
        print(f"Created session: {session_id}")
        
        # Test the query
        query = 'who is "Winfried Engelbrecht Bresges"'
        print(f"\nQuery: {query}")
        
        response = await query_agent(session_id, query)
        
        print(f"\nAgent Response:")
        print(f"Response: {response.get('response', 'No response')}")
        print(f"Search Results: {len(response.get('search_results', []))}")
        
        # Print search results
        for i, result in enumerate(response.get('search_results', [])):
            print(f"\nSearch Result {i+1}:")
            print(f"  Method: {result.get('search_method', 'Unknown')}")
            print(f"  Fact: {result.get('fact', 'No fact')[:200]}...")
        
        print("\n✅ Agent test completed!")
        
    except Exception as e:
        logger.error(f"Agent test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_agent_winfried())
