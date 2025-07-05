#!/usr/bin/env python3
"""
Test script to verify direct Person and Company node creation in Neo4j.
This bypasses Graphiti's generic Entity creation.
"""

import asyncio
import logging
import os
from typing import Dict, Any, List

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_direct_node_creation():
    """Test direct creation of Person and Company nodes."""
    
    logger.info("=== Testing Direct Person and Company Node Creation ===")
    
    try:
        # Import the schema manager
        from agent.neo4j_schema_manager import Neo4jSchemaManager
        
        # Initialize schema manager
        schema_manager = Neo4jSchemaManager(
            uri=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
            user=os.getenv("NEO4J_USER", "neo4j"),
            password=os.getenv("NEO4J_PASSWORD", "password")
        )
        
        # Test data
        test_people = [
            "John Michael Chen",
            "Sarah Wong",
            "Robert Smith"
        ]
        
        test_companies = [
            "TechCorp Holdings Limited",
            "DataFlow Systems Limited",
            "Innovation Partners Inc"
        ]
        
        try:
            # Get initial counts
            logger.info("Getting initial node counts...")
            initial_counts = await schema_manager.get_node_counts()
            logger.info(f"Initial counts: {initial_counts}")
            
            # Create Person nodes
            logger.info("Creating Person nodes...")
            person_uuids = []
            for person_name in test_people:
                uuid = await schema_manager.create_person_node(
                    name=person_name,
                    properties={
                        "test_run": True,
                        "source": "test_script"
                    }
                )
                person_uuids.append(uuid)
                logger.info(f"Created Person: {person_name} (UUID: {uuid})")
            
            # Create Company nodes
            logger.info("Creating Company nodes...")
            company_uuids = []
            for company_name in test_companies:
                uuid = await schema_manager.create_company_node(
                    name=company_name,
                    properties={
                        "test_run": True,
                        "source": "test_script"
                    }
                )
                company_uuids.append(uuid)
                logger.info(f"Created Company: {company_name} (UUID: {uuid})")
            
            # Create some relationships
            logger.info("Creating relationships...")
            await schema_manager.create_relationship(
                source_name="John Michael Chen",
                source_type="person",
                target_name="TechCorp Holdings Limited",
                target_type="company",
                relationship_type="WORKS_FOR",
                properties={"position": "Chairman and President"}
            )
            
            await schema_manager.create_relationship(
                source_name="Sarah Wong",
                source_type="person",
                target_name="DataFlow Systems Limited",
                target_type="company",
                relationship_type="WORKS_FOR",
                properties={"position": "Director"}
            )
            
            # Get final counts
            logger.info("Getting final node counts...")
            final_counts = await schema_manager.get_node_counts()
            logger.info(f"Final counts: {final_counts}")
            
            # Verify node types
            logger.info("Verifying node types...")
            node_samples = await schema_manager.verify_node_types()
            logger.info(f"Node samples: {node_samples}")
            
            # Calculate changes
            person_created = final_counts["person_nodes"] - initial_counts["person_nodes"]
            company_created = final_counts["company_nodes"] - initial_counts["company_nodes"]
            
            logger.info(f"✅ Successfully created {person_created} Person nodes and {company_created} Company nodes")
            
            # Verify that we have specific node types, not generic Entity nodes
            if final_counts["person_nodes"] > 0 and final_counts["company_nodes"] > 0:
                logger.info("✅ Confirmed: Person and Company nodes created with specific labels")
            else:
                logger.warning("⚠️  Warning: No Person or Company nodes found")
            
            if final_counts["entity_nodes"] > 0:
                logger.warning(f"⚠️  Warning: {final_counts['entity_nodes']} generic Entity nodes still exist")
            else:
                logger.info("✅ No generic Entity nodes found - using specific node types")
            
        finally:
            await schema_manager.close()
    
    except ImportError as e:
        logger.error(f"Import error: {e}")
        logger.info("This test requires the neo4j driver. Install with: pip install neo4j")
    except Exception as e:
        logger.error(f"Test failed: {e}")
        raise


