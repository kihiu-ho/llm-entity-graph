#!/usr/bin/env python3
"""
Utility script to check the current state of Neo4j nodes and verify entity types.
"""

import asyncio
import logging
import os
from typing import Dict, Any

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def check_node_types():
    """Check what types of nodes exist in the Neo4j database."""
    
    logger.info("=== Checking Neo4j Node Types ===")
    
    try:
        from agent.neo4j_schema_manager import Neo4jSchemaManager
        
        # Initialize schema manager
        schema_manager = Neo4jSchemaManager(
            uri=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
            user=os.getenv("NEO4J_USER", "neo4j"),
            password=os.getenv("NEO4J_PASSWORD", "password")
        )
        
        try:
            # Get node counts
            counts = await schema_manager.get_node_counts()
            logger.info(f"Node counts: {counts}")
            
            # Get sample nodes
            samples = await schema_manager.verify_node_types()
            logger.info(f"Sample nodes: {samples}")
            
            # Analyze the results
            logger.info("\n=== ANALYSIS ===")
            
            if counts["person_nodes"] > 0:
                logger.info(f"✅ Found {counts['person_nodes']} Person nodes")
                if samples["person_samples"]:
                    logger.info(f"   Sample Person nodes: {samples['person_samples']}")
            else:
                logger.warning("⚠️  No Person nodes found")
            
            if counts["company_nodes"] > 0:
                logger.info(f"✅ Found {counts['company_nodes']} Company nodes")
                if samples["company_samples"]:
                    logger.info(f"   Sample Company nodes: {samples['company_samples']}")
            else:
                logger.warning("⚠️  No Company nodes found")
            
            if counts["entity_nodes"] > 0:
                logger.warning(f"⚠️  Found {counts['entity_nodes']} generic Entity nodes")
                if samples["entity_samples"]:
                    logger.warning(f"   Sample Entity nodes: {samples['entity_samples']}")
                logger.warning("   These should be converted to Person/Company nodes")
            else:
                logger.info("✅ No generic Entity nodes found")
            
            # Summary
            total_specific = counts["person_nodes"] + counts["company_nodes"]
            total_generic = counts["entity_nodes"]
            
            logger.info(f"\n=== SUMMARY ===")
            logger.info(f"Specific node types (Person + Company): {total_specific}")
            logger.info(f"Generic node types (Entity): {total_generic}")
            
            if total_specific > 0 and total_generic == 0:
                logger.info("✅ SUCCESS: All entities are using specific node types!")
            elif total_specific > 0 and total_generic > 0:
                logger.warning("⚠️  MIXED: Some entities use specific types, some use generic Entity")
            elif total_specific == 0 and total_generic > 0:
                logger.error("❌ PROBLEM: All entities are using generic Entity nodes")
            else:
                logger.info("ℹ️  No entity nodes found in database")
        
        finally:
            await schema_manager.close()
    
    except ImportError as e:
        logger.error(f"Import error: {e}")
        logger.info("Install neo4j driver with: pip install neo4j")
    except Exception as e:
        logger.error(f"Failed to check node types: {e}")
        logger.info("Make sure Neo4j is running and credentials are correct")


async def run_detailed_query():
    """Run a detailed query to show all node labels and their counts."""
    
    logger.info("\n=== Detailed Node Analysis ===")
    
    try:
        from agent.neo4j_schema_manager import Neo4jSchemaManager
        
        schema_manager = Neo4jSchemaManager(
            uri=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
            user=os.getenv("NEO4J_USER", "neo4j"),
            password=os.getenv("NEO4J_PASSWORD", "password")
        )
        
        try:
            await schema_manager.initialize()
            
            # Query to get all labels and their counts
            cypher_query = """
            CALL db.labels() YIELD label
            CALL {
                WITH label
                CALL apoc.cypher.run('MATCH (n:' + label + ') RETURN count(n) as count', {}) YIELD value
                RETURN label, value.count as count
            }
            RETURN label, count
            ORDER BY count DESC
            """
            
            # Fallback query if APOC is not available
            fallback_query = """
            MATCH (n)
            RETURN labels(n) as node_labels, count(n) as count
            ORDER BY count DESC
            """
            
            async with schema_manager.driver.session() as session:
                try:
                    # Try the APOC query first
                    result = await session.run(cypher_query)
                    records = await result.data()
                    
                    if records:
                        logger.info("Node labels and counts:")
                        for record in records:
                            logger.info(f"  {record['label']}: {record['count']} nodes")
                    else:
                        logger.info("No labeled nodes found")
                
                except Exception:
                    # Fall back to simpler query
                    logger.info("Using fallback query (APOC not available)")
                    result = await session.run(fallback_query)
                    records = await result.data()
                    
                    label_counts = {}
                    for record in records:
                        labels = record['node_labels']
                        count = record['count']
                        for label in labels:
                            label_counts[label] = label_counts.get(label, 0) + count
                    
                    if label_counts:
                        logger.info("Node labels and counts:")
                        for label, count in sorted(label_counts.items(), key=lambda x: x[1], reverse=True):
                            logger.info(f"  {label}: {count} nodes")
                    else:
                        logger.info("No labeled nodes found")
        
        finally:
            await schema_manager.close()
    
    except Exception as e:
        logger.error(f"Failed to run detailed query: {e}")


