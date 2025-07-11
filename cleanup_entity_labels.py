#!/usr/bin/env python3
"""
Standalone utility to clean up Entity labels from Person and Company nodes.
This script can be run independently or integrated into other workflows.
"""

import asyncio
import logging
import os
from typing import Dict, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EntityLabelCleanup:
    """Utility class for cleaning up Entity labels from specific node types."""
    
    def __init__(
        self,
        neo4j_uri: Optional[str] = None,
        neo4j_user: Optional[str] = None,
        neo4j_password: Optional[str] = None
    ):
        """
        Initialize cleanup utility.
        
        Args:
            neo4j_uri: Neo4j connection URI
            neo4j_user: Neo4j username
            neo4j_password: Neo4j password
        """
        self.neo4j_uri = neo4j_uri or os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.neo4j_user = neo4j_user or os.getenv("NEO4J_USER", "neo4j")
        self.neo4j_password = neo4j_password or os.getenv("NEO4J_PASSWORD", "password")
        self.schema_manager = None
    
    async def initialize(self):
        """Initialize Neo4j connection."""
        try:
            from agent.neo4j_schema_manager import Neo4jSchemaManager
            
            self.schema_manager = Neo4jSchemaManager(
                uri=self.neo4j_uri,
                user=self.neo4j_user,
                password=self.neo4j_password
            )
            
            await self.schema_manager.initialize()
            logger.info("Neo4j connection initialized successfully")
            
        except ImportError as e:
            logger.error(f"Could not import Neo4jSchemaManager: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize Neo4j connection: {e}")
            raise
    
    async def close(self):
        """Close Neo4j connection."""
        if self.schema_manager:
            await self.schema_manager.close()
            self.schema_manager = None
    
    async def check_entity_labels(self) -> Dict[str, int]:
        """
        Check how many nodes have Entity labels.
        
        Returns:
            Dictionary with counts of nodes that have Entity labels
        """
        if not self.schema_manager:
            await self.initialize()
        
        async with self.schema_manager.driver.session() as session:
            # Count Person nodes with Entity label
            person_entity_query = """
            MATCH (n:Person:Entity)
            RETURN count(n) as count
            """
            result = await session.run(person_entity_query)
            record = await result.single()
            person_entity_count = record['count'] if record else 0
            
            # Count Company nodes with Entity label
            company_entity_query = """
            MATCH (n:Company:Entity)
            RETURN count(n) as count
            """
            result = await session.run(company_entity_query)
            record = await result.single()
            company_entity_count = record['count'] if record else 0
            
            return {
                "person_nodes_with_entity": person_entity_count,
                "company_nodes_with_entity": company_entity_count
            }
    
    async def cleanup_entity_labels(self, verbose: bool = True) -> Dict[str, int]:
        """
        Remove Entity labels from Person and Company nodes.
        
        Args:
            verbose: Whether to log detailed information
        
        Returns:
            Dictionary with cleanup statistics
        """
        if not self.schema_manager:
            await self.initialize()
        
        if verbose:
            logger.info("Starting Entity label cleanup...")
        
        async with self.schema_manager.driver.session() as session:
            # Check current state
            counts = await self.check_entity_labels()
            person_entity_count = counts["person_nodes_with_entity"]
            company_entity_count = counts["company_nodes_with_entity"]
            
            if verbose:
                logger.info(f"Found {person_entity_count} Person nodes with Entity label")
                logger.info(f"Found {company_entity_count} Company nodes with Entity label")
            
            # If no nodes need cleanup, return early
            if person_entity_count == 0 and company_entity_count == 0:
                if verbose:
                    logger.info("✅ No Entity labels found to clean up")
                return {
                    "person_nodes_fixed": 0,
                    "company_nodes_fixed": 0,
                    "total_nodes_fixed": 0
                }
            
            # Remove Entity label from Person nodes
            fixed_person_count = 0
            if person_entity_count > 0:
                if verbose:
                    logger.info("Removing Entity label from Person nodes...")
                remove_person_entity_query = """
                MATCH (n:Person:Entity)
                REMOVE n:Entity
                RETURN count(n) as fixed_count
                """
                result = await session.run(remove_person_entity_query)
                record = await result.single()
                fixed_person_count = record['fixed_count'] if record else 0
                if verbose:
                    logger.info(f"✅ Fixed {fixed_person_count} Person nodes")
            
            # Remove Entity label from Company nodes
            fixed_company_count = 0
            if company_entity_count > 0:
                if verbose:
                    logger.info("Removing Entity label from Company nodes...")
                remove_company_entity_query = """
                MATCH (n:Company:Entity)
                REMOVE n:Entity
                RETURN count(n) as fixed_count
                """
                result = await session.run(remove_company_entity_query)
                record = await result.single()
                fixed_company_count = record['fixed_count'] if record else 0
                if verbose:
                    logger.info(f"✅ Fixed {fixed_company_count} Company nodes")
            
            total_fixed = fixed_person_count + fixed_company_count
            
            if verbose:
                logger.info(f"✅ Entity label cleanup complete: {total_fixed} nodes fixed")
            
            return {
                "person_nodes_fixed": fixed_person_count,
                "company_nodes_fixed": fixed_company_count,
                "total_nodes_fixed": total_fixed
            }
    
    async def verify_cleanup(self) -> bool:
        """
        Verify that no Person or Company nodes have Entity labels.
        
        Returns:
            True if cleanup was successful (no Entity labels remain)
        """
        counts = await self.check_entity_labels()
        return counts["person_nodes_with_entity"] == 0 and counts["company_nodes_with_entity"] == 0


