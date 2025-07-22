#!/usr/bin/env python3
"""
Staging ingestion process that extracts entities/relationships but doesn't immediately add to Graphiti.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime, timezone

from ingestion.chunker import DocumentChunk
from ingestion.graph_builder import GraphBuilder
from staging.staging_manager import staging_manager
from agent.entity_models import Person, Company, PersonType, CompanyType

logger = logging.getLogger(__name__)


class StagingIngestion:
    """Handles document ingestion with staging for review."""
    
    def __init__(self):
        """Initialize staging ingestion."""
        self.graph_builder = GraphBuilder()
        
    async def ingest_document_for_review(
        self,
        file_path: str,
        document_title: str = None,
        document_source: str = None,
        extract_entities: bool = True
    ) -> str:
        """
        Ingest a document and stage extracted entities/relationships for review.
        
        Args:
            file_path: Path to the document file
            document_title: Title of the document
            document_source: Source of the document
            extract_entities: Whether to extract entities
            
        Returns:
            Staging session ID
        """
        try:
            # Initialize graph builder
            await self.graph_builder.initialize()
            
            # Create staging session
            if not document_title:
                document_title = Path(file_path).stem
            
            session_id = staging_manager.create_staging_session(
                document_title=document_title,
                document_source=document_source or file_path
            )
            
            logger.info(f"Starting staging ingestion for: {document_title}")
            
            # Process document into chunks
            from ingestion.chunker import create_chunker, ChunkingConfig

            # Create chunking configuration
            chunking_config = ChunkingConfig(
                chunk_size=8000,
                chunk_overlap=800,
                max_chunk_size=25000,
                min_chunk_size=100,
                use_semantic_splitting=True,
                preserve_structure=True
            )

            # Read file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            chunker = create_chunker(chunking_config)
            chunks = await chunker.chunk_document(
                content=content,
                title=document_title,
                source=document_source or file_path
            )
            
            logger.info(f"Document chunked into {len(chunks)} chunks")
            
            if extract_entities and chunks:
                # Extract entities from document
                await self._extract_and_stage_entities(session_id, chunks, document_title)
            
            logger.info(f"Staging ingestion complete. Session ID: {session_id}")
            return session_id
            
        except Exception as e:
            logger.error(f"Staging ingestion failed: {e}")
            raise
        finally:
            await self.graph_builder.close()
    
    async def _extract_and_stage_entities(
        self,
        session_id: str,
        chunks: List[DocumentChunk],
        document_title: str
    ):
        """Extract entities and relationships and stage them for review."""
        try:
            # Extract entities from document using the graph builder
            enriched_chunks = await self.graph_builder.extract_entities_from_document(
                chunks,
                extract_companies=True,
                extract_people=True,
                extract_financial_entities=True,
                extract_corporate_roles=True,
                extract_ownership=True,
                extract_transactions=True,
                extract_personal_connections=True,
                use_llm=True,
                use_llm_for_companies=True,
                use_llm_for_people=True,
                use_llm_for_financial_entities=True,
                use_llm_for_corporate_roles=True,
                use_llm_for_ownership=True,
                use_llm_for_transactions=True,
                use_llm_for_personal_connections=True
            )
            
            # Process extracted entities and relationships
            total_entities = 0
            total_relationships = 0
            
            for chunk in enriched_chunks:
                if hasattr(chunk, 'metadata') and chunk.metadata:
                    entities = chunk.metadata.get('entities', {})
                    
                    # Stage people with enhanced attributes
                    people = entities.get('people', [])
                    for person_name in people:
                        if person_name and isinstance(person_name, str):
                            # Clean name (remove markdown formatting)
                            clean_name = person_name.replace("**", "").strip()

                            # Extract additional person attributes from context
                            person_attributes = self._extract_person_attributes(person_name, chunk.content)

                            entity_data = {
                                "name": clean_name,
                                "type": "Person",
                                "attributes": {
                                    "entity_type": "person",
                                    "source_chunk": chunk.index,
                                    **person_attributes
                                },
                                "confidence": 0.8,
                                "source_text": chunk.content[:200] + "..." if len(chunk.content) > 200 else chunk.content
                            }
                            staging_manager.add_entity_to_staging(session_id, entity_data)
                            total_entities += 1
                    
                    # Stage companies with enhanced attributes
                    companies = entities.get('companies', [])
                    for company_name in companies:
                        if company_name and isinstance(company_name, str):
                            # Clean name (remove markdown formatting)
                            clean_name = company_name.replace("**", "").strip()

                            # Extract additional company attributes from context
                            company_attributes = self._extract_company_attributes(company_name, chunk.content)

                            entity_data = {
                                "name": clean_name,
                                "type": "Company",
                                "attributes": {
                                    "entity_type": "company",
                                    "source_chunk": chunk.index,
                                    **company_attributes
                                },
                                "confidence": 0.8,
                                "source_text": chunk.content[:200] + "..." if len(chunk.content) > 200 else chunk.content
                            }
                            staging_manager.add_entity_to_staging(session_id, entity_data)
                            total_entities += 1
                    
                    # Extract and stage relationships from corporate roles
                    corporate_roles = entities.get('corporate_roles', {})
                    if isinstance(corporate_roles, dict):
                        for role_category, roles in corporate_roles.items():
                            if isinstance(roles, list):
                                for role_info in roles:
                                    if isinstance(role_info, dict):
                                        person_name = role_info.get('name', '')
                                        company_name = role_info.get('company', '')
                                        position = role_info.get('position', role_category)

                                        if person_name and company_name:
                                            relationship_data = {
                                                "source": person_name,
                                                "target": company_name,
                                                "type": "Employment",
                                                "attributes": {
                                                    "position": position,
                                                    "role_category": role_category,
                                                    "source_chunk": chunk.index
                                                },
                                                "confidence": 0.9,
                                                "source_text": chunk.content[:200] + "..." if len(chunk.content) > 200 else chunk.content
                                            }
                                            staging_manager.add_relationship_to_staging(session_id, relationship_data)
                                            total_relationships += 1

                    # Extract additional relationships from text patterns
                    additional_relationships = self._extract_relationships_from_text(chunk.content, entities)
                    for rel_data in additional_relationships:
                        rel_data["attributes"]["source_chunk"] = chunk.index
                        rel_data["source_text"] = chunk.content[:200] + "..." if len(chunk.content) > 200 else chunk.content
                        staging_manager.add_relationship_to_staging(session_id, rel_data)
                        total_relationships += 1
            
            logger.info(f"Staged {total_entities} entities and {total_relationships} relationships for review")
            
        except Exception as e:
            logger.error(f"Entity extraction and staging failed: {e}")
            raise

    def _extract_person_attributes(self, person_name: str, content: str) -> Dict[str, Any]:
        """Extract additional attributes for a person from the content."""
        attributes = {}
        content_lower = content.lower()

        # Clean person name (remove markdown formatting)
        clean_person_name = person_name.replace("**", "").strip()
        person_lower = clean_person_name.lower()

        # Escape special regex characters
        import re
        person_escaped = re.escape(person_lower)

        # Extract position/title
        position_patterns = [
            rf"{person_escaped}\s+is\s+(?:the\s+)?([^,.\n]+?)(?:\s+of|\s+at|,|\.|$)",
            rf"{person_escaped}\s+serves\s+as\s+(?:the\s+)?([^,.\n]+?)(?:\s+of|\s+at|,|\.|$)",
            rf"{person_escaped},?\s+([^,.\n]*?(?:ceo|cto|cfo|president|director|manager|executive|chairman|founder)[^,.\n]*?)(?:,|\.|$)",
        ]

        for pattern in position_patterns:
            match = re.search(pattern, content_lower, re.IGNORECASE)
            if match:
                position = match.group(1).strip()
                if position and len(position) < 100:  # Reasonable length
                    attributes["position"] = position.title()
                    break

        # Extract company
        company_patterns = [
            rf"{person_escaped}\s+(?:is|serves)\s+(?:the\s+)?[^,.\n]*?\s+(?:of|at)\s+([^,.\n]+?)(?:,|\.|$)",
            rf"{person_escaped}\s+(?:works|worked)\s+(?:for|at)\s+([^,.\n]+?)(?:,|\.|$)",
            rf"{person_escaped}\s+joined\s+([^,.\n]+?)(?:,|\.|$)",
        ]

        for pattern in company_patterns:
            match = re.search(pattern, content_lower, re.IGNORECASE)
            if match:
                company = match.group(1).strip()
                if company and len(company) < 100:
                    attributes["current_company"] = company.title()
                    break

        # Extract age if mentioned
        age_pattern = rf"{person_escaped}[^.\n]*?(?:age|aged)\s+(\d+)"
        age_match = re.search(age_pattern, content_lower, re.IGNORECASE)
        if age_match:
            attributes["age"] = int(age_match.group(1))

        # Extract education if mentioned
        education_patterns = [
            rf"{person_escaped}[^.\n]*?(?:graduated|studied|degree)\s+(?:from\s+)?([^,.\n]+?)(?:,|\.|$)",
            rf"{person_escaped}[^.\n]*?(?:university|college|school)\s+(?:of\s+)?([^,.\n]+?)(?:,|\.|$)",
        ]

        for pattern in education_patterns:
            match = re.search(pattern, content_lower, re.IGNORECASE)
            if match:
                education = match.group(1).strip()
                if education and len(education) < 100:
                    attributes["education"] = education.title()
                    break

        return attributes

    def _extract_company_attributes(self, company_name: str, content: str) -> Dict[str, Any]:
        """Extract additional attributes for a company from the content."""
        attributes = {}
        content_lower = content.lower()

        # Clean company name (remove markdown formatting)
        clean_company_name = company_name.replace("**", "").strip()
        company_lower = clean_company_name.lower()

        # Escape special regex characters
        import re
        company_escaped = re.escape(company_lower)

        # Extract industry
        industry_patterns = [
            rf"{company_escaped}\s+is\s+a\s+([^,.\n]*?)(?:\s+company|,|\.|$)",
            rf"{company_escaped}[^.\n]*?(?:specializes|focuses)\s+(?:in|on)\s+([^,.\n]+?)(?:,|\.|$)",
            rf"{company_escaped}[^.\n]*?(?:industry|sector|business)\s+(?:of\s+)?([^,.\n]+?)(?:,|\.|$)",
        ]

        for pattern in industry_patterns:
            match = re.search(pattern, content_lower, re.IGNORECASE)
            if match:
                industry = match.group(1).strip()
                if industry and len(industry) < 100:
                    attributes["industry"] = industry.title()
                    break

        # Extract location/headquarters
        location_patterns = [
            rf"{company_escaped}[^.\n]*?(?:based|located|headquarters)\s+(?:in|at)\s+([^,.\n]+?)(?:,|\.|$)",
            rf"{company_escaped}[^.\n]*?(?:from|in)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*?)(?:,|\.|$)",
        ]

        for pattern in location_patterns:
            match = re.search(pattern, content_lower, re.IGNORECASE)
            if match:
                location = match.group(1).strip()
                if location and len(location) < 100:
                    attributes["headquarters"] = location.title()
                    break

        # Extract founding year
        founded_pattern = rf"{company_escaped}[^.\n]*?(?:founded|established|started)\s+(?:in\s+)?(\d{{4}})"
        founded_match = re.search(founded_pattern, content_lower, re.IGNORECASE)
        if founded_match:
            attributes["founded_year"] = int(founded_match.group(1))

        # Extract company type
        type_patterns = [
            rf"{company_escaped}\s+(?:is\s+a\s+)?([^,.\n]*?(?:private|public|corporation|inc|ltd|llc)[^,.\n]*?)(?:,|\.|$)",
        ]

        for pattern in type_patterns:
            match = re.search(pattern, content_lower, re.IGNORECASE)
            if match:
                company_type = match.group(1).strip()
                if company_type and len(company_type) < 100:
                    attributes["company_type"] = company_type.title()
                    break

        return attributes
    
    async def ingest_approved_items(self, session_id: str) -> Dict[str, Any]:
        """
        Ingest approved entities and relationships into Graphiti.
        
        Args:
            session_id: Staging session ID
            
        Returns:
            Ingestion results
        """
        try:
            # Get approved items
            approved_items = staging_manager.get_approved_items(session_id)
            approved_entities = approved_items["entities"]
            approved_relationships = approved_items["relationships"]
            
            logger.info(f"Ingesting {len(approved_entities)} entities and {len(approved_relationships)} relationships")
            
            # Initialize graph builder
            await self.graph_builder.initialize()
            
            # Add approved entities to Graphiti
            entity_results = []
            for entity in approved_entities:
                try:
                    if entity["type"] == "Person":
                        person = Person(
                            name=entity["name"],
                            person_type=PersonType.OTHER,
                            **entity.get("attributes", {})
                        )
                        episode_id = await self.graph_builder.graph_client.add_entity(person)
                        entity_results.append({"entity": entity["name"], "episode_id": episode_id, "status": "success"})
                    elif entity["type"] == "Company":
                        company = Company(
                            name=entity["name"],
                            company_type=CompanyType.PRIVATE,
                            **entity.get("attributes", {})
                        )
                        episode_id = await self.graph_builder.graph_client.add_entity(company)
                        entity_results.append({"entity": entity["name"], "episode_id": episode_id, "status": "success"})
                except Exception as e:
                    logger.error(f"Failed to add entity {entity['name']}: {e}")
                    entity_results.append({"entity": entity["name"], "error": str(e), "status": "failed"})
            
            # Add approved relationships
            relationship_results = []
            for relationship in approved_relationships:
                try:
                    # For now, we'll add relationships as episodes
                    # In a full implementation, you'd create proper relationship objects
                    relationship_content = f"Relationship: {relationship['source']} {relationship['type']} {relationship['target']}"
                    episode_id = f"rel_{relationship['id']}"
                    
                    await self.graph_builder.graph_client.add_episode(
                        episode_id=episode_id,
                        content=relationship_content,
                        source="approved_relationship",
                        timestamp=datetime.now(timezone.utc),
                        metadata=relationship.get("attributes", {})
                    )
                    relationship_results.append({
                        "relationship": f"{relationship['source']} -> {relationship['target']}", 
                        "episode_id": episode_id, 
                        "status": "success"
                    })
                except Exception as e:
                    logger.error(f"Failed to add relationship {relationship['source']} -> {relationship['target']}: {e}")
                    relationship_results.append({
                        "relationship": f"{relationship['source']} -> {relationship['target']}", 
                        "error": str(e), 
                        "status": "failed"
                    })
            
            # Mark session as ingested
            staging_manager.mark_session_ingested(session_id)
            
            results = {
                "session_id": session_id,
                "entities_ingested": len([r for r in entity_results if r["status"] == "success"]),
                "relationships_ingested": len([r for r in relationship_results if r["status"] == "success"]),
                "entity_results": entity_results,
                "relationship_results": relationship_results
            }
            
            logger.info(f"Ingestion complete: {results['entities_ingested']} entities, {results['relationships_ingested']} relationships")
            return results
            
        except Exception as e:
            logger.error(f"Approved items ingestion failed: {e}")
            raise
        finally:
            await self.graph_builder.close()

    def _extract_relationships_from_text(self, content: str, entities: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract relationships from text using pattern matching."""
        relationships = []

        people = entities.get('people', [])
        companies = entities.get('companies', [])

        # Employment/Leadership relationship patterns
        employment_patterns = [
            (r"(\w+(?:\s+\w+)*)\s+is\s+(?:the\s+)?([^,.\n]*?(?:ceo|cto|cfo|president|director|manager|executive|chairman|founder)[^,.\n]*?)\s+(?:of|at)\s+([^,.\n]+)", "Employment"),
            (r"(\w+(?:\s+\w+)*)\s+serves\s+as\s+(?:the\s+)?([^,.\n]*?)\s+(?:of|at)\s+([^,.\n]+)", "Leadership"),
            (r"(\w+(?:\s+\w+)*)\s+works\s+(?:for|at)\s+([^,.\n]+)", "Employment"),
            (r"(\w+(?:\s+\w+)*)\s+joined\s+([^,.\n]+)", "Employment"),
            (r"(\w+(?:\s+\w+)*)\s+leads\s+([^,.\n]+)", "Leadership"),
        ]

        import re
        for pattern, rel_type in employment_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                if rel_type == "Employment" and len(match.groups()) == 3:
                    person, position, company = match.groups()
                elif rel_type == "Employment" and len(match.groups()) == 2:
                    person, company = match.groups()
                    position = "Employee"
                elif len(match.groups()) >= 2:
                    person, company = match.groups()[:2]
                    position = match.groups()[2] if len(match.groups()) > 2 else "Unknown"
                else:
                    continue

                person = person.strip()
                company = company.strip()

                # Validate that entities exist in our extracted lists
                if any(p.lower() == person.lower() for p in people) and \
                   any(c.lower() == company.lower() for c in companies):

                    relationship_data = {
                        "source": person,
                        "target": company,
                        "type": rel_type,
                        "attributes": {
                            "position": position.strip() if 'position' in locals() else "Unknown",
                            "extraction_method": "pattern_matching"
                        },
                        "confidence": 0.8
                    }
                    relationships.append(relationship_data)

        # Partnership/Investment relationships
        business_patterns = [
            (r"([^,.\n]+)\s+(?:partners|partnered)\s+with\s+([^,.\n]+)", "Partnership"),
            (r"([^,.\n]+)\s+(?:invests|invested)\s+in\s+([^,.\n]+)", "Investment"),
            (r"([^,.\n]+)\s+(?:owns|acquired)\s+([^,.\n]+)", "Ownership"),
            (r"([^,.\n]+)\s+(?:subsidiary|division)\s+of\s+([^,.\n]+)", "Ownership"),
        ]

        for pattern, rel_type in business_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                source, target = match.groups()
                source = source.strip()
                target = target.strip()

                # Check if both entities exist in our lists
                source_exists = any(c.lower() == source.lower() for c in companies) or \
                               any(p.lower() == source.lower() for p in people)
                target_exists = any(c.lower() == target.lower() for c in companies) or \
                               any(p.lower() == target.lower() for p in people)

                if source_exists and target_exists:
                    relationship_data = {
                        "source": source,
                        "target": target,
                        "type": rel_type,
                        "attributes": {
                            "extraction_method": "pattern_matching"
                        },
                        "confidence": 0.7
                    }
                    relationships.append(relationship_data)

        return relationships


# Global staging ingestion instance
staging_ingestion = StagingIngestion()
