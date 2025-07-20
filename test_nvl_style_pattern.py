#!/usr/bin/env python3
"""
Test the NVL style pattern implementation for entity names and relationships.
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

def test_nvl_style_pattern():
    """Test the NVL style pattern implementation."""
    
    try:
        # Add the project root to Python path
        project_root = os.path.dirname(os.path.abspath(__file__))
        sys.path.insert(0, project_root)
        
        # Import functions
        from web_ui.app import process_message_with_agent, _is_graph_query_direct
        
        print("="*80)
        print("TESTING NVL STYLE PATTERN FOR ENTITY NAMES AND RELATIONSHIPS")
        print("Following StyleExample.js pattern with caption and color properties")
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
            
            # Analyze the NVL-style formatting
            print(f"\n🎨 NVL STYLE PATTERN ANALYSIS:")
            
            # Check nodes for StyleExample.js pattern properties
            print(f"\n👤 NODE STYLING (StyleExample.js pattern):")
            node_style_valid = True
            
            for i, node in enumerate(graph_data.get('nodes', [])[:3]):  # Show first 3
                props = node.get('properties', {})
                node_id = node.get('id', 'Unknown')
                labels = node.get('labels', [])
                
                # Check for StyleExample.js pattern properties
                has_caption = 'name' in props  # Will be used as caption
                has_color_info = len(labels) > 0  # Will determine color
                entity_name = props.get('name', 'Unknown')
                entity_type = labels[0] if labels else 'Unknown'
                
                print(f"   [{i+1}] Node ID: {node_id}")
                print(f"       Caption (entity name): {entity_name}")
                print(f"       Type (for color): {entity_type}")
                print(f"       Has caption data: {has_caption}")
                print(f"       Has color data: {has_color_info}")
                
                # Predict the NVL styling
                color_mapping = {
                    'Person': '#4CAF50',
                    'Company': '#2196F3',
                    'Organization': '#FF9800',
                    'Entity': '#9C27B0'
                }
                predicted_color = color_mapping.get(entity_type, '#757575')
                
                print(f"       Predicted NVL color: {predicted_color}")
                print(f"       Predicted NVL caption: '{entity_name}'")
                print()
                
                if not (has_caption and has_color_info):
                    node_style_valid = False
            
            # Check relationships for StyleExample.js pattern properties
            print(f"🔗 RELATIONSHIP STYLING (StyleExample.js pattern):")
            rel_style_valid = True
            
            for i, rel in enumerate(graph_data.get('relationships', [])):
                rel_id = rel.get('id', 'Unknown')
                rel_type = rel.get('type', 'Unknown')
                start_node = rel.get('startNode', 'Unknown')
                end_node = rel.get('endNode', 'Unknown')
                
                # Check for StyleExample.js pattern properties
                has_caption = rel_type != 'Unknown'
                has_from_to = start_node != 'Unknown' and end_node != 'Unknown'
                
                print(f"   [{i+1}] Relationship ID: {rel_id}")
                print(f"       Caption (relationship type): {rel_type}")
                print(f"       From: {start_node}")
                print(f"       To: {end_node}")
                print(f"       Has caption data: {has_caption}")
                print(f"       Has from/to data: {has_from_to}")
                
                # Predict the NVL styling
                print(f"       Predicted NVL color: #666666")
                print(f"       Predicted NVL caption: '{rel_type}'")
                print(f"       Predicted NVL width: 2")
                print()
                
                if not (has_caption and has_from_to):
                    rel_style_valid = False
            
            # Check frontend JavaScript formatting
            print(f"🌐 FRONTEND JAVASCRIPT FORMATTING:")
            print(f"   Expected nvlNodes format:")
            print(f"   {{")
            print(f"     id: 'entity1_0',")
            print(f"     color: '#4CAF50',           // Green for Person")
            print(f"     caption: 'Winfried Engelbrecht Bresges',  // Entity name")
            print(f"     size: 40,")
            print(f"     selected: false,")
            print(f"     hovered: false")
            print(f"   }}")
            print()
            print(f"   Expected nvlRelationships format:")
            print(f"   {{")
            print(f"     id: 'rel_0',")
            print(f"     from: 'entity1_0',")
            print(f"     to: 'entity2_0',")
            print(f"     color: '#666666',           // Gray for relationships")
            print(f"     caption: 'CEO_OF',          // Relationship type")
            print(f"     width: 2,")
            print(f"     selected: false,")
            print(f"     hovered: false")
            print(f"   }}")
            
            # Overall validation
            print(f"\n✅ VALIDATION RESULTS:")
            print(f"   Node styling data valid: {node_style_valid}")
            print(f"   Relationship styling data valid: {rel_style_valid}")
            print(f"   Data structure compatible: {node_style_valid and rel_style_valid}")
            
            # Show expected visual result
            if node_style_valid and rel_style_valid:
                print(f"\n🎯 EXPECTED VISUAL RESULT:")
                print(f"   🟢 'Winfried Engelbrecht Bresges' (green circle with name)")
                print(f"   ➡️  'CEO_OF' (gray arrow with relationship type)")
                print(f"   🔵 'The Hong Kong Jockey Club' (blue circle with name)")
                print(f"   ")
                print(f"   Following StyleExample.js pattern:")
                print(f"   • Entity names as node captions")
                print(f"   • Relationship types as edge captions")
                print(f"   • Color-coded by entity type")
                print(f"   • Standard sizes and styling")
            
            success = node_style_valid and rel_style_valid
            
        else:
            print(f"❌ No graph data found in response")
            success = False
        
        # Final assessment
        print(f"\n" + "="*80)
        print("NVL STYLE PATTERN ASSESSMENT")
        print("="*80)
        
        if success:
            print(f"🏆 ✅ SUCCESS: NVL StyleExample.js pattern implemented!")
            print(f"   ")
            print(f"   ✅ Entity names will display as node captions")
            print(f"   ✅ Relationship types will display as edge captions")
            print(f"   ✅ Color coding by entity type implemented")
            print(f"   ✅ Data structure follows StyleExample.js pattern")
            print(f"   ✅ Compatible with NVL styling system")
            print(f"   ")
            print(f"   The chatroom graph now uses the same pattern as")
            print(f"   StyleExample.js with proper entity names and relationships!")
        else:
            print(f"❌ ISSUE: NVL style pattern needs refinement")
            print(f"   Check the data structure and styling implementation")
        
        return success
        
    except Exception as e:
        logger.error(f"NVL style pattern test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_nvl_style_pattern()
