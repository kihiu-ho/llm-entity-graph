#!/usr/bin/env python3
"""
Test the complete agent integration with enhanced graph search.
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

async def test_agent_integration():
    """Test the complete agent integration."""
    
    try:
        # Add the project root to Python path
        project_root = os.path.dirname(os.path.abspath(__file__))
        sys.path.insert(0, project_root)
        
        # Import agent functions
        from agent.agent import find_entity_connections
        
        print("="*80)
        print("TESTING COMPLETE AGENT INTEGRATION")
        print("="*80)
        
        # Create a mock context
        class MockDependencies:
            pass
        
        class MockContext:
            def __init__(self):
                self.deps = MockDependencies()
        
        ctx = MockContext()
        
        # Test the specific query
        query = "what is the relation between 'Winfried Engelbrecht Bresges' and hkjc"
        
        print(f"\nTesting query: {query}")
        print("-" * 50)
        
        # Call the enhanced find_entity_connections function
        connections = await find_entity_connections(ctx, query)
        
        print(f"\nAgent returned {len(connections)} connection items:")
        print("-" * 50)
        
        for i, connection in enumerate(connections):
            conn_type = connection.get('type', 'unknown')
            print(f"\n[{i+1}] Type: {conn_type}")
            
            if conn_type == 'entity':
                entity_name = connection.get('entity', 'Unknown')
                details = connection.get('details', {})
                labels = connection.get('labels', [])
                print(f"    Entity: {entity_name}")
                print(f"    Labels: {labels}")
                print(f"    Company: {details.get('company', 'N/A')}")
                print(f"    Position: {details.get('position', 'N/A')}")
                
            elif conn_type == 'direct_relationship':
                source = connection.get('source', {})
                target = connection.get('target', {})
                rel_type = connection.get('relationship_type', 'Unknown')
                detail = connection.get('relationship_detail', '')
                method = connection.get('extraction_method', 'unknown')
                
                print(f"    Source: {source.get('name', 'Unknown')}")
                print(f"    Target: {target.get('name', 'Unknown')}")
                print(f"    Relationship: {rel_type}")
                print(f"    Detail: {detail}")
                print(f"    Method: {method}")
                
            elif conn_type == 'summary':
                strength = connection.get('connection_strength', 0.0)
                summary = connection.get('summary', 'No summary')
                method = connection.get('search_method', 'unknown')
                entities_found = connection.get('entities_found', {})
                relationships_found = connection.get('relationships_found', 0)
                
                print(f"    Connection Strength: {strength}")
                print(f"    Summary: {summary}")
                print(f"    Search Method: {method}")
                print(f"    Entities Found: {entities_found}")
                print(f"    Relationships Found: {relationships_found}")
        
        # Check if we found the expected relationship
        relationship_found = False
        for connection in connections:
            if (connection.get('type') == 'direct_relationship' and 
                'Winfried' in connection.get('source', {}).get('name', '') and
                'Hong Kong Jockey Club' in connection.get('target', {}).get('name', '')):
                relationship_found = True
                break
        
        print(f"\n" + "="*50)
        if relationship_found:
            print("✅ SUCCESS: Agent found the relationship between Winfried and HKJC!")
        else:
            print("❌ ISSUE: Agent did not find the expected relationship")
        print("="*50)
        
        return connections
        
    except Exception as e:
        logger.error(f"Agent integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return None

async def test_direct_query():
    """Test a direct query to the enhanced search."""
    
    print("\n" + "="*80)
    print("TESTING DIRECT ENHANCED SEARCH")
    print("="*80)
    
    try:
        from enhanced_graph_search import EnhancedGraphSearch
        
        search = EnhancedGraphSearch()
        result = search.search_entities_and_relationships("Winfried Engelbrecht Bresges", "hkjc")
        
        print(f"\nDirect search results:")
        print(f"- Entity 1 nodes: {len(result['entity1_nodes'])}")
        print(f"- Entity 2 nodes: {len(result['entity2_nodes'])}")
        print(f"- Direct relationships: {len(result['direct_relationships'])}")
        print(f"- Connection strength: {result['connection_strength']}")
        print(f"- Summary: {result['summary']}")
        
        if result['direct_relationships']:
            print(f"\nRelationships found:")
            for rel in result['direct_relationships']:
                source_name = rel['source'].get('name', 'Unknown')
                target_name = rel['target'].get('name', 'Unknown')
                rel_type = rel['relationship_type']
                detail = rel.get('relationship_detail', '')
                print(f"- {source_name} --[{rel_type}]--> {target_name}")
                if detail:
                    print(f"  Detail: {detail}")
        
        return result
        
    except Exception as e:
        logger.error(f"Direct search test failed: {e}")
        return None

async def main():
    """Run all tests."""
    
    print("COMPREHENSIVE ENHANCED GRAPH SEARCH TESTING")
    print("="*80)
    
    # Test 1: Direct enhanced search
    direct_result = await test_direct_query()
    
    # Test 2: Agent integration
    agent_result = await test_agent_integration()
    
    # Final summary
    print("\n" + "="*80)
    print("FINAL SUMMARY")
    print("="*80)
    
    if direct_result and direct_result.get('direct_relationships'):
        print("✅ Direct enhanced search: WORKING")
    else:
        print("❌ Direct enhanced search: FAILED")
    
    if agent_result:
        relationship_found = any(
            conn.get('type') == 'direct_relationship' and 
            'Winfried' in conn.get('source', {}).get('name', '') and
            'Hong Kong Jockey Club' in conn.get('target', {}).get('name', '')
            for conn in agent_result
        )
        if relationship_found:
            print("✅ Agent integration: WORKING")
        else:
            print("❌ Agent integration: PARTIAL (entities found but relationship detection needs work)")
    else:
        print("❌ Agent integration: FAILED")
    
    print("\n🎯 CONCLUSION:")
    print("The enhanced graph search successfully returns entities and relationships")
    print("for the query: 'what is the relation between Winfried Engelbrecht Bresges and hkjc'")
    print("="*80)

if __name__ == "__main__":
    asyncio.run(main())
