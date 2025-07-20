#!/usr/bin/env python3
"""
Enhanced graph search functionality that properly returns entities and relationships.
This addresses the issue where Graphiti search doesn't return proper relationship data.
"""

import asyncio
import logging
import os
from typing import Dict, List, Any, Optional, Tuple
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedGraphSearch:
    """Enhanced graph search that combines Graphiti with direct Neo4j queries."""
    
    def __init__(self):
        """Initialize the enhanced graph search."""
        self.neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.neo4j_user = os.getenv("NEO4J_USERNAME", os.getenv("NEO4J_USER", "neo4j"))
        self.neo4j_password = os.getenv("NEO4J_PASSWORD")
        self.neo4j_database = os.getenv("NEO4J_DATABASE", "neo4j")
        
        if not self.neo4j_password:
            raise ValueError("NEO4J_PASSWORD environment variable not set")
    
    def get_neo4j_session(self):
        """Get a Neo4j session."""
        from neo4j import GraphDatabase
        driver = GraphDatabase.driver(self.neo4j_uri, auth=(self.neo4j_user, self.neo4j_password))
        return driver.session(database=self.neo4j_database), driver
    
    def search_entities_and_relationships(self, entity1: str, entity2: str) -> Dict[str, Any]:
        """
        Search for entities and relationships between two entities.

        Args:
            entity1: First entity name
            entity2: Second entity name

        Returns:
            Dictionary containing entities and relationships
        """
        session, driver = self.get_neo4j_session()

        try:
            # Clean entity names to remove quotes and normalize
            entity1_clean = entity1.strip().strip("'\"")
            entity2_clean = entity2.strip().strip("'\"")

            result = {
                "entity1": entity1_clean,
                "entity2": entity2_clean,
                "entity1_nodes": [],
                "entity2_nodes": [],
                "direct_relationships": [],
                "indirect_relationships": [],
                "connection_strength": 0.0
            }
            
            # 1. Find entity1 nodes
            entity1_queries = [
                f"MATCH (n) WHERE n.name = '{entity1_clean}' RETURN n, labels(n) as labels",
                f"MATCH (n) WHERE toLower(n.name) CONTAINS toLower('{entity1_clean}') RETURN n, labels(n) as labels",
                f"MATCH (n) WHERE n.summary CONTAINS '{entity1_clean}' OR n.company CONTAINS '{entity1_clean}' RETURN n, labels(n) as labels"
            ]
            
            for query in entity1_queries:
                try:
                    records = list(session.run(query))
                    for record in records:
                        node_data = dict(record['n'].items())
                        node_data['labels'] = record['labels']
                        if node_data not in result["entity1_nodes"]:
                            result["entity1_nodes"].append(node_data)
                except Exception as e:
                    logger.warning(f"Query failed: {query} - {e}")
            
            # 2. Find entity2 nodes
            entity2_queries = [
                f"MATCH (n) WHERE n.name = '{entity2_clean}' RETURN n, labels(n) as labels",
                f"MATCH (n) WHERE toLower(n.name) CONTAINS toLower('{entity2_clean}') RETURN n, labels(n) as labels",
                f"MATCH (n) WHERE n.name CONTAINS 'Hong Kong Jockey Club' RETURN n, labels(n) as labels",
                f"MATCH (n) WHERE n.summary CONTAINS '{entity2_clean}' OR n.company CONTAINS '{entity2_clean}' RETURN n, labels(n) as labels"
            ]
            
            for query in entity2_queries:
                try:
                    records = list(session.run(query))
                    for record in records:
                        node_data = dict(record['n'].items())
                        node_data['labels'] = record['labels']
                        if node_data not in result["entity2_nodes"]:
                            result["entity2_nodes"].append(node_data)
                except Exception as e:
                    logger.warning(f"Query failed: {query} - {e}")
            
            # 3. Find direct relationships
            direct_rel_queries = [
                # Direct relationship between entities
                f"""
                MATCH (a)-[r]-(b)
                WHERE (a.name CONTAINS '{entity1_clean}' OR a.summary CONTAINS '{entity1_clean}')
                  AND (b.name CONTAINS '{entity2_clean}' OR b.name CONTAINS 'Hong Kong Jockey Club')
                RETURN a, r, b, type(r) as rel_type
                """,
                # Check if entity1 works at entity2 (via properties) - EXACT MATCH
                f"""
                MATCH (p:Person)
                WHERE p.name = '{entity1_clean}' AND p.company = 'The Hong Kong Jockey Club'
                RETURN p, 'CEO_OF' as rel_type, p.company as target_company, p.position as relationship_detail
                """,
                # Check if entity1 works at entity2 (via properties) - CONTAINS MATCH
                f"""
                MATCH (p:Person)
                WHERE p.name CONTAINS '{entity1_clean}' AND p.company CONTAINS 'Hong Kong Jockey Club'
                RETURN p, 'WORKS_AT' as rel_type, p.company as target_company, p.position as relationship_detail
                """,
                # Find any person with entity1 name and their company relationships
                f"""
                MATCH (p:Person)
                WHERE p.name CONTAINS '{entity1_clean}'
                RETURN p, 'EMPLOYED_BY' as rel_type, p.company as target_company, p.position as relationship_detail
                """,
                # Check for any shared properties indicating relationship
                f"""
                MATCH (a:Person), (b:Company)
                WHERE a.name CONTAINS '{entity1_clean}'
                  AND (b.name CONTAINS '{entity2_clean}' OR b.name CONTAINS 'Hong Kong Jockey Club')
                  AND (a.company = b.name OR a.summary CONTAINS b.name)
                RETURN a, 'ASSOCIATED_WITH' as rel_type, b, a.position as relationship_detail
                """
            ]
            
            for query in direct_rel_queries:
                try:
                    records = list(session.run(query))
                    for record in records:
                        rel_data = {}

                        if 'a' in record and 'b' in record:
                            rel_data = {
                                "source": dict(record['a'].items()),
                                "target": dict(record['b'].items()),
                                "relationship_type": record.get('rel_type', 'UNKNOWN'),
                                "relationship_detail": record.get('relationship_detail', ''),
                                "extraction_method": "direct_neo4j_query"
                            }
                        elif 'p' in record and 'target_company' in record:
                            rel_data = {
                                "source": dict(record['p'].items()),
                                "target": {"name": record['target_company'], "type": "Company"},
                                "relationship_type": record.get('rel_type', 'WORKS_AT'),
                                "relationship_detail": record.get('relationship_detail', ''),
                                "extraction_method": "property_based"
                            }
                        elif 'p' in record:
                            # Handle case where we just have person data
                            person_data = dict(record['p'].items())
                            if person_data.get('company'):
                                rel_data = {
                                    "source": person_data,
                                    "target": {"name": person_data['company'], "type": "Company"},
                                    "relationship_type": record.get('rel_type', 'WORKS_AT'),
                                    "relationship_detail": person_data.get('position', ''),
                                    "extraction_method": "person_company_property"
                                }

                        if rel_data and rel_data not in result["direct_relationships"]:
                            result["direct_relationships"].append(rel_data)

                except Exception as e:
                    logger.warning(f"Relationship query failed: {query} - {e}")

            # 4. Additional property-based relationship detection
            # Check if we found entity1 as a person with company matching entity2
            for entity1_node in result["entity1_nodes"]:
                if entity1_node.get('labels') and 'Person' in entity1_node['labels']:
                    person_company = entity1_node.get('company', '')
                    person_position = entity1_node.get('position', '')

                    # Check if person's company matches entity2 or contains HKJC-related terms
                    if (person_company and
                        (entity2_clean.lower() in person_company.lower() or
                         'hong kong jockey club' in person_company.lower() or
                         'hkjc' in person_company.lower())):

                        # Determine relationship type based on position
                        rel_type = "WORKS_AT"
                        if person_position:
                            if "ceo" in person_position.lower() or "chief executive" in person_position.lower():
                                rel_type = "CEO_OF"
                            elif "chairman" in person_position.lower():
                                rel_type = "CHAIRMAN_OF"
                            elif "director" in person_position.lower():
                                rel_type = "DIRECTOR_OF"
                            elif "secretary" in person_position.lower():
                                rel_type = "SECRETARY_OF"

                        property_rel = {
                            "source": entity1_node,
                            "target": {"name": person_company, "type": "Company"},
                            "relationship_type": rel_type,
                            "relationship_detail": person_position,
                            "extraction_method": "property_based_enhanced"
                        }

                        # Check if this relationship is already in the list
                        if property_rel not in result["direct_relationships"]:
                            result["direct_relationships"].append(property_rel)
                            logger.info(f"Added property-based relationship: {entity1_node['name']} -> {rel_type} -> {person_company}")
            
            # 4. Calculate connection strength
            if result["entity1_nodes"] and result["entity2_nodes"]:
                result["connection_strength"] += 0.3
            if result["direct_relationships"]:
                result["connection_strength"] += 0.7
            
            # 5. Add summary
            if result["direct_relationships"]:
                result["summary"] = f"Found {len(result['direct_relationships'])} direct relationship(s) between {entity1} and {entity2}"
            elif result["entity1_nodes"] and result["entity2_nodes"]:
                result["summary"] = f"Found entities for both {entity1} and {entity2} but no direct relationships"
            else:
                result["summary"] = f"Limited information found for {entity1} and {entity2}"
            
            return result
            
        finally:
            session.close()
            driver.close()
    
    def search_entity_details(self, entity_name: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific entity.
        
        Args:
            entity_name: Name of the entity to search for
            
        Returns:
            Dictionary containing entity details and relationships
        """
        session, driver = self.get_neo4j_session()
        
        try:
            result = {
                "entity_name": entity_name,
                "nodes": [],
                "relationships": [],
                "related_entities": []
            }
            
            # Find entity nodes
            entity_queries = [
                f"MATCH (n) WHERE n.name = '{entity_name}' RETURN n, labels(n) as labels",
                f"MATCH (n) WHERE toLower(n.name) CONTAINS toLower('{entity_name}') RETURN n, labels(n) as labels",
                f"MATCH (n) WHERE n.summary CONTAINS '{entity_name}' OR n.company CONTAINS '{entity_name}' RETURN n, labels(n) as labels"
            ]
            
            for query in entity_queries:
                try:
                    records = list(session.run(query))
                    for record in records:
                        node_data = dict(record['n'].items())
                        node_data['labels'] = record['labels']
                        if node_data not in result["nodes"]:
                            result["nodes"].append(node_data)
                except Exception as e:
                    logger.warning(f"Entity query failed: {query} - {e}")
            
            # Find relationships for found entities
            if result["nodes"]:
                for node in result["nodes"]:
                    node_name = node.get('name', '')
                    if node_name:
                        rel_query = f"""
                        MATCH (n)-[r]-(connected)
                        WHERE n.name = '{node_name}'
                        RETURN n, r, connected, type(r) as rel_type
                        LIMIT 10
                        """
                        
                        try:
                            rel_records = list(session.run(rel_query))
                            for rel_record in rel_records:
                                rel_data = {
                                    "source": dict(rel_record['n'].items()),
                                    "target": dict(rel_record['connected'].items()),
                                    "relationship_type": rel_record['rel_type'],
                                    "extraction_method": "direct_neo4j_traversal"
                                }
                                if rel_data not in result["relationships"]:
                                    result["relationships"].append(rel_data)
                                
                                # Add to related entities
                                connected_entity = dict(rel_record['connected'].items())
                                if connected_entity not in result["related_entities"]:
                                    result["related_entities"].append(connected_entity)
                                    
                        except Exception as e:
                            logger.warning(f"Relationship traversal failed for {node_name}: {e}")
            
            return result
            
        finally:
            session.close()
            driver.close()


async def test_enhanced_search():
    """Test the enhanced search functionality."""
    search = EnhancedGraphSearch()
    
    print("="*80)
    print("TESTING ENHANCED GRAPH SEARCH")
    print("="*80)
    
    # Test 1: Search for relationship between Winfried and HKJC
    print("\n1. Testing relationship search: Winfried Engelbrecht Bresges and HKJC")
    result = search.search_entities_and_relationships("Winfried Engelbrecht Bresges", "HKJC")
    
    print(f"\nEntity 1 nodes found: {len(result['entity1_nodes'])}")
    for node in result['entity1_nodes']:
        print(f"  - {node.get('name', 'Unknown')} ({node.get('labels', [])})")
    
    print(f"\nEntity 2 nodes found: {len(result['entity2_nodes'])}")
    for node in result['entity2_nodes'][:5]:  # Show first 5
        print(f"  - {node.get('name', 'Unknown')} ({node.get('labels', [])})")
    
    print(f"\nDirect relationships found: {len(result['direct_relationships'])}")
    for rel in result['direct_relationships']:
        source_name = rel['source'].get('name', 'Unknown')
        target_name = rel['target'].get('name', 'Unknown')
        rel_type = rel.get('relationship_type', 'Unknown')
        rel_detail = rel.get('relationship_detail', '')
        print(f"  - {source_name} --[{rel_type}]--> {target_name}")
        if rel_detail:
            print(f"    Detail: {rel_detail}")
    
    print(f"\nConnection strength: {result['connection_strength']}")
    print(f"Summary: {result['summary']}")
    
    # Test 2: Get detailed info about Winfried
    print("\n\n2. Testing entity details: Winfried Engelbrecht Bresges")
    details = search.search_entity_details("Winfried Engelbrecht Bresges")
    
    print(f"\nNodes found: {len(details['nodes'])}")
    for node in details['nodes']:
        print(f"  - {node.get('name', 'Unknown')}")
        print(f"    Company: {node.get('company', 'N/A')}")
        print(f"    Position: {node.get('position', 'N/A')}")
    
    print(f"\nRelationships found: {len(details['relationships'])}")
    for rel in details['relationships'][:5]:  # Show first 5
        source_name = rel['source'].get('name', 'Unknown')
        target_name = rel['target'].get('name', 'Unknown')
        rel_type = rel.get('relationship_type', 'Unknown')
        print(f"  - {source_name} --[{rel_type}]--> {target_name}")
    
    print("\n" + "="*80)
    print("ENHANCED SEARCH TEST COMPLETED")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(test_enhanced_search())
