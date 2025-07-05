#!/usr/bin/env python3
"""
Test script to verify the import fix.
"""

def test_entity_models():
    """Test entity models import."""
    try:
        from agent.entity_models import (
            Person, Company, Relationship, EntityGraph,
            EntityType, PersonType, CompanyType, RelationshipType
        )
        print("✓ Entity models imported successfully")
        
        # Test creating a person
        person = Person(
            name="Test Person",
            person_type=PersonType.EXECUTIVE
        )
        print(f"✓ Created person: {person.name}")
        
        # Test creating a company
        company = Company(
            name="Test Company",
            company_type=CompanyType.PRIVATE
        )
        print(f"✓ Created company: {company.name}")
        
        # Test relationship types
        rel_types = RelationshipType.get_person_to_company_relationships()
        print(f"✓ Got {len(rel_types)} person-to-company relationship types")
        
        return True
        
    except Exception as e:
        print(f"✗ Entity models import failed: {e}")
        return False


def test_graph_utils():
    """Test graph utils import."""
    try:
        from agent.graph_utils import GraphitiClient
        print("✓ GraphitiClient imported successfully")
        return True
        
    except Exception as e:
        print(f"✗ Graph utils import failed: {e}")
        return False


def test_relationship_utils():
    """Test relationship utils import."""
    try:
        from agent.relationship_utils import (
            RelationshipValidator, validate_relationship,
            suggest_relationships, describe_relationship
        )
        print("✓ Relationship utils imported successfully")
        
        # Test validation
        from agent.entity_models import EntityType, RelationshipType
        is_valid = validate_relationship(
            EntityType.PERSON, 
            EntityType.COMPANY, 
            RelationshipType.EXECUTIVE_OF
        )
        print(f"✓ Relationship validation works: {is_valid}")
        
        return True
        
    except Exception as e:
        print(f"✗ Relationship utils import failed: {e}")
        return False


def main():
    """Main test function."""
    print("Testing import fixes...")
    print("=" * 40)
    
    success_count = 0
    total_tests = 3
    
    if test_entity_models():
        success_count += 1
    
    if test_graph_utils():
        success_count += 1
    
    if test_relationship_utils():
        success_count += 1
    
    print("=" * 40)
    print(f"Tests passed: {success_count}/{total_tests}")
    
    if success_count == total_tests:
        print("✓ All imports working correctly!")
        return True
    else:
        print("✗ Some imports still have issues")
        return False


if __name__ == "__main__":
    main()
