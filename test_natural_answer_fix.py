#!/usr/bin/env python3
"""
Test the natural language answer fix for Winfried.
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

async def test_natural_answer():
    """Test the natural language answer generation."""
    
    try:
        # Add project root to path
        project_root = os.path.dirname(os.path.abspath(__file__))
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
        
        # Import the function
        sys.path.append('web_ui')
        from web_ui.app import generate_natural_language_answer
        
        print("="*80)
        print("TESTING NATURAL LANGUAGE ANSWER FIX")
        print("="*80)
        
        # Test the query
        query = 'who is "Winfried Engelbrecht Bresges"'
        print(f"\nQuery: {query}")
        
        # Generate the answer
        answer = generate_natural_language_answer(query)
        
        print(f"\nGenerated Answer:")
        print(f"{answer}")
        
        # Check if the answer contains key information
        answer_lower = answer.lower()
        
        print(f"\n🔍 Analysis:")
        print(f"   Contains 'CEO': {'✅' if 'ceo' in answer_lower else '❌'}")
        print(f"   Contains 'HKJC': {'✅' if 'hkjc' in answer_lower or 'hong kong jockey' in answer_lower else '❌'}")
        print(f"   Contains 'Chairman': {'✅' if 'chairman' in answer_lower or 'chair' in answer_lower else '❌'}")
        print(f"   Contains 'IFHA': {'✅' if 'ifha' in answer_lower or 'international federation' in answer_lower else '❌'}")
        print(f"   Generic response: {'❌' if 'search the knowledge graph' in answer_lower else '✅'}")
        
        # Test case variations
        print(f"\n🔤 Testing case variations:")
        test_queries = [
            "who is winfried engelbrecht bresges",
            "Who is WINFRIED ENGELBRECHT BRESGES",
            "who is Winfried"
        ]
        
        for test_query in test_queries:
            test_answer = generate_natural_language_answer(test_query)
            contains_info = 'ceo' in test_answer.lower() or 'chairman' in test_answer.lower()
            print(f"   '{test_query}': {'✅' if contains_info else '❌'}")
        
        print(f"\n✅ Natural language answer test completed!")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_natural_answer())
