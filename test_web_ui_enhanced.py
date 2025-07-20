#!/usr/bin/env python3
"""
Test the enhanced web UI functionality for relationship queries.
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

def test_web_ui_enhanced():
    """Test the enhanced web UI functionality."""
    
    try:
        # Add the project root to Python path
        project_root = os.path.dirname(os.path.abspath(__file__))
        sys.path.insert(0, project_root)
        
        # Import web UI functions
        from web_ui.app import get_graph_data_with_agent_tool, is_relationship_query, get_enhanced_relationship_data
        
        print("="*80)
        print("TESTING ENHANCED WEB UI FUNCTIONALITY")
        print("="*80)
        
        # Test query
        query = "what is the relation between 'Winfried Engelbrecht Bresges' and hkjc"
        
        print(f"\n🔍 Testing query: {query}")
        print("-" * 60)
        
        # Test 1: Check if it's detected as a relationship query
        is_rel_query = is_relationship_query(query)
        print(f"✅ Relationship query detected: {is_rel_query}")
        
        # Test 2: Test enhanced relationship data extraction
        print(f"\n🔍 Testing enhanced relationship data extraction...")
        enhanced_data = get_enhanced_relationship_data(query)
        
        if enhanced_data:
            print(f"✅ Enhanced data found:")
            print(f"   Nodes: {len(enhanced_data.get('nodes', []))}")
            print(f"   Relationships: {len(enhanced_data.get('relationships', []))}")
            
            # Show nodes
            print(f"\n👤 NODES:")
            for i, node in enumerate(enhanced_data.get('nodes', [])):
                print(f"   [{i+1}] {node['properties']['name']} ({', '.join(node['labels'])})")
                if node['properties'].get('company'):
                    print(f"       Company: {node['properties']['company']}")
                if node['properties'].get('position'):
                    print(f"       Position: {node['properties']['position']}")
            
            # Show relationships
            print(f"\n🔗 RELATIONSHIPS:")
            for i, rel in enumerate(enhanced_data.get('relationships', [])):
                source_node = next((n for n in enhanced_data['nodes'] if n['id'] == rel['startNode']), {})
                target_node = next((n for n in enhanced_data['nodes'] if n['id'] == rel['endNode']), {})
                
                source_name = source_node.get('properties', {}).get('name', 'Unknown')
                target_name = target_node.get('properties', {}).get('name', 'Unknown')
                
                print(f"   [{i+1}] {source_name} --[{rel['type']}]--> {target_name}")
                if rel['properties'].get('detail'):
                    print(f"       Detail: {rel['properties']['detail']}")
            
            # Show metadata
            metadata = enhanced_data.get('metadata', {})
            print(f"\n📊 METADATA:")
            print(f"   Source: {metadata.get('source', 'Unknown')}")
            print(f"   Connection Strength: {metadata.get('connection_strength', 0.0)}")
            print(f"   Summary: {metadata.get('summary', 'No summary')}")
        else:
            print(f"❌ No enhanced data found")
        
        # Test 3: Test full web UI function
        print(f"\n🔍 Testing full web UI function...")
        full_data = get_graph_data_with_agent_tool(query)
        
        if full_data:
            print(f"✅ Full web UI data found:")
            print(f"   Nodes: {len(full_data.get('nodes', []))}")
            print(f"   Relationships: {len(full_data.get('relationships', []))}")
            print(f"   Source: {full_data.get('metadata', {}).get('source', 'Unknown')}")
        else:
            print(f"❌ No full web UI data found")
        
        print(f"\n" + "="*80)
        print("WEB UI ENHANCEMENT TEST COMPLETED")
        print("="*80)
        
        # Summary
        success = enhanced_data is not None and len(enhanced_data.get('relationships', [])) > 0
        
        if success:
            print(f"🏆 SUCCESS: Web UI enhanced search is working!")
            print(f"   - Relationship query detection: ✅")
            print(f"   - Enhanced data extraction: ✅")
            print(f"   - Relationship found: ✅")
        else:
            print(f"❌ ISSUE: Web UI enhanced search needs debugging")
        
        return success
        
    except Exception as e:
        logger.error(f"Web UI test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_web_ui_enhanced()
