"""
Main ingestion script for processing markdown documents into vector DB and knowledge graph.
"""

import os
import asyncio
import logging
import json
import glob
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import argparse

import asyncpg
from dotenv import load_dotenv

from .chunker import ChunkingConfig, create_chunker, DocumentChunk
from .embedder import create_embedder
from .graph_builder import create_graph_builder

# Import agent utilities
try:
    from ..agent.db_utils import initialize_database, close_database, get_db_pool
    from ..agent.graph_utils import initialize_graph, close_graph
    from ..agent.models import IngestionConfig, IngestionResult
except ImportError:
    # For direct execution or testing
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from agent.db_utils import initialize_database, close_database, get_db_pool
    from agent.graph_utils import initialize_graph, close_graph
    from agent.models import IngestionConfig, IngestionResult

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class DocumentIngestionPipeline:
    """Pipeline for ingesting documents into vector DB and knowledge graph."""
    
    def __init__(
        self,
        config: IngestionConfig,
        documents_folder: str = "documents",
        clean_before_ingest: bool = False
    ):
        """
        Initialize ingestion pipeline.
        
        Args:
            config: Ingestion configuration
            documents_folder: Folder containing markdown documents
            clean_before_ingest: Whether to clean existing data before ingestion
        """
        self.config = config
        self.documents_folder = documents_folder
        self.clean_before_ingest = clean_before_ingest
        
        # Initialize components
        self.chunker_config = ChunkingConfig(
            chunk_size=config.chunk_size,
            chunk_overlap=config.chunk_overlap,
            max_chunk_size=config.max_chunk_size,
            use_semantic_splitting=config.use_semantic_chunking
        )
        
        self.chunker = create_chunker(self.chunker_config)
        self.embedder = create_embedder()
        self.graph_builder = create_graph_builder()
        
        self._initialized = False
    
    async def initialize(self):
        """Initialize database connections and Neo4j schema."""
        if self._initialized:
            return

        logger.info("Initializing ingestion pipeline...")

        # Initialize database connections
        await initialize_database()
        await initialize_graph()
        await self.graph_builder.initialize()

        # Initialize Neo4j schema for Person and Company nodes
        try:
            from agent.neo4j_schema_manager import Neo4jSchemaManager
            schema_manager = Neo4jSchemaManager()
            await schema_manager.initialize()
            logger.info("✓ Neo4j schema initialized with Person and Company node types")
        except Exception as e:
            logger.warning(f"Failed to initialize Neo4j schema: {e}")

        self._initialized = True
        logger.info("Ingestion pipeline initialized")
    
    async def close(self):
        """Close database connections."""
        if self._initialized:
            await self.graph_builder.close()
            await close_graph()
            await close_database()
            self._initialized = False
    
    async def ingest_documents(
        self,
        progress_callback: Optional[callable] = None
    ) -> List[IngestionResult]:
        """
        Ingest all documents from the documents folder.
        
        Args:
            progress_callback: Optional callback for progress updates
        
        Returns:
            List of ingestion results
        """
        if not self._initialized:
            await self.initialize()
        
        # Clean existing data if requested
        if self.clean_before_ingest:
            await self._clean_databases()
        
        # Find all markdown files
        markdown_files = self._find_markdown_files()
        
        if not markdown_files:
            logger.warning(f"No markdown files found in {self.documents_folder}")
            return []
        
        logger.info(f"Found {len(markdown_files)} markdown files to process")
        
        results = []
        
        for i, file_path in enumerate(markdown_files):
            try:
                logger.info(f"Processing file {i+1}/{len(markdown_files)}: {file_path}")
                
                result = await self._ingest_single_document(file_path)
                results.append(result)
                
                if progress_callback:
                    progress_callback(i + 1, len(markdown_files))
                
            except Exception as e:
                logger.error(f"Failed to process {file_path}: {e}")
                results.append(IngestionResult(
                    document_id="",
                    title=os.path.basename(file_path),
                    chunks_created=0,
                    entities_extracted=0,
                    relationships_created=0,
                    processing_time_ms=0,
                    errors=[str(e)]
                ))
        
        # Log summary
        total_chunks = sum(r.chunks_created for r in results)
        total_errors = sum(len(r.errors) for r in results)
        
        logger.info(f"Ingestion complete: {len(results)} documents, {total_chunks} chunks, {total_errors} errors")
        
        return results
    
    async def _ingest_single_document(self, file_path: str) -> IngestionResult:
        """
        Ingest a single document.
        
        Args:
            file_path: Path to the document file
        
        Returns:
            Ingestion result
        """
        start_time = datetime.now()
        
        # Read document
        document_content = self._read_document(file_path)
        document_title = self._extract_title(document_content, file_path)
        document_source = os.path.relpath(file_path, self.documents_folder)
        
        # Extract metadata from content
        document_metadata = self._extract_document_metadata(document_content, file_path)
        
        logger.info(f"Processing document: {document_title}")
        
        # Chunk the document
        try:
            chunks = await self.chunker.chunk_document(
                content=document_content,
                title=document_title,
                source=document_source,
                metadata=document_metadata
            )
        except Exception as chunk_error:
            logger.error(f"Chunking failed: {chunk_error}")
            # Check if it's the specific error we're trying to fix
            if "object list can't be used in 'await' expression" in str(chunk_error):
                logger.error("🎯 FOUND THE AWAIT ERROR IN CHUNKING!")
                import traceback
                traceback.print_exc()
            raise chunk_error
        
        if not chunks:
            logger.warning(f"No chunks created for {document_title}")
            return IngestionResult(
                document_id="",
                title=document_title,
                chunks_created=0,
                entities_extracted=0,
                relationships_created=0,
                processing_time_ms=(datetime.now() - start_time).total_seconds() * 1000,
                errors=["No chunks created"]
            )
        
        logger.info(f"Created {len(chunks)} chunks")
        
        # Extract entities if configured
        entities_extracted = 0
        if self.config.extract_entities:
            logger.info("Using document-level entity extraction for better context")
            try:
                chunks = await self.graph_builder.extract_entities_from_document(
                    chunks,
                    extract_companies=True,
                    extract_technologies=True,
                    extract_people=True,
                    extract_financial_entities=True,
                    extract_corporate_roles=True,
                    extract_ownership=True,
                    extract_transactions=True,
                    extract_personal_connections=True,
                    use_llm=True,
                    use_llm_for_companies=True,  # Use LLM for companies
                    use_llm_for_technologies=True,  # Use LLM for technologies
                    use_llm_for_people=True,  # Use LLM for people
                    use_llm_for_financial_entities=True,  # Use LLM for financial entities
                    use_llm_for_corporate_roles=True,  # Use LLM for corporate roles
                    use_llm_for_ownership=True,  # Use LLM for ownership
                    use_llm_for_transactions=True,  # Use LLM for transactions
                    use_llm_for_personal_connections=True  # Use LLM for personal connections
                )
            except Exception as entity_error:
                logger.error(f"Entity extraction failed: {entity_error}")
                # Check if it's the specific error we're trying to fix
                if "object list can't be used in 'await' expression" in str(entity_error):
                    logger.error("🎯 FOUND THE AWAIT ERROR IN ENTITY EXTRACTION!")
                    import traceback
                    traceback.print_exc()
                # Continue without entity extraction
                logger.warning("Continuing without entity extraction due to error")
                chunks = chunks  # Keep original chunks without entities

            # Count entities from document-level extraction (all chunks have same entities)
            if chunks:
                sample_entities = chunks[0].metadata.get("entities", {})
                entities_extracted = 0

                # Debug: Log extracted entities
                logger.info(f"Sample entities structure: {list(sample_entities.keys())}")

                # Count simple list entities
                for category in ["companies", "technologies", "people", "locations", "network_entities"]:
                    category_entities = sample_entities.get(category, [])
                    entities_extracted += len(category_entities)
                    if category_entities:
                        logger.info(f"Found {len(category_entities)} {category}: {category_entities[:5]}...")  # Show first 5

                # Count nested dict entities
                for category in ["financial_entities", "corporate_roles", "ownership", "transactions", "personal_connections"]:
                    nested_entities = sample_entities.get(category, {})
                    if isinstance(nested_entities, dict):
                        for subcategory, items in nested_entities.items():
                            if isinstance(items, list):
                                entities_extracted += len(items)
                                if items:
                                    logger.info(f"Found {len(items)} {category}.{subcategory}: {items[:3]}...")  # Show first 3

            logger.info(f"Extracted {entities_extracted} entities using document-level extraction")
        
        # Generate embeddings
        try:
            embedded_chunks = await self.embedder.embed_chunks(chunks)
            logger.info(f"Generated embeddings for {len(embedded_chunks)} chunks")
        except Exception as embed_error:
            logger.error(f"Embedding failed: {embed_error}")
            # Check if it's the specific error we're trying to fix
            if "object list can't be used in 'await' expression" in str(embed_error):
                logger.error("🎯 FOUND THE AWAIT ERROR IN EMBEDDING!")
                import traceback
                traceback.print_exc()
            raise embed_error
        
        # Save to PostgreSQL
        document_id = await self._save_to_postgres(
            document_title,
            document_source,
            document_content,
            embedded_chunks,
            document_metadata
        )
        
        logger.info(f"Saved document to PostgreSQL with ID: {document_id}")
        
        # Add to knowledge graph (if enabled)
        relationships_created = 0
        graph_errors = []

        if not self.config.skip_graph_building:
            try:
                logger.info("Building knowledge graph relationships (this may take several minutes)...")
                graph_result = await self.graph_builder.add_document_to_graph(
                    chunks=embedded_chunks,
                    document_title=document_title,
                    document_source=document_source,
                    document_metadata=document_metadata
                )

                relationships_created = graph_result.get("episodes_created", 0)
                graph_errors = graph_result.get("errors", [])

                logger.info(f"Added {relationships_created} episodes to knowledge graph")

                # Clean up Entity labels after graph building
                try:
                    logger.info("Cleaning up Entity labels from Person and Company nodes...")
                    cleanup_result = await self._cleanup_entity_labels()
                    if cleanup_result:
                        logger.info(f"✅ Cleaned up Entity labels: {cleanup_result['person_nodes_fixed']} Person nodes, {cleanup_result['company_nodes_fixed']} Company nodes")
                    else:
                        logger.info("✅ No Entity labels found to clean up")
                except Exception as cleanup_error:
                    logger.warning(f"Entity label cleanup failed (non-critical): {cleanup_error}")

            except Exception as e:
                error_msg = f"Failed to add to knowledge graph: {str(e)}"
                logger.error(error_msg)
                graph_errors.append(error_msg)
        else:
            logger.info("Skipping knowledge graph building (skip_graph_building=True)")
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        return IngestionResult(
            document_id=document_id,
            title=document_title,
            chunks_created=len(chunks),
            entities_extracted=entities_extracted,
            relationships_created=relationships_created,
            processing_time_ms=processing_time,
            errors=graph_errors
        )
    
    def _find_markdown_files(self) -> List[str]:
        """Find all markdown files in the documents folder."""
        if not os.path.exists(self.documents_folder):
            logger.error(f"Documents folder not found: {self.documents_folder}")
            return []
        
        patterns = ["*.md", "*.markdown", "*.txt"]
        files = []
        
        for pattern in patterns:
            files.extend(glob.glob(os.path.join(self.documents_folder, "**", pattern), recursive=True))
        
        return sorted(files)
    
    def _read_document(self, file_path: str) -> str:
        """Read document content from file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            # Try with different encoding
            with open(file_path, 'r', encoding='latin-1') as f:
                return f.read()
    
    def _extract_title(self, content: str, file_path: str) -> str:
        """Extract title from document content or filename."""
        # Try to find markdown title
        lines = content.split('\n')
        for line in lines[:10]:  # Check first 10 lines
            line = line.strip()
            if line.startswith('# '):
                return line[2:].strip()
        
        # Fallback to filename
        return os.path.splitext(os.path.basename(file_path))[0]
    
    def _extract_document_metadata(self, content: str, file_path: str) -> Dict[str, Any]:
        """Extract metadata from document content."""
        metadata = {
            "file_path": file_path,
            "file_size": len(content),
            "ingestion_date": datetime.now().isoformat()
        }
        
        # Try to extract YAML frontmatter
        if content.startswith('---'):
            try:
                import yaml
                end_marker = content.find('\n---\n', 4)
                if end_marker != -1:
                    frontmatter = content[4:end_marker]
                    yaml_metadata = yaml.safe_load(frontmatter)
                    if isinstance(yaml_metadata, dict):
                        metadata.update(yaml_metadata)
            except ImportError:
                logger.warning("PyYAML not installed, skipping frontmatter extraction")
            except Exception as e:
                logger.warning(f"Failed to parse frontmatter: {e}")
        
        # Extract some basic metadata from content
        lines = content.split('\n')
        metadata['line_count'] = len(lines)
        metadata['word_count'] = len(content.split())
        
        return metadata
    
    async def _save_to_postgres(
        self,
        title: str,
        source: str,
        content: str,
        chunks: List[DocumentChunk],
        metadata: Dict[str, Any]
    ) -> str:
        """Save document and chunks to PostgreSQL."""
        async with get_db_pool().acquire() as conn:
            async with conn.transaction():
                # Insert document
                document_result = await conn.fetchrow(
                    """
                    INSERT INTO documents (title, source, content, metadata)
                    VALUES ($1, $2, $3, $4)
                    RETURNING id::text
                    """,
                    title,
                    source,
                    content,
                    json.dumps(metadata)
                )
                
                document_id = document_result["id"]
                
                # Insert chunks
                for chunk in chunks:
                    # Convert embedding to PostgreSQL vector string format
                    embedding_data = None
                    if hasattr(chunk, 'embedding') and chunk.embedding:
                        # PostgreSQL vector format: '[1.0,2.0,3.0]' (no spaces after commas)
                        embedding_data = '[' + ','.join(map(str, chunk.embedding)) + ']'
                    
                    await conn.execute(
                        """
                        INSERT INTO chunks (document_id, content, embedding, chunk_index, metadata, token_count)
                        VALUES ($1::uuid, $2, $3::vector, $4, $5, $6)
                        """,
                        document_id,
                        chunk.content,
                        embedding_data,
                        chunk.index,
                        json.dumps(chunk.metadata),
                        chunk.token_count
                    )
                
                return document_id
    
    async def _clean_databases(self):
        """Clean existing data from databases."""
        logger.warning("Cleaning existing data from databases...")

        # Clean PostgreSQL
        db_pool = get_db_pool()
        if db_pool is None:
            logger.error("Database pool not initialized. Cannot clean PostgreSQL.")
            return

        async with db_pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute("DELETE FROM messages")
                await conn.execute("DELETE FROM sessions")
                await conn.execute("DELETE FROM chunks")
                await conn.execute("DELETE FROM documents")

        logger.info("Cleaned PostgreSQL database")
        
        # Clean knowledge graph
        await self.graph_builder.clear_graph()
        logger.info("Cleaned knowledge graph")

    async def _cleanup_entity_labels(self) -> Optional[Dict[str, int]]:
        """
        Clean up Entity labels from Person and Company nodes.

        Returns:
            Dictionary with cleanup statistics or None if no cleanup needed
        """
        try:
            # Import here to avoid circular imports
            from ..agent.neo4j_schema_manager import Neo4jSchemaManager

            schema_manager = Neo4jSchemaManager(
                uri=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
                user=os.getenv("NEO4J_USER", "neo4j"),
                password=os.getenv("NEO4J_PASSWORD", "password")
            )

            try:
                await schema_manager.initialize()

                async with schema_manager.driver.session() as session:
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

                    # If no nodes need cleanup, return None
                    if person_entity_count == 0 and company_entity_count == 0:
                        return None

                    # Remove Entity label from Person nodes
                    fixed_person_count = 0
                    if person_entity_count > 0:
                        remove_person_entity_query = """
                        MATCH (n:Person:Entity)
                        REMOVE n:Entity
                        RETURN count(n) as fixed_count
                        """
                        result = await session.run(remove_person_entity_query)
                        record = await result.single()
                        fixed_person_count = record['fixed_count'] if record else 0

                    # Remove Entity label from Company nodes
                    fixed_company_count = 0
                    if company_entity_count > 0:
                        remove_company_entity_query = """
                        MATCH (n:Company:Entity)
                        REMOVE n:Entity
                        RETURN count(n) as fixed_count
                        """
                        result = await session.run(remove_company_entity_query)
                        record = await result.single()
                        fixed_company_count = record['fixed_count'] if record else 0

                    return {
                        "person_nodes_fixed": fixed_person_count,
                        "company_nodes_fixed": fixed_company_count
                    }

            finally:
                await schema_manager.close()

        except ImportError as e:
            logger.warning(f"Could not import Neo4jSchemaManager for cleanup: {e}")
            return None
        except Exception as e:
            logger.warning(f"Entity label cleanup failed: {e}")
            return None


async def main():
    """Main function for running ingestion."""
    parser = argparse.ArgumentParser(description="Ingest documents into vector DB and knowledge graph")
    parser.add_argument("--documents", "-d", default="documents", help="Documents folder path")
    parser.add_argument("--clean", "-c", action="store_true", help="Clean existing data before ingestion")
    parser.add_argument("--chunk-size", type=int, default=12000, help="Chunk size for splitting documents (optimized for fewer chunks)")
    parser.add_argument("--chunk-overlap", type=int, default=1200, help="Chunk overlap size")
    parser.add_argument("--no-semantic", action="store_true", help="Disable semantic chunking (recommended for large chunks)")
    parser.add_argument("--no-entities", action="store_true", help="Disable entity extraction")
    parser.add_argument("--fast", "-f", action="store_true", help="Fast mode: skip knowledge graph building")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Create ingestion configuration
    config = IngestionConfig(
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
        use_semantic_chunking=not args.no_semantic,
        extract_entities=not args.no_entities,
        skip_graph_building=args.fast
    )
    
    # Create and run pipeline
    pipeline = DocumentIngestionPipeline(
        config=config,
        documents_folder=args.documents,
        clean_before_ingest=args.clean
    )
    
    def progress_callback(current: int, total: int):
        print(f"Progress: {current}/{total} documents processed")
    
    try:
        start_time = datetime.now()
        
        results = await pipeline.ingest_documents(progress_callback)
        
        end_time = datetime.now()
        total_time = (end_time - start_time).total_seconds()
        
        # Print summary
        print("\n" + "="*50)
        print("INGESTION SUMMARY")
        print("="*50)
        print(f"Documents processed: {len(results)}")
        print(f"Total chunks created: {sum(r.chunks_created for r in results)}")
        print(f"Total entities extracted: {sum(r.entities_extracted for r in results)}")
        print(f"Total graph episodes: {sum(r.relationships_created for r in results)}")
        print(f"Total errors: {sum(len(r.errors) for r in results)}")
        print(f"Total processing time: {total_time:.2f} seconds")
        print()
        
        # Print individual results
        for result in results:
            status = "✓" if not result.errors else "✗"
            print(f"{status} {result.title}: {result.chunks_created} chunks, {result.entities_extracted} entities")
            
            if result.errors:
                for error in result.errors:
                    print(f"  Error: {error}")
        
    except KeyboardInterrupt:
        print("\nIngestion interrupted by user")
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        raise
    finally:
        await pipeline.close()


if __name__ == "__main__":
    asyncio.run(main())