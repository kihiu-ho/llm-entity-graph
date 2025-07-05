#!/usr/bin/env python3
"""
Comprehensive script to fix Entity labels and ensure only Person and Company labels are used.
This script addresses the issue where nodes have both specific labels (Person/Company) and generic Entity labels.
"""

import asyncio
import logging
import os
from typing import Dict, Any, List

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def remove_entity_labels_from_specific_nodes():
    """Remove Entity labels from Person and Company nodes."""
    
    logger.info("=== Removing Entity Labels from Person and Company Nodes ===")
    
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
                # Check current state
                logger.info("Checking current node label state...")
                
                # Count Person nodes with Entity label
                person_entity_query = """
                MATCH (n:Person:Entity)
                RETURN count(n) as count
                """
                result = await session.run(person_entity_query)
                record = await result.single()
                person_entity_count = record['count'] if record else 0
                
                # Count Company nodes with Entity label
                company_entity_query = """
                MATCH (n:Company:Entity)
                RETURN count(n) as count
                """
                result = await session.run(company_entity_query)
                record = await result.single()
                company_entity_count = record['count'] if record else 0
                
                logger.info(f"Found {person_entity_count} Person nodes with Entity label")
                logger.info(f"Found {company_entity_count} Company nodes with Entity label")
                
                # Remove Entity label from Person nodes
                if person_entity_count > 0:
                    logger.info("Removing Entity label from Person nodes...")
                    remove_person_entity_query = """
                    MATCH (n:Person:Entity)
                    REMOVE n:Entity
                    RETURN count(n) as fixed_count
                    """
                    result = await session.run(remove_person_entity_query)
                    record = await result.single()
                    fixed_person_count = record['fixed_count'] if record else 0
                    logger.info(f"✅ Fixed {fixed_person_count} Person nodes")
                
                # Remove Entity label from Company nodes
                if company_entity_count > 0:
                    logger.info("Removing Entity label from Company nodes...")
                    remove_company_entity_query = """
                    MATCH (n:Company:Entity)
                    REMOVE n:Entity
                    RETURN count(n) as fixed_count
                    """
                    result = await session.run(remove_company_entity_query)
                    record = await result.single()
                    fixed_company_count = record['fixed_count'] if record else 0
                    logger.info(f"✅ Fixed {fixed_company_count} Company nodes")
                
                # Verify the fix
                logger.info("Verifying the fix...")
                
                # Check final counts
                final_person_query = """
                MATCH (n:Person)
                RETURN count(n) as total_count,
                       size([p IN collect(n) WHERE 'Entity' IN labels(p)]) as with_entity_count
                """
                result = await session.run(final_person_query)
                record = await result.single()
                total_person_count = record['total_count'] if record else 0
                person_with_entity_count = record['with_entity_count'] if record else 0
                
                final_company_query = """
                MATCH (n:Company)
                RETURN count(n) as total_count,
                       size([c IN collect(n) WHERE 'Entity' IN labels(c)]) as with_entity_count
                """
                result = await session.run(final_company_query)
                record = await result.single()
                total_company_count = record['total_count'] if record else 0
                company_with_entity_count = record['with_entity_count'] if record else 0
                
                logger.info("=== FINAL RESULTS ===")
                logger.info(f"Total Person nodes: {total_person_count}")
                logger.info(f"Person nodes with Entity label: {person_with_entity_count}")
                logger.info(f"Total Company nodes: {total_company_count}")
                logger.info(f"Company nodes with Entity label: {company_with_entity_count}")
                
                if person_with_entity_count == 0 and company_with_entity_count == 0:
                    logger.info("✅ SUCCESS: All Person and Company nodes now have only specific labels!")
                else:
                    logger.warning("⚠️  Some nodes still have Entity labels")
                
                return {
                    "person_nodes_fixed": person_entity_count,
                    "company_nodes_fixed": company_entity_count,
                    "person_nodes_remaining_with_entity": person_with_entity_count,
                    "company_nodes_remaining_with_entity": company_with_entity_count
                }
        
        finally:
            await schema_manager.close()
    
    except Exception as e:
        logger.error(f"Failed to remove Entity labels: {e}")
        return None


async def test_custom_entity_types_without_entity_label():
    """Test that new documents create only Person and Company nodes without Entity labels."""
    
    logger.info("\n=== Testing Custom Entity Types (No Entity Labels) ===")
    
    try:
        from ingestion.graph_builder import GraphBuilder
        from ingestion.chunker import DocumentChunk
        
        # Sample text with clear person and company entities
        sample_text = """
        Ms. Sarah Wong, aged 45, has been appointed as the Chief Technology Officer of DataFlow Systems Limited effective January 2024. She previously served as Senior Vice President of Engineering at TechCorp Holdings Limited from 2020 to 2023.
        
        DataFlow Systems Limited is a Singapore-based data analytics company founded in 2018. The company specializes in business intelligence solutions and has 300 employees. TechCorp Holdings Limited is its parent company, headquartered in Hong Kong.
        """
        
        # Create a document chunk
        chunk = DocumentChunk(
            content=sample_text,
            index=0,
            start_char=0,
            end_char=len(sample_text),
            metadata={},
            token_count=len(sample_text.split())
        )
        
        # Initialize graph builder with custom entity types
        graph_builder = GraphBuilder()
        
        logger.info("Processing test document with custom entity types...")
        logger.info("Custom entity types configured:")
        logger.info(f"  Entity types: {list(graph_builder.entity_types.keys())}")
        logger.info(f"  Excluded types: ['Entity']")
        
        try:
            # Process the document
            result = await graph_builder.add_document_to_graph(
                chunks=[chunk],
                document_title="Test CTO Appointment",
                document_source="test_appointment.pdf",
                document_metadata={"test": True}
            )
            
            logger.info(f"✅ Successfully processed document: {result.get('episodes_created', 0)} episodes created")
            
            # Wait a moment for processing
            await asyncio.sleep(2)
            
            # Check what nodes were created
            await check_newly_created_nodes()
            
        finally:
            await graph_builder.close()
    
    except Exception as e:
        logger.error(f"Test failed: {e}")


