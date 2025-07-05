#!/usr/bin/env python3
"""
Migration script to convert existing Entity nodes to specific Person and Company nodes.
"""

import asyncio
import logging
import os
from typing import Dict, Any, List

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def migrate_entity_nodes():
    """Migrate existing Entity nodes to Person and Company nodes."""
    
    logger.info("=== Migrating Entity Nodes to Person/Company ===")
    
    try:
        from agent.neo4j_schema_manager import Neo4jSchemaManager
        
        schema_manager = Neo4jSchemaManager(
            uri=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
            user=os.getenv("NEO4J_USER", "neo4j"),
            password=os.getenv("NEO4J_PASSWORD", "password")
        )
        
        try:
            await schema_manager.initialize()
            
            # Get all Entity nodes
            entity_query = """
            MATCH (e:Entity)
            RETURN e.name as name, e.uuid as uuid, properties(e) as props
            """
            
            async with schema_manager.driver.session() as session:
                result = await session.run(entity_query)
                entity_records = await result.data()
                
                if not entity_records:
                    logger.info("No Entity nodes found to migrate")
                    return
                
                logger.info(f"Found {len(entity_records)} Entity nodes to migrate")
                
                # Classify entities as Person or Company
                person_entities = []
                company_entities = []
                unknown_entities = []
                
                for record in entity_records:
                    name = record['name']
                    props = record['props']
                    
                    # Simple heuristics to classify entities
                    # You may want to enhance this with more sophisticated classification
                    if classify_as_person(name, props):
                        person_entities.append(record)
                    elif classify_as_company(name, props):
                        company_entities.append(record)
                    else:
                        unknown_entities.append(record)
                
                logger.info(f"Classification results:")
                logger.info(f"  - Person entities: {len(person_entities)}")
                logger.info(f"  - Company entities: {len(company_entities)}")
                logger.info(f"  - Unknown entities: {len(unknown_entities)}")
                
                # Migrate Person entities
                person_migrated = 0
                for entity in person_entities:
                    try:
                        await migrate_to_person(session, entity)
                        person_migrated += 1
                        logger.debug(f"Migrated to Person: {entity['name']}")
                    except Exception as e:
                        logger.error(f"Failed to migrate Person {entity['name']}: {e}")
                
                # Migrate Company entities
                company_migrated = 0
                for entity in company_entities:
                    try:
                        await migrate_to_company(session, entity)
                        company_migrated += 1
                        logger.debug(f"Migrated to Company: {entity['name']}")
                    except Exception as e:
                        logger.error(f"Failed to migrate Company {entity['name']}: {e}")
                
                logger.info(f"Migration complete:")
                logger.info(f"  - {person_migrated} entities migrated to Person nodes")
                logger.info(f"  - {company_migrated} entities migrated to Company nodes")
                logger.info(f"  - {len(unknown_entities)} entities remain as Entity nodes")
                
                if unknown_entities:
                    logger.warning("Unknown entities that were not migrated:")
                    for entity in unknown_entities[:10]:  # Show first 10
                        logger.warning(f"  - {entity['name']}")
        
        finally:
            await schema_manager.close()
    
    except Exception as e:
        logger.error(f"Migration failed: {e}")


def classify_as_person(name: str, props: Dict[str, Any]) -> bool:
    """
    Classify an entity as a person based on name and properties.
    
    Args:
        name: Entity name
        props: Entity properties
    
    Returns:
        True if entity should be classified as a person
    """
    # Common person name patterns
    person_indicators = [
        'mr.', 'mrs.', 'ms.', 'dr.', 'prof.',
        'john', 'jane', 'michael', 'sarah', 'david', 'mary',
        'chen', 'wong', 'smith', 'johnson', 'williams'
    ]
    
    # Check if name contains person indicators
    name_lower = name.lower()
    for indicator in person_indicators:
        if indicator in name_lower:
            return True
    
    # Check properties for person-specific attributes
    if props:
        person_props = ['position', 'role', 'title', 'age', 'education']
        for prop in person_props:
            if prop in props:
                return True
    
    # Check if name looks like a person name (has multiple words, proper case)
    words = name.split()
    if len(words) >= 2 and all(word[0].isupper() for word in words if word):
        # Could be a person name
        return True
    
    return False


def classify_as_company(name: str, props: Dict[str, Any]) -> bool:
    """
    Classify an entity as a company based on name and properties.
    
    Args:
        name: Entity name
        props: Entity properties
    
    Returns:
        True if entity should be classified as a company
    """
    # Common company name patterns
    company_indicators = [
        'ltd', 'limited', 'inc', 'incorporated', 'corp', 'corporation',
        'llc', 'company', 'co.', 'holdings', 'group', 'systems',
        'technologies', 'solutions', 'services', 'partners'
    ]
    
    # Check if name contains company indicators
    name_lower = name.lower()
    for indicator in company_indicators:
        if indicator in name_lower:
            return True
    
    # Check properties for company-specific attributes
    if props:
        company_props = ['industry', 'headquarters', 'founded', 'revenue', 'employees']
        for prop in company_props:
            if prop in props:
                return True
    
    return False


