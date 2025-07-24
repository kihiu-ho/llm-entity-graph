/**
 * Entity Management Main - Orchestrates the complete entity management system
 * Integrates table editor, validation engine, and all management features
 */

class EntityManagementSystem {
    constructor() {
        this.currentSessionId = null;
        this.entitiesTable = null;
        this.relationshipsTable = null;
        this.currentTab = 'entities';
        this.conflictsData = null;
        
        this.init();
    }
    
    init() {
        this.setupTabs();
        this.setupControls();
        this.setupModals();
        this.setupTables();
        this.loadSessions();
        this.setupKeyboardShortcuts();
    }
    
    setupTabs() {
        const tabs = document.querySelectorAll('.tab');
        const tabContents = document.querySelectorAll('.tab-content');
        
        tabs.forEach(tab => {
            tab.addEventListener('click', () => {
                // Remove active class from all tabs and contents
                tabs.forEach(t => t.classList.remove('active'));
                tabContents.forEach(content => content.classList.remove('active'));
                
                // Add active class to clicked tab and corresponding content
                tab.classList.add('active');
                const tabName = tab.dataset.tab;
                const content = document.getElementById(`${tabName}Tab`);
                if (content) {
                    content.classList.add('active');
                    this.currentTab = tabName;
                    this.onTabChange(tabName);
                }
            });
        });
    }
    
    setupControls() {
        // Session selection
        const sessionSelect = document.getElementById('sessionSelect');
        if (sessionSelect) {
            sessionSelect.addEventListener('change', (e) => {
                this.selectSession(e.target.value);
            });
        }
        
        // Filters
        const statusFilter = document.getElementById('statusFilter');
        const typeFilter = document.getElementById('typeFilter');
        const searchInput = document.getElementById('searchInput');
        
        if (statusFilter) {
            statusFilter.addEventListener('change', () => this.applyFilters());
        }
        
        if (typeFilter) {
            typeFilter.addEventListener('change', () => this.applyFilters());
        }
        
        if (searchInput) {
            searchInput.addEventListener('input', this.debounce(() => this.applyFilters(), 300));
        }
        
        // Action buttons
        this.setupActionButtons();
        
        // Batch operation buttons
        this.setupBatchOperations();
    }
    
    setupActionButtons() {
        const buttons = {
            'addEntityBtn': () => this.showEntityModal(),
            'addRelationshipBtn': () => this.showRelationshipModal(),
            'detectConflictsBtn': () => this.detectConflicts(),
            'exportBtn': () => this.showExportOptions(),
            'importBtn': () => this.showImportModal()
        };
        
        Object.entries(buttons).forEach(([id, handler]) => {
            const button = document.getElementById(id);
            if (button) {
                button.addEventListener('click', handler);
            }
        });
    }
    
    setupBatchOperations() {
        const batchButtons = {
            'batchApproveBtn': () => this.batchApprove(),
            'batchRejectBtn': () => this.batchReject(),
            'batchDeleteBtn': () => this.batchDelete()
        };
        
        Object.entries(batchButtons).forEach(([id, handler]) => {
            const button = document.getElementById(id);
            if (button) {
                button.addEventListener('click', handler);
            }
        });
    }
    
