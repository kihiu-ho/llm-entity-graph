#!/usr/bin/env python3
"""
Staging manager for entity and relationship review before Graphiti ingestion.
"""

import json
import os
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class StagingManager:
    """Manages staging of extracted entities and relationships for review."""
    
    def __init__(self, staging_dir: str = "staging/data"):
        """Initialize staging manager."""
        self.staging_dir = Path(staging_dir)
        self.staging_dir.mkdir(parents=True, exist_ok=True)
        
    def create_staging_session(self, document_title: str, document_source: str = None) -> str:
        """
        Create a new staging session for a document.
        
        Args:
            document_title: Title of the document
            document_source: Source of the document
            
        Returns:
            Session ID
        """
        session_id = str(uuid.uuid4())
        session_data = {
            "session_id": session_id,
            "document_title": document_title,
            "document_source": document_source,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "status": "pending_review",
            "entities": [],
            "relationships": [],
            "statistics": {
                "total_entities": 0,
                "total_relationships": 0,
                "approved_entities": 0,
                "approved_relationships": 0,
                "rejected_entities": 0,
                "rejected_relationships": 0
            }
        }
        
        session_file = self.staging_dir / f"{session_id}.json"
        with open(session_file, 'w') as f:
            json.dump(session_data, f, indent=2)
            
        logger.info(f"Created staging session: {session_id} for document: {document_title}")
        return session_id
    
    def add_entity_to_staging(self, session_id: str, entity_data: Dict[str, Any]) -> str:
        """
        Add an extracted entity to staging for review.
        
        Args:
            session_id: Staging session ID
            entity_data: Entity data dictionary
            
        Returns:
            Entity ID
        """
        entity_id = str(uuid.uuid4())
        entity = {
            "id": entity_id,
            "name": entity_data.get("name", ""),
            "type": entity_data.get("type", "Entity"),
            "attributes": entity_data.get("attributes", {}),
            "confidence": entity_data.get("confidence", 1.0),
            "status": "pending",
            "edited": False,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "source_text": entity_data.get("source_text", "")
        }
        
        session_data = self.load_session(session_id)
        session_data["entities"].append(entity)
        session_data["statistics"]["total_entities"] += 1
        self.save_session(session_id, session_data)
        
        return entity_id
    
    def add_relationship_to_staging(self, session_id: str, relationship_data: Dict[str, Any]) -> str:
        """
        Add an extracted relationship to staging for review.
        
        Args:
            session_id: Staging session ID
            relationship_data: Relationship data dictionary
            
        Returns:
            Relationship ID
        """
        relationship_id = str(uuid.uuid4())
        relationship = {
            "id": relationship_id,
            "source": relationship_data.get("source", ""),
            "target": relationship_data.get("target", ""),
            "type": relationship_data.get("type", "RELATES_TO"),
            "attributes": relationship_data.get("attributes", {}),
            "confidence": relationship_data.get("confidence", 1.0),
            "status": "pending",
            "edited": False,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "source_text": relationship_data.get("source_text", "")
        }
        
        session_data = self.load_session(session_id)
        session_data["relationships"].append(relationship)
        session_data["statistics"]["total_relationships"] += 1
        self.save_session(session_id, session_data)
        
        return relationship_id
    
    def load_session(self, session_id: str) -> Dict[str, Any]:
        """Load staging session data."""
        session_file = self.staging_dir / f"{session_id}.json"
        if not session_file.exists():
            raise FileNotFoundError(f"Staging session not found: {session_id}")
            
        with open(session_file, 'r') as f:
            return json.load(f)
    
    def save_session(self, session_id: str, session_data: Dict[str, Any]):
        """Save staging session data."""
        session_file = self.staging_dir / f"{session_id}.json"
        with open(session_file, 'w') as f:
            json.dump(session_data, f, indent=2)
    
    def list_sessions(self) -> List[Dict[str, Any]]:
        """List all staging sessions."""
        sessions = []
        for session_file in self.staging_dir.glob("*.json"):
            try:
                with open(session_file, 'r') as f:
                    session_data = json.load(f)
                    sessions.append({
                        "session_id": session_data["session_id"],
                        "document_title": session_data["document_title"],
                        "created_at": session_data["created_at"],
                        "status": session_data["status"],
                        "statistics": session_data["statistics"]
                    })
            except Exception as e:
                logger.warning(f"Failed to load session {session_file}: {e}")
        
        # Sort by creation date (newest first)
        sessions.sort(key=lambda x: x["created_at"], reverse=True)
        return sessions
    
    def update_entity_status(self, session_id: str, entity_id: str, status: str, 
                           updated_data: Dict[str, Any] = None):
        """Update entity status and optionally edit data."""
        session_data = self.load_session(session_id)
        
        for entity in session_data["entities"]:
            if entity["id"] == entity_id:
                old_status = entity["status"]
                entity["status"] = status
                entity["updated_at"] = datetime.now(timezone.utc).isoformat()
                
                if updated_data:
                    entity.update(updated_data)
                    entity["edited"] = True
                
                # Update statistics
                self._update_entity_statistics(session_data, old_status, status)
                break
        
        self.save_session(session_id, session_data)
    
    def update_relationship_status(self, session_id: str, relationship_id: str, status: str,
                                 updated_data: Dict[str, Any] = None):
        """Update relationship status and optionally edit data."""
        session_data = self.load_session(session_id)
        
        for relationship in session_data["relationships"]:
            if relationship["id"] == relationship_id:
                old_status = relationship["status"]
                relationship["status"] = status
                relationship["updated_at"] = datetime.now(timezone.utc).isoformat()
                
                if updated_data:
                    relationship.update(updated_data)
                    relationship["edited"] = True
                
                # Update statistics
                self._update_relationship_statistics(session_data, old_status, status)
                break
        
        self.save_session(session_id, session_data)
    
    def _update_entity_statistics(self, session_data: Dict[str, Any], old_status: str, new_status: str):
        """Update entity statistics when status changes."""
        stats = session_data["statistics"]
        
        # Remove from old status count
        if old_status == "approved":
            stats["approved_entities"] -= 1
        elif old_status == "rejected":
            stats["rejected_entities"] -= 1
            
        # Add to new status count
        if new_status == "approved":
            stats["approved_entities"] += 1
        elif new_status == "rejected":
            stats["rejected_entities"] += 1
    
    def _update_relationship_statistics(self, session_data: Dict[str, Any], old_status: str, new_status: str):
        """Update relationship statistics when status changes."""
        stats = session_data["statistics"]
        
        # Remove from old status count
        if old_status == "approved":
            stats["approved_relationships"] -= 1
        elif old_status == "rejected":
            stats["rejected_relationships"] -= 1
            
        # Add to new status count
        if new_status == "approved":
            stats["approved_relationships"] += 1
        elif new_status == "rejected":
            stats["rejected_relationships"] += 1
    
    def get_approved_items(self, session_id: str) -> Dict[str, List[Dict[str, Any]]]:
        """Get all approved entities and relationships for ingestion."""
        session_data = self.load_session(session_id)
        
        approved_entities = [e for e in session_data["entities"] if e["status"] == "approved"]
        approved_relationships = [r for r in session_data["relationships"] if r["status"] == "approved"]
        
        return {
            "entities": approved_entities,
            "relationships": approved_relationships
        }
    
    def mark_session_ingested(self, session_id: str):
        """Mark a session as ingested to Graphiti."""
        session_data = self.load_session(session_id)
        session_data["status"] = "ingested"
        session_data["ingested_at"] = datetime.now(timezone.utc).isoformat()
        self.save_session(session_id, session_data)
    
    def delete_session(self, session_id: str):
        """Delete a staging session."""
        session_file = self.staging_dir / f"{session_id}.json"
        if session_file.exists():
            session_file.unlink()
            logger.info(f"Deleted staging session: {session_id}")


# Global staging manager instance
staging_manager = StagingManager()
