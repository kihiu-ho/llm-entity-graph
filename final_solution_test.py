#!/usr/bin/env python3
"""
Final comprehensive test demonstrating the complete working solution.
This shows that the enhanced graph search successfully returns entities and relationships
for the query: "what is the relation between 'Winfried Engelbrecht Bresges' and hkjc"
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

def test_enhanced_search_direct():
    """Test the enhanced search directly."""
    
    print("="*80)
    print("FINAL SOLUTION TEST: ENHANCED GRAPH SEARCH")
    print("="*80)
    
    try:
        from enhanced_graph_search import EnhancedGraphSearch
        
        # Initialize enhanced search
        search = EnhancedGraphSearch()
        
        # Test the specific query
        query_entity1 = "Winfried Engelbrecht Bresges"
        query_entity2 = "hkjc"
        
        print(f"\n🔍 QUERY: What is the relation between '{query_entity1}' and '{query_entity2}'?")
        print("-" * 60)
        
        # Search for relationships
        result = search.search_entities_and_relationships(query_entity1, query_entity2)
        
        print(f"\n📊 SEARCH RESULTS:")
        print(f"   Entity 1 ({result['entity1']}) nodes found: {len(result['entity1_nodes'])}")
        print(f"   Entity 2 ({result['entity2']}) nodes found: {len(result['entity2_nodes'])}")
        print(f"   Direct relationships found: {len(result['direct_relationships'])}")
        print(f"   Connection strength: {result['connection_strength']}")
        
        # Display entities found
        print(f"\n👤 ENTITIES FOUND:")
        
        for i, node in enumerate(result['entity1_nodes']):
            print(f"   [{i+1}] {node.get('name', 'Unknown')} ({', '.join(node.get('labels', []))})")
            if node.get('company'):
                print(f"       Company: {node['company']}")
            if node.get('position'):
                print(f"       Position: {node['position']}")
        
        for i, node in enumerate(result['entity2_nodes'][:3]):  # Show first 3
            print(f"   [{i+1}] {node.get('name', 'Unknown')} ({', '.join(node.get('labels', []))})")
        
        # Display relationships
        print(f"\n🔗 RELATIONSHIPS FOUND:")
        
        if result['direct_relationships']:
            for i, rel in enumerate(result['direct_relationships']):
                source_name = rel['source'].get('name', 'Unknown')
                target_name = rel['target'].get('name', 'Unknown')
                rel_type = rel['relationship_type']
                detail = rel.get('relationship_detail', '')
                method = rel.get('extraction_method', 'unknown')
                
                print(f"   [{i+1}] {source_name}")
                print(f"       --[{rel_type}]-->")
                print(f"       {target_name}")
                if detail:
                    print(f"       Detail: {detail}")
                print(f"       Extraction Method: {method}")
                print()
        else:
            print("   No direct relationships found")
        
        # Summary
        print(f"📋 SUMMARY: {result['summary']}")
        
        return result
        
    except Exception as e:
        logger.error(f"Enhanced search test failed: {e}")
        import traceback
        traceback.print_exc()
        return None

async def test_agent_integration():
    """Test the agent integration."""
    
    print(f"\n" + "="*80)
    print("AGENT INTEGRATION TEST")
    print("="*80)
    
    try:
        # Add the project root to Python path
        project_root = os.path.dirname(os.path.abspath(__file__))
        sys.path.insert(0, project_root)
        
        # Import agent functions
        from agent.agent import find_entity_connections
        
        # Create a mock context
        class MockDependencies:
            pass
        
        class MockContext:
            def __init__(self):
                self.deps = MockDependencies()
        
        ctx = MockContext()
        
        # Test the specific query
        query = "what is the relation between 'Winfried Engelbrecht Bresges' and hkjc"
        
        print(f"\n🔍 AGENT QUERY: {query}")
        print("-" * 60)
        
        # Call the enhanced find_entity_connections function
        connections = await find_entity_connections(ctx, query)
        
        print(f"\n📊 AGENT RESULTS:")
        print(f"   Connection items returned: {len(connections)}")
        
        # Parse and display results
        relationships_found = 0
        entities_found = 0
        
        for i, connection in enumerate(connections):
            if isinstance(connection, dict):
                # This is the enhanced relationship format
                source_entity = connection.get('source_entity', 'Unknown')
                target_entity = connection.get('target_entity', 'Unknown')
                relationship_type = connection.get('relationship_type', 'Unknown')
                relationship_description = connection.get('relationship_description', '')
                confidence_score = connection.get('confidence_score', 0.0)
                extraction_method = connection.get('extraction_method', 'unknown')
                
                print(f"\n   [{i+1}] RELATIONSHIP:")
                print(f"       Source: {source_entity}")
                print(f"       Target: {target_entity}")
                print(f"       Type: {relationship_type}")
                print(f"       Description: {relationship_description}")
                print(f"       Confidence: {confidence_score}")
                print(f"       Method: {extraction_method}")
                
                relationships_found += 1
        
        print(f"\n📋 AGENT SUMMARY:")
        print(f"   Relationships found: {relationships_found}")
        print(f"   Total items returned: {len(connections)}")
        
        return connections, relationships_found > 0
        
    except Exception as e:
        logger.error(f"Agent integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return None, False

def main():
    """Run the complete test suite."""
    
    print("FINAL SOLUTION DEMONSTRATION")
    print("Query: 'what is the relation between Winfried Engelbrecht Bresges and hkjc'")
    print("="*80)
    
    # Test 1: Direct enhanced search
    print("\n🧪 TEST 1: Direct Enhanced Search")
    direct_result = test_enhanced_search_direct()
    
    # Test 2: Agent integration
    print("\n🧪 TEST 2: Agent Integration")
    agent_result, agent_success = asyncio.run(test_agent_integration())
    
    # Final evaluation
    print(f"\n" + "="*80)
    print("FINAL EVALUATION")
    print("="*80)
    
    direct_success = (direct_result and 
                     len(direct_result.get('direct_relationships', [])) > 0)
    
    print(f"\n✅ RESULTS:")
    print(f"   Direct Enhanced Search: {'✅ SUCCESS' if direct_success else '❌ FAILED'}")
    print(f"   Agent Integration: {'✅ SUCCESS' if agent_success else '❌ FAILED'}")
    
    if direct_success:
        rel = direct_result['direct_relationships'][0]
        print(f"\n🎯 RELATIONSHIP FOUND:")
        print(f"   {rel['source']['name']} --[{rel['relationship_type']}]--> {rel['target']['name']}")
        print(f"   Detail: {rel.get('relationship_detail', 'N/A')}")
    
    print(f"\n🏆 CONCLUSION:")
    if direct_success and agent_success:
        print("   ✅ COMPLETE SUCCESS: Enhanced graph search returns entities and relationships!")
    elif direct_success:
        print("   ⚠️  PARTIAL SUCCESS: Enhanced search works, agent integration needs refinement")
    else:
        print("   ❌ NEEDS WORK: Core functionality requires debugging")
    
    print("="*80)

if __name__ == "__main__":
    main()
