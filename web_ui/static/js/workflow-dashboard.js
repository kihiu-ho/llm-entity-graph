/**
 * Workflow Dashboard - Frontend JavaScript
 * Manages workflow creation, monitoring, and control
 */

class WorkflowDashboard {
    constructor() {
        this.workflows = new Map();
        this.currentFilter = '';
        this.searchQuery = '';
        this.refreshInterval = null;
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.loadWorkflows();
        this.loadActivityTimeline();
        this.startAutoRefresh();
    }
    
    setupEventListeners() {
        // Filter and search
        const statusFilter = document.getElementById('statusFilter');
        const searchInput = document.getElementById('searchInput');
        
        if (statusFilter) {
            statusFilter.addEventListener('change', (e) => {
                this.currentFilter = e.target.value;
                this.filterWorkflows();
            });
        }
        
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                this.searchQuery = e.target.value;
                this.filterWorkflows();
            });
        }
        
        // Action buttons
        const createWorkflowBtn = document.getElementById('createWorkflowBtn');
        const uploadDocumentsBtn = document.getElementById('uploadDocumentsBtn');
        const refreshBtn = document.getElementById('refreshBtn');
        const refreshTimelineBtn = document.getElementById('refreshTimelineBtn');
        
        if (createWorkflowBtn) {
            createWorkflowBtn.addEventListener('click', () => {
                this.showCreateWorkflowModal();
            });
        }
        
        if (uploadDocumentsBtn) {
            uploadDocumentsBtn.addEventListener('click', () => {
                window.location.href = '/document-ingestion';
            });
        }
        
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                this.loadWorkflows();
            });
        }
        
        if (refreshTimelineBtn) {
            refreshTimelineBtn.addEventListener('click', () => {
                this.loadActivityTimeline();
            });
        }
        
        // Modal handlers
        this.setupModalHandlers();
        
        // Form submission
        const createWorkflowForm = document.getElementById('createWorkflowForm');
        if (createWorkflowForm) {
            createWorkflowForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.createWorkflow();
            });
        }
    }
    
    setupModalHandlers() {
        // Close modal handlers
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
        
        // Cancel buttons
        const createWorkflowCancel = document.getElementById('createWorkflowCancel');
        if (createWorkflowCancel) {
            createWorkflowCancel.addEventListener('click', () => {
                this.closeModals();
            });
        }
    }
    
    async loadWorkflows() {
        try {
            this.showLoadingState();
            
            const response = await fetch('/api/workflows?user_id=web_user');
            const result = await response.json();
            
            if (result.success) {
                this.workflows.clear();
                result.workflows.forEach(workflow => {
                    this.workflows.set(workflow.workflow_id, workflow);
                });
                
                this.renderWorkflows();
            } else {
                throw new Error(result.error);
            }
        } catch (error) {
            console.error('Error loading workflows:', error);
            this.showErrorState('Failed to load workflows');
        }
    }
    
    renderWorkflows() {
        const workflowsGrid = document.getElementById('workflowsGrid');
        if (!workflowsGrid) return;
        
        const workflows = Array.from(this.workflows.values());
        
        if (workflows.length === 0) {
            workflowsGrid.innerHTML = this.createEmptyState();
            return;
        }
        
        // Apply filters
        const filteredWorkflows = this.applyFilters(workflows);
        
        if (filteredWorkflows.length === 0) {
            workflowsGrid.innerHTML = this.createEmptyState('No workflows match your filters');
            return;
        }
        
        // Sort by creation time (newest first)
        filteredWorkflows.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
        
        workflowsGrid.innerHTML = filteredWorkflows.map(workflow => 
            this.createWorkflowCard(workflow)
        ).join('');
    }
    
    applyFilters(workflows) {
        return workflows.filter(workflow => {
            // Status filter
            if (this.currentFilter && workflow.status !== this.currentFilter) {
                return false;
            }
            
            // Search filter
            if (this.searchQuery) {
                const query = this.searchQuery.toLowerCase();
                return workflow.name.toLowerCase().includes(query) ||
                       workflow.description.toLowerCase().includes(query);
            }
            
            return true;
        });
    }
    
    createWorkflowCard(workflow) {
        const progress = this.calculateProgress(workflow);
        const progressPercentage = Math.round(progress * 100);
        
        return `
            <div class="workflow-card">
                <div class="stage-indicator"></div>
                <div class="workflow-header-card">
                    <div>
                        <h3 class="workflow-title">${workflow.name}</h3>
                        <p class="workflow-description">${workflow.description || 'No description'}</p>
                    </div>
                    <span class="workflow-status status-${workflow.status}">${workflow.status}</span>
                </div>
                
                <div class="workflow-progress">
                    <div class="progress-label">
                        <span class="progress-text">${workflow.current_stage.replace('_', ' ')}</span>
                        <span class="progress-percentage">${progressPercentage}%</span>
                    </div>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${progressPercentage}%"></div>
                    </div>
                </div>
                
                <div class="workflow-stats">
                    <div class="stat-item">
                        <div class="stat-number">${workflow.total_documents}</div>
                        <div class="stat-label">Documents</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-number">${workflow.total_entities}</div>
                        <div class="stat-label">Entities</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-number">${workflow.approved_entities}</div>
                        <div class="stat-label">Approved</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-number">${workflow.conflicts_detected}</div>
                        <div class="stat-label">Conflicts</div>
                    </div>
                </div>
                
                <div class="workflow-actions">
                    <button class="action-btn view-btn" onclick="workflowDashboard.viewWorkflow('${workflow.workflow_id}')">
                        <i class="fas fa-eye"></i> View
                    </button>
                    ${this.getWorkflowActions(workflow)}
                </div>
            </div>
        `;
    }
    
    getWorkflowActions(workflow) {
        const actions = [];
        
        switch (workflow.current_stage) {
            case 'manual_review':
                actions.push(`
                    <button class="action-btn approve-btn" onclick="workflowDashboard.approveWorkflow('${workflow.workflow_id}')">
                        <i class="fas fa-check"></i> Approve
                    </button>
                `);
                break;
            
            case 'entity_approval':
            case 'neo4j_ingestion':
                actions.push(`
                    <button class="action-btn ingest-btn" onclick="workflowDashboard.ingestWorkflow('${workflow.workflow_id}')">
                        <i class="fas fa-database"></i> Ingest
                    </button>
                `);
                break;
        }
        
        if (workflow.status === 'active') {
            actions.push(`
                <button class="action-btn cancel-btn" onclick="workflowDashboard.cancelWorkflow('${workflow.workflow_id}')">
                    <i class="fas fa-stop"></i> Cancel
                </button>
            `);
        }
        
        return actions.join('');
    }
    
    calculateProgress(workflow) {
        const stageWeights = {
            'document_upload': 0.1,
            'document_processing': 0.3,
            'entity_staging': 0.1,
            'conflict_detection': 0.1,
            'manual_review': 0.2,
            'entity_approval': 0.1,
            'neo4j_ingestion': 0.1,
            'completed': 1.0
        };
        
        const stages = Object.keys(stageWeights);
        const currentStageIndex = stages.indexOf(workflow.current_stage);
        
        if (currentStageIndex === -1) return 0;
        
        let progress = 0;
        
        // Add completed stages
        for (let i = 0; i < currentStageIndex; i++) {
            progress += stageWeights[stages[i]];
        }
        
        // Add partial progress for current stage
        if (workflow.current_stage === 'document_processing' && workflow.total_documents > 0) {
            const stageProgress = workflow.processed_documents / workflow.total_documents;
            progress += stageWeights[workflow.current_stage] * stageProgress;
        } else if (workflow.current_stage === 'manual_review' && workflow.total_entities > 0) {
            const stageProgress = workflow.approved_entities / workflow.total_entities;
            progress += stageWeights[workflow.current_stage] * stageProgress;
        } else {
            progress += stageWeights[workflow.current_stage] * 0.5; // Assume 50% for other stages
        }
        
        return Math.min(progress, 1.0);
    }
    
    createEmptyState(message = 'No workflows found') {
        return `
            <div class="empty-state">
                <i class="fas fa-project-diagram"></i>
                <h3>${message}</h3>
                <p>Create a new workflow to get started with document processing</p>
                <button class="btn btn-primary" onclick="workflowDashboard.showCreateWorkflowModal()">
                    <i class="fas fa-plus"></i> Create Workflow
                </button>
            </div>
        `;
    }
    
    showLoadingState() {
        const workflowsGrid = document.getElementById('workflowsGrid');
        if (workflowsGrid) {
            workflowsGrid.innerHTML = `
                <div class="loading-state">
                    <div class="loading-spinner"></div>
                    <p>Loading workflows...</p>
                </div>
            `;
        }
    }
    
    showErrorState(message) {
        const workflowsGrid = document.getElementById('workflowsGrid');
        if (workflowsGrid) {
            workflowsGrid.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-exclamation-triangle"></i>
                    <h3>Error</h3>
                    <p>${message}</p>
                    <button class="btn btn-primary" onclick="workflowDashboard.loadWorkflows()">
                        <i class="fas fa-sync"></i> Retry
                    </button>
                </div>
            `;
        }
    }
    
    filterWorkflows() {
        this.renderWorkflows();
    }
    
    showCreateWorkflowModal() {
        const modal = document.getElementById('createWorkflowModal');
        if (modal) {
            modal.style.display = 'block';
            
            // Reset form
            const form = document.getElementById('createWorkflowForm');
            if (form) {
                form.reset();
            }
        }
    }
    
    async createWorkflow() {
        try {
            const form = document.getElementById('createWorkflowForm');
            const formData = new FormData(form);
            
            const workflowData = {
                user_id: 'web_user',
                name: formData.get('name'),
                description: formData.get('description'),
                config: {
                    auto_approve_threshold: parseFloat(formData.get('auto_approve_threshold')),
                    auto_resolve_conflicts: formData.get('auto_resolve_conflicts') === 'on',
                    batch_processing: formData.get('batch_processing') === 'on'
                }
            };
            
            const response = await fetch('/api/workflows', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(workflowData)
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showNotification('Workflow created successfully', 'success');
                this.closeModals();
                this.loadWorkflows();
            } else {
                throw new Error(result.error);
            }
        } catch (error) {
            console.error('Error creating workflow:', error);
            this.showNotification('Failed to create workflow', 'error');
        }
    }
    
    async viewWorkflow(workflowId) {
        try {
            const response = await fetch(`/api/workflows/${workflowId}?user_id=web_user`);
            const result = await response.json();
            
            if (result.success) {
                this.showWorkflowDetailsModal(result.workflow, result.jobs, result.sessions);
            } else {
                throw new Error(result.error);
            }
        } catch (error) {
            console.error('Error loading workflow details:', error);
            this.showNotification('Failed to load workflow details', 'error');
        }
    }
    
    showWorkflowDetailsModal(workflow, jobs, sessions) {
        const modal = document.getElementById('workflowDetailsModal');
        const content = document.getElementById('workflowDetailsContent');
        
        content.innerHTML = `
            <div class="workflow-details">
                <div class="workflow-overview">
                    <h4>${workflow.name}</h4>
                    <p>${workflow.description}</p>
                    <div class="detail-grid">
                        <div><strong>Status:</strong> ${workflow.status}</div>
                        <div><strong>Stage:</strong> ${workflow.current_stage.replace('_', ' ')}</div>
                        <div><strong>Progress:</strong> ${workflow.overall_progress}%</div>
                        <div><strong>Created:</strong> ${new Date(workflow.created_at).toLocaleString()}</div>
                        <div><strong>Updated:</strong> ${new Date(workflow.updated_at).toLocaleString()}</div>
                        <div><strong>Documents:</strong> ${workflow.total_documents}</div>
                        <div><strong>Entities:</strong> ${workflow.total_entities}</div>
                        <div><strong>Approved:</strong> ${workflow.approved_entities}</div>
                    </div>
                </div>
                
                ${jobs && jobs.length > 0 ? `
                    <div class="workflow-jobs">
                        <h5>Processing Jobs</h5>
                        <div class="jobs-list">
                            ${jobs.map(job => `
                                <div class="job-summary">
                                    <span class="job-name">${job.filename}</span>
                                    <span class="job-status status-${job.status}">${job.status}</span>
                                    <span class="job-progress">${Math.round(job.progress * 100)}%</span>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                ` : ''}
                
                ${sessions && sessions.length > 0 ? `
                    <div class="workflow-sessions">
                        <h5>Entity Sessions</h5>
                        <div class="sessions-list">
                            ${sessions.map(session => `
                                <div class="session-summary">
                                    <span class="session-id">${session.session_id}</span>
                                    <span class="session-entities">${session.entities_count} entities</span>
                                    <span class="session-relationships">${session.relationships_count} relationships</span>
                                    <a href="/entity-management?session=${session.session_id}" target="_blank" class="btn btn-sm btn-primary">
                                        <i class="fas fa-external-link-alt"></i> View
                                    </a>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                ` : ''}
            </div>
        `;
        
        modal.style.display = 'block';
    }
    
    async approveWorkflow(workflowId) {
        if (!confirm('Approve entities in this workflow for Neo4j ingestion?')) return;
        
        try {
            const response = await fetch(`/api/workflows/${workflowId}/approve`, {
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
                this.showNotification(`${result.approved_count} entities approved`, 'success');
                this.loadWorkflows();
            } else {
                throw new Error(result.error);
            }
        } catch (error) {
            console.error('Error approving workflow:', error);
            this.showNotification('Failed to approve workflow', 'error');
        }
    }
    
    async ingestWorkflow(workflowId) {
        if (!confirm('Ingest approved entities to Neo4j? This action cannot be undone.')) return;
        
        try {
            const response = await fetch(`/api/workflows/${workflowId}/ingest`, {
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
                this.showNotification(`Ingested ${result.ingested_entities} entities and ${result.ingested_relationships} relationships`, 'success');
                this.loadWorkflows();
            } else {
                throw new Error(result.error);
            }
        } catch (error) {
            console.error('Error ingesting workflow:', error);
            this.showNotification('Failed to ingest workflow', 'error');
        }
    }
    
    async cancelWorkflow(workflowId) {
        if (!confirm('Cancel this workflow? All processing will be stopped.')) return;
        
        try {
            const response = await fetch(`/api/workflows/${workflowId}/cancel`, {
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
                this.showNotification('Workflow cancelled', 'success');
                this.loadWorkflows();
            } else {
                throw new Error(result.error);
            }
        } catch (error) {
            console.error('Error cancelling workflow:', error);
            this.showNotification('Failed to cancel workflow', 'error');
        }
    }
    
    async loadActivityTimeline() {
        try {
            const timelineContent = document.getElementById('timelineContent');
            if (!timelineContent) return;
            
            timelineContent.innerHTML = `
                <div class="loading-state">
                    <div class="loading-spinner"></div>
                    <p>Loading activity timeline...</p>
                </div>
            `;
            
            // For now, show a placeholder timeline
            // In a real implementation, this would fetch from an activity API
            setTimeout(() => {
                timelineContent.innerHTML = `
                    <div class="timeline-item">
                        <div class="timeline-icon workflow">
                            <i class="fas fa-plus"></i>
                        </div>
                        <div class="timeline-content">
                            <div class="timeline-title-text">Workflow Created</div>
                            <div class="timeline-description">New workflow "Document Analysis" created</div>
                            <div class="timeline-time">2 hours ago</div>
                        </div>
                    </div>
                    <div class="timeline-item">
                        <div class="timeline-icon document">
                            <i class="fas fa-file-upload"></i>
                        </div>
                        <div class="timeline-content">
                            <div class="timeline-title-text">Documents Uploaded</div>
                            <div class="timeline-description">5 documents uploaded for processing</div>
                            <div class="timeline-time">1 hour ago</div>
                        </div>
                    </div>
                    <div class="timeline-item">
                        <div class="timeline-icon approval">
                            <i class="fas fa-check"></i>
                        </div>
                        <div class="timeline-content">
                            <div class="timeline-title-text">Entities Approved</div>
                            <div class="timeline-description">45 entities approved for ingestion</div>
                            <div class="timeline-time">30 minutes ago</div>
                        </div>
                    </div>
                `;
            }, 1000);
        } catch (error) {
            console.error('Error loading activity timeline:', error);
        }
    }
    
    startAutoRefresh() {
        // Refresh workflows every 30 seconds
        this.refreshInterval = setInterval(() => {
            this.loadWorkflows();
        }, 30000);
    }
    
    stopAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
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
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.workflowDashboard = new WorkflowDashboard();
});

// Export for module use
window.WorkflowDashboard = WorkflowDashboard;
