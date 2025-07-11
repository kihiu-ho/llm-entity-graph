#!/usr/bin/env python3
"""
Wrapper script for document ingestion with automatic Entity label cleanup.
This script runs the standard ingestion pipeline and then automatically
cleans up any Entity labels from Person and Company nodes.
"""

import asyncio
import logging
import sys
import argparse
from pathlib import Path
from typing import Dict, Any

# Import the ingestion pipeline
from ingestion.ingest import DocumentIngestionPipeline
from agent.models import IngestionConfig

# Import the cleanup utility
from cleanup_entity_labels import EntityLabelCleanup

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def _cleanup_neo4j_only(verbose: bool = False) -> Dict[str, Any]:
    """
    Clean up Neo4j database only (without ingestion).

    Args:
        verbose: Whether to enable verbose logging

    Returns:
        Dictionary with cleanup results
    """
    from ingestion.graph_builder import create_graph_builder
    from agent.db_utils import initialize_database, close_database, db_pool
    from agent.graph_utils import initialize_graph, close_graph

    logger.info("🗑️  Starting comprehensive Neo4j database cleanup...")

    try:
        # Initialize connections
        await initialize_database()
        await initialize_graph()

        # Create graph builder for cleanup
        graph_builder = create_graph_builder()
        await graph_builder.initialize()

        # Step 1: Clear knowledge graph
        logger.info("🧹 Step 1: Clearing knowledge graph...")
        await graph_builder.clear_graph()
        logger.info("✅ Knowledge graph cleared")

        # Step 2: Clean PostgreSQL database
        logger.info("🧹 Step 2: Cleaning PostgreSQL database...")
        async with db_pool.acquire() as conn:
            async with conn.transaction():
                # Get counts before cleanup
                messages_count = await conn.fetchval("SELECT COUNT(*) FROM messages")
                sessions_count = await conn.fetchval("SELECT COUNT(*) FROM sessions")
                chunks_count = await conn.fetchval("SELECT COUNT(*) FROM chunks")
                documents_count = await conn.fetchval("SELECT COUNT(*) FROM documents")

                if verbose:
                    logger.info(f"Found {messages_count} messages, {sessions_count} sessions, {chunks_count} chunks, {documents_count} documents")

                # Clean tables
                await conn.execute("DELETE FROM messages")
                await conn.execute("DELETE FROM sessions")
                await conn.execute("DELETE FROM chunks")
                await conn.execute("DELETE FROM documents")

                logger.info("✅ PostgreSQL database cleaned")

        # Step 3: Clean up Entity labels
        logger.info("🧹 Step 3: Cleaning up Entity labels...")
        cleanup = EntityLabelCleanup()
        await cleanup.initialize()

        cleanup_result = await cleanup.cleanup_entity_labels(verbose=verbose)

        if cleanup_result['total_nodes_fixed'] > 0:
            logger.info(f"✅ Entity label cleanup: {cleanup_result['total_nodes_fixed']} nodes fixed")
        else:
            logger.info("✅ No Entity labels found to clean up")

        await cleanup.close()

        # Close connections
        await graph_builder.close()
        await close_graph()
        await close_database()

        logger.info("🎉 Neo4j database cleanup completed successfully!")

        return {
            "cleanup_performed": True,
            "knowledge_graph_cleared": True,
            "postgresql_cleaned": True,
            "entity_labels_fixed": cleanup_result['total_nodes_fixed'],
            "messages_removed": messages_count,
            "sessions_removed": sessions_count,
            "chunks_removed": chunks_count,
            "documents_removed": documents_count
        }

    except Exception as e:
        logger.error(f"❌ Neo4j cleanup failed: {e}")
        raise


