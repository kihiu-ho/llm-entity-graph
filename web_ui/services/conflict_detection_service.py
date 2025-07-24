"""
Conflict detection service for entity management system.
Identifies potential conflicts, duplicates, and inconsistencies in entity data.
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Set
from collections import defaultdict
import difflib
import re

from ..models.enhanced_staging_models import (
    EnhancedStagingSession, EnhancedEntity, EnhancedRelationship,
    EntityStatus, ValidationResult
)

logger = logging.getLogger(__name__)


class ConflictDetectionService:
    """Service for detecting conflicts and inconsistencies in entity data."""
    
    def __init__(self, staging_dir: str = "staging/data"):
        self.staging_dir = Path(staging_dir)
        self.staging_dir.mkdir(parents=True, exist_ok=True)
        self._initialized = False
        
        # Configuration for conflict detection
        self.similarity_threshold = 0.8  # Threshold for name similarity
        self.confidence_threshold = 0.5  # Threshold for low confidence warnings
        
        # Common entity type mappings for normalization
        self.entity_type_aliases = {
            "person": ["person", "individual", "people", "human"],
            "company": ["company", "corporation", "business", "organization", "org", "firm"],
            "location": ["location", "place", "address", "city", "country"],
            "technology": ["technology", "tech", "software", "system", "platform"]
        }
    
    async def initialize(self):
        """Initialize the conflict detection service."""
        if not self._initialized:
            logger.info("Initializing Conflict Detection Service")
            self._initialized = True
    
    async def detect_session_conflicts(self, session_id: str) -> Dict[str, Any]:
        """Detect all types of conflicts in a session."""
        if not self._initialized:
            await self.initialize()
        
        try:
            session = await self._load_session(session_id)
            if not session:
                return {"success": False, "error": "Session not found"}
            
            conflicts = {
                "duplicate_entities": await self._detect_duplicate_entities(session),
                "similar_entities": await self._detect_similar_entities(session),
                "invalid_relationships": await self._detect_invalid_relationships(session),
                "circular_relationships": await self._detect_circular_relationships(session),
                "orphaned_relationships": await self._detect_orphaned_relationships(session),
                "low_confidence_items": await self._detect_low_confidence_items(session),
                "inconsistent_types": await self._detect_inconsistent_types(session),
                "missing_required_fields": await self._detect_missing_fields(session)
            }
            
            # Calculate conflict summary
            total_conflicts = sum(len(conflict_list) for conflict_list in conflicts.values())
            severity_counts = self._calculate_severity_counts(conflicts)
            
            return {
                "success": True,
                "session_id": session_id,
                "total_conflicts": total_conflicts,
                "severity_counts": severity_counts,
                "conflicts": conflicts,
                "recommendations": await self._generate_recommendations(conflicts)
            }
            
        except Exception as e:
            logger.error(f"Error detecting conflicts in session {session_id}: {e}")
            return {"success": False, "error": str(e)}
    
    async def detect_cross_session_conflicts(self, session_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """Detect conflicts across multiple sessions."""
        if not self._initialized:
            await self.initialize()
        
        try:
            if session_ids is None:
                # Load all sessions
                sessions = await self._load_all_sessions()
            else:
                sessions = []
                for session_id in session_ids:
                    session = await self._load_session(session_id)
                    if session:
                        sessions.append(session)
            
            if not sessions:
                return {"success": False, "error": "No sessions found"}
            
            conflicts = {
                "cross_session_duplicates": await self._detect_cross_session_duplicates(sessions),
                "conflicting_entity_types": await self._detect_conflicting_entity_types(sessions),
                "inconsistent_relationships": await self._detect_inconsistent_relationships(sessions)
            }
            
            total_conflicts = sum(len(conflict_list) for conflict_list in conflicts.values())
            
            return {
                "success": True,
                "sessions_analyzed": len(sessions),
                "total_conflicts": total_conflicts,
                "conflicts": conflicts,
                "recommendations": await self._generate_cross_session_recommendations(conflicts)
            }
            
        except Exception as e:
            logger.error(f"Error detecting cross-session conflicts: {e}")
            return {"success": False, "error": str(e)}
    
    async def resolve_conflict(self, session_id: str, conflict_id: str, 
                             resolution_action: str, user: str = "system") -> Dict[str, Any]:
        """Resolve a specific conflict with the given action."""
        if not self._initialized:
            await self.initialize()
        
        try:
            session = await self._load_session(session_id)
            if not session:
                return {"success": False, "error": "Session not found"}
            
            # Find the conflict
            conflicts = await self.detect_session_conflicts(session_id)
            if not conflicts["success"]:
                return conflicts
            
            conflict_item = None
            conflict_type = None
            
            # Search for the conflict in all conflict types
            for c_type, c_list in conflicts["conflicts"].items():
                for conflict in c_list:
                    if conflict.get("id") == conflict_id:
                        conflict_item = conflict
                        conflict_type = c_type
                        break
                if conflict_item:
                    break
            
            if not conflict_item:
                return {"success": False, "error": "Conflict not found"}
            
            # Apply resolution based on conflict type and action
            resolution_result = await self._apply_conflict_resolution(
                session, conflict_item, conflict_type, resolution_action, user
            )
            
            if resolution_result["success"]:
                # Save updated session
                await self._save_session(session)
            
            return resolution_result
            
        except Exception as e:
            logger.error(f"Error resolving conflict {conflict_id}: {e}")
            return {"success": False, "error": str(e)}
    
    # Private conflict detection methods
    
    async def _detect_duplicate_entities(self, session: EnhancedStagingSession) -> List[Dict[str, Any]]:
        """Detect exact duplicate entities."""
        duplicates = []
        seen_entities = {}
        
        for entity in session.entities:
            # Create a key based on name and type (case-insensitive)
            key = (entity.name.lower().strip(), entity.type.lower().strip())
            
            if key in seen_entities:
                duplicates.append({
                    "id": f"dup_{entity.id}_{seen_entities[key].id}",
                    "type": "exact_duplicate",
                    "severity": "high",
                    "entity1": {
                        "id": entity.id,
                        "name": entity.name,
                        "type": entity.type,
                        "confidence": entity.confidence
                    },
                    "entity2": {
                        "id": seen_entities[key].id,
                        "name": seen_entities[key].name,
                        "type": seen_entities[key].type,
                        "confidence": seen_entities[key].confidence
                    },
                    "description": f"Exact duplicate: '{entity.name}' ({entity.type})",
                    "suggested_actions": ["merge", "delete_duplicate", "mark_as_different"]
                })
            else:
                seen_entities[key] = entity
        
        return duplicates
    
    async def _detect_similar_entities(self, session: EnhancedStagingSession) -> List[Dict[str, Any]]:
        """Detect similar entities that might be duplicates."""
        similar_entities = []
        entities = session.entities
        
        for i, entity1 in enumerate(entities):
            for entity2 in entities[i+1:]:
                # Skip if same entity or different types
                if entity1.id == entity2.id or entity1.type.lower() != entity2.type.lower():
                    continue
                
                # Calculate name similarity
                similarity = difflib.SequenceMatcher(None, entity1.name.lower(), entity2.name.lower()).ratio()
                
                if similarity >= self.similarity_threshold:
                    similar_entities.append({
                        "id": f"sim_{entity1.id}_{entity2.id}",
                        "type": "similar_entities",
                        "severity": "medium",
                        "similarity_score": round(similarity, 3),
                        "entity1": {
                            "id": entity1.id,
                            "name": entity1.name,
                            "type": entity1.type,
                            "confidence": entity1.confidence
                        },
                        "entity2": {
                            "id": entity2.id,
                            "name": entity2.name,
                            "type": entity2.type,
                            "confidence": entity2.confidence
                        },
                        "description": f"Similar entities: '{entity1.name}' and '{entity2.name}' ({similarity:.1%} similar)",
                        "suggested_actions": ["merge", "mark_as_different", "review_manually"]
                    })
        
        return similar_entities
    
    async def _detect_invalid_relationships(self, session: EnhancedStagingSession) -> List[Dict[str, Any]]:
        """Detect relationships with invalid entity references."""
        invalid_relationships = []
        entity_ids = {entity.id for entity in session.entities}
        
        for relationship in session.relationships:
            issues = []
            
            if relationship.source_entity_id not in entity_ids:
                issues.append(f"Source entity '{relationship.source_entity_id}' not found")
            
            if relationship.target_entity_id not in entity_ids:
                issues.append(f"Target entity '{relationship.target_entity_id}' not found")
            
            if relationship.source_entity_id == relationship.target_entity_id:
                issues.append("Self-referencing relationship")
            
            if issues:
                invalid_relationships.append({
                    "id": f"inv_{relationship.id}",
                    "type": "invalid_relationship",
                    "severity": "high",
                    "relationship_id": relationship.id,
                    "relationship_type": relationship.relationship_type,
                    "source_entity_id": relationship.source_entity_id,
                    "target_entity_id": relationship.target_entity_id,
                    "issues": issues,
                    "description": f"Invalid relationship: {', '.join(issues)}",
                    "suggested_actions": ["delete", "fix_references", "review_manually"]
                })
        
        return invalid_relationships
    
    async def _detect_circular_relationships(self, session: EnhancedStagingSession) -> List[Dict[str, Any]]:
        """Detect circular relationships that might indicate logical issues."""
        circular_relationships = []
        
        # Build relationship graph
        graph = defaultdict(list)
        for rel in session.relationships:
            graph[rel.source_entity_id].append((rel.target_entity_id, rel.id, rel.relationship_type))
        
        # Find cycles using DFS
        visited = set()
        rec_stack = set()
        
        def has_cycle(node, path):
            if node in rec_stack:
                # Found a cycle, extract it
                cycle_start = path.index(node)
                cycle = path[cycle_start:] + [node]
                return cycle
            
            if node in visited:
                return None
            
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor, rel_id, rel_type in graph[node]:
                cycle = has_cycle(neighbor, path + [node])
                if cycle:
                    return cycle
            
            rec_stack.remove(node)
            return None
        
        # Check for cycles from each node
        for entity in session.entities:
            if entity.id not in visited:
                cycle = has_cycle(entity.id, [])
                if cycle:
                    # Get entity names for the cycle
                    entity_map = {e.id: e.name for e in session.entities}
                    cycle_names = [entity_map.get(eid, eid) for eid in cycle]
                    
                    circular_relationships.append({
                        "id": f"circ_{'_'.join(cycle[:3])}",  # Use first 3 entities for ID
                        "type": "circular_relationship",
                        "severity": "medium",
                        "cycle": cycle,
                        "cycle_names": cycle_names,
                        "description": f"Circular relationship detected: {' → '.join(cycle_names)}",
                        "suggested_actions": ["review_logic", "break_cycle", "mark_as_valid"]
                    })
        
        return circular_relationships
    
    async def _detect_orphaned_relationships(self, session: EnhancedStagingSession) -> List[Dict[str, Any]]:
        """Detect relationships that reference non-existent entities."""
        orphaned_relationships = []
        entity_ids = {entity.id for entity in session.entities}
        
        for relationship in session.relationships:
            orphaned_entities = []
            
            if relationship.source_entity_id not in entity_ids:
                orphaned_entities.append(relationship.source_entity_id)
            
            if relationship.target_entity_id not in entity_ids:
                orphaned_entities.append(relationship.target_entity_id)
            
            if orphaned_entities:
                orphaned_relationships.append({
                    "id": f"orph_{relationship.id}",
                    "type": "orphaned_relationship",
                    "severity": "high",
                    "relationship_id": relationship.id,
                    "relationship_type": relationship.relationship_type,
                    "orphaned_entities": orphaned_entities,
                    "description": f"Orphaned relationship: references missing entities {orphaned_entities}",
                    "suggested_actions": ["delete", "create_missing_entities", "fix_references"]
                })
        
        return orphaned_relationships
    
    async def _detect_low_confidence_items(self, session: EnhancedStagingSession) -> List[Dict[str, Any]]:
        """Detect entities and relationships with low confidence scores."""
        low_confidence_items = []
        
        # Check entities
        for entity in session.entities:
            if entity.confidence < self.confidence_threshold:
                low_confidence_items.append({
                    "id": f"lowconf_entity_{entity.id}",
                    "type": "low_confidence_entity",
                    "severity": "low",
                    "item_type": "entity",
                    "item_id": entity.id,
                    "item_name": entity.name,
                    "confidence": entity.confidence,
                    "description": f"Low confidence entity: '{entity.name}' ({entity.confidence:.2f})",
                    "suggested_actions": ["review_manually", "improve_extraction", "accept_as_is"]
                })
        
        # Check relationships
        for relationship in session.relationships:
            if relationship.confidence < self.confidence_threshold:
                low_confidence_items.append({
                    "id": f"lowconf_rel_{relationship.id}",
                    "type": "low_confidence_relationship",
                    "severity": "low",
                    "item_type": "relationship",
                    "item_id": relationship.id,
                    "relationship_type": relationship.relationship_type,
                    "confidence": relationship.confidence,
                    "description": f"Low confidence relationship: {relationship.relationship_type} ({relationship.confidence:.2f})",
                    "suggested_actions": ["review_manually", "improve_extraction", "accept_as_is"]
                })
        
        return low_confidence_items
    
    async def _detect_inconsistent_types(self, session: EnhancedStagingSession) -> List[Dict[str, Any]]:
        """Detect entities with potentially inconsistent types."""
        inconsistent_types = []
        
        # Group entities by normalized name
        name_groups = defaultdict(list)
        for entity in session.entities:
            normalized_name = entity.name.lower().strip()
            name_groups[normalized_name].append(entity)
        
        # Check for entities with same name but different types
        for name, entities in name_groups.items():
            if len(entities) > 1:
                types = {entity.type for entity in entities}
                if len(types) > 1:
                    inconsistent_types.append({
                        "id": f"inconsist_{hash(name) % 10000}",
                        "type": "inconsistent_entity_types",
                        "severity": "medium",
                        "entity_name": name,
                        "entities": [
                            {
                                "id": entity.id,
                                "name": entity.name,
                                "type": entity.type,
                                "confidence": entity.confidence
                            }
                            for entity in entities
                        ],
                        "conflicting_types": list(types),
                        "description": f"Inconsistent types for '{name}': {', '.join(types)}",
                        "suggested_actions": ["standardize_type", "split_entities", "review_manually"]
                    })
        
        return inconsistent_types
    
    async def _detect_missing_fields(self, session: EnhancedStagingSession) -> List[Dict[str, Any]]:
        """Detect entities and relationships with missing required fields."""
        missing_fields = []
        
        # Check entities
        for entity in session.entities:
            missing = []
            if not entity.name or entity.name.strip() == "":
                missing.append("name")
            if not entity.type or entity.type.strip() == "":
                missing.append("type")
            
            if missing:
                missing_fields.append({
                    "id": f"missing_entity_{entity.id}",
                    "type": "missing_required_fields",
                    "severity": "high",
                    "item_type": "entity",
                    "item_id": entity.id,
                    "missing_fields": missing,
                    "description": f"Entity missing required fields: {', '.join(missing)}",
                    "suggested_actions": ["add_missing_fields", "delete", "review_manually"]
                })
        
        # Check relationships
        for relationship in session.relationships:
            missing = []
            if not relationship.source_entity_id:
                missing.append("source_entity_id")
            if not relationship.target_entity_id:
                missing.append("target_entity_id")
            if not relationship.relationship_type:
                missing.append("relationship_type")
            
            if missing:
                missing_fields.append({
                    "id": f"missing_rel_{relationship.id}",
                    "type": "missing_required_fields",
                    "severity": "high",
                    "item_type": "relationship",
                    "item_id": relationship.id,
                    "missing_fields": missing,
                    "description": f"Relationship missing required fields: {', '.join(missing)}",
                    "suggested_actions": ["add_missing_fields", "delete", "review_manually"]
                })
        
        return missing_fields

    # Cross-session conflict detection methods

    async def _detect_cross_session_duplicates(self, sessions: List[EnhancedStagingSession]) -> List[Dict[str, Any]]:
        """Detect duplicate entities across multiple sessions."""
        cross_duplicates = []
        all_entities = []

        # Collect all entities with session info
        for session in sessions:
            for entity in session.entities:
                all_entities.append({
                    "entity": entity,
                    "session_id": session.session_id,
                    "session_title": session.document_title
                })

        # Find duplicates
        seen_entities = {}
        for item in all_entities:
            entity = item["entity"]
            key = (entity.name.lower().strip(), entity.type.lower().strip())

            if key in seen_entities:
                cross_duplicates.append({
                    "id": f"cross_dup_{entity.id}_{seen_entities[key]['entity'].id}",
                    "type": "cross_session_duplicate",
                    "severity": "medium",
                    "entity1": {
                        "id": entity.id,
                        "name": entity.name,
                        "type": entity.type,
                        "session_id": item["session_id"],
                        "session_title": item["session_title"]
                    },
                    "entity2": {
                        "id": seen_entities[key]["entity"].id,
                        "name": seen_entities[key]["entity"].name,
                        "type": seen_entities[key]["entity"].type,
                        "session_id": seen_entities[key]["session_id"],
                        "session_title": seen_entities[key]["session_title"]
                    },
                    "description": f"Cross-session duplicate: '{entity.name}' appears in multiple sessions",
                    "suggested_actions": ["merge_sessions", "mark_as_different", "create_global_entity"]
                })
            else:
                seen_entities[key] = item

        return cross_duplicates

    async def _detect_conflicting_entity_types(self, sessions: List[EnhancedStagingSession]) -> List[Dict[str, Any]]:
        """Detect entities with same name but different types across sessions."""
        conflicting_types = []
        entity_types = defaultdict(set)
        entity_sessions = defaultdict(list)

        # Collect entity types across sessions
        for session in sessions:
            for entity in session.entities:
                name_key = entity.name.lower().strip()
                entity_types[name_key].add(entity.type.lower())
                entity_sessions[name_key].append({
                    "entity": entity,
                    "session_id": session.session_id,
                    "session_title": session.document_title
                })

        # Find conflicts
        for name, types in entity_types.items():
            if len(types) > 1:
                conflicting_types.append({
                    "id": f"cross_type_{hash(name) % 10000}",
                    "type": "cross_session_type_conflict",
                    "severity": "medium",
                    "entity_name": name,
                    "conflicting_types": list(types),
                    "sessions": [
                        {
                            "session_id": item["session_id"],
                            "session_title": item["session_title"],
                            "entity_type": item["entity"].type
                        }
                        for item in entity_sessions[name]
                    ],
                    "description": f"Entity '{name}' has conflicting types across sessions: {', '.join(types)}",
                    "suggested_actions": ["standardize_type", "review_context", "split_by_context"]
                })

        return conflicting_types

    async def _detect_inconsistent_relationships(self, sessions: List[EnhancedStagingSession]) -> List[Dict[str, Any]]:
        """Detect inconsistent relationships across sessions."""
        inconsistent_relationships = []
        relationship_patterns = defaultdict(set)

        # Collect relationship patterns
        for session in sessions:
            for rel in session.relationships:
                # Get entity names for pattern matching
                source_entity = session.get_entity_by_id(rel.source_entity_id)
                target_entity = session.get_entity_by_id(rel.target_entity_id)

                if source_entity and target_entity:
                    pattern_key = (
                        source_entity.name.lower().strip(),
                        target_entity.name.lower().strip()
                    )
                    relationship_patterns[pattern_key].add(rel.relationship_type.lower())

        # Find inconsistencies
        for (source_name, target_name), rel_types in relationship_patterns.items():
            if len(rel_types) > 1:
                inconsistent_relationships.append({
                    "id": f"cross_rel_{hash((source_name, target_name)) % 10000}",
                    "type": "cross_session_relationship_conflict",
                    "severity": "low",
                    "source_entity": source_name,
                    "target_entity": target_name,
                    "conflicting_types": list(rel_types),
                    "description": f"Inconsistent relationship types between '{source_name}' and '{target_name}': {', '.join(rel_types)}",
                    "suggested_actions": ["standardize_relationship", "review_context", "accept_multiple"]
                })

        return inconsistent_relationships

    # Helper methods

    def _calculate_severity_counts(self, conflicts: Dict[str, List[Dict[str, Any]]]) -> Dict[str, int]:
        """Calculate counts by severity level."""
        severity_counts = {"high": 0, "medium": 0, "low": 0}

        for conflict_list in conflicts.values():
            for conflict in conflict_list:
                severity = conflict.get("severity", "low")
                severity_counts[severity] += 1

        return severity_counts

    async def _generate_recommendations(self, conflicts: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """Generate recommendations based on detected conflicts."""
        recommendations = []

        # High priority recommendations
        if conflicts["duplicate_entities"]:
            recommendations.append({
                "priority": "high",
                "title": "Resolve Duplicate Entities",
                "description": f"Found {len(conflicts['duplicate_entities'])} exact duplicate entities",
                "action": "Review and merge duplicate entities to improve data quality",
                "conflict_type": "duplicate_entities"
            })

        if conflicts["invalid_relationships"]:
            recommendations.append({
                "priority": "high",
                "title": "Fix Invalid Relationships",
                "description": f"Found {len(conflicts['invalid_relationships'])} invalid relationships",
                "action": "Delete or fix relationships with missing entity references",
                "conflict_type": "invalid_relationships"
            })

        # Medium priority recommendations
        if conflicts["similar_entities"]:
            recommendations.append({
                "priority": "medium",
                "title": "Review Similar Entities",
                "description": f"Found {len(conflicts['similar_entities'])} potentially similar entities",
                "action": "Review similar entities to determine if they should be merged",
                "conflict_type": "similar_entities"
            })

        if conflicts["inconsistent_types"]:
            recommendations.append({
                "priority": "medium",
                "title": "Standardize Entity Types",
                "description": f"Found {len(conflicts['inconsistent_types'])} entities with inconsistent types",
                "action": "Standardize entity types for consistency",
                "conflict_type": "inconsistent_types"
            })

        # Low priority recommendations
        if conflicts["low_confidence_items"]:
            recommendations.append({
                "priority": "low",
                "title": "Review Low Confidence Items",
                "description": f"Found {len(conflicts['low_confidence_items'])} items with low confidence scores",
                "action": "Review and validate low confidence entities and relationships",
                "conflict_type": "low_confidence_items"
            })

        return recommendations

    async def _generate_cross_session_recommendations(self, conflicts: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """Generate recommendations for cross-session conflicts."""
        recommendations = []

        if conflicts["cross_session_duplicates"]:
            recommendations.append({
                "priority": "medium",
                "title": "Resolve Cross-Session Duplicates",
                "description": f"Found {len(conflicts['cross_session_duplicates'])} entities duplicated across sessions",
                "action": "Consider creating global entities or merging related sessions",
                "conflict_type": "cross_session_duplicates"
            })

        if conflicts["conflicting_entity_types"]:
            recommendations.append({
                "priority": "medium",
                "title": "Standardize Entity Types Globally",
                "description": f"Found {len(conflicts['conflicting_entity_types'])} entities with conflicting types across sessions",
                "action": "Establish consistent entity type standards across all sessions",
                "conflict_type": "conflicting_entity_types"
            })

        return recommendations

    async def _apply_conflict_resolution(self, session: EnhancedStagingSession, conflict: Dict[str, Any],
                                       conflict_type: str, action: str, user: str) -> Dict[str, Any]:
        """Apply a specific resolution action to a conflict."""
        try:
            if conflict_type == "duplicate_entities" and action == "merge":
                return await self._merge_duplicate_entities(session, conflict, user)
            elif conflict_type == "duplicate_entities" and action == "delete_duplicate":
                return await self._delete_duplicate_entity(session, conflict, user)
            elif conflict_type == "invalid_relationships" and action == "delete":
                return await self._delete_invalid_relationship(session, conflict, user)
            elif action == "mark_as_resolved":
                return await self._mark_conflict_as_resolved(session, conflict, user)
            else:
                return {"success": False, "error": f"Unsupported resolution action: {action}"}

        except Exception as e:
            logger.error(f"Error applying conflict resolution: {e}")
            return {"success": False, "error": str(e)}

    async def _merge_duplicate_entities(self, session: EnhancedStagingSession,
                                      conflict: Dict[str, Any], user: str) -> Dict[str, Any]:
        """Merge duplicate entities."""
        entity1_id = conflict["entity1"]["id"]
        entity2_id = conflict["entity2"]["id"]

        entity1 = session.get_entity_by_id(entity1_id)
        entity2 = session.get_entity_by_id(entity2_id)

        if not entity1 or not entity2:
            return {"success": False, "error": "One or both entities not found"}

        # Keep the entity with higher confidence
        keep_entity = entity1 if entity1.confidence >= entity2.confidence else entity2
        remove_entity = entity2 if keep_entity == entity1 else entity1

        # Merge attributes
        merged_attributes = keep_entity.attributes.copy()
        merged_attributes.update(remove_entity.attributes)

        # Update the kept entity
        keep_entity.update_attributes(merged_attributes, user, f"Merged with entity {remove_entity.id}")

        # Update relationships to point to the kept entity
        for rel in session.relationships:
            if rel.source_entity_id == remove_entity.id:
                rel.source_entity_id = keep_entity.id
                rel.add_audit_entry(user, "updated", {"source_entity_id": keep_entity.id}, "Updated due to entity merge")
            if rel.target_entity_id == remove_entity.id:
                rel.target_entity_id = keep_entity.id
                rel.add_audit_entry(user, "updated", {"target_entity_id": keep_entity.id}, "Updated due to entity merge")

        # Remove the duplicate entity
        session.remove_entity(remove_entity.id, user)

        return {
            "success": True,
            "action": "merged",
            "kept_entity_id": keep_entity.id,
            "removed_entity_id": remove_entity.id,
            "message": f"Successfully merged entities {entity1_id} and {entity2_id}"
        }

    async def _delete_duplicate_entity(self, session: EnhancedStagingSession,
                                     conflict: Dict[str, Any], user: str) -> Dict[str, Any]:
        """Delete one of the duplicate entities."""
        entity1_id = conflict["entity1"]["id"]
        entity2_id = conflict["entity2"]["id"]

        # Delete the entity with lower confidence
        entity1 = session.get_entity_by_id(entity1_id)
        entity2 = session.get_entity_by_id(entity2_id)

        if not entity1 or not entity2:
            return {"success": False, "error": "One or both entities not found"}

        remove_entity = entity1 if entity1.confidence < entity2.confidence else entity2
        session.remove_entity(remove_entity.id, user)

        return {
            "success": True,
            "action": "deleted",
            "deleted_entity_id": remove_entity.id,
            "message": f"Successfully deleted duplicate entity {remove_entity.id}"
        }

    async def _delete_invalid_relationship(self, session: EnhancedStagingSession,
                                         conflict: Dict[str, Any], user: str) -> Dict[str, Any]:
        """Delete an invalid relationship."""
        relationship_id = conflict["relationship_id"]
        session.remove_relationship(relationship_id, user)

        return {
            "success": True,
            "action": "deleted",
            "deleted_relationship_id": relationship_id,
            "message": f"Successfully deleted invalid relationship {relationship_id}"
        }

    async def _mark_conflict_as_resolved(self, session: EnhancedStagingSession,
                                       conflict: Dict[str, Any], user: str) -> Dict[str, Any]:
        """Mark a conflict as resolved without taking action."""
        session.add_audit_entry(user, "conflict_resolved", {
            "conflict_id": conflict["id"],
            "conflict_type": conflict["type"],
            "resolution": "marked_as_resolved"
        }, "Conflict marked as resolved by user")

        return {
            "success": True,
            "action": "marked_resolved",
            "conflict_id": conflict["id"],
            "message": f"Conflict {conflict['id']} marked as resolved"
        }

    # Helper methods for loading/saving sessions

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

    async def _load_all_sessions(self) -> List[EnhancedStagingSession]:
        """Load all staging sessions."""
        sessions = []
        for session_file in self.staging_dir.glob("*.json"):
            try:
                with open(session_file, 'r', encoding='utf-8') as f:
                    session_data = json.load(f)
                sessions.append(EnhancedStagingSession.from_dict(session_data))
            except Exception as e:
                logger.error(f"Error loading session file {session_file}: {e}")
        return sessions

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
conflict_detection_service = ConflictDetectionService()
