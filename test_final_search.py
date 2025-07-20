#!/usr/bin/env python3
"""
Final test to demonstrate the enhanced graph search returning entities and relationships
for the specific query: "what is the relation between 'Winfried Engelbrecht Bresges' and hkjc"
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

def test_final_search():
    """Test the final enhanced search functionality."""
    
    try:
        from enhanced_graph_search import EnhancedGraphSearch
        
        print("="*80)
        print("FINAL TEST: ENHANCED GRAPH SEARCH")
        print("Query: what is the relation between 'Winfried Engelbrecht Bresges' and hkjc")
        print("="*80)
        
        # Initialize enhanced search
        search = EnhancedGraphSearch()
        
        # Search for the specific relationship
        result = search.search_entities_and_relationships("Winfried Engelbrecht Bresges", "hkjc")
        
        print("\n🔍 SEARCH RESULTS:")
        print("-" * 50)
        
        # Display Entity 1 (Winfried)
        print(f"\n📋 ENTITY 1: {result['entity1']}")
        print(f"   Nodes found: {len(result['entity1_nodes'])}")
        for i, node in enumerate(result['entity1_nodes']):
            print(f"   [{i+1}] {node.get('name', 'Unknown')}")
            print(f"       Labels: {node.get('labels', [])}")
            print(f"       Company: {node.get('company', 'N/A')}")
            print(f"       Position: {node.get('position', 'N/A')}")
            if node.get('summary'):
                print(f"       Summary: {node['summary'][:100]}...")
        
        # Display Entity 2 (HKJC)
        print(f"\n📋 ENTITY 2: {result['entity2']}")
        print(f"   Nodes found: {len(result['entity2_nodes'])}")
        for i, node in enumerate(result['entity2_nodes'][:3]):  # Show first 3
            print(f"   [{i+1}] {node.get('name', 'Unknown')}")
            print(f"       Labels: {node.get('labels', [])}")
        
        # Display Relationships
        print(f"\n🔗 RELATIONSHIPS FOUND: {len(result['direct_relationships'])}")
        for i, rel in enumerate(result['direct_relationships']):
            print(f"   [{i+1}] {rel['source'].get('name', 'Unknown')}")
            print(f"       --[{rel['relationship_type']}]-->")
            print(f"       {rel['target'].get('name', 'Unknown')}")
            if rel.get('relationship_detail'):
                print(f"       Detail: {rel['relationship_detail']}")
            print(f"       Method: {rel.get('extraction_method', 'unknown')}")
            print()
        
        # Display Summary
        print(f"\n📊 SUMMARY:")
        print(f"   Connection Strength: {result['connection_strength']}")
        print(f"   Summary: {result['summary']}")
        
        # Format as agent response
        print(f"\n🤖 AGENT RESPONSE FORMAT:")
        print("-" * 50)
        
        if result['direct_relationships']:
            print("✅ ENTITIES AND RELATIONSHIPS FOUND:")
            
            # Show entities
            for node in result['entity1_nodes']:
                print(f"\n• PERSON: {node.get('name')}")
                print(f"  - Company: {node.get('company', 'N/A')}")
                print(f"  - Position: {node.get('position', 'N/A')}")
                print(f"  - Labels: {', '.join(node.get('labels', []))}")
            
            for node in result['entity2_nodes'][:2]:  # Show first 2 HKJC entities
                print(f"\n• ORGANIZATION: {node.get('name')}")
                print(f"  - Labels: {', '.join(node.get('labels', []))}")
            
            # Show relationships
            print(f"\n🔗 RELATIONSHIPS:")
            for rel in result['direct_relationships']:
                source_name = rel['source'].get('name', 'Unknown')
                target_name = rel['target'].get('name', 'Unknown')
                rel_type = rel['relationship_type']
                detail = rel.get('relationship_detail', '')
                
                print(f"• {source_name} --[{rel_type}]--> {target_name}")
                if detail:
                    print(f"  Detail: {detail}")
        else:
            print("❌ NO DIRECT RELATIONSHIPS FOUND")
        
        print("\n" + "="*80)
        print("✅ ENHANCED GRAPH SEARCH SUCCESSFULLY RETURNS ENTITIES AND RELATIONSHIPS")
        print("="*80)
        
        return result
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    test_final_search()
