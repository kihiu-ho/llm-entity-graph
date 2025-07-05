#!/usr/bin/env python3
"""
Test script for corporate relationship types.
"""

import asyncio
import logging
from datetime import datetime

from agent.entity_models import (
    Person, Company, Relationship, EntityGraph,
    EntityType, PersonType, CompanyType, RelationshipType
)
from agent.relationship_utils import (
    RelationshipValidator, validate_relationship, 
    suggest_relationships, describe_relationship
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_relationship_types():
    """Test the specific relationship types."""
    logger.info("Testing relationship types...")
    
    # Test person-to-person relationships
    logger.info("\n=== Person-to-Person Relationships ===")
    person_to_person = RelationshipType.get_person_to_person_relationships()
    for rel_type in person_to_person:
        logger.info(f"  {rel_type}: {describe_relationship(rel_type)}")
    
    # Test person-to-company relationships
    logger.info("\n=== Person-to-Company Relationships ===")
    person_to_company = RelationshipType.get_person_to_company_relationships()
    for rel_type in person_to_company:
        logger.info(f"  {rel_type}: {describe_relationship(rel_type)}")
    
    # Test company-to-company relationships
    logger.info("\n=== Company-to-Company Relationships ===")
    company_to_company = RelationshipType.get_company_to_company_relationships()
    for rel_type in company_to_company:
        logger.info(f"  {rel_type}: {describe_relationship(rel_type)}")


def test_relationship_validation():
    """Test relationship validation."""
    logger.info("\n=== Testing Relationship Validation ===")
    
    # Valid relationships
    test_cases = [
        (EntityType.PERSON, EntityType.PERSON, RelationshipType.PROVIDED_FUND_FOR, True),
        (EntityType.PERSON, EntityType.COMPANY, RelationshipType.EXECUTIVE_DIRECTOR_OF, True),
        (EntityType.COMPANY, EntityType.COMPANY, RelationshipType.SUBSIDIARY_OF, True),
        
        # Invalid relationships (wrong entity type combinations)
        (EntityType.PERSON, EntityType.PERSON, RelationshipType.SUBSIDIARY_OF, False),
        (EntityType.COMPANY, EntityType.PERSON, RelationshipType.PROVIDED_FUND_FOR, False),
    ]
    
    for source_type, target_type, rel_type, expected_valid in test_cases:
        is_valid = validate_relationship(source_type, target_type, rel_type)
        status = "✓" if is_valid == expected_valid else "✗"
        logger.info(f"  {status} {source_type.value} → {target_type.value}: {rel_type} (Expected: {expected_valid}, Got: {is_valid})")


def test_relationship_suggestions():
    """Test relationship suggestions."""
    logger.info("\n=== Testing Relationship Suggestions ===")
    
    # Test suggestions with context
    test_contexts = [
        (EntityType.PERSON, EntityType.PERSON, "John provided funding to Mary for her startup"),
        (EntityType.PERSON, EntityType.COMPANY, "Sarah serves as chairman and president of TechCorp"),
        (EntityType.PERSON, EntityType.COMPANY, "David is an independent non-executive director"),
        (EntityType.COMPANY, EntityType.COMPANY, "TechCorp is a subsidiary of Holdings Ltd"),
        (EntityType.COMPANY, EntityType.COMPANY, "Bank provided guarantee to TechCorp"),
        (EntityType.COMPANY, EntityType.COMPANY, "Investment firm underwrote the IPO"),
    ]
    
    for source_type, target_type, context in test_contexts:
        suggestions = suggest_relationships(source_type, target_type, context)
        logger.info(f"  Context: '{context}'")
        logger.info(f"  Suggestions: {suggestions[:3]}")  # Show top 3 suggestions
        logger.info("")


def test_relationship_categories():
    """Test relationship categorization."""
    logger.info("\n=== Testing Relationship Categories ===")
    
    # Create sample relationships
    sample_relationships = [
        RelationshipType.PROVIDED_FUND_FOR,
        RelationshipType.EXECUTIVE_DIRECTOR_OF,
        RelationshipType.SHAREHOLDER_OF,
        RelationshipType.SUBSIDIARY_OF,
        RelationshipType.HAD_LOAN_TRANSFER_AGREEMENT_WITH,
        RelationshipType.CHAIRMAN_AND_PRESIDENT_AND_EXECUTIVE_DIRECTOR_OF,
        RelationshipType.PROVIDED_GUARANTEE_TO,
        RelationshipType.RELATED_TO,
    ]
    
    categories = RelationshipValidator.categorize_relationships(sample_relationships)
    
    for category, relationships in categories.items():
        if relationships:
            logger.info(f"  {category.upper()}:")
            for rel in relationships:
                logger.info(f"    - {rel}")


def test_corporate_structure_example():
    """Test a complete corporate structure example."""
    logger.info("\n=== Testing Corporate Structure Example ===")
    
    # Create entities
    chairman = Person(
        name="John Chen",
        person_type=PersonType.EXECUTIVE,
        current_position="Chairman and President and Executive Director"
    )
    
    vice_chair = Person(
        name="Sarah Wong", 
        person_type=PersonType.DIRECTOR,
        current_position="Vice Chairperson and Non-Executive Director"
    )
    
    company_secretary = Person(
        name="Robert Lee",
        person_type=PersonType.EXECUTIVE,
        current_position="Company Secretary"
    )
    
    holding_company = Company(
        name="TechCorp Holdings",
        company_type=CompanyType.PUBLIC,
        industry="Technology"
    )
    
    subsidiary = Company(
        name="TechCorp Software",
        company_type=CompanyType.SUBSIDIARY,
        industry="Software"
    )
    
    # Create relationships
    relationships = [
        Relationship(
            source_entity_id=chairman.name,
            target_entity_id=holding_company.name,
            relationship_type=RelationshipType.CHAIRMAN_AND_PRESIDENT_AND_EXECUTIVE_DIRECTOR_OF,
            description="John Chen serves in combined leadership role"
        ),
        Relationship(
            source_entity_id=vice_chair.name,
            target_entity_id=holding_company.name,
            relationship_type=RelationshipType.VICECHAIRPERSON_AND_NON_EXECUTIVE_DIRECTOR_OF,
            description="Sarah Wong serves as Vice Chairperson and Non-Executive Director"
        ),
        Relationship(
            source_entity_id=company_secretary.name,
            target_entity_id=holding_company.name,
            relationship_type=RelationshipType.COMPANY_SECRETARY_OF,
            description="Robert Lee serves as Company Secretary"
        ),
        Relationship(
            source_entity_id=subsidiary.name,
            target_entity_id=holding_company.name,
            relationship_type=RelationshipType.SUBSIDIARY_OF,
            description="TechCorp Software is a wholly-owned subsidiary"
        ),
        Relationship(
            source_entity_id=chairman.name,
            target_entity_id=vice_chair.name,
            relationship_type=RelationshipType.RELATED_TO,
            description="Professional colleagues on the board"
        )
    ]
    
    # Create entity graph
    graph = EntityGraph()
    graph.add_entity(chairman)
    graph.add_entity(vice_chair)
    graph.add_entity(company_secretary)
    graph.add_entity(holding_company)
    graph.add_entity(subsidiary)
    
    for rel in relationships:
        graph.add_relationship(rel)
    
    logger.info(f"Created corporate structure with:")
    logger.info(f"  - {len(graph.entities)} entities")
    logger.info(f"  - {len(graph.relationships)} relationships")
    
    # Analyze relationships
    for rel in graph.relationships:
        logger.info(f"  Relationship: {rel.source_entity_id} {rel.relationship_type} {rel.target_entity_id}")
        logger.info(f"    Financial: {rel.is_financial_relationship()}")
        logger.info(f"    Governance: {rel.is_governance_relationship()}")
        logger.info(f"    Category: {rel.is_person_to_person() and 'Person-to-Person' or rel.is_person_to_company() and 'Person-to-Company' or 'Company-to-Company'}")
        logger.info("")


def test_financial_relationships():
    """Test financial relationship examples."""
    logger.info("\n=== Testing Financial Relationships ===")
    
    financial_relationships = RelationshipType.get_financial_relationships()
    logger.info(f"Financial relationship types ({len(financial_relationships)}):")
    
    for rel_type in financial_relationships:
        logger.info(f"  - {rel_type}: {describe_relationship(rel_type)}")
    
    # Create examples
    examples = [
        ("Person A", "Person B", RelationshipType.PROVIDED_FUND_FOR),
        ("Person C", "Company X", RelationshipType.SHAREHOLDER_OF),
        ("Company Y", "Company Z", RelationshipType.HAD_EQUITY_TRANSFER_AGREEMENT_WITH),
        ("Bank Corp", "TechCorp", RelationshipType.PROVIDED_GUARANTEE_TO),
    ]
    
    logger.info("\nFinancial relationship examples:")
    for source, target, rel_type in examples:
        rel = Relationship(
            source_entity_id=source,
            target_entity_id=target,
            relationship_type=rel_type
        )
        logger.info(f"  {source} {rel_type} {target} (Financial: {rel.is_financial_relationship()})")


def main():
    """Main test function."""
    logger.info("Starting corporate relationship tests...")
    
    # Run all tests
    test_relationship_types()
    test_relationship_validation()
    test_relationship_suggestions()
    test_relationship_categories()
    test_corporate_structure_example()
    test_financial_relationships()
    
    logger.info("\nAll corporate relationship tests completed!")


if __name__ == "__main__":
    main()
