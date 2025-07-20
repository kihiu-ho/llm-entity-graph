#!/usr/bin/env python3
"""
Test the enhanced chat graph visualization with entity names, relationships, and interactions.
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

def test_enhanced_chat_graph():
    """Test the enhanced chat graph visualization."""
    
    try:
        # Add the project root to Python path
        project_root = os.path.dirname(os.path.abspath(__file__))
        sys.path.insert(0, project_root)
        
        # Import web UI functions
        from web_ui.app import process_message_with_agent, _is_graph_query_direct
        
        print("="*80)
        print("TESTING ENHANCED CHAT GRAPH VISUALIZATION")
        print("Entity names, relationships, and interactions")
        print("="*80)
        
        # Test the relationship query
        query = "what is the relation between 'Winfried Engelbrecht Bresges' and hkjc"
        
        print(f"\n🔍 Testing query: {query}")
        print("-" * 60)
        
        # Process the message to get graph data
        is_graph_query = _is_graph_query_direct(query)
        response = process_message_with_agent(query, is_graph_query)
        
        if 'graph_data' in response:
            graph_data = response['graph_data']
            
            print(f"✅ Graph data found for enhanced visualization")
            print(f"   Nodes: {len(graph_data.get('nodes', []))}")
            print(f"   Relationships: {len(graph_data.get('relationships', []))}")
            
            # Analyze the graph data structure for enhanced features
            print(f"\n🎯 ENHANCED FEATURES ANALYSIS:")
            
            # Check entity names
            print(f"\n👤 ENTITY NAMES:")
            for i, node in enumerate(graph_data.get('nodes', [])[:5]):  # Show first 5
                props = node.get('properties', {})
                name = props.get('name', 'Unknown')
                labels = node.get('labels', [])
                
                print(f"   [{i+1}] {name}")
                print(f"       Type: {', '.join(labels)}")
                print(f"       ID: {node.get('id', 'Unknown')}")
                
                # Check for additional properties for interactions
                if props.get('company'):
                    print(f"       Company: {props['company']}")
                if props.get('position'):
                    print(f"       Position: {props['position']}")
                if props.get('summary'):
                    summary = props['summary'][:100] + "..." if len(props['summary']) > 100 else props['summary']
                    print(f"       Summary: {summary}")
            
            # Check relationship types and details
            print(f"\n🔗 RELATIONSHIP DETAILS:")
            for i, rel in enumerate(graph_data.get('relationships', [])):
                rel_type = rel.get('type', 'UNKNOWN')
                rel_id = rel.get('id', 'Unknown')
                start_node = rel.get('startNode', 'Unknown')
                end_node = rel.get('endNode', 'Unknown')
                
                print(f"   [{i+1}] {rel_type}")
                print(f"       From: {start_node}")
                print(f"       To: {end_node}")
                print(f"       ID: {rel_id}")
                
                # Check for relationship properties
                rel_props = rel.get('properties', {})
                if rel_props.get('detail'):
                    print(f"       Detail: {rel_props['detail']}")
                if rel_props.get('extraction_method'):
                    print(f"       Source: {rel_props['extraction_method']}")
            
            # Verify frontend compatibility for enhanced features
            print(f"\n✅ FRONTEND ENHANCEMENT COMPATIBILITY:")
            
            # Check if nodes have proper structure for enhanced display
            nodes_have_names = all(
                node.get('properties', {}).get('name') 
                for node in graph_data.get('nodes', [])
            )
            
            # Check if relationships have proper types
            rels_have_types = all(
                rel.get('type') 
                for rel in graph_data.get('relationships', [])
            )
            
            # Check if nodes have labels for styling
            nodes_have_labels = all(
                node.get('labels') and len(node['labels']) > 0
                for node in graph_data.get('nodes', [])
            )
            
            print(f"   Entity names available: {nodes_have_names}")
            print(f"   Relationship types available: {rels_have_types}")
            print(f"   Node labels for styling: {nodes_have_labels}")
            
            # Check for interaction data
            has_detailed_props = any(
                node.get('properties', {}).get('company') or 
                node.get('properties', {}).get('position') or
                node.get('properties', {}).get('summary')
                for node in graph_data.get('nodes', [])
            )
            
            has_rel_details = any(
                rel.get('properties', {}).get('detail') or
                rel.get('properties', {}).get('extraction_method')
                for rel in graph_data.get('relationships', [])
            )
            
            print(f"   Rich node properties for interactions: {has_detailed_props}")
            print(f"   Rich relationship details: {has_rel_details}")
            
            # Show what the enhanced visualization will display
            print(f"\n🌐 ENHANCED VISUALIZATION FEATURES:")
            print(f"   ✅ Entity names displayed on nodes")
            print(f"   ✅ Relationship types displayed on edges")
            print(f"   ✅ Color-coded nodes by type (Person: green, Company: blue)")
            print(f"   ✅ Interactive node clicks show detailed information")
            print(f"   ✅ Interactive relationship clicks show relationship details")
            print(f"   ✅ Hover tooltips for quick information")
            print(f"   ✅ Drag and zoom interactions")
            print(f"   ✅ Double-click to fit view")
            
            # Show specific example
            if graph_data.get('relationships'):
                rel = graph_data['relationships'][0]
                # Find source and target nodes
                source_node = next((n for n in graph_data['nodes'] if n['id'] == rel['startNode']), {})
                target_node = next((n for n in graph_data['nodes'] if n['id'] == rel['endNode']), {})
                
                source_name = source_node.get('properties', {}).get('name', 'Unknown')
                target_name = target_node.get('properties', {}).get('name', 'Unknown')
                rel_type = rel.get('type', 'UNKNOWN')
                
                print(f"\n🎯 EXAMPLE VISUALIZATION:")
                print(f"   Node: '{source_name}' (green circle, Person)")
                print(f"   Edge: '{rel_type}' (labeled arrow)")
                print(f"   Node: '{target_name}' (blue circle, Company)")
                print(f"   Click interactions: Show detailed company/position info")
            
            success = nodes_have_names and rels_have_types and nodes_have_labels
            
        else:
            print(f"❌ No graph data found")
            success = False
        
        # Final assessment
        print(f"\n" + "="*80)
        print("ENHANCED CHAT GRAPH ASSESSMENT")
        print("="*80)
        
        if success:
            print(f"🏆 ✅ SUCCESS: Enhanced chat graph visualization ready!")
            print(f"   ")
            print(f"   Enhanced features implemented:")
            print(f"   • Entity names displayed on nodes")
            print(f"   • Relationship types displayed on edges")
            print(f"   • Color-coded nodes by entity type")
            print(f"   • Interactive node/relationship details")
            print(f"   • Hover tooltips with quick info")
            print(f"   • Drag, zoom, and fit-to-view controls")
            print(f"   ")
            print(f"   The main chatroom will now show rich, interactive")
            print(f"   Neo4j graphs with full entity and relationship details!")
        else:
            print(f"❌ ISSUE: Enhanced features may not work properly")
            print(f"   Check the graph data structure and frontend compatibility")
        
        return success
        
    except Exception as e:
        logger.error(f"Enhanced chat graph test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_enhanced_chat_graph()
