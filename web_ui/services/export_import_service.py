"""
Export/Import service for entity management system.
Supports JSON, CSV, and Excel formats with validation and conflict resolution.
"""

import os
import json
import csv
import uuid
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Union
from io import StringIO, BytesIO

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    pd = None

from ..models.enhanced_staging_models import (
    EnhancedStagingSession, EnhancedEntity, EnhancedRelationship,
    EntityStatus, ApprovalStage, ValidationResult
)

logger = logging.getLogger(__name__)


class ExportImportService:
    """Service for exporting and importing entity data in various formats."""
    
    def __init__(self, staging_dir: str = "staging/data"):
        self.staging_dir = Path(staging_dir)
        self.staging_dir.mkdir(parents=True, exist_ok=True)
        self._initialized = False
    
    async def initialize(self):
        """Initialize the export/import service."""
        if not self._initialized:
            logger.info("Initializing Export/Import Service")
            self._initialized = True
    
    # Export Methods
    
    async def export_session(self, session_id: str, format_type: str = "json", 
                           include_audit_trail: bool = True) -> Dict[str, Any]:
        """Export a complete session in the specified format."""
        if not self._initialized:
            await self.initialize()
        
        try:
            session = await self._load_session(session_id)
            if not session:
                return {"success": False, "error": "Session not found"}
            
            if format_type.lower() == "json":
                return await self._export_session_json(session, include_audit_trail)
            elif format_type.lower() == "csv":
                return await self._export_session_csv(session)
            elif format_type.lower() == "excel" and PANDAS_AVAILABLE:
                return await self._export_session_excel(session)
            else:
                return {"success": False, "error": f"Unsupported format: {format_type}"}
                
        except Exception as e:
            logger.error(f"Error exporting session {session_id}: {e}")
            return {"success": False, "error": str(e)}
    
    async def export_entities(self, session_id: str, entity_ids: Optional[List[str]] = None,
                            format_type: str = "json") -> Dict[str, Any]:
        """Export specific entities from a session."""
        if not self._initialized:
            await self.initialize()
        
        try:
            session = await self._load_session(session_id)
            if not session:
                return {"success": False, "error": "Session not found"}
            
            # Filter entities if specific IDs provided
            entities = session.entities
            if entity_ids:
                entities = [e for e in entities if e.id in entity_ids]
            
            if format_type.lower() == "json":
                return await self._export_entities_json(entities)
            elif format_type.lower() == "csv":
                return await self._export_entities_csv(entities)
            elif format_type.lower() == "excel" and PANDAS_AVAILABLE:
                return await self._export_entities_excel(entities)
            else:
                return {"success": False, "error": f"Unsupported format: {format_type}"}
                
        except Exception as e:
            logger.error(f"Error exporting entities: {e}")
            return {"success": False, "error": str(e)}
    
    async def export_relationships(self, session_id: str, relationship_ids: Optional[List[str]] = None,
                                 format_type: str = "json") -> Dict[str, Any]:
        """Export specific relationships from a session."""
        if not self._initialized:
            await self.initialize()
        
        try:
            session = await self._load_session(session_id)
            if not session:
                return {"success": False, "error": "Session not found"}
            
            # Filter relationships if specific IDs provided
            relationships = session.relationships
            if relationship_ids:
                relationships = [r for r in relationships if r.id in relationship_ids]
            
            if format_type.lower() == "json":
                return await self._export_relationships_json(relationships)
            elif format_type.lower() == "csv":
                return await self._export_relationships_csv(relationships)
            elif format_type.lower() == "excel" and PANDAS_AVAILABLE:
                return await self._export_relationships_excel(relationships)
            else:
                return {"success": False, "error": f"Unsupported format: {format_type}"}
                
        except Exception as e:
            logger.error(f"Error exporting relationships: {e}")
            return {"success": False, "error": str(e)}
    
    # Import Methods
    
    async def import_data(self, session_id: str, data: Union[str, bytes], 
                         format_type: str, user: str = "import_user",
                         validate: bool = True, merge_strategy: str = "skip") -> Dict[str, Any]:
        """Import data into a session with validation and conflict resolution."""
        if not self._initialized:
            await self.initialize()
        
        try:
            session = await self._load_session(session_id)
            if not session:
                return {"success": False, "error": "Session not found"}
            
            # Parse data based on format
            if format_type.lower() == "json":
                parsed_data = await self._parse_json_import(data)
            elif format_type.lower() == "csv":
                parsed_data = await self._parse_csv_import(data)
            elif format_type.lower() == "excel" and PANDAS_AVAILABLE:
                parsed_data = await self._parse_excel_import(data)
            else:
                return {"success": False, "error": f"Unsupported format: {format_type}"}
            
            if not parsed_data["success"]:
                return parsed_data
            
            # Validate imported data
            validation_result = {"success": True, "errors": [], "warnings": []}
            if validate:
                validation_result = await self._validate_import_data(parsed_data["data"], session)
            
            # Import data with conflict resolution
            import_result = await self._import_validated_data(
                session, parsed_data["data"], user, merge_strategy, validation_result
            )
            
            return {
                "success": import_result["success"],
                "imported_entities": import_result.get("imported_entities", 0),
                "imported_relationships": import_result.get("imported_relationships", 0),
                "skipped_items": import_result.get("skipped_items", 0),
                "conflicts": import_result.get("conflicts", []),
                "validation_errors": validation_result.get("errors", []),
                "validation_warnings": validation_result.get("warnings", [])
            }
            
        except Exception as e:
            logger.error(f"Error importing data: {e}")
            return {"success": False, "error": str(e)}
    
    async def validate_import_file(self, data: Union[str, bytes], format_type: str) -> Dict[str, Any]:
        """Validate an import file without actually importing it."""
        if not self._initialized:
            await self.initialize()
        
        try:
            # Parse data based on format
            if format_type.lower() == "json":
                parsed_data = await self._parse_json_import(data)
            elif format_type.lower() == "csv":
                parsed_data = await self._parse_csv_import(data)
            elif format_type.lower() == "excel" and PANDAS_AVAILABLE:
                parsed_data = await self._parse_excel_import(data)
            else:
                return {"success": False, "error": f"Unsupported format: {format_type}"}
            
            if not parsed_data["success"]:
                return parsed_data
            
            # Basic validation
            data_dict = parsed_data["data"]
            entities = data_dict.get("entities", [])
            relationships = data_dict.get("relationships", [])
            
            validation_errors = []
            validation_warnings = []
            
            # Validate entities
            for i, entity_data in enumerate(entities):
                if not entity_data.get("name"):
                    validation_errors.append(f"Entity {i+1}: Missing required field 'name'")
                if not entity_data.get("type"):
                    validation_errors.append(f"Entity {i+1}: Missing required field 'type'")
            
            # Validate relationships
            entity_ids = {e.get("id") for e in entities if e.get("id")}
            for i, rel_data in enumerate(relationships):
                if not rel_data.get("source_entity_id"):
                    validation_errors.append(f"Relationship {i+1}: Missing required field 'source_entity_id'")
                if not rel_data.get("target_entity_id"):
                    validation_errors.append(f"Relationship {i+1}: Missing required field 'target_entity_id'")
                if not rel_data.get("relationship_type"):
                    validation_errors.append(f"Relationship {i+1}: Missing required field 'relationship_type'")
                
                # Check if referenced entities exist
                source_id = rel_data.get("source_entity_id")
                target_id = rel_data.get("target_entity_id")
                if source_id and source_id not in entity_ids:
                    validation_warnings.append(f"Relationship {i+1}: Source entity {source_id} not found in import data")
                if target_id and target_id not in entity_ids:
                    validation_warnings.append(f"Relationship {i+1}: Target entity {target_id} not found in import data")
            
            return {
                "success": True,
                "valid": len(validation_errors) == 0,
                "entities_count": len(entities),
                "relationships_count": len(relationships),
                "validation_errors": validation_errors,
                "validation_warnings": validation_warnings,
                "preview": {
                    "entities": entities[:5],  # First 5 entities for preview
                    "relationships": relationships[:5]  # First 5 relationships for preview
                }
            }
            
        except Exception as e:
            logger.error(f"Error validating import file: {e}")
            return {"success": False, "error": str(e)}
    
    # Private Export Methods
    
    async def _export_session_json(self, session: EnhancedStagingSession, 
                                  include_audit_trail: bool = True) -> Dict[str, Any]:
        """Export session as JSON."""
        session_dict = session.to_dict()
        
        if not include_audit_trail:
            # Remove audit trail data to reduce file size
            session_dict.pop("audit_trail", None)
            for entity in session_dict.get("entities", []):
                entity.pop("edit_history", None)
            for relationship in session_dict.get("relationships", []):
                relationship.pop("edit_history", None)
        
        return {
            "success": True,
            "data": json.dumps(session_dict, indent=2, ensure_ascii=False),
            "filename": f"session_{session.session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            "content_type": "application/json"
        }
    
    async def _export_session_csv(self, session: EnhancedStagingSession) -> Dict[str, Any]:
        """Export session as CSV (entities and relationships in separate files)."""
        # Create CSV for entities
        entities_csv = await self._export_entities_csv(session.entities)
        relationships_csv = await self._export_relationships_csv(session.relationships)
        
        if not entities_csv["success"] or not relationships_csv["success"]:
            return {"success": False, "error": "Failed to export CSV data"}
        
        # Combine both CSVs with headers
        combined_csv = "# ENTITIES\n" + entities_csv["data"] + "\n\n# RELATIONSHIPS\n" + relationships_csv["data"]
        
        return {
            "success": True,
            "data": combined_csv,
            "filename": f"session_{session.session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "content_type": "text/csv"
        }
    
    async def _export_entities_json(self, entities: List[EnhancedEntity]) -> Dict[str, Any]:
        """Export entities as JSON."""
        entities_data = [entity.to_dict() for entity in entities]
        
        return {
            "success": True,
            "data": json.dumps({"entities": entities_data}, indent=2, ensure_ascii=False),
            "filename": f"entities_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            "content_type": "application/json"
        }
    
    async def _export_entities_csv(self, entities: List[EnhancedEntity]) -> Dict[str, Any]:
        """Export entities as CSV."""
        if not entities:
            return {"success": True, "data": "", "filename": "entities_empty.csv", "content_type": "text/csv"}
        
        output = StringIO()
        writer = csv.writer(output)
        
        # Write header
        headers = ["id", "name", "type", "status", "confidence", "created_at", "updated_at", "source_text"]
        writer.writerow(headers)
        
        # Write entity data
        for entity in entities:
            writer.writerow([
                entity.id,
                entity.name,
                entity.type,
                entity.status.value,
                entity.confidence,
                entity.created_at,
                entity.updated_at,
                entity.source_text or ""
            ])
        
        return {
            "success": True,
            "data": output.getvalue(),
            "filename": f"entities_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "content_type": "text/csv"
        }
    
    async def _export_relationships_json(self, relationships: List[EnhancedRelationship]) -> Dict[str, Any]:
        """Export relationships as JSON."""
        relationships_data = [rel.to_dict() for rel in relationships]
        
        return {
            "success": True,
            "data": json.dumps({"relationships": relationships_data}, indent=2, ensure_ascii=False),
            "filename": f"relationships_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            "content_type": "application/json"
        }
    
    async def _export_relationships_csv(self, relationships: List[EnhancedRelationship]) -> Dict[str, Any]:
        """Export relationships as CSV."""
        if not relationships:
            return {"success": True, "data": "", "filename": "relationships_empty.csv", "content_type": "text/csv"}
        
        output = StringIO()
        writer = csv.writer(output)
        
        # Write header
        headers = ["id", "source_entity_id", "target_entity_id", "relationship_type", "status", "confidence", "created_at", "updated_at"]
        writer.writerow(headers)
        
        # Write relationship data
        for rel in relationships:
            writer.writerow([
                rel.id,
                rel.source_entity_id,
                rel.target_entity_id,
                rel.relationship_type,
                rel.status.value,
                rel.confidence,
                rel.created_at,
                rel.updated_at
            ])
        
        return {
            "success": True,
            "data": output.getvalue(),
            "filename": f"relationships_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "content_type": "text/csv"
        }
    
    # Excel export methods (if pandas is available)
    
    async def _export_session_excel(self, session: EnhancedStagingSession) -> Dict[str, Any]:
        """Export session as Excel with multiple sheets."""
        if not PANDAS_AVAILABLE:
            return {"success": False, "error": "Pandas not available for Excel export"}
        
        try:
            output = BytesIO()
            
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                # Session info sheet
                session_info = pd.DataFrame([{
                    "session_id": session.session_id,
                    "document_title": session.document_title,
                    "document_source": session.document_source,
                    "status": session.status.value,
                    "workflow_stage": session.workflow_stage.value,
                    "created_at": session.created_at,
                    "updated_at": session.updated_at
                }])
                session_info.to_excel(writer, sheet_name='Session Info', index=False)
                
                # Entities sheet
                if session.entities:
                    entities_data = []
                    for entity in session.entities:
                        entities_data.append({
                            "id": entity.id,
                            "name": entity.name,
                            "type": entity.type,
                            "status": entity.status.value,
                            "confidence": entity.confidence,
                            "created_at": entity.created_at,
                            "updated_at": entity.updated_at,
                            "source_text": entity.source_text or ""
                        })
                    entities_df = pd.DataFrame(entities_data)
                    entities_df.to_excel(writer, sheet_name='Entities', index=False)
                
                # Relationships sheet
                if session.relationships:
                    relationships_data = []
                    for rel in session.relationships:
                        relationships_data.append({
                            "id": rel.id,
                            "source_entity_id": rel.source_entity_id,
                            "target_entity_id": rel.target_entity_id,
                            "relationship_type": rel.relationship_type,
                            "status": rel.status.value,
                            "confidence": rel.confidence,
                            "created_at": rel.created_at,
                            "updated_at": rel.updated_at
                        })
                    relationships_df = pd.DataFrame(relationships_data)
                    relationships_df.to_excel(writer, sheet_name='Relationships', index=False)
            
            return {
                "success": True,
                "data": output.getvalue(),
                "filename": f"session_{session.session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                "content_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            }
            
        except Exception as e:
            logger.error(f"Error exporting Excel: {e}")
            return {"success": False, "error": str(e)}
    
    async def _export_entities_excel(self, entities: List[EnhancedEntity]) -> Dict[str, Any]:
        """Export entities as Excel."""
        if not PANDAS_AVAILABLE:
            return {"success": False, "error": "Pandas not available for Excel export"}
        
        try:
            entities_data = []
            for entity in entities:
                entities_data.append({
                    "id": entity.id,
                    "name": entity.name,
                    "type": entity.type,
                    "status": entity.status.value,
                    "confidence": entity.confidence,
                    "created_at": entity.created_at,
                    "updated_at": entity.updated_at,
                    "source_text": entity.source_text or ""
                })
            
            df = pd.DataFrame(entities_data)
            output = BytesIO()
            df.to_excel(output, index=False, engine='openpyxl')
            
            return {
                "success": True,
                "data": output.getvalue(),
                "filename": f"entities_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                "content_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            }
            
        except Exception as e:
            logger.error(f"Error exporting entities Excel: {e}")
            return {"success": False, "error": str(e)}
    
    async def _export_relationships_excel(self, relationships: List[EnhancedRelationship]) -> Dict[str, Any]:
        """Export relationships as Excel."""
        if not PANDAS_AVAILABLE:
            return {"success": False, "error": "Pandas not available for Excel export"}
        
        try:
            relationships_data = []
            for rel in relationships:
                relationships_data.append({
                    "id": rel.id,
                    "source_entity_id": rel.source_entity_id,
                    "target_entity_id": rel.target_entity_id,
                    "relationship_type": rel.relationship_type,
                    "status": rel.status.value,
                    "confidence": rel.confidence,
                    "created_at": rel.created_at,
                    "updated_at": rel.updated_at
                })
            
            df = pd.DataFrame(relationships_data)
            output = BytesIO()
            df.to_excel(output, index=False, engine='openpyxl')
            
            return {
                "success": True,
                "data": output.getvalue(),
                "filename": f"relationships_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                "content_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            }
            
        except Exception as e:
            logger.error(f"Error exporting relationships Excel: {e}")
            return {"success": False, "error": str(e)}

    # Private Import Methods

    async def _parse_json_import(self, data: Union[str, bytes]) -> Dict[str, Any]:
        """Parse JSON import data."""
        try:
            if isinstance(data, bytes):
                data = data.decode('utf-8')

            parsed = json.loads(data)

            # Handle different JSON structures
            if "entities" in parsed or "relationships" in parsed:
                return {"success": True, "data": parsed}
            elif isinstance(parsed, list):
                # Assume it's a list of entities
                return {"success": True, "data": {"entities": parsed, "relationships": []}}
            else:
                return {"success": False, "error": "Invalid JSON structure"}

        except json.JSONDecodeError as e:
            return {"success": False, "error": f"Invalid JSON: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": f"Error parsing JSON: {str(e)}"}

    async def _parse_csv_import(self, data: Union[str, bytes]) -> Dict[str, Any]:
        """Parse CSV import data."""
        try:
            if isinstance(data, bytes):
                data = data.decode('utf-8')

            # Check if it's a combined CSV with sections
            if "# ENTITIES" in data and "# RELATIONSHIPS" in data:
                return await self._parse_combined_csv(data)
            else:
                # Assume it's entities only
                return await self._parse_entities_csv(data)

        except Exception as e:
            return {"success": False, "error": f"Error parsing CSV: {str(e)}"}

    async def _parse_combined_csv(self, data: str) -> Dict[str, Any]:
        """Parse combined CSV with entities and relationships sections."""
        try:
            sections = data.split("# RELATIONSHIPS")
            entities_section = sections[0].replace("# ENTITIES", "").strip()
            relationships_section = sections[1].strip() if len(sections) > 1 else ""

            entities = []
            relationships = []

            # Parse entities
            if entities_section:
                entities_result = await self._parse_entities_csv(entities_section)
                if entities_result["success"]:
                    entities = entities_result["data"]["entities"]

            # Parse relationships
            if relationships_section:
                relationships_result = await self._parse_relationships_csv(relationships_section)
                if relationships_result["success"]:
                    relationships = relationships_result["data"]["relationships"]

            return {"success": True, "data": {"entities": entities, "relationships": relationships}}

        except Exception as e:
            return {"success": False, "error": f"Error parsing combined CSV: {str(e)}"}

    async def _parse_entities_csv(self, data: str) -> Dict[str, Any]:
        """Parse entities from CSV data."""
        try:
            reader = csv.DictReader(StringIO(data))
            entities = []

            for row in reader:
                entity_data = {
                    "id": row.get("id") or str(uuid.uuid4()),
                    "name": row.get("name", ""),
                    "type": row.get("type", ""),
                    "status": row.get("status", "pending"),
                    "confidence": float(row.get("confidence", 0.0)),
                    "source_text": row.get("source_text", ""),
                    "attributes": {}
                }

                # Add any additional columns as attributes
                for key, value in row.items():
                    if key not in ["id", "name", "type", "status", "confidence", "source_text", "created_at", "updated_at"]:
                        entity_data["attributes"][key] = value

                entities.append(entity_data)

            return {"success": True, "data": {"entities": entities, "relationships": []}}

        except Exception as e:
            return {"success": False, "error": f"Error parsing entities CSV: {str(e)}"}

    async def _parse_relationships_csv(self, data: str) -> Dict[str, Any]:
        """Parse relationships from CSV data."""
        try:
            reader = csv.DictReader(StringIO(data))
            relationships = []

            for row in reader:
                relationship_data = {
                    "id": row.get("id") or str(uuid.uuid4()),
                    "source_entity_id": row.get("source_entity_id", ""),
                    "target_entity_id": row.get("target_entity_id", ""),
                    "relationship_type": row.get("relationship_type", ""),
                    "status": row.get("status", "pending"),
                    "confidence": float(row.get("confidence", 0.0)),
                    "attributes": {}
                }

                # Add any additional columns as attributes
                for key, value in row.items():
                    if key not in ["id", "source_entity_id", "target_entity_id", "relationship_type", "status", "confidence", "created_at", "updated_at"]:
                        relationship_data["attributes"][key] = value

                relationships.append(relationship_data)

            return {"success": True, "data": {"entities": [], "relationships": relationships}}

        except Exception as e:
            return {"success": False, "error": f"Error parsing relationships CSV: {str(e)}"}

    async def _parse_excel_import(self, data: bytes) -> Dict[str, Any]:
        """Parse Excel import data."""
        if not PANDAS_AVAILABLE:
            return {"success": False, "error": "Pandas not available for Excel import"}

        try:
            # Read Excel file
            excel_data = pd.read_excel(BytesIO(data), sheet_name=None)

            entities = []
            relationships = []

            # Check for different sheet structures
            if "Entities" in excel_data:
                entities_df = excel_data["Entities"]
                entities = self._dataframe_to_entities(entities_df)

            if "Relationships" in excel_data:
                relationships_df = excel_data["Relationships"]
                relationships = self._dataframe_to_relationships(relationships_df)

            # If no specific sheets, try to parse the first sheet as entities
            if not entities and not relationships and excel_data:
                first_sheet = list(excel_data.values())[0]
                if "source_entity_id" in first_sheet.columns:
                    relationships = self._dataframe_to_relationships(first_sheet)
                else:
                    entities = self._dataframe_to_entities(first_sheet)

            return {"success": True, "data": {"entities": entities, "relationships": relationships}}

        except Exception as e:
            return {"success": False, "error": f"Error parsing Excel: {str(e)}"}

    def _dataframe_to_entities(self, df: 'pd.DataFrame') -> List[Dict[str, Any]]:
        """Convert DataFrame to entities list."""
        entities = []

        for _, row in df.iterrows():
            entity_data = {
                "id": str(row.get("id", uuid.uuid4())),
                "name": str(row.get("name", "")),
                "type": str(row.get("type", "")),
                "status": str(row.get("status", "pending")),
                "confidence": float(row.get("confidence", 0.0)),
                "source_text": str(row.get("source_text", "")),
                "attributes": {}
            }

            # Add any additional columns as attributes
            for col in df.columns:
                if col not in ["id", "name", "type", "status", "confidence", "source_text", "created_at", "updated_at"]:
                    entity_data["attributes"][col] = str(row.get(col, ""))

            entities.append(entity_data)

        return entities

    def _dataframe_to_relationships(self, df: 'pd.DataFrame') -> List[Dict[str, Any]]:
        """Convert DataFrame to relationships list."""
        relationships = []

        for _, row in df.iterrows():
            relationship_data = {
                "id": str(row.get("id", uuid.uuid4())),
                "source_entity_id": str(row.get("source_entity_id", "")),
                "target_entity_id": str(row.get("target_entity_id", "")),
                "relationship_type": str(row.get("relationship_type", "")),
                "status": str(row.get("status", "pending")),
                "confidence": float(row.get("confidence", 0.0)),
                "attributes": {}
            }

            # Add any additional columns as attributes
            for col in df.columns:
                if col not in ["id", "source_entity_id", "target_entity_id", "relationship_type", "status", "confidence", "created_at", "updated_at"]:
                    relationship_data["attributes"][col] = str(row.get(col, ""))

            relationships.append(relationship_data)

        return relationships

    async def _validate_import_data(self, data: Dict[str, Any], session: EnhancedStagingSession) -> Dict[str, Any]:
        """Validate imported data against existing session data."""
        errors = []
        warnings = []

        entities = data.get("entities", [])
        relationships = data.get("relationships", [])

        # Get existing entity IDs and names
        existing_entity_ids = {e.id for e in session.entities}
        existing_entity_names = {e.name.lower() for e in session.entities}

        # Validate entities
        import_entity_ids = set()
        for i, entity_data in enumerate(entities):
            entity_id = entity_data.get("id")
            entity_name = entity_data.get("name", "").lower()

            if not entity_data.get("name"):
                errors.append(f"Entity {i+1}: Missing required field 'name'")
            if not entity_data.get("type"):
                errors.append(f"Entity {i+1}: Missing required field 'type'")

            if entity_id in existing_entity_ids:
                warnings.append(f"Entity {i+1}: ID {entity_id} already exists in session")
            if entity_name in existing_entity_names:
                warnings.append(f"Entity {i+1}: Name '{entity_data.get('name')}' already exists in session")

            if entity_id:
                import_entity_ids.add(entity_id)

        # Validate relationships
        all_entity_ids = existing_entity_ids.union(import_entity_ids)
        for i, rel_data in enumerate(relationships):
            if not rel_data.get("source_entity_id"):
                errors.append(f"Relationship {i+1}: Missing required field 'source_entity_id'")
            if not rel_data.get("target_entity_id"):
                errors.append(f"Relationship {i+1}: Missing required field 'target_entity_id'")
            if not rel_data.get("relationship_type"):
                errors.append(f"Relationship {i+1}: Missing required field 'relationship_type'")

            # Check if referenced entities exist
            source_id = rel_data.get("source_entity_id")
            target_id = rel_data.get("target_entity_id")
            if source_id and source_id not in all_entity_ids:
                errors.append(f"Relationship {i+1}: Source entity {source_id} not found")
            if target_id and target_id not in all_entity_ids:
                errors.append(f"Relationship {i+1}: Target entity {target_id} not found")

        return {
            "success": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }

    async def _import_validated_data(self, session: EnhancedStagingSession, data: Dict[str, Any],
                                   user: str, merge_strategy: str, validation_result: Dict[str, Any]) -> Dict[str, Any]:
        """Import validated data into the session."""
        imported_entities = 0
        imported_relationships = 0
        skipped_items = 0
        conflicts = []

        entities = data.get("entities", [])
        relationships = data.get("relationships", [])

        # Import entities
        existing_entity_ids = {e.id for e in session.entities}
        existing_entity_names = {e.name.lower(): e.id for e in session.entities}

        for entity_data in entities:
            try:
                entity_id = entity_data.get("id", str(uuid.uuid4()))
                entity_name = entity_data.get("name", "").lower()

                # Handle conflicts based on merge strategy
                if entity_id in existing_entity_ids or entity_name in existing_entity_names:
                    if merge_strategy == "skip":
                        skipped_items += 1
                        conflicts.append({
                            "type": "entity",
                            "id": entity_id,
                            "name": entity_data.get("name"),
                            "action": "skipped",
                            "reason": "Already exists"
                        })
                        continue
                    elif merge_strategy == "update":
                        # Update existing entity
                        existing_entity = None
                        if entity_id in existing_entity_ids:
                            existing_entity = session.get_entity_by_id(entity_id)
                        elif entity_name in existing_entity_names:
                            existing_entity = session.get_entity_by_id(existing_entity_names[entity_name])

                        if existing_entity:
                            existing_entity.update_attributes(entity_data.get("attributes", {}), user, "Updated via import")
                            conflicts.append({
                                "type": "entity",
                                "id": entity_id,
                                "name": entity_data.get("name"),
                                "action": "updated",
                                "reason": "Merged with existing"
                            })
                            continue

                # Create new entity
                new_entity = EnhancedEntity(
                    id=entity_id,
                    name=entity_data.get("name", ""),
                    type=entity_data.get("type", ""),
                    attributes=entity_data.get("attributes", {}),
                    status=EntityStatus(entity_data.get("status", "pending")),
                    confidence=entity_data.get("confidence", 0.0),
                    source_text=entity_data.get("source_text")
                )

                session.add_entity(new_entity, user)
                imported_entities += 1

            except Exception as e:
                logger.error(f"Error importing entity {entity_data.get('name', 'unknown')}: {e}")
                skipped_items += 1

        # Import relationships
        for rel_data in relationships:
            try:
                rel_id = rel_data.get("id", str(uuid.uuid4()))

                # Check if relationship already exists
                existing_rel = session.get_relationship_by_id(rel_id)
                if existing_rel:
                    if merge_strategy == "skip":
                        skipped_items += 1
                        conflicts.append({
                            "type": "relationship",
                            "id": rel_id,
                            "action": "skipped",
                            "reason": "Already exists"
                        })
                        continue
                    elif merge_strategy == "update":
                        existing_rel.update_attributes(rel_data.get("attributes", {}), user, "Updated via import")
                        conflicts.append({
                            "type": "relationship",
                            "id": rel_id,
                            "action": "updated",
                            "reason": "Merged with existing"
                        })
                        continue

                # Create new relationship
                new_relationship = EnhancedRelationship(
                    id=rel_id,
                    source_entity_id=rel_data.get("source_entity_id", ""),
                    target_entity_id=rel_data.get("target_entity_id", ""),
                    relationship_type=rel_data.get("relationship_type", ""),
                    attributes=rel_data.get("attributes", {}),
                    status=EntityStatus(rel_data.get("status", "pending")),
                    confidence=rel_data.get("confidence", 0.0)
                )

                session.add_relationship(new_relationship, user)
                imported_relationships += 1

            except Exception as e:
                logger.error(f"Error importing relationship {rel_data.get('id', 'unknown')}: {e}")
                skipped_items += 1

        # Save updated session
        await self._save_session(session)

        return {
            "success": True,
            "imported_entities": imported_entities,
            "imported_relationships": imported_relationships,
            "skipped_items": skipped_items,
            "conflicts": conflicts
        }

    # Helper methods

    async def _load_session(self, session_id: str) -> Optional[EnhancedStagingSession]:
        """Load a specific session."""
        session_file = self.staging_dir / f"{session_id}.json"
        if not session_file.exists():
            return None

        try:
            with open(session_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
            return EnhancedStagingSession.from_dict(session_data)
        except Exception as e:
            logger.error(f"Error loading session {session_id}: {e}")
            return None

    async def _save_session(self, session: EnhancedStagingSession) -> bool:
        """Save a session."""
        try:
            session.updated_at = datetime.now().isoformat()
            session.update_statistics()

            session_file = self.staging_dir / f"{session.session_id}.json"
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(session.to_dict(), f, indent=2, ensure_ascii=False)

            return True
        except Exception as e:
            logger.error(f"Error saving session {session.session_id}: {e}")
            return False


# Global service instance
export_import_service = ExportImportService()
