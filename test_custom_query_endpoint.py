#!/usr/bin/env python3
"""
Test script for the custom Neo4j query endpoint.
"""

import requests
import json
import sys

def test_custom_query_endpoint():
    """Test the custom Neo4j query endpoint."""
    
    # Test endpoint URL
    url = "http://localhost:5001/api/graph/neo4j/custom"
    
    # Test query
    test_query = "MATCH (n) WHERE n.name CONTAINS 'Winfried Engelbrecht Bresges' RETURN n, labels(n) as labels, properties(n) as props LIMIT 10"
    
    # Request payload
    payload = {
        "query": test_query,
        "limit": 50
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    print(f"🔍 Testing custom query endpoint...")
    print(f"URL: {url}")
    print(f"Query: {test_query}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print("-" * 50)
    
    try:
        # Make the request
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        print(f"Response Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Success!")
            print(f"Nodes: {len(result.get('nodes', []))}")
            print(f"Relationships: {len(result.get('relationships', []))}")
            print(f"Query Time: {result.get('query_time', 'N/A')}")
            
            # Print first few nodes
            nodes = result.get('nodes', [])
            if nodes:
                print("\nFirst few nodes:")
                for i, node in enumerate(nodes[:3]):
                    print(f"  Node {i+1}: {node.get('properties', {}).get('name', 'Unknown')} ({node.get('labels', [])})")
            
            return True
            
        else:
            print("❌ Error!")
            print(f"Response Text: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Could not connect to the server.")
        print("Make sure the web UI server is running on localhost:5001")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        return False

if __name__ == "__main__":
    success = test_custom_query_endpoint()
    sys.exit(0 if success else 1)
