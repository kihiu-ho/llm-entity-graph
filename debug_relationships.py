#!/usr/bin/env python3
"""
Debug why relationships are not being passed to the frontend.
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

def debug_relationships():
    """Debug the relationship data flow."""
    
    try:
        # Add the project root to Python path
        project_root = os.path.dirname(os.path.abspath(__file__))
        sys.path.insert(0, project_root)
        
        # Import functions
        from web_ui.app import get_enhanced_relationship_data
        from enhanced_graph_search import EnhancedGraphSearch
        
        print("="*80)
        print("DEBUGGING RELATIONSHIP DATA FLOW")
        print("="*80)
        
        query = "what is the relation between 'Winfried Engelbrecht Bresges' and hkjc"
        
        print(f"\n🔍 Testing query: {query}")
        print("-" * 60)
        
        # Step 1: Test enhanced search directly
        print(f"\n1. Testing enhanced search directly...")
        search = EnhancedGraphSearch()
        result = search.search_entities_and_relationships("Winfried Engelbrecht Bresges", "hkjc")
        
        print(f"   Direct relationships found: {len(result.get('direct_relationships', []))}")
        for i, rel in enumerate(result.get('direct_relationships', [])):
            print(f"   [{i+1}] {rel['source']['name']} --[{rel['relationship_type']}]--> {rel['target']['name']}")
        
        # Step 2: Test web UI enhanced relationship data
        print(f"\n2. Testing web UI enhanced relationship data...")
        web_ui_result = get_enhanced_relationship_data(query)
        
        if web_ui_result:
            print(f"   Web UI nodes: {len(web_ui_result.get('nodes', []))}")
            print(f"   Web UI relationships: {len(web_ui_result.get('relationships', []))}")
            
            # Show the relationships
            for i, rel in enumerate(web_ui_result.get('relationships', [])):
                print(f"   [{i+1}] Relationship:")
                print(f"       ID: {rel.get('id')}")
                print(f"       Type: {rel.get('type')}")
                print(f"       Start: {rel.get('startNode')}")
                print(f"       End: {rel.get('endNode')}")
                print(f"       Properties: {rel.get('properties', {})}")
            
            # Check if nodes exist for the relationship endpoints
            print(f"\n   Node ID mapping:")
            for node in web_ui_result.get('nodes', []):
                print(f"   {node['id']}: {node['properties']['name']}")
        else:
            print(f"   ❌ No web UI result")
        
        # Step 3: Check the issue
        print(f"\n3. Analyzing the issue...")
        
        if result.get('direct_relationships') and not web_ui_result.get('relationships'):
            print(f"   🔍 Issue: Enhanced search finds relationships but web UI doesn't create them")
            
            # Debug the relationship creation logic
            rel = result['direct_relationships'][0]
            source_name = rel['source'].get('name', 'Unknown')
            target_name = rel['target'].get('name', 'Unknown')
            
            print(f"   Source name: '{source_name}'")
            print(f"   Target name: '{target_name}'")
            
            # Check if these names exist in the nodes
            if web_ui_result:
                source_found = False
                target_found = False
                
                for node in web_ui_result['nodes']:
                    node_name = node['properties']['name']
                    if node_name == source_name:
                        source_found = True
                        print(f"   ✅ Source node found: {node['id']}")
                    if node_name == target_name:
                        target_found = True
                        print(f"   ✅ Target node found: {node['id']}")
                
                if not source_found:
                    print(f"   ❌ Source node '{source_name}' not found in nodes")
                if not target_found:
                    print(f"   ❌ Target node '{target_name}' not found in nodes")
        
        return result, web_ui_result
        
    except Exception as e:
        logger.error(f"Debug failed: {e}")
        import traceback
        traceback.print_exc()
        return None, None

if __name__ == "__main__":
    debug_relationships()
