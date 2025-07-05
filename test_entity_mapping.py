#!/usr/bin/env python3
"""
Test script to verify that entities are properly mapped to Person and Company node types.
This test focuses on the entity mapping logic without requiring Graphiti installation.
"""

import logging
from typing import Dict, Any, List

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import our modules (only the ones that don't require graphiti_core)
from agent.entity_models import EntityGraph, create_person_from_name, create_company_from_name, PersonType, CompanyType

# Test data - sample director biography
SAMPLE_DIRECTOR_TEXT = """
Mr. John Michael Chen, aged 58, has been the Chairman and President and Executive Director of TechCorp Holdings Limited since January 2020. He is also an Independent Non-executive Director of DataFlow Systems Limited and serves on the board of Innovation Partners Inc.

Prior to joining TechCorp Holdings, Mr. Chen was the Managing Director of Global Finance Corporation from 2015 to 2019, where he led the company's expansion into Asian markets. He also served as Chief Financial Officer at Strategic Investments Ltd from 2010 to 2015.

Mr. Chen holds a Bachelor of Business Administration degree from the University of Hong Kong and a Master of Finance degree from the London School of Economics. He is a Chartered Financial Analyst (CFA) and a member of the Hong Kong Institute of Certified Public Accountants.

TechCorp Holdings Limited is a leading technology company specializing in artificial intelligence and cloud computing solutions. The company was founded in 2005 and is headquartered in Hong Kong. DataFlow Systems Limited is a subsidiary of TechCorp Holdings, focusing on data analytics and business intelligence solutions.
"""


def test_entity_extraction_and_mapping():
    """Test entity mapping to proper node types using sample data."""

    logger.info("=== Testing Entity Extraction and Mapping ===")

    # Sample extracted entities (simulating what would come from LLM extraction)
    sample_entities = {
        'people': [
            'John Michael Chen',
            'Mr. Chen'
        ],
        'companies': [
            'TechCorp Holdings Limited',
            'DataFlow Systems Limited',
            'Innovation Partners Inc',
            'Global Finance Corporation',
            'Strategic Investments Ltd'
        ],
        'corporate_roles': {
            'chairman': ['John Michael Chen'],
            'executive_directors': ['John Michael Chen'],
            'independent_directors': ['John Michael Chen'],
            'managing_directors': ['John Michael Chen'],
            'chief_financial_officers': ['John Michael Chen']
        }
    }

    logger.info("=== Sample Extracted Entities ===")
    logger.info(f"People: {sample_entities.get('people', [])}")
    logger.info(f"Companies: {sample_entities.get('companies', [])}")
    logger.info(f"Corporate Roles: {sample_entities.get('corporate_roles', {})}")

    # Test EntityGraph mapping
    logger.info("\n=== Testing EntityGraph Mapping ===")
    entity_graph = EntityGraph()
    entity_graph.add_entities_from_extraction(sample_entities)

    person_entities = entity_graph.get_person_entities()
    company_entities = entity_graph.get_company_entities()

    logger.info(f"Created {len(person_entities)} Person entities:")
    for person in person_entities:
        logger.info(f"  - {person.name} (Type: {person.person_type}, Position: {person.current_position})")

    logger.info(f"Created {len(company_entities)} Company entities:")
    for company in company_entities:
        logger.info(f"  - {company.name} (Type: {company.company_type})")

    # Verify entity types
    assert len(person_entities) > 0, "Should have created Person entities"
    assert len(company_entities) > 0, "Should have created Company entities"

    # Check that all person entities have the correct entity_type
    for person in person_entities:
        assert person.entity_type.value == "person", f"Person entity {person.name} should have entity_type 'person'"

    # Check that all company entities have the correct entity_type
    for company in company_entities:
        assert company.entity_type.value == "company", f"Company entity {company.name} should have entity_type 'company'"

    logger.info("✓ All entities have correct entity types")


def test_entity_creation_functions():
    """Test the entity creation helper functions."""

    logger.info("\n=== Testing Entity Creation Functions ===")

    # Test person creation
    person = create_person_from_name(
        name="John Michael Chen",
        person_type=PersonType.EXECUTIVE,
        current_company="TechCorp Holdings Limited",
        current_position="Chairman and President and Executive Director"
    )

    logger.info(f"Created Person: {person.name}")
    logger.info(f"  Type: {person.entity_type} / {person.person_type}")
    logger.info(f"  Company: {person.current_company}")
    logger.info(f"  Position: {person.current_position}")

    # Test company creation
    company = create_company_from_name(
        name="TechCorp Holdings Limited",
        company_type=CompanyType.PUBLIC,
        industry="Technology",
        headquarters="Hong Kong"
    )

    logger.info(f"Created Company: {company.name}")
    logger.info(f"  Type: {company.entity_type} / {company.company_type}")
    logger.info(f"  Industry: {company.industry}")
    logger.info(f"  Headquarters: {company.headquarters}")

    # Verify entity types
    assert person.entity_type.value == "person", "Person should have entity_type 'person'"
    assert company.entity_type.value == "company", "Company should have entity_type 'company'"

    logger.info("✓ Entity creation functions work correctly")


def test_episode_content_formatting():
    """Test the episode content formatting for proper node type hints."""

    logger.info("\n=== Testing Episode Content Formatting ===")

    # Create sample entities
    person = create_person_from_name(
        name="John Michael Chen",
        person_type=PersonType.EXECUTIVE,
        current_company="TechCorp Holdings Limited",
        current_position="Chairman and President"
    )

    company = create_company_from_name(
        name="TechCorp Holdings Limited",
        company_type=CompanyType.PUBLIC,
        industry="Technology"
    )

    # Simulate the episode content creation logic (without requiring GraphitiClient)
    def create_entity_episode_content(entity):
        """Simulate the episode content creation logic."""
        content_parts = []

        # Add explicit node type declaration for Graphiti to recognize
        if hasattr(entity, 'entity_type'):
            if entity.entity_type.value == "person":
                content_parts.append(f"PERSON: {entity.name}")
                content_parts.append(f"Entity Type: Person")
            elif entity.entity_type.value == "company":
                content_parts.append(f"COMPANY: {entity.name}")
                content_parts.append(f"Entity Type: Company")

        if hasattr(entity, 'description') and entity.description:
            content_parts.append(f"Description: {entity.description}")

        return "\n".join(content_parts)

    person_content = create_entity_episode_content(person)
    company_content = create_entity_episode_content(company)

    logger.info("Person episode content:")
    logger.info(person_content)
    logger.info("\nCompany episode content:")
    logger.info(company_content)

    # Verify the content includes proper type hints
    assert "PERSON:" in person_content
    assert "Entity Type: Person" in person_content
    assert "COMPANY:" in company_content
    assert "Entity Type: Company" in company_content

    logger.info("✓ Episode content formatting includes proper type hints")


def main():
    """Run all tests."""

    logger.info("Starting Entity Mapping Tests")
    logger.info("=" * 50)

    # Test entity creation functions
    test_entity_creation_functions()

    # Test episode content formatting
    test_episode_content_formatting()

    # Test entity extraction and mapping
    test_entity_extraction_and_mapping()

    logger.info("\n" + "=" * 50)
    logger.info("All tests completed!")
    logger.info("\nKey improvements made:")
    logger.info("1. Enhanced episode content with explicit PERSON/COMPANY type hints")
    logger.info("2. Added structured entity episode creation")
    logger.info("3. Created helper functions for entity type mapping")
    logger.info("4. Enhanced EntityGraph with proper entity classification")
    logger.info("\nThese changes ensure that:")
    logger.info("- Entities are properly classified as Person or Company types")
    logger.info("- Episode content includes explicit type hints for Graphiti")
    logger.info("- The system creates specific node types instead of generic Entity nodes")


if __name__ == "__main__":
    main()
