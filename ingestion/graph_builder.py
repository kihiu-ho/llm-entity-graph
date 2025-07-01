"""
Knowledge graph builder for extracting entities and relationships.
"""

import os
import logging
from typing import List, Dict, Any, Optional, Set, Tuple
from datetime import datetime, timezone
import asyncio
import re
import json

from graphiti_core import Graphiti
from graphiti_core.llm_client.config import LLMConfig
from graphiti_core.llm_client.openai_client import OpenAIClient
from dotenv import load_dotenv

from .chunker import DocumentChunk

# Import graph utilities
try:
    from ..agent.graph_utils import GraphitiClient
except ImportError:
    # For direct execution or testing
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from agent.graph_utils import GraphitiClient

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class GraphBuilder:
    """Builds knowledge graph from document chunks."""

    def __init__(self):
        """Initialize graph builder."""
        self.graph_client = GraphitiClient()
        self._initialized = False
        self._llm_client = None

        # LLM configuration for entity extraction
        self.llm_api_key = os.getenv("LLM_API_KEY")
        self.llm_choice = os.getenv("LLM_CHOICE")
        self.llm_base_url = os.getenv("LLM_BASE_URL")
    
    async def initialize(self):
        """Initialize graph client and LLM client."""
        if not self._initialized:
            await self.graph_client.initialize()

            # Initialize LLM client for entity extraction
            if self.llm_api_key:
                llm_config = LLMConfig(
                    api_key=self.llm_api_key,
                    model=self.llm_choice,
                    small_model=self.llm_choice,
                    base_url=self.llm_base_url
                )
                self._llm_client = OpenAIClient(config=llm_config)
                logger.info(f"LLM client initialized for entity extraction: {self.llm_choice}")
            else:
                logger.warning("No LLM API key provided, falling back to rule-based entity extraction")

            self._initialized = True
    
    async def close(self):
        """Close graph client."""
        if self._initialized:
            await self.graph_client.close()
            self._initialized = False
    
    async def add_document_to_graph(
        self,
        chunks: List[DocumentChunk],
        document_title: str,
        document_source: str,
        document_metadata: Optional[Dict[str, Any]] = None,
        batch_size: int = 3  # Reduced batch size for Graphiti
    ) -> Dict[str, Any]:
        """
        Add document chunks to the knowledge graph.
        
        Args:
            chunks: List of document chunks
            document_title: Title of the document
            document_source: Source of the document
            document_metadata: Additional metadata
            batch_size: Number of chunks to process in each batch
        
        Returns:
            Processing results
        """
        if not self._initialized:
            await self.initialize()
        
        if not chunks:
            return {"episodes_created": 0, "errors": []}
        
        logger.info(f"Adding {len(chunks)} chunks to knowledge graph for document: {document_title}")
        logger.info("⚠️ Large chunks will be truncated to avoid Graphiti token limits.")
        logger.info(f"Document source: {document_source}")
        logger.info(f"Document metadata: {document_metadata}")
        logger.info(f"Batch size: {batch_size}")

        # Check for oversized chunks and warn
        oversized_chunks = [i for i, chunk in enumerate(chunks) if len(chunk.content) > 6000]
        if oversized_chunks:
            logger.warning(f"Found {len(oversized_chunks)} chunks over 6000 chars that will be truncated: {oversized_chunks}")

        # Log chunk statistics
        chunk_sizes = [len(chunk.content) for chunk in chunks]
        logger.info(f"Chunk size statistics - Min: {min(chunk_sizes)}, Max: {max(chunk_sizes)}, Avg: {sum(chunk_sizes)/len(chunk_sizes):.1f}")

        episodes_created = 0
        errors = []
        
        # Process chunks one by one to avoid overwhelming Graphiti
        logger.info("Starting episode creation process...")

        for i, chunk in enumerate(chunks):
            try:
                logger.debug(f"Processing chunk {i+1}/{len(chunks)} (index: {chunk.index})")

                # Create episode ID
                episode_id = f"{document_source}_{chunk.index}_{datetime.now().timestamp()}"
                logger.debug(f"Created episode ID: {episode_id}")

                # Prepare episode content with size limits
                episode_content = self._prepare_episode_content(
                    chunk,
                    document_title,
                    document_metadata
                )
                logger.debug(f"Episode content prepared - Original: {len(chunk.content)} chars, Processed: {len(episode_content)} chars")

                # Create source description (shorter)
                source_description = f"Document: {document_title} (Chunk: {chunk.index})"

                # Log entity information if available
                if hasattr(chunk, 'metadata') and 'entities' in chunk.metadata:
                    entities = chunk.metadata['entities']
                    entity_summary = {}
                    for category, items in entities.items():
                        if isinstance(items, dict):
                            entity_summary[category] = sum(len(subitems) if isinstance(subitems, list) else 1 for subitems in items.values())
                        elif isinstance(items, list):
                            entity_summary[category] = len(items)
                    logger.debug(f"Chunk {chunk.index} entities: {entity_summary}")

                # Add episode to graph
                logger.debug(f"Adding episode to graph...")
                await self.graph_client.add_episode(
                    episode_id=episode_id,
                    content=episode_content,
                    source=source_description,
                    timestamp=datetime.now(timezone.utc),
                    metadata={
                        "document_title": document_title,
                        "document_source": document_source,
                        "chunk_index": chunk.index,
                        "original_length": len(chunk.content),
                        "processed_length": len(episode_content),
                        "entities": chunk.metadata.get('entities', {}) if hasattr(chunk, 'metadata') else {}
                    }
                )

                episodes_created += 1
                logger.info(f"✓ Added episode {episode_id} to knowledge graph ({episodes_created}/{len(chunks)})")

                # Small delay between each episode to reduce API pressure
                if i < len(chunks) - 1:
                    logger.debug(f"Waiting 0.5s before next episode...")
                    await asyncio.sleep(0.5)
                    
            except Exception as e:
                error_msg = f"Failed to add chunk {chunk.index} to graph: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
                
                # Continue processing other chunks even if one fails
                continue
        
        result = {
            "episodes_created": episodes_created,
            "total_chunks": len(chunks),
            "errors": errors
        }
        
        logger.info(f"Graph building complete: {episodes_created} episodes created, {len(errors)} errors")
        return result
    
    def _prepare_episode_content(
        self,
        chunk: DocumentChunk,
        document_title: str,
        document_metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Prepare episode content with minimal context to avoid token limits.
        
        Args:
            chunk: Document chunk
            document_title: Title of the document
            document_metadata: Additional metadata
        
        Returns:
            Formatted episode content (optimized for Graphiti)
        """
        # Limit chunk content to avoid Graphiti's 8192 token limit
        # Estimate ~4 chars per token, keep content under 6000 chars to leave room for processing
        max_content_length = 6000
        
        content = chunk.content
        if len(content) > max_content_length:
            # Truncate content but try to end at a sentence boundary
            truncated = content[:max_content_length]
            last_sentence_end = max(
                truncated.rfind('. '),
                truncated.rfind('! '),
                truncated.rfind('? ')
            )
            
            if last_sentence_end > max_content_length * 0.7:  # If we can keep 70% and end cleanly
                content = truncated[:last_sentence_end + 1] + " [TRUNCATED]"
            else:
                content = truncated + "... [TRUNCATED]"
            
            logger.warning(f"Truncated chunk {chunk.index} from {len(chunk.content)} to {len(content)} chars for Graphiti")
        
        # Add minimal context (just document title for now)
        if document_title and len(content) < max_content_length - 100:
            episode_content = f"[Doc: {document_title[:50]}]\n\n{content}"
        else:
            episode_content = content
        
        return episode_content
    
    def _estimate_tokens(self, text: str) -> int:
        """Rough estimate of token count (4 chars per token)."""
        return len(text) // 4
    
    def _is_content_too_large(self, content: str, max_tokens: int = 7000) -> bool:
        """Check if content is too large for Graphiti processing."""
        return self._estimate_tokens(content) > max_tokens
    
    async def extract_entities_from_document(
        self,
        chunks: List[DocumentChunk],
        extract_companies: bool = True,
        extract_technologies: bool = True,
        extract_people: bool = True,
        extract_financial_entities: bool = True,
        extract_corporate_roles: bool = True,
        extract_ownership: bool = True,
        extract_transactions: bool = True,
        extract_personal_connections: bool = True
    ) -> List[DocumentChunk]:
        """
        Extract entities from the entire document content (all chunks combined) using LLM.
        This provides better context and more accurate entity extraction across the whole document.

        Args:
            chunks: List of document chunks
            extract_*: Boolean flags for each entity type

        Returns:
            Chunks with shared entity metadata added to all chunks
        """
        if not self._initialized:
            await self.initialize()

        # Combine all chunk content into one document
        full_document_content = "\n\n".join([chunk.content for chunk in chunks])
        document_length = len(full_document_content)

        logger.info(f"Extracting entities from entire document ({len(chunks)} chunks, {document_length} characters total)")

        # Use LLM for all entity extraction (no more manual/rule-based extraction)
        logger.info("Document-level extraction - Using LLM for all entity types")

        # Initialize entity structure
        document_entities = {
            "companies": [],
            "technologies": [],
            "people": [],
            "locations": [],
            "financial_entities": {
                "company_secretaries": [],
                "payees": [],
                "document_issuers": [],
                "target_issuers": [],
                "target_companies": []
            },
            "corporate_roles": {
                "executive_directors": [],
                "non_executive_directors": [],
                "independent_directors": [],
                "chairman": [],
                "deputy_chairman": [],
                "ceo_coo": [],
                "company_secretaries": [],
                "board_committees": [],
                "auditors": [],
                "other_roles": []
            },
            "ownership": {
                "direct_ownership": [],
                "indirect_ownership": [],
                "shareholding_disclosures": []
            },
            "transactions": {
                "mergers": [],
                "joint_ventures": [],
                "spin_offs": [],
                "asset_sales": [],
                "rights_issues": [],
                "general_offers": [],
                "other_transactions": []
            },
            "personal_connections": {
                "marriages": [],
                "career_overlaps": [],
                "alma_mater": [],
                "other_connections": []
            },
            "network_entities": []
        }

        logger.debug(f"Processing entire document with {document_length} characters")

        # Extract entities using a mix of LLM and rule-based methods based on flags
        if any(llm_usage.values()):
            # Some entities need LLM extraction
            try:
                logger.debug(f"Using LLM extraction for document-level types: {llm_types}")

                # Split large documents into 50,000 character chunks for LLM processing
                if document_length > 50000:
                    logger.info(f"Document is large ({document_length} chars). Splitting into chunks of 50,000 chars for LLM processing.")
                    llm_entities = await self._extract_entities_from_large_document(
                        full_document_content,
                        extract_companies=extract_companies and use_llm_for_companies,
                        extract_technologies=extract_technologies and use_llm_for_technologies,
                        extract_people=extract_people and use_llm_for_people,
                        extract_financial_entities=extract_financial_entities and use_llm_for_financial_entities,
                        extract_corporate_roles=extract_corporate_roles and use_llm_for_corporate_roles,
                        extract_ownership=extract_ownership and use_llm_for_ownership,
                        extract_transactions=extract_transactions and use_llm_for_transactions,
                        extract_personal_connections=extract_personal_connections and use_llm_for_personal_connections
                    )
                else:
                    llm_entities = await self._extract_entities_with_llm(
                        full_document_content,
                        extract_companies=extract_companies and use_llm_for_companies,
                        extract_technologies=extract_technologies and use_llm_for_technologies,
                        extract_people=extract_people and use_llm_for_people,
                        extract_financial_entities=extract_financial_entities and use_llm_for_financial_entities,
                        extract_corporate_roles=extract_corporate_roles and use_llm_for_corporate_roles,
                        extract_ownership=extract_ownership and use_llm_for_ownership,
                        extract_transactions=extract_transactions and use_llm_for_transactions,
                        extract_personal_connections=extract_personal_connections and use_llm_for_personal_connections
                    )

                logger.debug(f"LLM extraction completed for entire document")

                # Filter and merge LLM results based on usage flags
                used_entities = {}
                for category, items in llm_entities.items():
                    if category in document_entities and llm_usage.get(category, False):
                        used_entities[category] = items
                        if isinstance(document_entities[category], dict) and isinstance(items, dict):
                            for subcategory, subitems in items.items():
                                if subcategory in document_entities[category]:
                                    document_entities[category][subcategory] = subitems
                        elif isinstance(document_entities[category], list):
                            document_entities[category] = items

                # Log what entities were actually used from LLM
                if used_entities:
                    used_counts = {}
                    for category, items in used_entities.items():
                        if isinstance(items, dict):
                            used_counts[category] = sum(len(subitems) if isinstance(subitems, list) else 1 for subitems in items.values())
                        elif isinstance(items, list):
                            used_counts[category] = len(items)
                        else:
                            used_counts[category] = 1 if items else 0
                    logger.info(f"LLM entities used for document: {used_counts}")
                else:
                    logger.info(f"No LLM entities used for document (all filtered out)")

            except Exception as e:
                logger.warning(f"LLM entity extraction failed for document: {e}. Falling back to rule-based extraction.")
                # Fall back to rule-based extraction for failed LLM types
                llm_usage = {k: False for k in llm_usage.keys()}  # Disable LLM for this document

        # Use rule-based extraction for remaining entity types
        logger.debug(f"Using rule-based extraction for document-level types: {[k for k, v in llm_usage.items() if not v]}")
        document_entities = await self._extract_entities_rule_based(
            full_document_content,
            document_entities,
            extract_companies and not llm_usage.get('companies', False),
            extract_technologies and not llm_usage.get('technologies', False),
            extract_people and not llm_usage.get('people', False),
            extract_financial_entities and not llm_usage.get('financial_entities', False),
            extract_corporate_roles and not llm_usage.get('corporate_roles', False),
            extract_ownership and not llm_usage.get('ownership', False),
            extract_transactions and not llm_usage.get('transactions', False),
            extract_personal_connections and not llm_usage.get('personal_connections', False)
        )

        # Apply the same entities to all chunks
        enriched_chunks = []
        for chunk in chunks:
            # Create enriched chunk with shared document-level entities
            enriched_chunk = DocumentChunk(
                content=chunk.content,
                index=chunk.index,
                start_char=chunk.start_char,
                end_char=chunk.end_char,
                metadata={
                    **chunk.metadata,
                    "entities": document_entities,  # Same entities for all chunks
                    "entity_extraction_date": datetime.now().isoformat(),
                    "entity_extraction_scope": "document_level"  # Indicate this was document-level extraction
                },
                token_count=chunk.token_count
            )

            # Preserve embedding if it exists
            if hasattr(chunk, 'embedding'):
                enriched_chunk.embedding = chunk.embedding

            enriched_chunks.append(enriched_chunk)

        # Log summary
        total_entities = 0
        for category, items in document_entities.items():
            if isinstance(items, dict):
                total_entities += sum(len(subitems) if isinstance(subitems, list) else 1 for subitems in items.values())
            elif isinstance(items, list):
                total_entities += len(items)

        logger.info(f"Document-level entity extraction complete: {total_entities} total entities found")
        logger.info(f"Applied same entities to all {len(enriched_chunks)} chunks")

        return enriched_chunks

    async def extract_entities_from_chunks(
        self,
        chunks: List[DocumentChunk],
        extract_companies: bool = True,
        extract_technologies: bool = True,
        extract_people: bool = True,
        extract_financial_entities: bool = True,
        extract_corporate_roles: bool = True,
        extract_ownership: bool = True,
        extract_transactions: bool = True,
        extract_personal_connections: bool = True,
        use_llm: bool = True,
        use_llm_for_companies: bool = False,
        use_llm_for_technologies: bool = False,
        use_llm_for_people: bool = False,
        use_llm_for_financial_entities: bool = False,
        use_llm_for_corporate_roles: bool = True,  # Default to LLM for corporate roles
        use_llm_for_ownership: bool = False,
        use_llm_for_transactions: bool = False,
        use_llm_for_personal_connections: bool = False
    ) -> List[DocumentChunk]:
        """
        Extract entities from chunks individually (chunk-by-chunk processing).
        Use extract_entities_from_document() for document-level extraction instead.

        Args:
            chunks: List of document chunks
            extract_companies: Whether to extract company names
            extract_technologies: Whether to extract technology terms
            extract_people: Whether to extract person names
            extract_financial_entities: Whether to extract financial entities (payees, issuers, etc.)
            extract_corporate_roles: Whether to extract corporate roles (company secretary, executive director, etc.)
            extract_ownership: Whether to extract ownership information (direct/indirect)
            extract_transactions: Whether to extract transaction information (mergers, JVs, etc.)
            extract_personal_connections: Whether to extract personal connections (marriage, career, alma mater)
            use_llm: Global flag for LLM usage (overridden by specific flags)
            use_llm_for_*: Specific flags to control LLM usage for each entity type

        Returns:
            Chunks with individual entity metadata added (each chunk processed separately)
        """
        if not self._initialized:
            await self.initialize()

        # Determine which entity types will use LLM
        llm_usage = {
            'companies': use_llm_for_companies and use_llm and self._llm_client,
            'technologies': use_llm_for_technologies and use_llm and self._llm_client,
            'people': use_llm_for_people and use_llm and self._llm_client,
            'financial_entities': use_llm_for_financial_entities and use_llm and self._llm_client,
            'corporate_roles': use_llm_for_corporate_roles and use_llm and self._llm_client,
            'ownership': use_llm_for_ownership and use_llm and self._llm_client,
            'transactions': use_llm_for_transactions and use_llm and self._llm_client,
            'personal_connections': use_llm_for_personal_connections and use_llm and self._llm_client
        }

        llm_types = [k for k, v in llm_usage.items() if v]
        rule_types = [k for k, v in llm_usage.items() if not v]

        logger.info(f"Extracting entities from {len(chunks)} chunks")
        logger.info(f"LLM-based extraction for: {llm_types if llm_types else 'None'}")
        logger.info(f"Rule-based extraction for: {rule_types if rule_types else 'None'}")

        enriched_chunks = []

        for chunk in chunks:
            # Initialize entity structure with all new categories
            entities = {
                "companies": [],
                "technologies": [],
                "people": [],
                "locations": [],
                "financial_entities": {
                    "company_secretaries": [],
                    "payees": [],
                    "document_issuers": [],
                    "target_issuers": [],
                    "target_companies": []
                },
                "corporate_roles": {
                    "executive_directors": [],
                    "non_executive_directors": [],
                    "independent_directors": [],
                    "chairman": [],
                    "deputy_chairman": [],
                    "ceo_coo": [],
                    "company_secretaries": [],
                    "board_committees": [],
                    "auditors": [],
                    "other_roles": []
                },
                "ownership": {
                    "direct_ownership": [],
                    "indirect_ownership": [],
                    "shareholding_disclosures": []
                },
                "transactions": {
                    "mergers": [],
                    "joint_ventures": [],
                    "spin_offs": [],
                    "asset_sales": [],
                    "rights_issues": [],
                    "general_offers": [],
                    "other_transactions": []
                },
                "personal_connections": {
                    "marriages": [],
                    "career_overlaps": [],
                    "alma_mater": [],
                    "other_connections": []
                },
                "network_entities": []
            }

            content = chunk.content

            logger.debug(f"Processing chunk {chunk.index} with {len(content)} characters")

            # Extract entities using a mix of LLM and rule-based methods based on flags
            if any(llm_usage.values()):
                # Some entities need LLM extraction
                try:
                    logger.debug(f"Using LLM extraction for chunk {chunk.index} for types: {llm_types}")
                    llm_entities = await self._extract_entities_with_llm(
                        content,
                        extract_companies=extract_companies and use_llm_for_companies,
                        extract_technologies=extract_technologies and use_llm_for_technologies,
                        extract_people=extract_people and use_llm_for_people,
                        extract_financial_entities=extract_financial_entities and use_llm_for_financial_entities,
                        extract_corporate_roles=extract_corporate_roles and use_llm_for_corporate_roles,
                        extract_ownership=extract_ownership and use_llm_for_ownership,
                        extract_transactions=extract_transactions and use_llm_for_transactions,
                        extract_personal_connections=extract_personal_connections and use_llm_for_personal_connections
                    )

                    logger.debug(f"LLM extraction completed for chunk {chunk.index}")

                    # Filter and merge LLM results based on usage flags
                    used_entities = {}
                    for category, items in llm_entities.items():
                        if category in entities and llm_usage.get(category, False):
                            used_entities[category] = items
                            if isinstance(entities[category], dict) and isinstance(items, dict):
                                for subcategory, subitems in items.items():
                                    if subcategory in entities[category]:
                                        entities[category][subcategory] = subitems
                            elif isinstance(entities[category], list):
                                entities[category] = items

                    # Log what entities were actually used from LLM
                    if used_entities:
                        used_counts = {}
                        for category, items in used_entities.items():
                            if isinstance(items, dict):
                                used_counts[category] = sum(len(subitems) if isinstance(subitems, list) else 1 for subitems in items.values())
                            elif isinstance(items, list):
                                used_counts[category] = len(items)
                            else:
                                used_counts[category] = 1 if items else 0
                        logger.info(f"LLM entities used for chunk {chunk.index}: {used_counts}")
                    else:
                        logger.info(f"No LLM entities used for chunk {chunk.index} (all filtered out)")

                except Exception as e:
                    logger.warning(f"LLM entity extraction failed for chunk {chunk.index}: {e}. Falling back to rule-based extraction.")
                    # Fall back to rule-based extraction for failed LLM types
                    llm_usage = {k: False for k in llm_usage.keys()}  # Disable LLM for this chunk

            # Use rule-based extraction for remaining entity types
            logger.debug(f"Using rule-based extraction for chunk {chunk.index} for types: {[k for k, v in llm_usage.items() if not v]}")
            entities = await self._extract_entities_rule_based(
                content,
                entities,
                extract_companies and not llm_usage.get('companies', False),
                extract_technologies and not llm_usage.get('technologies', False),
                extract_people and not llm_usage.get('people', False),
                extract_financial_entities and not llm_usage.get('financial_entities', False),
                extract_corporate_roles and not llm_usage.get('corporate_roles', False),
                extract_ownership and not llm_usage.get('ownership', False),
                extract_transactions and not llm_usage.get('transactions', False),
                extract_personal_connections and not llm_usage.get('personal_connections', False)
            )
            
            # Create enriched chunk
            enriched_chunk = DocumentChunk(
                content=chunk.content,
                index=chunk.index,
                start_char=chunk.start_char,
                end_char=chunk.end_char,
                metadata={
                    **chunk.metadata,
                    "entities": entities,
                    "entity_extraction_date": datetime.now().isoformat()
                },
                token_count=chunk.token_count
            )
            
            # Preserve embedding if it exists
            if hasattr(chunk, 'embedding'):
                enriched_chunk.embedding = chunk.embedding
            
            enriched_chunks.append(enriched_chunk)
        
        logger.info("Entity extraction complete")
        return enriched_chunks

    async def _extract_entities_with_llm(
        self,
        text: str,
        extract_companies: bool = True,
        extract_technologies: bool = True,
        extract_people: bool = True,
        extract_financial_entities: bool = True,
        extract_corporate_roles: bool = True,
        extract_ownership: bool = True,
        extract_transactions: bool = True,
        extract_personal_connections: bool = True
    ) -> Dict[str, Any]:
        """
        Extract entities using LLM with structured prompts.

        Args:
            text: Text content to analyze
            extract_*: Boolean flags for each entity type

        Returns:
            Dictionary of extracted entities
        """
        import time
        start_time = time.time()

        # Log extraction request details
        requested_types = []
        if extract_companies: requested_types.append("companies")
        if extract_technologies: requested_types.append("technologies")
        if extract_people: requested_types.append("people")
        if extract_financial_entities: requested_types.append("financial_entities")
        if extract_corporate_roles: requested_types.append("corporate_roles")
        if extract_ownership: requested_types.append("ownership")
        if extract_transactions: requested_types.append("transactions")
        if extract_personal_connections: requested_types.append("personal_connections")

        logger.info(f"Starting LLM entity extraction for types: {requested_types}")
        logger.debug(f"Text content length: {len(text)} characters")

        # Create the extraction prompt
        prompt = self._create_entity_extraction_prompt(
            text,
            extract_companies=extract_companies,
            extract_technologies=extract_technologies,
            extract_people=extract_people,
            extract_financial_entities=extract_financial_entities,
            extract_corporate_roles=extract_corporate_roles,
            extract_ownership=extract_ownership,
            extract_transactions=extract_transactions,
            extract_personal_connections=extract_personal_connections
        )

        try:
            logger.debug(f"Calling LLM for entity extraction with model: {self._llm_client.config.model}")
            logger.debug(f"Prompt length: {len(prompt)} characters")
            logger.debug(f"LLM prompt preview (first 500 chars): {prompt[:500]}...")

            # Call LLM for entity extraction using the OpenAI client interface
            # The graphiti OpenAIClient wraps the standard OpenAI client
            response = await self._llm_client.client.chat.completions.create(
                model=self._llm_client.config.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,  # Low temperature for consistent extraction
                max_tokens=2000
            )

            # Extract content from response
            content = response.choices[0].message.content

            # Enhanced LLM response logging
            logger.info(f"LLM Response received (length: {len(content)} characters)")
            logger.info(f"LLM extraction took {time.time() - start_time:.2f} seconds")
            logger.debug(f"Full LLM response: {content}")

            # Parse the JSON response
            entities_json = content.strip()
            if entities_json.startswith("```json"):
                entities_json = entities_json[7:]
            if entities_json.endswith("```"):
                entities_json = entities_json[:-3]

            entities = json.loads(entities_json)

            # Enhanced entity validation and classification logging
            validated_entities = self._validate_and_classify_entities(entities)

            # Log extracted entities summary with detailed breakdown
            entity_counts = {}
            person_entities = []
            organization_entities = []

            for category, items in validated_entities.items():
                if isinstance(items, dict):
                    entity_counts[category] = sum(len(subitems) if isinstance(subitems, list) else 1 for subitems in items.values())
                elif isinstance(items, list):
                    entity_counts[category] = len(items)

                    # Classify entities as person vs organization
                    if category in ["people", "corporate_roles"]:
                        person_entities.extend(items if isinstance(items, list) else [])
                    elif category in ["companies", "financial_entities"]:
                        organization_entities.extend(items if isinstance(items, list) else [])
                else:
                    entity_counts[category] = 1 if items else 0

            logger.info(f"LLM extracted entities summary: {entity_counts}")
            logger.info(f"Person entities extracted: {len(person_entities)} ({person_entities[:5]}{'...' if len(person_entities) > 5 else ''})")
            logger.info(f"Organization entities extracted: {len(organization_entities)} ({organization_entities[:5]}{'...' if len(organization_entities) > 5 else ''})")
            logger.debug(f"LLM extracted entities details: {validated_entities}")

            return validated_entities

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            logger.error(f"LLM response was: {content}")
            logger.error(f"Attempted to parse: {entities_json}")
            return {}
        except Exception as e:
            logger.error(f"LLM entity extraction failed: {e}")
            logger.error(f"Extraction took {time.time() - start_time:.2f} seconds before failure")
            return {}

    def _validate_and_classify_entities(self, entities: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and classify extracted entities to distinguish between persons and organizations.

        Args:
            entities: Raw entities extracted from LLM

        Returns:
            Validated and classified entities
        """
        logger.debug("Starting entity validation and classification")

        validated_entities = {}

        # Person indicators (titles, prefixes, suffixes that indicate individuals)
        person_indicators = {
            'titles': ['mr', 'mrs', 'ms', 'dr', 'prof', 'sir', 'dame', 'lord', 'lady'],
            'suffixes': ['jr', 'sr', 'ii', 'iii', 'iv', 'phd', 'md', 'esq'],
            'roles': ['ceo', 'cfo', 'cto', 'chairman', 'director', 'president', 'manager', 'officer']
        }

        # Organization indicators (suffixes, types that indicate companies/organizations)
        org_indicators = {
            'suffixes': ['inc', 'corp', 'corporation', 'ltd', 'limited', 'llc', 'ag', 'se', 'sa', 'plc', 'gmbh'],
            'types': ['company', 'corporation', 'group', 'holdings', 'enterprises', 'industries', 'systems', 'technologies'],
            'prefixes': ['the', 'bank of', 'university of', 'institute of']
        }

        for category, items in entities.items():
            if isinstance(items, list):
                validated_items = []
                person_count = 0
                org_count = 0

                for item in items:
                    if not item or not isinstance(item, str):
                        continue

                    item_clean = item.strip()
                    if not item_clean:
                        continue

                    # Classify as person or organization
                    is_person = self._is_person_entity(item_clean, person_indicators)
                    is_organization = self._is_organization_entity(item_clean, org_indicators)

                    if category in ["people", "corporate_roles"] and is_person:
                        person_count += 1
                        logger.debug(f"Classified as PERSON: {item_clean}")
                    elif category in ["companies", "financial_entities"] and is_organization:
                        org_count += 1
                        logger.debug(f"Classified as ORGANIZATION: {item_clean}")
                    elif category in ["people", "corporate_roles"] and not is_organization:
                        # Default to person for people/roles categories unless clearly an organization
                        person_count += 1
                        logger.debug(f"Default classified as PERSON: {item_clean}")
                    elif category in ["companies", "financial_entities"] and not is_person:
                        # Default to organization for company categories unless clearly a person
                        org_count += 1
                        logger.debug(f"Default classified as ORGANIZATION: {item_clean}")
                    else:
                        logger.debug(f"Ambiguous classification for {category}: {item_clean}")

                    validated_items.append(item_clean)

                validated_entities[category] = validated_items
                logger.debug(f"Category {category}: {len(validated_items)} items ({person_count} persons, {org_count} organizations)")

            elif isinstance(items, dict):
                validated_entities[category] = {}
                for subcategory, subitems in items.items():
                    if isinstance(subitems, list):
                        validated_subitems = [item.strip() for item in subitems if item and isinstance(item, str) and item.strip()]
                        validated_entities[category][subcategory] = validated_subitems
                        logger.debug(f"Category {category}.{subcategory}: {len(validated_subitems)} items")
                    else:
                        validated_entities[category][subcategory] = subitems
            else:
                validated_entities[category] = items

        logger.debug("Entity validation and classification completed")
        return validated_entities

    def _is_person_entity(self, entity: str, person_indicators: Dict[str, List[str]]) -> bool:
        """Check if an entity is likely a person based on indicators."""
        entity_lower = entity.lower()

        # Check for person titles/prefixes
        for title in person_indicators['titles']:
            if entity_lower.startswith(title + ' ') or entity_lower.startswith(title + '.'):
                return True

        # Check for person suffixes
        for suffix in person_indicators['suffixes']:
            if entity_lower.endswith(' ' + suffix) or entity_lower.endswith(',' + suffix):
                return True

        # Check for role indicators in the name
        for role in person_indicators['roles']:
            if role in entity_lower:
                return True

        # Check for typical person name patterns (First Last, Last First, etc.)
        words = entity.split()
        if len(words) >= 2:
            # Check if it looks like a person name (capitalized words, reasonable length)
            if all(word[0].isupper() for word in words if word) and len(words) <= 4:
                return True

        return False

    def _is_organization_entity(self, entity: str, org_indicators: Dict[str, List[str]]) -> bool:
        """Check if an entity is likely an organization based on indicators."""
        entity_lower = entity.lower()

        # Check for organization suffixes
        for suffix in org_indicators['suffixes']:
            if entity_lower.endswith(' ' + suffix) or entity_lower.endswith(',' + suffix):
                return True

        # Check for organization types
        for org_type in org_indicators['types']:
            if org_type in entity_lower:
                return True

        # Check for organization prefixes
        for prefix in org_indicators['prefixes']:
            if entity_lower.startswith(prefix + ' '):
                return True

        return False

    async def _extract_entities_from_large_document(
        self,
        full_document_content: str,
        extract_companies: bool = True,
        extract_technologies: bool = True,
        extract_people: bool = True,
        extract_financial_entities: bool = True,
        extract_corporate_roles: bool = True,
        extract_ownership: bool = True,
        extract_transactions: bool = True,
        extract_personal_connections: bool = True
    ) -> Dict[str, Any]:
        """
        Extract entities from large documents by splitting into 50,000 character chunks
        and combining the results.

        Args:
            full_document_content: Complete document text
            extract_*: Boolean flags for each entity type

        Returns:
            Combined entities from all chunks
        """
        chunk_size = 50000
        document_length = len(full_document_content)

        # Split document into chunks of 50,000 characters
        # Try to split at sentence boundaries when possible
        text_chunks = []
        start = 0

        while start < document_length:
            end = min(start + chunk_size, document_length)

            # If not at the end of document, try to find a good break point
            if end < document_length:
                # Look for sentence endings within the last 1000 characters
                search_start = max(start, end - 1000)
                sentence_endings = []

                for i in range(search_start, end):
                    if full_document_content[i] in '.!?\n':
                        sentence_endings.append(i)

                # Use the last sentence ending if found
                if sentence_endings:
                    end = sentence_endings[-1] + 1

            chunk_text = full_document_content[start:end].strip()
            if chunk_text:
                text_chunks.append(chunk_text)

            start = end

        logger.info(f"Split large document ({document_length} chars) into {len(text_chunks)} chunks for LLM processing")

        # Initialize combined entities structure
        combined_entities = {
            "companies": [],
            "technologies": [],
            "people": [],
            "locations": [],
            "financial_entities": {
                "company_secretaries": [],
                "payees": [],
                "document_issuers": [],
                "target_issuers": [],
                "target_companies": []
            },
            "corporate_roles": {
                "executive_directors": [],
                "non_executive_directors": [],
                "independent_directors": [],
                "chairman": [],
                "deputy_chairman": [],
                "ceo_coo": [],
                "company_secretaries": [],
                "board_committees": [],
                "auditors": [],
                "other_roles": []
            },
            "ownership": {
                "direct_ownership": [],
                "indirect_ownership": [],
                "shareholding_disclosures": []
            },
            "transactions": {
                "mergers": [],
                "joint_ventures": [],
                "spin_offs": [],
                "asset_sales": [],
                "rights_issues": [],
                "general_offers": [],
                "other_transactions": []
            },
            "personal_connections": {
                "marriages": [],
                "career_overlaps": [],
                "alma_mater": [],
                "other_connections": []
            },
            "network_entities": []
        }

        # Process each chunk with LLM
        for i, chunk_text in enumerate(text_chunks):
            try:
                logger.debug(f"Processing large document chunk {i+1}/{len(text_chunks)} ({len(chunk_text)} chars)")

                chunk_entities = await self._extract_entities_with_llm(
                    chunk_text,
                    extract_companies=extract_companies,
                    extract_technologies=extract_technologies,
                    extract_people=extract_people,
                    extract_financial_entities=extract_financial_entities,
                    extract_corporate_roles=extract_corporate_roles,
                    extract_ownership=extract_ownership,
                    extract_transactions=extract_transactions,
                    extract_personal_connections=extract_personal_connections
                )

                # Merge entities from this chunk
                self._merge_entities(combined_entities, chunk_entities)

                logger.debug(f"Completed processing chunk {i+1}/{len(text_chunks)}")

            except Exception as e:
                logger.warning(f"Failed to process chunk {i+1}/{len(text_chunks)}: {e}")
                continue

        # Deduplicate entities
        self._deduplicate_entities(combined_entities)

        # Log final counts
        total_entities = 0
        for category, items in combined_entities.items():
            if isinstance(items, dict):
                total_entities += sum(len(subitems) if isinstance(subitems, list) else 1 for subitems in items.values())
            elif isinstance(items, list):
                total_entities += len(items)

        logger.info(f"Large document processing complete: {total_entities} total entities extracted from {len(text_chunks)} chunks")

        return combined_entities

    def _merge_entities(self, combined_entities: Dict[str, Any], chunk_entities: Dict[str, Any]) -> None:
        """
        Merge entities from a chunk into the combined entities structure.

        Args:
            combined_entities: The main entities structure to merge into
            chunk_entities: Entities from a single chunk to merge
        """
        for category, items in chunk_entities.items():
            if category not in combined_entities:
                continue

            if isinstance(combined_entities[category], dict) and isinstance(items, dict):
                # Handle nested dictionaries (like financial_entities, corporate_roles, etc.)
                for subcategory, subitems in items.items():
                    if subcategory in combined_entities[category]:
                        if isinstance(subitems, list):
                            combined_entities[category][subcategory].extend(subitems)
                        else:
                            combined_entities[category][subcategory].append(subitems)
            elif isinstance(combined_entities[category], list) and isinstance(items, list):
                # Handle simple lists (like companies, technologies, etc.)
                combined_entities[category].extend(items)

    def _deduplicate_entities(self, entities: Dict[str, Any]) -> None:
        """
        Remove duplicate entities from the combined entities structure.

        Args:
            entities: The entities structure to deduplicate
        """
        for category, items in entities.items():
            if isinstance(items, dict):
                # Handle nested dictionaries
                for subcategory, subitems in items.items():
                    if isinstance(subitems, list):
                        # Remove duplicates while preserving order
                        seen = set()
                        deduplicated = []
                        for item in subitems:
                            # Normalize for comparison (strip whitespace, lowercase)
                            normalized = item.strip().lower() if isinstance(item, str) else str(item).strip().lower()
                            if normalized not in seen:
                                seen.add(normalized)
                                deduplicated.append(item)
                        entities[category][subcategory] = deduplicated
            elif isinstance(items, list):
                # Handle simple lists
                seen = set()
                deduplicated = []
                for item in items:
                    # Normalize for comparison (strip whitespace, lowercase)
                    normalized = item.strip().lower() if isinstance(item, str) else str(item).strip().lower()
                    if normalized not in seen:
                        seen.add(normalized)
                        deduplicated.append(item)
                entities[category] = deduplicated

    def _create_entity_extraction_prompt(
        self,
        text: str,
        extract_companies: bool = True,
        extract_technologies: bool = True,
        extract_people: bool = True,
        extract_financial_entities: bool = True,
        extract_corporate_roles: bool = True,
        extract_ownership: bool = True,
        extract_transactions: bool = True,
        extract_personal_connections: bool = True
    ) -> str:
        """
        Create a structured prompt for LLM entity extraction.

        Args:
            text: Text to analyze
            extract_*: Boolean flags for each entity type

        Returns:
            Formatted prompt string
        """
        prompt = f"""You are an expert entity extraction system. Analyze the following text and extract relevant entities in the specified categories. Return your response as a valid JSON object.

TEXT TO ANALYZE:
{text}

EXTRACTION INSTRUCTIONS:
Extract entities in the following categories. If no entities are found in a category, return an empty list or object as appropriate.

"""

        # Add category-specific instructions based on flags
        # Only include categories that are actually requested for LLM extraction
        requested_categories = []

        if extract_companies:
            prompt += """
COMPANIES: Extract company names, organizations, and corporate entities.
- Include: corporations, businesses, firms, organizations, institutions
- Format: Full official company names (e.g., "Apple Inc.", "Microsoft Corporation")
- Exclude: Individual person names, even if they hold corporate positions
- Look for: suffixes like Inc, Corp, Ltd, LLC, AG, SE, SA, PLC, GmbH
"""
            requested_categories.append("companies")

        if extract_technologies:
            prompt += """
TECHNOLOGIES: Extract technology terms, software, platforms, and technical concepts.
- Include: software, hardware, platforms, technical methodologies, systems
- Format: Specific technology names and technical terms
"""
            requested_categories.append("technologies")

        if extract_people:
            prompt += """
PEOPLE: Extract individual person names only - NOT company names or organizations.
- Include: Individual human beings, executives, employees, board members
- Format: Full person names (e.g., "John Smith", "Mary Johnson", "Dr. Sarah Wilson")
- Look for: titles like Mr., Mrs., Dr., Prof., or role-based context
- Exclude: Company names, organization names, group entities
- Separate person names from their titles/qualifications (extract "John Smith" not "John Smith, CEO")
"""
            requested_categories.append("people")

        if extract_financial_entities:
            prompt += """
FINANCIAL_ENTITIES:
- company_secretaries: Individuals or entities serving as company secretaries
- payees: Recipients of payments, beneficiaries
- document_issuers: Entities that issued documents, certificates, or statements
- target_issuers: Companies or entities that are targets of transactions or disclosures
- target_companies: Companies that are acquisition targets or subjects of corporate actions
"""
            requested_categories.append("financial_entities")

        if extract_corporate_roles:
            prompt += """
CORPORATE_ROLES:
Extract comprehensive director and management information from biographical profiles with detailed formatting:

FORMAT REQUIREMENTS:
- Separate person names from their qualifications/credentials
- Bold the surname (family name) in the person's name
- Extract age, tenure, and career history
- Capture all committee memberships and roles
- Include board positions at other companies
- Extract educational qualifications and professional memberships
- Identify alternate director relationships
- Capture appointment and re-designation dates

BIOGRAPHICAL EXTRACTION EXAMPLES:
- "**FOK** Kin Ning, Canning - BA, DFM, FCA (ANZ) | Chairman and Non-executive Director (since March 2009, aged 73)"
- "**LUI** Dennis Pok Man - BSc | Executive Deputy Chairman (re-designated 11 December 2024, aged 74)"
- "**CHAN** Tze Leung - BSc(Econ), MBA, FHKIOD | Independent Non-executive Director (since 9 May 2024, aged 78)"
- "**IM** Man Ieng - BCom, MBus(Acc), CPA | Independent Non-executive Director and Audit Committee member"

CATEGORIES TO EXTRACT:
- executive_directors: Executive directors with full biographical details including age, tenure, qualifications, and career history
- non_executive_directors: Non-executive directors with complete profiles including other board positions
- independent_directors: Independent non-executive directors with professional background and committee roles
- chairman: Chairman with executive/non-executive status, age, and appointment history
- deputy_chairman: Deputy chairmen with re-designation dates and previous roles
- ceo_coo: Chief executives and operating officers with career progression and experience
- company_secretaries: Company secretaries with legal qualifications and tenure
- board_committees: Extract all committee structures with member names and roles:
  * Audit Committee: Chairman and members
  * Remuneration Committee: Chairman and members
  * Nomination Committee: Chairman and members
  * Sustainability Committee: Chairman and members
- auditors: External auditors with full firm names and certifications
- other_roles: Management team, alternates, and special positions including:
  * Chief Financial Officer with qualifications
  * Chief Technology Officer with experience
  * Alternate directors with relationships

COMMITTEE EXTRACTION PATTERNS:
- "Audit Committee: **CHAN** Tze Leung (Chairman), **IM** Man Ieng (member)"
- "Remuneration Committee: **IP** Yuk Keung (Chairman since 9 May 2024)"
- "Nomination Committee: **CHAN** Tze Leung (Chairman), **IP** Yuk Keung (member)"
- "Sustainability Committee: **SHIH** Edith (Chairman since July 2020)"

QUALIFICATION PATTERNS TO RECOGNIZE:
Academic: BSc, MSc, PhD, BA, MA, MBA, BCom, BEng, LLB, LLM, EdM, BSE, MBus, Bachelor of Science, Master of Arts, Master of Business Administration
Professional: FCA, CPA, FCPA, HKICPA, ACCA, ACA, CFA, FRM, CAIA, CQF, PRM, FHKIOD, FCG, HKFCG, Fellow of the Chartered Accountants, Chartered Engineer
Legal: Solicitor, Barrister, QC, SC, qualified in England and Wales, Hong Kong, Victoria Australia
Honours: JP, SBS, MBE, OBE, CBE, GBS, GBM, MH, BBS
Memberships: Fellow of Hong Kong Institute of Directors, Member of Hong Kong Institute of Certified Public Accountants

BIOGRAPHICAL DETAILS TO CAPTURE:
- Age and tenure information
- Previous positions and career history
- Educational background with institutions
- Professional qualifications and memberships
- Committee appointment dates and role changes
- Other board positions and directorships
- Alternate director relationships
- Re-designation dates and effective periods

IMPORTANT:
1. Always bold the surname (family name) using **surname** format
2. Include age and tenure: "(aged 73, since March 2009)"
3. Separate qualifications from names using " - "
4. Use " | " to separate qualifications from current role
5. Extract complete committee structures with chairmanship details
6. Capture all appointment and re-designation dates
7. Include professional experience and background
8. Handle complex biographical narratives and extract key facts
"""
            requested_categories.append("corporate_roles")

        if extract_ownership:
            prompt += """
OWNERSHIP:
- direct_ownership: Direct ownership stakes, shareholdings, or equity positions
- indirect_ownership: Indirect ownership through subsidiaries, holding companies, or complex structures
- shareholding_disclosures: Formal disclosures of shareholding positions or changes
"""
            requested_categories.append("ownership")

        if extract_transactions:
            prompt += """
TRANSACTIONS:
- mergers: Merger transactions and consolidations
- joint_ventures: Joint venture formations and partnerships
- spin_offs: Corporate spin-offs and demergers
- asset_sales: Asset sales and disposals
- rights_issues: Rights offerings and equity raises
- general_offers: General offers and takeover bids
- other_transactions: Other corporate transactions not covered above
"""
            requested_categories.append("transactions")

        if extract_personal_connections:
            prompt += """
PERSONAL_CONNECTIONS:
- marriages: Marriage relationships between individuals
- career_overlaps: Professional relationships, shared employment history
- alma_mater: Educational connections, shared schools or universities
- other_connections: Other personal or professional connections
"""
            requested_categories.append("personal_connections")

        # Always include network entities and locations as they are basic
        prompt += """
LOCATIONS: Extract location names, cities, countries, and geographical references.
NETWORK_ENTITIES: Any other entities that appear to be part of a broader network or ecosystem related to the main entities.

RESPONSE FORMAT:
Return a valid JSON object with ONLY the categories that were requested above. """

        # Build the JSON structure dynamically based on requested categories
        json_structure = "{\n"

        if "companies" in requested_categories:
            json_structure += '    "companies": ["company1", "company2"],\n'
        if "technologies" in requested_categories:
            json_structure += '    "technologies": ["tech1", "tech2"],\n'
        if "people" in requested_categories:
            json_structure += '    "people": ["person1", "person2"],\n'

        # Always include locations
        json_structure += '    "locations": ["location1", "location2"],\n'

        if "financial_entities" in requested_categories:
            json_structure += '''    "financial_entities": {
        "company_secretaries": ["secretary1"],
        "payees": ["payee1"],
        "document_issuers": ["issuer1"],
        "target_issuers": ["target1"],
        "target_companies": ["target_company1"]
    },\n'''

        if "corporate_roles" in requested_categories:
            json_structure += '''    "corporate_roles": {
        "executive_directors": ["**LUI** Dennis Pok Man - BSc | Executive Deputy Chairman (aged 74, re-designated 11 December 2024)"],
        "non_executive_directors": ["**WOO** Chiu Man, Cliff - BSc, Diploma in Management | Non-executive Deputy Chairman (aged 71)"],
        "independent_directors": ["**CHAN** Tze Leung - BSc(Econ), MBA, FHKIOD | Independent Non-executive Director (aged 78, since 9 May 2024)"],
        "chairman": ["**FOK** Kin Ning, Canning - BA, DFM, FCA (ANZ) | Chairman and Non-executive Director (aged 73, since March 2009)"],
        "deputy_chairman": ["**LUI** Dennis Pok Man - BSc | Executive Deputy Chairman (re-designated 11 December 2024)"],
        "ceo_coo": ["**KOO** Sing Fai - BSc Computer Science | Chief Executive Officer (aged 52, since August 2018)"],
        "company_secretaries": ["**SHIH** Edith - BSc, MA, MA, EdM, Solicitor, FCG, HKFCG | Former Company Secretary (November 2007 to May 2023)"],
        "board_committees": [
            "Audit Committee: **CHAN** Tze Leung (Chairman), **IM** Man Ieng (member)",
            "Remuneration Committee: **IP** Yuk Keung (Chairman since 9 May 2024)",
            "Nomination Committee: **CHAN** Tze Leung (Chairman), **IP** Yuk Keung (member)",
            "Sustainability Committee: **SHIH** Edith (Chairman since July 2020)"
        ],
        "auditors": ["PricewaterhouseCoopers - Certified Public Accountants, Registered Public Interest Entity Auditor"],
        "other_roles": [
            "**NG** Marcus Byron - BSc Accounting, CPA | Chief Financial Officer (aged 41, since April 2023)",
            "**LEONG** Bing Yow - BEng | Chief Technology Officer (aged 41, since January 2023)",
            "**LAI** Kai Ming, Dominic - BSc(Hons), MBA | Alternate to **FOK** Kin Ning, Canning and **SHIH** Edith"
        ]
    },\n'''

        if "ownership" in requested_categories:
            json_structure += '''    "ownership": {
        "direct_ownership": ["ownership1"],
        "indirect_ownership": ["indirect1"],
        "shareholding_disclosures": ["disclosure1"]
    },\n'''

        if "transactions" in requested_categories:
            json_structure += '''    "transactions": {
        "mergers": ["merger1"],
        "joint_ventures": ["jv1"],
        "spin_offs": ["spinoff1"],
        "asset_sales": ["sale1"],
        "rights_issues": ["rights1"],
        "general_offers": ["offer1"],
        "other_transactions": ["transaction1"]
    },\n'''

        if "personal_connections" in requested_categories:
            json_structure += '''    "personal_connections": {
        "marriages": ["marriage1"],
        "career_overlaps": ["overlap1"],
        "alma_mater": ["school1"],
        "other_connections": ["connection1"]
    },\n'''

        # Always include network entities
        json_structure += '    "network_entities": ["entity1", "entity2"]\n'
        json_structure += "}"

        prompt += f"""
Example structure (only include requested categories):
{json_structure}

IMPORTANT:
- Only extract entities that are explicitly mentioned in the text
- Only include the categories that were specifically requested above
- Be precise and avoid speculation
- Use the exact names/terms as they appear in the text
- If uncertain about categorization, include in the most appropriate category
- Return valid JSON only, no additional text or explanation
- If no entities found for a category, return empty arrays or objects
"""

        return prompt

    async def _extract_entities_rule_based(
        self,
        content: str,
        entities: Dict[str, Any],
        extract_companies: bool,
        extract_technologies: bool,
        extract_people: bool ,
        extract_financial_entities: bool = True,
        extract_corporate_roles: bool = True,
        extract_ownership: bool = True,
        extract_transactions: bool = True,
        extract_personal_connections: bool = True
    ) -> Dict[str, Any]:
        """
        Extract entities using rule-based methods as fallback.

        Args:
            content: Text content to analyze
            entities: Entity structure to populate
            extract_*: Boolean flags for extraction

        Returns:
            Updated entities dictionary
        """
        import time
        start_time = time.time()

        # Log rule-based extraction request
        requested_types = []
        if extract_companies: requested_types.append("companies")
        if extract_technologies: requested_types.append("technologies")
        if extract_people: requested_types.append("people")
        if extract_financial_entities: requested_types.append("financial_entities")
        if extract_corporate_roles: requested_types.append("corporate_roles")
        if extract_ownership: requested_types.append("ownership")
        if extract_transactions: requested_types.append("transactions")
        if extract_personal_connections: requested_types.append("personal_connections")

        logger.info(f"Starting rule-based entity extraction for types: {requested_types}")
        logger.debug(f"Rule-based extraction starting for content length: {len(content)}")

        # Extract basic entities using existing rule-based methods with enhanced logging
        if extract_companies:
            companies_start = time.time()
            entities["companies"] = self._extract_companies(content)
            companies_time = time.time() - companies_start

            # Validate companies are organizations, not people
            validated_companies = self._filter_organizations_from_people(entities["companies"])
            entities["companies"] = validated_companies

            logger.info(f"Rule-based companies extracted: {len(entities['companies'])} in {companies_time:.3f}s")
            logger.debug(f"Companies found: {entities['companies'][:5]}{'...' if len(entities['companies']) > 5 else ''}")

        if extract_technologies:
            tech_start = time.time()
            entities["technologies"] = self._extract_technologies(content)
            tech_time = time.time() - tech_start
            logger.info(f"Rule-based technologies extracted: {len(entities['technologies'])} in {tech_time:.3f}s")
            logger.debug(f"Technologies found: {entities['technologies'][:5]}{'...' if len(entities['technologies']) > 5 else ''}")

        if extract_people:
            people_start = time.time()
            entities["people"] = self._extract_people(content)
            people_time = time.time() - people_start

            # Validate people are individuals, not organizations
            validated_people = self._filter_people_from_organizations(entities["people"])
            entities["people"] = validated_people

            logger.info(f"Rule-based people extracted: {len(entities['people'])} in {people_time:.3f}s")
            logger.debug(f"People found: {entities['people'][:5]}{'...' if len(entities['people']) > 5 else ''}")

        # Extract locations
        locations_start = time.time()
        entities["locations"] = self._extract_locations(content)
        locations_time = time.time() - locations_start
        logger.info(f"Rule-based locations extracted: {len(entities['locations'])} in {locations_time:.3f}s")
        logger.debug(f"Locations found: {entities['locations'][:5]}{'...' if len(entities['locations']) > 5 else ''}")

        # For new entity types, use basic pattern matching as fallback
        if extract_financial_entities:
            entities["financial_entities"] = self._extract_financial_entities_rule_based(content)
            logger.debug(f"Rule-based financial entities extracted")

        if extract_corporate_roles:
            entities["corporate_roles"] = self._extract_corporate_roles_rule_based(content)
            logger.debug(f"Rule-based corporate roles extracted")

        if extract_ownership:
            entities["ownership"] = self._extract_ownership_rule_based(content)
            logger.debug(f"Rule-based ownership extracted")

        if extract_transactions:
            entities["transactions"] = self._extract_transactions_rule_based(content)
            logger.debug(f"Rule-based transactions extracted")

        if extract_personal_connections:
            entities["personal_connections"] = self._extract_personal_connections_rule_based(content)
            logger.debug(f"Rule-based personal connections extracted")

        entities["network_entities"] = self._extract_network_entities_rule_based(content)
        logger.debug(f"Rule-based network entities extracted: {len(entities['network_entities'])}")

        # Log total rule-based extraction time
        total_time = time.time() - start_time
        logger.info(f"Rule-based entity extraction completed in {total_time:.3f}s")

        return entities

    def _filter_organizations_from_people(self, entities: List[str]) -> List[str]:
        """Filter out person names from organization entities."""
        filtered = []
        person_indicators = ['mr', 'mrs', 'ms', 'dr', 'prof', 'sir', 'dame']

        for entity in entities:
            entity_lower = entity.lower()
            is_person = False

            # Check for person titles
            for indicator in person_indicators:
                if entity_lower.startswith(indicator + ' ') or entity_lower.startswith(indicator + '.'):
                    is_person = True
                    logger.debug(f"Filtered out person from companies: {entity}")
                    break

            # Check for typical person name patterns (avoid false positives)
            words = entity.split()
            if len(words) == 2 and all(word[0].isupper() and word[1:].islower() for word in words):
                # Could be a person name, but keep if it has clear org indicators
                org_suffixes = ['inc', 'corp', 'ltd', 'llc', 'ag', 'se', 'sa', 'plc']
                has_org_suffix = any(entity_lower.endswith(' ' + suffix) for suffix in org_suffixes)
                if not has_org_suffix:
                    is_person = True
                    logger.debug(f"Filtered out potential person name from companies: {entity}")

            if not is_person:
                filtered.append(entity)

        return filtered

    def _filter_people_from_organizations(self, entities: List[str]) -> List[str]:
        """Filter out organization names from people entities."""
        filtered = []
        org_indicators = ['inc', 'corp', 'corporation', 'ltd', 'limited', 'llc', 'ag', 'se', 'sa', 'plc', 'gmbh']
        org_types = ['company', 'corporation', 'group', 'holdings', 'enterprises', 'industries']

        for entity in entities:
            entity_lower = entity.lower()
            is_organization = False

            # Check for organization suffixes
            for indicator in org_indicators:
                if entity_lower.endswith(' ' + indicator) or entity_lower.endswith(',' + indicator):
                    is_organization = True
                    logger.debug(f"Filtered out organization from people: {entity}")
                    break

            # Check for organization types
            if not is_organization:
                for org_type in org_types:
                    if org_type in entity_lower:
                        is_organization = True
                        logger.debug(f"Filtered out organization type from people: {entity}")
                        break

            if not is_organization:
                filtered.append(entity)

        return filtered

    def _extract_financial_entities_rule_based(self, text: str) -> Dict[str, List[str]]:
        """Extract financial entities using rule-based patterns."""
        financial_entities = {
            "company_secretaries": [],
            "payees": [],
            "document_issuers": [],
            "target_issuers": [],
            "target_companies": []
        }

        # Company Secretary patterns
        secretary_patterns = [
            r'(?:company secretary|corporate secretary)\s*:?\s*([A-Z][A-Za-z\s&.,]+)',
            r'([A-Z][A-Za-z\s&.,]+)\s+(?:as|is|was|acting as)?\s*(?:company|corporate)\s+secretary',
            r'secretary\s*:?\s*([A-Z][A-Za-z\s&.,]+)'
        ]

        # Payee patterns
        payee_patterns = [
            r'(?:payee|paid to|payment to|beneficiary)\s*:?\s*([A-Z][A-Za-z\s&.,]+(?:Ltd|Inc|Corp|Corporation|Limited|AG|SE|Pte|Pty|LLC|LLP)?)',
            r'(?:remit to|transfer to|wire to)\s*:?\s*([A-Z][A-Za-z\s&.,]+(?:Ltd|Inc|Corp|Corporation|Limited|AG|SE|Pte|Pty|LLC|LLP)?)',
            r'(?:in favor of|in favour of)\s*:?\s*([A-Z][A-Za-z\s&.,]+(?:Ltd|Inc|Corp|Corporation|Limited|AG|SE|Pte|Pty|LLC|LLP)?)'
        ]

        # Document Issuer patterns
        issuer_patterns = [
            r'(?:issued by|issuer|issued from)\s*:?\s*([A-Z][A-Za-z\s&.,]+(?:Ltd|Inc|Corp|Corporation|Limited|AG|SE|Pte|Pty|LLC|LLP)?)',
            r'([A-Z][A-Za-z\s&.,]+(?:Ltd|Inc|Corp|Corporation|Limited|AG|SE|Pte|Pty|LLC|LLP)?)\s+(?:issued|has issued|hereby issues)'
        ]

        # Target patterns
        target_patterns = [
            r'(?:target|target company|target issuer)\s*:?\s*([A-Z][A-Za-z\s&.,]+(?:Ltd|Inc|Corp|Corporation|Limited|AG|SE|Pte|Pty|LLC|LLP)?)',
            r'(?:acquisition of|acquiring|takeover of)\s*([A-Z][A-Za-z\s&.,]+(?:Ltd|Inc|Corp|Corporation|Limited|AG|SE|Pte|Pty|LLC|LLP)?)'
        ]

        # Extract entities using patterns
        for pattern in secretary_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            financial_entities["company_secretaries"].extend([match.strip() for match in matches if match.strip()])

        for pattern in payee_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            financial_entities["payees"].extend([match.strip() for match in matches if match.strip()])

        for pattern in issuer_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            financial_entities["document_issuers"].extend([match.strip() for match in matches if match.strip()])

        for pattern in target_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            financial_entities["target_issuers"].extend([match.strip() for match in matches if match.strip()])
            financial_entities["target_companies"].extend([match.strip() for match in matches if match.strip()])

        # Remove duplicates
        for key in financial_entities:
            financial_entities[key] = list(set(financial_entities[key]))

        return financial_entities

    def _extract_corporate_roles_rule_based(self, text: str) -> Dict[str, List[str]]:
        """Extract corporate roles using rule-based patterns."""
        corporate_roles = {
            "executive_directors": [],
            "non_executive_directors": [],
            "independent_directors": [],
            "chairman": [],
            "deputy_chairman": [],
            "ceo_coo": [],
            "company_secretaries": [],
            "board_committees": [],
            "auditors": [],
            "other_roles": []
        }

        # Enhanced patterns for biographical and management extraction

        # Biographical header patterns (extract from detailed profiles)
        biographical_patterns = [
            r'# ([A-Z][A-Za-z\s,.\(\)]+)\s*\n\s*([A-Za-z\s]+(?:Director|Chairman|Officer))\s*\n\s*([A-Za-z\s,.\(\)]+),\s*aged\s+(\d+),\s*has\s+been\s+([^.]+)',
            r'([A-Z][A-Za-z\s,.\(\)]+),\s*aged\s+(\d+),\s*has\s+been\s+([^.]+)\s+since\s+([^.]+)',
        ]

        # Executive Director patterns (enhanced for biographical data)
        executive_director_patterns = [
            r'# ([A-Z][A-Za-z\s,.\(\)]+)\s*\n\s*Executive\s+(?:Deputy\s+)?(?:Chairman|Director)',
            r'([A-Z][A-Za-z\s,.\(\)]+),\s*aged\s+(\d+),\s*has\s+been\s+[^.]*Executive\s+(?:Deputy\s+)?(?:Chairman|Director)',
            r'Mr\s+([A-Z][A-Za-z\s,.\(\)]+)\s*\(Executive\s+Deputy\s+Chairman\)',
            r'([A-Z][A-Za-z\s,.\(\)]+)\s*(?:\([0-9]+\))?\s*(?:,\s*[A-Za-z\s,]+)?\s*\|\s*Executive\s+(?:Deputy\s+)?(?:Chairman|Director)',
        ]

        # Non-Executive Director patterns
        non_executive_director_patterns = [
            r'# ([A-Z][A-Za-z\s,.\(\)]+)\s*\n\s*(?:Chairman\s+and\s+)?Non-executive\s+(?:Deputy\s+)?Director',
            r'([A-Z][A-Za-z\s,.\(\)]+),\s*aged\s+(\d+),\s*has\s+been\s+[^.]*Non-executive\s+(?:Deputy\s+)?Director',
            r'Mr\s+([A-Z][A-Za-z\s,.\(\)]+)\s*\(Non-executive\s+Deputy\s+Chairman\)',
        ]

        # Independent Director patterns
        independent_director_patterns = [
            r'# ([A-Z][A-Za-z\s,.\(\)]+)\s*\n\s*Independent\s+Non-executive\s+Director',
            r'([A-Z][A-Za-z\s,.\(\)]+),\s*aged\s+(\d+),\s*has\s+been\s+an\s+Independent\s+Non-executive\s+Director',
            r'Mr\s+([A-Z][A-Za-z\s,.\(\)]+)\s*Independent\s+Non-executive\s+Director',
            r'Ms\s+([A-Z][A-Za-z\s,.\(\)]+)\s*Independent\s+Non-executive\s+Director',
        ]

        # Chairman patterns (enhanced)
        chairman_patterns = [
            r'# ([A-Z][A-Za-z\s,.\(\)]+)\s*\n\s*Chairman\s+and\s+Non-executive\s+Director',
            r'([A-Z][A-Za-z\s,.\(\)]+),\s*aged\s+(\d+),\s*has\s+been\s+Chairman',
            r'Mr\s+([A-Z][A-Za-z\s,.\(\)]+)\s*Chairman\s+and\s+Non-executive\s+Director',
        ]

        # Deputy Chairman patterns
        deputy_chairman_patterns = [
            r'([A-Z][A-Za-z\s,.\(\)]+)\s*(?:\([0-9]+\))?\s*(?:,\s*[A-Za-z\s,]+)?\s*\|\s*(?:Executive|Non-executive)\s+Deputy\s+Chairman',
            r'([A-Z][A-Za-z\s,.\(\)]+),\s*aged\s+(\d+),\s*[^.]*re-designated\s+as\s+(?:Executive|Non-executive)\s+Deputy\s+Chairman',
        ]

        # CEO/COO patterns (enhanced)
        ceo_coo_patterns = [
            r'# ([A-Z][A-Za-z\s,.\(\)]+)\s*\n\s*(?:Executive\s+Director\s+and\s+)?Chief\s+(?:Executive|Operating)\s+Officer',
            r'([A-Z][A-Za-z\s,.\(\)]+),\s*aged\s+(\d+),\s*has\s+been\s+[^.]*Chief\s+(?:Executive|Operating)\s+Officer',
            r'Mr\s+([A-Z][A-Za-z\s,.\(\)]+)\s*\(Chief\s+(?:Executive|Operating)\s+Officer\)',
        ]

        # Management team patterns
        management_patterns = [
            r'# ([A-Z][A-Za-z\s,.\(\)]+)\s*\n\s*Chief\s+(?:Financial|Technology)\s+Officer',
            r'([A-Z][A-Za-z\s,.\(\)]+),\s*aged\s+(\d+),\s*has\s+been\s+Chief\s+(?:Financial|Technology)\s+Officer',
        ]

        # Committee patterns (enhanced for biographical extraction)
        committee_patterns = [
            r'([A-Z][A-Za-z\s,.\(\)]+)[^.]*Chairman\s+of\s+the\s+([A-Za-z\s]+Committee)',
            r'([A-Z][A-Za-z\s,.\(\)]+)[^.]*(?:member|Chairman)\s+of\s+the\s+([A-Za-z\s]+Committee)\s+since\s+([^.]+)',
            r'(Audit|Remuneration|Nomination|Sustainability)\s+Committee:\s*([A-Z][A-Za-z\s,.\(\)]+(?:\s*\([^)]+\))?(?:\s*,\s*[A-Z][A-Za-z\s,.\(\)]+)*)',
        ]

        # Company Secretary patterns
        secretary_patterns = [
            r'# Company Secretary[^#]*?([A-Z][A-Za-z\s,.\(\)]+)',
            r'Company Secretary[^A-Z]*([A-Z][A-Za-z\s,.\(\)]+)',
            r'([A-Z][A-Za-z\s,.\(\)]+)\s*(?:-\s*)?Company Secretary'
        ]

        # Auditor patterns
        auditor_patterns = [
            r'# Auditor[^#]*?([A-Z][A-Za-z\s,.\(\)]+(?:\s*Certified Public Accountants)?)',
            r'Auditor[^A-Z]*([A-Z][A-Za-z\s,.\(\)]+)',
            r'(PricewaterhouseCoopers|Deloitte|KPMG|Ernst & Young|BDO|Grant Thornton|RSM|Mazars|PKF|Moore Stephens)[^#]*?Certified Public Accountants'
        ]

        # Extract entities using enhanced biographical patterns
        for pattern in executive_director_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)
            # Handle both simple matches and tuple matches (with age, etc.)
            for match in matches:
                if isinstance(match, tuple):
                    corporate_roles["executive_directors"].append(match[0].strip())
                else:
                    corporate_roles["executive_directors"].append(match.strip())

        for pattern in non_executive_director_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)
            for match in matches:
                if isinstance(match, tuple):
                    corporate_roles["non_executive_directors"].append(match[0].strip())
                else:
                    corporate_roles["non_executive_directors"].append(match.strip())

        for pattern in independent_director_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)
            for match in matches:
                if isinstance(match, tuple):
                    corporate_roles["independent_directors"].append(match[0].strip())
                else:
                    corporate_roles["independent_directors"].append(match.strip())

        for pattern in chairman_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)
            for match in matches:
                if isinstance(match, tuple):
                    corporate_roles["chairman"].append(match[0].strip())
                else:
                    corporate_roles["chairman"].append(match.strip())

        for pattern in deputy_chairman_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)
            for match in matches:
                if isinstance(match, tuple):
                    corporate_roles["deputy_chairman"].append(match[0].strip())
                else:
                    corporate_roles["deputy_chairman"].append(match.strip())

        for pattern in ceo_coo_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)
            for match in matches:
                if isinstance(match, tuple):
                    corporate_roles["ceo_coo"].append(match[0].strip())
                else:
                    corporate_roles["ceo_coo"].append(match.strip())

        for pattern in management_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)
            for match in matches:
                if isinstance(match, tuple):
                    corporate_roles["other_roles"].append(match[0].strip())
                else:
                    corporate_roles["other_roles"].append(match.strip())

        for pattern in committee_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)
            for match in matches:
                if isinstance(match, tuple) and len(match) >= 2:
                    committee_info = f"{match[1].strip()}: {match[0].strip()}"
                    corporate_roles["board_committees"].append(committee_info)
                else:
                    corporate_roles["board_committees"].append(str(match).strip())

        for pattern in secretary_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            corporate_roles["company_secretaries"].extend([match.strip() for match in matches if match.strip()])

        for pattern in auditor_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)
            corporate_roles["auditors"].extend([match.strip() for match in matches if match.strip()])

        # Remove duplicates
        for key in corporate_roles:
            corporate_roles[key] = list(set(corporate_roles[key]))

        return corporate_roles

    def _parse_corporate_role_entry(self, entry: str) -> Dict[str, str]:
        """
        Parse a corporate role entry into structured components.

        Expected format: "**SURNAME** Given Names - Qualifications | Role Title (Time Period)"

        Args:
            entry: Corporate role entry string

        Returns:
            Dictionary with parsed components
        """
        parsed = {
            "full_name": "",
            "surname": "",
            "given_names": "",
            "qualifications": "",
            "role_title": "",
            "time_period": "",
            "raw_entry": entry
        }

        try:
            # Extract time period if present (in parentheses at the end)
            time_match = re.search(r'\(([^)]+(?:effective|from|since|until|to)[^)]*)\)$', entry, re.IGNORECASE)
            if time_match:
                parsed["time_period"] = time_match.group(1).strip()
                entry = entry[:time_match.start()].strip()

            # Split by | to separate name/qualifications from role title
            if ' | ' in entry:
                name_qual_part, role_part = entry.split(' | ', 1)
                parsed["role_title"] = role_part.strip()
            else:
                name_qual_part = entry

            # Split by - to separate name from qualifications
            if ' - ' in name_qual_part:
                name_part, qual_part = name_qual_part.split(' - ', 1)
                # Check if qual_part is actually a role title (no | separator and contains role keywords)
                role_keywords = ['secretary', 'director', 'chairman', 'officer', 'auditor', 'committee']
                if not parsed["role_title"] and any(keyword in qual_part.lower() for keyword in role_keywords):
                    parsed["role_title"] = qual_part.strip()
                else:
                    parsed["qualifications"] = qual_part.strip()
            else:
                name_part = name_qual_part

            # Extract surname (bolded) and given names
            surname_match = re.search(r'\*\*([A-Z]+)\*\*', name_part)
            if surname_match:
                parsed["surname"] = surname_match.group(1)
                # Remove the bolded surname and clean up the remaining name
                remaining_name = re.sub(r'\*\*[A-Z]+\*\*\s*', '', name_part).strip()
                parsed["given_names"] = remaining_name
                parsed["full_name"] = f"{parsed['surname']} {remaining_name}".strip()
            else:
                # Fallback if no bolded surname found
                parsed["full_name"] = name_part.strip()
                # Try to guess surname (first word if all caps, or last word)
                name_words = parsed["full_name"].split()
                if name_words and name_words[0].isupper():
                    parsed["surname"] = name_words[0]
                    parsed["given_names"] = " ".join(name_words[1:])
                elif name_words:
                    parsed["surname"] = name_words[-1]
                    parsed["given_names"] = " ".join(name_words[:-1])

        except Exception as e:
            logger.warning(f"Error parsing corporate role entry '{entry}': {e}")

        return parsed

    def _extract_ownership_rule_based(self, text: str) -> Dict[str, List[str]]:
        """Extract ownership information using rule-based patterns."""
        ownership = {
            "direct_ownership": [],
            "indirect_ownership": [],
            "shareholding_disclosures": []
        }

        # Direct ownership patterns
        direct_patterns = [
            r'(?:owns|holds|direct ownership of|directly owns)\s+(\d+(?:\.\d+)?%?\s*(?:shares?|stake|interest|equity))',
            r'(\d+(?:\.\d+)?%)\s+(?:direct|ownership|shareholding|stake)',
            r'direct(?:ly)?\s+(?:owns|holds)\s+([^,\.]+)'
        ]

        # Indirect ownership patterns
        indirect_patterns = [
            r'(?:indirect ownership|indirectly owns|through subsidiaries)\s+([^,\.]+)',
            r'(?:via|through)\s+([A-Z][A-Za-z\s&.,]+(?:Ltd|Inc|Corp|Corporation|Limited|AG|SE|Pte|Pty|LLC|LLP)?)\s+(?:owns|holds)',
            r'indirect(?:ly)?\s+(?:owns|holds)\s+([^,\.]+)'
        ]

        # Shareholding disclosure patterns
        disclosure_patterns = [
            r'(?:disclosure|disclosed|filing|filed)\s+(?:of|regarding)\s+([^,\.]+(?:shares?|shareholding|stake))',
            r'(?:substantial|major)\s+(?:shareholder|shareholding)\s+([^,\.]+)',
            r'(?:shareholding|stake)\s+(?:disclosure|filing)\s+([^,\.]+)'
        ]

        # Extract entities using patterns
        for pattern in direct_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            ownership["direct_ownership"].extend([match.strip() for match in matches if match.strip()])

        for pattern in indirect_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            ownership["indirect_ownership"].extend([match.strip() for match in matches if match.strip()])

        for pattern in disclosure_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            ownership["shareholding_disclosures"].extend([match.strip() for match in matches if match.strip()])

        # Remove duplicates
        for key in ownership:
            ownership[key] = list(set(ownership[key]))

        return ownership

    def _extract_transactions_rule_based(self, text: str) -> Dict[str, List[str]]:
        """Extract transaction information using rule-based patterns."""
        transactions = {
            "mergers": [],
            "joint_ventures": [],
            "spin_offs": [],
            "asset_sales": [],
            "rights_issues": [],
            "general_offers": [],
            "other_transactions": []
        }

        # Merger patterns
        merger_patterns = [
            r'(?:merger|merge|consolidation|amalgamation)\s+(?:with|of|between)\s+([A-Z][A-Za-z\s&.,]+(?:Ltd|Inc|Corp|Corporation|Limited|AG|SE|Pte|Pty|LLC|LLP)?)',
            r'([A-Z][A-Za-z\s&.,]+(?:Ltd|Inc|Corp|Corporation|Limited|AG|SE|Pte|Pty|LLC|LLP)?)\s+(?:merger|merge|consolidation)'
        ]

        # Joint venture patterns
        jv_patterns = [
            r'(?:joint venture|JV|partnership)\s+(?:with|between)\s+([A-Z][A-Za-z\s&.,]+(?:Ltd|Inc|Corp|Corporation|Limited|AG|SE|Pte|Pty|LLC|LLP)?)',
            r'([A-Z][A-Za-z\s&.,]+(?:Ltd|Inc|Corp|Corporation|Limited|AG|SE|Pte|Pty|LLC|LLP)?)\s+(?:joint venture|JV)'
        ]

        # Spin-off patterns
        spinoff_patterns = [
            r'(?:spin-off|spinoff|demerger|divestiture)\s+(?:of|from)\s+([A-Z][A-Za-z\s&.,]+(?:Ltd|Inc|Corp|Corporation|Limited|AG|SE|Pte|Pty|LLC|LLP)?)',
            r'([A-Z][A-Za-z\s&.,]+(?:Ltd|Inc|Corp|Corporation|Limited|AG|SE|Pte|Pty|LLC|LLP)?)\s+(?:spin-off|spinoff|demerger)'
        ]

        # Asset sale patterns
        sale_patterns = [
            r'(?:asset sale|sale of assets|disposal)\s+(?:of|to)\s+([A-Z][A-Za-z\s&.,]+(?:Ltd|Inc|Corp|Corporation|Limited|AG|SE|Pte|Pty|LLC|LLP)?)',
            r'(?:sale|disposal|divestment)\s+(?:to|of)\s+([A-Z][A-Za-z\s&.,]+(?:Ltd|Inc|Corp|Corporation|Limited|AG|SE|Pte|Pty|LLC|LLP)?)'
        ]

        # Rights issue patterns
        rights_patterns = [
            r'(?:rights issue|rights offering|equity raise)\s+(?:by|of)\s+([A-Z][A-Za-z\s&.,]+(?:Ltd|Inc|Corp|Corporation|Limited|AG|SE|Pte|Pty|LLC|LLP)?)',
            r'([A-Z][A-Za-z\s&.,]+(?:Ltd|Inc|Corp|Corporation|Limited|AG|SE|Pte|Pty|LLC|LLP)?)\s+(?:rights issue|rights offering)'
        ]

        # General offer patterns
        offer_patterns = [
            r'(?:general offer|takeover offer|tender offer)\s+(?:for|by)\s+([A-Z][A-Za-z\s&.,]+(?:Ltd|Inc|Corp|Corporation|Limited|AG|SE|Pte|Pty|LLC|LLP)?)',
            r'([A-Z][A-Za-z\s&.,]+(?:Ltd|Inc|Corp|Corporation|Limited|AG|SE|Pte|Pty|LLC|LLP)?)\s+(?:general offer|takeover)'
        ]

        # Extract entities using patterns
        for pattern in merger_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            transactions["mergers"].extend([match.strip() for match in matches if match.strip()])

        for pattern in jv_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            transactions["joint_ventures"].extend([match.strip() for match in matches if match.strip()])

        for pattern in spinoff_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            transactions["spin_offs"].extend([match.strip() for match in matches if match.strip()])

        for pattern in sale_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            transactions["asset_sales"].extend([match.strip() for match in matches if match.strip()])

        for pattern in rights_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            transactions["rights_issues"].extend([match.strip() for match in matches if match.strip()])

        for pattern in offer_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            transactions["general_offers"].extend([match.strip() for match in matches if match.strip()])

        # Remove duplicates
        for key in transactions:
            transactions[key] = list(set(transactions[key]))

        return transactions

    def _extract_personal_connections_rule_based(self, text: str) -> Dict[str, List[str]]:
        """Extract personal connections using rule-based patterns."""
        connections = {
            "marriages": [],
            "career_overlaps": [],
            "alma_mater": [],
            "other_connections": []
        }

        # Marriage patterns
        marriage_patterns = [
            r'([A-Z][A-Za-z\s]+)\s+(?:married to|spouse of|wife of|husband of)\s+([A-Z][A-Za-z\s]+)',
            r'([A-Z][A-Za-z\s]+)\s+and\s+([A-Z][A-Za-z\s]+)\s+(?:are married|were married)'
        ]

        # Career overlap patterns
        career_patterns = [
            r'([A-Z][A-Za-z\s]+)\s+(?:worked with|colleague of|former colleague)\s+([A-Z][A-Za-z\s]+)',
            r'(?:both|previously)\s+(?:worked at|employed by)\s+([A-Z][A-Za-z\s&.,]+(?:Ltd|Inc|Corp|Corporation|Limited|AG|SE|Pte|Pty|LLC|LLP)?)',
            r'([A-Z][A-Za-z\s]+)\s+and\s+([A-Z][A-Za-z\s]+)\s+(?:worked together|shared employment)'
        ]

        # Alma mater patterns
        education_patterns = [
            r'(?:graduated from|alumni of|studied at)\s+([A-Z][A-Za-z\s&.,]+(?:University|College|School|Institute))',
            r'([A-Z][A-Za-z\s&.,]+(?:University|College|School|Institute))\s+(?:graduate|alumni)',
            r'([A-Z][A-Za-z\s]+)\s+and\s+([A-Z][A-Za-z\s]+)\s+(?:both attended|classmates at)'
        ]

        # Other connection patterns
        other_patterns = [
            r'([A-Z][A-Za-z\s]+)\s+(?:friend of|associate of|connected to)\s+([A-Z][A-Za-z\s]+)',
            r'(?:family|relative|relation)\s+(?:of|to)\s+([A-Z][A-Za-z\s]+)',
            r'([A-Z][A-Za-z\s]+)\s+(?:knows|acquainted with)\s+([A-Z][A-Za-z\s]+)'
        ]

        # Extract entities using patterns
        for pattern in marriage_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple) and len(match) == 2:
                    connections["marriages"].append(f"{match[0].strip()} - {match[1].strip()}")

        for pattern in career_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    connections["career_overlaps"].append(" - ".join([m.strip() for m in match if m.strip()]))
                else:
                    connections["career_overlaps"].append(match.strip())

        for pattern in education_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    connections["alma_mater"].append(" - ".join([m.strip() for m in match if m.strip()]))
                else:
                    connections["alma_mater"].append(match.strip())

        for pattern in other_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    connections["other_connections"].append(" - ".join([m.strip() for m in match if m.strip()]))
                else:
                    connections["other_connections"].append(match.strip())

        # Remove duplicates
        for key in connections:
            connections[key] = list(set(connections[key]))

        return connections

    def _extract_network_entities_rule_based(self, text: str) -> List[str]:
        """Extract other network-related entities using rule-based patterns."""
        network_entities = []

        # Network entity patterns
        network_patterns = [
            r'(?:subsidiary|affiliate|related company|associated entity)\s+([A-Z][A-Za-z\s&.,]+(?:Ltd|Inc|Corp|Corporation|Limited|AG|SE|Pte|Pty|LLC|LLP)?)',
            r'(?:group company|member of|part of)\s+([A-Z][A-Za-z\s&.,]+(?:Ltd|Inc|Corp|Corporation|Limited|AG|SE|Pte|Pty|LLC|LLP)?)',
            r'(?:network|ecosystem|consortium)\s+(?:of|including)\s+([A-Z][A-Za-z\s&.,]+(?:Ltd|Inc|Corp|Corporation|Limited|AG|SE|Pte|Pty|LLC|LLP)?)'
        ]

        # Extract entities using patterns
        for pattern in network_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            network_entities.extend([match.strip() for match in matches if match.strip()])

        # Remove duplicates
        return list(set(network_entities))
    
    def _extract_companies(self, text: str) -> List[str]:
        """Extract company names from text with enhanced patterns and logging."""
        logger.debug("Starting rule-based company extraction")

        # Known tech companies (extend this list as needed)
        tech_companies = {
            "Google", "Microsoft", "Apple", "Amazon", "Meta", "Facebook",
            "Tesla", "OpenAI", "Anthropic", "Nvidia", "Intel", "AMD",
            "IBM", "Oracle", "Salesforce", "Adobe", "Netflix", "Uber",
            "Airbnb", "Spotify", "Twitter", "LinkedIn", "Snapchat",
            "TikTok", "ByteDance", "Baidu", "Alibaba", "Tencent",
            "Samsung", "Sony", "Huawei", "Xiaomi", "DeepMind"
        }

        # Enhanced company patterns for better detection
        company_patterns = [
            r'\b([A-Z][A-Za-z\s&]+(?:Inc|Corp|Corporation|Ltd|Limited|LLC|LLP|AG|SE|SA|PLC|GmbH))\b',
            r'\b([A-Z][A-Za-z\s&]+(?:Company|Group|Holdings|Enterprises|Industries|Systems|Technologies))\b',
            r'\b(The\s+[A-Z][A-Za-z\s&]+(?:Inc|Corp|Corporation|Ltd|Limited|LLC|LLP|AG|SE|SA|PLC|GmbH))\b',
            r'\b([A-Z][A-Za-z\s&]+\s+(?:Bank|Insurance|Financial|Capital|Investment|Management))\b'
        ]

        found_companies = set()
        text_lower = text.lower()

        # Search for known companies
        for company in tech_companies:
            # Case-insensitive search with word boundaries
            pattern = r'\b' + re.escape(company.lower()) + r'\b'
            if re.search(pattern, text_lower):
                found_companies.add(company)
                logger.debug(f"Found known company: {company}")

        # Search using patterns
        for pattern in company_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if match and len(match.strip()) > 2:
                    company_name = match.strip()
                    found_companies.add(company_name)
                    logger.debug(f"Found company via pattern: {company_name}")

        companies_list = list(found_companies)
        logger.debug(f"Rule-based company extraction found {len(companies_list)} companies")
        return companies_list
    
    def _extract_technologies(self, text: str) -> List[str]:
        """Extract technology terms from text."""
        tech_terms = {
            "AI", "artificial intelligence", "machine learning", "ML",
            "deep learning", "neural network", "LLM", "large language model",
            "GPT", "transformer", "NLP", "natural language processing",
            "computer vision", "reinforcement learning", "generative AI",
            "foundation model", "multimodal", "chatbot", "API",
            "cloud computing", "edge computing", "quantum computing",
            "blockchain", "cryptocurrency", "IoT", "5G", "AR", "VR",
            "autonomous vehicles", "robotics", "automation"
        }
        
        found_terms = set()
        text_lower = text.lower()
        
        for term in tech_terms:
            if term.lower() in text_lower:
                found_terms.add(term)
        
        return list(found_terms)
    
    def _extract_people(self, text: str) -> List[str]:
        """Extract person names from text with enhanced patterns and logging."""
        logger.debug("Starting rule-based people extraction")

        # Known tech leaders (extend this list as needed)
        tech_leaders = {
            "Elon Musk", "Jeff Bezos", "Tim Cook", "Satya Nadella",
            "Sundar Pichai", "Mark Zuckerberg", "Sam Altman",
            "Dario Amodei", "Daniela Amodei", "Jensen Huang",
            "Bill Gates", "Larry Page", "Sergey Brin", "Jack Dorsey",
            "Reed Hastings", "Marc Benioff", "Andy Jassy"
        }

        # Enhanced person name patterns
        person_patterns = [
            r'\b(?:Mr|Mrs|Ms|Dr|Prof|Sir|Dame|Lord|Lady)\.?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b',
            r'\b([A-Z][a-z]+\s+[A-Z][a-z]+)(?:\s*,\s*(?:CEO|CFO|CTO|Chairman|Director|President|Manager))\b',
            r'\b([A-Z][a-z]+\s+[A-Z][a-z]+)(?:\s*\([^)]*(?:CEO|CFO|CTO|Chairman|Director|President|Manager)[^)]*\))\b',
            r'(?:Chairman|CEO|CFO|CTO|Director|President|Manager)[\s:]+([A-Z][a-z]+\s+[A-Z][a-z]+)\b',
            r'\b([A-Z][a-z]+\s+[A-Z][a-z]+)(?:\s+Jr\.?|\s+Sr\.?|\s+II|\s+III|\s+IV)?\b'
        ]

        found_people = set()

        # Search for known people
        for person in tech_leaders:
            if person in text:
                found_people.add(person)
                logger.debug(f"Found known person: {person}")

        # Search using patterns
        for pattern in person_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if match and len(match.strip()) > 3:
                    person_name = match.strip()
                    # Additional validation to ensure it's likely a person name
                    words = person_name.split()
                    if len(words) >= 2 and all(word[0].isupper() for word in words):
                        # Check it's not obviously a company
                        person_lower = person_name.lower()
                        org_indicators = ['inc', 'corp', 'ltd', 'llc', 'company', 'group']
                        if not any(indicator in person_lower for indicator in org_indicators):
                            found_people.add(person_name)
                            logger.debug(f"Found person via pattern: {person_name}")

        people_list = list(found_people)
        logger.debug(f"Rule-based people extraction found {len(people_list)} people")
        return people_list
    
    def _extract_locations(self, text: str) -> List[str]:
        """Extract location names from text."""
        locations = {
            "Silicon Valley", "San Francisco", "Seattle", "Austin",
            "New York", "Boston", "London", "Tel Aviv", "Singapore",
            "Beijing", "Shanghai", "Tokyo", "Seoul", "Bangalore",
            "Mountain View", "Cupertino", "Redmond", "Menlo Park"
        }
        
        found_locations = set()
        
        for location in locations:
            if location in text:
                found_locations.add(location)
        
        return list(found_locations)
    
    async def clear_graph(self):
        """Clear all data from the knowledge graph."""
        if not self._initialized:
            await self.initialize()
        
        logger.warning("Clearing knowledge graph...")
        await self.graph_client.clear_graph()
        logger.info("Knowledge graph cleared")


