#!/usr/bin/env python3
"""
Example of using structured node types for document processing and graph building.
"""

import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Any

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
    initialize_graph,
    close_graph
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def extract_entities_from_text(text: str) -> EntityGraph:
    """
    Example function to extract structured nodes from text.
    In a real implementation, this would use NLP/LLM to extract nodes.
    """
    graph = EntityGraph()
    
    # Example: Extract entities from a corporate announcement
    if "CEO" in text and "TechCorp" in text:
        # Create person entity
        person = Person(
            name="Sarah Chen",
            person_type=PersonType.EXECUTIVE,
            full_name="Sarah Michelle Chen",
            current_company="TechCorp Inc",
            current_position="Chief Executive Officer",
            description="Experienced technology executive with 15 years in the industry"
        )
        graph.add_entity(person)
        
        # Create company entity
        company = Company(
            name="TechCorp Inc",
            company_type=CompanyType.PUBLIC,
            industry="Technology",
            headquarters="Seattle, WA",
            description="Leading provider of cloud computing solutions",
            key_executives=["Sarah Chen"],
            ticker_symbol="TECH"
        )
        graph.add_entity(company)
        
        # Create relationship
        relationship = Relationship(
            source_entity_id="Sarah Chen",
            target_entity_id="TechCorp Inc",
            relationship_type=RelationshipType.EXECUTIVE_OF,
            description="Sarah Chen serves as CEO of TechCorp Inc",
            strength=1.0,
            start_date=datetime(2022, 3, 1)
        )
        graph.add_relationship(relationship)
    
    return graph


async def process_document_with_entities(document_text: str, document_id: str):
    """
    Process a document and extract structured entities.
    """
    logger.info(f"Processing document: {document_id}")
    
    # Extract entities from text
    entity_graph = extract_entities_from_text(document_text)
    
    logger.info(f"Extracted {len(entity_graph.entities)} entities and {len(entity_graph.relationships)} relationships")
    
    # Add entities to knowledge graph
    entity_episode_ids = []
    
    for entity in entity_graph.entities:
        if isinstance(entity, Person):
            episode_id = await add_person_to_graph(
                name=entity.name,
                person_type=entity.person_type,
                current_company=entity.current_company,
                current_position=entity.current_position,
                full_name=entity.full_name,
                description=entity.description,
                source_document=document_id
            )
            entity_episode_ids.append(episode_id)
            logger.info(f"Added person: {entity.name}")
            
        elif isinstance(entity, Company):
            episode_id = await add_company_to_graph(
                name=entity.name,
                company_type=entity.company_type,
                industry=entity.industry,
                headquarters=entity.headquarters,
                description=entity.description,
                ticker_symbol=entity.ticker_symbol,
                source_document=document_id
            )
            entity_episode_ids.append(episode_id)
            logger.info(f"Added company: {entity.name}")
    
    # Add relationships to knowledge graph
    relationship_episode_ids = []
    
    for relationship in entity_graph.relationships:
        episode_id = await add_relationship_to_graph(
            source_entity=relationship.source_entity_id,
            target_entity=relationship.target_entity_id,
            relationship_type=relationship.relationship_type,
            description=relationship.description,
            strength=relationship.strength,
            start_date=relationship.start_date,
            source_document=document_id
        )
        relationship_episode_ids.append(episode_id)
        logger.info(f"Added relationship: {relationship.relationship_type}")
    
    return {
        "entity_episodes": entity_episode_ids,
        "relationship_episodes": relationship_episode_ids,
        "total_entities": len(entity_graph.entities),
        "total_relationships": len(entity_graph.relationships)
    }