async def ingest_with_cleanup(
    documents_folder: str = "documents",
    clean_before_ingest: bool = False,
    clean_neo4j_only: bool = False,
    chunk_size: int = 12000,
    chunk_overlap: int = 1200,
    use_semantic_chunking: bool = True,
    extract_entities: bool = True,
    skip_graph_building: bool = False,
    verbose: bool = False
):
    """
    Run document ingestion followed by Entity label cleanup.

    Args:
        documents_folder: Folder containing documents to ingest
        clean_before_ingest: Whether to clean existing data before ingestion
        clean_neo4j_only: Whether to only clean Neo4j database (skip ingestion)
        chunk_size: Size of document chunks
        chunk_overlap: Overlap between chunks
        use_semantic_chunking: Whether to use semantic chunking
        extract_entities: Whether to extract entities
        skip_graph_building: Whether to skip knowledge graph building
        verbose: Whether to enable verbose logging
    """
    
    # Configure logging
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Handle Neo4j-only cleanup mode
    if clean_neo4j_only:
        logger.info("🧹 Starting Neo4j database cleanup only")
        return await _cleanup_neo4j_only(verbose)

    logger.info("🚀 Starting document ingestion with automatic Entity label cleanup")

    # Create ingestion configuration
    config = IngestionConfig(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        use_semantic_chunking=use_semantic_chunking,
        extract_entities=extract_entities,
        skip_graph_building=skip_graph_building
    )

    # Create ingestion pipeline
    pipeline = DocumentIngestionPipeline(
        config=config,
        documents_folder=documents_folder,
        clean_before_ingest=clean_before_ingest
    )

    # Create cleanup utility
    cleanup = EntityLabelCleanup()
    
    try:
        # Step 1: Run document ingestion
        logger.info("📄 Step 1: Running document ingestion...")
        
        def progress_callback(current: int, total: int):
            logger.info(f"Progress: {current}/{total} documents processed")
        
        results = await pipeline.ingest_documents(progress_callback)
        
        # Log ingestion summary
        total_chunks = sum(r.chunks_created for r in results)
        total_entities = sum(r.entities_extracted for r in results)
        total_episodes = sum(r.relationships_created for r in results)
        total_errors = sum(len(r.errors) for r in results)
        
        logger.info(f"✅ Ingestion complete: {len(results)} documents, {total_chunks} chunks, {total_entities} entities, {total_episodes} episodes")
        
        if total_errors > 0:
            logger.warning(f"⚠️  {total_errors} errors occurred during ingestion")
        
        # Step 2: Run Entity label cleanup (only if graph building was enabled)
        if not skip_graph_building:
            logger.info("🧹 Step 2: Running Entity label cleanup...")
            
            await cleanup.initialize()
            
            # Check if cleanup is needed
            counts = await cleanup.check_entity_labels()
            total_entity_labels = counts["person_nodes_with_entity"] + counts["company_nodes_with_entity"]
            
            if total_entity_labels > 0:
                logger.info(f"Found {total_entity_labels} nodes with Entity labels to clean up")
                
                # Perform cleanup
                cleanup_result = await cleanup.cleanup_entity_labels(verbose=verbose)
                
                logger.info(f"✅ Cleanup complete: {cleanup_result['total_nodes_fixed']} nodes fixed")
            else:
                logger.info("✅ No Entity labels found - cleanup not needed")
        else:
            logger.info("⏭️  Skipping Entity label cleanup (graph building was disabled)")
        
        # Step 3: Final summary
        logger.info("🎉 Document ingestion with cleanup completed successfully!")
        
        return {
            "ingestion_results": results,
            "cleanup_performed": not skip_graph_building,
            "total_documents": len(results),
            "total_chunks": total_chunks,
            "total_entities": total_entities,
            "total_episodes": total_episodes,
            "total_errors": total_errors
        }
        
    except Exception as e:
        logger.error(f"❌ Process failed: {e}")
        raise
    
    finally:
        # Clean up resources
        await pipeline.close()
        await cleanup.close()


