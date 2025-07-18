#!/usr/bin/env python3
"""
Script to fix duplicate entity nodes and clean up the Neo4j database.
Specifically addresses the Winfried Engelbrecht Bresges duplicate issue.
"""

import os
import sys
import asyncio
from typing import List, Dict, Any
from neo4j import GraphDatabase
from difflib import SequenceMatcher

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def get_neo4j_connection():
    """Get Neo4j connection from environment variables."""
    neo4j_uri = os.getenv('NEO4J_URI', 'neo4j+s://41654f35.databases.neo4j.io')
    neo4j_user = os.getenv('NEO4J_USERNAME', 'neo4j')
    neo4j_password = os.getenv('NEO4J_PASSWORD', 'os_erUj0BtJ3c-MQ-hbNBUsRIkGRlIl1jqMF2ggZmPc')
    
    return GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))

def similarity(a: str, b: str) -> float:
    """Calculate similarity between two strings."""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def normalize_name(name: str) -> str:
    """Normalize a name for comparison."""
    # Remove extra spaces, normalize hyphens vs spaces
    normalized = name.strip()
    # Convert "Engelbrecht Bresges" to "Engelbrecht-Bresges" for consistency
    if "Engelbrecht Bresges" in normalized:
        normalized = normalized.replace("Engelbrecht Bresges", "Engelbrecht-Bresges")
    return normalized

def find_duplicate_entities(driver) -> Dict[str, List[Dict]]:
    """Find duplicate entities in the database."""
    duplicates = {}
    
    with driver.session() as session:
        # Get all Person and Company nodes
        query = """
        MATCH (n)
        WHERE 'Person' IN labels(n) OR 'Company' IN labels(n)
        RETURN elementId(n) as id, n.name as name, labels(n) as labels, n as node
        ORDER BY n.name
        """
        
        result = session.run(query)
        nodes = list(result)
        
        print(f"Found {len(nodes)} Person/Company nodes")
        
        # Group similar names
        for i, node1 in enumerate(nodes):
            name1 = node1['name']
            if not name1:
                continue
                
            group_key = normalize_name(name1)
            if group_key not in duplicates:
                duplicates[group_key] = []
            
            # Check if this node is already in a group
            already_grouped = False
            for existing_group in duplicates.values():
                for existing_node in existing_group:
                    if existing_node['id'] == node1['id']:
                        already_grouped = True
                        break
                if already_grouped:
                    break
            
            if not already_grouped:
                duplicates[group_key].append(node1)
            
            # Look for similar names
            for j, node2 in enumerate(nodes[i+1:], i+1):
                name2 = node2['name']
                if not name2:
                    continue
                
                # Check similarity
                if similarity(name1, name2) > 0.85:  # 85% similarity threshold
                    # Check if node2 is already grouped
                    node2_grouped = False
                    for existing_group in duplicates.values():
                        for existing_node in existing_group:
                            if existing_node['id'] == node2['id']:
                                node2_grouped = True
                                break
                        if node2_grouped:
                            break
                    
                    if not node2_grouped:
                        duplicates[group_key].append(node2)
    
    # Filter out groups with only one node
    return {k: v for k, v in duplicates.items() if len(v) > 1}