async def search_and_analyze_entities():
    """
    Demonstrate searching and analyzing entities in the graph.
    """
    logger.info("Searching and analyzing entities...")
    
    # Search for people
    logger.info("Searching for executives...")
    people_results = await search_people(position="CEO", limit=10)
    logger.info(f"Found {len(people_results)} executives")
    
    for result in people_results:
        logger.info(f"  Executive: {result}")
    
    # Search for technology companies
    logger.info("Searching for technology companies...")
    tech_companies = await search_companies(industry="Technology", limit=10)
    logger.info(f"Found {len(tech_companies)} technology companies")
    
    for result in tech_companies:
        logger.info(f"  Company: {result}")
    
    # Analyze relationships for a specific person
    if people_results:
        person_name = "Sarah Chen"  # Example from our test data
        logger.info(f"Analyzing relationships for {person_name}...")
        
        relationships = await get_person_relationships(person_name)
        logger.info(f"Found {len(relationships)} relationships for {person_name}")
        
        for rel in relationships:
            logger.info(f"  Relationship: {rel}")


async def demonstrate_entity_types():
    """
    Demonstrate the different entity types and their properties.
    """
    logger.info("Demonstrating entity types...")
    
    # Create examples of different person types
    executive = Person(
        name="John Executive",
        person_type=PersonType.EXECUTIVE,
        current_position="Chief Technology Officer"
    )
    
    director = Person(
        name="Jane Director",
        person_type=PersonType.DIRECTOR,
        current_position="Board Member"
    )
    
    employee = Person(
        name="Bob Employee",
        person_type=PersonType.EMPLOYEE,
        current_position="Software Engineer"
    )
    
    # Create examples of different company types
    public_company = Company(
        name="PublicCorp",
        company_type=CompanyType.PUBLIC,
        ticker_symbol="PUB"
    )
    
    private_company = Company(
        name="PrivateCorp",
        company_type=CompanyType.PRIVATE
    )
    
    subsidiary = Company(
        name="SubsidiaryCorp",
        company_type=CompanyType.SUBSIDIARY,
        parent_company="PublicCorp"
    )
    
    logger.info("Created example entities:")
    logger.info(f"  People: {[p.name for p in [executive, director, employee]]}")
    logger.info(f"  Companies: {[c.name for c in [public_company, private_company, subsidiary]]}")
    
    # Demonstrate relationship types
    relationships = [
        Relationship(
            source_entity_id=executive.name,
            target_entity_id=public_company.name,
            relationship_type=RelationshipType.EXECUTIVE_OF
        ),
        Relationship(
            source_entity_id=director.name,
            target_entity_id=public_company.name,
            relationship_type=RelationshipType.DIRECTOR_OF
        ),
        Relationship(
            source_entity_id=employee.name,
            target_entity_id=public_company.name,
            relationship_type=RelationshipType.EMPLOYED_BY
        ),
        Relationship(
            source_entity_id=subsidiary.name,
            target_entity_id=public_company.name,
            relationship_type=RelationshipType.SUBSIDIARY_OF
        )
    ]
    
    logger.info("Created example relationships:")
    for rel in relationships:
        logger.info(f"  {rel.source_entity_id} {rel.relationship_type} {rel.target_entity_id}")


async def main():
    """
    Main example function.
    """
    logger.info("Starting entity extraction example...")
    
    try:
        # Initialize graph connection
        await initialize_graph()
        
        # Demonstrate entity types
        await demonstrate_entity_types()
        
        # Process a sample document
        sample_document = """
        TechCorp Inc announced today that Sarah Chen has been appointed as the new CEO.
        Ms. Chen brings over 15 years of experience in the technology industry.
        TechCorp is a leading provider of cloud computing solutions based in Seattle, WA.
        The company trades on NASDAQ under the symbol TECH.
        """
        
        result = await process_document_with_entities(sample_document, "sample_doc_001")
        logger.info(f"Document processing result: {result}")
        
        # Wait for indexing
        await asyncio.sleep(2)
        
        # Search and analyze entities
        await search_and_analyze_entities()
        
    except Exception as e:
        logger.error(f"Example failed: {e}")
        raise
    
    finally:
        # Close graph connection
        await close_graph()
    
    logger.info("Entity extraction example completed!")


if __name__ == "__main__":
    asyncio.run(main())
