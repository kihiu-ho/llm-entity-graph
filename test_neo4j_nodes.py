#!/usr/bin/env python3
"""
Test script for Neo4j Person and Company node types.
"""

import logging
from datetime import datetime
from agent.neo4j_schema import create_neo4j_schema_manager

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_neo4j_schema():
    """Test Neo4j schema creation and node operations."""
    
    # Neo4j connection details (update these for your setup)
    NEO4J_URI = "bolt://localhost:7687"
    NEO4J_USERNAME = "neo4j"
    NEO4J_PASSWORD = "password"  # Change this to your Neo4j password
    
    try:
        # Create schema manager
        logger.info("Connecting to Neo4j...")
        schema_manager = create_neo4j_schema_manager(
            uri=NEO4J_URI,
            username=NEO4J_USERNAME,
            password=NEO4J_PASSWORD
        )
        
        # Initialize schema
        logger.info("Initializing Neo4j schema...")
        schema_manager.initialize_schema()
        
        # Create Person nodes
        logger.info("Creating Person nodes...")
        
        person1_id = schema_manager.create_person_node(
            name="John Chen",
            person_type="executive",
            full_name="John Michael Chen",
            current_company="TechCorp Holdings",
            current_position="Chairman and President and Executive Director",
            email="john.chen@techcorp.com",
            education=["Harvard Business School", "MIT"],
            skills=["Leadership", "Strategy", "Technology"],
            aliases=["J. Chen", "John M. Chen"]
        )
        
        person2_id = schema_manager.create_person_node(
            name="Sarah Wong",
            person_type="director",
            full_name="Sarah Li Wong",
            current_company="TechCorp Holdings",
            current_position="Vice Chairperson and Non-Executive Director",
            email="sarah.wong@techcorp.com",
            education=["Stanford University", "London Business School"],
            skills=["Finance", "Governance", "Risk Management"]
        )
        
        person3_id = schema_manager.create_person_node(
            name="David Kim",
            person_type="executive",
            full_name="David Sung Kim",
            current_company="TechCorp Holdings",
            current_position="Executive Director",
            email="david.kim@techcorp.com"
        )
        
        # Create Company nodes
        logger.info("Creating Company nodes...")
        
        company1_id = schema_manager.create_company_node(
            name="TechCorp Holdings",
            company_type="public",
            legal_name="TechCorp Holdings Limited",
            industry="Technology",
            headquarters="Hong Kong",
            ticker_symbol="TECH",
            website="https://techcorp.com",
            key_executives=["John Chen", "Sarah Wong", "David Kim"],
            employee_count=5000,
            aliases=["TechCorp", "TC Holdings"]
        )
        
        company2_id = schema_manager.create_company_node(
            name="TechCorp Software",
            company_type="subsidiary",
            legal_name="TechCorp Software Limited",
            industry="Software Development",
            headquarters="Singapore",
            parent_company="TechCorp Holdings",
            website="https://software.techcorp.com",
            employee_count=1200
        )
        
        company3_id = schema_manager.create_company_node(
            name="DataFlow Systems",
            company_type="private",
            legal_name="DataFlow Systems Pte Ltd",
            industry="Data Analytics",
            headquarters="Singapore",
            website="https://dataflow.com",
            employee_count=300
        )
        
        # Create relationships
        logger.info("Creating relationships...")
        
        # Person-Company relationships
        rel1_id = schema_manager.create_relationship(
            source_node_name="John Chen",
            source_node_type="Person",
            target_node_name="TechCorp Holdings",
            target_node_type="Company",
            relationship_type="Chairman_AND_President_AND_Executive_Director_OF",
            description="John Chen serves as Chairman, President and Executive Director",
            strength=1.0,
            start_date="2020-01-15",
            is_active=True
        )
        
        rel2_id = schema_manager.create_relationship(
            source_node_name="Sarah Wong",
            source_node_type="Person",
            target_node_name="TechCorp Holdings",
            target_node_type="Company",
            relationship_type="ViceChairperson_AND_Non_Executive_Director_OF",
            description="Sarah Wong serves as Vice Chairperson and Non-Executive Director",
            strength=0.9,
            start_date="2019-06-01",
            is_active=True
        )
        
        rel3_id = schema_manager.create_relationship(
            source_node_name="David Kim",
            source_node_type="Person",
            target_node_name="TechCorp Holdings",
            target_node_type="Company",
            relationship_type="Executive_Director_OF",
            description="David Kim serves as Executive Director",
            strength=0.8,
            start_date="2021-03-01",
            is_active=True
        )
        
        # Company-Company relationships
        rel4_id = schema_manager.create_relationship(
            source_node_name="TechCorp Software",
            source_node_type="Company",
            target_node_name="TechCorp Holdings",
            target_node_type="Company",
            relationship_type="Subsidiary_OF",
            description="TechCorp Software is a wholly-owned subsidiary",
            strength=1.0,
            is_active=True
        )
        
        rel5_id = schema_manager.create_relationship(
            source_node_name="TechCorp Holdings",
            source_node_type="Company",
            target_node_name="DataFlow Systems",
            target_node_type="Company",
            relationship_type="Shareholder_OF",
            description="TechCorp Holdings owns 25% stake in DataFlow Systems",
            strength=0.25,
            is_active=True
        )
        
        # Person-Person relationships
        rel6_id = schema_manager.create_relationship(
            source_node_name="John Chen",
            source_node_type="Person",
            target_node_name="Sarah Wong",
            target_node_type="Person",
            relationship_type="Related_TO",
            description="Professional colleagues on the board",
            strength=0.7,
            is_active=True
        )
        
        # Test search functionality
        logger.info("Testing search functionality...")
        
        # Search for people
        people = schema_manager.search_person_nodes(name_query="John", limit=5)
        logger.info(f"Found {len(people)} people matching 'John'")
        
        # Search for companies
        companies = schema_manager.search_company_nodes(industry="Technology", limit=5)
        logger.info(f"Found {len(companies)} technology companies")
        
        # Get all Person nodes
        all_people = schema_manager.get_person_nodes(limit=10)
        logger.info(f"Total Person nodes: {len(all_people)}")
        
        # Get all Company nodes
        all_companies = schema_manager.get_company_nodes(limit=10)
        logger.info(f"Total Company nodes: {len(all_companies)}")
        
        logger.info("✓ Neo4j Person and Company node types test completed successfully!")
        
        # Print summary
        print("\n" + "="*60)
        print("NEO4J NODE TYPES TEST SUMMARY")
        print("="*60)
        print(f"Person nodes created: 3")
        print(f"Company nodes created: 3") 
        print(f"Relationships created: 6")
        print(f"Schema constraints: Person.name, Company.name (unique)")
        print(f"Indexes created: Multiple for efficient querying")
        print("="*60)
        
        return True
        
    except Exception as e:
        logger.error(f"Neo4j test failed: {e}")
        return False
        
    finally:
        # Close connection
        if 'schema_manager' in locals():
            schema_manager.close()
            logger.info("Neo4j connection closed")


