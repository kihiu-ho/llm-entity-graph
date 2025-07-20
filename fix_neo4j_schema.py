#!/usr/bin/env python3
"""
Fix Neo4j schema issues for Graphiti compatibility.

This script addresses the following issues:
1. Missing properties: fact_embedding, episodes
2. Missing fulltext index: edge_name_and_fact
3. Schema compatibility with Graphiti queries
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

class Neo4jSchemaFixer:
    """Fix Neo4j schema issues for Graphiti compatibility."""
    
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
    
    def check_database_status(self):
        """Check current database status and identify issues."""
        logger.info("🔍 Checking Neo4j database status...")
        
        with self.driver.session(database=self.neo4j_database) as session:
            # Check node counts
            result = session.run("MATCH (n) RETURN labels(n) as labels, count(n) as count")
            node_stats = {}
            for record in result:
                labels = tuple(sorted(record['labels']))
                node_stats[labels] = record['count']
            
            logger.info(f"📊 Node statistics: {node_stats}")
            
            # Check relationship counts
            result = session.run("MATCH ()-[r]->() RETURN type(r) as type, count(r) as count")
            rel_stats = {}
            for record in result:
                rel_stats[record['type']] = record['count']
            
            logger.info(f"📊 Relationship statistics: {rel_stats}")
            
            # Check for missing properties
            self.check_missing_properties(session)
            
            # Check indices
            self.check_indices(session)
    
    def check_missing_properties(self, session):
        """Check for missing properties that Graphiti expects."""
        logger.info("🔍 Checking for missing properties...")
        
        # Check for fact_embedding property
        result = session.run("""
            MATCH ()-[r:RELATES_TO]->()
            WHERE r.fact_embedding IS NOT NULL
            RETURN count(r) as count
        """)
        fact_embedding_count = result.single()['count']
        logger.info(f"📊 Relationships with fact_embedding: {fact_embedding_count}")
        
        # Check for episodes property
        result = session.run("""
            MATCH ()-[r:RELATES_TO]->()
            WHERE r.episodes IS NOT NULL
            RETURN count(r) as count
        """)
        episodes_count = result.single()['count']
        logger.info(f"📊 Relationships with episodes: {episodes_count}")
        
        if fact_embedding_count == 0:
            logger.warning("⚠️ No relationships have fact_embedding property")
        
        if episodes_count == 0:
            logger.warning("⚠️ No relationships have episodes property")
    
    def check_indices(self, session):
        """Check for required indices."""
        logger.info("🔍 Checking indices...")
        
        # List all indices
        result = session.run("SHOW INDEXES")
        indices = []
        for record in result:
            indices.append({
                'name': record.get('name', ''),
                'type': record.get('type', ''),
                'state': record.get('state', ''),
                'labels': record.get('labelsOrTypes', []),
                'properties': record.get('properties', [])
            })
        
        logger.info(f"📊 Found {len(indices)} indices")
        
        # Check for specific indices
        fulltext_indices = [idx for idx in indices if idx['type'] == 'FULLTEXT']
        logger.info(f"📊 Fulltext indices: {len(fulltext_indices)}")
        
        edge_name_fact_exists = any(
            idx['name'] == 'edge_name_and_fact' for idx in fulltext_indices
        )
        
        if not edge_name_fact_exists:
            logger.warning("⚠️ Missing fulltext index: edge_name_and_fact")
        else:
            logger.info("✅ Found edge_name_and_fact index")
    
    def create_missing_indices(self):
        """Create missing indices required by Graphiti."""
        logger.info("🔧 Creating missing indices...")
        
        with self.driver.session(database=self.neo4j_database) as session:
            try:
                # Create fulltext index for relationships
                logger.info("📝 Creating edge_name_and_fact fulltext index...")
                session.run("""
                    CREATE FULLTEXT INDEX edge_name_and_fact IF NOT EXISTS
                    FOR ()-[r:RELATES_TO]-()
                    ON EACH [r.name, r.fact]
                """)
                logger.info("✅ Created edge_name_and_fact index")
                
                # Create vector index for fact embeddings if supported
                try:
                    logger.info("📝 Creating vector index for fact_embedding...")
                    session.run("""
                        CREATE VECTOR INDEX fact_embedding_index IF NOT EXISTS
                        FOR ()-[r:RELATES_TO]-()
                        ON (r.fact_embedding)
                        OPTIONS {indexConfig: {
                            `vector.dimensions`: 1536,
                            `vector.similarity_function`: 'cosine'
                        }}
                    """)
                    logger.info("✅ Created fact_embedding vector index")
                except Exception as e:
                    logger.warning(f"⚠️ Could not create vector index (may not be supported): {e}")
                
            except Exception as e:
                logger.error(f"❌ Failed to create indices: {e}")
    
    def add_missing_properties(self):
        """Add missing properties to existing relationships."""
        logger.info("🔧 Adding missing properties to relationships...")
        
        with self.driver.session(database=self.neo4j_database) as session:
            try:
                # Add empty episodes array to relationships that don't have it
                result = session.run("""
                    MATCH ()-[r:RELATES_TO]->()
                    WHERE r.episodes IS NULL
                    SET r.episodes = []
                    RETURN count(r) as updated
                """)
                updated_count = result.single()['updated']
                logger.info(f"✅ Added episodes property to {updated_count} relationships")
                
                # Note: We don't add fact_embedding as it requires actual embeddings
                # This will be handled by Graphiti during normal operation
                
            except Exception as e:
                logger.error(f"❌ Failed to add missing properties: {e}")
    
    def fix_schema_issues(self):
        """Fix all identified schema issues."""
        logger.info("🚀 Starting Neo4j schema fixes...")
        
        try:
            # Check current status
            self.check_database_status()
            
            # Create missing indices
            self.create_missing_indices()
            
            # Add missing properties
            self.add_missing_properties()
            
            # Verify fixes
            logger.info("🔍 Verifying fixes...")
            self.check_database_status()
            
            logger.info("✅ Schema fixes completed successfully")
            
        except Exception as e:
            logger.error(f"❌ Schema fix failed: {e}")
            raise
        finally:
            self.close()

def main():
    """Main function to fix Neo4j schema issues."""
    try:
        logger.info("🔧 Neo4j Schema Fixer")
        logger.info("=" * 50)
        
        fixer = Neo4jSchemaFixer()
        fixer.fix_schema_issues()
        
        logger.info("=" * 50)
        logger.info("✅ Schema fixes completed")
        
    except Exception as e:
        logger.error(f"❌ Schema fix failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
