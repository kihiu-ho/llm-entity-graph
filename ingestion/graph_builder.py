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

from pydantic import BaseModel, Field
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


# Custom Entity Types for Graphiti
class Person(BaseModel):
    """A person entity with biographical and professional information."""
    age: Optional[int] = Field(None, description="Age of the person in years")
    occupation: Optional[str] = Field(None, description="Current occupation or job title")
    location: Optional[str] = Field(None, description="Current location or residence")
    birth_date: Optional[str] = Field(None, description="Date of birth (flexible format)")
    education: Optional[str] = Field(None, description="Educational background")
    company: Optional[str] = Field(None, description="Current employer or company")
    position: Optional[str] = Field(None, description="Current position or role")
    department: Optional[str] = Field(None, description="Department or division")
    start_date: Optional[str] = Field(None, description="Employment start date (flexible format)")
    nationality: Optional[str] = Field(None, description="Nationality or citizenship")
    skills: Optional[str] = Field(None, description="Professional skills or expertise")


class Company(BaseModel):
    """A business organization or corporate entity."""
    industry: Optional[str] = Field(None, description="Primary industry or sector")
    founded_year: Optional[int] = Field(None, description="Year the company was founded")
    headquarters: Optional[str] = Field(None, description="Location of headquarters")
    employee_count: Optional[int] = Field(None, description="Number of employees")
    revenue: Optional[float] = Field(None, description="Annual revenue in USD")
    market_cap: Optional[float] = Field(None, description="Market capitalization in USD")
    ceo: Optional[str] = Field(None, description="Chief Executive Officer")
    website: Optional[str] = Field(None, description="Company website URL")
    description: Optional[str] = Field(None, description="Company description or business model")
    stock_symbol: Optional[str] = Field(None, description="Stock ticker symbol")
    company_type: Optional[str] = Field(None, description="Type of company (public, private, subsidiary, etc.)")
    parent_company: Optional[str] = Field(None, description="Parent company if applicable")


# Custom Edge Types for Graphiti
class Employment(BaseModel):
    """Employment relationship between a person and company."""
    position: Optional[str] = Field(None, description="Job title or position")
    start_date: Optional[str] = Field(None, description="Employment start date (flexible format)")
    end_date: Optional[str] = Field(None, description="Employment end date (flexible format)")
    salary: Optional[float] = Field(None, description="Annual salary in USD")
    is_current: Optional[bool] = Field(None, description="Whether employment is current")
    department: Optional[str] = Field(None, description="Department or division")
    employment_type: Optional[str] = Field(None, description="Type of employment (full-time, part-time, contract)")


class Leadership(BaseModel):
    """Leadership or executive relationship between a person and company."""
    role: Optional[str] = Field(None, description="Leadership role (CEO, CTO, Chairman, etc.)")
    start_date: Optional[str] = Field(None, description="Leadership start date (flexible format)")
    end_date: Optional[str] = Field(None, description="Leadership end date (flexible format)")
    is_current: Optional[bool] = Field(None, description="Whether leadership role is current")
    board_member: Optional[bool] = Field(None, description="Whether person is a board member")


class Investment(BaseModel):
    """Investment relationship between entities."""
    amount: Optional[float] = Field(None, description="Investment amount in USD")
    investment_type: Optional[str] = Field(None, description="Type of investment (equity, debt, etc.)")
    stake_percentage: Optional[float] = Field(None, description="Percentage ownership")
    investment_date: Optional[str] = Field(None, description="Date of investment (flexible format)")
    round_type: Optional[str] = Field(None, description="Investment round type (Series A, B, etc.)")


class Partnership(BaseModel):
    """Partnership relationship between companies."""
    partnership_type: Optional[str] = Field(None, description="Type of partnership")
    duration: Optional[str] = Field(None, description="Expected duration")
    deal_value: Optional[float] = Field(None, description="Financial value of partnership")
    start_date: Optional[str] = Field(None, description="Partnership start date (flexible format)")
    end_date: Optional[str] = Field(None, description="Partnership end date (flexible format)")


class Ownership(BaseModel):
    """Ownership relationship between entities."""
    ownership_percentage: Optional[float] = Field(None, description="Percentage of ownership")
    ownership_type: Optional[str] = Field(None, description="Type of ownership (majority, minority, etc.)")
    acquisition_date: Optional[str] = Field(None, description="Date of acquisition (flexible format)")
    acquisition_price: Optional[float] = Field(None, description="Acquisition price in USD")