async def check_newly_created_nodes():
    """Check what types of nodes were created recently."""
    
    logger.info("Checking recently created nodes...")
    
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
                # Check recent Person nodes
                recent_person_query = """
                MATCH (p:Person)
                WHERE p.created_at IS NOT NULL
                RETURN p.name as name, labels(p) as labels, p.created_at as created_at
                ORDER BY p.created_at DESC
                LIMIT 5
                """
                
                result = await session.run(recent_person_query)
                person_records = await result.data()
                
                if person_records:
                    logger.info("Recent Person nodes:")
                    for record in person_records:
                        name = record['name']
                        labels = record['labels']
                        created_at = record['created_at']
                        has_entity_label = 'Entity' in labels
                        status = "❌ HAS Entity label" if has_entity_label else "✅ No Entity label"
                        logger.info(f"  - {name}: {labels} {status}")
                
                # Check recent Company nodes
                recent_company_query = """
                MATCH (c:Company)
                WHERE c.created_at IS NOT NULL
                RETURN c.name as name, labels(c) as labels, c.created_at as created_at
                ORDER BY c.created_at DESC
                LIMIT 5
                """
                
                result = await session.run(recent_company_query)
                company_records = await result.data()
                
                if company_records:
                    logger.info("Recent Company nodes:")
                    for record in company_records:
                        name = record['name']
                        labels = record['labels']
                        created_at = record['created_at']
                        has_entity_label = 'Entity' in labels
                        status = "❌ HAS Entity label" if has_entity_label else "✅ No Entity label"
                        logger.info(f"  - {name}: {labels} {status}")
        
        finally:
            await schema_manager.close()
    
    except Exception as e:
        logger.error(f"Failed to check recent nodes: {e}")


def show_solution_summary():
    """Show summary of the solution implemented."""
    
    logger.info("\n" + "=" * 70)
    logger.info("SOLUTION SUMMARY: REMOVING ENTITY LABELS")
    logger.info("=" * 70)
    
    logger.info("\n🎯 PROBLEM:")
    logger.info("- Nodes were being created with both specific labels (Person/Company) and generic Entity labels")
    logger.info("- This resulted in labels like ['Person', 'Entity'] and ['Company', 'Entity']")
    logger.info("- We want only specific labels: ['Person'] and ['Company']")
    
    logger.info("\n✅ SOLUTION IMPLEMENTED:")
    logger.info("1. Added excluded_entity_types=['Entity'] to GraphBuilder")
    logger.info("2. Enhanced add_episode() to support excluded_entity_types parameter")
    logger.info("3. Created script to remove Entity labels from existing nodes")
    logger.info("4. Configured Graphiti to exclude generic Entity type")
    
    logger.info("\n🔧 CODE CHANGES:")
    logger.info("- ingestion/graph_builder.py: Added excluded_entity_types=['Entity']")
    logger.info("- agent/graph_utils.py: Enhanced add_episode() with excluded_entity_types")
    logger.info("- Created fix_entity_labels.py: Script to clean existing nodes")
    
    logger.info("\n🎉 EXPECTED RESULTS:")
    logger.info("- New Person nodes: labels=['Person'] (no Entity)")
    logger.info("- New Company nodes: labels=['Company'] (no Entity)")
    logger.info("- Existing nodes: Entity labels removed")
    logger.info("- Better graph queries: MATCH (p:Person) without Entity interference")


async def main():
    """Run the complete Entity label fixing process."""
    
    logger.info("Entity Label Fixing Script")
    logger.info("=" * 50)
    
    # Step 1: Remove Entity labels from existing nodes
    result = await remove_entity_labels_from_specific_nodes()
    
    # Step 2: Test that new documents don't create Entity labels
    await test_custom_entity_types_without_entity_label()
    
    # Step 3: Show solution summary
    show_solution_summary()
    
    logger.info("\n" + "=" * 50)
    logger.info("Entity Label Fixing Complete!")
    
    if result:
        logger.info(f"\n📊 SUMMARY:")
        logger.info(f"- Person nodes fixed: {result['person_nodes_fixed']}")
        logger.info(f"- Company nodes fixed: {result['company_nodes_fixed']}")
        logger.info(f"- Person nodes still with Entity: {result['person_nodes_remaining_with_entity']}")
        logger.info(f"- Company nodes still with Entity: {result['company_nodes_remaining_with_entity']}")
    
    logger.info("\n🎯 NEXT STEPS:")
    logger.info("1. Verify in Neo4j Browser: MATCH (p:Person) RETURN labels(p), count(p)")
    logger.info("2. Verify in Neo4j Browser: MATCH (c:Company) RETURN labels(c), count(c)")
    logger.info("3. Process new documents and verify only specific labels are created")
    logger.info("4. Use type-specific queries: MATCH (p:Person)-[:Employment]->(c:Company)")


if __name__ == "__main__":
    asyncio.run(main())
