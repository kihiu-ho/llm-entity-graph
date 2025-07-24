"""
Workflow Orchestration Service - Manages the complete document-to-graph pipeline
Coordinates document ingestion, entity management, conflict resolution, and Neo4j ingestion
"""

import os
import json
import uuid
import logging
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, asdict
from enum import Enum

from .document_ingestion_service import document_ingestion_service, ProcessingStatus
from .enhanced_staging_service import enhanced_staging_service
from .conflict_detection_service import conflict_detection_service
from .analytics_service import analytics_service
from .websocket_service import websocket_manager, DocumentProcessingMessages

logger = logging.getLogger(__name__)


class WorkflowStage(Enum):
    """Workflow stage enumeration."""
    DOCUMENT_UPLOAD = "document_upload"
    DOCUMENT_PROCESSING = "document_processing"
    ENTITY_STAGING = "entity_staging"
    CONFLICT_DETECTION = "conflict_detection"
    MANUAL_REVIEW = "manual_review"
    ENTITY_APPROVAL = "entity_approval"
    NEO4J_INGESTION = "neo4j_ingestion"
    COMPLETED = "completed"
    FAILED = "failed"


class WorkflowStatus(Enum):
    """Workflow status enumeration."""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class WorkflowInstance:
    """Represents a complete workflow instance."""
    workflow_id: str
    user_id: str
    name: str
    description: str
    status: WorkflowStatus
    current_stage: WorkflowStage
    created_at: datetime
    updated_at: datetime
    
    # Associated IDs
    job_ids: List[str]  # Document processing jobs
    session_ids: List[str]  # Staging sessions
    
    # Progress tracking
    total_documents: int = 0
    processed_documents: int = 0
    total_entities: int = 0
    approved_entities: int = 0
    total_relationships: int = 0
    approved_relationships: int = 0
    conflicts_detected: int = 0
    conflicts_resolved: int = 0
    
    # Configuration
    auto_approve_threshold: float = 0.9
    auto_resolve_conflicts: bool = False
    batch_processing: bool = True
    
    # Metadata
    metadata: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


