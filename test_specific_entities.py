#!/usr/bin/env python3
"""
Test script to check what data exists in Neo4j for specific entities.
This will help debug the graph search issue.
"""

import logging
import os
from typing import Dict, List, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_specific_entities():
    """Test what data exists for Winfried Engelbrecht Bresges and HKJC."""

    try:
        # Direct Neo4j import
        from neo4j import GraphDatabase

        # Get Neo4j configuration from environment
        neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        neo4j_user = os.getenv("NEO4J_USERNAME", os.getenv("NEO4J_USER", "neo4j"))
        neo4j_password = os.getenv("NEO4J_PASSWORD")
        neo4j_database = os.getenv("NEO4J_DATABASE", "neo4j")

        if not neo4j_password:
            print("ERROR: NEO4J_PASSWORD environment variable not set")
            return

        # Create driver and session
        driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
        session = driver.session(database=neo4j_database)
        
        print("="*80)
        print("TESTING SPECIFIC ENTITIES IN NEO4J")
        print("="*80)
        
        # Test 1: Search for Winfried Engelbrecht Bresges
        print("\n1. Searching for 'Winfried Engelbrecht Bresges'...")
        
        winfried_queries = [
            # Exact name match
            "MATCH (n) WHERE n.name = 'Winfried Engelbrecht Bresges' RETURN n, labels(n) as labels",
            # Case insensitive contains
            "MATCH (n) WHERE toLower(n.name) CONTAINS 'winfried' RETURN n, labels(n) as labels",
            # Partial name match
            "MATCH (n) WHERE n.name CONTAINS 'Bresges' RETURN n, labels(n) as labels",
            # Summary or company contains
            "MATCH (n) WHERE n.summary CONTAINS 'Winfried' OR n.company CONTAINS 'Winfried' RETURN n, labels(n) as labels"
        ]
        
        winfried_found = False
        for i, query in enumerate(winfried_queries):
            print(f"\n  Query {i+1}: {query}")
            result = session.run(query)
            records = list(result)
            if records:
                winfried_found = True
                print(f"  ✓ Found {len(records)} results:")
                for record in records:
                    node = record['n']
                    labels = record['labels']
                    print(f"    - Node: {dict(node.items())}")
                    print(f"      Labels: {labels}")
            else:
                print(f"  ✗ No results")
        
        if not winfried_found:
            print("\n  ⚠️ No nodes found for Winfried Engelbrecht Bresges")
        
        # Test 2: Search for HKJC
        print("\n\n2. Searching for 'HKJC'...")
        
        hkjc_queries = [
            # Exact name match
            "MATCH (n) WHERE n.name = 'HKJC' RETURN n, labels(n) as labels",
            # Case insensitive contains
            "MATCH (n) WHERE toLower(n.name) CONTAINS 'hkjc' RETURN n, labels(n) as labels",
            # Full name variations
            "MATCH (n) WHERE n.name CONTAINS 'Hong Kong Jockey Club' RETURN n, labels(n) as labels",
            # Summary or company contains
            "MATCH (n) WHERE n.summary CONTAINS 'HKJC' OR n.company CONTAINS 'HKJC' RETURN n, labels(n) as labels"
        ]
        
        hkjc_found = False
        for i, query in enumerate(hkjc_queries):
            print(f"\n  Query {i+1}: {query}")
            result = session.run(query)
            records = list(result)
            if records:
                hkjc_found = True
                print(f"  ✓ Found {len(records)} results:")
                for record in records:
                    node = record['n']
                    labels = record['labels']
                    print(f"    - Node: {dict(node.items())}")
                    print(f"      Labels: {labels}")
            else:
                print(f"  ✗ No results")
        
        if not hkjc_found:
            print("\n  ⚠️ No nodes found for HKJC")
        
        # Test 3: Search for any relationships between them
        print("\n\n3. Searching for relationships between Winfried and HKJC...")
        
        relationship_queries = [
            # Direct relationship
            """
            MATCH (a)-[r]-(b) 
            WHERE (a.name CONTAINS 'Winfried' OR a.name CONTAINS 'Bresges') 
              AND (b.name CONTAINS 'HKJC' OR b.name CONTAINS 'Hong Kong Jockey Club')
            RETURN a, r, b, type(r) as rel_type
            """,
            # Indirect relationship (2 hops)
            """
            MATCH path = (a)-[*1..2]-(b) 
            WHERE (a.name CONTAINS 'Winfried' OR a.name CONTAINS 'Bresges') 
              AND (b.name CONTAINS 'HKJC' OR b.name CONTAINS 'Hong Kong Jockey Club')
            RETURN path, length(path) as path_length
            """,
            # Any path between them
            """
            MATCH (a), (b)
            WHERE (a.name CONTAINS 'Winfried' OR a.name CONTAINS 'Bresges') 
              AND (b.name CONTAINS 'HKJC' OR b.name CONTAINS 'Hong Kong Jockey Club')
            MATCH path = shortestPath((a)-[*]-(b))
            RETURN path, length(path) as path_length
            """
        ]
        
        relationships_found = False
        for i, query in enumerate(relationship_queries):
            print(f"\n  Query {i+1}:")
            print(f"  {query}")
            try:
                result = session.run(query)
                records = list(result)
                if records:
                    relationships_found = True
                    print(f"  ✓ Found {len(records)} relationship(s):")
                    for record in records:
                        if 'path' in record:
                            path = record['path']
                            print(f"    - Path length: {record['path_length']}")
                            print(f"      Nodes: {[dict(node.items()) for node in path.nodes]}")
                            print(f"      Relationships: {[rel.type for rel in path.relationships]}")
                        else:
                            print(f"    - From: {dict(record['a'].items())}")
                            print(f"      Relationship: {record['rel_type']}")
                            print(f"      To: {dict(record['b'].items())}")
                else:
                    print(f"  ✗ No relationships found")
            except Exception as e:
                print(f"  ✗ Query failed: {e}")
        
        if not relationships_found:
            print("\n  ⚠️ No relationships found between Winfried and HKJC")
        
        # Test 4: General database statistics
        print("\n\n4. General database statistics...")
        
        stats_queries = [
            "MATCH (n) RETURN count(n) as total_nodes",
            "MATCH ()-[r]->() RETURN count(r) as total_relationships",
            "MATCH (n) RETURN DISTINCT labels(n) as node_labels, count(n) as count ORDER BY count DESC",
            "MATCH ()-[r]->() RETURN DISTINCT type(r) as rel_type, count(r) as count ORDER BY count DESC LIMIT 10"
        ]
        
        for query in stats_queries:
            print(f"\n  {query}")
            result = session.run(query)
            records = list(result)
            for record in records:
                print(f"    {dict(record.items())}")
        
        # Test 5: Sample nodes with names containing key terms
        print("\n\n5. Sample nodes with relevant names...")
        
        sample_queries = [
            "MATCH (n) WHERE n.name CONTAINS 'Hong Kong' RETURN n.name, labels(n) LIMIT 5",
            "MATCH (n) WHERE n.name CONTAINS 'Jockey' RETURN n.name, labels(n) LIMIT 5",
            "MATCH (n) WHERE n.name CONTAINS 'Club' RETURN n.name, labels(n) LIMIT 5",
            "MATCH (n:Person) RETURN n.name LIMIT 10",
            "MATCH (n:Company) RETURN n.name LIMIT 10"
        ]
        
        for query in sample_queries:
            print(f"\n  {query}")
            result = session.run(query)
            records = list(result)
            if records:
                for record in records:
                    print(f"    {dict(record.items())}")
            else:
                print("    No results")
        
        print("\n" + "="*80)
        print("TEST COMPLETED")
        print("="*80)

        session.close()
        driver.close()

    except Exception as e:
        logger.error(f"Test failed: {e}")
        raise

if __name__ == "__main__":
    test_specific_entities()
