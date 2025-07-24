/**
 * Document Ingestion System - Frontend JavaScript
 * Handles file upload, processing monitoring, and real-time updates
 */

class DocumentIngestionSystem {
    constructor() {
        this.selectedFiles = new Map();
        this.activeJobs = new Map();
        this.websocket = null;
        this.currentMode = 'single';
        this.currentWorkflowId = null;
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.setupDropzone();
        this.setupWebSocket();
        this.loadExistingJobs();
        this.updateStats();
    }
    
    setupEventListeners() {
        // Workflow mode selection
        document.querySelectorAll('.workflow-option').forEach(option => {
            option.addEventListener('click', (e) => {
                this.selectWorkflowMode(e.target.closest('.workflow-option').dataset.mode);
            });
        });
        
        // File input
        const fileInput = document.getElementById('fileInput');
        if (fileInput) {
            fileInput.addEventListener('change', (e) => {
                this.handleFileSelection(e.target.files);
            });
        }
        
        // Process button
        const processBtn = document.getElementById('processBtn');
        if (processBtn) {
            processBtn.addEventListener('click', () => {
                this.startProcessing();
            });
        }
        
        // Clear button
        const clearBtn = document.getElementById('clearBtn');
        if (clearBtn) {
            clearBtn.addEventListener('click', () => {
                this.clearAllFiles();
            });
        }
        
        // Modal close handlers
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('close') || e.target.classList.contains('modal')) {
                this.closeModals();
            }
        });
        
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeModals();
            }
        });
    }
    
    setupDropzone() {
        const dropzone = document.getElementById('dropzone');
        if (!dropzone) return;
        
        // Prevent default drag behaviors
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropzone.addEventListener(eventName, this.preventDefaults, false);
            document.body.addEventListener(eventName, this.preventDefaults, false);
        });
        
        // Highlight drop area when item is dragged over it
        ['dragenter', 'dragover'].forEach(eventName => {
            dropzone.addEventListener(eventName, () => {
                dropzone.classList.add('dragover');
            }, false);
        });
        
        ['dragleave', 'drop'].forEach(eventName => {
            dropzone.addEventListener(eventName, () => {
                dropzone.classList.remove('dragover');
            }, false);
        });
        
        // Handle dropped files
        dropzone.addEventListener('drop', (e) => {
            const files = e.dataTransfer.files;
            this.handleFileSelection(files);
        }, false);
        
        // Handle click to browse
        dropzone.addEventListener('click', () => {
            document.getElementById('fileInput').click();
        });
    }
    
    preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    selectWorkflowMode(mode) {
        // Update UI
        document.querySelectorAll('.workflow-option').forEach(option => {
            option.classList.remove('selected');
        });
        document.querySelector(`[data-mode="${mode}"]`).classList.add('selected');
        
        this.currentMode = mode;
        
        // Update dropzone text based on mode
        const dropzoneTitle = document.querySelector('.dropzone h3');
        const dropzoneDesc = document.querySelector('.dropzone p');
        
        switch (mode) {
            case 'single':
                dropzoneTitle.textContent = 'Drop files here or click to browse';
                dropzoneDesc.textContent = 'Process individual documents with immediate review';
                break;
            case 'batch':
                dropzoneTitle.textContent = 'Drop multiple files for batch processing';
                dropzoneDesc.textContent = 'Upload multiple documents for automated processing';
                break;
            case 'workflow':
                dropzoneTitle.textContent = 'Add documents to workflow';
                dropzoneDesc.textContent = 'Upload documents to a managed workflow with approval stages';
                break;
        }
    }
    
    handleFileSelection(files) {
        const fileArray = Array.from(files);
        
        // Validate files
        const validFiles = fileArray.filter(file => this.validateFile(file));
        
        if (validFiles.length === 0) {
            this.showNotification('No valid files selected', 'warning');
            return;
        }
        
        // Add files to selection
        validFiles.forEach(file => {
            const fileId = this.generateFileId();
            this.selectedFiles.set(fileId, {
                id: fileId,
                file: file,
                name: file.name,
                size: file.size,
                type: file.type,
                lastModified: file.lastModified,
                metadata: {
                    title: file.name.replace(/\.[^/.]+$/, ""), // Remove extension
                    description: '',
                    source: 'upload'
                }
            });
        });
        
        this.updateFileList();
        this.updateProcessButton();
        
        this.showNotification(`${validFiles.length} file(s) added`, 'success');
    }
    
    validateFile(file) {
        // Check file size (max 50MB)
        const maxSize = 50 * 1024 * 1024;
        if (file.size > maxSize) {
            this.showNotification(`File ${file.name} is too large (max 50MB)`, 'error');
            return false;
        }
        
        // Check file type
        const allowedTypes = [
            'application/pdf',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'text/plain',
            'text/markdown'
        ];
        
        const allowedExtensions = ['.pdf', '.doc', '.docx', '.txt', '.md'];
        const fileExtension = file.name.toLowerCase().substring(file.name.lastIndexOf('.'));
        
        if (!allowedTypes.includes(file.type) && !allowedExtensions.includes(fileExtension)) {
            this.showNotification(`File type not supported: ${file.name}`, 'error');
            return false;
        }
        
        return true;
    }
    
    updateFileList() {
        const fileList = document.getElementById('fileList');
        const fileItems = document.getElementById('fileItems');
        
        if (this.selectedFiles.size === 0) {
            fileList.style.display = 'none';
            return;
        }
        
        fileList.style.display = 'block';
        fileItems.innerHTML = '';
        
        this.selectedFiles.forEach((fileData, fileId) => {
            const fileItem = this.createFileItem(fileData);
            fileItems.appendChild(fileItem);
        });
    }
    
    createFileItem(fileData) {
        const item = document.createElement('div');
        item.className = 'file-item';
        item.innerHTML = `
            <div class="file-icon">
                <i class="fas ${this.getFileIcon(fileData.file)}"></i>
            </div>
            <div class="file-info">
                <div class="file-name">${fileData.name}</div>
                <div class="file-details">
                    <span><i class="fas fa-weight-hanging"></i> ${this.formatFileSize(fileData.size)}</span>
                    <span><i class="fas fa-file-alt"></i> ${fileData.type || 'Unknown'}</span>
                    <span><i class="fas fa-clock"></i> ${new Date(fileData.lastModified).toLocaleString()}</span>
                </div>
            </div>
            <div class="file-actions">
                <button class="file-action-btn config-btn" onclick="documentIngestion.configureFile('${fileData.id}')">
                    <i class="fas fa-cog"></i> Configure
                </button>
                <button class="file-action-btn remove-btn" onclick="documentIngestion.removeFile('${fileData.id}')">
                    <i class="fas fa-trash"></i> Remove
                </button>
            </div>
        `;
        return item;
    }
    
    getFileIcon(file) {
        const type = file.type.toLowerCase();
        const name = file.name.toLowerCase();
        
        if (type.includes('pdf') || name.endsWith('.pdf')) return 'fa-file-pdf';
        if (type.includes('word') || name.endsWith('.doc') || name.endsWith('.docx')) return 'fa-file-word';
        if (type.includes('text') || name.endsWith('.txt')) return 'fa-file-alt';
        if (name.endsWith('.md')) return 'fa-file-code';
        
        return 'fa-file';
    }
    
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
    
    removeFile(fileId) {
        this.selectedFiles.delete(fileId);
        this.updateFileList();
        this.updateProcessButton();
        this.showNotification('File removed', 'info');
    }
    
    configureFile(fileId) {
        const fileData = this.selectedFiles.get(fileId);
        if (!fileData) return;
        
        // Show configuration modal (simplified for now)
        const title = prompt('Enter document title:', fileData.metadata.title);
        if (title !== null) {
            fileData.metadata.title = title;
        }
        
        const description = prompt('Enter document description:', fileData.metadata.description);
        if (description !== null) {
            fileData.metadata.description = description;
        }
        
        this.showNotification('File configuration updated', 'success');
    }
    
    updateProcessButton() {
        const processBtn = document.getElementById('processBtn');
        if (processBtn) {
            processBtn.disabled = this.selectedFiles.size === 0;
        }
    }
    
    clearAllFiles() {
        this.selectedFiles.clear();
        this.updateFileList();
        this.updateProcessButton();
        this.showNotification('All files cleared', 'info');
    }
    
    async startProcessing() {
        if (this.selectedFiles.size === 0) {
            this.showNotification('No files selected for processing', 'warning');
            return;
        }
        
        const config = this.getProcessingConfig();
        
        try {
            if (this.currentMode === 'workflow') {
                await this.processAsWorkflow(config);
            } else {
                await this.processIndividualFiles(config);
            }
        } catch (error) {
            console.error('Error starting processing:', error);
            this.showNotification('Failed to start processing', 'error');
        }
    }
    
    getProcessingConfig() {
        return {
            auto_approve_threshold: parseFloat(document.getElementById('autoApproveThreshold').value),
            chunk_size: parseInt(document.getElementById('chunkSize').value),
            priority: document.getElementById('priority').value,
            auto_resolve_conflicts: document.getElementById('autoResolveConflicts').value === 'true'
        };
    }
    
    async processIndividualFiles(config) {
        const uploadPromises = Array.from(this.selectedFiles.values()).map(async (fileData) => {
            try {
                const formData = new FormData();
                formData.append('file', fileData.file);
                formData.append('user_id', 'web_user');
                formData.append('priority', config.priority);
                formData.append('title', fileData.metadata.title);
                formData.append('description', fileData.metadata.description);
                formData.append('auto_approve_threshold', config.auto_approve_threshold);
                formData.append('chunk_size', config.chunk_size);
                
                const response = await fetch('/api/ingestion/upload', {
                    method: 'POST',
                    body: formData
                });
                
                const result = await response.json();
                
                if (result.success) {
                    this.activeJobs.set(result.job_id, {
                        job_id: result.job_id,
                        filename: result.filename,
                        status: result.status,
                        progress: 0,
                        stage: 'queued',
                        created_at: new Date().toISOString()
                    });
                    
                    this.showNotification(`Processing started for ${fileData.name}`, 'success');
                } else {
                    throw new Error(result.error);
                }
            } catch (error) {
                console.error(`Error uploading ${fileData.name}:`, error);
                this.showNotification(`Failed to upload ${fileData.name}: ${error.message}`, 'error');
            }
        });
        
        await Promise.all(uploadPromises);
        
        // Clear selected files after successful upload
        this.selectedFiles.clear();
        this.updateFileList();
        this.updateProcessButton();
        this.updateJobsList();
        this.updateStats();
    }
    
    async processAsWorkflow(config) {
        // Create workflow first
        try {
            const workflowResponse = await fetch('/api/workflows', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    user_id: 'web_user',
                    name: `Workflow ${new Date().toLocaleString()}`,
                    description: 'Auto-created workflow from document ingestion',
                    config: config
                })
            });
            
            const workflowResult = await workflowResponse.json();
            
            if (!workflowResult.success) {
                throw new Error(workflowResult.error);
            }
            
            this.currentWorkflowId = workflowResult.workflow_id;
            
            // Upload documents to workflow
            const formData = new FormData();
            formData.append('user_id', 'web_user');
            
            this.selectedFiles.forEach((fileData, index) => {
                formData.append(`file_${index}`, fileData.file);
                formData.append(`file_${index}_title`, fileData.metadata.title);
                formData.append(`file_${index}_description`, fileData.metadata.description);
            });
            
            const uploadResponse = await fetch(`/api/workflows/${this.currentWorkflowId}/upload`, {
                method: 'POST',
                body: formData
            });
            
            const uploadResult = await uploadResponse.json();
            
            if (uploadResult.success) {
                this.showNotification(`Workflow created with ${uploadResult.uploaded_count} documents`, 'success');
                
                // Track workflow jobs
                uploadResult.job_ids.forEach(jobId => {
                    this.activeJobs.set(jobId, {
                        job_id: jobId,
                        workflow_id: this.currentWorkflowId,
                        status: 'queued',
                        progress: 0,
                        stage: 'queued',
                        created_at: new Date().toISOString()
                    });
                });
                
                // Clear selected files
                this.selectedFiles.clear();
                this.updateFileList();
                this.updateProcessButton();
                this.updateJobsList();
                this.updateStats();
            } else {
                throw new Error(uploadResult.error);
            }
            
        } catch (error) {
            console.error('Error creating workflow:', error);
            this.showNotification(`Failed to create workflow: ${error.message}`, 'error');
        }
    }
    
    setupWebSocket() {
        // Note: This is a simplified WebSocket setup
        // In a real implementation, you'd use Socket.IO or similar
        try {
            // For now, we'll poll for updates instead of WebSocket
            this.startPolling();
        } catch (error) {
            console.error('WebSocket setup failed:', error);
            this.startPolling();
        }
    }
    
    startPolling() {
        // Poll for job updates every 5 seconds
        setInterval(() => {
            this.updateJobStatuses();
        }, 5000);
    }
    
    async updateJobStatuses() {
        if (this.activeJobs.size === 0) return;
        
        try {
            const response = await fetch('/api/ingestion/jobs?user_id=web_user');
            const result = await response.json();
            
            if (result.success) {
                result.jobs.forEach(job => {
                    if (this.activeJobs.has(job.job_id)) {
                        this.activeJobs.set(job.job_id, {
                            ...this.activeJobs.get(job.job_id),
                            ...job
                        });
                    }
                });
                
                this.updateJobsList();
                this.updateStats();
            }
        } catch (error) {
            console.error('Error updating job statuses:', error);
        }
    }
    
    async loadExistingJobs() {
        try {
            const response = await fetch('/api/ingestion/jobs?user_id=web_user');
            const result = await response.json();
            
            if (result.success) {
                result.jobs.forEach(job => {
                    if (!['completed', 'failed', 'cancelled'].includes(job.status)) {
                        this.activeJobs.set(job.job_id, job);
                    }
                });
                
                this.updateJobsList();
                this.updateStats();
            }
        } catch (error) {
            console.error('Error loading existing jobs:', error);
        }
    }
    
    updateJobsList() {
        const jobsList = document.getElementById('jobsList');
        if (!jobsList) return;
        
        if (this.activeJobs.size === 0) {
            jobsList.innerHTML = '<p class="text-center text-muted">No processing jobs yet</p>';
            return;
        }
        
        const jobsArray = Array.from(this.activeJobs.values());
        jobsArray.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
        
        jobsList.innerHTML = jobsArray.map(job => this.createJobItem(job)).join('');
    }
    
    createJobItem(job) {
        const statusIcon = this.getStatusIcon(job.status);
        const progressPercentage = Math.round((job.progress || 0) * 100);
        
        return `
            <div class="job-item">
                <div class="job-icon ${job.status}">
                    <i class="fas ${statusIcon}"></i>
                </div>
                <div class="job-info">
                    <div class="job-name">${job.filename || 'Unknown Document'}</div>
                    <div class="job-status">${job.stage || job.status} - ${progressPercentage}%</div>
                    <div class="job-progress">
                        <div class="job-progress-fill ${job.status}" style="width: ${progressPercentage}%"></div>
                    </div>
                </div>
                <div class="job-actions">
                    <button class="job-action-btn view-btn" onclick="documentIngestion.viewJobDetails('${job.job_id}')">
                        <i class="fas fa-eye"></i> View
                    </button>
                    ${job.status === 'processing' || job.status === 'queued' ? 
                        `<button class="job-action-btn cancel-btn" onclick="documentIngestion.cancelJob('${job.job_id}')">
                            <i class="fas fa-stop"></i> Cancel
                        </button>` : ''}
                    ${job.status === 'failed' ? 
                        `<button class="job-action-btn reprocess-btn" onclick="documentIngestion.reprocessJob('${job.job_id}')">
                            <i class="fas fa-redo"></i> Retry
                        </button>` : ''}
                </div>
            </div>
        `;
    }
    
    getStatusIcon(status) {
        const icons = {
            'queued': 'fa-clock',
            'processing': 'fa-spinner',
            'completed': 'fa-check-circle',
            'failed': 'fa-exclamation-circle',
            'cancelled': 'fa-ban'
        };
        return icons[status] || 'fa-question-circle';
    }
    
    updateStats() {
        const activeCount = Array.from(this.activeJobs.values()).filter(job => 
            ['queued', 'processing'].includes(job.status)
        ).length;
        
        const completedCount = Array.from(this.activeJobs.values()).filter(job => 
            job.status === 'completed'
        ).length;
        
        const failedCount = Array.from(this.activeJobs.values()).filter(job => 
            job.status === 'failed'
        ).length;
        
        document.getElementById('activeJobs').textContent = activeCount;
        document.getElementById('completedJobs').textContent = completedCount;
        document.getElementById('failedJobs').textContent = failedCount;
    }
    
    async viewJobDetails(jobId) {
        try {
            const response = await fetch(`/api/ingestion/jobs/${jobId}`);
            const result = await response.json();
            
            if (result.success) {
                this.showJobDetailsModal(result.job);
            } else {
                this.showNotification('Failed to load job details', 'error');
            }
        } catch (error) {
            console.error('Error loading job details:', error);
            this.showNotification('Failed to load job details', 'error');
        }
    }
    
    showJobDetailsModal(job) {
        const modal = document.getElementById('jobDetailsModal');
        const content = document.getElementById('jobDetailsContent');
        
        content.innerHTML = `
            <div class="job-details">
                <h4>${job.filename}</h4>
                <div class="detail-grid">
                    <div><strong>Status:</strong> ${job.status}</div>
                    <div><strong>Progress:</strong> ${Math.round(job.progress * 100)}%</div>
                    <div><strong>Stage:</strong> ${job.stage}</div>
                    <div><strong>Created:</strong> ${new Date(job.created_at).toLocaleString()}</div>
                    <div><strong>Updated:</strong> ${new Date(job.updated_at).toLocaleString()}</div>
                    <div><strong>Entities:</strong> ${job.entities_extracted || 0}</div>
                    <div><strong>Relationships:</strong> ${job.relationships_extracted || 0}</div>
                    <div><strong>File Size:</strong> ${this.formatFileSize(job.file_size)}</div>
                </div>
                ${job.error_message ? `<div class="error-message"><strong>Error:</strong> ${job.error_message}</div>` : ''}
                ${job.session_id ? `<div class="session-link"><a href="/entity-management?session=${job.session_id}" target="_blank">View in Entity Management</a></div>` : ''}
            </div>
        `;
        
        modal.style.display = 'block';
    }
    
    async cancelJob(jobId) {
        if (!confirm('Are you sure you want to cancel this job?')) return;
        
        try {
            const response = await fetch(`/api/ingestion/jobs/${jobId}/cancel`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    user_id: 'web_user'
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showNotification('Job cancelled successfully', 'success');
                this.updateJobStatuses();
            } else {
                this.showNotification('Failed to cancel job', 'error');
            }
        } catch (error) {
            console.error('Error cancelling job:', error);
            this.showNotification('Failed to cancel job', 'error');
        }
    }
    
    async reprocessJob(jobId) {
        if (!confirm('Are you sure you want to reprocess this document?')) return;
        
        try {
            const response = await fetch(`/api/ingestion/jobs/${jobId}/reprocess`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    user_id: 'web_user'
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showNotification('Document queued for reprocessing', 'success');
                this.activeJobs.set(result.new_job_id, {
                    job_id: result.new_job_id,
                    status: 'queued',
                    progress: 0,
                    stage: 'queued',
                    created_at: new Date().toISOString()
                });
                this.updateJobsList();
                this.updateStats();
            } else {
                this.showNotification('Failed to reprocess document', 'error');
            }
        } catch (error) {
            console.error('Error reprocessing job:', error);
            this.showNotification('Failed to reprocess document', 'error');
        }
    }
    
    closeModals() {
        document.querySelectorAll('.modal').forEach(modal => {
            modal.style.display = 'none';
        });
    }
    
    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.innerHTML = `
            <i class="fas fa-${type === 'success' ? 'check' : type === 'error' ? 'times' : type === 'warning' ? 'exclamation' : 'info'}-circle"></i>
            <span>${message}</span>
        `;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 5000);
    }
    
    generateFileId() {
        return 'file_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.documentIngestion = new DocumentIngestionSystem();
});

// Export for module use
window.DocumentIngestionSystem = DocumentIngestionSystem;
