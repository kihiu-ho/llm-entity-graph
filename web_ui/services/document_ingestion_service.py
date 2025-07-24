"""
Document Ingestion Service - Web-based replacement for CLI graph_builder.py workflow
Provides complete document processing pipeline with real-time progress tracking
"""

import os
import json
import uuid
import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum

# Import existing ingestion components
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ingestion.graph_builder import GraphBuilder
from ingestion.chunker import SemanticChunker, ChunkingConfig, DocumentChunk
from ingestion.ingest import DocumentProcessor, IngestionConfig

logger = logging.getLogger(__name__)


class ProcessingStatus(Enum):
    """Document processing status enumeration."""
    QUEUED = "queued"
    UPLOADING = "uploading"
    UPLOADED = "uploaded"
    CHUNKING = "chunking"
    EXTRACTING = "extracting"
    STAGING = "staging"
    STAGED = "staged"
    REVIEWING = "reviewing"
    APPROVED = "approved"
    INGESTING = "ingesting"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ProcessingJob:
    """Represents a document processing job."""
    job_id: str
    document_id: str
    filename: str
    file_path: str
    file_size: int
    mime_type: str
    status: ProcessingStatus
    progress: float  # 0.0 to 1.0
    stage: str
    stage_progress: float
    created_at: datetime
    updated_at: datetime
    user_id: str
    session_id: Optional[str] = None
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    processing_config: Optional[Dict[str, Any]] = None
    
    # Processing results
    chunks_created: int = 0
    entities_extracted: int = 0
    relationships_extracted: int = 0
    conflicts_detected: int = 0
    
    # Timing information
    upload_duration: Optional[float] = None
    chunking_duration: Optional[float] = None
    extraction_duration: Optional[float] = None
    total_duration: Optional[float] = None


