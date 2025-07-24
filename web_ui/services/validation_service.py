"""
Enhanced validation service for entity and relationship data.
Provides real-time validation, conflict detection, data quality checks, and validation rules.
"""

import re
import json
from datetime import datetime
from typing import Dict, List, Optional, Any, Set, Tuple
from difflib import SequenceMatcher
import logging

from ..models.enhanced_staging_models import (
    EnhancedEntity, EnhancedRelationship, EnhancedStagingSession,
    ValidationResult, EntityStatus
)

logger = logging.getLogger(__name__)


class ValidationService:
    """Advanced validation service with conflict detection and data quality checks."""
    
    def __init__(self):
        self.entity_type_patterns = {
            'Person': [
                r'\b[A-Z][a-z]+ [A-Z][a-z]+\b',  # First Last
                r'\b[A-Z][a-z]+ [A-Z]\. [A-Z][a-z]+\b',  # First M. Last
                r'\b[A-Z][a-z]+ [A-Z][a-z]+ [A-Z][a-z]+\b'  # First Middle Last
            ],
            'Company': [
                r'\b\w+\s+(Ltd|Limited|Inc|Corporation|Corp|LLC|LLP)\b',
                r'\b\w+\s+(Holdings|Group|International|Global)\b'
            ]
        }
        
        self.relationship_type_hierarchy = {
            'CEO_OF': ['EXECUTIVE_OF', 'EMPLOYED_BY'],
            'CHAIRMAN_OF': ['DIRECTOR_OF', 'EMPLOYED_BY'],
            'DIRECTOR_OF': ['EMPLOYED_BY'],
            'SECRETARY_OF': ['EMPLOYED_BY'],
            'SHAREHOLDER_OF': ['RELATED_TO'],
            'SUBSIDIARY_OF': ['RELATED_TO']
        }
        
        self.confidence_thresholds = {
            'high': 0.8,
            'medium': 0.5,
            'low': 0.3
        }

        # Real-time validation rules
        self.validation_rules = {
            'entity_name_min_length': 2,
            'entity_name_max_length': 200,
            'entity_type_required': True,
            'confidence_min_threshold': 0.0,
            'confidence_max_threshold': 1.0,
            'relationship_type_required': True,
            'entity_reference_required': True
        }

        # Common entity type aliases for normalization
        self.entity_type_aliases = {
            'person': ['person', 'individual', 'people', 'human', 'man', 'woman'],
            'company': ['company', 'corporation', 'business', 'organization', 'org', 'firm', 'enterprise'],
            'location': ['location', 'place', 'address', 'city', 'country', 'region'],
            'technology': ['technology', 'tech', 'software', 'system', 'platform', 'tool']
        }

        # Valid relationship types
        self.valid_relationship_types = {
            'person_to_person': [
                'RELATED_TO', 'SPOUSE_OF', 'PARENT_OF', 'CHILD_OF', 'SIBLING_OF',
                'PARTNER_OF', 'COLLEAGUE_OF', 'FRIEND_OF', 'MENTOR_OF'
            ],
            'person_to_company': [
                'CEO_OF', 'CHAIRMAN_OF', 'DIRECTOR_OF', 'EXECUTIVE_OF', 'EMPLOYEE_OF',
                'FOUNDER_OF', 'OWNER_OF', 'SHAREHOLDER_OF', 'CONSULTANT_OF', 'ADVISOR_OF'
            ],
            'company_to_company': [
                'SUBSIDIARY_OF', 'PARENT_OF', 'PARTNER_OF', 'COMPETITOR_OF',
                'SUPPLIER_OF', 'CLIENT_OF', 'INVESTOR_IN', 'ACQUIRED_BY'
            ]
        }
    
    def validate_entity_comprehensive(self, entity: EnhancedEntity, 
                                    session: EnhancedStagingSession) -> ValidationResult:
        """Comprehensive validation of an entity."""
        warnings = []
        errors = []
        
        # Basic validation
        basic_result = self._validate_entity_basic(entity)
        warnings.extend(basic_result.warnings)
        errors.extend(basic_result.errors)
        
        # Advanced validation
        advanced_warnings, advanced_errors = self._validate_entity_advanced(entity, session)
        warnings.extend(advanced_warnings)
        errors.extend(advanced_errors)
        
        # Conflict detection
        conflicts = self.detect_entity_conflicts(entity, session)
        if conflicts:
            warnings.extend([f"Conflict detected: {conflict}" for conflict in conflicts])
        
        is_valid = len(errors) == 0
        return ValidationResult(is_valid=is_valid, warnings=warnings, errors=errors)
    
    def validate_relationship_comprehensive(self, relationship: EnhancedRelationship,
                                          session: EnhancedStagingSession) -> ValidationResult:
        """Comprehensive validation of a relationship."""
        warnings = []
        errors = []
        
        # Basic validation
        basic_result = self._validate_relationship_basic(relationship, session)
        warnings.extend(basic_result.warnings)
        errors.extend(basic_result.errors)
        
        # Advanced validation
        advanced_warnings, advanced_errors = self._validate_relationship_advanced(relationship, session)
        warnings.extend(advanced_warnings)
        errors.extend(advanced_errors)
        
        # Conflict detection
        conflicts = self.detect_relationship_conflicts(relationship, session)
        if conflicts:
            warnings.extend([f"Conflict detected: {conflict}" for conflict in conflicts])
        
        is_valid = len(errors) == 0
        return ValidationResult(is_valid=is_valid, warnings=warnings, errors=errors)
    
    def _validate_entity_basic(self, entity: EnhancedEntity) -> ValidationResult:
        """Basic entity validation."""
        warnings = []
        errors = []
        
        # Name validation
        if not entity.name or not entity.name.strip():
            errors.append("Entity name cannot be empty")
        elif len(entity.name.strip()) < 2:
            warnings.append("Entity name is very short")
        elif len(entity.name) > 200:
            warnings.append("Entity name is very long")
        
        # Type validation
        if not entity.type:
            errors.append("Entity type is required")
        elif entity.type not in ['Person', 'Company', 'Organization', 'Location', 'Technology', 'Financial']:
            warnings.append(f"Unusual entity type: {entity.type}")
        
        # Confidence validation
        if entity.confidence < self.confidence_thresholds['low']:
            warnings.append(f"Very low confidence score: {entity.confidence:.2f}")
        elif entity.confidence < self.confidence_thresholds['medium']:
            warnings.append(f"Low confidence score: {entity.confidence:.2f}")
        
        return ValidationResult(is_valid=len(errors) == 0, warnings=warnings, errors=errors)
    
    def _validate_entity_advanced(self, entity: EnhancedEntity, 
                                 session: EnhancedStagingSession) -> Tuple[List[str], List[str]]:
        """Advanced entity validation."""
        warnings = []
        errors = []
        
        # Pattern matching for entity types
        if entity.type in self.entity_type_patterns:
            patterns = self.entity_type_patterns[entity.type]
            matches_pattern = any(re.search(pattern, entity.name, re.IGNORECASE) for pattern in patterns)
            if not matches_pattern:
                warnings.append(f"Entity name doesn't match typical {entity.type} pattern")
        
        # Check for suspicious characters
        if re.search(r'[^\w\s\-\.\,\(\)]', entity.name):
            warnings.append("Entity name contains unusual characters")
        
        # Check for all caps or all lowercase
        if entity.name.isupper():
            warnings.append("Entity name is all uppercase")
        elif entity.name.islower():
            warnings.append("Entity name is all lowercase")
        
        # Check for missing attributes for specific types
        if entity.type == 'Person':
            if 'role' not in entity.attributes and 'position' not in entity.attributes:
                warnings.append("Person entity missing role/position information")
        elif entity.type == 'Company':
            if 'industry' not in entity.attributes and 'sector' not in entity.attributes:
                warnings.append("Company entity missing industry/sector information")
        
        return warnings, errors
    
    def _validate_relationship_basic(self, relationship: EnhancedRelationship,
                                   session: EnhancedStagingSession) -> ValidationResult:
        """Basic relationship validation."""
        warnings = []
        errors = []
        
        # Check if entities exist
        source_entity = session.get_entity_by_id(relationship.source_entity_id)
        target_entity = session.get_entity_by_id(relationship.target_entity_id)
        
        if not source_entity:
            errors.append(f"Source entity not found: {relationship.source_entity_id}")
        if not target_entity:
            errors.append(f"Target entity not found: {relationship.target_entity_id}")
        
        # Self-relationship check
        if relationship.source_entity_id == relationship.target_entity_id:
            warnings.append("Self-relationship detected")
        
        # Relationship type validation
        if not relationship.relationship_type or not relationship.relationship_type.strip():
            errors.append("Relationship type cannot be empty")
        
        # Confidence validation
        if relationship.confidence < self.confidence_thresholds['low']:
            warnings.append(f"Very low confidence score: {relationship.confidence:.2f}")
        
        return ValidationResult(is_valid=len(errors) == 0, warnings=warnings, errors=errors)
    
    def _validate_relationship_advanced(self, relationship: EnhancedRelationship,
                                      session: EnhancedStagingSession) -> Tuple[List[str], List[str]]:
        """Advanced relationship validation."""
        warnings = []
        errors = []
        
        source_entity = session.get_entity_by_id(relationship.source_entity_id)
        target_entity = session.get_entity_by_id(relationship.target_entity_id)
        
        if source_entity and target_entity:
            # Type compatibility checks
            rel_type = relationship.relationship_type
            source_type = source_entity.type
            target_type = target_entity.type
            
            # Person-Company relationship validation
            if source_type == 'Person' and target_type == 'Company':
                valid_relations = ['CEO_OF', 'CHAIRMAN_OF', 'DIRECTOR_OF', 'SECRETARY_OF', 
                                 'EMPLOYED_BY', 'SHAREHOLDER_OF', 'FOUNDER_OF']
                if rel_type not in valid_relations:
                    warnings.append(f"Unusual Person-Company relationship: {rel_type}")
            
            # Company-Company relationship validation
            elif source_type == 'Company' and target_type == 'Company':
                valid_relations = ['SUBSIDIARY_OF', 'SHAREHOLDER_OF', 'PARTNER_OF', 
                                 'COMPETITOR_OF', 'SUPPLIER_OF', 'CLIENT_OF']
                if rel_type not in valid_relations:
                    warnings.append(f"Unusual Company-Company relationship: {rel_type}")
            
            # Person-Person relationship validation
            elif source_type == 'Person' and target_type == 'Person':
                valid_relations = ['RELATED_TO', 'COLLEAGUE_OF', 'PARTNER_OF', 
                                 'FRIEND_OF', 'FAMILY_OF']
                if rel_type not in valid_relations:
                    warnings.append(f"Unusual Person-Person relationship: {rel_type}")
        
        return warnings, errors
    
    def detect_entity_conflicts(self, entity: EnhancedEntity, 
                               session: EnhancedStagingSession) -> List[str]:
        """Detect conflicts with other entities in the session."""
        conflicts = []
        
        for other_entity in session.entities:
            if other_entity.id == entity.id:
                continue
            
            # Exact name match
            if entity.name.lower() == other_entity.name.lower():
                conflicts.append(f"Duplicate name with entity {other_entity.id}")
            
            # Similar name match (fuzzy matching)
            similarity = SequenceMatcher(None, entity.name.lower(), other_entity.name.lower()).ratio()
            if similarity > 0.85:
                conflicts.append(f"Very similar name to entity {other_entity.id} ({similarity:.2f} similarity)")
            
            # Type conflict for same name
            if (entity.name.lower() == other_entity.name.lower() and 
                entity.type != other_entity.type):
                conflicts.append(f"Type conflict: same name but different types ({entity.type} vs {other_entity.type})")
        
        return conflicts
    
    def detect_relationship_conflicts(self, relationship: EnhancedRelationship,
                                    session: EnhancedStagingSession) -> List[str]:
        """Detect conflicts with other relationships in the session."""
        conflicts = []
        
        for other_rel in session.relationships:
            if other_rel.id == relationship.id:
                continue
            
            # Exact duplicate relationship
            if (relationship.source_entity_id == other_rel.source_entity_id and
                relationship.target_entity_id == other_rel.target_entity_id and
                relationship.relationship_type == other_rel.relationship_type):
                conflicts.append(f"Duplicate relationship with {other_rel.id}")
            
            # Conflicting relationship types
            if (relationship.source_entity_id == other_rel.source_entity_id and
                relationship.target_entity_id == other_rel.target_entity_id):
                if self._are_conflicting_relationship_types(relationship.relationship_type, 
                                                          other_rel.relationship_type):
                    conflicts.append(f"Conflicting relationship type with {other_rel.id}")
            
            # Hierarchical conflicts (e.g., CEO and employee of same company)
            if self._check_hierarchical_conflict(relationship, other_rel, session):
                conflicts.append(f"Hierarchical conflict with {other_rel.id}")
        
        return conflicts
    
    def _are_conflicting_relationship_types(self, type1: str, type2: str) -> bool:
        """Check if two relationship types are conflicting."""
        # Define conflicting pairs
        conflicts = [
            ('CEO_OF', 'EMPLOYEE_OF'),  # Can't be both CEO and regular employee
            ('CHAIRMAN_OF', 'EMPLOYEE_OF'),
            ('COMPETITOR_OF', 'PARTNER_OF'),  # Can't be both competitor and partner
            ('SUBSIDIARY_OF', 'PARENT_OF')  # Circular ownership
        ]
        
        return (type1, type2) in conflicts or (type2, type1) in conflicts
    
    def _check_hierarchical_conflict(self, rel1: EnhancedRelationship, 
                                   rel2: EnhancedRelationship,
                                   session: EnhancedStagingSession) -> bool:
        """Check for hierarchical conflicts between relationships."""
        # This is a simplified check - in practice, you'd want more sophisticated logic
        if (rel1.source_entity_id == rel2.source_entity_id and
            rel1.target_entity_id == rel2.target_entity_id):
            
            # Check if one relationship implies the other
            if rel1.relationship_type in self.relationship_type_hierarchy:
                implied_types = self.relationship_type_hierarchy[rel1.relationship_type]
                if rel2.relationship_type in implied_types:
                    return False  # Not a conflict, one implies the other
            
            # Check for contradictory hierarchical relationships
            hierarchical_types = ['CEO_OF', 'CHAIRMAN_OF', 'DIRECTOR_OF', 'EMPLOYEE_OF']
            if (rel1.relationship_type in hierarchical_types and 
                rel2.relationship_type in hierarchical_types and
                rel1.relationship_type != rel2.relationship_type):
                return True
        
        return False
    
    def get_data_quality_score(self, session: EnhancedStagingSession) -> Dict[str, Any]:
        """Calculate overall data quality score for a session."""
        if not session.entities and not session.relationships:
            return {"score": 0.0, "details": "No data to evaluate"}
        
        total_score = 0.0
        total_items = 0
        
        entity_scores = []
        relationship_scores = []
        
        # Score entities
        for entity in session.entities:
            score = self._calculate_entity_quality_score(entity, session)
            entity_scores.append(score)
            total_score += score
            total_items += 1
        
        # Score relationships
        for relationship in session.relationships:
            score = self._calculate_relationship_quality_score(relationship, session)
            relationship_scores.append(score)
            total_score += score
            total_items += 1
        
        overall_score = total_score / total_items if total_items > 0 else 0.0
        
        return {
            "overall_score": round(overall_score, 2),
            "entity_average": round(sum(entity_scores) / len(entity_scores), 2) if entity_scores else 0.0,
            "relationship_average": round(sum(relationship_scores) / len(relationship_scores), 2) if relationship_scores else 0.0,
            "total_entities": len(session.entities),
            "total_relationships": len(session.relationships),
            "quality_grade": self._get_quality_grade(overall_score)
        }
    
    def _calculate_entity_quality_score(self, entity: EnhancedEntity, 
                                      session: EnhancedStagingSession) -> float:
        """Calculate quality score for a single entity."""
        score = 0.0
        
        # Confidence score (40% weight)
        score += entity.confidence * 0.4
        
        # Name quality (30% weight)
        name_score = 1.0
        if len(entity.name) < 2:
            name_score -= 0.5
        if not entity.name.strip():
            name_score = 0.0
        if re.search(r'[^\w\s\-\.\,\(\)]', entity.name):
            name_score -= 0.2
        score += max(0.0, name_score) * 0.3
        
        # Type appropriateness (20% weight)
        type_score = 1.0 if entity.type in ['Person', 'Company', 'Organization'] else 0.8
        score += type_score * 0.2
        
        # Attributes completeness (10% weight)
        attr_score = min(1.0, len(entity.attributes) / 3)  # Assume 3 attributes is good
        score += attr_score * 0.1
        
        return min(1.0, score)
    
    def _calculate_relationship_quality_score(self, relationship: EnhancedRelationship,
                                            session: EnhancedStagingSession) -> float:
        """Calculate quality score for a single relationship."""
        score = 0.0
        
        # Confidence score (50% weight)
        score += relationship.confidence * 0.5
        
        # Entity existence (30% weight)
        source_exists = session.get_entity_by_id(relationship.source_entity_id) is not None
        target_exists = session.get_entity_by_id(relationship.target_entity_id) is not None
        entity_score = (int(source_exists) + int(target_exists)) / 2
        score += entity_score * 0.3
        
        # Relationship type appropriateness (20% weight)
        type_score = 1.0 if relationship.relationship_type else 0.0
        score += type_score * 0.2
        
        return min(1.0, score)
    
    def _get_quality_grade(self, score: float) -> str:
        """Convert quality score to letter grade."""
        if score >= 0.9:
            return "A"
        elif score >= 0.8:
            return "B"
        elif score >= 0.7:
            return "C"
        elif score >= 0.6:
            return "D"
        else:
            return "F"

    # Real-time validation methods

    def validate_entity_real_time(self, entity_data: Dict[str, Any],
                                 session_entities: Optional[List[EnhancedEntity]] = None) -> Dict[str, Any]:
        """Perform real-time validation on entity data as user types."""
        validation_result = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "suggestions": [],
            "field_validations": {}
        }

        # Validate name field
        name_validation = self._validate_entity_name_real_time(entity_data.get("name", ""))
        validation_result["field_validations"]["name"] = name_validation
        if not name_validation["is_valid"]:
            validation_result["is_valid"] = False
            validation_result["errors"].extend(name_validation["errors"])
        validation_result["warnings"].extend(name_validation.get("warnings", []))
        validation_result["suggestions"].extend(name_validation.get("suggestions", []))

        # Validate type field
        type_validation = self._validate_entity_type_real_time(entity_data.get("type", ""))
        validation_result["field_validations"]["type"] = type_validation
        if not type_validation["is_valid"]:
            validation_result["is_valid"] = False
            validation_result["errors"].extend(type_validation["errors"])
        validation_result["warnings"].extend(type_validation.get("warnings", []))
        validation_result["suggestions"].extend(type_validation.get("suggestions", []))

        # Validate confidence field
        confidence_validation = self._validate_confidence_real_time(entity_data.get("confidence", 0.0))
        validation_result["field_validations"]["confidence"] = confidence_validation
        if not confidence_validation["is_valid"]:
            validation_result["is_valid"] = False
            validation_result["errors"].extend(confidence_validation["errors"])
        validation_result["warnings"].extend(confidence_validation.get("warnings", []))

        # Check for duplicates if session entities provided
        if session_entities:
            duplicate_validation = self._check_entity_duplicates_real_time(entity_data, session_entities)
            validation_result["warnings"].extend(duplicate_validation.get("warnings", []))
            validation_result["suggestions"].extend(duplicate_validation.get("suggestions", []))

        return validation_result

    def validate_relationship_real_time(self, relationship_data: Dict[str, Any],
                                      session_entities: Optional[List[EnhancedEntity]] = None) -> Dict[str, Any]:
        """Perform real-time validation on relationship data."""
        validation_result = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "suggestions": [],
            "field_validations": {}
        }

        # Validate source entity
        source_validation = self._validate_entity_reference_real_time(
            relationship_data.get("source_entity_id", ""), "source", session_entities
        )
        validation_result["field_validations"]["source_entity_id"] = source_validation
        if not source_validation["is_valid"]:
            validation_result["is_valid"] = False
            validation_result["errors"].extend(source_validation["errors"])

        # Validate target entity
        target_validation = self._validate_entity_reference_real_time(
            relationship_data.get("target_entity_id", ""), "target", session_entities
        )
        validation_result["field_validations"]["target_entity_id"] = target_validation
        if not target_validation["is_valid"]:
            validation_result["is_valid"] = False
            validation_result["errors"].extend(target_validation["errors"])

        # Validate relationship type
        type_validation = self._validate_relationship_type_real_time(
            relationship_data.get("relationship_type", ""),
            relationship_data.get("source_entity_id", ""),
            relationship_data.get("target_entity_id", ""),
            session_entities
        )
        validation_result["field_validations"]["relationship_type"] = type_validation
        if not type_validation["is_valid"]:
            validation_result["is_valid"] = False
            validation_result["errors"].extend(type_validation["errors"])
        validation_result["suggestions"].extend(type_validation.get("suggestions", []))

        # Validate confidence
        confidence_validation = self._validate_confidence_real_time(relationship_data.get("confidence", 0.0))
        validation_result["field_validations"]["confidence"] = confidence_validation
        if not confidence_validation["is_valid"]:
            validation_result["is_valid"] = False
            validation_result["errors"].extend(confidence_validation["errors"])
        validation_result["warnings"].extend(confidence_validation.get("warnings", []))

        # Check for circular relationships
        if (relationship_data.get("source_entity_id") and
            relationship_data.get("target_entity_id") and
            relationship_data.get("source_entity_id") == relationship_data.get("target_entity_id")):
            validation_result["warnings"].append("Self-referencing relationship detected")

        return validation_result

    def _validate_entity_name_real_time(self, name: str) -> Dict[str, Any]:
        """Validate entity name in real-time."""
        validation = {"is_valid": True, "errors": [], "warnings": [], "suggestions": []}

        if not name:
            validation["is_valid"] = False
            validation["errors"].append("Entity name is required")
            return validation

        name = name.strip()

        # Check length
        if len(name) < self.validation_rules["entity_name_min_length"]:
            validation["is_valid"] = False
            validation["errors"].append(f"Entity name must be at least {self.validation_rules['entity_name_min_length']} characters")

        if len(name) > self.validation_rules["entity_name_max_length"]:
            validation["is_valid"] = False
            validation["errors"].append(f"Entity name must be less than {self.validation_rules['entity_name_max_length']} characters")

        # Check for invalid characters
        if re.search(r'[<>{}[\]\\|`~]', name):
            validation["warnings"].append("Entity name contains potentially problematic characters")

        # Check for common patterns
        if re.match(r'^[A-Z][a-z]+ [A-Z][a-z]+$', name):
            validation["suggestions"].append("This looks like a person name - consider setting type to 'Person'")
        elif re.search(r'\b(Ltd|Limited|Inc|Corporation|Corp|LLC|LLP)\b', name, re.IGNORECASE):
            validation["suggestions"].append("This looks like a company name - consider setting type to 'Company'")

        return validation

    def _validate_entity_type_real_time(self, entity_type: str) -> Dict[str, Any]:
        """Validate entity type in real-time."""
        validation = {"is_valid": True, "errors": [], "warnings": [], "suggestions": []}

        if not entity_type:
            if self.validation_rules["entity_type_required"]:
                validation["is_valid"] = False
                validation["errors"].append("Entity type is required")
            return validation

        entity_type = entity_type.strip()

        # Normalize and suggest standard types
        normalized_type = self._normalize_entity_type(entity_type.lower())
        if normalized_type and normalized_type != entity_type.lower():
            validation["suggestions"].append(f"Consider using standard type: '{normalized_type.title()}'")

        # Check for common typos
        common_types = ['Person', 'Company', 'Organization', 'Location', 'Technology']
        for common_type in common_types:
            similarity = SequenceMatcher(None, entity_type.lower(), common_type.lower()).ratio()
            if 0.7 <= similarity < 1.0:
                validation["suggestions"].append(f"Did you mean '{common_type}'?")

        return validation

    def _validate_confidence_real_time(self, confidence: Any) -> Dict[str, Any]:
        """Validate confidence score in real-time."""
        validation = {"is_valid": True, "errors": [], "warnings": []}

        try:
            confidence_float = float(confidence)
        except (ValueError, TypeError):
            validation["is_valid"] = False
            validation["errors"].append("Confidence must be a number")
            return validation

        if confidence_float < self.validation_rules["confidence_min_threshold"]:
            validation["is_valid"] = False
            validation["errors"].append(f"Confidence must be at least {self.validation_rules['confidence_min_threshold']}")

        if confidence_float > self.validation_rules["confidence_max_threshold"]:
            validation["is_valid"] = False
            validation["errors"].append(f"Confidence must be at most {self.validation_rules['confidence_max_threshold']}")

        if confidence_float < 0.5:
            validation["warnings"].append("Low confidence score - consider reviewing this item")

        return validation

    def _validate_entity_reference_real_time(self, entity_id: str, field_name: str,
                                           session_entities: Optional[List[EnhancedEntity]] = None) -> Dict[str, Any]:
        """Validate entity reference in real-time."""
        validation = {"is_valid": True, "errors": [], "warnings": []}

        if not entity_id:
            if self.validation_rules["entity_reference_required"]:
                validation["is_valid"] = False
                validation["errors"].append(f"{field_name.title()} entity is required")
            return validation

        if session_entities:
            entity_ids = {entity.id for entity in session_entities}
            if entity_id not in entity_ids:
                validation["is_valid"] = False
                validation["errors"].append(f"{field_name.title()} entity '{entity_id}' not found")

        return validation

    def _validate_relationship_type_real_time(self, relationship_type: str, source_entity_id: str,
                                            target_entity_id: str, session_entities: Optional[List[EnhancedEntity]] = None) -> Dict[str, Any]:
        """Validate relationship type in real-time."""
        validation = {"is_valid": True, "errors": [], "warnings": [], "suggestions": []}

        if not relationship_type:
            if self.validation_rules["relationship_type_required"]:
                validation["is_valid"] = False
                validation["errors"].append("Relationship type is required")
            return validation

        # Get entity types if available
        source_type = None
        target_type = None

        if session_entities and source_entity_id and target_entity_id:
            for entity in session_entities:
                if entity.id == source_entity_id:
                    source_type = entity.type.lower()
                elif entity.id == target_entity_id:
                    target_type = entity.type.lower()

        # Suggest appropriate relationship types based on entity types
        if source_type and target_type:
            suggested_types = self._get_suggested_relationship_types(source_type, target_type)
            if suggested_types and relationship_type.upper() not in [t.upper() for t in suggested_types]:
                validation["suggestions"].extend([f"Consider: {t}" for t in suggested_types[:3]])

        # Check for common typos in relationship types
        all_valid_types = []
        for type_list in self.valid_relationship_types.values():
            all_valid_types.extend(type_list)

        for valid_type in all_valid_types:
            similarity = SequenceMatcher(None, relationship_type.upper(), valid_type.upper()).ratio()
            if 0.7 <= similarity < 1.0:
                validation["suggestions"].append(f"Did you mean '{valid_type}'?")
                break

        return validation

    def _check_entity_duplicates_real_time(self, entity_data: Dict[str, Any],
                                         session_entities: List[EnhancedEntity]) -> Dict[str, Any]:
        """Check for potential duplicates in real-time."""
        validation = {"warnings": [], "suggestions": []}

        entity_name = entity_data.get("name", "").lower().strip()
        entity_type = entity_data.get("type", "").lower().strip()

        if not entity_name:
            return validation

        for existing_entity in session_entities:
            existing_name = existing_entity.name.lower().strip()
            existing_type = existing_entity.type.lower().strip()

            # Check for exact duplicates
            if entity_name == existing_name and entity_type == existing_type:
                validation["warnings"].append(f"Exact duplicate found: '{existing_entity.name}' already exists")
                continue

            # Check for similar names
            similarity = SequenceMatcher(None, entity_name, existing_name).ratio()
            if similarity >= 0.8 and entity_type == existing_type:
                validation["warnings"].append(f"Similar entity found: '{existing_entity.name}' ({similarity:.1%} similar)")
            elif similarity >= 0.9:  # Very similar names regardless of type
                validation["suggestions"].append(f"Very similar name found: '{existing_entity.name}' (different type)")

        return validation

    def _normalize_entity_type(self, entity_type: str) -> Optional[str]:
        """Normalize entity type to standard form."""
        entity_type_lower = entity_type.lower().strip()

        for standard_type, aliases in self.entity_type_aliases.items():
            if entity_type_lower in aliases:
                return standard_type

        return None

    def _get_suggested_relationship_types(self, source_type: str, target_type: str) -> List[str]:
        """Get suggested relationship types based on entity types."""
        source_type = source_type.lower()
        target_type = target_type.lower()

        # Normalize entity types
        source_normalized = self._normalize_entity_type(source_type) or source_type
        target_normalized = self._normalize_entity_type(target_type) or target_type

        if source_normalized == "person" and target_normalized == "person":
            return self.valid_relationship_types["person_to_person"][:5]
        elif source_normalized == "person" and target_normalized == "company":
            return self.valid_relationship_types["person_to_company"][:5]
        elif source_normalized == "company" and target_normalized == "person":
            # Reverse the person-to-company relationships
            return [f"EMPLOYS_{rel.split('_OF')[0]}" if "_OF" in rel else rel
                   for rel in self.valid_relationship_types["person_to_company"][:3]]
        elif source_normalized == "company" and target_normalized == "company":
            return self.valid_relationship_types["company_to_company"][:5]
        else:
            # Generic relationships
            return ["RELATED_TO", "ASSOCIATED_WITH", "CONNECTED_TO"]

    def validate_batch_data(self, entities_data: List[Dict[str, Any]],
                          relationships_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate batch data for import operations."""
        validation_result = {
            "is_valid": True,
            "total_items": len(entities_data) + len(relationships_data),
            "valid_entities": 0,
            "valid_relationships": 0,
            "errors": [],
            "warnings": [],
            "entity_validations": [],
            "relationship_validations": []
        }

        # Create temporary entity list for reference validation
        temp_entities = []
        entity_id_map = {}

        # Validate entities first
        for i, entity_data in enumerate(entities_data):
            entity_validation = self.validate_entity_real_time(entity_data)
            entity_validation["index"] = i
            validation_result["entity_validations"].append(entity_validation)

            if entity_validation["is_valid"]:
                validation_result["valid_entities"] += 1
                # Create temporary entity for relationship validation
                temp_entity = EnhancedEntity(
                    id=entity_data.get("id", f"temp_{i}"),
                    name=entity_data.get("name", ""),
                    type=entity_data.get("type", "")
                )
                temp_entities.append(temp_entity)
                entity_id_map[temp_entity.id] = temp_entity
            else:
                validation_result["is_valid"] = False
                validation_result["errors"].extend([f"Entity {i+1}: {error}" for error in entity_validation["errors"]])

        # Validate relationships
        for i, relationship_data in enumerate(relationships_data):
            relationship_validation = self.validate_relationship_real_time(relationship_data, temp_entities)
            relationship_validation["index"] = i
            validation_result["relationship_validations"].append(relationship_validation)

            if relationship_validation["is_valid"]:
                validation_result["valid_relationships"] += 1
            else:
                validation_result["is_valid"] = False
                validation_result["errors"].extend([f"Relationship {i+1}: {error}" for error in relationship_validation["errors"]])

        # Collect all warnings
        for entity_val in validation_result["entity_validations"]:
            validation_result["warnings"].extend([f"Entity {entity_val['index']+1}: {warning}" for warning in entity_val["warnings"]])

        for rel_val in validation_result["relationship_validations"]:
            validation_result["warnings"].extend([f"Relationship {rel_val['index']+1}: {warning}" for warning in rel_val["warnings"]])

        return validation_result


# Global service instance
validation_service = ValidationService()