    setupModals() {
        // Entity modal
        this.setupEntityModal();
        
        // Relationship modal
        this.setupRelationshipModal();
        
        // Import modal
        this.setupImportModal();
        
        // Generic modal close handlers
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
    
    setupEntityModal() {
        const form = document.getElementById('entityForm');
        if (form) {
            form.addEventListener('submit', async (e) => {
                e.preventDefault();
                await this.saveEntity();
            });
        }
        
        const cancelBtn = document.getElementById('entityCancelBtn');
        if (cancelBtn) {
            cancelBtn.addEventListener('click', () => this.closeModals());
        }
        
        // Real-time validation for entity form
        const entityInputs = form?.querySelectorAll('input, select, textarea');
        entityInputs?.forEach(input => {
            input.addEventListener('input', () => {
                this.validateEntityField(input);
            });
        });
    }
    
    setupRelationshipModal() {
        const form = document.getElementById('relationshipForm');
        if (form) {
            form.addEventListener('submit', async (e) => {
                e.preventDefault();
                await this.saveRelationship();
            });
        }
        
        const cancelBtn = document.getElementById('relationshipCancelBtn');
        if (cancelBtn) {
            cancelBtn.addEventListener('click', () => this.closeModals());
        }
    }
    
    setupImportModal() {
        const form = document.getElementById('importForm');
        if (form) {
            form.addEventListener('submit', async (e) => {
                e.preventDefault();
                await this.importData();
            });
        }
        
        const cancelBtn = document.getElementById('importCancelBtn');
        if (cancelBtn) {
            cancelBtn.addEventListener('click', () => this.closeModals());
        }
        
        // File format detection
        const fileInput = document.getElementById('importFile');
        const formatSelect = document.getElementById('importFormat');
        
        if (fileInput && formatSelect) {
            fileInput.addEventListener('change', (e) => {
                const file = e.target.files[0];
                if (file) {
                    const extension = file.name.split('.').pop().toLowerCase();
                    const formatMap = {
                        'json': 'json',
                        'csv': 'csv',
                        'xlsx': 'excel',
                        'xls': 'excel'
                    };
                    
                    if (formatMap[extension]) {
                        formatSelect.value = formatMap[extension];
                    }
                }
            });
        }
    }
    
    setupTables() {
        // Setup entities table
        this.entitiesTable = new EntityTableEditor('entitiesTable', {
            onDataChange: (data) => this.onEntitiesDataChange(data),
            onSelectionChange: (selected) => this.onSelectionChange(selected),
            onEdit: (editData) => this.onEntityEdit(editData),
            onValidation: (validationData) => this.validateEntityData(validationData)
        });
        
        // Setup relationships table
        this.relationshipsTable = new EntityTableEditor('relationshipsTable', {
            onDataChange: (data) => this.onRelationshipsDataChange(data),
            onSelectionChange: (selected) => this.onSelectionChange(selected),
            onEdit: (editData) => this.onRelationshipEdit(editData),
            onValidation: (validationData) => this.validateRelationshipData(validationData)
        });
        
        // Custom render methods
        this.entitiesTable.render = () => this.renderEntitiesTable();
        this.relationshipsTable.render = () => this.renderRelationshipsTable();
    }
    
    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey || e.metaKey) {
                switch (e.key) {
                    case 'n':
                        e.preventDefault();
                        if (this.currentTab === 'entities') {
                            this.showEntityModal();
                        } else if (this.currentTab === 'relationships') {
                            this.showRelationshipModal();
                        }
                        break;
                    case 'f':
                        e.preventDefault();
                        document.getElementById('searchInput')?.focus();
                        break;
                    case 'r':
                        e.preventDefault();
                        this.refreshCurrentData();
                        break;
                }
            }
        });
    }
    
    async loadSessions() {
        try {
            const response = await fetch('/api/staging/sessions');
            const data = await response.json();
            
            if (data.success) {
                this.populateSessionSelect(data.sessions);
            }
        } catch (error) {
            console.error('Error loading sessions:', error);
            this.showNotification('Failed to load sessions', 'error');
        }
    }
    
    populateSessionSelect(sessions) {
        const select = document.getElementById('sessionSelect');
        if (!select) return;
        
        select.innerHTML = '<option value="">Select a session...</option>';
        
        sessions.forEach(session => {
            const option = document.createElement('option');
            option.value = session.session_id;
            option.textContent = `${session.document_title} (${session.status})`;
            select.appendChild(option);
        });
    }
    
    async selectSession(sessionId) {
        if (!sessionId) {
            this.currentSessionId = null;
            this.clearTables();
            return;
        }
        
        this.currentSessionId = sessionId;
        window.currentSessionId = sessionId; // For validation engine
        
        this.showLoading();
        
        try {
            await this.loadSessionData(sessionId);
            this.hideLoading();
        } catch (error) {
            console.error('Error loading session data:', error);
            this.showNotification('Failed to load session data', 'error');
            this.hideLoading();
        }
    }
    
    async loadSessionData(sessionId) {
        const response = await fetch(`/api/staging/sessions/${sessionId}`);
        const data = await response.json();
        
        if (data.success) {
            const session = data.session;
            
            // Update tables
            this.entitiesTable.setData(session.entities || []);
            this.relationshipsTable.setData(session.relationships || []);
            
            // Update entity selects in relationship modal
            this.updateEntitySelects(session.entities || []);
            
            // Update UI state
            this.updateBatchButtonStates();
        } else {
            throw new Error(data.error || 'Failed to load session');
        }
    }
    
    updateEntitySelects(entities) {
        const sourceSelect = document.getElementById('sourceEntitySelect');
        const targetSelect = document.getElementById('targetEntitySelect');
        
        [sourceSelect, targetSelect].forEach(select => {
            if (select) {
                select.innerHTML = '<option value="">Select entity...</option>';
                entities.forEach(entity => {
                    const option = document.createElement('option');
                    option.value = entity.id;
                    option.textContent = `${entity.name} (${entity.type})`;
                    select.appendChild(option);
                });
            }
        });
    }
    
    applyFilters() {
        const statusFilter = document.getElementById('statusFilter')?.value;
        const typeFilter = document.getElementById('typeFilter')?.value;
        const searchQuery = document.getElementById('searchInput')?.value;
        
        const filters = {};
        if (statusFilter) filters.status = statusFilter;
        if (typeFilter) filters.type = typeFilter;
        
        // Apply filters to current table
        if (this.currentTab === 'entities') {
            this.entitiesTable.filter(filters);
            if (searchQuery) {
                this.entitiesTable.search(searchQuery);
            }
        } else if (this.currentTab === 'relationships') {
            this.relationshipsTable.filter(filters);
            if (searchQuery) {
                this.relationshipsTable.search(searchQuery);
            }
        }
    }
    
    onTabChange(tabName) {
        switch (tabName) {
            case 'conflicts':
                this.loadConflicts();
                break;
            case 'analytics':
                this.loadAnalytics();
                break;
        }
    }
    
    async loadConflicts() {
        if (!this.currentSessionId) {
            document.getElementById('conflictsContent').innerHTML = 
                '<p class="text-center text-muted">Please select a session to detect conflicts</p>';
            return;
        }
        
        try {
            const response = await fetch(`/api/conflicts/session/${this.currentSessionId}`);
            const data = await response.json();
            
            if (data.success) {
                this.conflictsData = data;
                this.renderConflicts(data);
            } else {
                throw new Error(data.error);
            }
        } catch (error) {
            console.error('Error loading conflicts:', error);
            document.getElementById('conflictsContent').innerHTML = 
                '<div class="error-state"><i class="fas fa-exclamation-triangle"></i><p>Failed to load conflicts</p></div>';
        }
    }
    
    renderConflicts(conflictsData) {
        const container = document.getElementById('conflictsContent');
        if (!container) return;
        
        const totalConflicts = conflictsData.total_conflicts || 0;
        
        if (totalConflicts === 0) {
            container.innerHTML = '<p class="text-center text-success"><i class="fas fa-check-circle"></i> No conflicts detected</p>';
            return;
        }
        
        let html = `
            <div class="conflicts-summary">
                <h4>Found ${totalConflicts} conflicts</h4>
                <div class="severity-counts">
                    <span class="badge badge-danger">High: ${conflictsData.severity_counts?.high || 0}</span>
                    <span class="badge badge-warning">Medium: ${conflictsData.severity_counts?.medium || 0}</span>
                    <span class="badge badge-info">Low: ${conflictsData.severity_counts?.low || 0}</span>
                </div>
            </div>
        `;
        
        // Render each conflict type
        Object.entries(conflictsData.conflicts || {}).forEach(([type, conflicts]) => {
            if (conflicts.length > 0) {
                html += this.renderConflictSection(type, conflicts);
            }
        });
        
        container.innerHTML = html;
    }
    
    renderConflictSection(type, conflicts) {
        const title = type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
        
        let html = `
            <div class="conflict-section">
                <h5>${title} (${conflicts.length})</h5>
                <div class="conflict-items">
        `;
        
        conflicts.forEach(conflict => {
            html += `
                <div class="conflict-item severity-${conflict.severity}">
                    <div class="conflict-header">
                        <span class="conflict-type">${conflict.type}</span>
                        <span class="conflict-severity badge badge-${conflict.severity}">${conflict.severity}</span>
                    </div>
                    <div class="conflict-description">${conflict.description}</div>
                    <div class="conflict-actions">
                        ${conflict.suggested_actions?.map(action => 
                            `<button class="btn btn-sm btn-outline-primary" onclick="entityManagement.resolveConflict('${conflict.id}', '${action}')">${action}</button>`
                        ).join(' ') || ''}
                    </div>
                </div>
            `;
        });
        
        html += '</div></div>';
        return html;
    }
    
    async resolveConflict(conflictId, action) {
        if (!this.currentSessionId) return;
        
        try {
            const response = await fetch('/api/conflicts/resolve', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: this.currentSessionId,
                    conflict_id: conflictId,
                    action: action,
                    user: 'web_user'
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showNotification(`Conflict resolved: ${data.message}`, 'success');
                this.loadConflicts(); // Refresh conflicts
                this.refreshCurrentData(); // Refresh main data
            } else {
                throw new Error(data.error);
            }
        } catch (error) {
            console.error('Error resolving conflict:', error);
            this.showNotification('Failed to resolve conflict', 'error');
        }
    }
    
    async loadAnalytics() {
        if (!this.currentSessionId) {
            document.getElementById('analyticsContent').innerHTML = 
                '<p class="text-center text-muted">Please select a session to view analytics</p>';
            return;
        }
        
        try {
            const response = await fetch(`/api/analytics/sessions/${this.currentSessionId}`);
            const data = await response.json();
            
            if (data.success) {
                this.renderAnalytics(data);
            } else {
                throw new Error(data.error);
            }
        } catch (error) {
            console.error('Error loading analytics:', error);
            document.getElementById('analyticsContent').innerHTML = 
                '<div class="error-state"><i class="fas fa-exclamation-triangle"></i><p>Failed to load analytics</p></div>';
        }
    }
    
    renderAnalytics(analyticsData) {
        const container = document.getElementById('analyticsContent');
        if (!container) return;
        
        const stats = analyticsData.statistics || {};
        const sessionInfo = analyticsData.session_info || {};
        
        container.innerHTML = `
            <div class="analytics-overview">
                <div class="row">
                    <div class="col-md-6">
                        <h5>Session Information</h5>
                        <table class="table table-sm">
                            <tr><td>Document:</td><td>${sessionInfo.document_title || 'N/A'}</td></tr>
                            <tr><td>Status:</td><td><span class="badge badge-${sessionInfo.status}">${sessionInfo.status || 'N/A'}</span></td></tr>
                            <tr><td>Created:</td><td>${new Date(sessionInfo.created_at).toLocaleString()}</td></tr>
                            <tr><td>Updated:</td><td>${new Date(sessionInfo.updated_at).toLocaleString()}</td></tr>
                        </table>
                    </div>
                    <div class="col-md-6">
                        <h5>Statistics</h5>
                        <table class="table table-sm">
                            <tr><td>Total Entities:</td><td>${stats.total_entities || 0}</td></tr>
                            <tr><td>Total Relationships:</td><td>${stats.total_relationships || 0}</td></tr>
                            <tr><td>Approved Entities:</td><td>${stats.approved_entities || 0}</td></tr>
                            <tr><td>Pending Items:</td><td>${stats.pending_entities || 0}</td></tr>
                        </table>
                    </div>
                </div>
            </div>
        `;
    }
    
    // Modal management
    showEntityModal(entityData = null) {
        const modal = document.getElementById('entityModal');
        const form = document.getElementById('entityForm');
        const title = document.getElementById('entityModalTitle');
        
        if (entityData) {
            title.textContent = 'Edit Entity';
            this.populateEntityForm(entityData);
        } else {
            title.textContent = 'Add Entity';
            form.reset();
        }
        
        modal.style.display = 'block';
    }
    
    showRelationshipModal(relationshipData = null) {
        const modal = document.getElementById('relationshipModal');
        const form = document.getElementById('relationshipForm');
        const title = document.getElementById('relationshipModalTitle');
        
        if (relationshipData) {
            title.textContent = 'Edit Relationship';
            this.populateRelationshipForm(relationshipData);
        } else {
            title.textContent = 'Add Relationship';
            form.reset();
        }
        
        modal.style.display = 'block';
    }
    
    showImportModal() {
        const modal = document.getElementById('importModal');
        modal.style.display = 'block';
    }
    
    closeModals() {
        const modals = document.querySelectorAll('.modal');
        modals.forEach(modal => {
            modal.style.display = 'none';
        });
    }
    
    // Utility methods
    showLoading() {
        const overlay = document.getElementById('loadingOverlay');
        if (overlay) overlay.style.display = 'flex';
    }
    
    hideLoading() {
        const overlay = document.getElementById('loadingOverlay');
        if (overlay) overlay.style.display = 'none';
    }
    
    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <i class="fas fa-${type === 'success' ? 'check' : type === 'error' ? 'times' : 'info'}-circle"></i>
            <span>${message}</span>
        `;
        
        // Add to page
        document.body.appendChild(notification);
        
        // Auto-remove after 3 seconds
        setTimeout(() => {
            notification.remove();
        }, 3000);
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
    
    clearTables() {
        this.entitiesTable?.setData([]);
        this.relationshipsTable?.setData([]);
    }
    
    updateBatchButtonStates() {
        // This would be implemented to enable/disable batch buttons based on selection
    }
    
    refreshCurrentData() {
        if (this.currentSessionId) {
            this.loadSessionData(this.currentSessionId);
        }
    }
    
    // Placeholder methods for table callbacks
    onEntitiesDataChange(data) { /* Implementation needed */ }
    onRelationshipsDataChange(data) { /* Implementation needed */ }
    onSelectionChange(selected) { /* Implementation needed */ }
    onEntityEdit(editData) { /* Implementation needed */ }
    onRelationshipEdit(editData) { /* Implementation needed */ }
    async validateEntityData(validationData) { /* Implementation needed */ }
    async validateRelationshipData(validationData) { /* Implementation needed */ }
    renderEntitiesTable() { /* Implementation needed */ }
    renderRelationshipsTable() { /* Implementation needed */ }
    populateEntityForm(entityData) { /* Implementation needed */ }
    populateRelationshipForm(relationshipData) { /* Implementation needed */ }
    async saveEntity() { /* Implementation needed */ }
    async saveRelationship() { /* Implementation needed */ }
    async importData() { /* Implementation needed */ }
    async detectConflicts() { /* Implementation needed */ }
    showExportOptions() { /* Implementation needed */ }
    batchApprove() { /* Implementation needed */ }
    batchReject() { /* Implementation needed */ }
    batchDelete() { /* Implementation needed */ }
    validateEntityField(input) { /* Implementation needed */ }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.entityManagement = new EntityManagementSystem();
});

// Export for module use
window.EntityManagementSystem = EntityManagementSystem;