async def main():
    """Main function for standalone execution."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Clean up Entity labels from Person and Company nodes")
    parser.add_argument("--check-only", action="store_true", help="Only check for Entity labels, don't remove them")
    parser.add_argument("--quiet", "-q", action="store_true", help="Quiet mode - minimal output")
    parser.add_argument("--neo4j-uri", help="Neo4j URI (default: from NEO4J_URI env var)")
    parser.add_argument("--neo4j-user", help="Neo4j username (default: from NEO4J_USER env var)")
    parser.add_argument("--neo4j-password", help="Neo4j password (default: from NEO4J_PASSWORD env var)")
    
    args = parser.parse_args()
    
    # Configure logging
    if args.quiet:
        logging.getLogger().setLevel(logging.WARNING)
    
    # Create cleanup utility
    cleanup = EntityLabelCleanup(
        neo4j_uri=args.neo4j_uri,
        neo4j_user=args.neo4j_user,
        neo4j_password=args.neo4j_password
    )
    
    try:
        await cleanup.initialize()
        
        if args.check_only:
            # Just check for Entity labels
            counts = await cleanup.check_entity_labels()
            print(f"Person nodes with Entity label: {counts['person_nodes_with_entity']}")
            print(f"Company nodes with Entity label: {counts['company_nodes_with_entity']}")
            total = counts['person_nodes_with_entity'] + counts['company_nodes_with_entity']
            print(f"Total nodes with Entity label: {total}")
            
            if total > 0:
                print("\n💡 Run without --check-only to clean up these labels")
        else:
            # Perform cleanup
            result = await cleanup.cleanup_entity_labels(verbose=not args.quiet)
            
            if not args.quiet:
                print("\n" + "="*50)
                print("CLEANUP SUMMARY")
                print("="*50)
                print(f"Person nodes fixed: {result['person_nodes_fixed']}")
                print(f"Company nodes fixed: {result['company_nodes_fixed']}")
                print(f"Total nodes fixed: {result['total_nodes_fixed']}")
                
                # Verify cleanup
                if await cleanup.verify_cleanup():
                    print("✅ Verification successful: No Entity labels remain")
                else:
                    print("⚠️  Verification failed: Some Entity labels may still exist")
    
    except Exception as e:
        logger.error(f"Cleanup failed: {e}")
        return 1
    
    finally:
        await cleanup.close()
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main()))
