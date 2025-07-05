#!/usr/bin/env python3
"""
Example demonstrating the specific corporate relationship types.
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
    initialize_graph,
    close_graph
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def create_corporate_network_example():
    """Create a comprehensive corporate network with specific relationship types."""
    
    logger.info("Creating corporate network example...")
    
    # Create people
    people = [
        Person(
            name="John Chen",
            person_type=PersonType.EXECUTIVE,
            full_name="John Michael Chen",
            current_company="TechCorp Holdings",
            current_position="Chairman and President and Executive Director"
        ),
        Person(
            name="Sarah Wong",
            person_type=PersonType.DIRECTOR,
            full_name="Sarah Li Wong",
            current_company="TechCorp Holdings",
            current_position="Vice Chairperson and Non-Executive Director"
        ),
        Person(
            name="David Kim",
            person_type=PersonType.EXECUTIVE,
            full_name="David Sung Kim",
            current_company="TechCorp Holdings",
            current_position="Executive Director"
        ),
        Person(
            name="Lisa Zhang",
            person_type=PersonType.DIRECTOR,
            full_name="Lisa Ming Zhang",
            current_company="TechCorp Holdings",
            current_position="Independent Non-Executive Director"
        ),
        Person(
            name="Robert Lee",
            person_type=PersonType.EXECUTIVE,
            full_name="Robert James Lee",
            current_company="TechCorp Holdings",
            current_position="Company Secretary"
        )
    ]
    
    # Create companies
    companies = [
        Company(
            name="TechCorp Holdings",
            company_type=CompanyType.PUBLIC,
            legal_name="TechCorp Holdings Limited",
            industry="Technology",
            headquarters="Hong Kong",
            ticker_symbol="TECH"
        ),
        Company(
            name="TechCorp Software",
            company_type=CompanyType.SUBSIDIARY,
            legal_name="TechCorp Software Limited",
            industry="Software Development",
            headquarters="Singapore",
            parent_company="TechCorp Holdings"
        ),
        Company(
            name="DataFlow Systems",
            company_type=CompanyType.PRIVATE,
            legal_name="DataFlow Systems Pte Ltd",
            industry="Data Analytics",
            headquarters="Singapore"
        ),
        Company(
            name="Hong Kong Stock Exchange",
            company_type=CompanyType.PUBLIC,
            legal_name="Hong Kong Exchanges and Clearing Limited",
            industry="Financial Services",
            headquarters="Hong Kong"
        ),
        Company(
            name="Global Investment Bank",
            company_type=CompanyType.PUBLIC,
            legal_name="Global Investment Bank Limited",
            industry="Investment Banking",
            headquarters="London"
        )
    ]
    
    # Add entities to graph
    logger.info("Adding entities to knowledge graph...")
    
    for person in people:
        await add_person_to_graph(
            name=person.name,
            person_type=person.person_type,
            current_company=person.current_company,
            current_position=person.current_position,
            full_name=person.full_name,
            source_document="corporate_network_example"
        )
        logger.info(f"Added person: {person.name}")
    
    for company in companies:
        await add_company_to_graph(
            name=company.name,
            company_type=company.company_type,
            legal_name=company.legal_name,
            industry=company.industry,
            headquarters=company.headquarters,
            ticker_symbol=getattr(company, 'ticker_symbol', None),
            parent_company=getattr(company, 'parent_company', None),
            source_document="corporate_network_example"
        )
        logger.info(f"Added company: {company.name}")
    
    # Create person-to-person relationships
    person_relationships = [
        Relationship(
            source_entity_id="John Chen",
            target_entity_id="Sarah Wong",
            relationship_type=RelationshipType.RELATED_TO,
            description="Professional colleagues on the board"
        ),
        Relationship(
            source_entity_id="John Chen",
            target_entity_id="David Kim",
            relationship_type=RelationshipType.PROVIDED_FUND_FOR,
            description="John Chen provided funding for David Kim's previous venture"
        ),
        Relationship(
            source_entity_id="Sarah Wong",
            target_entity_id="Lisa Zhang",
            relationship_type=RelationshipType.PROVIDED_GUARANTEES_FOR,
            description="Sarah Wong provided guarantees for Lisa Zhang's business loan"
        ),
        Relationship(
            source_entity_id="David Kim",
            target_entity_id="Robert Lee",
            relationship_type=RelationshipType.HAD_TRANSACTIONS_WITH,
            description="Previous business transactions in software licensing"
        )
    ]
    
    # Create person-to-company relationships
    person_company_relationships = [
        Relationship(
            source_entity_id="John Chen",
            target_entity_id="TechCorp Holdings",
            relationship_type=RelationshipType.CHAIRMAN_AND_PRESIDENT_AND_EXECUTIVE_DIRECTOR_OF,
            description="John Chen serves as Chairman, President and Executive Director"
        ),
        Relationship(
            source_entity_id="Sarah Wong",
            target_entity_id="TechCorp Holdings",
            relationship_type=RelationshipType.VICECHAIRPERSON_AND_NON_EXECUTIVE_DIRECTOR_OF,
            description="Sarah Wong serves as Vice Chairperson and Non-Executive Director"
        ),
        Relationship(
            source_entity_id="David Kim",
            target_entity_id="TechCorp Holdings",
            relationship_type=RelationshipType.EXECUTIVE_DIRECTOR_OF,
            description="David Kim serves as Executive Director"
        ),
        Relationship(
            source_entity_id="Lisa Zhang",
            target_entity_id="TechCorp Holdings",
            relationship_type=RelationshipType.INDEPENDENT_NON_EXECUTIVE_DIRECTOR_OF,
            description="Lisa Zhang serves as Independent Non-Executive Director"
        ),
        Relationship(
            source_entity_id="Robert Lee",
            target_entity_id="TechCorp Holdings",
            relationship_type=RelationshipType.COMPANY_SECRETARY_OF,
            description="Robert Lee serves as Company Secretary"
        ),
        Relationship(
            source_entity_id="John Chen",
            target_entity_id="DataFlow Systems",
            relationship_type=RelationshipType.SHAREHOLDER_OF,
            description="John Chen holds shares in DataFlow Systems"
        )
    ]
    
    # Create company-to-company relationships
    company_relationships = [
        Relationship(
            source_entity_id="TechCorp Software",
            target_entity_id="TechCorp Holdings",
            relationship_type=RelationshipType.SUBSIDIARY_OF,
            description="TechCorp Software is a wholly-owned subsidiary"
        ),
        Relationship(
            source_entity_id="TechCorp Holdings",
            target_entity_id="DataFlow Systems",
            relationship_type=RelationshipType.SHAREHOLDER_OF_COMPANY,
            description="TechCorp Holdings owns 25% stake in DataFlow Systems"
        ),
        Relationship(
            source_entity_id="TechCorp Holdings",
            target_entity_id="Hong Kong Stock Exchange",
            relationship_type=RelationshipType.LIST_BONDS_ON,
            description="TechCorp Holdings has corporate bonds listed on HKEX"
        ),
        Relationship(
            source_entity_id="Global Investment Bank",
            target_entity_id="TechCorp Holdings",
            relationship_type=RelationshipType.UNDERWRITER_OF,
            description="Global Investment Bank underwrote TechCorp's IPO"
        ),
        Relationship(
            source_entity_id="TechCorp Holdings",
            target_entity_id="DataFlow Systems",
            relationship_type=RelationshipType.PROVIDED_GUARANTEE_TO,
            description="TechCorp Holdings provided guarantee for DataFlow's bank loan"
        ),
        Relationship(
            source_entity_id="TechCorp Holdings",
            target_entity_id="DataFlow Systems",
            relationship_type=RelationshipType.HAD_EQUITY_TRANSFER_AGREEMENT_WITH,
            description="Equity transfer agreement for 25% stake acquisition"
        ),
        Relationship(
            source_entity_id="TechCorp Software",
            target_entity_id="DataFlow Systems",
            relationship_type=RelationshipType.HAD_FACILITY_AGREEMENT_WITH,
            description="Software licensing and support facility agreement"
        )
    ]
    
    # Add all relationships to graph
    logger.info("Adding relationships to knowledge graph...")
    
    all_relationships = person_relationships + person_company_relationships + company_relationships
    
    for rel in all_relationships:
        await add_relationship_to_graph(
            source_entity=rel.source_entity_id,
            target_entity=rel.target_entity_id,
            relationship_type=rel.relationship_type,
            description=rel.description,
            source_document="corporate_network_example"
        )
        logger.info(f"Added relationship: {rel.source_entity_id} {rel.relationship_type} {rel.target_entity_id}")
    
    logger.info(f"Created corporate network with {len(people)} people, {len(companies)} companies, and {len(all_relationships)} relationships")
    
    return {
        "people": len(people),
        "companies": len(companies),
        "relationships": len(all_relationships),
        "relationship_types": {
            "person_to_person": len(person_relationships),
            "person_to_company": len(person_company_relationships),
            "company_to_company": len(company_relationships)
        }
    }


async def demonstrate_relationship_categories():
    """Demonstrate the different relationship categories."""
    
    logger.info("Demonstrating relationship categories...")
    
    # Create sample relationships
    sample_relationships = [
        Relationship(
            source_entity_id="Person A",
            target_entity_id="Person B",
            relationship_type=RelationshipType.PROVIDED_FUND_FOR
        ),
        Relationship(
            source_entity_id="Person C",
            target_entity_id="Company X",
            relationship_type=RelationshipType.EXECUTIVE_DIRECTOR_OF
        ),
        Relationship(
            source_entity_id="Company Y",
            target_entity_id="Company Z",
            relationship_type=RelationshipType.HAD_LOAN_TRANSFER_AGREEMENT_WITH
        )
    ]
    
    for rel in sample_relationships:
        logger.info(f"Relationship: {rel.relationship_type}")
        logger.info(f"  Is Financial: {rel.is_financial_relationship()}")
        logger.info(f"  Is Governance: {rel.is_governance_relationship()}")
        logger.info(f"  Is Person-to-Person: {rel.is_person_to_person()}")
        logger.info(f"  Is Person-to-Company: {rel.is_person_to_company()}")
        logger.info(f"  Is Company-to-Company: {rel.is_company_to_company()}")
        logger.info("")


async def main():
    """Main example function."""
    
    logger.info("Starting corporate relationships example...")
    
    try:
        # Initialize graph connection
        await initialize_graph()
        
        # Demonstrate relationship categories
        await demonstrate_relationship_categories()
        
        # Create comprehensive corporate network
        result = await create_corporate_network_example()
        
        logger.info("Corporate network creation completed!")
        logger.info(f"Summary: {result}")
        
    except Exception as e:
        logger.error(f"Example failed: {e}")
        raise
    
    finally:
        # Close graph connection
        await close_graph()
    
    logger.info("Corporate relationships example completed!")


if __name__ == "__main__":
    asyncio.run(main())
