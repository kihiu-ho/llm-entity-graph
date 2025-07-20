#!/usr/bin/env python3
"""
Debug the current state of Neo4j database to understand the graph visualization issue.
"""

import asyncio
import logging
from dotenv import load_dotenv
from neo4j import GraphDatabase
import os

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def debug_neo4j_state():
    """Debug the current state of Neo4j database."""
    
    print("="*80)
    print("DEBUGGING NEO4J DATABASE STATE")
    print("="*80)
    
    # Get Neo4j connection details
    neo4j_uri = os.getenv('NEO4J_URI')
    neo4j_user = os.getenv('NEO4J_USERNAME')  # Fixed: was NEO4J_USER
    neo4j_password = os.getenv('NEO4J_PASSWORD')
    
    if not all([neo4j_uri, neo4j_user, neo4j_password]):
        print("❌ Missing Neo4j environment variables")
        return False
    
    print(f"🔗 Connecting to Neo4j: {neo4j_uri}")
    
    driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
    
    try:
        with driver.session() as session:
            
            # 1. Check all node labels
            print(f"\n🔍 1. Checking all node labels...")
            result = session.run("CALL db.labels()")
            labels = [record["label"] for record in result]
            print(f"   Available labels: {labels}")
            
            # 2. Check all relationship types
            print(f"\n🔍 2. Checking all relationship types...")
            result = session.run("CALL db.relationshipTypes()")
            rel_types = [record["relationshipType"] for record in result]
            print(f"   Available relationship types: {rel_types}")
            
            # 3. Count nodes by label
            print(f"\n🔍 3. Counting nodes by label...")
            for label in labels:
                result = session.run(f"MATCH (n:{label}) RETURN count(n) as count")
                count = result.single()["count"]
                print(f"   {label}: {count} nodes")
            
            # 4. Check for Entity nodes specifically
            print(f"\n🔍 4. Checking Entity nodes...")
            result = session.run("MATCH (n:Entity) RETURN n.name as name, labels(n) as labels LIMIT 10")
            entities = list(result)
            print(f"   Found {len(entities)} Entity nodes (showing first 10):")
            for entity in entities:
                print(f"      - {entity['name']} (labels: {entity['labels']})")
            
            # 5. Look for specific entities mentioned in the error
            print(f"\n🔍 5. Searching for specific entities...")
            
            # Search for Winfried Engelbrecht Bresges
            result = session.run("""
                MATCH (n)
                WHERE toLower(n.name) CONTAINS 'winfried'
                RETURN n.name as name, labels(n) as labels, n.uuid as uuid
            """)
            winfried_results = list(result)
            print(f"   Winfried search results: {len(winfried_results)}")
            for res in winfried_results:
                print(f"      - {res['name']} (labels: {res['labels']}, uuid: {res['uuid']})")
            
            # Search for Hong Kong Jockey Club / HKJC
            result = session.run("""
                MATCH (n)
                WHERE toLower(n.name) CONTAINS 'hong kong' OR toLower(n.name) CONTAINS 'hkjc'
                RETURN n.name as name, labels(n) as labels, n.uuid as uuid
            """)
            hkjc_results = list(result)
            print(f"   HKJC search results: {len(hkjc_results)}")
            for res in hkjc_results:
                print(f"      - {res['name']} (labels: {res['labels']}, uuid: {res['uuid']})")
            
            # 6. Check relationships between these entities
            print(f"\n🔍 6. Checking relationships...")
            if winfried_results and hkjc_results:
                winfried_uuid = winfried_results[0]['uuid']
                hkjc_uuid = hkjc_results[0]['uuid']
                
                result = session.run("""
                    MATCH (a {uuid: $uuid1})-[r]-(b {uuid: $uuid2})
                    RETURN type(r) as rel_type, r.name as rel_name, r.fact as fact
                """, uuid1=winfried_uuid, uuid2=hkjc_uuid)
                
                relationships = list(result)
                print(f"   Direct relationships: {len(relationships)}")
                for rel in relationships:
                    print(f"      - {rel['rel_type']}: {rel['rel_name']} ({rel['fact']})")
                
                # Check indirect relationships (2 hops)
                result = session.run("""
                    MATCH (a {uuid: $uuid1})-[r1]-(intermediate)-[r2]-(b {uuid: $uuid2})
                    RETURN intermediate.name as intermediate_name, 
                           type(r1) as rel1_type, r1.name as rel1_name,
                           type(r2) as rel2_type, r2.name as rel2_name
                    LIMIT 5
                """, uuid1=winfried_uuid, uuid2=hkjc_uuid)
                
                indirect_rels = list(result)
                print(f"   Indirect relationships (2 hops): {len(indirect_rels)}")
                for rel in indirect_rels:
                    print(f"      - Via {rel['intermediate_name']}: {rel['rel1_type']}({rel['rel1_name']}) -> {rel['rel2_type']}({rel['rel2_name']})")
            
            # 7. Check properties available on Entity nodes
            print(f"\n🔍 7. Checking Entity node properties...")
            result = session.run("""
                MATCH (n:Entity)
                WITH n, keys(n) as props
                UNWIND props as prop
                RETURN DISTINCT prop
                ORDER BY prop
            """)
            properties = [record["prop"] for record in result]
            print(f"   Available properties on Entity nodes: {properties}")
            
            # 8. Sample Entity node with all properties
            print(f"\n🔍 8. Sample Entity node structure...")
            result = session.run("MATCH (n:Entity) RETURN n LIMIT 1")
            sample = result.single()
            if sample:
                node = sample["n"]
                print(f"   Sample Entity node:")
                print(f"      Labels: {list(node.labels)}")
                print(f"      Properties: {dict(node)}")
            
            print(f"\n✅ Neo4j state analysis complete!")
            return True
            
    except Exception as e:
        print(f"❌ Error analyzing Neo4j state: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        driver.close()

if __name__ == "__main__":
    success = asyncio.run(debug_neo4j_state())
    
    print(f"\n🎯 NEO4J DEBUG RESULT: {'SUCCESS' if success else 'FAILED'}")
