#!/usr/bin/env python3
"""
Test the debug logs to see where relationships are being lost.
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

def test_debug_relationships():
    """Test with debug logs to trace relationship flow."""
    
    try:
        # Add the project root to Python path
        project_root = os.path.dirname(os.path.abspath(__file__))
        sys.path.insert(0, project_root)
        
        print("="*80)
        print("TESTING WITH DEBUG LOGS TO TRACE RELATIONSHIP FLOW")
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
            
            print(f"✅ Backend graph data found")
            print(f"   Nodes: {len(graph_data.get('nodes', []))}")
            print(f"   Relationships: {len(graph_data.get('relationships', []))}")
            
            # Show the exact relationship data structure
            print(f"\n🔗 BACKEND RELATIONSHIP DATA STRUCTURE:")
            for i, rel in enumerate(graph_data.get('relationships', [])):
                print(f"   [{i+1}] Relationship:")
                print(f"       id: {rel.get('id')}")
                print(f"       type: {rel.get('type')}")
                print(f"       startNode: {rel.get('startNode')}")
                print(f"       endNode: {rel.get('endNode')}")
                print(f"       startNodeId: {rel.get('startNodeId')}")
                print(f"       endNodeId: {rel.get('endNodeId')}")
                print(f"       source: {rel.get('source')}")
                print(f"       target: {rel.get('target')}")
                print(f"       properties: {rel.get('properties', {})}")
                print()
            
            # Show node IDs for reference
            print(f"📋 BACKEND NODE IDS:")
            for node in graph_data.get('nodes', [])[:5]:  # Show first 5
                print(f"   {node.get('id')}: {node.get('properties', {}).get('name', 'Unknown')}")
            
            print(f"\n🌐 FRONTEND JAVASCRIPT WILL RECEIVE:")
            print(f"   The debug logs in the browser console will show:")
            print(f"   1. Raw graph data received")
            print(f"   2. Raw relationships count and data")
            print(f"   3. Processing each relationship")
            print(f"   4. Available node IDs")
            print(f"   5. Whether relationships are added or skipped")
            print(f"   ")
            print(f"   Check the browser console for detailed logs!")
            
            success = len(graph_data.get('relationships', [])) > 0
            
        else:
            print(f"❌ No graph data found in response")
            success = False
        
        # Instructions for debugging
        print(f"\n" + "="*80)
        print("DEBUGGING INSTRUCTIONS")
        print("="*80)
        
        print(f"🔍 TO DEBUG THE FRONTEND ISSUE:")
        print(f"   1. Open the web UI in your browser")
        print(f"   2. Open Developer Tools (F12)")
        print(f"   3. Go to the Console tab")
        print(f"   4. Ask the query: '{query}'")
        print(f"   5. Look for these debug logs:")
        print(f"      📊 Raw graph data received")
        print(f"      📊 Raw relationships count")
        print(f"      🔍 Processing X relationships")
        print(f"      🔍 Relationship 0: [object]")
        print(f"      🔍 Extracted IDs: startNode='...', endNode='...'")
        print(f"      🔍 Available node IDs: [array]")
        print(f"      ✅ Added relationship OR ⚠️ Skipping relationship")
        print(f"   ")
        print(f"   The logs will show exactly where relationships are being lost!")
        
        if success:
            print(f"\n✅ Backend has relationships - issue is in frontend validation")
        else:
            print(f"\n❌ Backend has no relationships - issue is in backend processing")
        
        return success
        
    except Exception as e:
        logger.error(f"Debug test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_debug_relationships()
