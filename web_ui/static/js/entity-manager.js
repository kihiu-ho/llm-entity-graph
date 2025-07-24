/**
 * Entity Management Application
 * Comprehensive interface for managing entity and relationship extraction workflows
 */

class EntityManager {
    constructor() {
        this.currentSession = null;
        this.currentTab = 'entities';
        this.entities = [];
        this.relationships = [];
        this.selectedItems = new Set();
        this.filters = {
            status: '',
            type: '',
            search: ''
        };
        
        this.init();
    }
    
    async init() {
        console.log('🚀 Initializing Entity Manager');
        
        // Set up event listeners
        this.setupEventListeners();
        
        // Load initial data
        await this.loadSessions();
        
        console.log('✅ Entity Manager initialized');
    }
    
    setupEventListeners() {
        // Session selection
        document.getElementById('session-select').addEventListener('change', (e) => {
            this.selectSession(e.target.value);
        });
        
        // Filters
        document.getElementById('status-filter').addEventListener('change', (e) => {
            this.filters.status = e.target.value;
            this.applyFilters();
        });
        
        document.getElementById('type-filter').addEventListener('change', (e) => {
            this.filters.type = e.target.value;
            this.applyFilters();
        });
        
        document.getElementById('search-input').addEventListener('input', (e) => {
            this.filters.search = e.target.value;
            this.debounceSearch();
        });
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey || e.metaKey) {
                switch(e.key) {
                    case 'a':
                        e.preventDefault();
                        this.selectAll();
                        break;
                    case 's':
                        e.preventDefault();
                        this.saveChanges();
                        break;
                }
            }
        });
    }
    
    async loadSessions() {
        try {
            this.showLoading('Loading sessions...');
            
            const response = await fetch('/api/staging/sessions/enhanced');
            const data = await response.json();
            
            if (data.success) {
                this.populateSessionSelector(data.sessions);
            } else {
                this.showError('Failed to load sessions: ' + data.error);
            }
        } catch (error) {
            console.error('Error loading sessions:', error);
            this.showError('Failed to load sessions: ' + error.message);
        } finally {
            this.hideLoading();
        }
    }
    
    populateSessionSelector(sessions) {
        const selector = document.getElementById('session-select');
        selector.innerHTML = '<option value="">Select a session...</option>';
        
        sessions.forEach(session => {
            const option = document.createElement('option');
            option.value = session.session_id;
            option.textContent = `${session.document_title} (${session.status})`;
            selector.appendChild(option);
        });
        
        // Auto-select first session if available
        if (sessions.length > 0) {
            selector.value = sessions[0].session_id;
            this.selectSession(sessions[0].session_id);
        }
    }
    
    async selectSession(sessionId) {
        if (!sessionId) {
            this.currentSession = null;
            this.clearData();
            return;
        }
        
        try {
            this.showLoading('Loading session data...');
            
            const response = await fetch(`/api/staging/sessions/${sessionId}/enhanced`);
            const data = await response.json();
            
            if (data.success) {
                this.currentSession = data.session;
                await this.loadSessionData();
                this.updateHeader();
                this.updateWorkflowProgress();
            } else {
                this.showError('Failed to load session: ' + data.error);
            }
        } catch (error) {
            console.error('Error loading session:', error);
            this.showError('Failed to load session: ' + error.message);
        } finally {
            this.hideLoading();
        }
    }
    
    async loadSessionData() {
        if (!this.currentSession) return;
        
        // Load entities and relationships in parallel
        await Promise.all([
            this.loadEntities(),
            this.loadRelationships(),
            this.loadQualityScore()
        ]);
    }
    
    async loadEntities() {
        try {
            const params = new URLSearchParams({
                status: this.filters.status,
                type: this.filters.type,
                search: this.filters.search
            });
            
            const response = await fetch(`/api/staging/sessions/${this.currentSession.session_id}/entities/enhanced?${params}`);
            const data = await response.json();
            
            if (data.success) {
                this.entities = data.entities;
                this.renderEntitiesTable();
            } else {
                this.showError('Failed to load entities: ' + data.error);
            }
        } catch (error) {
            console.error('Error loading entities:', error);
            this.showError('Failed to load entities: ' + error.message);
        }
    }
    
    async loadRelationships() {
        try {
            const params = new URLSearchParams({
                status: this.filters.status,
                type: this.filters.type
            });
            
            const response = await fetch(`/api/staging/sessions/${this.currentSession.session_id}/relationships/enhanced?${params}`);
            const data = await response.json();
            
            if (data.success) {
                this.relationships = data.relationships;
                this.renderRelationshipsTable();
            } else {
                this.showError('Failed to load relationships: ' + data.error);
            }
        } catch (error) {
            console.error('Error loading relationships:', error);
            this.showError('Failed to load relationships: ' + error.message);
        }
    }
    
    async loadQualityScore() {
        try {
            const response = await fetch(`/api/staging/sessions/${this.currentSession.session_id}/quality-score`);
            const data = await response.json();
            
            if (data.success) {
                document.getElementById('quality-score').textContent = data.quality_score.quality_grade;
            }
        } catch (error) {
            console.error('Error loading quality score:', error);
        }
    }
    
    renderEntitiesTable() {
        const container = document.getElementById('entities-content');
        const loading = document.getElementById('entities-loading');
        
        if (this.entities.length === 0) {
            container.innerHTML = '<p style="text-align: center; color: #6c757d; margin-top: 40px;">No entities found</p>';
            container.style.display = 'block';
            loading.style.display = 'none';
            return;
        }
        
        const html = `
            <div class="table-controls">
                <div class="batch-actions">
                    <button class="btn btn-success" onclick="entityManager.batchApprove('entities')">
                        <i class="fas fa-check"></i> Approve Selected
                    </button>
                    <button class="btn btn-danger" onclick="entityManager.batchReject('entities')">
                        <i class="fas fa-times"></i> Reject Selected
                    </button>
                    <button class="btn btn-secondary" onclick="entityManager.selectAll()">
                        <i class="fas fa-check-square"></i> Select All
                    </button>
                    <button class="btn btn-outline" onclick="entityManager.addNewEntity()">
                        <i class="fas fa-plus"></i> Add Entity
                    </button>
                </div>
            </div>
            
            <table class="data-table">
                <thead>
                    <tr>
                        <th><input type="checkbox" id="select-all-entities" onchange="entityManager.toggleSelectAll(this)"></th>
                        <th>Name</th>
                        <th>Type</th>
                        <th>Status</th>
                        <th>Confidence</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    ${this.entities.map(entity => this.renderEntityRow(entity)).join('')}
                </tbody>
            </table>
        `;
        
        container.innerHTML = html;
        container.style.display = 'block';
        loading.style.display = 'none';
    }
    
    renderEntityRow(entity) {
        const statusClass = `status-${entity.status}`;
        const isSelected = this.selectedItems.has(`entity-${entity.id}`);
        
        return `
            <tr class="entity-row" data-id="${entity.id}" onclick="entityManager.selectItem('entity', '${entity.id}')">
                <td>
                    <input type="checkbox" ${isSelected ? 'checked' : ''} 
                           onchange="entityManager.toggleItemSelection('entity-${entity.id}', this.checked)"
                           onclick="event.stopPropagation()">
                </td>
                <td>
                    <div class="entity-name" contenteditable="true" 
                         onblur="entityManager.updateEntityField('${entity.id}', 'name', this.textContent)">${entity.name}</div>
                </td>
                <td>
                    <select onchange="entityManager.updateEntityField('${entity.id}', 'type', this.value)"
                            onclick="event.stopPropagation()">
                        <option value="Person" ${entity.type === 'Person' ? 'selected' : ''}>Person</option>
                        <option value="Company" ${entity.type === 'Company' ? 'selected' : ''}>Company</option>
                        <option value="Organization" ${entity.type === 'Organization' ? 'selected' : ''}>Organization</option>
                        <option value="Location" ${entity.type === 'Location' ? 'selected' : ''}>Location</option>
                    </select>
                </td>
                <td>
                    <span class="status-badge ${statusClass}">${entity.status}</span>
                </td>
                <td>
                    <span class="confidence-score">${(entity.confidence * 100).toFixed(1)}%</span>
                </td>
                <td>
                    <div class="action-buttons">
                        <button class="btn btn-success btn-sm" onclick="entityManager.approveItem('entity', '${entity.id}'); event.stopPropagation()">
                            <i class="fas fa-check"></i>
                        </button>
                        <button class="btn btn-danger btn-sm" onclick="entityManager.rejectItem('entity', '${entity.id}'); event.stopPropagation()">
                            <i class="fas fa-times"></i>
                        </button>
                        <button class="btn btn-secondary btn-sm" onclick="entityManager.editItem('entity', '${entity.id}'); event.stopPropagation()">
                            <i class="fas fa-edit"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `;
    }
    
    renderRelationshipsTable() {
        const container = document.getElementById('relationships-content');
        const loading = document.getElementById('relationships-loading');
        
        if (this.relationships.length === 0) {
            container.innerHTML = '<p style="text-align: center; color: #6c757d; margin-top: 40px;">No relationships found</p>';
            container.style.display = 'block';
            loading.style.display = 'none';
            return;
        }
        
        const html = `
            <div class="table-controls">
                <div class="batch-actions">
                    <button class="btn btn-success" onclick="entityManager.batchApprove('relationships')">
                        <i class="fas fa-check"></i> Approve Selected
                    </button>
                    <button class="btn btn-danger" onclick="entityManager.batchReject('relationships')">
                        <i class="fas fa-times"></i> Reject Selected
                    </button>
                    <button class="btn btn-secondary" onclick="entityManager.selectAll()">
                        <i class="fas fa-check-square"></i> Select All
                    </button>
                    <button class="btn btn-outline" onclick="entityManager.addNewRelationship()">
                        <i class="fas fa-plus"></i> Add Relationship
                    </button>
                </div>
            </div>
            
            <table class="data-table">
                <thead>
                    <tr>
                        <th><input type="checkbox" id="select-all-relationships" onchange="entityManager.toggleSelectAll(this)"></th>
                        <th>Source</th>
                        <th>Relationship</th>
                        <th>Target</th>
                        <th>Status</th>
                        <th>Confidence</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    ${this.relationships.map(rel => this.renderRelationshipRow(rel)).join('')}
                </tbody>
            </table>
        `;
        
        container.innerHTML = html;
        container.style.display = 'block';
        loading.style.display = 'none';
    }
    
    renderRelationshipRow(relationship) {
        const statusClass = `status-${relationship.status}`;
        const isSelected = this.selectedItems.has(`relationship-${relationship.id}`);
        
        // Find entity names
        const sourceEntity = this.entities.find(e => e.id === relationship.source_entity_id);
        const targetEntity = this.entities.find(e => e.id === relationship.target_entity_id);
        
        return `
            <tr class="relationship-row" data-id="${relationship.id}" onclick="entityManager.selectItem('relationship', '${relationship.id}')">
                <td>
                    <input type="checkbox" ${isSelected ? 'checked' : ''} 
                           onchange="entityManager.toggleItemSelection('relationship-${relationship.id}', this.checked)"
                           onclick="event.stopPropagation()">
                </td>
                <td>${sourceEntity ? sourceEntity.name : 'Unknown'}</td>
                <td>
                    <div class="relationship-type" contenteditable="true"
                         onblur="entityManager.updateRelationshipField('${relationship.id}', 'relationship_type', this.textContent)">${relationship.relationship_type}</div>
                </td>
                <td>${targetEntity ? targetEntity.name : 'Unknown'}</td>
                <td>
                    <span class="status-badge ${statusClass}">${relationship.status}</span>
                </td>
                <td>
                    <span class="confidence-score">${(relationship.confidence * 100).toFixed(1)}%</span>
                </td>
                <td>
                    <div class="action-buttons">
                        <button class="btn btn-success btn-sm" onclick="entityManager.approveItem('relationship', '${relationship.id}'); event.stopPropagation()">
                            <i class="fas fa-check"></i>
                        </button>
                        <button class="btn btn-danger btn-sm" onclick="entityManager.rejectItem('relationship', '${relationship.id}'); event.stopPropagation()">
                            <i class="fas fa-times"></i>
                        </button>
                        <button class="btn btn-secondary btn-sm" onclick="entityManager.editItem('relationship', '${relationship.id}'); event.stopPropagation()">
                            <i class="fas fa-edit"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `;
    }
    
    updateHeader() {
        if (!this.currentSession) return;
        
        const stats = this.currentSession.statistics;
        document.getElementById('total-entities').textContent = stats.total_entities;
        document.getElementById('total-relationships').textContent = stats.total_relationships;
        
        const totalItems = stats.total_entities + stats.total_relationships;
        const approvedItems = stats.approved_entities + stats.approved_relationships;
        const approvalPercentage = totalItems > 0 ? Math.round((approvedItems / totalItems) * 100) : 0;
        
        document.getElementById('approval-progress').textContent = `${approvalPercentage}%`;
    }
    
    updateWorkflowProgress() {
        if (!this.currentSession) return;
        
        const stage = this.currentSession.workflow_stage;
        const steps = ['extraction', 'review', 'approval', 'ingestion'];
        const currentIndex = steps.indexOf(stage);
        
        steps.forEach((step, index) => {
            const element = document.getElementById(`step-${step}`);
            if (index < currentIndex) {
                element.className = 'step-circle completed';
            } else if (index === currentIndex) {
                element.className = 'step-circle active';
            } else {
                element.className = 'step-circle pending';
            }
        });
        
        const progressFill = document.getElementById('progress-fill');
        const progressPercentage = ((currentIndex + 1) / steps.length) * 100;
        progressFill.style.width = `${progressPercentage}%`;
    }
    
    // Utility methods
    showLoading(message = 'Loading...') {
        const overlay = document.getElementById('loading-overlay');
        if (overlay) {
            overlay.querySelector('p').textContent = message;
            overlay.style.display = 'flex';
        }
    }
    
    hideLoading() {
        const overlay = document.getElementById('loading-overlay');
        if (overlay) {
            overlay.style.display = 'none';
        }
    }
    
    showError(message) {
        const errorDiv = document.getElementById('error-message');
        errorDiv.textContent = message;
        errorDiv.style.display = 'block';
        setTimeout(() => {
            errorDiv.style.display = 'none';
        }, 5000);
    }
    
    showSuccess(message) {
        const successDiv = document.getElementById('success-message');
        successDiv.textContent = message;
        successDiv.style.display = 'block';
        setTimeout(() => {
            successDiv.style.display = 'none';
        }, 3000);
    }
    
    clearData() {
        this.entities = [];
        this.relationships = [];
        this.selectedItems.clear();
        
        document.getElementById('entities-content').innerHTML = '';
        document.getElementById('relationships-content').innerHTML = '';
        document.getElementById('details-content').innerHTML = '<p style="text-align: center; color: #6c757d; margin-top: 40px;">Select an item to view details</p>';
    }
    
    debounceSearch() {
        clearTimeout(this.searchTimeout);
        this.searchTimeout = setTimeout(() => {
            this.applyFilters();
        }, 300);
    }
    
    applyFilters() {
        if (this.currentSession) {
            this.loadSessionData();
        }
    }
}