async def main():
    """Main function for command-line execution."""
    parser = argparse.ArgumentParser(
        description="Ingest documents with automatic Entity label cleanup",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic ingestion with cleanup
  python ingest_with_cleanup.py

  # Ingest specific folder with cleanup
  python ingest_with_cleanup.py --documents my_docs

  # Fast mode (skip graph building and cleanup)
  python ingest_with_cleanup.py --fast

  # Clean existing data first, then ingest with cleanup
  python ingest_with_cleanup.py --clean --verbose

  # Only clean Neo4j database (no ingestion)
  python ingest_with_cleanup.py --clean-neo4j-only --verbose

  # Clean Neo4j database quietly
  python ingest_with_cleanup.py --clean-neo4j-only
        """
    )
    
    parser.add_argument("--documents", "-d", default="documents", 
                       help="Documents folder path (default: documents)")
    parser.add_argument("--clean", "-c", action="store_true",
                       help="Clean existing data before ingestion")
    parser.add_argument("--clean-neo4j-only", action="store_true",
                       help="Only clean Neo4j database (skip ingestion)")
    parser.add_argument("--chunk-size", type=int, default=12000,
                       help="Chunk size for splitting documents (default: 12000)")
    parser.add_argument("--chunk-overlap", type=int, default=1200,
                       help="Chunk overlap size (default: 1200)")
    parser.add_argument("--no-semantic", action="store_true",
                       help="Disable semantic chunking")
    parser.add_argument("--no-entities", action="store_true",
                       help="Disable entity extraction")
    parser.add_argument("--fast", "-f", action="store_true",
                       help="Fast mode: skip knowledge graph building (and cleanup)")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Enable verbose logging")
    
    args = parser.parse_args()

    # Validate arguments
    if args.clean_neo4j_only and args.clean:
        logger.error("Cannot use both --clean-neo4j-only and --clean together")
        return 1

    if args.clean_neo4j_only and args.fast:
        logger.warning("--fast option ignored when using --clean-neo4j-only")

    # Check if documents folder exists (only for ingestion mode)
    if not args.clean_neo4j_only and not Path(args.documents).exists():
        logger.error(f"Documents folder not found: {args.documents}")
        return 1
    
    try:
        result = await ingest_with_cleanup(
            documents_folder=args.documents,
            clean_before_ingest=args.clean,
            clean_neo4j_only=args.clean_neo4j_only,
            chunk_size=args.chunk_size,
            chunk_overlap=args.chunk_overlap,
            use_semantic_chunking=not args.no_semantic,
            extract_entities=not args.no_entities,
            skip_graph_building=args.fast,
            verbose=args.verbose
        )
        
        # Print final summary
        print("\n" + "="*60)
        print("📊 FINAL SUMMARY")
        print("="*60)

        if 'total_documents' in result:
            # Standard ingestion mode
            print(f"Documents processed: {result['total_documents']}")
            print(f"Chunks created: {result['total_chunks']}")
            print(f"Entities extracted: {result['total_entities']}")
            print(f"Graph episodes: {result['total_episodes']}")
            print(f"Errors: {result['total_errors']}")
            print(f"Entity cleanup performed: {'Yes' if result['cleanup_performed'] else 'No (fast mode)'}")
        else:
            # Cleanup-only mode
            print(f"Knowledge graph cleared: {'Yes' if result['knowledge_graph_cleared'] else 'No'}")
            print(f"PostgreSQL cleaned: {'Yes' if result['postgresql_cleaned'] else 'No'}")
            print(f"Documents removed: {result.get('documents_removed', 0)}")
            print(f"Chunks removed: {result.get('chunks_removed', 0)}")
            print(f"Messages removed: {result.get('messages_removed', 0)}")
            print(f"Sessions removed: {result.get('sessions_removed', 0)}")
            print(f"Entity labels fixed: {result.get('entity_labels_fixed', 0)}")

        print("="*60)
        print("✅ All operations completed successfully!")
        
        return 0
        
    except KeyboardInterrupt:
        logger.info("❌ Process interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"❌ Process failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
