"""
Analytics service for entity management system.
Provides session statistics, quality scores, activity timelines, and dashboard data.
"""

import os
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict, Counter

from ..models.enhanced_staging_models import (
    EnhancedStagingSession, EnhancedEntity, EnhancedRelationship,
    EntityStatus, SessionStatus, WorkflowStage
)

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Service for generating analytics and dashboard data."""
    
    def __init__(self, staging_dir: str = "staging/data"):
        self.staging_dir = Path(staging_dir)
        self.staging_dir.mkdir(parents=True, exist_ok=True)
        self._initialized = False
    
    async def initialize(self):
        """Initialize the analytics service."""
        if not self._initialized:
            logger.info("Initializing Analytics Service")
            self._initialized = True
    
    async def get_dashboard_overview(self) -> Dict[str, Any]:
        """Get comprehensive dashboard overview data."""
        if not self._initialized:
            await self.initialize()
        
        try:
            sessions = await self._load_all_sessions()
            
            # Calculate overview statistics
            total_sessions = len(sessions)
            total_entities = sum(len(session.entities) for session in sessions)
            total_relationships = sum(len(session.relationships) for session in sessions)
            
            # Status distribution
            session_status_counts = Counter(session.status.value for session in sessions)
            entity_status_counts = Counter()
            relationship_status_counts = Counter()
            
            for session in sessions:
                for entity in session.entities:
                    entity_status_counts[entity.status.value] += 1
                for relationship in session.relationships:
                    relationship_status_counts[relationship.status.value] += 1
            
            # Calculate approval rates
            approved_entities = entity_status_counts.get('approved', 0)
            approved_relationships = relationship_status_counts.get('approved', 0)
            
            entity_approval_rate = (approved_entities / total_entities * 100) if total_entities > 0 else 0
            relationship_approval_rate = (approved_relationships / total_relationships * 100) if total_relationships > 0 else 0
            
            # Recent activity (last 7 days)
            recent_activity = await self._get_recent_activity(days=7)
            
            # Quality metrics
            quality_metrics = await self._calculate_quality_metrics(sessions)
            
            return {
                "overview": {
                    "total_sessions": total_sessions,
                    "total_entities": total_entities,
                    "total_relationships": total_relationships,
                    "entity_approval_rate": round(entity_approval_rate, 1),
                    "relationship_approval_rate": round(relationship_approval_rate, 1)
                },
                "status_distribution": {
                    "sessions": dict(session_status_counts),
                    "entities": dict(entity_status_counts),
                    "relationships": dict(relationship_status_counts)
                },
                "recent_activity": recent_activity,
                "quality_metrics": quality_metrics,
                "pending_items": await self._get_pending_items_summary()
            }
        except Exception as e:
            logger.error(f"Error generating dashboard overview: {e}")
            return {"error": str(e)}
    
    async def get_session_analytics(self, session_id: str) -> Dict[str, Any]:
        """Get detailed analytics for a specific session."""
        if not self._initialized:
            await self.initialize()
        
        try:
            session = await self._load_session(session_id)
            if not session:
                return {"error": "Session not found"}
            
            # Entity type distribution
            entity_types = Counter(entity.type for entity in session.entities)
            relationship_types = Counter(rel.relationship_type for rel in session.relationships)
            
            # Confidence score analysis
            entity_confidence_stats = self._calculate_confidence_stats(
                [entity.confidence for entity in session.entities]
            )
            relationship_confidence_stats = self._calculate_confidence_stats(
                [rel.confidence for rel in session.relationships]
            )
            
            # Edit history analysis
            edit_activity = self._analyze_edit_activity(session)
            
            # Validation issues
            validation_issues = await self._get_validation_issues(session)
            
            return {
                "session_info": {
                    "session_id": session.session_id,
                    "document_title": session.document_title,
                    "status": session.status.value,
                    "workflow_stage": session.workflow_stage.value,
                    "created_at": session.created_at,
                    "updated_at": session.updated_at
                },
                "statistics": session.statistics.to_dict(),
                "type_distribution": {
                    "entities": dict(entity_types),
                    "relationships": dict(relationship_types)
                },
                "confidence_analysis": {
                    "entities": entity_confidence_stats,
                    "relationships": relationship_confidence_stats
                },
                "edit_activity": edit_activity,
                "validation_issues": validation_issues
            }
        except Exception as e:
            logger.error(f"Error generating session analytics for {session_id}: {e}")
            return {"error": str(e)}
    
    async def get_activity_timeline(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get activity timeline for the specified number of days."""
        if not self._initialized:
            await self.initialize()
        
        try:
            sessions = await self._load_all_sessions()
            timeline = []
            
            cutoff_date = datetime.now() - timedelta(days=days)
            
            for session in sessions:
                # Add session creation
                session_date = datetime.fromisoformat(session.created_at.replace('Z', '+00:00'))
                if session_date >= cutoff_date:
                    timeline.append({
                        "timestamp": session.created_at,
                        "type": "session_created",
                        "session_id": session.session_id,
                        "document_title": session.document_title,
                        "details": {
                            "entities_count": len(session.entities),
                            "relationships_count": len(session.relationships)
                        }
                    })
                
                # Add audit trail entries
                for audit_entry in session.audit_trail:
                    entry_date = datetime.fromisoformat(audit_entry.timestamp.replace('Z', '+00:00'))
                    if entry_date >= cutoff_date:
                        timeline.append({
                            "timestamp": audit_entry.timestamp,
                            "type": "session_action",
                            "session_id": session.session_id,
                            "action": audit_entry.action,
                            "user": audit_entry.user,
                            "details": audit_entry.changes
                        })
                
                # Add entity and relationship actions
                for entity in session.entities:
                    for audit_entry in entity.edit_history:
                        entry_date = datetime.fromisoformat(audit_entry.timestamp.replace('Z', '+00:00'))
                        if entry_date >= cutoff_date:
                            timeline.append({
                                "timestamp": audit_entry.timestamp,
                                "type": "entity_action",
                                "session_id": session.session_id,
                                "entity_id": entity.id,
                                "entity_name": entity.name,
                                "action": audit_entry.action,
                                "user": audit_entry.user,
                                "details": audit_entry.changes
                            })
            
            # Sort by timestamp (newest first)
            timeline.sort(key=lambda x: x["timestamp"], reverse=True)
            return timeline[:100]  # Limit to 100 most recent items
            
        except Exception as e:
            logger.error(f"Error generating activity timeline: {e}")
            return []
    
    async def get_quality_report(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Generate a comprehensive quality report."""
        if not self._initialized:
            await self.initialize()
        
        try:
            if session_id:
                sessions = [await self._load_session(session_id)]
                sessions = [s for s in sessions if s is not None]
            else:
                sessions = await self._load_all_sessions()
            
            if not sessions:
                return {"error": "No sessions found"}
            
            quality_metrics = await self._calculate_quality_metrics(sessions)
            
            # Detailed quality analysis
            issues_by_type = defaultdict(list)
            recommendations = []
            
            for session in sessions:
                session_issues = await self._get_validation_issues(session)
                for issue_type, issues in session_issues.items():
                    issues_by_type[issue_type].extend(issues)
            
            # Generate recommendations based on issues
            if issues_by_type.get("duplicates"):
                recommendations.append({
                    "type": "warning",
                    "title": "Duplicate Entities Detected",
                    "description": f"Found {len(issues_by_type['duplicates'])} potential duplicate entities",
                    "action": "Review and merge duplicate entities"
                })
            
            if issues_by_type.get("low_confidence"):
                recommendations.append({
                    "type": "info",
                    "title": "Low Confidence Entities",
                    "description": f"Found {len(issues_by_type['low_confidence'])} entities with low confidence scores",
                    "action": "Review and validate low confidence entities"
                })
            
            return {
                "quality_score": quality_metrics["overall_score"],
                "metrics": quality_metrics,
                "issues_summary": {k: len(v) for k, v in issues_by_type.items()},
                "detailed_issues": dict(issues_by_type),
                "recommendations": recommendations,
                "sessions_analyzed": len(sessions)
            }
            
        except Exception as e:
            logger.error(f"Error generating quality report: {e}")
            return {"error": str(e)}
    
    # Private helper methods
    
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
    
    async def _get_recent_activity(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get recent activity summary."""
        timeline = await self.get_activity_timeline(days)
        
        # Group by day
        daily_activity = defaultdict(lambda: {"sessions": 0, "entities": 0, "relationships": 0, "actions": 0})
        
        for item in timeline:
            date = item["timestamp"][:10]  # Extract date part
            daily_activity[date]["actions"] += 1
            
            if item["type"] == "session_created":
                daily_activity[date]["sessions"] += 1
                daily_activity[date]["entities"] += item["details"].get("entities_count", 0)
                daily_activity[date]["relationships"] += item["details"].get("relationships_count", 0)
        
        return [{"date": date, **stats} for date, stats in sorted(daily_activity.items(), reverse=True)]
    
    def _calculate_confidence_stats(self, confidence_scores: List[float]) -> Dict[str, float]:
        """Calculate confidence score statistics."""
        if not confidence_scores:
            return {"mean": 0, "min": 0, "max": 0, "std": 0}
        
        mean_score = sum(confidence_scores) / len(confidence_scores)
        min_score = min(confidence_scores)
        max_score = max(confidence_scores)
        
        # Calculate standard deviation
        variance = sum((x - mean_score) ** 2 for x in confidence_scores) / len(confidence_scores)
        std_score = variance ** 0.5
        
        return {
            "mean": round(mean_score, 3),
            "min": round(min_score, 3),
            "max": round(max_score, 3),
            "std": round(std_score, 3)
        }
    
    def _analyze_edit_activity(self, session: EnhancedStagingSession) -> Dict[str, Any]:
        """Analyze edit activity for a session."""
        total_edits = 0
        users = set()
        actions = Counter()
        
        # Session-level edits
        for audit_entry in session.audit_trail:
            total_edits += 1
            users.add(audit_entry.user)
            actions[audit_entry.action] += 1
        
        # Entity-level edits
        for entity in session.entities:
            for audit_entry in entity.edit_history:
                total_edits += 1
                users.add(audit_entry.user)
                actions[audit_entry.action] += 1
        
        # Relationship-level edits
        for relationship in session.relationships:
            for audit_entry in relationship.edit_history:
                total_edits += 1
                users.add(audit_entry.user)
                actions[audit_entry.action] += 1
        
        return {
            "total_edits": total_edits,
            "unique_users": len(users),
            "users": list(users),
            "actions": dict(actions)
        }
    
    async def _get_validation_issues(self, session: EnhancedStagingSession) -> Dict[str, List[Dict[str, Any]]]:
        """Get validation issues for a session."""
        issues = {
            "duplicates": [],
            "low_confidence": [],
            "missing_fields": [],
            "invalid_relationships": []
        }
        
        # Check for duplicate entities
        entity_names = {}
        for entity in session.entities:
            name_lower = entity.name.lower()
            if name_lower in entity_names:
                issues["duplicates"].append({
                    "type": "duplicate_entity",
                    "entity_id": entity.id,
                    "entity_name": entity.name,
                    "duplicate_of": entity_names[name_lower]
                })
            else:
                entity_names[name_lower] = entity.id
        
        # Check for low confidence entities
        for entity in session.entities:
            if entity.confidence < 0.5:
                issues["low_confidence"].append({
                    "type": "low_confidence_entity",
                    "entity_id": entity.id,
                    "entity_name": entity.name,
                    "confidence": entity.confidence
                })
        
        # Check for missing required fields
        for entity in session.entities:
            if not entity.name or not entity.type:
                issues["missing_fields"].append({
                    "type": "missing_required_field",
                    "entity_id": entity.id,
                    "missing_fields": [f for f in ["name", "type"] if not getattr(entity, f)]
                })
        
        return issues
    
    async def _calculate_quality_metrics(self, sessions: List[EnhancedStagingSession]) -> Dict[str, Any]:
        """Calculate overall quality metrics."""
        if not sessions:
            return {"overall_score": 0}
        
        total_entities = sum(len(session.entities) for session in sessions)
        total_relationships = sum(len(session.relationships) for session in sessions)
        
        if total_entities == 0:
            return {"overall_score": 0}
        
        # Calculate various quality metrics
        approved_entities = sum(
            sum(1 for entity in session.entities if entity.status == EntityStatus.APPROVED)
            for session in sessions
        )
        
        high_confidence_entities = sum(
            sum(1 for entity in session.entities if entity.confidence >= 0.7)
            for session in sessions
        )
        
        entities_with_validation = sum(
            sum(1 for entity in session.entities if entity.validation_results is not None)
            for session in sessions
        )
        
        # Calculate scores (0-100)
        approval_score = (approved_entities / total_entities) * 100 if total_entities > 0 else 0
        confidence_score = (high_confidence_entities / total_entities) * 100 if total_entities > 0 else 0
        validation_score = (entities_with_validation / total_entities) * 100 if total_entities > 0 else 0
        
        # Overall score (weighted average)
        overall_score = (approval_score * 0.4 + confidence_score * 0.3 + validation_score * 0.3)
        
        return {
            "overall_score": round(overall_score, 1),
            "approval_score": round(approval_score, 1),
            "confidence_score": round(confidence_score, 1),
            "validation_score": round(validation_score, 1),
            "total_entities": total_entities,
            "total_relationships": total_relationships
        }
    
    async def _get_pending_items_summary(self) -> Dict[str, Any]:
        """Get summary of pending items across all sessions."""
        sessions = await self._load_all_sessions()
        
        pending_sessions = [s for s in sessions if s.status == SessionStatus.PENDING_REVIEW]
        pending_entities = sum(
            sum(1 for entity in session.entities if entity.status == EntityStatus.PENDING)
            for session in sessions
        )
        pending_relationships = sum(
            sum(1 for rel in session.relationships if rel.status == EntityStatus.PENDING)
            for session in sessions
        )
        
        return {
            "pending_sessions": len(pending_sessions),
            "pending_entities": pending_entities,
            "pending_relationships": pending_relationships,
            "sessions_needing_attention": [
                {
                    "session_id": session.session_id,
                    "document_title": session.document_title,
                    "pending_entities": sum(1 for e in session.entities if e.status == EntityStatus.PENDING),
                    "pending_relationships": sum(1 for r in session.relationships if r.status == EntityStatus.PENDING)
                }
                for session in pending_sessions
            ]
        }


# Global service instance
analytics_service = AnalyticsService()