// Global functions for HTML event handlers
window.switchTab = function(tab) {
    // Update tab buttons
    document.querySelectorAll('.tab-button').forEach(btn => btn.classList.remove('active'));
    event.target.classList.add('active');
    
    // Update tab content
    document.getElementById('entities-tab').style.display = tab === 'entities' ? 'block' : 'none';
    document.getElementById('relationships-tab').style.display = tab === 'relationships' ? 'block' : 'none';
    
    entityManager.currentTab = tab;
};

window.refreshSessions = function() {
    entityManager.loadSessions();
};

window.validateSession = function() {
    if (entityManager.currentSession) {
        entityManager.validateCurrentSession();
    }
};

window.exportData = function() {
    if (entityManager.currentSession) {
        entityManager.exportSessionData();
    }
};

window.importData = function() {
    entityManager.showImportDialog();
};

    // Item selection and interaction methods
    toggleItemSelection(itemKey, isSelected) {
        if (isSelected) {
            this.selectedItems.add(itemKey);
        } else {
            this.selectedItems.delete(itemKey);
        }
    }

    toggleSelectAll(checkbox) {
        const isChecked = checkbox.checked;
        const currentItems = this.currentTab === 'entities' ? this.entities : this.relationships;
        const prefix = this.currentTab === 'entities' ? 'entity' : 'relationship';

        currentItems.forEach(item => {
            const itemKey = `${prefix}-${item.id}`;
            if (isChecked) {
                this.selectedItems.add(itemKey);
            } else {
                this.selectedItems.delete(itemKey);
            }
        });

        // Update individual checkboxes
        document.querySelectorAll(`input[type="checkbox"][onchange*="${prefix}"]`).forEach(cb => {
            cb.checked = isChecked;
        });
    }

    selectAll() {
        const selectAllCheckbox = document.getElementById(`select-all-${this.currentTab}`);
        if (selectAllCheckbox) {
            selectAllCheckbox.checked = true;
            this.toggleSelectAll(selectAllCheckbox);
        }
    }

    selectItem(type, id) {
        const item = type === 'entity' ?
            this.entities.find(e => e.id === id) :
            this.relationships.find(r => r.id === id);

        if (item) {
            this.showItemDetails(type, item);
        }
    }

    showItemDetails(type, item) {
        const detailsContainer = document.getElementById('details-content');

        const html = `
            <div class="item-details">
                <h4><i class="fas fa-${type === 'entity' ? 'user' : 'link'}"></i> ${type === 'entity' ? item.name : item.relationship_type}</h4>

                <div class="detail-section">
                    <h5>Basic Information</h5>
                    <div class="detail-grid">
                        <div class="detail-item">
                            <label>ID:</label>
                            <span>${item.id}</span>
                        </div>
                        <div class="detail-item">
                            <label>Status:</label>
                            <span class="status-badge status-${item.status}">${item.status}</span>
                        </div>
                        <div class="detail-item">
                            <label>Confidence:</label>
                            <span>${(item.confidence * 100).toFixed(1)}%</span>
                        </div>
                        <div class="detail-item">
                            <label>Created:</label>
                            <span>${new Date(item.created_at).toLocaleString()}</span>
                        </div>
                    </div>
                </div>

                ${type === 'entity' ? this.renderEntityDetails(item) : this.renderRelationshipDetails(item)}

                <div class="detail-section">
                    <h5>Edit History</h5>
                    <div class="edit-history">
                        ${item.edit_history && item.edit_history.length > 0 ?
                            item.edit_history.map(entry => `
                                <div class="history-entry">
                                    <div class="history-header">
                                        <strong>${entry.action}</strong> by ${entry.user}
                                        <span class="history-time">${new Date(entry.timestamp).toLocaleString()}</span>
                                    </div>
                                    ${entry.comment ? `<div class="history-comment">${entry.comment}</div>` : ''}
                                </div>
                            `).join('') :
                            '<p>No edit history available</p>'
                        }
                    </div>
                </div>

                <div class="detail-actions">
                    <button class="btn btn-success" onclick="entityManager.approveItem('${type}', '${item.id}')">
                        <i class="fas fa-check"></i> Approve
                    </button>
                    <button class="btn btn-danger" onclick="entityManager.rejectItem('${type}', '${item.id}')">
                        <i class="fas fa-times"></i> Reject
                    </button>
                    <button class="btn btn-primary" onclick="entityManager.editItem('${type}', '${item.id}')">
                        <i class="fas fa-edit"></i> Edit
                    </button>
                </div>
            </div>
        `;

        detailsContainer.innerHTML = html;
    }

    renderEntityDetails(entity) {
        return `
            <div class="detail-section">
                <h5>Entity Details</h5>
                <div class="detail-grid">
                    <div class="detail-item">
                        <label>Name:</label>
                        <span>${entity.name}</span>
                    </div>
                    <div class="detail-item">
                        <label>Type:</label>
                        <span>${entity.type}</span>
                    </div>
                    ${Object.entries(entity.attributes || {}).map(([key, value]) => `
                        <div class="detail-item">
                            <label>${key}:</label>
                            <span>${value}</span>
                        </div>
                    `).join('')}
                </div>
                ${entity.source_text ? `
                    <div class="source-text">
                        <label>Source Text:</label>
                        <div class="source-content">${entity.source_text}</div>
                    </div>
                ` : ''}
            </div>
        `;
    }

    renderRelationshipDetails(relationship) {
        const sourceEntity = this.entities.find(e => e.id === relationship.source_entity_id);
        const targetEntity = this.entities.find(e => e.id === relationship.target_entity_id);

        return `
            <div class="detail-section">
                <h5>Relationship Details</h5>
                <div class="detail-grid">
                    <div class="detail-item">
                        <label>Source:</label>
                        <span>${sourceEntity ? sourceEntity.name : 'Unknown'}</span>
                    </div>
                    <div class="detail-item">
                        <label>Relationship:</label>
                        <span>${relationship.relationship_type}</span>
                    </div>
                    <div class="detail-item">
                        <label>Target:</label>
                        <span>${targetEntity ? targetEntity.name : 'Unknown'}</span>
                    </div>
                    ${Object.entries(relationship.attributes || {}).map(([key, value]) => `
                        <div class="detail-item">
                            <label>${key}:</label>
                            <span>${value}</span>
                        </div>
                    `).join('')}
                </div>
                ${relationship.source_text ? `
                    <div class="source-text">
                        <label>Source Text:</label>
                        <div class="source-content">${relationship.source_text}</div>
                    </div>
                ` : ''}
            </div>
        `;
    }

    // CRUD operations
    async updateEntityField(entityId, field, value) {
        try {
            const updates = { [field]: value };

            const response = await fetch(`/api/staging/entities/${entityId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: this.currentSession.session_id,
                    updates: updates,
                    user: 'web_user',
                    comment: `Updated ${field} to "${value}"`
                })
            });

            const data = await response.json();
            if (data.success) {
                this.showSuccess('Entity updated successfully');
                await this.loadEntities();
            } else {
                this.showError('Failed to update entity: ' + data.error);
            }
        } catch (error) {
            console.error('Error updating entity:', error);
            this.showError('Failed to update entity: ' + error.message);
        }
    }

    async updateRelationshipField(relationshipId, field, value) {
        try {
            const updates = { [field]: value };

            const response = await fetch(`/api/staging/relationships/${relationshipId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: this.currentSession.session_id,
                    updates: updates,
                    user: 'web_user',
                    comment: `Updated ${field} to "${value}"`
                })
            });

            const data = await response.json();
            if (data.success) {
                this.showSuccess('Relationship updated successfully');
                await this.loadRelationships();
            } else {
                this.showError('Failed to update relationship: ' + data.error);
            }
        } catch (error) {
            console.error('Error updating relationship:', error);
            this.showError('Failed to update relationship: ' + error.message);
        }
    }

    async approveItem(type, id) {
        try {
            const endpoint = type === 'entity' ?
                `/api/staging/entities/${id}` :
                `/api/staging/relationships/${id}`;

            const response = await fetch(endpoint, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: this.currentSession.session_id,
                    updates: { status: 'approved' },
                    user: 'web_user',
                    comment: 'Approved via web interface'
                })
            });

            const data = await response.json();
            if (data.success) {
                this.showSuccess(`${type} approved successfully`);
                await this.loadSessionData();
            } else {
                this.showError(`Failed to approve ${type}: ` + data.error);
            }
        } catch (error) {
            console.error(`Error approving ${type}:`, error);
            this.showError(`Failed to approve ${type}: ` + error.message);
        }
    }

    async rejectItem(type, id) {
        try {
            const endpoint = type === 'entity' ?
                `/api/staging/entities/${id}` :
                `/api/staging/relationships/${id}`;

            const response = await fetch(endpoint, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: this.currentSession.session_id,
                    updates: { status: 'rejected' },
                    user: 'web_user',
                    comment: 'Rejected via web interface'
                })
            });

            const data = await response.json();
            if (data.success) {
                this.showSuccess(`${type} rejected successfully`);
                await this.loadSessionData();
            } else {
                this.showError(`Failed to reject ${type}: ` + data.error);
            }
        } catch (error) {
            console.error(`Error rejecting ${type}:`, error);
            this.showError(`Failed to reject ${type}: ` + error.message);
        }
    }

    // Batch operations
    async batchApprove(type) {
        const selectedIds = Array.from(this.selectedItems)
            .filter(key => key.startsWith(type === 'entities' ? 'entity-' : 'relationship-'))
            .map(key => key.split('-')[1]);

        if (selectedIds.length === 0) {
            this.showError('No items selected');
            return;
        }

        try {
            const endpoint = type === 'entities' ?
                '/api/staging/batch/approve-entities' :
                '/api/staging/batch/approve-relationships';

            const response = await fetch(endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: this.currentSession.session_id,
                    [type === 'entities' ? 'entity_ids' : 'relationship_ids']: selectedIds,
                    user: 'web_user',
                    comment: 'Batch approved via web interface'
                })
            });

            const data = await response.json();
            if (data.success) {
                this.showSuccess(`${data.approved_count} ${type} approved successfully`);
                this.selectedItems.clear();
                await this.loadSessionData();
            } else {
                this.showError(`Failed to batch approve ${type}: ` + data.error);
            }
        } catch (error) {
            console.error(`Error batch approving ${type}:`, error);
            this.showError(`Failed to batch approve ${type}: ` + error.message);
        }
    }

    async batchReject(type) {
        const selectedIds = Array.from(this.selectedItems)
            .filter(key => key.startsWith(type === 'entities' ? 'entity-' : 'relationship-'))
            .map(key => key.split('-')[1]);

        if (selectedIds.length === 0) {
            this.showError('No items selected');
            return;
        }

        try {
            const endpoint = type === 'entities' ?
                '/api/staging/batch/reject-entities' :
                '/api/staging/batch/reject-relationships';

            const response = await fetch(endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: this.currentSession.session_id,
                    [type === 'entities' ? 'entity_ids' : 'relationship_ids']: selectedIds,
                    user: 'web_user',
                    comment: 'Batch rejected via web interface'
                })
            });

            const data = await response.json();
            if (data.success) {
                this.showSuccess(`${data.rejected_count} ${type} rejected successfully`);
                this.selectedItems.clear();
                await this.loadSessionData();
            } else {
                this.showError(`Failed to batch reject ${type}: ` + data.error);
            }
        } catch (error) {
            console.error(`Error batch rejecting ${type}:`, error);
            this.showError(`Failed to batch reject ${type}: ` + error.message);
        }
    }

    // Validation
    async validateCurrentSession() {
        if (!this.currentSession) return;

        try {
            this.showLoading('Validating session...');

            const response = await fetch(`/api/staging/sessions/${this.currentSession.session_id}/validate`);
            const data = await response.json();

            if (data.success) {
                this.showValidationResults(data.validation_results);
            } else {
                this.showError('Failed to validate session: ' + data.error);
            }
        } catch (error) {
            console.error('Error validating session:', error);
            this.showError('Failed to validate session: ' + error.message);
        } finally {
            this.hideLoading();
        }
    }

    showValidationResults(results) {
        const summary = results.summary;
        const message = `
            Validation Complete:
            • Entities: ${summary.valid_entities}/${summary.total_entities} valid
            • Relationships: ${summary.valid_relationships}/${summary.total_relationships} valid
            • Warnings: ${summary.entities_with_warnings + summary.relationships_with_warnings}
            • Errors: ${summary.entities_with_errors + summary.relationships_with_errors}
        `;

        if (summary.entities_with_errors === 0 && summary.relationships_with_errors === 0) {
            this.showSuccess(message);
        } else {
            this.showError(message);
        }
    }
}

// Initialize the application
let entityManager;
document.addEventListener('DOMContentLoaded', () => {
    entityManager = new EntityManager();
});
