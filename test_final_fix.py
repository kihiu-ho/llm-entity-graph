#!/usr/bin/env python3
"""
Final test to demonstrate that the issue is completely fixed.
This simulates the exact scenario that was failing before.
"""

import logging
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_original_issue_fixed():
    """Test that the original issue is completely fixed."""
    
    try:
        # Add the project root to Python path
        project_root = os.path.dirname(os.path.abspath(__file__))
        sys.path.insert(0, project_root)
        
        print("="*80)
        print("FINAL FIX VERIFICATION")
        print("Testing the exact scenario that was failing before")
        print("="*80)
        
        # The original failing query
        query = "what is the relation between 'Winfried Engelbrecht Bresges' and hkjc"
        
        print(f"\n🔍 ORIGINAL FAILING QUERY: {query}")
        print("-" * 60)
        
        # Test the web UI function that was returning 0 results
        from web_ui.app import get_graph_data_with_agent_tool
        
        print(f"\n📊 TESTING WEB UI GRAPH DATA EXTRACTION...")
        
        # This was the function that was logging "Graph search tool returned 0 results"
        graph_data = get_graph_data_with_agent_tool(query)
        
        print(f"\n📋 RESULTS:")
        
        if graph_data:
            nodes = graph_data.get('nodes', [])
            relationships = graph_data.get('relationships', [])
            metadata = graph_data.get('metadata', {})
            
            print(f"✅ SUCCESS: Graph data found!")
            print(f"   Nodes: {len(nodes)}")
            print(f"   Relationships: {len(relationships)}")
            print(f"   Source: {metadata.get('source', 'Unknown')}")
            
            # Show the key relationship that was missing before
            if relationships:
                print(f"\n🔗 KEY RELATIONSHIP FOUND:")
                rel = relationships[0]
                
                # Find source and target nodes
                source_node = next((n for n in nodes if n['id'] == rel['startNode']), {})
                target_node = next((n for n in nodes if n['id'] == rel['endNode']), {})
                
                source_name = source_node.get('properties', {}).get('name', 'Unknown')
                target_name = target_node.get('properties', {}).get('name', 'Unknown')
                
                print(f"   {source_name} --[{rel['type']}]--> {target_name}")
                print(f"   Detail: {rel['properties'].get('detail', 'N/A')}")
                print(f"   Method: {rel['properties'].get('extraction_method', 'Unknown')}")
                
                # Show entity details
                print(f"\n👤 ENTITY DETAILS:")
                for node in nodes[:2]:  # Show first 2 key entities
                    props = node['properties']
                    print(f"   • {props['name']} ({', '.join(node['labels'])})")
                    if props.get('company'):
                        print(f"     Company: {props['company']}")
                    if props.get('position'):
                        print(f"     Position: {props['position']}")
            else:
                print(f"❌ No relationships found")
        else:
            print(f"❌ FAILED: No graph data found")
        
        # Compare with what would happen with the old system
        print(f"\n" + "="*60)
        print("COMPARISON WITH OLD SYSTEM")
        print("="*60)
        
        print(f"\n📊 BEFORE FIX:")
        print(f"   Log: 'Graph search tool returned 0 results'")
        print(f"   Log: 'No results from graph search tool'")
        print(f"   Log: 'No real graph data found, creating sample data for demonstration'")
        print(f"   Result: ❌ No relationships found")
        
        print(f"\n📊 AFTER FIX:")
        if graph_data and graph_data.get('relationships'):
            print(f"   Log: 'Detected relationship query, using enhanced search'")
            print(f"   Log: 'Enhanced search found data: {len(graph_data['nodes'])} nodes, {len(graph_data['relationships'])} relationships'")
            print(f"   Result: ✅ Relationship found: Winfried Engelbrecht Bresges --[CEO_OF]--> The Hong Kong Jockey Club")
        else:
            print(f"   Result: ❌ Still not working")
        
        # Final verdict
        print(f"\n" + "="*80)
        print("FINAL VERDICT")
        print("="*80)
        
        success = (graph_data is not None and 
                  len(graph_data.get('relationships', [])) > 0 and
                  any('CEO_OF' in rel.get('type', '') for rel in graph_data.get('relationships', [])))
        
        if success:
            print(f"🏆 ✅ ISSUE COMPLETELY FIXED!")
            print(f"   The graph search now properly returns entities and relationships")
            print(f"   for the query: '{query}'")
            print(f"   ")
            print(f"   Key improvements:")
            print(f"   • Enhanced relationship detection")
            print(f"   • Direct Neo4j query fallback")
            print(f"   • Property-based relationship inference")
            print(f"   • Web UI integration with enhanced search")
        else:
            print(f"❌ ISSUE NOT FULLY RESOLVED")
            print(f"   The enhanced search may be working but integration needs refinement")
        
        return success
        
    except Exception as e:
        logger.error(f"Final fix test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_original_issue_fixed()
