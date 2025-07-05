#!/usr/bin/env python3
"""
Test script for entity models and graph operations.
"""

import asyncio
import logging
from datetime import datetime

from agent.entity_models import (
    Person, Company, Relationship, EntityGraph,
    EntityType, PersonType, CompanyType, RelationshipType
)
from agent.graph_utils import (
    add_person_to_graph,
    add_company_to_graph,
    add_relationship_to_graph,
    search_people,
    search_companies,
    get_person_relationships,
    get_company_relationships,
    initialize_graph,
    close_graph
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_entity_models():
    """Test entity model creation."""
    logger.info("Testing entity models...")
    
    # Create a person
    person = Person(
        name="John Smith",
        person_type=PersonType.EXECUTIVE,
        full_name="John Michael Smith",
        current_company="TechCorp Inc",
        current_position="Chief Technology Officer",
        email="john.smith@techcorp.com",
        education=["MIT Computer Science", "Stanford MBA"],
        skills=["Python", "Machine Learning", "Leadership"],
        aliases=["John M. Smith", "J. Smith"]
    )
    
    logger.info(f"Created person: {person.name}")
    logger.info(f"  Type: {person.person_type}")
    logger.info(f"  Company: {person.current_company}")
    logger.info(f"  Position: {person.current_position}")
    
    # Create a company
    company = Company(
        name="TechCorp Inc",
        company_type=CompanyType.PUBLIC,
        legal_name="TechCorp Incorporated",
        industry="Technology",
        headquarters="San Francisco, CA",
        website="https://techcorp.com",
        products=["AI Software", "Cloud Services", "Data Analytics"],
        key_executives=["John Smith", "Jane Doe"],
        ticker_symbol="TECH",
        employee_count=5000,
        aliases=["TechCorp", "TC Inc"]
    )
    
    logger.info(f"Created company: {company.name}")
    logger.info(f"  Type: {company.company_type}")
    logger.info(f"  Industry: {company.industry}")
    logger.info(f"  Headquarters: {company.headquarters}")
    
    # Create a relationship
    relationship = Relationship(
        source_entity_id="John Smith",
        target_entity_id="TechCorp Inc",
        relationship_type=RelationshipType.EXECUTIVE_OF,
        description="John Smith is the CTO of TechCorp Inc",
        strength=0.9,
        start_date=datetime(2020, 1, 15)
    )
    
    logger.info(f"Created relationship: {relationship.relationship_type}")
    logger.info(f"  From: {relationship.source_entity_id}")
    logger.info(f"  To: {relationship.target_entity_id}")
    logger.info(f"  Strength: {relationship.strength}")
    
    # Create entity graph
    graph = EntityGraph()
    graph.add_entity(person)
    graph.add_entity(company)
    graph.add_relationship(relationship)
    
    logger.info(f"Created entity graph with {len(graph.entities)} entities and {len(graph.relationships)} relationships")
    
    return person, company, relationship, graph


async def test_graph_operations():
    """Test graph database operations."""
    logger.info("Testing graph operations...")
    
    try:
        # Initialize graph connection
        await initialize_graph()
        logger.info("Graph connection initialized")
        
        # Add a person to the graph
        person_episode_id = await add_person_to_graph(
            name="Alice Johnson",
            person_type=PersonType.EXECUTIVE,
            current_company="DataCorp",
            current_position="CEO",
            full_name="Alice Marie Johnson",
            email="alice@datacorp.com",
            source_document="test_document_1"
        )
        logger.info(f"Added person to graph: {person_episode_id}")
        
        # Add a company to the graph
        company_episode_id = await add_company_to_graph(
            name="DataCorp",
            company_type=CompanyType.PRIVATE,
            industry="Data Analytics",
            headquarters="New York, NY",
            website="https://datacorp.com",
            source_document="test_document_1"
        )
        logger.info(f"Added company to graph: {company_episode_id}")
        
        # Add a relationship
        relationship_episode_id = await add_relationship_to_graph(
            source_entity="Alice Johnson",
            target_entity="DataCorp",
            relationship_type=RelationshipType.EXECUTIVE_OF,
            description="Alice Johnson is the CEO of DataCorp",
            strength=1.0,
            source_document="test_document_1"
        )
        logger.info(f"Added relationship to graph: {relationship_episode_id}")
        
        # Wait a moment for indexing
        await asyncio.sleep(2)
        
        # Search for people
        logger.info("Searching for people...")
        people_results = await search_people(name_query="Alice", limit=5)
        logger.info(f"Found {len(people_results)} people")
        for result in people_results:
            logger.info(f"  - {result}")
        
        # Search for companies
        logger.info("Searching for companies...")
        company_results = await search_companies(name_query="DataCorp", limit=5)
        logger.info(f"Found {len(company_results)} companies")
        for result in company_results:
            logger.info(f"  - {result}")
        
        # Get person relationships
        logger.info("Getting person relationships...")
        person_rels = await get_person_relationships("Alice Johnson")
        logger.info(f"Found {len(person_rels)} relationships for Alice Johnson")
        for rel in person_rels:
            logger.info(f"  - {rel}")
        
        # Get company relationships
        logger.info("Getting company relationships...")
        company_rels = await get_company_relationships("DataCorp")
        logger.info(f"Found {len(company_rels)} relationships for DataCorp")
        for rel in company_rels:
            logger.info(f"  - {rel}")
        
    except Exception as e:
        logger.error(f"Graph operations failed: {e}")
        raise
    
    finally:
        # Close graph connection
        await close_graph()
        logger.info("Graph connection closed")


async def main():
    """Main test function."""
    logger.info("Starting entity and graph tests...")
    
    # Test entity models
    await test_entity_models()
    
    # Test graph operations
    await test_graph_operations()
    
    logger.info("All tests completed!")


if __name__ == "__main__":
    asyncio.run(main())
