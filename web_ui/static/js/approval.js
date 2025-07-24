/**
 * Approval Dashboard JavaScript
 * Interactive functionality for entity and relationship approval system
 */

class ApprovalDashboard {
    constructor() {
        this.currentSession = null;
        this.entities = [];
        this.relationships = [];
        this.selectedEntities = new Set();
        this.currentEntity = null;
        this.filters = {
            entityTypes: [],
            status: 'pending',
            search: ''
        };
        
        this.init();
    }

    init() {
        // Skip full initialization if DOM elements don't exist
        if (!this.bindEvents()) {
            console.warn('ApprovalDashboard: Skipping full initialization due to missing DOM elements');
            return;
        }
        this.loadExistingSession();
        this.setupNotificationSystem();
    }

    bindEvents() {
        // Check if required elements exist before binding
        const newSessionBtn = document.getElementById('new-session-btn');
        if (!newSessionBtn) {
            console.warn('ApprovalDashboard: Required DOM elements not found, skipping initialization');
            return false;
        }
        
        // Navigation events
        const backToMainBtn = document.getElementById('back-to-main');
        if (backToMainBtn) {
            backToMainBtn.addEventListener('click', () => {
                window.location.href = '/';
            });
        }

        newSessionBtn.addEventListener('click', () => {
            this.showSessionPanel();
        });

        // Session panel events
        const closeSessionPanel = document.getElementById('close-session-panel');
        if (closeSessionPanel) {
            closeSessionPanel.addEventListener('click', () => {
                this.hideSessionPanel();
            });
        }

        const cancelSession = document.getElementById('cancel-session');
        if (cancelSession) {
            cancelSession.addEventListener('click', () => {
                this.hideSessionPanel();
            });
        }

        const sessionForm = document.getElementById('session-form');
        if (sessionForm) {
            sessionForm.addEventListener('submit', (e) => {
                this.handleSessionCreation(e);
            });
        }

        // Control panel events
        document.getElementById('bulk-approve-btn').addEventListener('click', () => {
            this.handleBulkApproval();
        });

        document.getElementById('clean-pending-btn').addEventListener('click', () => {
            this.handleCleanPending();
        });

        document.getElementById('approve-all-btn').addEventListener('click', () => {
            this.handleApproveAll();
        });

        document.getElementById('refresh-data-btn').addEventListener('click', () => {
            this.refreshData();
        });

        // Filter events
        document.getElementById('entity-type-filter').addEventListener('change', () => {
            this.updateFilters();
        });

        document.getElementById('status-filter').addEventListener('change', () => {
            this.updateFilters();
        });

        document.getElementById('search-input').addEventListener('input', (e) => {
            this.debounce(() => {
                this.filters.search = e.target.value;
                this.filterEntities();
            }, 300)();
        });

        // Selection events
        document.getElementById('select-all-btn').addEventListener('click', () => {
            this.selectAllEntities();
        });

        document.getElementById('clear-selection-btn').addEventListener('click', () => {
            this.clearSelection();
        });

        document.getElementById('select-all-checkbox').addEventListener('change', (e) => {
            if (e.target.checked) {
                this.selectAllEntities();
            } else {
                this.clearSelection();
            }
        });

        // Relationship toggle
        document.getElementById('toggle-relationships-btn').addEventListener('click', () => {
            this.toggleRelationships();
        });

        // Modal events
        document.getElementById('close-entity-modal').addEventListener('click', () => {
            this.hideEntityModal();
        });

        document.getElementById('modal-cancel-btn').addEventListener('click', () => {
            this.hideEntityModal();
        });

        document.getElementById('modal-approve-btn').addEventListener('click', () => {
            this.handleModalApproval('approve');
        });

        document.getElementById('modal-approve-with-changes-btn').addEventListener('click', () => {
            this.handleModalApproval('approve_with_changes');
        });

        document.getElementById('modal-reject-btn').addEventListener('click', () => {
            this.handleModalApproval('reject');
        });

        // Click outside modal to close
        document.getElementById('entity-modal').addEventListener('click', (e) => {
            if (e.target.id === 'entity-modal') {
                this.hideEntityModal();
            }
        });

        const sessionPanel = document.getElementById('session-panel');
        if (sessionPanel) {
            sessionPanel.addEventListener('click', (e) => {
                if (e.target.id === 'session-panel') {
                    this.hideSessionPanel();
                }
            });
        }
        
        return true; // Successfully bound all events
    }

