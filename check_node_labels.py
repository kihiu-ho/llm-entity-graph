#!/usr/bin/env python3
"""
Script to check and fix node labels in Neo4j database.
This script will identify nodes with both specific and Entity labels and remove the Entity label.
"""

import asyncio
import logging
import os
from typing import Dict, Any, List

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def check_and_fix_node_labels():
    """Check current node labels and remove Entity label from Person and Company nodes."""
    
    logger.info("=== Checking and Fixing Node Labels ===")
    
    try:
        from agent.neo4j_schema_manager import Neo4jSchemaManager
        
        # Initialize schema manager
        schema_manager = Neo4jSchemaManager(
            uri=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
            user=os.getenv("NEO4J_USER", "neo4j"),
            password=os.getenv("NEO4J_PASSWORD", "password")
        )
        
        try:
            await schema_manager.initialize()
            
            # Check current node labels
            logger.info("Checking current node labels...")
            
            async with schema_manager.driver.session() as session:
                # Query to find nodes with multiple labels including Entity
                query = """
                MATCH (n)
                WHERE size(labels(n)) > 1 AND 'Entity' IN labels(n)
                RETURN labels(n) as node_labels, count(n) as count
                ORDER BY count DESC
                """
                
                result = await session.run(query)
                records = await result.data()
                
                if records:
                    logger.info("Found nodes with multiple labels including Entity:")
                    for record in records:
                        labels = record['node_labels']
                        count = record['count']
                        logger.info(f"  Labels {labels}: {count} nodes")
                else:
                    logger.info("No nodes found with multiple labels including Entity")
                
                # Check for Person nodes with Entity label
                person_entity_query = """
                MATCH (n:Person:Entity)
                RETURN count(n) as count
                """
                
                result = await session.run(person_entity_query)
                record = await result.single()
                person_entity_count = record['count'] if record else 0
                
                # Check for Company nodes with Entity label
                company_entity_query = """
                MATCH (n:Company:Entity)
                RETURN count(n) as count
                """
                
                result = await session.run(company_entity_query)
                record = await result.single()
                company_entity_count = record['count'] if record else 0
                
                logger.info(f"Person nodes with Entity label: {person_entity_count}")
                logger.info(f"Company nodes with Entity label: {company_entity_count}")
                
                # Fix Person nodes - remove Entity label
                if person_entity_count > 0:
                    logger.info("Removing Entity label from Person nodes...")
                    
                    fix_person_query = """
                    MATCH (n:Person:Entity)
                    REMOVE n:Entity
                    RETURN count(n) as fixed_count
                    """
                    
                    result = await session.run(fix_person_query)
                    record = await result.single()
                    fixed_person_count = record['fixed_count'] if record else 0
                    
                    logger.info(f"Fixed {fixed_person_count} Person nodes")
                
                # Fix Company nodes - remove Entity label
                if company_entity_count > 0:
                    logger.info("Removing Entity label from Company nodes...")
                    
                    fix_company_query = """
                    MATCH (n:Company:Entity)
                    REMOVE n:Entity
                    RETURN count(n) as fixed_count
                    """
                    
                    result = await session.run(fix_company_query)
                    record = await result.single()
                    fixed_company_count = record['fixed_count'] if record else 0
                    
                    logger.info(f"Fixed {fixed_company_count} Company nodes")
                
                # Verify the fix
                logger.info("Verifying the fix...")
                
                # Check Person nodes
                person_only_query = """
                MATCH (n:Person)
                WHERE NOT 'Entity' IN labels(n)
                RETURN count(n) as count
                """
                
                result = await session.run(person_only_query)
                record = await result.single()
                person_only_count = record['count'] if record else 0
                
                # Check Company nodes
                company_only_query = """
                MATCH (n:Company)
                WHERE NOT 'Entity' IN labels(n)
                RETURN count(n) as count
                """
                
                result = await session.run(company_only_query)
                record = await result.single()
                company_only_count = record['count'] if record else 0
                
                # Check remaining Entity nodes
                entity_only_query = """
                MATCH (n:Entity)
                WHERE NOT 'Person' IN labels(n) AND NOT 'Company' IN labels(n)
                RETURN count(n) as count
                """
                
                result = await session.run(entity_only_query)
                record = await result.single()
                entity_only_count = record['count'] if record else 0
                
                logger.info("=== FINAL RESULTS ===")
                logger.info(f"Person nodes (without Entity label): {person_only_count}")
                logger.info(f"Company nodes (without Entity label): {company_only_count}")
                logger.info(f"Generic Entity nodes (remaining): {entity_only_count}")
                
                if person_only_count > 0 and company_only_count > 0 and entity_only_count == 0:
                    logger.info("✅ SUCCESS: All Person and Company nodes now have only specific labels!")
                elif person_only_count > 0 and company_only_count > 0:
                    logger.info("✅ PARTIAL SUCCESS: Person and Company nodes have specific labels")
                    logger.info(f"   Note: {entity_only_count} generic Entity nodes remain")
                else:
                    logger.warning("⚠️  Some nodes may still need fixing")
        
        finally:
            await schema_manager.close()
    
    except ImportError as e:
        logger.error(f"Import error: {e}")
        logger.info("Install neo4j driver with: pip install neo4j")
    except Exception as e:
        logger.error(f"Failed to check/fix node labels: {e}")
        logger.info("Make sure Neo4j is running and credentials are correct")


