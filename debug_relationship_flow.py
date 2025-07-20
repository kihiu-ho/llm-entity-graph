#!/usr/bin/env python3
"""
Debug the complete relationship data flow from enhanced search to frontend.
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

def debug_relationship_flow():
    """Debug the complete relationship data flow."""
    
    try:
        # Add the project root to Python path
        project_root = os.path.dirname(os.path.abspath(__file__))
        sys.path.insert(0, project_root)
        
        print("="*80)
        print("DEBUGGING COMPLETE RELATIONSHIP DATA FLOW")
        print("="*80)
        
        query = "what is the relation between 'Winfried Engelbrecht Bresges' and hkjc"
        
        print(f"\n🔍 Testing query: {query}")
        print("-" * 60)
        
        # Step 1: Test enhanced search directly
        print(f"\n1. ENHANCED SEARCH DIRECT TEST:")
        from enhanced_graph_search import EnhancedGraphSearch
        
        search = EnhancedGraphSearch()
        result = search.search_entities_and_relationships("Winfried Engelbrecht Bresges", "hkjc")
        
        print(f"   Entity1 nodes: {len(result.get('entity1_nodes', []))}")
        print(f"   Entity2 nodes: {len(result.get('entity2_nodes', []))}")
        print(f"   Direct relationships: {len(result.get('direct_relationships', []))}")
        
        if result.get('direct_relationships'):
            for i, rel in enumerate(result['direct_relationships']):
                print(f"   [{i+1}] {rel['source']['name']} --[{rel['relationship_type']}]--> {rel['target']['name']}")
        
        # Step 2: Test web UI enhanced relationship data
        print(f"\n2. WEB UI ENHANCED RELATIONSHIP DATA TEST:")
        from web_ui.app import get_enhanced_relationship_data
        
        web_ui_result = get_enhanced_relationship_data(query)
        
        if web_ui_result:
            print(f"   Nodes: {len(web_ui_result.get('nodes', []))}")
            print(f"   Relationships: {len(web_ui_result.get('relationships', []))}")
            
            # Show relationships in detail
            for i, rel in enumerate(web_ui_result.get('relationships', [])):
                print(f"   [{i+1}] Relationship:")
                print(f"       ID: {rel.get('id')}")
                print(f"       Type: {rel.get('type')}")
                print(f"       StartNode: {rel.get('startNode')}")
                print(f"       EndNode: {rel.get('endNode')}")
                
                # Find the actual node names
                start_name = "Unknown"
                end_name = "Unknown"
                for node in web_ui_result.get('nodes', []):
                    if node.get('id') == rel.get('startNode'):
                        start_name = node.get('properties', {}).get('name', 'Unknown')
                    if node.get('id') == rel.get('endNode'):
                        end_name = node.get('properties', {}).get('name', 'Unknown')
                
                print(f"       Actual: {start_name} --[{rel.get('type')}]--> {end_name}")
        else:
            print(f"   ❌ No web UI result")
        
        # Step 3: Test full web UI graph data function
        print(f"\n3. FULL WEB UI GRAPH DATA TEST:")
        from web_ui.app import get_graph_data_with_agent_tool
        
        full_result = get_graph_data_with_agent_tool(query)
        
        if full_result:
            print(f"   Nodes: {len(full_result.get('nodes', []))}")
            print(f"   Relationships: {len(full_result.get('relationships', []))}")
            
            # Show relationships in detail
            for i, rel in enumerate(full_result.get('relationships', [])):
                print(f"   [{i+1}] Relationship:")
                print(f"       ID: {rel.get('id')}")
                print(f"       Type: {rel.get('type')}")
                print(f"       StartNode: {rel.get('startNode')}")
                print(f"       EndNode: {rel.get('endNode')}")
                
                # Find the actual node names
                start_name = "Unknown"
                end_name = "Unknown"
                for node in full_result.get('nodes', []):
                    if node.get('id') == rel.get('startNode'):
                        start_name = node.get('properties', {}).get('name', 'Unknown')
                    if node.get('id') == rel.get('endNode'):
                        end_name = node.get('properties', {}).get('name', 'Unknown')
                
                print(f"       Actual: {start_name} --[{rel.get('type')}]--> {end_name}")
        else:
            print(f"   ❌ No full result")
        
        # Step 4: Test complete web UI process
        print(f"\n4. COMPLETE WEB UI PROCESS TEST:")
        from web_ui.app import process_message_with_agent, _is_graph_query_direct
        
        is_graph_query = _is_graph_query_direct(query)
        response = process_message_with_agent(query, is_graph_query)
        
        if 'graph_data' in response:
            graph_data = response['graph_data']
            print(f"   Final nodes: {len(graph_data.get('nodes', []))}")
            print(f"   Final relationships: {len(graph_data.get('relationships', []))}")
            
            # Show final relationships
            for i, rel in enumerate(graph_data.get('relationships', [])):
                print(f"   [{i+1}] Final Relationship:")
                print(f"       ID: {rel.get('id')}")
                print(f"       Type: {rel.get('type')}")
                print(f"       StartNode: {rel.get('startNode')}")
                print(f"       EndNode: {rel.get('endNode')}")
                
                # Find the actual node names
                start_name = "Unknown"
                end_name = "Unknown"
                for node in graph_data.get('nodes', []):
                    if node.get('id') == rel.get('startNode'):
                        start_name = node.get('properties', {}).get('name', 'Unknown')
                    if node.get('id') == rel.get('endNode'):
                        end_name = node.get('properties', {}).get('name', 'Unknown')
                
                print(f"       Final: {start_name} --[{rel.get('type')}]--> {end_name}")
        else:
            print(f"   ❌ No graph data in final response")
        
        # Analysis
        print(f"\n" + "="*80)
        print("ANALYSIS")
        print("="*80)
        
        enhanced_has_rels = len(result.get('direct_relationships', [])) > 0
        web_ui_has_rels = web_ui_result and len(web_ui_result.get('relationships', [])) > 0
        full_has_rels = full_result and len(full_result.get('relationships', [])) > 0
        final_has_rels = 'graph_data' in response and len(response['graph_data'].get('relationships', [])) > 0
        
        print(f"Enhanced search has relationships: {enhanced_has_rels}")
        print(f"Web UI enhanced data has relationships: {web_ui_has_rels}")
        print(f"Full graph data has relationships: {full_has_rels}")
        print(f"Final response has relationships: {final_has_rels}")
        
        if enhanced_has_rels and not final_has_rels:
            print(f"\n🔍 ISSUE IDENTIFIED:")
            print(f"   Enhanced search finds relationships but they're lost in the pipeline")
            print(f"   Need to check the data conversion logic")
        elif final_has_rels:
            print(f"\n✅ SUCCESS:")
            print(f"   Relationships are properly flowing through the pipeline")
        else:
            print(f"\n❌ PROBLEM:")
            print(f"   No relationships found at any stage")
        
        return enhanced_has_rels, web_ui_has_rels, full_has_rels, final_has_rels
        
    except Exception as e:
        logger.error(f"Debug failed: {e}")
        import traceback
        traceback.print_exc()
        return False, False, False, False

if __name__ == "__main__":
    debug_relationship_flow()