    // Session Management
    async showSessionPanel() {
        document.getElementById('session-panel').classList.remove('hidden');
        document.getElementById('document-title').focus();
    }

    hideSessionPanel() {
        document.getElementById('session-panel').classList.add('hidden');
        document.getElementById('session-form').reset();
    }

    async handleSessionCreation(e) {
        e.preventDefault();
        
        const formData = new FormData(e.target);
        const sessionData = {
            document_title: formData.get('document-title') || document.getElementById('document-title').value,
            document_source: formData.get('document-source') || document.getElementById('document-source').value,
            reviewer_id: formData.get('reviewer-id') || document.getElementById('reviewer-id').value || 'default_reviewer'
        };

        if (!sessionData.document_title || !sessionData.document_source) {
            this.showNotification('Please fill in all required fields', 'error');
            return;
        }

        this.showLoading();
        
        try {
            const response = await fetch('/api/approval/sessions', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(sessionData)
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            
            if (data.success) {
                this.currentSession = {
                    id: data.session_id,
                    document_title: sessionData.document_title,
                    document_source: sessionData.document_source,
                    reviewer_id: sessionData.reviewer_id
                };
                
                this.hideSessionPanel();
                this.updateSessionStatus();
                this.loadEntities();
                this.showNotification('Session created successfully', 'success');
            } else {
                throw new Error(data.error || 'Failed to create session');
            }
        } catch (error) {
            console.error('Session creation error:', error);
            this.showNotification(`Error creating session: ${error.message}`, 'error');
        } finally {
            this.hideLoading();
        }
    }

    async loadExistingSession() {
        // Try to load the most recent session from localStorage
        const savedSession = localStorage.getItem('approval_session');
        if (savedSession) {
            try {
                this.currentSession = JSON.parse(savedSession);
                this.updateSessionStatus();
                this.loadEntities();
            } catch (error) {
                console.error('Error loading saved session:', error);
                localStorage.removeItem('approval_session');
            }
        }
    }

    updateSessionStatus() {
        if (this.currentSession) {
            document.getElementById('session-status').textContent = 
                `Session: ${this.currentSession.document_title}`;
            localStorage.setItem('approval_session', JSON.stringify(this.currentSession));
        } else {
            document.getElementById('session-status').textContent = 'No Session';
            localStorage.removeItem('approval_session');
        }
    }

    // Data Loading
    async loadEntities() {
        if (!this.currentSession) {
            this.showNotification('No active session', 'warning');
            return;
        }

        this.showLoading();
        
        try {
            const params = new URLSearchParams({
                status_filter: this.filters.status,
                entity_types: this.filters.entityTypes.join(',')
            });

            const response = await fetch(`/api/approval/entities/${this.currentSession.document_source}?${params}`);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            
            if (data.success) {
                this.entities = data.entities || [];
                this.relationships = data.relationships || [];
                this.renderEntities();
                this.updateStatistics();
                this.updateProgress();
            } else {
                throw new Error(data.error || 'Failed to load entities');
            }
        } catch (error) {
            console.error('Error loading entities:', error);
            this.showNotification(`Error loading entities: ${error.message}`, 'error');
            this.entities = [];
            this.relationships = [];
            this.renderEntities();
        } finally {
            this.hideLoading();
        }
    }

    async refreshData() {
        this.selectedEntities.clear();
        this.updateSelectionUI();
        await this.loadEntities();
        this.showNotification('Data refreshed', 'success');
    }

    // Entity Rendering
    renderEntities() {
        const tbody = document.getElementById('entities-tbody');
        const noEntities = document.getElementById('no-entities');
        
        if (this.entities.length === 0) {
            tbody.innerHTML = '';
            noEntities.classList.remove('hidden');
            document.getElementById('entity-count').textContent = '0 entities';
            return;
        }

        noEntities.classList.add('hidden');
        
        const filteredEntities = this.getFilteredEntities();
        document.getElementById('entity-count').textContent = `${filteredEntities.length} entities`;

        tbody.innerHTML = filteredEntities.map(entity => this.renderEntityRow(entity)).join('');
        
        // Bind row events
        this.bindEntityRowEvents();
    }

    renderEntityRow(entity) {
        const isSelected = this.selectedEntities.has(entity.entity_id);
        const properties = this.formatProperties(entity.properties);
        const confidence = this.getConfidenceClass(entity.confidence);
        
        return `
            <tr data-entity-id="${entity.entity_id}" class="${isSelected ? 'selected' : ''}">
                <td class="select-col">
                    <input type="checkbox" class="entity-checkbox" 
                           ${isSelected ? 'checked' : ''} 
                           data-entity-id="${entity.entity_id}">
                </td>
                <td class="type-col">
                    <span class="entity-type">${entity.entity_type}</span>
                </td>
                <td class="name-col">
                    <strong>${this.escapeHtml(entity.name || 'Unnamed')}</strong>
                </td>
                <td class="properties-col">
                    <div class="entity-properties">${properties}</div>
                </td>
                <td class="confidence-col">
                    <span class="confidence-score ${confidence}">${(entity.confidence * 100).toFixed(1)}%</span>
                </td>
                <td class="status-col">
                    <span class="status-badge ${entity.status}">${entity.status}</span>
                </td>
                <td class="actions-col">
                    <div class="action-buttons">
                        <button class="action-btn approve" data-action="approve" data-entity-id="${entity.entity_id}">
                            <i class="fas fa-check"></i>
                        </button>
                        <button class="action-btn reject" data-action="reject" data-entity-id="${entity.entity_id}">
                            <i class="fas fa-times"></i>
                        </button>
                        <button class="action-btn edit" data-action="edit" data-entity-id="${entity.entity_id}">
                            <i class="fas fa-edit"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `;
    }

    formatProperties(properties) {
        if (!properties || typeof properties !== 'object') {
            return '<span class="text-muted">No properties</span>';
        }

        const items = Object.entries(properties)
            .filter(([key, value]) => value !== null && value !== undefined && value !== '')
            .slice(0, 3) // Show only first 3 properties
            .map(([key, value]) => 
                `<div class="property-item">
                    <span class="property-key">${this.escapeHtml(key)}:</span>
                    <span class="property-value">${this.escapeHtml(String(value))}</span>
                </div>`
            );

        return items.length > 0 ? items.join('') : '<span class="text-muted">No properties</span>';
    }

    getConfidenceClass(confidence) {
        if (confidence >= 0.8) return 'confidence-high';
        if (confidence >= 0.6) return 'confidence-medium';
        return 'confidence-low';
    }

    bindEntityRowEvents() {
        // Checkbox events
        document.querySelectorAll('.entity-checkbox').forEach(checkbox => {
            checkbox.addEventListener('change', (e) => {
                const entityId = e.target.dataset.entityId;
                if (e.target.checked) {
                    this.selectedEntities.add(entityId);
                } else {
                    this.selectedEntities.delete(entityId);
                }
                this.updateSelectionUI();
            });
        });

        // Action button events
        document.querySelectorAll('.action-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const action = e.currentTarget.dataset.action;
                const entityId = e.currentTarget.dataset.entityId;
                this.handleEntityAction(action, entityId);
            });
        });

        // Row click to show details
        document.querySelectorAll('#entities-tbody tr').forEach(row => {
            row.addEventListener('click', (e) => {
                if (e.target.type !== 'checkbox' && !e.target.closest('.action-btn')) {
                    const entityId = row.dataset.entityId;
                    this.showEntityDetails(entityId);
                }
            });
        });
    }

    // Entity Actions
    async handleEntityAction(action, entityId) {
        const entity = this.entities.find(e => e.entity_id === entityId);
        if (!entity) return;

        if (action === 'edit') {
            this.showEntityDetails(entityId);
            return;
        }

        const endpoint = action === 'approve' ? 'approve' : 'reject';
        const reviewerId = this.currentSession?.reviewer_id || 'default_reviewer';

        this.showLoading();

        try {
            const response = await fetch(`/api/pre-approval/entities/${entityId}/${endpoint}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ reviewer_id: reviewerId })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            
            if (data.success) {
                // Update entity status in local data
                entity.status = action === 'approve' ? 'approved' : 'rejected';
                entity.reviewer_id = reviewerId;
                entity.reviewed_at = new Date().toISOString();
                
                this.renderEntities();
                this.updateStatistics();
                this.updateProgress();
                
                this.showNotification(`Entity ${action}d successfully`, 'success');
                
                // Auto-trigger Neo4j ingestion if entity was approved
                if (action === 'approve') {
                    this.triggerAutoIngestion(`Entity ${entity.name} approved and queued for ingestion`);
                }
            } else {
                throw new Error(data.error || `Failed to ${action} entity`);
            }
        } catch (error) {
            console.error(`Error ${action}ing entity:`, error);
            this.showNotification(`Error ${action}ing entity: ${error.message}`, 'error');
        } finally {
            this.hideLoading();
        }
    }

    async handleBulkApproval() {
        if (this.selectedEntities.size === 0) {
            this.showNotification('No entities selected', 'warning');
            return;
        }

        const entityIds = Array.from(this.selectedEntities);
        const reviewerId = this.currentSession?.reviewer_id || 'default_reviewer';

        this.showLoading();

        try {
            const response = await fetch('/api/approval/entities/bulk-approve', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    entity_ids: entityIds,
                    reviewer_id: reviewerId
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            
            if (data.success) {
                // Update entities status in local data
                entityIds.forEach(entityId => {
                    const entity = this.entities.find(e => e.entity_id === entityId);
                    if (entity) {
                        entity.status = 'approved';
                        entity.reviewer_id = reviewerId;
                        entity.reviewed_at = new Date().toISOString();
                    }
                });
                
                this.selectedEntities.clear();
                this.renderEntities();
                this.updateStatistics();
                this.updateProgress();
                this.updateSelectionUI();
                
                this.showNotification(`${data.approved_count} entities approved successfully`, 'success');
                
                // Auto-trigger Neo4j ingestion for bulk approved entities
                this.triggerAutoIngestion(`${data.approved_count} entities approved and queued for ingestion`);
            } else {
                throw new Error(data.error || 'Failed to approve entities');
            }
        } catch (error) {
            console.error('Error in bulk approval:', error);
            this.showNotification(`Error in bulk approval: ${error.message}`, 'error');
        } finally {
            this.hideLoading();
        }
    }

    async handleCleanPending() {
        const pendingEntities = this.entities.filter(e => e.status === 'pending');
        
        if (pendingEntities.length === 0) {
            this.showNotification('No pending entities to clean', 'info');
            return;
        }

        // Confirmation dialog
        const confirmed = confirm(
            `Are you sure you want to delete all ${pendingEntities.length} pending entities? This action cannot be undone.`
        );

        if (!confirmed) {
            return;
        }

        this.showLoading();

        try {
            const response = await fetch('/api/pre-approval/entities/clean-pending', {
                method: 'DELETE',
                headers: { 'Content-Type': 'application/json' }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            
            if (data.success) {
                // Remove pending entities from local data
                this.entities = this.entities.filter(e => e.status !== 'pending');
                this.selectedEntities.clear();
                
                this.renderEntities();
                this.updateStatistics();
                this.updateProgress();
                this.updateSelectionUI();
                
                this.showNotification(`${data.deleted_count} pending entities cleaned successfully`, 'success');
            } else {
                throw new Error(data.error || 'Failed to clean pending entities');
            }
        } catch (error) {
            console.error('Error cleaning pending entities:', error);
            this.showNotification(`Error cleaning pending entities: ${error.message}`, 'error');
        } finally {
            this.hideLoading();
        }
    }

    async handleApproveAll() {
        const pendingEntities = this.entities.filter(e => e.status === 'pending');
        
        if (pendingEntities.length === 0) {
            this.showNotification('No pending entities to approve', 'info');
            return;
        }

        // Confirmation dialog
        const confirmed = confirm(
            `Are you sure you want to approve all ${pendingEntities.length} pending entities?`
        );

        if (!confirmed) {
            return;
        }

        const reviewerId = this.currentSession?.reviewer_id || 'default_reviewer';

        this.showLoading();

        try {
            const response = await fetch('/api/pre-approval/entities/approve-all', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    reviewer_id: reviewerId
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            
            if (data.success) {
                // Update all pending entities to approved in local data
                pendingEntities.forEach(entity => {
                    entity.status = 'approved';
                    entity.reviewer_id = reviewerId;
                    entity.reviewed_at = new Date().toISOString();
                });
                
                this.selectedEntities.clear();
                this.renderEntities();
                this.updateStatistics();
                this.updateProgress();
                this.updateSelectionUI();
                
                this.showNotification(`${data.approved_count} entities approved successfully`, 'success');
                
                // Auto-trigger Neo4j ingestion for all approved entities
                this.triggerAutoIngestion(`${data.approved_count} entities approved and queued for ingestion`);
            } else {
                throw new Error(data.error || 'Failed to approve all entities');
            }
        } catch (error) {
            console.error('Error approving all entities:', error);
            this.showNotification(`Error approving all entities: ${error.message}`, 'error');
        } finally {
            this.hideLoading();
        }
    }

    // Entity Details Modal
    showEntityDetails(entityId) {
        const entity = this.entities.find(e => e.entity_id === entityId);
        if (!entity) return;

        this.currentEntity = entity;
        
        // Populate entity details
        const detailsContainer = document.getElementById('entity-details');
        detailsContainer.innerHTML = `
            <div class="entity-overview">
                <h4>${this.escapeHtml(entity.name || 'Unnamed Entity')}</h4>
                <p><strong>Type:</strong> ${entity.entity_type}</p>
                <p><strong>Confidence:</strong> ${(entity.confidence * 100).toFixed(1)}%</p>
                <p><strong>Status:</strong> <span class="status-badge ${entity.status}">${entity.status}</span></p>
                ${entity.reviewed_at ? `<p><strong>Reviewed:</strong> ${new Date(entity.reviewed_at).toLocaleString()}</p>` : ''}
            </div>
        `;

        // Populate property editor
        this.populatePropertyEditor(entity);
        
        // Clear previous notes
        document.getElementById('modal-review-notes').value = entity.review_notes || '';
        
        // Show modal
        document.getElementById('entity-modal').classList.remove('hidden');
    }

    populatePropertyEditor(entity) {
        const fieldsContainer = document.getElementById('property-fields');
        const properties = entity.properties || {};
        
        // Define common fields based on entity type
        const commonFields = this.getCommonFields(entity.entity_type);
        
        fieldsContainer.innerHTML = commonFields.map(field => {
            const value = properties[field.name] || '';
            return `
                <div class="form-group">
                    <label for="prop-${field.name}">${field.label}:</label>
                    <input type="${field.type}" 
                           id="prop-${field.name}" 
                           name="${field.name}"
                           value="${this.escapeHtml(String(value))}"
                           placeholder="${field.placeholder || ''}">
                </div>
            `;
        }).join('');
    }

    getCommonFields(entityType) {
        const commonFields = {
            'Person': [
                { name: 'age', label: 'Age', type: 'number', placeholder: 'Age in years' },
                { name: 'occupation', label: 'Occupation', type: 'text', placeholder: 'Job title or profession' },
                { name: 'location', label: 'Location', type: 'text', placeholder: 'City, Country' },
                { name: 'email', label: 'Email', type: 'email', placeholder: 'email@example.com' },
                { name: 'phone', label: 'Phone', type: 'tel', placeholder: '+1-234-567-8900' }
            ],
            'Company': [
                { name: 'industry', label: 'Industry', type: 'text', placeholder: 'Business sector' },
                { name: 'founded_year', label: 'Founded Year', type: 'number', placeholder: 'YYYY' },
                { name: 'headquarters', label: 'Headquarters', type: 'text', placeholder: 'City, Country' },
                { name: 'website', label: 'Website', type: 'url', placeholder: 'https://example.com' },
                { name: 'employees', label: 'Employees', type: 'number', placeholder: 'Number of employees' }
            ]
        };
        
        return commonFields[entityType] || [
            { name: 'description', label: 'Description', type: 'text', placeholder: 'Entity description' }
        ];
    }

    hideEntityModal() {
        document.getElementById('entity-modal').classList.add('hidden');
        this.currentEntity = null;
    }

    async handleModalApproval(action) {
        if (!this.currentEntity) return;

        const entityId = this.currentEntity.entity_id;
        const reviewNotes = document.getElementById('modal-review-notes').value;
        const reviewerId = this.currentSession?.reviewer_id || 'default_reviewer';
        
        let modifiedData = null;
        
        if (action === 'approve_with_changes') {
            // Collect modified properties
            const formData = new FormData();
            document.querySelectorAll('#property-fields input').forEach(input => {
                if (input.value.trim()) {
                    formData.append(input.name, input.value.trim());
                }
            });
            
            modifiedData = Object.fromEntries(formData.entries());
        }

        const endpoint = action === 'reject' ? 'reject' : 'approve';
        
        this.showLoading();

        try {
            const requestBody = {
                reviewer_id: reviewerId,
                review_notes: reviewNotes
            };
            
            if (modifiedData) {
                requestBody.modified_data = modifiedData;
            }

            const response = await fetch(`/api/pre-approval/entities/${entityId}/${endpoint}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(requestBody)
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            
            if (data.success) {
                // Update entity in local data
                const entity = this.entities.find(e => e.entity_id === entityId);
                if (entity) {
                    entity.status = action === 'reject' ? 'rejected' : 'approved';
                    entity.reviewer_id = reviewerId;
                    entity.reviewed_at = new Date().toISOString();
                    entity.review_notes = reviewNotes;
                    
                    if (modifiedData) {
                        entity.properties = { ...entity.properties, ...modifiedData };
                    }
                }
                
                this.hideEntityModal();
                this.renderEntities();
                this.updateStatistics();
                this.updateProgress();
                
                const actionText = action === 'reject' ? 'rejected' : 
                                 action === 'approve_with_changes' ? 'approved with changes' : 'approved';
                this.showNotification(`Entity ${actionText} successfully`, 'success');
                
                // Auto-trigger Neo4j ingestion if entity was approved
                if (action !== 'reject') {
                    this.triggerAutoIngestion(`Entity ${entity.name} ${actionText} and queued for ingestion`);
                }
            } else {
                throw new Error(data.error || `Failed to ${action} entity`);
            }
        } catch (error) {
            console.error(`Error ${action}ing entity:`, error);
            this.showNotification(`Error processing entity: ${error.message}`, 'error');
        } finally {
            this.hideLoading();
        }
    }

    // Filtering and Selection
    updateFilters() {
        const entityTypeFilter = document.getElementById('entity-type-filter');
        const statusFilter = document.getElementById('status-filter');
        
        this.filters.entityTypes = Array.from(entityTypeFilter.selectedOptions).map(opt => opt.value);
        this.filters.status = statusFilter.value;
        
        this.filterEntities();
    }

    filterEntities() {
        this.renderEntities();
    }

    getFilteredEntities() {
        return this.entities.filter(entity => {
            // Entity type filter
            if (this.filters.entityTypes.length > 0 && 
                !this.filters.entityTypes.includes(entity.entity_type)) {
                return false;
            }
            
            // Status filter
            if (this.filters.status !== 'all' && entity.status !== this.filters.status) {
                return false;
            }
            
            // Search filter
            if (this.filters.search) {
                const searchTerm = this.filters.search.toLowerCase();
                const name = (entity.name || '').toLowerCase();
                const properties = JSON.stringify(entity.properties || {}).toLowerCase();
                
                if (!name.includes(searchTerm) && !properties.includes(searchTerm)) {
                    return false;
                }
            }
            
            return true;
        });
    }

    selectAllEntities() {
        const filteredEntities = this.getFilteredEntities();
        filteredEntities.forEach(entity => {
            this.selectedEntities.add(entity.entity_id);
        });
        this.updateSelectionUI();
        this.renderEntities();
    }

    clearSelection() {
        this.selectedEntities.clear();
        this.updateSelectionUI();
        this.renderEntities();
    }

    updateSelectionUI() {
        const selectedCount = this.selectedEntities.size;
        const bulkApproveBtn = document.getElementById('bulk-approve-btn');
        const clearSelectionBtn = document.getElementById('clear-selection-btn');
        
        bulkApproveBtn.disabled = selectedCount === 0;
        clearSelectionBtn.disabled = selectedCount === 0;
        
        if (selectedCount > 0) {
            bulkApproveBtn.innerHTML = `<i class="fas fa-check-double"></i> Bulk Approve (${selectedCount})`;
        } else {
            bulkApproveBtn.innerHTML = `<i class="fas fa-check-double"></i> Bulk Approve`;
        }
    }

    // Relationships
    toggleRelationships() {
        const container = document.getElementById('relationships-container');
        const btn = document.getElementById('toggle-relationships-btn');
        
        if (container.classList.contains('hidden')) {
            container.classList.remove('hidden');
            btn.innerHTML = '<i class="fas fa-eye-slash"></i> Hide Relationships';
            this.renderRelationships();
        } else {
            container.classList.add('hidden');
            btn.innerHTML = '<i class="fas fa-eye"></i> Show Relationships';
        }
    }

    renderRelationships() {
        const tbody = document.getElementById('relationships-tbody');
        
        tbody.innerHTML = this.relationships.map(rel => `
            <tr>
                <td class="type-col">${rel.relationship_type}</td>
                <td class="source-col">${this.escapeHtml(rel.source_name || rel.source_id)}</td>
                <td class="target-col">${this.escapeHtml(rel.target_name || rel.target_id)}</td>
                <td class="confidence-col">
                    <span class="confidence-score ${this.getConfidenceClass(rel.confidence)}">
                        ${(rel.confidence * 100).toFixed(1)}%
                    </span>
                </td>
                <td class="status-col">
                    <span class="status-badge ${rel.status}">${rel.status}</span>
                </td>
                <td class="actions-col">
                    <div class="action-buttons">
                        <button class="action-btn approve" data-action="approve-rel" data-rel-id="${rel.relationship_id}">
                            <i class="fas fa-check"></i>
                        </button>
                        <button class="action-btn reject" data-action="reject-rel" data-rel-id="${rel.relationship_id}">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `).join('');
        
        document.getElementById('relationship-count').textContent = `${this.relationships.length} relationships`;
    }

    // Statistics and Progress
    updateStatistics() {
        const total = this.entities.length;
        const approved = this.entities.filter(e => e.status === 'approved').length;
        const rejected = this.entities.filter(e => e.status === 'rejected').length;
        const pending = this.entities.filter(e => e.status === 'pending').length;
        
        document.getElementById('total-entities').textContent = total;
        document.getElementById('approved-count').textContent = approved;
        document.getElementById('rejected-count').textContent = rejected;
        document.getElementById('pending-count').textContent = pending;
    }

    updateProgress() {
        const total = this.entities.length;
        const reviewed = this.entities.filter(e => e.status !== 'pending').length;
        const progress = total > 0 ? Math.round((reviewed / total) * 100) : 0;
        
        document.getElementById('approval-progress').textContent = `${progress}%`;
    }

    // Notification System
    setupNotificationSystem() {
        this.notifications = document.getElementById('notifications');
    }

    showNotification(message, type = 'info', duration = 5000) {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        
        const icon = this.getNotificationIcon(type);
        notification.innerHTML = `
            <i class="${icon}"></i>
            <span>${this.escapeHtml(message)}</span>
        `;
        
        this.notifications.appendChild(notification);
        
        // Auto remove
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, duration);
        
        // Click to remove
        notification.addEventListener('click', () => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        });
    }

    getNotificationIcon(type) {
        const icons = {
            success: 'fas fa-check-circle',
            error: 'fas fa-exclamation-circle',
            warning: 'fas fa-exclamation-triangle',
            info: 'fas fa-info-circle'
        };
        return icons[type] || icons.info;
    }

    // Loading Overlay
    showLoading() {
        document.getElementById('loading-overlay').classList.remove('hidden');
    }

    hideLoading() {
        document.getElementById('loading-overlay').classList.add('hidden');
    }

    // Neo4j Auto-Ingestion
    async triggerAutoIngestion(message = 'Auto-triggering Neo4j ingestion') {
        try {
            this.showNotification(message, 'info');
            
            const response = await fetch('/api/pre-approval/ingest-approved', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            
            if (data.entities_ingested > 0) {
                this.showNotification(
                    `✅ ${data.entities_ingested} entities successfully ingested into Neo4j`, 
                    'success'
                );
            } else if (data.entities_processed === 0) {
                this.showNotification('ℹ️ No approved entities ready for ingestion', 'info');
            } else {
                this.showNotification('⚠️ Ingestion completed with some issues', 'warning');
            }
        } catch (error) {
            console.error('Error triggering auto-ingestion:', error);
            this.showNotification(`Auto-ingestion failed: ${error.message}`, 'error');
        }
    }

    // Utility Functions
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Skip initialization if we're on the unified dashboard
    if (window.location.pathname === '/unified' || document.body.classList.contains('unified-page')) {
        console.info('ApprovalDashboard: Skipping initialization on unified dashboard');
        return;
    }
    
    // Only initialize if required elements exist
    if (!document.getElementById('new-session-btn')) {
        console.warn('ApprovalDashboard: Required elements not found, skipping initialization');
        return;
    }
    
    window.approvalDashboard = new ApprovalDashboard();
});

// Error handling
window.addEventListener('error', (e) => {
    console.error('JavaScript error:', e.error);
    if (window.approvalDashboard) {
        window.approvalDashboard.showNotification('An unexpected error occurred', 'error');
    }
});

window.addEventListener('unhandledrejection', (e) => {
    console.error('Unhandled promise rejection:', e.reason);
    if (window.approvalDashboard) {
        window.approvalDashboard.showNotification('An unexpected error occurred', 'error');
    }
});