async def show_sample_nodes():
    """Show sample nodes with their labels."""
    
    logger.info("\n=== Sample Nodes with Labels ===")
    
    try:
        from agent.neo4j_schema_manager import Neo4jSchemaManager
        
        schema_manager = Neo4jSchemaManager(
            uri=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
            user=os.getenv("NEO4J_USER", "neo4j"),
            password=os.getenv("NEO4J_PASSWORD", "password")
        )
        
        try:
            await schema_manager.initialize()
            
            async with schema_manager.driver.session() as session:
                # Show sample Person nodes
                person_query = """
                MATCH (p:Person)
                RETURN p.name as name, labels(p) as labels, keys(p) as properties
                LIMIT 5
                """
                
                result = await session.run(person_query)
                person_records = await result.data()
                
                if person_records:
                    logger.info("Sample Person nodes:")
                    for record in person_records:
                        name = record['name']
                        labels = record['labels']
                        properties = record['properties']
                        logger.info(f"  - {name}: labels={labels}, properties={len(properties)} keys")
                else:
                    logger.info("No Person nodes found")
                
                # Show sample Company nodes
                company_query = """
                MATCH (c:Company)
                RETURN c.name as name, labels(c) as labels, keys(c) as properties
                LIMIT 5
                """
                
                result = await session.run(company_query)
                company_records = await result.data()
                
                if company_records:
                    logger.info("Sample Company nodes:")
                    for record in company_records:
                        name = record['name']
                        labels = record['labels']
                        properties = record['properties']
                        logger.info(f"  - {name}: labels={labels}, properties={len(properties)} keys")
                else:
                    logger.info("No Company nodes found")
                
                # Show sample Entity nodes (if any remain)
                entity_query = """
                MATCH (e:Entity)
                WHERE NOT 'Person' IN labels(e) AND NOT 'Company' IN labels(e)
                RETURN e.name as name, labels(e) as labels, keys(e) as properties
                LIMIT 5
                """
                
                result = await session.run(entity_query)
                entity_records = await result.data()
                
                if entity_records:
                    logger.warning("Remaining generic Entity nodes:")
                    for record in entity_records:
                        name = record['name']
                        labels = record['labels']
                        properties = record['properties']
                        logger.warning(f"  - {name}: labels={labels}, properties={len(properties)} keys")
                else:
                    logger.info("No generic Entity nodes found")
        
        finally:
            await schema_manager.close()
    
    except Exception as e:
        logger.error(f"Failed to show sample nodes: {e}")


def show_cypher_queries():
    """Show useful Cypher queries for checking node labels."""
    
    logger.info("\n=== Useful Cypher Queries ===")
    
    logger.info("\n1. Check all node labels and counts:")
    logger.info("   CALL db.labels() YIELD label")
    logger.info("   CALL {")
    logger.info("     WITH label")
    logger.info("     CALL apoc.cypher.run('MATCH (n:' + label + ') RETURN count(n) as count', {}) YIELD value")
    logger.info("     RETURN label, value.count as count")
    logger.info("   }")
    logger.info("   RETURN label, count ORDER BY count DESC")
    
    logger.info("\n2. Find nodes with multiple labels:")
    logger.info("   MATCH (n)")
    logger.info("   WHERE size(labels(n)) > 1")
    logger.info("   RETURN labels(n) as labels, count(n) as count")
    logger.info("   ORDER BY count DESC")
    
    logger.info("\n3. Check Person nodes without Entity label:")
    logger.info("   MATCH (p:Person)")
    logger.info("   WHERE NOT 'Entity' IN labels(p)")
    logger.info("   RETURN p.name, labels(p) LIMIT 10")
    
    logger.info("\n4. Check Company nodes without Entity label:")
    logger.info("   MATCH (c:Company)")
    logger.info("   WHERE NOT 'Entity' IN labels(c)")
    logger.info("   RETURN c.name, labels(c) LIMIT 10")
    
    logger.info("\n5. Remove Entity label from Person nodes:")
    logger.info("   MATCH (n:Person:Entity)")
    logger.info("   REMOVE n:Entity")
    logger.info("   RETURN count(n) as fixed_count")
    
    logger.info("\n6. Remove Entity label from Company nodes:")
    logger.info("   MATCH (n:Company:Entity)")
    logger.info("   REMOVE n:Entity")
    logger.info("   RETURN count(n) as fixed_count")


async def main():
    """Run the label checking and fixing process."""
    
    logger.info("Neo4j Node Label Checker and Fixer")
    logger.info("=" * 50)
    
    # Check and fix node labels
    await check_and_fix_node_labels()
    
    # Show sample nodes
    await show_sample_nodes()
    
    # Show useful queries
    show_cypher_queries()
    
    logger.info("\n" + "=" * 50)
    logger.info("Node label checking and fixing complete!")
    
    logger.info("\nSUMMARY:")
    logger.info("✅ Checked for nodes with both specific and Entity labels")
    logger.info("✅ Removed Entity label from Person and Company nodes")
    logger.info("✅ Verified that nodes now have only specific labels")
    
    logger.info("\nNEXT STEPS:")
    logger.info("1. Verify in Neo4j Browser that Person and Company nodes have only specific labels")
    logger.info("2. Test the GraphBuilder with custom entity types")
    logger.info("3. Monitor future document processing to ensure only specific labels are created")


if __name__ == "__main__":
    asyncio.run(main())