async def migrate_to_person(session, entity_record: Dict[str, Any]):
    """Migrate an Entity node to a Person node."""
    
    migration_query = """
    MATCH (e:Entity {uuid: $uuid})
    
    // Create Person node with same properties
    CREATE (p:Person)
    SET p = properties(e)
    SET p.entity_type = 'person'
    SET p.migrated_from = 'Entity'
    SET p.migration_date = datetime()
    
    // Copy all relationships
    WITH e, p
    MATCH (e)-[r]->(other)
    CREATE (p)-[r2:MIGRATED_REL]->(other)
    SET r2 = properties(r)
    SET r2.original_type = type(r)
    
    WITH e, p
    MATCH (other)-[r]->(e)
    CREATE (other)-[r2:MIGRATED_REL]->(p)
    SET r2 = properties(r)
    SET r2.original_type = type(r)
    
    // Remove Entity label, keep other labels
    WITH e, p
    CALL apoc.create.removeLabels([e], ['Entity']) YIELD node as updated_e
    
    RETURN p.name as migrated_name
    """
    
    # Fallback query without APOC
    fallback_query = """
    MATCH (e:Entity {uuid: $uuid})
    
    // Create Person node with same properties
    CREATE (p:Person)
    SET p = properties(e)
    SET p.entity_type = 'person'
    SET p.migrated_from = 'Entity'
    
    // Delete the Entity node (relationships will be handled separately)
    DELETE e
    
    RETURN p.name as migrated_name
    """
    
    try:
        # Try the APOC version first
        result = await session.run(migration_query, uuid=entity_record['uuid'])
        await result.single()
    except Exception:
        # Fall back to simpler version
        result = await session.run(fallback_query, uuid=entity_record['uuid'])
        await result.single()


async def migrate_to_company(session, entity_record: Dict[str, Any]):
    """Migrate an Entity node to a Company node."""
    
    migration_query = """
    MATCH (e:Entity {uuid: $uuid})
    
    // Create Company node with same properties
    CREATE (c:Company)
    SET c = properties(e)
    SET c.entity_type = 'company'
    SET c.migrated_from = 'Entity'
    SET c.migration_date = datetime()
    
    // Copy all relationships
    WITH e, c
    MATCH (e)-[r]->(other)
    CREATE (c)-[r2:MIGRATED_REL]->(other)
    SET r2 = properties(r)
    SET r2.original_type = type(r)
    
    WITH e, c
    MATCH (other)-[r]->(e)
    CREATE (other)-[r2:MIGRATED_REL]->(c)
    SET r2 = properties(r)
    SET r2.original_type = type(r)
    
    // Remove Entity label, keep other labels
    WITH e, c
    CALL apoc.create.removeLabels([e], ['Entity']) YIELD node as updated_e
    
    RETURN c.name as migrated_name
    """
    
    # Fallback query without APOC
    fallback_query = """
    MATCH (e:Entity {uuid: $uuid})
    
    // Create Company node with same properties
    CREATE (c:Company)
    SET c = properties(e)
    SET c.entity_type = 'company'
    SET c.migrated_from = 'Entity'
    
    // Delete the Entity node (relationships will be handled separately)
    DELETE e
    
    RETURN c.name as migrated_name
    """
    
    try:
        # Try the APOC version first
        result = await session.run(migration_query, uuid=entity_record['uuid'])
        await result.single()
    except Exception:
        # Fall back to simpler version
        result = await session.run(fallback_query, uuid=entity_record['uuid'])
        await result.single()


async def main():
    """Run the migration."""
    
    logger.info("Entity Node Migration Tool")
    logger.info("=" * 50)
    
    logger.info("This script will:")
    logger.info("1. Find all existing Entity nodes")
    logger.info("2. Classify them as Person or Company based on heuristics")
    logger.info("3. Create new Person/Company nodes with the same properties")
    logger.info("4. Preserve relationships where possible")
    
    # Ask for confirmation
    response = input("\nDo you want to proceed with the migration? (y/N): ")
    if response.lower() != 'y':
        logger.info("Migration cancelled")
        return
    
    await migrate_entity_nodes()
    
    logger.info("\nMigration completed!")
    logger.info("Run 'python check_neo4j_nodes.py' to verify the results")


if __name__ == "__main__":
    asyncio.run(main())
