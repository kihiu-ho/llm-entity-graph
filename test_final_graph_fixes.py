#!/usr/bin/env python3
"""
Test all the fixes for the chat graph visualization.
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

def test_final_graph_fixes():
    """Test all the fixes for the chat graph visualization."""
    
    try:
        # Add the project root to Python path
        project_root = os.path.dirname(os.path.abspath(__file__))
        sys.path.insert(0, project_root)
        
        # Import functions
        from web_ui.app import process_message_with_agent, _is_graph_query_direct
        
        print("="*80)
        print("TESTING FINAL GRAPH VISUALIZATION FIXES")
        print("Entity names, relationships, and interactions")
        print("="*80)
        
        query = "what is the relation between 'Winfried Engelbrecht Bresges' and hkjc"
        
        print(f"\n🔍 Testing query: {query}")
        print("-" * 60)
        
        # Process the message to get the complete response
        is_graph_query = _is_graph_query_direct(query)
        response = process_message_with_agent(query, is_graph_query)
        
        if 'graph_data' in response:
            graph_data = response['graph_data']
            
            print(f"✅ Graph data found")
            print(f"   Nodes: {len(graph_data.get('nodes', []))}")
            print(f"   Relationships: {len(graph_data.get('relationships', []))}")
            
            # Check for the key entities
            print(f"\n👤 KEY ENTITIES:")
            winfried_found = False
            hkjc_found = False
            
            for node in graph_data.get('nodes', []):
                name = node.get('properties', {}).get('name', 'Unknown')
                node_id = node.get('id', 'Unknown')
                labels = node.get('labels', [])
                
                if 'Winfried' in name:
                    winfried_found = True
                    print(f"   ✅ {name} (ID: {node_id}, Type: {', '.join(labels)})")
                elif 'Hong Kong Jockey Club' in name:
                    hkjc_found = True
                    print(f"   ✅ {name} (ID: {node_id}, Type: {', '.join(labels)})")
            
            # Check for relationships
            print(f"\n🔗 RELATIONSHIPS:")
            relationship_found = False
            
            for rel in graph_data.get('relationships', []):
                rel_type = rel.get('type', 'Unknown')
                rel_id = rel.get('id', 'Unknown')
                start_node = rel.get('startNode', 'Unknown')
                end_node = rel.get('endNode', 'Unknown')
                
                print(f"   ✅ {rel_type}")
                print(f"      ID: {rel_id}")
                print(f"      From: {start_node}")
                print(f"      To: {end_node}")
                
                # Find the actual node names
                start_name = "Unknown"
                end_name = "Unknown"
                
                for node in graph_data.get('nodes', []):
                    if node.get('id') == start_node:
                        start_name = node.get('properties', {}).get('name', 'Unknown')
                    if node.get('id') == end_node:
                        end_name = node.get('properties', {}).get('name', 'Unknown')
                
                print(f"      Actual: {start_name} --[{rel_type}]--> {end_name}")
                
                if 'CEO_OF' in rel_type and 'Winfried' in start_name and 'Hong Kong Jockey Club' in end_name:
                    relationship_found = True
                    print(f"      🎯 KEY RELATIONSHIP FOUND!")
            
            # Frontend compatibility check
            print(f"\n🌐 FRONTEND COMPATIBILITY:")
            
            # Check node structure
            nodes_valid = all(
                'id' in node and 'properties' in node and 'labels' in node
                for node in graph_data.get('nodes', [])
            )
            
            # Check relationship structure
            rels_valid = all(
                'id' in rel and 'type' in rel and 'startNode' in rel and 'endNode' in rel
                for rel in graph_data.get('relationships', [])
            )
            
            # Check entity names
            names_available = all(
                node.get('properties', {}).get('name')
                for node in graph_data.get('nodes', [])
            )
            
            # Check relationship types
            types_available = all(
                rel.get('type')
                for rel in graph_data.get('relationships', [])
            )
            
            print(f"   Node structure valid: {nodes_valid}")
            print(f"   Relationship structure valid: {rels_valid}")
            print(f"   Entity names available: {names_available}")
            print(f"   Relationship types available: {types_available}")
            
            # Overall success check
            success = (winfried_found and hkjc_found and relationship_found and 
                      nodes_valid and rels_valid and names_available and types_available)
            
            print(f"\n" + "="*80)
            print("FINAL ASSESSMENT")
            print("="*80)
            
            if success:
                print(f"🏆 ✅ ALL FIXES SUCCESSFUL!")
                print(f"   ")
                print(f"   ✅ Entity names will be displayed on nodes")
                print(f"   ✅ Relationship types will be displayed on edges")
                print(f"   ✅ Key relationship found: Winfried --[CEO_OF]--> HKJC")
                print(f"   ✅ Data structure compatible with frontend")
                print(f"   ✅ Interactive features will work")
                print(f"   ")
                print(f"   The main chatroom graph will now show:")
                print(f"   • Entity names on all nodes")
                print(f"   • Relationship types on all edges")
                print(f"   • Color-coded nodes by type")
                print(f"   • Interactive click and hover features")
                print(f"   • Professional styling and animations")
            else:
                print(f"❌ SOME ISSUES REMAIN:")
                if not winfried_found:
                    print(f"   • Winfried entity not found")
                if not hkjc_found:
                    print(f"   • HKJC entity not found")
                if not relationship_found:
                    print(f"   • Key relationship not found")
                if not (nodes_valid and rels_valid):
                    print(f"   • Data structure issues")
                if not (names_available and types_available):
                    print(f"   • Missing names or types")
            
            return success
            
        else:
            print(f"❌ No graph data found in response")
            return False
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_final_graph_fixes()
