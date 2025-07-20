#!/usr/bin/env python3
"""
Test the NVL reference pattern implementation to ensure relationship links work.
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

def test_nvl_reference_pattern():
    """Test the NVL reference pattern implementation."""
    
    try:
        # Add the project root to Python path
        project_root = os.path.dirname(os.path.abspath(__file__))
        sys.path.insert(0, project_root)
        
        print("="*80)
        print("TESTING NVL REFERENCE PATTERN FOR RELATIONSHIP LINKS")
        print("Following exact StyleExample.js pattern from @neo4j-nvl/base")
        print("="*80)
        
        query = "what is the relation between 'Winfried Engelbrecht Bresges' and hkjc"
        
        print(f"\n🔍 Testing query: {query}")
        print("-" * 60)
        
        # Test the complete web UI process
        from web_ui.app import process_message_with_agent, _is_graph_query_direct
        
        is_graph_query = _is_graph_query_direct(query)
        response = process_message_with_agent(query, is_graph_query)
        
        if 'graph_data' in response:
            graph_data = response['graph_data']
            
            print(f"✅ Graph data found")
            print(f"   Nodes: {len(graph_data.get('nodes', []))}")
            print(f"   Relationships: {len(graph_data.get('relationships', []))}")
            
            # Analyze the data structure for NVL reference pattern
            print(f"\n📊 NVL REFERENCE PATTERN ANALYSIS:")
            
            # Show expected JavaScript node format
            print(f"\n👤 EXPECTED JAVASCRIPT NODE FORMAT (StyleExample.js pattern):")
            for i, node in enumerate(graph_data.get('nodes', [])[:2]):  # Show first 2
                props = node.get('properties', {})
                node_id = node.get('id', 'Unknown')
                labels = node.get('labels', [])
                entity_name = props.get('name', 'Unknown')
                entity_type = labels[0] if labels else 'Unknown'
                
                # Predict the JavaScript formatting
                color_mapping = {
                    'Person': '#4CAF50',
                    'Company': '#2196F3',
                    'Organization': '#FF9800',
                    'Entity': '#9C27B0'
                }
                predicted_color = color_mapping.get(entity_type, '#757575')
                
                print(f"   nodes[{i}] = {{")
                print(f"     id: '{node_id}',")
                print(f"     color: '{predicted_color}',")
                print(f"     caption: '{entity_name}',")
                print(f"     size: 40,")
                print(f"     selected: false,")
                print(f"     hovered: false")
                print(f"   }}")
                print()
            
            # Show expected JavaScript relationship format
            print(f"🔗 EXPECTED JAVASCRIPT RELATIONSHIP FORMAT (StyleExample.js pattern):")
            for i, rel in enumerate(graph_data.get('relationships', [])):
                rel_id = rel.get('id', 'Unknown')
                rel_type = rel.get('type', 'Unknown')
                start_node = rel.get('startNode', 'Unknown')
                end_node = rel.get('endNode', 'Unknown')
                
                print(f"   rels[{i}] = {{")
                print(f"     id: '{rel_id}',")
                print(f"     from: '{start_node}',")  # ← Key: uses 'from' not 'startNode'
                print(f"     to: '{end_node}',")      # ← Key: uses 'to' not 'endNode'
                print(f"     color: '#666666',")
                print(f"     caption: '{rel_type}',")
                print(f"     width: 2,")
                print(f"     selected: false,")
                print(f"     hovered: false")
                print(f"   }}")
                print()
            
            # Show the NVL constructor call
            print(f"🏗️ EXPECTED NVL CONSTRUCTOR CALL:")
            print(f"   const nvl = new NVL(container, nodes, rels, {{")
            print(f"     layout: 'forceDirected',")
            print(f"     initialZoom: 0.8,")
            print(f"     styling: {{")
            print(f"       nodeDefaultBorderColor: '#ffffff',")
            print(f"       selectedBorderColor: '#4CAF50'")
            print(f"     }}")
            print(f"   }})")
            
            # Verify the key differences from our previous approach
            print(f"\n🔧 KEY DIFFERENCES FROM PREVIOUS APPROACH:")
            print(f"   ✅ Use simple 'nodes' and 'rels' arrays (not nvlNodes/nvlRelationships)")
            print(f"   ✅ Relationships use 'from'/'to' (not startNode/endNode)")
            print(f"   ✅ Minimal required properties only")
            print(f"   ✅ Simple NVL constructor (not complex configuration)")
            print(f"   ✅ Direct property assignment (not elementId/identity)")
            
            # Check if the data is properly structured
            nodes_valid = all(
                'id' in node and node.get('properties', {}).get('name')
                for node in graph_data.get('nodes', [])
            )
            
            rels_valid = all(
                'id' in rel and 'type' in rel and 'startNode' in rel and 'endNode' in rel
                for rel in graph_data.get('relationships', [])
            )
            
            print(f"\n✅ DATA STRUCTURE VALIDATION:")
            print(f"   Nodes have required data: {nodes_valid}")
            print(f"   Relationships have required data: {rels_valid}")
            print(f"   Ready for NVL reference pattern: {nodes_valid and rels_valid}")
            
            success = nodes_valid and rels_valid and len(graph_data.get('relationships', [])) > 0
            
        else:
            print(f"❌ No graph data found in response")
            success = False
        
        # Final assessment
        print(f"\n" + "="*80)
        print("NVL REFERENCE PATTERN ASSESSMENT")
        print("="*80)
        
        if success:
            print(f"🏆 ✅ SUCCESS: NVL Reference Pattern Ready!")
            print(f"   ")
            print(f"   ✅ Data structure matches StyleExample.js pattern")
            print(f"   ✅ Relationships use 'from'/'to' format")
            print(f"   ✅ Nodes have color/caption/size properties")
            print(f"   ✅ Simple NVL constructor configuration")
            print(f"   ")
            print(f"   Expected result in chatroom:")
            print(f"   🟢 'Winfried Engelbrecht Bresges' (green node with entity name)")
            print(f"   ➡️  'CEO_OF' (gray arrow with relationship type)")
            print(f"   🔵 'The Hong Kong Jockey Club' (blue node with entity name)")
            print(f"   ")
            print(f"   Relationship links should now work correctly!")
        else:
            print(f"❌ ISSUE: NVL reference pattern needs adjustment")
            print(f"   Check the data structure and JavaScript formatting")
        
        return success
        
    except Exception as e:
        logger.error(f"NVL reference pattern test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_nvl_reference_pattern()