class SimpleEntityExtractor:
    """Simple rule-based entity extractor as fallback."""
    
    def __init__(self):
        """Initialize extractor."""
        self.company_patterns = [
            r'\b(?:Google|Microsoft|Apple|Amazon|Meta|Facebook|Tesla|OpenAI)\b',
            r'\b\w+\s+(?:Inc|Corp|Corporation|Ltd|Limited|AG|SE)\b'
        ]
        
        self.tech_patterns = [
            r'\b(?:AI|artificial intelligence|machine learning|ML|deep learning)\b',
            r'\b(?:neural network|transformer|GPT|LLM|NLP)\b',
            r'\b(?:cloud computing|API|blockchain|IoT|5G)\b'
        ]
    
    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract entities using patterns."""
        entities = {
            "companies": [],
            "technologies": []
        }
        
        # Extract companies
        for pattern in self.company_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            entities["companies"].extend(matches)
        
        # Extract technologies
        for pattern in self.tech_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            entities["technologies"].extend(matches)
        
        # Remove duplicates and clean up
        entities["companies"] = list(set(entities["companies"]))
        entities["technologies"] = list(set(entities["technologies"]))
        
        return entities


# Factory function
def create_graph_builder() -> GraphBuilder:
    """Create graph builder instance."""
    return GraphBuilder()


# Example usage
async def main():
    """Example usage of the graph builder."""
    from .chunker import ChunkingConfig, create_chunker
    
    # Create chunker and graph builder
    config = ChunkingConfig(chunk_size=300, use_semantic_splitting=False)
    chunker = create_chunker(config)
    graph_builder = create_graph_builder()

    sample_text = """
    TechCorp Ltd announced a merger with InnovateCorp Inc, with John Smith serving as
    executive director and Mary Johnson as company secretary. The transaction involves
    a direct ownership of 51% shares by TechCorp, while InnovateCorp maintains indirect
    ownership through its subsidiary HoldingCorp AG.

    The document issuer, Financial Services Authority, disclosed that the payee for
    the transaction will be Investment Bank Ltd. The target company, StartupTech Pte,
    has filed a shareholding disclosure showing substantial ownership changes.

    Personal connections revealed that John Smith and Mary Johnson both graduated from
    Stanford University and previously worked together at Microsoft. The joint venture
    between TechCorp and InnovateCorp represents a significant consolidation in the
    artificial intelligence and machine learning space.

    The spin-off of the robotics division will create a separate entity, while the
    rights issue will raise additional capital for expansion into cloud computing
    and blockchain technologies.
    """

    # Chunk the document
    chunks = chunker.chunk_document(
        content=sample_text,
        title="Corporate Network Analysis",
        source="example.md"
    )
    
    print(f"Created {len(chunks)} chunks")
    
    # Method 1: Extract entities from entire document (RECOMMENDED)
    # This provides better context and more accurate entity extraction
    enriched_chunks = await graph_builder.extract_entities_from_document(
        chunks,
        extract_companies=True,
        extract_technologies=False,
        extract_people=True,
        extract_financial_entities=True,
        extract_corporate_roles=True,
        extract_ownership=True,
        extract_transactions=True,
        extract_personal_connections=True,
        use_llm=True,
        use_llm_for_companies=False,
        use_llm_for_technologies=False,
        use_llm_for_people=False,
        use_llm_for_financial_entities=False,
        use_llm_for_corporate_roles=True,  # Only this uses LLM
        use_llm_for_ownership=False,
        use_llm_for_transactions=False,
        use_llm_for_personal_connections=False
    )

    # Method 2: Extract entities chunk by chunk (alternative)
    # Use this if you need different entities per chunk or for very large documents
    # enriched_chunks = await graph_builder.extract_entities_from_chunks(
    #     chunks,
    #     extract_companies=True,
    #     extract_technologies=False,
    #     extract_people=True,
    #     extract_financial_entities=True,
    #     extract_corporate_roles=True,
    #     extract_ownership=True,
    #     extract_transactions=True,
    #     extract_personal_connections=True,
    #     use_llm=True,
    #     use_llm_for_companies=False,
    #     use_llm_for_technologies=False,
    #     use_llm_for_people=False,
    #     use_llm_for_financial_entities=False,
    #     use_llm_for_corporate_roles=True,  # Only this uses LLM
    #     use_llm_for_ownership=False,
    #     use_llm_for_transactions=False,
    #     use_llm_for_personal_connections=False
    # )
    
    for i, chunk in enumerate(enriched_chunks):
        entities = chunk.metadata.get('entities', {})
        print(f"\nChunk {i} entities:")
        for category, items in entities.items():
            if items:  # Only show non-empty categories
                if isinstance(items, dict):
                    print(f"  {category}:")
                    for subcategory, subitems in items.items():
                        if subitems:
                            print(f"    {subcategory}: {subitems}")
                else:
                    print(f"  {category}: {items}")
    
    # Add to knowledge graph
    try:
        result = await graph_builder.add_document_to_graph(
            chunks=enriched_chunks,
            document_title="Corporate Network Analysis",
            document_source="example.md",
            document_metadata={"topic": "Corporate Networks", "date": "2024"}
        )
        
        print(f"Graph building result: {result}")
        
    except Exception as e:
        print(f"Graph building failed: {e}")
    
    finally:
        await graph_builder.close()


if __name__ == "__main__":
    asyncio.run(main())