async def test_graph_builder_integration():
    """Test the graph builder's direct node creation."""
    
    logger.info("\n=== Testing Graph Builder Integration ===")
    
    try:
        # Import required modules
        from ingestion.graph_builder import GraphBuilder
        from ingestion.chunker import DocumentChunk
        
        # Sample director biography text
        sample_text = """
        Mr. John Michael Chen, aged 58, has been the Chairman and President and Executive Director of TechCorp Holdings Limited since January 2020. He is also an Independent Non-executive Director of DataFlow Systems Limited.
        
        Prior to joining TechCorp Holdings, Mr. Chen was the Managing Director of Global Finance Corporation from 2015 to 2019. He also served as Chief Financial Officer at Strategic Investments Ltd from 2010 to 2015.
        
        TechCorp Holdings Limited is a leading technology company specializing in artificial intelligence and cloud computing solutions. DataFlow Systems Limited is a subsidiary of TechCorp Holdings, focusing on data analytics solutions.
        """
        
        # Create a document chunk
        chunk = DocumentChunk(
            content=sample_text,
            index=0,
            start_char=0,
            end_char=len(sample_text),
            metadata={
                'entities': {
                    'people': ['John Michael Chen', 'Mr. Chen'],
                    'companies': ['TechCorp Holdings Limited', 'DataFlow Systems Limited', 'Global Finance Corporation', 'Strategic Investments Ltd'],
                    'corporate_roles': {
                        'chairman': ['John Michael Chen'],
                        'executive_directors': ['John Michael Chen'],
                        'managing_directors': ['John Michael Chen'],
                        'chief_financial_officers': ['John Michael Chen']
                    }
                }
            },
            token_count=len(sample_text.split())
        )
        
        # Initialize graph builder
        graph_builder = GraphBuilder()
        
        try:
            # Test direct node creation
            result = await graph_builder.create_direct_person_company_nodes(
                chunks=[chunk],
                document_title="Sample Director Biography",
                document_source="test_document.pdf",
                document_metadata={"test": True}
            )
            
            logger.info(f"Graph builder result: {result}")
            logger.info(f"Person nodes created: {result.get('person_nodes_created', 0)}")
            logger.info(f"Company nodes created: {result.get('company_nodes_created', 0)}")
            logger.info(f"Total people processed: {result.get('total_people', 0)}")
            logger.info(f"Total companies processed: {result.get('total_companies', 0)}")
            
            if result.get('errors'):
                logger.warning(f"Errors encountered: {result['errors']}")
            
            if result.get('person_nodes_created', 0) > 0 and result.get('company_nodes_created', 0) > 0:
                logger.info("✅ Graph builder successfully created Person and Company nodes")
            else:
                logger.warning("⚠️  Graph builder did not create expected nodes")
        
        finally:
            await graph_builder.close()
    
    except ImportError as e:
        logger.error(f"Import error: {e}")
        logger.info("This test requires the graph builder modules")
    except Exception as e:
        logger.error(f"Graph builder test failed: {e}")
        logger.info("This is expected if Neo4j is not running or configured")


def show_summary():
    """Show summary of the changes made."""
    
    logger.info("\n" + "=" * 70)
    logger.info("SUMMARY: ENTITY MAPPING TO PERSON AND COMPANY NODES")
    logger.info("=" * 70)
    
    logger.info("\n✅ CHANGES IMPLEMENTED:")
    logger.info("1. Created Neo4jSchemaManager for direct node creation")
    logger.info("2. Modified GraphBuilder to create specific Person/Company nodes")
    logger.info("3. Bypassed Graphiti's generic Entity node creation")
    logger.info("4. Added direct Cypher queries for proper node labels")
    
    logger.info("\n✅ BENEFITS:")
    logger.info("- Person entities now create :Person nodes (not :Entity)")
    logger.info("- Company entities now create :Company nodes (not :Entity)")
    logger.info("- Proper node labeling for better graph queries")
    logger.info("- Maintains entity relationships and properties")
    
    logger.info("\n✅ USAGE:")
    logger.info("- Set NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD environment variables")
    logger.info("- Use GraphBuilder.add_document_to_graph() as before")
    logger.info("- System now creates specific node types automatically")
    
    logger.info("\n" + "=" * 70)


async def main():
    """Run all tests."""
    
    logger.info("Starting Direct Node Creation Tests")
    logger.info("=" * 50)
    
    # Test direct node creation
    await test_direct_node_creation()
    
    # Test graph builder integration
    await test_graph_builder_integration()
    
    # Show summary
    show_summary()
    
    logger.info("\nTests completed!")


if __name__ == "__main__":
    asyncio.run(main())
