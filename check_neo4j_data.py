#!/usr/bin/env python3
"""
Check what data actually exists in the Neo4j database.
"""

import logging
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_neo4j_data():
    """Check what data exists in Neo4j."""
    
    try:
        from neo4j import GraphDatabase
        
        # Get Neo4j configuration from environment
        neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        neo4j_user = os.getenv("NEO4J_USERNAME", os.getenv("NEO4J_USER", "neo4j"))
        neo4j_password = os.getenv("NEO4J_PASSWORD")
        neo4j_database = os.getenv("NEO4J_DATABASE", "neo4j")
        
        # Create driver and session
        driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
        session = driver.session(database=neo4j_database)
        
        print("="*80)
        print("CHECKING NEO4J DATABASE CONTENT")
        print("="*80)
        
        # 1. Check all node labels
        print("\n1. All node labels:")
        labels_query = "CALL db.labels()"
        result = session.run(labels_query)
        labels = [record["label"] for record in result]
        print(f"   Labels found: {labels}")
        
        # 2. Count nodes by label
        print("\n2. Node counts by label:")
        for label in labels:
            count_query = f"MATCH (n:{label}) RETURN count(n) as count"
            result = session.run(count_query)
            count = result.single()["count"]
            print(f"   {label}: {count} nodes")
        
        # 3. Sample Person nodes
        print("\n3. Sample Person nodes:")
        person_query = "MATCH (p:Person) RETURN p.name, p.company, p.position LIMIT 10"
        result = session.run(person_query)
        records = list(result)
        
        if records:
            for record in records:
                name = record.get("p.name", "Unknown")
                company = record.get("p.company", "Unknown")
                position = record.get("p.position", "Unknown")
                print(f"   - {name} | {company} | {position}")
        else:
            print("   No Person nodes found")
        
        # 4. Sample Company nodes
        print("\n4. Sample Company nodes:")
        company_query = "MATCH (c:Company) RETURN c.name, c.industry LIMIT 10"
        result = session.run(company_query)
        records = list(result)
        
        if records:
            for record in records:
                name = record.get("c.name", "Unknown")
                industry = record.get("c.industry", "Unknown")
                print(f"   - {name} | {industry}")
        else:
            print("   No Company nodes found")
        
        # 5. Search for any nodes containing "Winfried"
        print("\n5. Searching for 'Winfried':")
        winfried_query = "MATCH (n) WHERE n.name CONTAINS 'Winfried' OR n.summary CONTAINS 'Winfried' RETURN n, labels(n) as labels"
        result = session.run(winfried_query)
        records = list(result)
        
        if records:
            for record in records:
                node_data = dict(record['n'].items())
                labels = record['labels']
                print(f"   - Labels: {labels}")
                print(f"     Name: {node_data.get('name', 'Unknown')}")
                print(f"     Summary: {node_data.get('summary', 'No summary')[:100]}...")
        else:
            print("   No nodes found containing 'Winfried'")
        
        # 6. Search for any nodes containing "HKJC" or "Hong Kong Jockey"
        print("\n6. Searching for 'HKJC' or 'Hong Kong Jockey':")
        hkjc_query = """
        MATCH (n) 
        WHERE n.name CONTAINS 'HKJC' 
           OR n.name CONTAINS 'Hong Kong Jockey' 
           OR n.summary CONTAINS 'HKJC'
           OR n.summary CONTAINS 'Hong Kong Jockey'
           OR n.company CONTAINS 'Hong Kong Jockey'
        RETURN n, labels(n) as labels
        """
        result = session.run(hkjc_query)
        records = list(result)
        
        if records:
            for record in records:
                node_data = dict(record['n'].items())
                labels = record['labels']
                print(f"   - Labels: {labels}")
                print(f"     Name: {node_data.get('name', 'Unknown')}")
                print(f"     Company: {node_data.get('company', 'Unknown')}")
                print(f"     Summary: {node_data.get('summary', 'No summary')[:100]}...")
        else:
            print("   No nodes found containing 'HKJC' or 'Hong Kong Jockey'")
        
        # 7. Check for any relationships
        print("\n7. Sample relationships:")
        rel_query = "MATCH (a)-[r]->(b) RETURN type(r) as rel_type, a.name as source, b.name as target LIMIT 10"
        result = session.run(rel_query)
        records = list(result)
        
        if records:
            for record in records:
                rel_type = record.get("rel_type", "Unknown")
                source = record.get("source", "Unknown")
                target = record.get("target", "Unknown")
                print(f"   - {source} --[{rel_type}]--> {target}")
        else:
            print("   No relationships found")
        
        session.close()
        driver.close()
        
    except Exception as e:
        logger.error(f"Check failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_neo4j_data()