def print_cypher_examples():
    """Print example Cypher queries for working with the node types."""
    
    print("\n" + "="*60)
    print("EXAMPLE CYPHER QUERIES")
    print("="*60)
    
    print("\n-- Find all Person nodes:")
    print("MATCH (p:Person) RETURN p.name, p.current_company, p.current_position;")
    
    print("\n-- Find all Company nodes:")
    print("MATCH (c:Company) RETURN c.name, c.industry, c.headquarters;")
    
    print("\n-- Find all executives:")
    print("MATCH (p:Person)-[r:RELATED]->(c:Company)")
    print("WHERE r.relationship_type CONTAINS 'Executive'")
    print("RETURN p.name, r.relationship_type, c.name;")
    
    print("\n-- Find company relationships:")
    print("MATCH (c1:Company)-[r:RELATED]->(c2:Company)")
    print("RETURN c1.name, r.relationship_type, c2.name;")
    
    print("\n-- Find people in TechCorp Holdings:")
    print("MATCH (p:Person)-[r:RELATED]->(c:Company {name: 'TechCorp Holdings'})")
    print("RETURN p.name, p.current_position, r.relationship_type;")
    
    print("="*60)


if __name__ == "__main__":
    print("Testing Neo4j Person and Company node types...")
    
    # Print Cypher examples
    print_cypher_examples()
    
    # Run the test
    success = test_neo4j_schema()
    
    if success:
        print("\n✓ All tests passed!")
    else:
        print("\n✗ Tests failed!")
        exit(1)
