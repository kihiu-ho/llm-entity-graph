#!/usr/bin/env python3
"""
Fix duplicate entities in Neo4j database.

This script identifies and merges duplicate entities that have the same name
but different UUIDs, which is a common issue with entity resolution.
"""

import os
import sys
import logging
import asyncio
from typing import List, Dict, Any
from dotenv import load_dotenv
from neo4j import GraphDatabase

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DuplicateEntityFixer:
    """Fix duplicate entities in Neo4j database."""
    
    def __init__(self):
        """Initialize Neo4j connection."""
        self.neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.neo4j_user = os.getenv("NEO4J_USER", "neo4j")
        self.neo4j_password = os.getenv("NEO4J_PASSWORD")
        self.neo4j_database = os.getenv("NEO4J_DATABASE", "neo4j")
        
        if not self.neo4j_password:
            raise ValueError("NEO4J_PASSWORD environment variable not set")
        
        self.driver = GraphDatabase.driver(
            self.neo4j_uri,
            auth=(self.neo4j_user, self.neo4j_password)
        )
    
    def close(self):
        """Close Neo4j connection."""
        if self.driver:
            self.driver.close()
    
    def find_duplicate_entities(self):
        """Find entities with the same name but different UUIDs."""
        logger.info("🔍 Finding duplicate entities...")
        
        with self.driver.session(database=self.neo4j_database) as session:
            # Find duplicate companies
            company_duplicates = session.run("""
                MATCH (n:Company)
                WITH n.name as name, collect(n) as nodes
                WHERE size(nodes) > 1
                RETURN name, nodes
                ORDER BY size(nodes) DESC
            """)
            
            # Find duplicate people
            person_duplicates = session.run("""
                MATCH (n:Person)
                WITH n.name as name, collect(n) as nodes
                WHERE size(nodes) > 1
                RETURN name, nodes
                ORDER BY size(nodes) DESC
            """)
            
            duplicates = {
                'companies': [],
                'people': []
            }
            
            for record in company_duplicates:
                name = record['name']
                nodes = record['nodes']
                duplicates['companies'].append({
                    'name': name,
                    'count': len(nodes),
                    'uuids': [node['uuid'] for node in nodes]
                })
                logger.info(f"📊 Found {len(nodes)} duplicate companies for: {name}")
            
            for record in person_duplicates:
                name = record['name']
                nodes = record['nodes']
                duplicates['people'].append({
                    'name': name,
                    'count': len(nodes),
                    'uuids': [node['uuid'] for node in nodes]
                })
                logger.info(f"📊 Found {len(nodes)} duplicate people for: {name}")
            
            return duplicates
    
    def merge_duplicate_entities(self, duplicates):
        """Merge duplicate entities by keeping the first one and merging relationships."""
        logger.info("🔧 Merging duplicate entities...")
        
        with self.driver.session(database=self.neo4j_database) as session:
            total_merged = 0
            
            # Merge duplicate companies
            for dup in duplicates['companies']:
                name = dup['name']
                uuids = dup['uuids']
                
                if len(uuids) > 1:
                    primary_uuid = uuids[0]  # Keep the first one
                    duplicate_uuids = uuids[1:]  # Merge the rest
                    
                    logger.info(f"🔗 Merging {len(duplicate_uuids)} duplicate companies for: {name}")
                    
                    for dup_uuid in duplicate_uuids:
                        # Transfer all relationships from duplicate to primary
                        # First, transfer incoming relationships
                        session.run("""
                            MATCH (primary:Company {uuid: $primary_uuid})
                            MATCH (duplicate:Company {uuid: $dup_uuid})
                            MATCH (other)-[r]->(duplicate)
                            WHERE NOT EXISTS {
                                MATCH (other)-[r2:RELATES_TO]->(primary)
                                WHERE r2.name = r.name
                            }
                            CREATE (other)-[new_r:RELATES_TO]->(primary)
                            SET new_r = properties(r)
                            DELETE r
                        """, primary_uuid=primary_uuid, dup_uuid=dup_uuid)

                        # Then, transfer outgoing relationships
                        session.run("""
                            MATCH (primary:Company {uuid: $primary_uuid})
                            MATCH (duplicate:Company {uuid: $dup_uuid})
                            MATCH (duplicate)-[r]->(other)
                            WHERE NOT EXISTS {
                                MATCH (primary)-[r2:RELATES_TO]->(other)
                                WHERE r2.name = r.name
                            }
                            CREATE (primary)-[new_r2:RELATES_TO]->(other)
                            SET new_r2 = properties(r)
                            DELETE r
                        """, primary_uuid=primary_uuid, dup_uuid=dup_uuid)

                        # Finally, delete the duplicate node
                        session.run("""
                            MATCH (duplicate:Company {uuid: $dup_uuid})
                            DELETE duplicate
                        """, dup_uuid=dup_uuid)
                        
                        total_merged += 1
                        logger.info(f"✅ Merged company duplicate: {dup_uuid} -> {primary_uuid}")
            
            # Merge duplicate people
            for dup in duplicates['people']:
                name = dup['name']
                uuids = dup['uuids']
                
                if len(uuids) > 1:
                    primary_uuid = uuids[0]  # Keep the first one
                    duplicate_uuids = uuids[1:]  # Merge the rest
                    
                    logger.info(f"🔗 Merging {len(duplicate_uuids)} duplicate people for: {name}")
                    
                    for dup_uuid in duplicate_uuids:
                        # Transfer all relationships from duplicate to primary
                        # First, transfer incoming relationships
                        session.run("""
                            MATCH (primary:Person {uuid: $primary_uuid})
                            MATCH (duplicate:Person {uuid: $dup_uuid})
                            MATCH (other)-[r]->(duplicate)
                            WHERE NOT EXISTS {
                                MATCH (other)-[r2:RELATES_TO]->(primary)
                                WHERE r2.name = r.name
                            }
                            CREATE (other)-[new_r:RELATES_TO]->(primary)
                            SET new_r = properties(r)
                            DELETE r
                        """, primary_uuid=primary_uuid, dup_uuid=dup_uuid)

                        # Then, transfer outgoing relationships
                        session.run("""
                            MATCH (primary:Person {uuid: $primary_uuid})
                            MATCH (duplicate:Person {uuid: $dup_uuid})
                            MATCH (duplicate)-[r]->(other)
                            WHERE NOT EXISTS {
                                MATCH (primary)-[r2:RELATES_TO]->(other)
                                WHERE r2.name = r.name
                            }
                            CREATE (primary)-[new_r2:RELATES_TO]->(other)
                            SET new_r2 = properties(r)
                            DELETE r
                        """, primary_uuid=primary_uuid, dup_uuid=dup_uuid)

                        # Finally, delete the duplicate node
                        session.run("""
                            MATCH (duplicate:Person {uuid: $dup_uuid})
                            DELETE duplicate
                        """, dup_uuid=dup_uuid)
                        
                        total_merged += 1
                        logger.info(f"✅ Merged person duplicate: {dup_uuid} -> {primary_uuid}")
            
            logger.info(f"✅ Total entities merged: {total_merged}")
            return total_merged
    
    def fix_name_variations(self):
        """Fix name variations like 'Winfried Engelbrecht Bresges' vs 'ENGELBRECHT-BRESGES Winfried'."""
        logger.info("🔧 Fixing name variations...")
        
        with self.driver.session(database=self.neo4j_database) as session:
            # Fix Winfried name variations - first transfer incoming relationships
            session.run("""
                MATCH (n1:Person) WHERE n1.name = "Winfried Engelbrecht Bresges"
                MATCH (n2:Person) WHERE n2.name = "ENGELBRECHT-BRESGES Winfried"
                MATCH (other)-[r]->(n2)
                WHERE NOT EXISTS {
                    MATCH (other)-[r2:RELATES_TO]->(n1)
                    WHERE r2.name = r.name
                }
                CREATE (other)-[new_r:RELATES_TO]->(n1)
                SET new_r = properties(r)
                DELETE r
            """)

            # Then transfer outgoing relationships
            session.run("""
                MATCH (n1:Person) WHERE n1.name = "Winfried Engelbrecht Bresges"
                MATCH (n2:Person) WHERE n2.name = "ENGELBRECHT-BRESGES Winfried"
                MATCH (n2)-[r]->(other)
                WHERE NOT EXISTS {
                    MATCH (n1)-[r2:RELATES_TO]->(other)
                    WHERE r2.name = r.name
                }
                CREATE (n1)-[new_r2:RELATES_TO]->(other)
                SET new_r2 = properties(r)
                DELETE r
            """)

            # Finally delete the variant (first delete any remaining relationships)
            result = session.run("""
                MATCH (n2:Person) WHERE n2.name = "ENGELBRECHT-BRESGES Winfried"
                OPTIONAL MATCH (n2)-[r]-()
                DELETE r, n2
                RETURN count(*) as merged
            """)
            
            merged_count = result.single()['merged'] if result.single() else 0
            if merged_count > 0:
                logger.info(f"✅ Fixed Winfried name variation: merged {merged_count} nodes")
            else:
                logger.info("ℹ️ No Winfried name variations found to fix")
    
    def verify_fixes(self):
        """Verify that duplicates have been fixed."""
        logger.info("🔍 Verifying fixes...")
        
        with self.driver.session(database=self.neo4j_database) as session:
            # Check for remaining duplicates
            remaining_company_dups = session.run("""
                MATCH (n:Company)
                WITH n.name as name, count(n) as count
                WHERE count > 1
                RETURN name, count
                ORDER BY count DESC
            """)
            
            remaining_person_dups = session.run("""
                MATCH (n:Person)
                WITH n.name as name, count(n) as count
                WHERE count > 1
                RETURN name, count
                ORDER BY count DESC
            """)
            
            company_issues = list(remaining_company_dups)
            person_issues = list(remaining_person_dups)
            
            if company_issues:
                logger.warning(f"⚠️ Remaining company duplicates:")
                for record in company_issues:
                    logger.warning(f"  - {record['name']}: {record['count']} entities")
            else:
                logger.info("✅ No remaining company duplicates")
            
            if person_issues:
                logger.warning(f"⚠️ Remaining person duplicates:")
                for record in person_issues:
                    logger.warning(f"  - {record['name']}: {record['count']} entities")
            else:
                logger.info("✅ No remaining person duplicates")
            
            return len(company_issues) == 0 and len(person_issues) == 0
    
    def fix_all_duplicates(self):
        """Fix all duplicate entity issues."""
        logger.info("🚀 Starting duplicate entity fix process...")
        
        try:
            # Find duplicates
            duplicates = self.find_duplicate_entities()
            
            # Merge duplicates
            merged_count = self.merge_duplicate_entities(duplicates)
            
            # Fix name variations
            self.fix_name_variations()
            
            # Verify fixes
            success = self.verify_fixes()
            
            if success:
                logger.info("✅ All duplicate entities fixed successfully")
            else:
                logger.warning("⚠️ Some duplicate entities may still exist")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Failed to fix duplicates: {e}")
            raise
        finally:
            self.close()

def main():
    """Main function to fix duplicate entities."""
    try:
        logger.info("🔧 Duplicate Entity Fixer")
        logger.info("=" * 50)
        
        fixer = DuplicateEntityFixer()
        success = fixer.fix_all_duplicates()
        
        logger.info("=" * 50)
        if success:
            logger.info("✅ Duplicate entity fixes completed successfully")
        else:
            logger.warning("⚠️ Some issues may remain - check logs above")
        
    except Exception as e:
        logger.error(f"❌ Duplicate entity fix failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
