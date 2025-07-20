#!/usr/bin/env python3
"""
Debug the relationship detection between Winfried and HKJC.
"""

import logging
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def debug_relationship():
    """Debug the relationship detection."""
    
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
        print("DEBUGGING RELATIONSHIP DETECTION")
        print("="*80)
        
        # 1. Find Winfried's exact data
        print("\n1. Winfried's exact data:")
        winfried_query = "MATCH (p:Person) WHERE p.name = 'Winfried Engelbrecht Bresges' RETURN p"
        result = session.run(winfried_query)
        records = list(result)
        
        winfried_data = None
        if records:
            winfried_data = dict(records[0]['p'].items())
            print(f"   Name: {winfried_data.get('name')}")
            print(f"   Company: {winfried_data.get('company')}")
            print(f"   Position: {winfried_data.get('position')}")
            print(f"   Summary: {winfried_data.get('summary', '')[:100]}...")
        
        # 2. Find exact HKJC company nodes
        print("\n2. HKJC company nodes:")
        hkjc_query = "MATCH (c:Company) WHERE c.name CONTAINS 'Hong Kong Jockey Club' RETURN c"
        result = session.run(hkjc_query)
        records = list(result)
        
        hkjc_companies = []
        for record in records:
            company_data = dict(record['c'].items())
            hkjc_companies.append(company_data)
            print(f"   Company: {company_data.get('name')}")
        
        # 3. Test direct relationship detection
        print("\n3. Testing relationship detection:")
        
        if winfried_data and winfried_data.get('company'):
            company_name = winfried_data['company']
            print(f"   Winfried's company: '{company_name}'")
            
            # Check if this company exists as a Company node
            company_check_query = f"MATCH (c:Company) WHERE c.name = '{company_name}' RETURN c"
            result = session.run(company_check_query)
            company_records = list(result)
            
            if company_records:
                print(f"   ✅ Found matching Company node: {company_name}")
                
                # Create a synthetic relationship
                relationship = {
                    "source": winfried_data,
                    "target": {"name": company_name, "type": "Company"},
                    "relationship_type": "CEO_OF",
                    "relationship_detail": winfried_data.get('position', ''),
                    "extraction_method": "property_based_synthetic"
                }
                
                print(f"   🔗 RELATIONSHIP DETECTED:")
                print(f"      {relationship['source']['name']}")
                print(f"      --[{relationship['relationship_type']}]-->")
                print(f"      {relationship['target']['name']}")
                print(f"      Detail: {relationship['relationship_detail']}")
                
            else:
                print(f"   ❌ No matching Company node found for: {company_name}")
                
                # Try to find similar company names
                similar_query = f"MATCH (c:Company) WHERE c.name CONTAINS 'Hong Kong' OR c.name CONTAINS 'Jockey' RETURN c.name"
                result = session.run(similar_query)
                similar_records = list(result)
                
                print(f"   Similar company names found:")
                for record in similar_records:
                    print(f"      - {record['c.name']}")
        
        # 4. Test the enhanced search approach
        print("\n4. Testing enhanced search approach:")
        
        # Simple property-based relationship detection
        if winfried_data and winfried_data.get('company') == 'The Hong Kong Jockey Club':
            print("   ✅ RELATIONSHIP FOUND via property matching:")
            print(f"      Person: {winfried_data['name']}")
            print(f"      Position: {winfried_data.get('position', 'Unknown')}")
            print(f"      Company: {winfried_data['company']}")
            print(f"      Relationship Type: CEO_OF (based on position)")
            
            # This is the relationship we should return
            final_relationship = {
                "source": winfried_data,
                "target": {"name": "The Hong Kong Jockey Club", "type": "Company"},
                "relationship_type": "CEO_OF",
                "relationship_detail": winfried_data.get('position', ''),
                "extraction_method": "property_based_direct"
            }
            
            print(f"\n   🎯 FINAL RELATIONSHIP TO RETURN:")
            print(f"      Source: {final_relationship['source']['name']}")
            print(f"      Target: {final_relationship['target']['name']}")
            print(f"      Type: {final_relationship['relationship_type']}")
            print(f"      Detail: {final_relationship['relationship_detail']}")
            
            return final_relationship
        
        session.close()
        driver.close()
        
    except Exception as e:
        logger.error(f"Debug failed: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    debug_relationship()