def merge_duplicate_nodes(driver, duplicates: Dict[str, List[Dict]]):
    """Merge duplicate nodes."""
    with driver.session() as session:
        for group_name, nodes in duplicates.items():
            if len(nodes) <= 1:
                continue
                
            print(f"\n🔄 Processing duplicate group: {group_name}")
            print(f"   Found {len(nodes)} duplicate nodes:")
            for node in nodes:
                print(f"   - {node['name']} (ID: {node['id']}, Labels: {node['labels']})")
            
            # Choose the "primary" node (first one, or one with most relationships)
            primary_node = nodes[0]
            duplicate_nodes = nodes[1:]
            
            print(f"   Primary node: {primary_node['name']} (ID: {primary_node['id']})")
            
            # For each duplicate node, transfer its relationships to the primary
            for dup_node in duplicate_nodes:
                print(f"   Merging {dup_node['name']} into primary...")
                
                # Transfer incoming relationships
                transfer_incoming_query = """
                MATCH (dup) WHERE elementId(dup) = $dup_id
                MATCH (primary) WHERE elementId(primary) = $primary_id
                MATCH (other)-[r]->(dup)
                WHERE elementId(other) <> $primary_id AND elementId(other) <> $dup_id
                WITH other, r, primary, type(r) as rel_type, properties(r) as rel_props
                MERGE (other)-[new_r:RELATES_TO]->(primary)
                SET new_r = rel_props
                DELETE r
                """

                # Transfer outgoing relationships
                transfer_outgoing_query = """
                MATCH (dup) WHERE elementId(dup) = $dup_id
                MATCH (primary) WHERE elementId(primary) = $primary_id
                MATCH (dup)-[r]->(other)
                WHERE elementId(other) <> $primary_id AND elementId(other) <> $dup_id
                WITH dup, r, other, primary, type(r) as rel_type, properties(r) as rel_props
                MERGE (primary)-[new_r:RELATES_TO]->(other)
                SET new_r = rel_props
                DELETE r
                """

                # Delete any remaining relationships to/from the duplicate node
                delete_relationships_query = """
                MATCH (dup) WHERE elementId(dup) = $dup_id
                MATCH (dup)-[r]-()
                DELETE r
                """

                # Execute transfers and cleanup
                session.run(transfer_incoming_query,
                           dup_id=dup_node['id'],
                           primary_id=primary_node['id'])
                session.run(transfer_outgoing_query,
                           dup_id=dup_node['id'],
                           primary_id=primary_node['id'])
                session.run(delete_relationships_query,
                           dup_id=dup_node['id'])

                # Delete the duplicate node
                delete_query = """
                MATCH (dup) WHERE elementId(dup) = $dup_id
                DELETE dup
                """
                session.run(delete_query, dup_id=dup_node['id'])
                
                print(f"   ✅ Merged and deleted {dup_node['name']}")

def remove_entity_labels(driver):
    """Remove Entity labels from Person and Company nodes."""
    with driver.session() as session:
        # Remove Entity label from Person nodes
        query_person = """
        MATCH (n:Entity:Person)
        REMOVE n:Entity
        RETURN count(n) as count
        """
        
        result = session.run(query_person)
        person_count = result.single()['count']
        print(f"✅ Removed Entity label from {person_count} Person nodes")
        
        # Remove Entity label from Company nodes
        query_company = """
        MATCH (n:Entity:Company)
        REMOVE n:Entity
        RETURN count(n) as count
        """
        
        result = session.run(query_company)
        company_count = result.single()['count']
        print(f"✅ Removed Entity label from {company_count} Company nodes")

def remove_self_relationships(driver):
    """Remove self-referencing relationships."""
    with driver.session() as session:
        query = """
        MATCH (n)-[r]->(n)
        DELETE r
        RETURN count(r) as count
        """
        
        result = session.run(query)
        count = result.single()['count']
        print(f"✅ Removed {count} self-referencing relationships")

def main():
    """Main function to fix duplicate entities."""
    print("🚀 Starting entity cleanup process...")
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    driver = get_neo4j_connection()
    
    try:
        # Step 1: Find duplicates
        print("\n📊 Step 1: Finding duplicate entities...")
        duplicates = find_duplicate_entities(driver)
        
        if not duplicates:
            print("✅ No duplicates found!")
        else:
            print(f"Found {len(duplicates)} groups of duplicates:")
            for group_name, nodes in duplicates.items():
                print(f"  - {group_name}: {len(nodes)} nodes")
        
        # Step 2: Merge duplicates
        if duplicates:
            print("\n🔄 Step 2: Merging duplicate entities...")
            merge_duplicate_nodes(driver, duplicates)
        
        # Step 3: Remove Entity labels
        print("\n🏷️ Step 3: Removing Entity labels...")
        remove_entity_labels(driver)
        
        # Step 4: Remove self-relationships
        print("\n🔗 Step 4: Removing self-relationships...")
        remove_self_relationships(driver)
        
        print("\n✅ Entity cleanup completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")
        import traceback
        traceback.print_exc()
    finally:
        driver.close()

if __name__ == "__main__":
    main()