class WorkflowOrchestrationService:
    """Service for orchestrating complete document-to-graph workflows."""
    
    def __init__(self, workflows_dir: str = "staging/workflows"):
        self.workflows_dir = Path(workflows_dir)
        self.workflows_dir.mkdir(parents=True, exist_ok=True)
        
        # Active workflows
        self.active_workflows: Dict[str, WorkflowInstance] = {}
        
        # Workflow automation rules
        self.automation_rules = {
            "auto_approve_high_confidence": True,
            "auto_resolve_simple_conflicts": True,
            "batch_process_documents": True,
            "notify_on_completion": True
        }
        
        self._initialized = False
        self._monitoring_task = None
    
    async def initialize(self):
        """Initialize the workflow orchestration service."""
        if not self._initialized:
            logger.info("Initializing Workflow Orchestration Service")
            
            # Initialize dependent services
            await document_ingestion_service.initialize()
            await enhanced_staging_service.initialize()
            await conflict_detection_service.initialize()
            await analytics_service.initialize()
            
            # Load existing workflows
            await self._load_existing_workflows()
            
            # Start monitoring task
            self._monitoring_task = asyncio.create_task(self._workflow_monitor())
            
            self._initialized = True
            logger.info("Workflow Orchestration Service initialized")
    
    async def close(self):
        """Close the workflow orchestration service."""
        if self._initialized:
            if self._monitoring_task:
                self._monitoring_task.cancel()
            
            await document_ingestion_service.close()
            
            self._initialized = False
    
    async def create_workflow(
        self,
        user_id: str,
        name: str,
        description: str = "",
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a new workflow instance."""
        try:
            workflow_id = str(uuid.uuid4())
            
            workflow = WorkflowInstance(
                workflow_id=workflow_id,
                user_id=user_id,
                name=name,
                description=description,
                status=WorkflowStatus.ACTIVE,
                current_stage=WorkflowStage.DOCUMENT_UPLOAD,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                job_ids=[],
                session_ids=[],
                metadata=config or {}
            )
            
            # Apply configuration
            if config:
                workflow.auto_approve_threshold = config.get("auto_approve_threshold", 0.9)
                workflow.auto_resolve_conflicts = config.get("auto_resolve_conflicts", False)
                workflow.batch_processing = config.get("batch_processing", True)
            
            # Save workflow
            await self._save_workflow(workflow)
            self.active_workflows[workflow_id] = workflow
            
            # Notify user
            await websocket_manager.send_to_user(user_id, {
                "type": "workflow_created",
                "workflow_id": workflow_id,
                "name": name,
                "timestamp": datetime.now().isoformat()
            })
            
            logger.info(f"Workflow created: {workflow_id} by user {user_id}")
            
            return {
                "success": True,
                "workflow_id": workflow_id,
                "status": workflow.status.value,
                "current_stage": workflow.current_stage.value
            }
            
        except Exception as e:
            logger.error(f"Error creating workflow: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def upload_documents_to_workflow(
        self,
        workflow_id: str,
        documents: List[Dict[str, Any]],
        user_id: str
    ) -> Dict[str, Any]:
        """Upload multiple documents to a workflow."""
        try:
            workflow = self.active_workflows.get(workflow_id)
            if not workflow:
                return {
                    "success": False,
                    "error": "Workflow not found"
                }
            
            if workflow.user_id != user_id:
                return {
                    "success": False,
                    "error": "Permission denied"
                }
            
            if workflow.current_stage != WorkflowStage.DOCUMENT_UPLOAD:
                return {
                    "success": False,
                    "error": f"Cannot upload documents in stage {workflow.current_stage.value}"
                }
            
            uploaded_jobs = []
            failed_uploads = []
            
            # Upload each document
            for doc in documents:
                try:
                    result = await document_ingestion_service.upload_document(
                        file_data=doc["file_data"],
                        filename=doc["filename"],
                        mime_type=doc["mime_type"],
                        user_id=user_id,
                        metadata={
                            "workflow_id": workflow_id,
                            **doc.get("metadata", {})
                        },
                        processing_config=doc.get("processing_config", {}),
                        priority="high" if workflow.batch_processing else "normal"
                    )
                    
                    if result["success"]:
                        uploaded_jobs.append(result["job_id"])
                        workflow.job_ids.append(result["job_id"])
                    else:
                        failed_uploads.append({
                            "filename": doc["filename"],
                            "error": result["error"]
                        })
                        
                except Exception as e:
                    failed_uploads.append({
                        "filename": doc.get("filename", "unknown"),
                        "error": str(e)
                    })
            
            # Update workflow
            workflow.total_documents = len(uploaded_jobs)
            workflow.current_stage = WorkflowStage.DOCUMENT_PROCESSING
            workflow.updated_at = datetime.now()
            
            await self._save_workflow(workflow)
            
            # Notify user
            await websocket_manager.send_to_user(user_id, {
                "type": "documents_uploaded",
                "workflow_id": workflow_id,
                "uploaded_count": len(uploaded_jobs),
                "failed_count": len(failed_uploads),
                "job_ids": uploaded_jobs,
                "failed_uploads": failed_uploads,
                "timestamp": datetime.now().isoformat()
            })
            
            return {
                "success": True,
                "uploaded_count": len(uploaded_jobs),
                "failed_count": len(failed_uploads),
                "job_ids": uploaded_jobs,
                "failed_uploads": failed_uploads
            }
            
        except Exception as e:
            logger.error(f"Error uploading documents to workflow {workflow_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_workflow_status(self, workflow_id: str, user_id: str) -> Dict[str, Any]:
        """Get the current status of a workflow."""
        try:
            workflow = self.active_workflows.get(workflow_id)
            if not workflow:
                workflow = await self._load_workflow(workflow_id)
            
            if not workflow:
                return {
                    "success": False,
                    "error": "Workflow not found"
                }
            
            if workflow.user_id != user_id:
                return {
                    "success": False,
                    "error": "Permission denied"
                }
            
            # Get job statuses
            job_statuses = []
            for job_id in workflow.job_ids:
                job_status = await document_ingestion_service.get_job_status(job_id)
                if job_status["success"]:
                    job_statuses.append(job_status["job"])
            
            # Get session information
            session_info = []
            for session_id in workflow.session_ids:
                session = await enhanced_staging_service.get_session(session_id)
                if session:
                    session_info.append({
                        "session_id": session_id,
                        "status": session.status.value,
                        "entities_count": len(session.entities),
                        "relationships_count": len(session.relationships),
                        "pending_entities": len([e for e in session.entities if e.status.value == "pending"]),
                        "approved_entities": len([e for e in session.entities if e.status.value == "approved"])
                    })
            
            # Calculate overall progress
            overall_progress = self._calculate_workflow_progress(workflow, job_statuses, session_info)
            
            return {
                "success": True,
                "workflow": {
                    "workflow_id": workflow.workflow_id,
                    "name": workflow.name,
                    "description": workflow.description,
                    "status": workflow.status.value,
                    "current_stage": workflow.current_stage.value,
                    "created_at": workflow.created_at.isoformat(),
                    "updated_at": workflow.updated_at.isoformat(),
                    "total_documents": workflow.total_documents,
                    "processed_documents": workflow.processed_documents,
                    "total_entities": workflow.total_entities,
                    "approved_entities": workflow.approved_entities,
                    "total_relationships": workflow.total_relationships,
                    "approved_relationships": workflow.approved_relationships,
                    "conflicts_detected": workflow.conflicts_detected,
                    "conflicts_resolved": workflow.conflicts_resolved,
                    "overall_progress": overall_progress,
                    "auto_approve_threshold": workflow.auto_approve_threshold,
                    "auto_resolve_conflicts": workflow.auto_resolve_conflicts
                },
                "jobs": job_statuses,
                "sessions": session_info
            }
            
        except Exception as e:
            logger.error(f"Error getting workflow status {workflow_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def approve_workflow_entities(
        self,
        workflow_id: str,
        user_id: str,
        approval_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Approve entities in workflow sessions for Neo4j ingestion."""
        try:
            workflow = self.active_workflows.get(workflow_id)
            if not workflow:
                return {
                    "success": False,
                    "error": "Workflow not found"
                }
            
            if workflow.user_id != user_id:
                return {
                    "success": False,
                    "error": "Permission denied"
                }
            
            if workflow.current_stage not in [WorkflowStage.MANUAL_REVIEW, WorkflowStage.ENTITY_APPROVAL]:
                return {
                    "success": False,
                    "error": f"Cannot approve entities in stage {workflow.current_stage.value}"
                }
            
            approved_count = 0
            total_entities = 0
            
            # Process each session
            for session_id in workflow.session_ids:
                session = await enhanced_staging_service.get_session(session_id)
                if session:
                    total_entities += len(session.entities)
                    
                    # Auto-approve high confidence entities
                    for entity in session.entities:
                        if (entity.confidence >= workflow.auto_approve_threshold and 
                            entity.status.value == "pending"):
                            
                            await enhanced_staging_service.update_entity_status(
                                session_id, entity.id, "approved", user_id, "Auto-approved (high confidence)"
                            )
                            approved_count += 1
                    
                    # Auto-approve high confidence relationships
                    for relationship in session.relationships:
                        if (relationship.confidence >= workflow.auto_approve_threshold and 
                            relationship.status.value == "pending"):
                            
                            await enhanced_staging_service.update_relationship_status(
                                session_id, relationship.id, "approved", user_id, "Auto-approved (high confidence)"
                            )
            
            # Update workflow
            workflow.approved_entities += approved_count
            workflow.current_stage = WorkflowStage.NEO4J_INGESTION
            workflow.updated_at = datetime.now()
            
            await self._save_workflow(workflow)
            
            # Notify user
            await websocket_manager.send_to_user(user_id, DocumentProcessingMessages.entities_approved(
                session_id="workflow", approved_count=approved_count
            ))
            
            return {
                "success": True,
                "approved_count": approved_count,
                "total_entities": total_entities,
                "approval_rate": approved_count / total_entities if total_entities > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error approving workflow entities {workflow_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def ingest_workflow_to_neo4j(self, workflow_id: str, user_id: str) -> Dict[str, Any]:
        """Ingest approved entities from workflow to Neo4j."""
        try:
            workflow = self.active_workflows.get(workflow_id)
            if not workflow:
                return {
                    "success": False,
                    "error": "Workflow not found"
                }
            
            if workflow.user_id != user_id:
                return {
                    "success": False,
                    "error": "Permission denied"
                }
            
            if workflow.current_stage != WorkflowStage.NEO4J_INGESTION:
                return {
                    "success": False,
                    "error": f"Cannot ingest in stage {workflow.current_stage.value}"
                }
            
            ingested_entities = 0
            ingested_relationships = 0
            
            # Ingest each session
            for session_id in workflow.session_ids:
                result = await enhanced_staging_service.ingest_session_to_neo4j(session_id, user_id)
                if result["success"]:
                    ingested_entities += result.get("ingested_entities", 0)
                    ingested_relationships += result.get("ingested_relationships", 0)
            
            # Update workflow
            workflow.status = WorkflowStatus.COMPLETED
            workflow.current_stage = WorkflowStage.COMPLETED
            workflow.updated_at = datetime.now()
            
            await self._save_workflow(workflow)
            
            # Remove from active workflows
            if workflow_id in self.active_workflows:
                del self.active_workflows[workflow_id]
            
            # Notify user
            await websocket_manager.send_to_user(user_id, DocumentProcessingMessages.ingestion_completed(
                session_id="workflow", 
                ingested_entities=ingested_entities,
                ingested_relationships=ingested_relationships
            ))
            
            logger.info(f"Workflow {workflow_id} completed: {ingested_entities} entities, {ingested_relationships} relationships ingested")
            
            return {
                "success": True,
                "ingested_entities": ingested_entities,
                "ingested_relationships": ingested_relationships,
                "message": "Workflow completed successfully"
            }
            
        except Exception as e:
            logger.error(f"Error ingesting workflow {workflow_id} to Neo4j: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def cancel_workflow(self, workflow_id: str, user_id: str) -> Dict[str, Any]:
        """Cancel an active workflow."""
        try:
            workflow = self.active_workflows.get(workflow_id)
            if not workflow:
                return {
                    "success": False,
                    "error": "Workflow not found"
                }
            
            if workflow.user_id != user_id:
                return {
                    "success": False,
                    "error": "Permission denied"
                }
            
            # Cancel all associated jobs
            for job_id in workflow.job_ids:
                await document_ingestion_service.cancel_job(job_id, user_id)
            
            # Update workflow
            workflow.status = WorkflowStatus.CANCELLED
            workflow.updated_at = datetime.now()
            workflow.error_message = "Cancelled by user"
            
            await self._save_workflow(workflow)
            
            # Remove from active workflows
            if workflow_id in self.active_workflows:
                del self.active_workflows[workflow_id]
            
            # Notify user
            await websocket_manager.send_to_user(user_id, {
                "type": "workflow_cancelled",
                "workflow_id": workflow_id,
                "timestamp": datetime.now().isoformat()
            })
            
            return {
                "success": True,
                "message": "Workflow cancelled successfully"
            }
            
        except Exception as e:
            logger.error(f"Error cancelling workflow {workflow_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    # Private methods

    async def _workflow_monitor(self):
        """Monitor workflows and trigger automatic actions."""
        while True:
            try:
                await asyncio.sleep(10)  # Check every 10 seconds

                for workflow_id, workflow in list(self.active_workflows.items()):
                    await self._check_workflow_progress(workflow)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in workflow monitor: {e}")

    async def _check_workflow_progress(self, workflow: WorkflowInstance):
        """Check and update workflow progress."""
        try:
            # Check document processing completion
            if workflow.current_stage == WorkflowStage.DOCUMENT_PROCESSING:
                all_completed = True
                processed_count = 0
                total_entities = 0
                total_relationships = 0

                for job_id in workflow.job_ids:
                    job_status = await document_ingestion_service.get_job_status(job_id)
                    if job_status["success"]:
                        job = job_status["job"]
                        if job["status"] in ["completed", "staged"]:
                            processed_count += 1
                            total_entities += job.get("entities_extracted", 0)
                            total_relationships += job.get("relationships_extracted", 0)

                            # Add session ID if not already added
                            if job.get("session_id") and job["session_id"] not in workflow.session_ids:
                                workflow.session_ids.append(job["session_id"])
                        elif job["status"] not in ["failed", "cancelled"]:
                            all_completed = False

                # Update workflow progress
                workflow.processed_documents = processed_count
                workflow.total_entities = total_entities
                workflow.total_relationships = total_relationships

                if all_completed and processed_count > 0:
                    workflow.current_stage = WorkflowStage.ENTITY_STAGING
                    await self._trigger_conflict_detection(workflow)

                await self._save_workflow(workflow)

            # Check conflict detection completion
            elif workflow.current_stage == WorkflowStage.CONFLICT_DETECTION:
                conflicts_detected = 0

                for session_id in workflow.session_ids:
                    conflicts_result = await conflict_detection_service.detect_session_conflicts(session_id)
                    if conflicts_result["success"]:
                        conflicts_detected += conflicts_result.get("total_conflicts", 0)

                workflow.conflicts_detected = conflicts_detected
                workflow.current_stage = WorkflowStage.MANUAL_REVIEW

                # Auto-resolve conflicts if enabled
                if workflow.auto_resolve_conflicts:
                    await self._auto_resolve_conflicts(workflow)

                await self._save_workflow(workflow)

                # Notify user
                await websocket_manager.send_to_user(
                    workflow.user_id,
                    DocumentProcessingMessages.conflicts_detected(
                        session_id="workflow",
                        conflicts_count=conflicts_detected
                    )
                )

        except Exception as e:
            logger.error(f"Error checking workflow progress {workflow.workflow_id}: {e}")

    async def _trigger_conflict_detection(self, workflow: WorkflowInstance):
        """Trigger conflict detection for workflow sessions."""
        workflow.current_stage = WorkflowStage.CONFLICT_DETECTION

        # Notify user
        await websocket_manager.send_to_user(workflow.user_id, {
            "type": "conflict_detection_started",
            "workflow_id": workflow.workflow_id,
            "sessions_count": len(workflow.session_ids),
            "timestamp": datetime.now().isoformat()
        })

    async def _auto_resolve_conflicts(self, workflow: WorkflowInstance):
        """Automatically resolve simple conflicts."""
        resolved_count = 0

        for session_id in workflow.session_ids:
            conflicts_result = await conflict_detection_service.detect_session_conflicts(session_id)
            if conflicts_result["success"]:
                conflicts = conflicts_result.get("conflicts", {})

                # Auto-resolve duplicate entities (merge high confidence ones)
                for conflict in conflicts.get("duplicate_entities", []):
                    if conflict.get("severity") == "high":
                        try:
                            resolution_result = await conflict_detection_service.resolve_conflict(
                                session_id, conflict["id"], "merge", "system_auto"
                            )
                            if resolution_result["success"]:
                                resolved_count += 1
                        except Exception as e:
                            logger.error(f"Error auto-resolving conflict {conflict['id']}: {e}")

        workflow.conflicts_resolved = resolved_count

        if resolved_count > 0:
            await websocket_manager.send_to_user(workflow.user_id, {
                "type": "conflicts_auto_resolved",
                "workflow_id": workflow.workflow_id,
                "resolved_count": resolved_count,
                "timestamp": datetime.now().isoformat()
            })

    def _calculate_workflow_progress(self, workflow: WorkflowInstance, job_statuses: List[Dict], session_info: List[Dict]) -> float:
        """Calculate overall workflow progress."""
        if workflow.total_documents == 0:
            return 0.0

        # Stage weights
        stage_weights = {
            WorkflowStage.DOCUMENT_UPLOAD: 0.1,
            WorkflowStage.DOCUMENT_PROCESSING: 0.3,
            WorkflowStage.ENTITY_STAGING: 0.1,
            WorkflowStage.CONFLICT_DETECTION: 0.1,
            WorkflowStage.MANUAL_REVIEW: 0.2,
            WorkflowStage.ENTITY_APPROVAL: 0.1,
            WorkflowStage.NEO4J_INGESTION: 0.1,
            WorkflowStage.COMPLETED: 1.0
        }

        base_progress = 0.0

        # Add progress for completed stages
        current_stage_index = list(WorkflowStage).index(workflow.current_stage)
        for i, stage in enumerate(WorkflowStage):
            if i < current_stage_index:
                base_progress += stage_weights[stage]
            elif i == current_stage_index:
                # Add partial progress for current stage
                if stage == WorkflowStage.DOCUMENT_PROCESSING:
                    stage_progress = workflow.processed_documents / workflow.total_documents
                elif stage == WorkflowStage.MANUAL_REVIEW:
                    if workflow.total_entities > 0:
                        stage_progress = workflow.approved_entities / workflow.total_entities
                    else:
                        stage_progress = 0.0
                else:
                    stage_progress = 0.5  # Assume 50% for other stages

                base_progress += stage_weights[stage] * stage_progress
                break

        return min(base_progress, 1.0)

    # Persistence methods

    async def _save_workflow(self, workflow: WorkflowInstance):
        """Save workflow to disk."""
        try:
            workflow_file = self.workflows_dir / f"{workflow.workflow_id}.json"
            workflow_data = asdict(workflow)

            # Convert datetime and enum objects
            workflow_data["created_at"] = workflow.created_at.isoformat()
            workflow_data["updated_at"] = workflow.updated_at.isoformat()
            workflow_data["status"] = workflow.status.value
            workflow_data["current_stage"] = workflow.current_stage.value

            with open(workflow_file, 'w', encoding='utf-8') as f:
                json.dump(workflow_data, f, indent=2, ensure_ascii=False)

        except Exception as e:
            logger.error(f"Error saving workflow {workflow.workflow_id}: {e}")

    async def _load_workflow(self, workflow_id: str) -> Optional[WorkflowInstance]:
        """Load workflow from disk."""
        try:
            workflow_file = self.workflows_dir / f"{workflow_id}.json"
            if not workflow_file.exists():
                return None

            with open(workflow_file, 'r', encoding='utf-8') as f:
                workflow_data = json.load(f)

            # Convert ISO strings back to datetime objects
            workflow_data["created_at"] = datetime.fromisoformat(workflow_data["created_at"])
            workflow_data["updated_at"] = datetime.fromisoformat(workflow_data["updated_at"])
            workflow_data["status"] = WorkflowStatus(workflow_data["status"])
            workflow_data["current_stage"] = WorkflowStage(workflow_data["current_stage"])

            return WorkflowInstance(**workflow_data)

        except Exception as e:
            logger.error(f"Error loading workflow {workflow_id}: {e}")
            return None

    async def _load_existing_workflows(self):
        """Load existing workflows from disk."""
        try:
            for workflow_file in self.workflows_dir.glob("*.json"):
                workflow = await self._load_workflow(workflow_file.stem)
                if workflow and workflow.status == WorkflowStatus.ACTIVE:
                    self.active_workflows[workflow.workflow_id] = workflow

            logger.info(f"Loaded {len(self.active_workflows)} active workflows")

        except Exception as e:
            logger.error(f"Error loading existing workflows: {e}")

    # Public query methods

    async def get_all_workflows(self, user_id: str, status: Optional[str] = None) -> Dict[str, Any]:
        """Get all workflows for a user."""
        try:
            workflows = []

            # Get active workflows
            for workflow in self.active_workflows.values():
                if workflow.user_id == user_id:
                    if not status or workflow.status.value == status:
                        workflows.append(workflow)

            # Get completed workflows from disk
            for workflow_file in self.workflows_dir.glob("*.json"):
                if workflow_file.stem not in self.active_workflows:
                    workflow = await self._load_workflow(workflow_file.stem)
                    if workflow and workflow.user_id == user_id:
                        if not status or workflow.status.value == status:
                            workflows.append(workflow)

            # Sort by creation time (newest first)
            workflows.sort(key=lambda x: x.created_at, reverse=True)

            return {
                "success": True,
                "workflows": [
                    {
                        "workflow_id": w.workflow_id,
                        "name": w.name,
                        "description": w.description,
                        "status": w.status.value,
                        "current_stage": w.current_stage.value,
                        "created_at": w.created_at.isoformat(),
                        "updated_at": w.updated_at.isoformat(),
                        "total_documents": w.total_documents,
                        "processed_documents": w.processed_documents,
                        "total_entities": w.total_entities,
                        "approved_entities": w.approved_entities,
                        "conflicts_detected": w.conflicts_detected
                    }
                    for w in workflows
                ]
            }

        except Exception as e:
            logger.error(f"Error getting workflows for user {user_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }


# Global service instance
workflow_orchestration_service = WorkflowOrchestrationService()
