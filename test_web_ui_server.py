#!/usr/bin/env python3
"""
Test script to verify the web UI server can handle the enhanced graph visualization.
"""

import requests
import json
import logging
import time
import threading
import subprocess
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def start_web_ui_server():
    """Start the web UI server in a separate process."""
    try:
        # Change to the web UI directory
        web_ui_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'web_ui')
        
        # Start the Flask server
        cmd = ["python", "app.py"]
        process = subprocess.Popen(
            cmd,
            cwd=web_ui_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Give the server time to start
        time.sleep(3)
        
        return process
        
    except Exception as e:
        logger.error(f"Failed to start web UI server: {e}")
        return None

def test_web_ui_endpoint():
    """Test the web UI endpoint with our enhanced query."""
    
    try:
        # Test the direct chat endpoint
        url = "http://localhost:5000/chat/direct"
        
        # The query that should trigger enhanced graph visualization
        test_data = {
            "message": "what is the relation between 'Winfried Engelbrecht Bresges' and hkjc",
            "session_id": "test_session",
            "user_id": "test_user"
        }
        
        print("="*80)
        print("TESTING WEB UI SERVER ENDPOINT")
        print("="*80)
        
        print(f"\n🔍 Testing endpoint: {url}")
        print(f"📝 Query: {test_data['message']}")
        
        # Make the request
        response = requests.post(
            url,
            json=test_data,
            headers={"Content-Type": "application/json"},
            stream=True,
            timeout=30
        )
        
        print(f"\n📊 Response status: {response.status_code}")
        
        if response.status_code == 200:
            print(f"✅ Server responded successfully")
            
            # Parse the streaming response
            response_data = None
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        try:
                            data = json.loads(line_str[6:])  # Remove 'data: ' prefix
                            if data.get('type') == 'content' and 'graph_data' in data:
                                response_data = data
                                break
                        except json.JSONDecodeError:
                            continue
            
            if response_data:
                print(f"🎯 Found response with graph data!")
                
                graph_data = response_data['graph_data']
                print(f"   Nodes: {len(graph_data.get('nodes', []))}")
                print(f"   Relationships: {len(graph_data.get('relationships', []))}")
                print(f"   Content: {response_data.get('content', '')[:100]}...")
                
                # Check if the key relationship is present
                relationships = graph_data.get('relationships', [])
                ceo_relationship_found = any(
                    rel.get('type') == 'CEO_OF' for rel in relationships
                )
                
                if ceo_relationship_found:
                    print(f"✅ Key relationship 'CEO_OF' found in graph data!")
                    print(f"🎯 Neo4j graph will be displayed in main chatroom!")
                    return True
                else:
                    print(f"⚠️ Key relationship not found in graph data")
                    return False
            else:
                print(f"❌ No graph data found in response")
                return False
        else:
            print(f"❌ Server error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"❌ Could not connect to web UI server at {url}")
        print(f"   Make sure the server is running with: cd web_ui && python app.py")
        return False
    except Exception as e:
        logger.error(f"Test failed: {e}")
        return False

def main():
    """Main test function."""
    
    print("WEB UI SERVER TEST")
    print("="*80)
    print("This test verifies that the Neo4j graph visualization")
    print("will be displayed in the main chatroom for relationship queries.")
    print("="*80)
    
    # Option 1: Test against running server
    print(f"\n🔍 Testing against running server...")
    success = test_web_ui_endpoint()
    
    if success:
        print(f"\n🏆 ✅ SUCCESS!")
        print(f"   The web UI server is properly configured to display")
        print(f"   Neo4j graph visualizations in the main chatroom.")
        print(f"   ")
        print(f"   To test manually:")
        print(f"   1. Start the web UI: cd web_ui && python app.py")
        print(f"   2. Open http://localhost:5000 in your browser")
        print(f"   3. Ask: \"what is the relation between 'Winfried Engelbrecht Bresges' and hkjc\"")
        print(f"   4. You should see a Neo4j graph visualization in the chat!")
    else:
        print(f"\n❌ Test failed or server not running")
        print(f"   To start the server manually:")
        print(f"   cd web_ui && python app.py")
    
    print(f"\n" + "="*80)

if __name__ == "__main__":
    main()
