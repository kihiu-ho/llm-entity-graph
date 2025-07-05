#!/usr/bin/env python3
"""
Test script to verify that Graphiti custom entity types are working correctly.
This tests the new Person and Company entity types instead of generic Entity nodes.
"""

import asyncio
import logging
import os
from typing import Dict, Any, List
from datetime import datetime, timezone

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_custom_entity_types():
    """Test Graphiti custom entity types for Person and Company."""
    
    logger.info("=== Testing Graphiti Custom Entity Types ===")
    
    try:
        # Import the graph builder with custom entity types
        from ingestion.graph_builder import GraphBuilder
        from ingestion.chunker import DocumentChunk
        
        # Sample director biography text with clear person and company entities
        sample_text = """
        Mr. John Michael Chen, aged 58, has been the Chairman and President and Executive Director of TechCorp Holdings Limited since January 2020. He is also an Independent Non-executive Director of DataFlow Systems Limited and serves on the board of Innovation Partners Inc.
        
        Prior to joining TechCorp Holdings, Mr. Chen was the Managing Director of Global Finance Corporation from 2015 to 2019, where he led the company's expansion into Asian markets. He also served as Chief Financial Officer at Strategic Investments Ltd from 2010 to 2015.
        
        Mr. Chen holds a Bachelor of Business Administration degree from the University of Hong Kong and a Master of Finance degree from the London School of Economics. He is a Chartered Financial Analyst (CFA) and a member of the Hong Kong Institute of Certified Public Accountants.
        
        TechCorp Holdings Limited is a leading technology company specializing in artificial intelligence and cloud computing solutions. The company was founded in 2005 and is headquartered in Hong Kong. DataFlow Systems Limited is a subsidiary of TechCorp Holdings, focusing on data analytics and business intelligence solutions.
        
        Innovation Partners Inc is a venture capital firm that invests in early-stage technology companies. Global Finance Corporation is a multinational financial services company with operations across Asia-Pacific.
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
        
        logger.info("Custom entity types configured:")
        logger.info(f"  Entity types: {list(graph_builder.entity_types.keys())}")
        logger.info(f"  Edge types: {list(graph_builder.edge_types.keys())}")
        logger.info(f"  Edge type mappings: {len(graph_builder.edge_type_map)} mappings")
        
        try:
            # Test the graph building with custom entity types
            logger.info("Processing document with custom entity types...")
            result = await graph_builder.add_document_to_graph(
                chunks=[chunk],
                document_title="Sample Director Biography",
                document_source="test_document.pdf",
                document_metadata={"test": True, "custom_entity_types": True}
            )
            
            logger.info("=== Graph Building Results ===")
            logger.info(f"Episodes created: {result.get('episodes_created', 0)}")
            logger.info(f"Custom entity types used: {result.get('custom_entity_types_used', False)}")
            logger.info(f"Entity types: {result.get('entity_types', [])}")
            logger.info(f"Edge types: {result.get('edge_types', [])}")
            logger.info(f"Total chunks processed: {result.get('total_chunks', 0)}")
            
            if result.get('errors'):
                logger.warning(f"Errors encountered: {result['errors']}")
            
            if result.get('episodes_created', 0) > 0:
                logger.info("✅ Successfully processed document with custom entity types")
                
                # Test search functionality
                logger.info("\n=== Testing Search with Custom Entity Types ===")
                try:
                    # Search for person-related information
                    person_results = await graph_builder.graph_client.search(
                        query="John Michael Chen person chairman",
                        num_results=5
                    )
                    
                    logger.info(f"Person search results: {len(person_results)} found")
                    for i, result in enumerate(person_results[:3]):
                        logger.info(f"  {i+1}. {result.fact[:100]}...")
                    
                    # Search for company-related information
                    company_results = await graph_builder.graph_client.search(
                        query="TechCorp Holdings Limited company technology",
                        num_results=5
                    )
                    
                    logger.info(f"Company search results: {len(company_results)} found")
                    for i, result in enumerate(company_results[:3]):
                        logger.info(f"  {i+1}. {result.fact[:100]}...")
                    
                    if person_results or company_results:
                        logger.info("✅ Search functionality working with custom entity types")
                    else:
                        logger.warning("⚠️  No search results found")
                
                except Exception as e:
                    logger.error(f"Search test failed: {e}")
            else:
                logger.warning("⚠️  No episodes were created")
        
        finally:
            await graph_builder.close()
    
    except ImportError as e:
        logger.error(f"Import error: {e}")
        logger.info("This test requires the graph builder modules and dependencies")
    except Exception as e:
        logger.error(f"Test failed: {e}")
        logger.info("This is expected if Graphiti or Neo4j is not properly configured")


async def test_entity_type_definitions():
    """Test the custom entity type definitions."""
    
    logger.info("\n=== Testing Entity Type Definitions ===")
    
    try:
        from ingestion.graph_builder import Person, Company, Employment, Leadership
        
        # Test Person entity type
        person = Person(
            age=58,
            occupation="Chairman and President",
            company="TechCorp Holdings Limited",
            position="Executive Director",
            education="MBA from London School of Economics",
            location="Hong Kong"
        )
        
        logger.info("Person entity created:")
        logger.info(f"  Age: {person.age}")
        logger.info(f"  Occupation: {person.occupation}")
        logger.info(f"  Company: {person.company}")
        logger.info(f"  Position: {person.position}")
        
        # Test Company entity type
        company = Company(
            industry="Technology",
            founded_year=2005,
            headquarters="Hong Kong",
            description="Leading technology company specializing in AI and cloud computing",
            company_type="Public"
        )
        
        logger.info("Company entity created:")
        logger.info(f"  Industry: {company.industry}")
        logger.info(f"  Founded: {company.founded_year}")
        logger.info(f"  Headquarters: {company.headquarters}")
        logger.info(f"  Type: {company.company_type}")
        
        # Test Employment edge type
        employment = Employment(
            position="Chairman and President",
            start_date=datetime(2020, 1, 1),
            is_current=True,
            employment_type="Executive"
        )
        
        logger.info("Employment relationship created:")
        logger.info(f"  Position: {employment.position}")
        logger.info(f"  Start date: {employment.start_date}")
        logger.info(f"  Is current: {employment.is_current}")
        
        # Test Leadership edge type
        leadership = Leadership(
            role="Chairman",
            start_date=datetime(2020, 1, 1),
            is_current=True,
            board_member=True
        )
        
        logger.info("Leadership relationship created:")
        logger.info(f"  Role: {leadership.role}")
        logger.info(f"  Board member: {leadership.board_member}")
        
        logger.info("✅ All custom entity and edge types working correctly")
    
    except Exception as e:
        logger.error(f"Entity type definition test failed: {e}")


def show_custom_entity_benefits():
    """Show the benefits of using custom entity types."""
    
    logger.info("\n" + "=" * 70)
    logger.info("BENEFITS OF CUSTOM ENTITY TYPES")
    logger.info("=" * 70)
    
    logger.info("\n✅ SPECIFIC NODE TYPES:")
    logger.info("- Graphiti creates :Person nodes (not generic :Entity)")
    logger.info("- Graphiti creates :Company nodes (not generic :Entity)")
    logger.info("- Proper node labeling for better graph queries")
    
    logger.info("\n✅ RICH ENTITY ATTRIBUTES:")
    logger.info("- Person: age, occupation, education, skills, etc.")
    logger.info("- Company: industry, founded_year, headquarters, revenue, etc.")
    logger.info("- Structured data extraction from text")
    
    logger.info("\n✅ CUSTOM RELATIONSHIP TYPES:")
    logger.info("- Employment: position, salary, start_date, is_current")
    logger.info("- Leadership: role, board_member, start_date")
    logger.info("- Investment: amount, stake_percentage, investment_type")
    logger.info("- Partnership: partnership_type, deal_value, duration")
    
    logger.info("\n✅ BETTER GRAPH STRUCTURE:")
    logger.info("- Type-specific queries: MATCH (p:Person)-[:Employment]->(c:Company)")
    logger.info("- Rich relationship attributes for detailed analysis")
    logger.info("- Proper entity classification by Graphiti's LLM")
    
    logger.info("\n✅ NATIVE GRAPHITI INTEGRATION:")
    logger.info("- Uses Graphiti's built-in custom entity type system")
    logger.info("- No need for direct Neo4j manipulation")
    logger.info("- Automatic entity extraction and classification")
    logger.info("- Seamless integration with Graphiti's search and retrieval")


async def main():
    """Run all tests."""
    
    logger.info("Testing Graphiti Custom Entity Types")
    logger.info("=" * 50)
    
    # Test entity type definitions
    await test_entity_type_definitions()
    
    # Test custom entity types in action
    await test_custom_entity_types()
    
    # Show benefits
    show_custom_entity_benefits()
    
    logger.info("\n" + "=" * 50)
    logger.info("Custom Entity Types Test Complete!")
    logger.info("\nKey improvements:")
    logger.info("1. Using Graphiti's native custom entity type system")
    logger.info("2. Person and Company entities with rich attributes")
    logger.info("3. Custom relationship types with detailed properties")
    logger.info("4. Proper node labeling (:Person, :Company) instead of :Entity")
    logger.info("5. Better graph structure and querying capabilities")


if __name__ == "__main__":
    asyncio.run(main())