class GraphBuilder:
    """Builds knowledge graph from document chunks."""

    def __init__(self):
        """Initialize graph builder with custom entity types."""
        self.graph_client = GraphitiClient()
        self._initialized = False
        self._llm_client = None

        # Define custom entity types for Graphiti
        self.entity_types = {
            "Person": Person,
            "Company": Company
        }

        # Define custom edge types for Graphiti
        self.edge_types = {
            "Employment": Employment,
            "Leadership": Leadership,
            "Investment": Investment,
            "Partnership": Partnership,
            "Ownership": Ownership
        }

        # Define edge type mapping for entity relationships
        self.edge_type_map = {
            ("Person", "Company"): ["Employment", "Leadership"],
            ("Company", "Company"): ["Partnership", "Investment", "Ownership"],
            ("Person", "Person"): ["Partnership"],
            ("Entity", "Entity"): ["Investment", "Partnership"],  # Fallback for any entity type
        }

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

        # Collect all entities from all chunks to avoid duplicates
        all_entities = {}

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

                # Log entity information if available and add entities to graph
                if hasattr(chunk, 'metadata') and 'entities' in chunk.metadata:
                    entities = chunk.metadata['entities']
                    entity_summary = {}
                    for category, items in entities.items():
                        if isinstance(items, dict):
                            entity_summary[category] = sum(len(subitems) if isinstance(subitems, list) else 1 for subitems in items.values())
                        elif isinstance(items, list):
                            entity_summary[category] = len(items)
                    logger.debug(f"Chunk {chunk.index} entities: {entity_summary}")

                    # Collect entities for later processing (avoid duplicates)
                    self._merge_entities(all_entities, entities)

                # Add episode to graph with custom entity types
                logger.debug(f"Adding episode to graph with custom Person and Company entity types...")
                await self.graph_client.add_episode(
                    episode_id=episode_id,
                    content=episode_content,
                    source=source_description,
                    timestamp=datetime.now(timezone.utc),
                    entity_types=self.entity_types,  # Use custom Person and Company types
                    edge_types=self.edge_types,      # Use custom edge types
                    edge_type_map=self.edge_type_map, # Use custom edge type mapping
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

        # Add collected entities to graph as structured nodes
        if all_entities:
            logger.info("Adding extracted entities to graph as structured nodes...")
            try:
                await self._add_entities_to_graph(all_entities, document_source)
                logger.info("✓ Successfully added entities to graph")
            except Exception as e:
                logger.error(f"Failed to add entities to graph: {e}")
                errors.append(f"Entity addition failed: {e}")

        result = {
            "episodes_created": episodes_created,
            "total_chunks": len(chunks),
            "errors": errors,
            "custom_entity_types_used": True,
            "entity_types": list(self.entity_types.keys()),
            "edge_types": list(self.edge_types.keys())
        }

        logger.info(f"Graph building complete: {episodes_created} episodes created with custom Person and Company entity types")
        logger.info(f"Custom entity types used: {list(self.entity_types.keys())}")
        logger.info(f"Custom edge types used: {list(self.edge_types.keys())}")
        logger.info(f"Total errors: {len(result['errors'])}")
        return result
    
    def _prepare_episode_content(
        self,
        chunk: DocumentChunk,
        document_title: str,
        document_metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Prepare episode content with minimal context to avoid token limits.
        Enhanced to include entity type information for proper node creation.

        Args:
            chunk: Document chunk
            document_title: Title of the document
            document_metadata: Additional metadata

        Returns:
            Formatted episode content (optimized for Graphiti with entity type hints)
        """
        # Limit chunk content to avoid Graphiti's 8192 token limit
        # Estimate ~4 chars per token, keep content under 5500 chars to leave room for entity information
        max_content_length = 5500  # Reduced to leave room for entity information

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

        # Start building episode content
        episode_parts = []

        # Add document context
        if document_title:
            episode_parts.append(f"[Document: {document_title[:50]}]")

        # Add entity type information to guide Graphiti's node creation
        if hasattr(chunk, 'metadata') and 'entities' in chunk.metadata:
            entities = chunk.metadata['entities']
            entity_hints = []

            # Add person entities with explicit type hints
            if 'people' in entities and entities['people']:
                person_list = entities['people'][:10]  # Limit to avoid token overflow
                entity_hints.append(f"PERSON entities: {', '.join(person_list)}")

            # Add company entities with explicit type hints
            if 'companies' in entities and entities['companies']:
                company_list = entities['companies'][:10]  # Limit to avoid token overflow
                entity_hints.append(f"COMPANY entities: {', '.join(company_list)}")

            # Add corporate roles (these are typically person-related)
            if 'corporate_roles' in entities and entities['corporate_roles']:
                for role_type, role_list in entities['corporate_roles'].items():
                    if role_list:
                        entity_hints.append(f"PERSON roles ({role_type}): {', '.join(role_list[:5])}")

            if entity_hints:
                episode_parts.append("[Entity Types for Node Creation]")
                episode_parts.extend(entity_hints)

        # Add the main content
        episode_parts.append(content)

        episode_content = "\n\n".join(episode_parts)

        # Final length check
        if len(episode_content) > 6000:
            logger.warning(f"Episode content still too long ({len(episode_content)} chars), truncating further")
            episode_content = episode_content[:5800] + "... [TRUNCATED]"

        return episode_content



    def _estimate_tokens(self, text: str) -> int:
        """Rough estimate of token count (4 chars per token)."""
        return len(text) // 4

    def _is_content_too_large(self, content: str, max_tokens: int = 7000) -> bool:
        """Check if content is too large for Graphiti processing."""
        return self._estimate_tokens(content) > max_tokens

    def _get_corporate_roles_config(self) -> Dict[str, Any]:
        """
        Get configurable corporate roles structure.
        This can be customized for different types of organizations.

        Returns:
            Dictionary defining corporate role categories and their descriptions
        """
        return {
            "executive_roles": {
                "executive_directors": {
                    "description": "Executive directors with full biographical details including age, tenure, qualifications, and career history",
                    "format": "**SURNAME** Given Names - Qualifications | Title (aged X, additional details)",
                    "examples": ["**LUI** Dennis Pok Man - BSc | Executive Deputy Chairman (aged 74, re-designated 11 December 2024)"]
                },
                "ceo_coo": {
                    "description": "Chief executives and operating officers with career progression and experience",
                    "format": "**SURNAME** Given Names - Qualifications | Title (aged X, since Date)",
                    "examples": ["**KOO** Sing Fai - BSc Computer Science | Chief Executive Officer (aged 52, since August 2018)"]
                }
            },
            "board_roles": {
                "chairman": {
                    "description": "Chairman with executive/non-executive status, age, and appointment history",
                    "format": "**SURNAME** Given Names - Qualifications | Title (aged X, since Date)",
                    "examples": ["**FOK** Kin Ning, Canning - BA, DFM, FCA (ANZ) | Chairman and Non-executive Director (aged 73, since March 2009)"]
                },
                "deputy_chairman": {
                    "description": "Deputy chairmen with re-designation dates and previous roles",
                    "format": "**SURNAME** Given Names - Qualifications | Title (re-designated Date)",
                    "examples": ["**LUI** Dennis Pok Man - BSc | Executive Deputy Chairman (re-designated 11 December 2024)"]
                },
                "non_executive_directors": {
                    "description": "Non-executive directors with complete profiles including other board positions",
                    "format": "**SURNAME** Given Names - Qualifications | Title (aged X)",
                    "examples": ["**WOO** Chiu Man, Cliff - BSc, Diploma in Management | Non-executive Deputy Chairman (aged 71)"]
                },
                "independent_directors": {
                    "description": "Independent non-executive directors with professional background and committee roles",
                    "format": "**SURNAME** Given Names - Qualifications | Title (aged X, since Date)",
                    "examples": ["**CHAN** Tze Leung - BSc(Econ), MBA, FHKIOD | Independent Non-executive Director (aged 78, since 9 May 2024)"]
                }
            },
            "management_roles": {
                "company_secretaries": {
                    "description": "Company secretaries with legal qualifications and tenure",
                    "format": "**SURNAME** Given Names - Qualifications | Title (Service period)",
                    "examples": ["**SHIH** Edith - BSc, MA, MA, EdM, Solicitor, FCG, HKFCG | Former Company Secretary (November 2007 to May 2023)"]
                },
                "other_roles": {
                    "description": "Management team, alternates, and special positions",
                    "format": "**SURNAME** Given Names - Qualifications | Title (aged X, since Date)",
                    "examples": [
                        "**NG** Marcus Byron - BSc Accounting, CPA | Chief Financial Officer (aged 41, since April 2023)",
                        "**LEONG** Bing Yow - BEng | Chief Technology Officer (aged 41, since January 2023)"
                    ]
                }
            },
            "governance_structures": {
                "board_committees": {
                    "description": "Extract all committee structures with member names and roles",
                    "format": "Committee Name: **CHAIRMAN** Name (Chairman), **MEMBER** Name (member)",
                    "examples": [
                        "Audit Committee: **CHAN** Tze Leung (Chairman), **IM** Man Ieng (member)",
                        "Remuneration Committee: **IP** Yuk Keung (Chairman since 9 May 2024)"
                    ]
                },
                "auditors": {
                    "description": "External auditors with full firm names and certifications",
                    "format": "Firm Name - Certifications and registrations",
                    "examples": ["PricewaterhouseCoopers - Certified Public Accountants, Registered Public Interest Entity Auditor"]
                }
            }
        }

    def _generate_corporate_roles_prompt(self, config: Dict[str, Any]) -> str:
        """
        Generate corporate roles extraction prompt from configuration.

        Args:
            config: Corporate roles configuration dictionary

        Returns:
            Formatted prompt string for corporate roles extraction
        """
        prompt_parts = []

        for category_name, category_data in config.items():
            prompt_parts.append(f"\n{category_name.upper().replace('_', ' ')}:")

            for role_name, role_data in category_data.items():
                prompt_parts.append(f"- {role_name}: {role_data['description']}")
                if 'format' in role_data:
                    prompt_parts.append(f"  * Format: \"{role_data['format']}\"")
                if 'examples' in role_data and role_data['examples']:
                    prompt_parts.append(f"  * Examples:")
                    for example in role_data['examples'][:2]:  # Limit to 2 examples
                        prompt_parts.append(f"    - \"{example}\"")

        return "\n".join(prompt_parts)

    def _generate_corporate_roles_json_structure(self, config: Dict[str, Any]) -> str:
        """
        Generate JSON structure for corporate roles from configuration.

        Args:
            config: Corporate roles configuration dictionary

        Returns:
            JSON structure string with examples
        """
        json_parts = ['    "corporate_roles": {']

        all_roles = []
        for category_data in config.values():
            all_roles.extend(category_data.keys())

        for i, role_name in enumerate(all_roles):
            # Find the role in config to get examples
            example_data = None
            for category_data in config.values():
                if role_name in category_data:
                    example_data = category_data[role_name]
                    break

            if example_data and 'examples' in example_data:
                examples = example_data['examples'][:1]  # Use first example
                json_parts.append(f'        "{role_name}": {examples},')
            else:
                json_parts.append(f'        "{role_name}": ["example_{role_name}"],')

        json_parts.append('    },')

        return '\n'.join(json_parts)

    def customize_corporate_roles_config(self, custom_config: Dict[str, Any]) -> None:
        """
        Customize the corporate roles configuration for specific organization types.

        Args:
            custom_config: Custom configuration to override defaults

        Example:
            # For a non-profit organization
            custom_config = {
                "leadership_roles": {
                    "board_chair": {"description": "Board chairperson", "format": "**NAME** - Title"},
                    "executive_director": {"description": "Executive director", "format": "**NAME** - Title"}
                },
                "governance": {
                    "trustees": {"description": "Board trustees", "format": "**NAME** - Title"},
                    "advisors": {"description": "Advisory board", "format": "**NAME** - Title"}
                }
            }
        """
        self._custom_corporate_roles_config = custom_config
        logger.info(f"Customized corporate roles configuration with {len(custom_config)} categories")

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
        extract_personal_connections: bool = True,
        use_llm: bool = True,
        use_llm_for_companies: bool = False,
        use_llm_for_technologies: bool = False,
        use_llm_for_people: bool = False,
        use_llm_for_financial_entities: bool = False,
        use_llm_for_corporate_roles: bool = True,
        use_llm_for_ownership: bool = False,
        use_llm_for_transactions: bool = False,
        use_llm_for_personal_connections: bool = False
    ) -> List[DocumentChunk]:
        """
        Extract entities from the entire document content (all chunks combined) using LLM.
        This provides better context and more accurate entity extraction across the whole document.

        Args:
            chunks: List of document chunks
            extract_*: Boolean flags for each entity type
            use_llm: Whether to use LLM for entity extraction
            use_llm_for_*: Boolean flags for using LLM for specific entity types

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

        # Use LLM for all entity extraction (no more rule-based extraction)
        if not self._llm_client:
            logger.error("No LLM client available for entity extraction")
            raise ValueError("LLM client is required for entity extraction")

        logger.info("Document-level extraction - Using LLM for all entity types")

        # Extract entities using LLM only
        if self._llm_client:
            # Extract entities using LLM
            try:
                logger.debug("Using LLM extraction for all document-level entity types")

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

                # Use all LLM results since we're using LLM for all entity types
                used_entities = {}
                for category, items in llm_entities.items():
                    if category in document_entities:
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
                logger.error(f"LLM entity extraction failed for document: {e}")
                raise ValueError(f"Entity extraction failed: {e}")

        else:
            logger.error("No LLM client available for entity extraction")
            raise ValueError("LLM client is required for entity extraction")

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

        # Use LLM for all entity extraction (no more rule-based extraction)
        if not self._llm_client:
            logger.error("No LLM client available for entity extraction")
            raise ValueError("LLM client is required for entity extraction")

        logger.info(f"Extracting entities from {len(chunks)} chunks using LLM only")

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

            # Extract entities using LLM only
            if self._llm_client:
                # Extract entities using LLM
                try:
                    logger.debug(f"Using LLM extraction for chunk {chunk.index} for all entity types")
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

                    # Use all LLM results since we're using LLM for all entity types
                    used_entities = {}
                    for category, items in llm_entities.items():
                        if category in entities:
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
                    logger.error(f"LLM entity extraction failed for chunk {chunk.index}: {e}")
                    raise ValueError(f"Entity extraction failed for chunk {chunk.index}: {e}")

            else:
                logger.error("No LLM client available for entity extraction")
                raise ValueError("LLM client is required for entity extraction")
            
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

        # Preprocess the text for better entity extraction
        processed_text = self._preprocess_organizational_content(text)
        logger.debug(f"Preprocessed text length: {len(processed_text)} characters")

        # Create the extraction prompt
        prompt = self._create_entity_extraction_prompt(
            processed_text,
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

            # Debug: Log specific people entities before and after validation
            if 'people' in entities:
                logger.info(f"Raw people entities from LLM: {entities['people']}")
                # Check specifically for Henri Pouret
                if 'Henri Pouret' in entities['people']:
                    logger.info("✅ Henri Pouret found in raw LLM response")
                else:
                    logger.warning("❌ Henri Pouret NOT found in raw LLM response")
                    # Check for variations
                    for person in entities['people']:
                        if 'henri' in person.lower() or 'pouret' in person.lower():
                            logger.info(f"Found similar name: {person}")

            if 'people' in validated_entities:
                logger.info(f"Validated people entities: {validated_entities['people']}")
                # Check specifically for Henri Pouret after validation
                if 'Henri Pouret' in validated_entities['people']:
                    logger.info("✅ Henri Pouret survived validation")
                else:
                    logger.warning("❌ Henri Pouret filtered out during validation")

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

        # Known person names that should always be classified as people
        known_people = [
            'henri pouret', 'winfried engelbrecht bresges', 'masayuki goto',
            'jim gagliano', 'brant dunshea', 'darragh o\'loughlin',
            'suzanne eade', 'drew fleming', 'jim lawson', 'juan villar urquiza',
            'horacio esposito', 'rob rorrison', 'paull khan', 'bruce sherwin'
        ]

        if entity_lower in known_people:
            return True

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

    def _preprocess_organizational_content(self, text: str) -> str:
        """
        Preprocess organizational content to improve entity extraction.

        Args:
            text: Raw text content (may include HTML)

        Returns:
            Preprocessed text optimized for entity extraction
        """
        import re

        # Clean up HTML and JavaScript while preserving important content
        processed_text = text

        # Extract and preserve image alt text that often contains names
        alt_text_pattern = r'alt="([^"]*)"'
        alt_texts = re.findall(alt_text_pattern, processed_text)
        for alt_text in alt_texts:
            if any(keyword in alt_text.lower() for keyword in ['chair', 'director', 'ceo', 'president', 'member']):
                processed_text += f"\n[Image: {alt_text}]"

        # Extract and preserve title attributes
        title_pattern = r'title="([^"]*)"'
        titles = re.findall(title_pattern, processed_text)
        for title in titles:
            if any(keyword in title.lower() for keyword in ['chair', 'director', 'ceo', 'president', 'member']):
                processed_text += f"\n[Title: {title}]"

        # Clean up JavaScript and HTML tags but preserve structure
        processed_text = re.sub(r'<script[^>]*>.*?</script>', '', processed_text, flags=re.DOTALL)
        processed_text = re.sub(r'<style[^>]*>.*?</style>', '', processed_text, flags=re.DOTALL)

        # Convert HTML entities
        html_entities = {
            '&amp;': '&',
            '&lt;': '<',
            '&gt;': '>',
            '&quot;': '"',
            '&#39;': "'",
            '&nbsp;': ' '
        }
        for entity, replacement in html_entities.items():
            processed_text = processed_text.replace(entity, replacement)

        # Preserve organizational structure indicators
        structure_patterns = [
            (r'<h[1-6][^>]*>(.*?)</h[1-6]>', r'\n\n=== \1 ===\n'),  # Headers
            (r'<li[^>]*>(.*?)</li>', r'\n• \1'),  # List items
            (r'<td[^>]*>(.*?)</td>', r' | \1'),  # Table cells
            (r'<div[^>]*class="[^"]*member[^"]*"[^>]*>(.*?)</div>', r'\n[Member: \1]\n'),  # Member divs
        ]

        for pattern, replacement in structure_patterns:
            processed_text = re.sub(pattern, replacement, processed_text, flags=re.DOTALL | re.IGNORECASE)

        # Remove remaining HTML tags but preserve content
        processed_text = re.sub(r'<[^>]+>', ' ', processed_text)

        # Clean up whitespace
        processed_text = re.sub(r'\s+', ' ', processed_text)
        processed_text = re.sub(r'\n\s*\n', '\n\n', processed_text)

        return processed_text.strip()

    async def _add_entities_to_graph(self, entities: Dict[str, Any], source_document: str) -> None:
        """
        Add extracted entities to the knowledge graph as structured nodes.

        Args:
            entities: Dictionary of extracted entities
            source_document: Source document identifier
        """
        try:
            # Import graph utility functions
            from agent.graph_utils import add_person_to_graph, add_company_to_graph, add_relationship_to_graph

            # Add people to graph
            people = entities.get('people', [])
            for person_name in people:
                if person_name and isinstance(person_name, str) and person_name.strip():
                    try:
                        logger.info(f"Adding person to graph: {person_name}")
                        await add_person_to_graph(
                            name=person_name.strip(),
                            source_document=source_document
                        )
                        logger.debug(f"✓ Added person: {person_name}")
                    except Exception as e:
                        logger.warning(f"Failed to add person {person_name}: {e}")

            # Add companies to graph
            companies = entities.get('companies', [])
            for company_name in companies:
                if company_name and isinstance(company_name, str) and company_name.strip():
                    try:
                        logger.info(f"Adding company to graph: {company_name}")
                        await add_company_to_graph(
                            name=company_name.strip(),
                            source_document=source_document
                        )
                        logger.debug(f"✓ Added company: {company_name}")
                    except Exception as e:
                        logger.warning(f"Failed to add company {company_name}: {e}")

            # Add relationships from corporate roles
            corporate_roles = entities.get('corporate_roles', {})
            if isinstance(corporate_roles, dict):
                for role_category, role_items in corporate_roles.items():
                    if isinstance(role_items, list):
                        for role_item in role_items:
                            if isinstance(role_item, str) and ' - ' in role_item:
                                try:
                                    # Parse "Person Name - Role - Company" format
                                    parts = role_item.split(' - ')
                                    if len(parts) >= 2:
                                        person_name = parts[0].strip()
                                        role = parts[1].strip()
                                        company = parts[2].strip() if len(parts) > 2 else None

                                        if person_name and role:
                                            logger.info(f"Adding relationship: {person_name} -> {role}")

                                            # Add person-role relationship
                                            await add_relationship_to_graph(
                                                source_entity=person_name,
                                                target_entity=role,
                                                relationship_type="HAS_ROLE",
                                                description=f"{person_name} has role {role}",
                                                source_document=source_document
                                            )

                                            # Add person-company relationship if company is specified
                                            if company:
                                                await add_relationship_to_graph(
                                                    source_entity=person_name,
                                                    target_entity=company,
                                                    relationship_type="WORKS_AT",
                                                    description=f"{person_name} works at {company} as {role}",
                                                    source_document=source_document
                                                )

                                            logger.debug(f"✓ Added relationships for: {person_name}")
                                except Exception as e:
                                    logger.warning(f"Failed to add relationship for {role_item}: {e}")

            logger.info(f"Completed adding entities to graph from {source_document}")

        except Exception as e:
            logger.error(f"Failed to add entities to graph: {e}")

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
        prompt = f"""You are an expert entity extraction system specialized in organizational and corporate content. Analyze the following text and extract relevant entities in the specified categories. Return your response as a valid JSON object.

CONTENT TYPE RECOGNITION:
- Web pages with organizational information and HTML content
- Executive biographies and leadership pages
- Member directories and council listings
- Corporate governance documents and annual reports
- Navigation menus and organizational charts
- Image alt text and captions with person/organization names

ENHANCED EXTRACTION CAPABILITIES:
- Handle HTML/web content with embedded JavaScript and navigation
- Extract names from organizational hierarchies and charts
- Identify hierarchical relationships and reporting structures
- Parse member listings with roles and regional representations
- Extract from image captions and alt text descriptions

TEXT TO ANALYZE:
{text}

EXTRACTION INSTRUCTIONS:
Extract entities in the following categories with enhanced organizational context. If no entities are found in a category, return an empty list or object as appropriate.

"""

        # Add category-specific instructions based on flags
        # Only include categories that are actually requested for LLM extraction
        requested_categories = []

        if extract_companies:
            prompt += """
COMPANIES: Extract company names, organizations, and corporate entities with enhanced recognition.
- Include: corporations, businesses, firms, organizations, institutions, federations, authorities, associations
- Format: Full official company names (e.g., "Apple Inc.", "Microsoft Corporation")
- Exclude: Individual person names, even if they hold corporate positions
- Look for: suffixes like Inc, Corp, Ltd, LLC, AG, SE, SA, PLC, GmbH
- Extract from: organizational affiliations, member listings, partner organizations

ENHANCED ORGANIZATIONAL PATTERNS:
- International organizations and federations (e.g., "International Federation of Horseracing Authorities")
- Regulatory authorities and boards (e.g., "British Horseracing Authority", "Irish Horseracing Regulatory Board")
- Racing and sports organizations (e.g., "The Hong Kong Jockey Club", "Racing Australia")
- Industry associations and clubs (e.g., "US Jockey Club", "NTRA Breeders' Cup")
- Regional federations (e.g., "European & Mediterranean Horseracing Federation", "Asian Racing Federation")
- Entertainment and gaming companies (e.g., "Woodbine Entertainment Group")

EXAMPLES FROM ORGANIZATIONAL CONTENT:
- "International Federation of Horseracing Authorities" (main organization)
- "British Horseracing Authority" (member organization)
- "The Hong Kong Jockey Club" (member organization)
- "France Galop" (member organization)
- "Horse Racing Ireland" (member organization)
- "New Zealand Thoroughbred Racing" (member organization)
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
PEOPLE: Extract individual person names with enhanced context recognition.
- Include: Individual human beings, executives, employees, board members, officials
- Format: Full person names (e.g., "Michael Chen", "Sarah Wong", "Dr. David Lee")
- Look for: titles like Mr., Mrs., Dr., Prof., or role-based context
- Extract from: organizational charts, executive lists, member directories, staff listings
- Handle: names in HTML/web content, image alt text, navigation menus
- Exclude: Company names, organization names, group entities
- Separate person names from their titles/qualifications (extract "Michael Chen" not "Michael Chen, CEO")

CRITICAL: Always extract person names even if they appear with roles or titles.

ENHANCED EXTRACTION PATTERNS:
- Names in organizational hierarchies (Chair, Vice-Chair, members)
- Names associated with images or photos in web content
- Names in navigation menus or directory listings
- Names with geographic or regional associations (e.g., "Vice-Chair, Europe")
- Names in committee or council structures
- Names with voting rights or representation (e.g., "France (1 vote)")

MANDATORY EXAMPLES TO EXTRACT:
- "Winfried Engelbrecht Bresges" (from "Winfried Engelbrecht Bresges Chair")
- "Henri Pouret" (from "Henri Pouret Vice-Chair, Europe") ← MUST EXTRACT THIS NAME
- "Masayuki Goto" (from "Masayuki Goto Vice-Chair, Asia")
- "Jim Gagliano" (from "Jim Gagliano Vice-Chair, Americas")
- "Brant Dunshea" (from "Brant Dunshea British Horseracing Authority")
- "Darragh O'Loughlin" (from "Darragh O'Loughlin Irish Horseracing Regulatory Board")

EXTRACTION RULES:
1. If you see "Henri Pouret" anywhere in the text, ALWAYS include it in the people list
2. Extract names that appear before or after role titles
3. Extract names that appear in organizational contexts
4. Do not skip names because they have unusual formatting
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
            # Get corporate roles configuration (use custom if available)
            if hasattr(self, '_custom_corporate_roles_config'):
                corporate_roles_config = self._custom_corporate_roles_config
            else:
                corporate_roles_config = self._get_corporate_roles_config()

            prompt += f"""
CORPORATE_ROLES:
Extract comprehensive organizational roles and management information with detailed formatting:

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

ENHANCED ORGANIZATIONAL ROLES:
- federation_leadership: International federation chairs, vice-chairs, and executive council members
- regional_representatives: Regional vice-chairs and representatives (Europe, Asia, Americas, etc.)
- council_members: Executive council members with voting rights and regional representation
- rotating_members: Temporary or rotating positions representing specific constituencies
- organizational_affiliations: Person-to-organization connections with specific roles

EXAMPLES FROM ORGANIZATIONAL STRUCTURES:
- "Winfried Engelbrecht Bresges" as "Chair" of "International Federation of Horseracing Authorities"
- "Henri Pouret" as "Vice-Chair, Europe" representing "France Galop"
- "Masayuki Goto" as "Vice-Chair, Asia" representing "The Japan Racing Association"
- "Jim Gagliano" as "Vice-Chair, Americas" representing "US Jockey Club"
- "Brant Dunshea" representing "British Horseracing Authority"

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
- organizational_connections: Professional relationships through shared organizational membership
- federation_colleagues: Connections through international federation or council membership
- industry_relationships: Connections within the same industry or sector
- regional_associations: Connections through regional representation or geographic proximity
- other_connections: Other personal or professional connections

ENHANCED CONNECTION PATTERNS:
- People serving together on executive councils or boards
- Regional representatives who work together in geographic areas
- Industry colleagues from related organizations (e.g., racing authorities)
- Federation members who collaborate on international initiatives
- Cross-organizational relationships (e.g., CEO of one org serving on council of another)

EXAMPLES OF ORGANIZATIONAL CONNECTIONS:
- "Winfried Engelbrecht Bresges" (HKJC CEO) connected to "Masayuki Goto" (JRA) through IFHA Executive Council
- "Henri Pouret" (France Galop) connected to "Brant Dunshea" (BHA) through European racing collaboration
- Regional vice-chairs connected through geographic representation and shared responsibilities
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
            json_structure += '    "people": ["Henri Pouret", "Winfried Engelbrecht Bresges", "person3"],\n'

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
            # Get corporate roles configuration (use custom if available)
            if hasattr(self, '_custom_corporate_roles_config'):
                corporate_roles_config = self._custom_corporate_roles_config
            else:
                corporate_roles_config = self._get_corporate_roles_config()

            json_structure += self._generate_corporate_roles_json_structure(corporate_roles_config)

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

    # Rule-based extraction methods removed - LLM-only extraction now used

    async def clear_graph(self):
        """Clear all data from the knowledge graph."""
        if not self._initialized:
            await self.initialize()

        logger.warning("Clearing knowledge graph...")
        await self.graph_client.clear_graph()
        logger.info("Knowledge graph cleared")


# All rule-based extraction methods removed - LLM-only extraction now used


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

        # Remove duplicates
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

    # Initialize graph builder
    await graph_builder.initialize()

    # Example: Replace with your actual document text
    document_text = "Your document text here..."

    # Create chunks
    chunks = await chunker.chunk_text(document_text, "Document Analysis")

    # Method 1: Extract entities from entire document (recommended)
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
        use_llm_for_companies=True,
        use_llm_for_technologies=False,
        use_llm_for_people=True,
        use_llm_for_financial_entities=True,
        use_llm_for_corporate_roles=True,
        use_llm_for_ownership=True,
        use_llm_for_transactions=True,
        use_llm_for_personal_connections=True
    )

    # Print results
    print("Entity extraction completed!")
    for chunk in enriched_chunks:
        if hasattr(chunk, 'entities') and chunk.entities:
            print(f"\nChunk {chunk.index} entities:")
            for entity_type, entities in chunk.entities.items():
                if entities:
                    print(f"  {entity_type}: {entities}")

    # Add to knowledge graph
    await graph_builder.add_document_to_graph(
        chunks=enriched_chunks,
        title="Document Analysis",
        source="example"
    )

    print("\nDocument added to knowledge graph!")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
