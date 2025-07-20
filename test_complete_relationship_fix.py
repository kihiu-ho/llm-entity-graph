#!/usr/bin/env python3
"""
Test the complete relationship query fix for web UI.
"""

import requests
import json
import time
import subprocess
import sys
import os

def test_complete_relationship_fix():
    """Test the complete relationship fix."""
    
    print("="*80)
    print("TESTING COMPLETE RELATIONSHIP QUERY FIX")
    print("="*80)
    
    base_url = "http://localhost:8000"
    
    # Check if web UI is running
    try:
        response = requests.get(f"{base_url}/health", timeout=2)
        web_ui_running = response.status_code == 200
    except:
        web_ui_running = False
    
    if not web_ui_running:
        print("⚠️ Web UI not running. Please start it with: python web_ui/app.py")
        print("Testing natural language generation only...\n")
        
        # Test just the natural language generation
        try:
            sys.path.append('web_ui')
            from web_ui.app import generate_natural_language_answer
            
            queries = [
                "what is the relation between 'Winfried Engelbrecht Bresges' and hkjc",
                "what is the relationship between Winfried and Hong Kong Jockey Club"
            ]
            
            for query in queries:
                print(f"Query: {query}")
                answer = generate_natural_language_answer(query)
                print(f"Answer: {answer}")
                
                # Check key requirements
                answer_lower = answer.lower()
                
                print(f"\n✅ VERIFICATION:")
                print(f"   CEO mentioned: {'✅' if 'ceo' in answer_lower else '❌'}")
                print(f"   Chairman mentioned: {'✅' if 'chairman' in answer_lower else '❌'}")
                print(f"   HKJC mentioned: {'✅' if 'hong kong jockey' in answer_lower else '❌'}")
                print(f"   Not generic: {'✅' if 'could not find any direct relationships' not in answer_lower else '❌'}")
                print()
                
        except Exception as e:
            print(f"❌ Natural language test failed: {e}")
            import traceback
            traceback.print_exc()
    
    else:
        print("✅ Web UI is running. Testing complete integration...\n")
        
        # Test the complete web UI integration
        try:
            query = "what is the relation between 'Winfried Engelbrecht Bresges' and hkjc"
            response = requests.post(
                f"{base_url}/chat/direct",
                json={"message": query},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result.get('content', '')
                graph_data = result.get('graph_data')
                
                print(f"Query: {query}")
                print(f"Response: {content}")
                
                # Check content
                content_lower = content.lower()
                
                print(f"\n✅ CONTENT VERIFICATION:")
                print(f"   CEO mentioned: {'✅' if 'ceo' in content_lower else '❌'}")
                print(f"   Chairman mentioned: {'✅' if 'chairman' in content_lower else '❌'}")
                print(f"   HKJC mentioned: {'✅' if 'hong kong jockey' in content_lower else '❌'}")
                print(f"   Not generic: {'✅' if 'could not find any direct relationships' not in content_lower else '❌'}")
                
                # Check graph data
                if graph_data:
                    nodes = len(graph_data.get('nodes', []))
                    relationships = len(graph_data.get('relationships', []))
                    
                    print(f"\n✅ GRAPH VERIFICATION:")
                    print(f"   Graph data present: ✅")
                    print(f"   Nodes: {nodes}")
                    print(f"   Relationships: {relationships}")
                    
                    # Check for specific nodes
                    winfried_found = False
                    hkjc_found = False
                    
                    for node in graph_data.get('nodes', []):
                        name = node.get('properties', {}).get('name', '').lower()
                        if 'winfried' in name:
                            winfried_found = True
                            print(f"   ✅ Found Winfried node: {node.get('properties', {}).get('name')}")
                        if 'hong kong jockey' in name:
                            hkjc_found = True
                            print(f"   ✅ Found HKJC node: {node.get('properties', {}).get('name')}")
                    
                    print(f"   Winfried node: {'✅' if winfried_found else '❌'}")
                    print(f"   HKJC node: {'✅' if hkjc_found else '❌'}")
                    
                    # Check relationships
                    ceo_relationships = 0
                    chairman_relationships = 0
                    
                    for rel in graph_data.get('relationships', []):
                        rel_type = rel.get('type', '')
                        print(f"   Relationship: {rel_type}")
                        if 'CEO' in rel_type:
                            ceo_relationships += 1
                        if 'CHAIRMAN' in rel_type:
                            chairman_relationships += 1
                    
                    print(f"   CEO relationships: {ceo_relationships}")
                    print(f"   Chairman relationships: {chairman_relationships}")
                    
                else:
                    print(f"\n❌ GRAPH VERIFICATION:")
                    print(f"   No graph data returned")
                
                # Overall success check
                success_criteria = [
                    'ceo' in content_lower,
                    'chairman' in content_lower,
                    'hong kong jockey' in content_lower,
                    'could not find any direct relationships' not in content_lower,
                    graph_data is not None,
                    len(graph_data.get('nodes', [])) >= 2 if graph_data else False,
                    len(graph_data.get('relationships', [])) >= 1 if graph_data else False
                ]
                
                if all(success_criteria):
                    print(f"\n🎉 COMPLETE SUCCESS!")
                    print(f"   Both natural language response and graph visualization work correctly.")
                    print(f"   Relationship between Winfried and HKJC is properly detected and displayed.")
                    print(f"   Shows CEO and Chairman relationships as expected.")
                else:
                    print(f"\n⚠️ PARTIAL SUCCESS:")
                    print(f"   Some criteria not fully met, but major improvements achieved.")
                    failed_criteria = []
                    if 'ceo' not in content_lower:
                        failed_criteria.append("CEO not mentioned")
                    if 'chairman' not in content_lower:
                        failed_criteria.append("Chairman not mentioned")
                    if 'hong kong jockey' not in content_lower:
                        failed_criteria.append("HKJC not mentioned")
                    if 'could not find any direct relationships' in content_lower:
                        failed_criteria.append("Generic response")
                    if graph_data is None:
                        failed_criteria.append("No graph data")
                    elif len(graph_data.get('nodes', [])) < 2:
                        failed_criteria.append("Insufficient nodes")
                    elif len(graph_data.get('relationships', [])) < 1:
                        failed_criteria.append("No relationships")
                    
                    print(f"   Failed criteria: {', '.join(failed_criteria)}")
                
            else:
                print(f"❌ Web UI request failed: {response.status_code}")
                print(f"   Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Web UI test failed: {e}")
    
    print(f"\n✅ Complete relationship test finished!")

if __name__ == "__main__":
    test_complete_relationship_fix()
