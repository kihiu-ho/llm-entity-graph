#!/usr/bin/env python3
"""
Check the HKJC node summary for CEO information.
"""

import logging
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_hkjc_summary():
    """Check the HKJC node summary."""
    
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
        print("CHECKING HKJC NODE SUMMARY")
        print("="*80)
        
        # Search for HKJC node
        query = """
        MATCH (n)
        WHERE n.name CONTAINS 'Hong Kong Jockey Club'
        RETURN n.name as name, n.summary as summary, labels(n) as labels
        """
        
        result = session.run(query)
        records = list(result)
        
        for record in records:
            name = record.get("name", "Unknown")
            summary = record.get("summary", "No summary")
            labels = record.get("labels", [])
            
            print(f"\nNode: {name}")
            print(f"Labels: {labels}")
            print(f"Summary: {summary}")
            
            # Check if summary contains CEO information
            if "ceo" in summary.lower() or "chief executive" in summary.lower():
                print("✅ Contains CEO information!")
            else:
                print("❌ No CEO information found")
            
            # Check for Winfried mentions
            if "winfried" in summary.lower():
                print("✅ Contains Winfried mention!")
            else:
                print("❌ No Winfried mention")
        
        session.close()
        driver.close()
        
    except Exception as e:
        logger.error(f"Check failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_hkjc_summary()
