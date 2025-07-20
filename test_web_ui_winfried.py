#!/usr/bin/env python3
"""
Test the web UI fix for Winfried Engelbrecht Bresges.
"""

import requests
import json
import time

def test_web_ui_winfried():
    """Test the web UI with Winfried query."""
    
    base_url = "http://localhost:8000"
    
    print("="*80)
    print("TESTING WEB UI FIX FOR WINFRIED ENGELBRECHT BRESGES")
    print("="*80)
    
    # Test 1: Health check
    print("\n1. Testing health check...")
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            print("✅ Health check passed")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Cannot connect to web UI: {e}")
        print("Please start the web UI with: python web_ui/app.py")
        return
    
    # Test 2: Direct chat query
    print("\n2. Testing direct chat query...")
    try:
        query = 'who is "Winfried Engelbrecht Bresges"'
        response = requests.post(
            f"{base_url}/chat/direct",
            json={"message": query}
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Query successful")
            print(f"   Response type: {result.get('type')}")
            print(f"   Content length: {len(result.get('content', ''))}")
            print(f"   Has graph data: {'graph_data' in result}")
            
            if 'graph_data' in result:
                graph_data = result['graph_data']
                if graph_data:
                    nodes = len(graph_data.get('nodes', []))
                    relationships = len(graph_data.get('relationships', []))
                    print(f"   Graph: {nodes} nodes, {relationships} relationships")
                    
                    # Check if we found Winfried
                    for node in graph_data.get('nodes', []):
                        name = node.get('properties', {}).get('name', '')
                        if 'winfried' in name.lower():
                            print(f"   ✅ Found Winfried: {name}")
                            print(f"      Position: {node.get('properties', {}).get('position')}")
                            print(f"      Type: {node.get('properties', {}).get('type')}")
                            break
                    else:
                        print("   ❌ Winfried not found in nodes")
                    
                    # Check relationships
                    ceo_relationships = 0
                    hkjc_relationships = 0
                    for rel in graph_data.get('relationships', []):
                        rel_type = rel.get('type', '')
                        if 'CEO' in rel_type:
                            ceo_relationships += 1
                        # Check if target node is HKJC
                        end_node_id = rel.get('endNodeId', '')
                        for node in graph_data.get('nodes', []):
                            if node.get('id') == end_node_id:
                                target_name = node.get('properties', {}).get('name', '')
                                if 'hong kong jockey' in target_name.lower():
                                    hkjc_relationships += 1
                                break
                    
                    print(f"   CEO relationships: {ceo_relationships}")
                    print(f"   HKJC relationships: {hkjc_relationships}")
                else:
                    print("   ❌ No graph data returned")
            else:
                print("   ❌ No graph data in response")
            
            # Print first 200 chars of content
            content = result.get('content', '')
            if content:
                print(f"\n   Content preview: {content[:200]}...")
        else:
            print(f"❌ Query failed: {response.status_code}")
            print(f"   Response: {response.text}")
    
    except Exception as e:
        print(f"❌ Query failed: {e}")
    
    print("\n✅ Web UI test completed!")

if __name__ == "__main__":
    test_web_ui_winfried()
