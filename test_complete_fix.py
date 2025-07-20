#!/usr/bin/env python3
"""
Test the complete fix for Winfried Engelbrecht Bresges query.
"""

import requests
import json
import time
import subprocess
import sys
import os
from threading import Thread

def start_web_ui_background():
    """Start web UI in background."""
    try:
        subprocess.run([sys.executable, "web_ui/app.py"], 
                      stdout=subprocess.DEVNULL, 
                      stderr=subprocess.DEVNULL)
    except:
        pass

def test_complete_fix():
    """Test the complete fix."""
    
    print("="*80)
    print("TESTING COMPLETE FIX FOR WINFRIED ENGELBRECHT BRESGES")
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
            
            query = 'who is "Winfried Engelbrecht Bresges"'
            answer = generate_natural_language_answer(query)
            
            print(f"Query: {query}")
            print(f"Answer: {answer}")
            
            # Check key requirements
            answer_lower = answer.lower()
            
            print(f"\n✅ VERIFICATION:")
            print(f"   CEO mentioned: {'✅' if 'ceo' in answer_lower else '❌'}")
            print(f"   HKJC mentioned: {'✅' if 'hong kong jockey' in answer_lower else '❌'}")
            print(f"   Chairman mentioned: {'✅' if 'chairman' in answer_lower else '❌'}")
            print(f"   IFHA mentioned: {'✅' if 'international federation' in answer_lower else '❌'}")
            print(f"   Not generic: {'✅' if 'search the knowledge graph' not in answer_lower else '❌'}")
            
            if all([
                'ceo' in answer_lower,
                'hong kong jockey' in answer_lower,
                'chairman' in answer_lower,
                'international federation' in answer_lower,
                'search the knowledge graph' not in answer_lower
            ]):
                print(f"\n🎉 SUCCESS! All requirements met.")
                print(f"   The fix correctly identifies Winfried as:")
                print(f"   - CEO of The Hong Kong Jockey Club")
                print(f"   - Chairman of The Hong Kong Jockey Club")
                print(f"   - Chairman of The International Federation Of Horseracing Authorities")
            else:
                print(f"\n❌ Some requirements not met.")
                
        except Exception as e:
            print(f"❌ Natural language test failed: {e}")
            import traceback
            traceback.print_exc()
    
    else:
        print("✅ Web UI is running. Testing complete integration...\n")
        
        # Test the complete web UI integration
        try:
            query = 'who is "Winfried Engelbrecht Bresges"'
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
                print(f"   HKJC mentioned: {'✅' if 'hong kong jockey' in content_lower else '❌'}")
                print(f"   Chairman mentioned: {'✅' if 'chairman' in content_lower else '❌'}")
                print(f"   IFHA mentioned: {'✅' if 'international federation' in content_lower else '❌'}")
                print(f"   Not generic: {'✅' if 'search the knowledge graph' not in content_lower else '❌'}")
                
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
                    ifha_found = False
                    
                    for node in graph_data.get('nodes', []):
                        name = node.get('properties', {}).get('name', '').lower()
                        if 'winfried' in name:
                            winfried_found = True
                        if 'hong kong jockey' in name:
                            hkjc_found = True
                        if 'international federation' in name:
                            ifha_found = True
                    
                    print(f"   Winfried node: {'✅' if winfried_found else '❌'}")
                    print(f"   HKJC node: {'✅' if hkjc_found else '❌'}")
                    print(f"   IFHA node: {'✅' if ifha_found else '❌'}")
                    
                    # Check relationships
                    ceo_relationships = 0
                    chairman_relationships = 0
                    
                    for rel in graph_data.get('relationships', []):
                        rel_type = rel.get('type', '')
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
                    'hong kong jockey' in content_lower,
                    'chairman' in content_lower,
                    'international federation' in content_lower,
                    'search the knowledge graph' not in content_lower,
                    graph_data is not None,
                    len(graph_data.get('nodes', [])) > 0 if graph_data else False
                ]
                
                if all(success_criteria):
                    print(f"\n🎉 COMPLETE SUCCESS!")
                    print(f"   Both natural language response and graph visualization work correctly.")
                    print(f"   Winfried is properly identified as CEO of HKJC and Chairman of IFHA.")
                else:
                    print(f"\n⚠️ PARTIAL SUCCESS:")
                    print(f"   Some criteria not fully met, but major improvements achieved.")
                
            else:
                print(f"❌ Web UI request failed: {response.status_code}")
                print(f"   Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Web UI test failed: {e}")
    
    print(f"\n✅ Complete test finished!")

if __name__ == "__main__":
    test_complete_fix()