class DocumentIngestionService:
    """Service for managing document ingestion workflow."""
    
    def __init__(self, upload_dir: str = "uploads", staging_dir: str = "staging/data"):
        self.upload_dir = Path(upload_dir)
        self.staging_dir = Path(staging_dir)
        self.jobs_dir = Path("staging/jobs")
        
        # Create directories
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.staging_dir.mkdir(parents=True, exist_ok=True)
        self.jobs_dir.mkdir(parents=True, exist_ok=True)
        
        # Active jobs tracking
        self.active_jobs: Dict[str, ProcessingJob] = {}
        self.job_queues: Dict[str, asyncio.Queue] = {
            "high": asyncio.Queue(),
            "normal": asyncio.Queue(),
            "low": asyncio.Queue()
        }
        
        # Processing components
        self.graph_builder = None
        self.chunker = None
        self.document_processor = None
        
        # WebSocket connections for real-time updates
        self.websocket_connections: Dict[str, List] = {}
        
        self._initialized = False
        self._processing_tasks = []
    
    async def initialize(self):
        """Initialize the ingestion service."""
        if not self._initialized:
            logger.info("Initializing Document Ingestion Service")
            
            # Initialize processing components
            self.graph_builder = GraphBuilder()
            await self.graph_builder.initialize()
            
            # Initialize chunker with default config
            chunking_config = ChunkingConfig(
                chunk_size=8000,
                chunk_overlap=800,
                use_semantic_splitting=True,
                preserve_structure=True
            )
            self.chunker = SemanticChunker(chunking_config)
            
            # Initialize document processor
            ingestion_config = IngestionConfig(
                skip_graph_building=False,
                use_entity_staging=True,
                batch_size=3
            )
            self.document_processor = DocumentProcessor(ingestion_config)
            await self.document_processor.initialize()
            
            # Start processing workers
            await self._start_processing_workers()
            
            # Load existing jobs
            await self._load_existing_jobs()
            
            self._initialized = True
            logger.info("Document Ingestion Service initialized successfully")
    
    async def close(self):
        """Close the ingestion service."""
        if self._initialized:
            # Cancel processing tasks
            for task in self._processing_tasks:
                task.cancel()
            
            # Close components
            if self.graph_builder:
                await self.graph_builder.close()
            
            if self.document_processor:
                await self.document_processor.close()
            
            self._initialized = False
    
    async def upload_document(
        self,
        file_data: bytes,
        filename: str,
        mime_type: str,
        user_id: str,
        metadata: Optional[Dict[str, Any]] = None,
        processing_config: Optional[Dict[str, Any]] = None,
        priority: str = "normal"
    ) -> Dict[str, Any]:
        """
        Upload and queue a document for processing.
        
        Args:
            file_data: Document file data
            filename: Original filename
            mime_type: MIME type of the file
            user_id: ID of the user uploading
            metadata: Additional metadata
            processing_config: Processing configuration
            priority: Processing priority (high, normal, low)
        
        Returns:
            Upload result with job ID
        """
        try:
            # Generate IDs
            job_id = str(uuid.uuid4())
            document_id = str(uuid.uuid4())
            
            # Validate file
            validation_result = self._validate_file(file_data, filename, mime_type)
            if not validation_result["valid"]:
                return {
                    "success": False,
                    "error": validation_result["error"]
                }
            
            # Save file
            file_path = self.upload_dir / f"{document_id}_{filename}"
            with open(file_path, 'wb') as f:
                f.write(file_data)
            
            # Create processing job
            job = ProcessingJob(
                job_id=job_id,
                document_id=document_id,
                filename=filename,
                file_path=str(file_path),
                file_size=len(file_data),
                mime_type=mime_type,
                status=ProcessingStatus.QUEUED,
                progress=0.0,
                stage="queued",
                stage_progress=0.0,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                user_id=user_id,
                metadata=metadata or {},
                processing_config=processing_config or {}
            )
            
            # Save job
            await self._save_job(job)
            self.active_jobs[job_id] = job
            
            # Queue for processing
            await self.job_queues[priority].put(job_id)
            
            # Notify WebSocket connections
            await self._notify_job_update(job)
            
            logger.info(f"Document uploaded and queued: {filename} (Job ID: {job_id})")
            
            return {
                "success": True,
                "job_id": job_id,
                "document_id": document_id,
                "filename": filename,
                "file_size": len(file_data),
                "status": job.status.value,
                "message": "Document uploaded and queued for processing"
            }
            
        except Exception as e:
            logger.error(f"Error uploading document {filename}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Get the status of a processing job."""
        try:
            job = self.active_jobs.get(job_id)
            if not job:
                # Try to load from disk
                job = await self._load_job(job_id)
            
            if not job:
                return {
                    "success": False,
                    "error": "Job not found"
                }
            
            return {
                "success": True,
                "job": {
                    "job_id": job.job_id,
                    "document_id": job.document_id,
                    "filename": job.filename,
                    "status": job.status.value,
                    "progress": job.progress,
                    "stage": job.stage,
                    "stage_progress": job.stage_progress,
                    "created_at": job.created_at.isoformat(),
                    "updated_at": job.updated_at.isoformat(),
                    "session_id": job.session_id,
                    "error_message": job.error_message,
                    "chunks_created": job.chunks_created,
                    "entities_extracted": job.entities_extracted,
                    "relationships_extracted": job.relationships_extracted,
                    "conflicts_detected": job.conflicts_detected,
                    "upload_duration": job.upload_duration,
                    "chunking_duration": job.chunking_duration,
                    "extraction_duration": job.extraction_duration,
                    "total_duration": job.total_duration
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting job status {job_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_all_jobs(self, user_id: Optional[str] = None, status: Optional[str] = None) -> Dict[str, Any]:
        """Get all processing jobs with optional filtering."""
        try:
            jobs = []
            
            # Get active jobs
            for job in self.active_jobs.values():
                if user_id and job.user_id != user_id:
                    continue
                if status and job.status.value != status:
                    continue
                jobs.append(job)
            
            # Get completed jobs from disk
            for job_file in self.jobs_dir.glob("*.json"):
                if job_file.stem not in self.active_jobs:
                    try:
                        job = await self._load_job(job_file.stem)
                        if job:
                            if user_id and job.user_id != user_id:
                                continue
                            if status and job.status.value != status:
                                continue
                            jobs.append(job)
                    except Exception as e:
                        logger.error(f"Error loading job {job_file}: {e}")
            
            # Sort by creation time (newest first)
            jobs.sort(key=lambda x: x.created_at, reverse=True)
            
            return {
                "success": True,
                "jobs": [
                    {
                        "job_id": job.job_id,
                        "document_id": job.document_id,
                        "filename": job.filename,
                        "status": job.status.value,
                        "progress": job.progress,
                        "stage": job.stage,
                        "created_at": job.created_at.isoformat(),
                        "updated_at": job.updated_at.isoformat(),
                        "user_id": job.user_id,
                        "session_id": job.session_id,
                        "entities_extracted": job.entities_extracted,
                        "relationships_extracted": job.relationships_extracted,
                        "file_size": job.file_size
                    }
                    for job in jobs
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting all jobs: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def cancel_job(self, job_id: str, user_id: str) -> Dict[str, Any]:
        """Cancel a processing job."""
        try:
            job = self.active_jobs.get(job_id)
            if not job:
                return {
                    "success": False,
                    "error": "Job not found"
                }
            
            # Check permissions
            if job.user_id != user_id:
                return {
                    "success": False,
                    "error": "Permission denied"
                }
            
            # Check if job can be cancelled
            if job.status in [ProcessingStatus.COMPLETED, ProcessingStatus.FAILED, ProcessingStatus.CANCELLED]:
                return {
                    "success": False,
                    "error": f"Cannot cancel job in {job.status.value} status"
                }
            
            # Update job status
            job.status = ProcessingStatus.CANCELLED
            job.updated_at = datetime.now()
            job.error_message = "Cancelled by user"
            
            await self._save_job(job)
            await self._notify_job_update(job)
            
            logger.info(f"Job cancelled: {job_id}")
            
            return {
                "success": True,
                "message": "Job cancelled successfully"
            }
            
        except Exception as e:
            logger.error(f"Error cancelling job {job_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def reprocess_document(self, job_id: str, user_id: str, new_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Reprocess a failed or completed document."""
        try:
            job = self.active_jobs.get(job_id)
            if not job:
                job = await self._load_job(job_id)
            
            if not job:
                return {
                    "success": False,
                    "error": "Job not found"
                }
            
            # Check permissions
            if job.user_id != user_id:
                return {
                    "success": False,
                    "error": "Permission denied"
                }
            
            # Create new job for reprocessing
            new_job_id = str(uuid.uuid4())
            new_job = ProcessingJob(
                job_id=new_job_id,
                document_id=job.document_id,
                filename=f"REPROCESS_{job.filename}",
                file_path=job.file_path,
                file_size=job.file_size,
                mime_type=job.mime_type,
                status=ProcessingStatus.QUEUED,
                progress=0.0,
                stage="queued",
                stage_progress=0.0,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                user_id=user_id,
                metadata=job.metadata,
                processing_config=new_config or job.processing_config
            )
            
            # Save and queue new job
            await self._save_job(new_job)
            self.active_jobs[new_job_id] = new_job
            await self.job_queues["normal"].put(new_job_id)
            
            await self._notify_job_update(new_job)
            
            return {
                "success": True,
                "new_job_id": new_job_id,
                "message": "Document queued for reprocessing"
            }
            
        except Exception as e:
            logger.error(f"Error reprocessing job {job_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    # WebSocket management
    
    async def register_websocket(self, websocket, user_id: str):
        """Register a WebSocket connection for real-time updates."""
        if user_id not in self.websocket_connections:
            self.websocket_connections[user_id] = []
        self.websocket_connections[user_id].append(websocket)
        logger.info(f"WebSocket registered for user {user_id}")
    
    async def unregister_websocket(self, websocket, user_id: str):
        """Unregister a WebSocket connection."""
        if user_id in self.websocket_connections:
            try:
                self.websocket_connections[user_id].remove(websocket)
                if not self.websocket_connections[user_id]:
                    del self.websocket_connections[user_id]
            except ValueError:
                pass
        logger.info(f"WebSocket unregistered for user {user_id}")
    
    async def _notify_job_update(self, job: ProcessingJob):
        """Notify WebSocket connections about job updates."""
        if job.user_id in self.websocket_connections:
            message = {
                "type": "job_update",
                "job_id": job.job_id,
                "status": job.status.value,
                "progress": job.progress,
                "stage": job.stage,
                "stage_progress": job.stage_progress,
                "updated_at": job.updated_at.isoformat(),
                "entities_extracted": job.entities_extracted,
                "relationships_extracted": job.relationships_extracted,
                "error_message": job.error_message
            }
            
            # Send to all connections for this user
            connections_to_remove = []
            for websocket in self.websocket_connections[job.user_id]:
                try:
                    await websocket.send_text(json.dumps(message))
                except Exception as e:
                    logger.error(f"Error sending WebSocket message: {e}")
                    connections_to_remove.append(websocket)
            
            # Remove failed connections
            for websocket in connections_to_remove:
                await self.unregister_websocket(websocket, job.user_id)

    # Private processing methods

    async def _start_processing_workers(self):
        """Start background processing workers."""
        # Start workers for each priority queue
        for priority in ["high", "normal", "low"]:
            task = asyncio.create_task(self._processing_worker(priority))
            self._processing_tasks.append(task)

        logger.info("Processing workers started")

    async def _processing_worker(self, priority: str):
        """Background worker for processing documents."""
        queue = self.job_queues[priority]

        while True:
            try:
                # Get next job from queue
                job_id = await queue.get()

                # Process the job
                await self._process_document_job(job_id)

                # Mark task as done
                queue.task_done()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in processing worker ({priority}): {e}")
                await asyncio.sleep(1)  # Brief pause before continuing

    async def _process_document_job(self, job_id: str):
        """Process a single document job."""
        job = self.active_jobs.get(job_id)
        if not job:
            logger.error(f"Job {job_id} not found in active jobs")
            return

        start_time = datetime.now()

        try:
            logger.info(f"Starting processing for job {job_id}: {job.filename}")

            # Update status to processing
            await self._update_job_status(job, ProcessingStatus.UPLOADING, "Reading document", 0.1)

            # Read document content
            document_content = await self._read_document(job)
            if not document_content:
                raise Exception("Failed to read document content")

            # Chunking phase
            await self._update_job_status(job, ProcessingStatus.CHUNKING, "Creating document chunks", 0.2)
            chunk_start = datetime.now()

            chunks = await self._chunk_document(job, document_content)
            job.chunks_created = len(chunks)
            job.chunking_duration = (datetime.now() - chunk_start).total_seconds()

            # Entity extraction phase
            await self._update_job_status(job, ProcessingStatus.EXTRACTING, "Extracting entities and relationships", 0.4)
            extraction_start = datetime.now()

            extraction_result = await self._extract_entities(job, chunks)
            job.entities_extracted = extraction_result.get("entities_extracted", 0)
            job.relationships_extracted = extraction_result.get("relationships_extracted", 0)
            job.session_id = extraction_result.get("session_id")
            job.extraction_duration = (datetime.now() - extraction_start).total_seconds()

            # Staging phase
            await self._update_job_status(job, ProcessingStatus.STAGING, "Staging for review", 0.8)

            # Detect conflicts
            if job.session_id:
                conflicts_result = await self._detect_conflicts(job.session_id)
                job.conflicts_detected = conflicts_result.get("total_conflicts", 0)

            # Complete processing
            await self._update_job_status(job, ProcessingStatus.STAGED, "Ready for review", 1.0)

            job.total_duration = (datetime.now() - start_time).total_seconds()

            logger.info(f"Processing completed for job {job_id}: {job.entities_extracted} entities, {job.relationships_extracted} relationships")

        except Exception as e:
            logger.error(f"Error processing job {job_id}: {e}")
            job.status = ProcessingStatus.FAILED
            job.error_message = str(e)
            job.updated_at = datetime.now()

            await self._save_job(job)
            await self._notify_job_update(job)

    async def _read_document(self, job: ProcessingJob) -> Optional[str]:
        """Read and extract text content from document."""
        try:
            file_path = Path(job.file_path)

            if job.mime_type == "text/plain":
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()

            elif job.mime_type == "text/markdown":
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()

            elif job.mime_type == "application/pdf":
                # Use PyPDF2 or similar for PDF extraction
                try:
                    import PyPDF2
                    with open(file_path, 'rb') as f:
                        reader = PyPDF2.PdfReader(f)
                        text = ""
                        for page in reader.pages:
                            text += page.extract_text() + "\n"
                        return text
                except ImportError:
                    logger.warning("PyPDF2 not available for PDF processing")
                    return None

            elif job.mime_type in ["application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]:
                # Use python-docx for Word documents
                try:
                    import docx
                    doc = docx.Document(file_path)
                    text = ""
                    for paragraph in doc.paragraphs:
                        text += paragraph.text + "\n"
                    return text
                except ImportError:
                    logger.warning("python-docx not available for Word processing")
                    return None

            else:
                # Try to read as text
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        return f.read()
                except UnicodeDecodeError:
                    logger.error(f"Unsupported file type: {job.mime_type}")
                    return None

        except Exception as e:
            logger.error(f"Error reading document {job.file_path}: {e}")
            return None

    async def _chunk_document(self, job: ProcessingJob, content: str) -> List[DocumentChunk]:
        """Chunk the document content."""
        try:
            # Extract title from filename or metadata
            title = job.metadata.get("title", job.filename)
            source = job.metadata.get("source", f"upload_{job.document_id}")

            # Use the chunker to create chunks
            chunks = await self.chunker.chunk_document(
                content=content,
                title=title,
                source=source,
                metadata={
                    "job_id": job.job_id,
                    "document_id": job.document_id,
                    "filename": job.filename,
                    "user_id": job.user_id,
                    **job.metadata
                }
            )

            return chunks

        except Exception as e:
            logger.error(f"Error chunking document for job {job.job_id}: {e}")
            raise

    async def _extract_entities(self, job: ProcessingJob, chunks: List[DocumentChunk]) -> Dict[str, Any]:
        """Extract entities and relationships from document chunks."""
        try:
            # Get processing configuration
            config = job.processing_config or {}

            # Extract entities using the graph builder
            result = await self.graph_builder.stage_document_entities(
                chunks=chunks,
                document_title=job.metadata.get("title", job.filename),
                document_source=f"upload_{job.document_id}",
                document_metadata={
                    "job_id": job.job_id,
                    "document_id": job.document_id,
                    "filename": job.filename,
                    "user_id": job.user_id,
                    "upload_time": job.created_at.isoformat(),
                    **job.metadata
                },
                use_staging=True
            )

            return result

        except Exception as e:
            logger.error(f"Error extracting entities for job {job.job_id}: {e}")
            raise

    async def _detect_conflicts(self, session_id: str) -> Dict[str, Any]:
        """Detect conflicts in the extracted entities."""
        try:
            from .conflict_detection_service import conflict_detection_service

            conflicts_result = await conflict_detection_service.detect_session_conflicts(session_id)
            return conflicts_result

        except Exception as e:
            logger.error(f"Error detecting conflicts for session {session_id}: {e}")
            return {"total_conflicts": 0}

    async def _update_job_status(self, job: ProcessingJob, status: ProcessingStatus, stage: str, progress: float):
        """Update job status and notify connections."""
        job.status = status
        job.stage = stage
        job.progress = progress
        job.stage_progress = progress
        job.updated_at = datetime.now()

        await self._save_job(job)
        await self._notify_job_update(job)

    # File validation and management

    def _validate_file(self, file_data: bytes, filename: str, mime_type: str) -> Dict[str, Any]:
        """Validate uploaded file."""
        # Check file size (max 50MB)
        max_size = 50 * 1024 * 1024  # 50MB
        if len(file_data) > max_size:
            return {
                "valid": False,
                "error": f"File size ({len(file_data)} bytes) exceeds maximum allowed size ({max_size} bytes)"
            }

        # Check file extension
        allowed_extensions = {
            ".txt", ".md", ".pdf", ".doc", ".docx", ".rtf"
        }
        file_ext = Path(filename).suffix.lower()
        if file_ext not in allowed_extensions:
            return {
                "valid": False,
                "error": f"File type {file_ext} not supported. Allowed types: {', '.join(allowed_extensions)}"
            }

        # Check MIME type
        allowed_mime_types = {
            "text/plain",
            "text/markdown",
            "application/pdf",
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/rtf"
        }
        if mime_type not in allowed_mime_types:
            return {
                "valid": False,
                "error": f"MIME type {mime_type} not supported"
            }

        # Check for empty file
        if len(file_data) == 0:
            return {
                "valid": False,
                "error": "File is empty"
            }

        return {"valid": True}

    # Job persistence

    async def _save_job(self, job: ProcessingJob):
        """Save job to disk."""
        try:
            job_file = self.jobs_dir / f"{job.job_id}.json"
            job_data = asdict(job)

            # Convert datetime objects to ISO strings
            job_data["created_at"] = job.created_at.isoformat()
            job_data["updated_at"] = job.updated_at.isoformat()
            job_data["status"] = job.status.value

            with open(job_file, 'w', encoding='utf-8') as f:
                json.dump(job_data, f, indent=2, ensure_ascii=False)

        except Exception as e:
            logger.error(f"Error saving job {job.job_id}: {e}")

    async def _load_job(self, job_id: str) -> Optional[ProcessingJob]:
        """Load job from disk."""
        try:
            job_file = self.jobs_dir / f"{job_id}.json"
            if not job_file.exists():
                return None

            with open(job_file, 'r', encoding='utf-8') as f:
                job_data = json.load(f)

            # Convert ISO strings back to datetime objects
            job_data["created_at"] = datetime.fromisoformat(job_data["created_at"])
            job_data["updated_at"] = datetime.fromisoformat(job_data["updated_at"])
            job_data["status"] = ProcessingStatus(job_data["status"])

            return ProcessingJob(**job_data)

        except Exception as e:
            logger.error(f"Error loading job {job_id}: {e}")
            return None

    async def _load_existing_jobs(self):
        """Load existing jobs from disk."""
        try:
            for job_file in self.jobs_dir.glob("*.json"):
                job = await self._load_job(job_file.stem)
                if job and job.status not in [ProcessingStatus.COMPLETED, ProcessingStatus.FAILED, ProcessingStatus.CANCELLED]:
                    self.active_jobs[job.job_id] = job

                    # Re-queue incomplete jobs
                    if job.status == ProcessingStatus.QUEUED:
                        await self.job_queues["normal"].put(job.job_id)

            logger.info(f"Loaded {len(self.active_jobs)} existing jobs")

        except Exception as e:
            logger.error(f"Error loading existing jobs: {e}")


# Global service instance
document_ingestion_service = DocumentIngestionService()