async def show_sample_nodes():
    """Show sample nodes of each type with their properties."""
    
    logger.info("\n=== Sample Node Properties ===")
    
    try:
        from agent.neo4j_schema_manager import Neo4jSchemaManager
        
        schema_manager = Neo4jSchemaManager(
            uri=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
            user=os.getenv("NEO4J_USER", "neo4j"),
            password=os.getenv("NEO4J_PASSWORD", "password")
        )
        
        try:
            await schema_manager.initialize()
            
            # Query for sample Person nodes
            person_query = """
            MATCH (p:Person)
            RETURN p.name as name, p.entity_type as entity_type, keys(p) as properties
            LIMIT 3
            """
            
            # Query for sample Company nodes
            company_query = """
            MATCH (c:Company)
            RETURN c.name as name, c.entity_type as entity_type, keys(c) as properties
            LIMIT 3
            """
            
            # Query for sample Entity nodes
            entity_query = """
            MATCH (e:Entity)
            RETURN e.name as name, e.entity_type as entity_type, keys(e) as properties
            LIMIT 3
            """
            
            async with schema_manager.driver.session() as session:
                # Check Person nodes
                result = await session.run(person_query)
                person_records = await result.data()
                
                if person_records:
                    logger.info("Sample Person nodes:")
                    for record in person_records:
                        logger.info(f"  - {record['name']} (type: {record.get('entity_type', 'N/A')})")
                        logger.info(f"    Properties: {record['properties']}")
                else:
                    logger.info("No Person nodes found")
                
                # Check Company nodes
                result = await session.run(company_query)
                company_records = await result.data()
                
                if company_records:
                    logger.info("Sample Company nodes:")
                    for record in company_records:
                        logger.info(f"  - {record['name']} (type: {record.get('entity_type', 'N/A')})")
                        logger.info(f"    Properties: {record['properties']}")
                else:
                    logger.info("No Company nodes found")
                
                # Check Entity nodes
                result = await session.run(entity_query)
                entity_records = await result.data()
                
                if entity_records:
                    logger.warning("Sample Entity nodes (should be converted):")
                    for record in entity_records:
                        logger.warning(f"  - {record['name']} (type: {record.get('entity_type', 'N/A')})")
                        logger.warning(f"    Properties: {record['properties']}")
                else:
                    logger.info("No generic Entity nodes found")
        
        finally:
            await schema_manager.close()
    
    except Exception as e:
        logger.error(f"Failed to show sample nodes: {e}")


async def main():
    """Run all checks."""
    
    logger.info("Neo4j Node Type Checker")
    logger.info("=" * 50)
    
    # Check basic node types
    await check_node_types()
    
    # Run detailed analysis
    await run_detailed_query()
    
    # Show sample nodes
    await show_sample_nodes()
    
    logger.info("\n" + "=" * 50)
    logger.info("Check completed!")
    
    logger.info("\nTo fix generic Entity nodes:")
    logger.info("1. Use the new GraphBuilder.create_direct_person_company_nodes() method")
    logger.info("2. Run document processing with the updated system")
    logger.info("3. The system will create Person and Company nodes instead of Entity nodes")


if __name__ == "__main__":
    asyncio.run(main())
