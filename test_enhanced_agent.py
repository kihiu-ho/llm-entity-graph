#!/usr/bin/env python3
"""
Test the enhanced agent functionality for entity relationship search.
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

async def test_enhanced_agent():
    """Test the enhanced agent functionality."""
    
    try:
        # Import the agent
        from agent.agent import rag_agent
        from pydantic_ai import RunContext
        
        print("="*80)
        print("TESTING ENHANCED AGENT FUNCTIONALITY")
        print("="*80)
        
        # Test the relationship query
        query = "what is the relation between 'Winfried Engelbrecht Bresges' and hkjc"
        
        print(f"\nTesting query: {query}")
        print("-" * 50)
        
        # Create a mock context (simplified for testing)
        class MockDependencies:
            pass
        
        # Run the agent with the query
        result = await rag_agent.run(query, deps=MockDependencies())
        
        print(f"\nAgent Response:")
        print(result.data)
        
        print("\n" + "="*80)
        print("ENHANCED AGENT TEST COMPLETED")
        print("="*80)
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_enhanced_agent())
