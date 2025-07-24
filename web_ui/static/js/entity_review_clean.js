class EntityReviewApp {
    constructor() {
        this.currentSessionId = null;
        this.currentSessionData = null;
        this.selectedEntities = new Set();
        this.selectedRelationships = new Set();
        this.init();
    }

    async init() {
        await this.loadSessions();
    }

    async loadSessions() {
        try {
            const response = await fetch('/api/staging/sessions');
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            this.renderSessions(data.sessions);
            
            document.getElementById('loading').style.display = 'none';
            document.getElementById('sessions-container').style.display = 'grid';
            
        } catch (error) {
            console.error('Failed to load sessions:', error);
            this.showError(`Failed to load sessions: ${error.message}`);
            document.getElementById('loading').style.display = 'none';
        }
    }

    renderSessions(sessions) {
        const container = document.getElementById('sessions-container');
        
        if (sessions.length === 0) {
            container.innerHTML = `
                <div style="grid-column: 1 / -1; text-align: center; padding: 40px; color: #6c757d;">
                    <i class="fas fa-inbox" style="font-size: 3em; margin-bottom: 20px;"></i>
                    <h3>No staging sessions found</h3>
                    <p>Extract entities from documents to see them here for review.</p>
                </div>
            `;
            return;
        }

        container.innerHTML = sessions.map(session => this.renderSessionCard(session)).join('');
    }

    renderSessionCard(session) {
        const stats = session.statistics || {};
        const statusClass = `status-${session.status || 'pending'}`;
        const createdAt = new Date(session.created_at).toLocaleDateString();
        
        return `
            <div class="session-card">
                <div class="session-header">
                    <h3 class="session-title">${session.document_title || 'Untitled Document'}</h3>
                    <span class="session-status ${statusClass}">${session.status || 'pending'}</span>
                </div>
                
                <div class="session-info">
                    <p><strong>Source:</strong> ${session.document_source || 'Unknown'}</p>
                    <p><strong>Created:</strong> ${createdAt}</p>
                </div>
                
                <div class="session-stats">
                    <div class="stat-item">
                        <div class="stat-number">${stats.total_entities || 0}</div>
                        <div class="stat-label">Entities</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-number">${stats.total_relationships || 0}</div>
                        <div class="stat-label">Relationships</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-number">${stats.approved_entities || 0}</div>
                        <div class="stat-label">Approved</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-number">${stats.pending_entities || 0}</div>
                        <div class="stat-label">Pending</div>
                    </div>
                </div>
                
                <div class="session-actions">
                    <button class="btn btn-primary" onclick="app.openSession('${session.session_id}')">
                        <i class="fas fa-edit"></i> Review
                    </button>
                    ${session.status === 'pending_review' ? `
                        <button class="btn btn-success" onclick="app.quickApproveAll('${session.session_id}')">
                            <i class="fas fa-check-double"></i> Approve All
                        </button>
                    ` : ''}
                </div>
            </div>
        `;
    }

    async openSession(sessionId) {
        try {
            this.currentSessionId = sessionId;
            
            // Load session data
            const response = await fetch(`/api/staging/sessions/${sessionId}`);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            this.currentSessionData = await response.json();
            
            // Update modal title
            document.getElementById('modalTitle').textContent = 
                `Review: ${this.currentSessionData.document_title || 'Untitled Document'}`;
            
            // Load entities and relationships
            await this.loadEntities();
            await this.loadRelationships();
            
            // Show modal
            document.getElementById('entityModal').style.display = 'block';
            
        } catch (error) {
            console.error('Failed to open session:', error);
            this.showError(`Failed to open session: ${error.message}`);
        }
    }

    async loadEntities() {
        try {
            const response = await fetch(`/api/staging/sessions/${this.currentSessionId}/entities`);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            this.renderEntities(data.entities);
            document.getElementById('entitiesCount').textContent = data.entities.length;
            
        } catch (error) {
            console.error('Failed to load entities:', error);
            document.getElementById('entitiesContent').innerHTML = 
                `<div class="error">Failed to load entities: ${error.message}</div>`;
        }
    }

    async loadRelationships() {
        try {
            const response = await fetch(`/api/staging/sessions/${this.currentSessionId}/relationships`);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            this.renderRelationships(data.relationships);
            document.getElementById('relationshipsCount').textContent = data.relationships.length;
            
        } catch (error) {
            console.error('Failed to load relationships:', error);
            document.getElementById('relationshipsContent').innerHTML = 
                `<div class="error">Failed to load relationships: ${error.message}</div>`;
        }
    }

    renderEntities(entities) {
        const container = document.getElementById('entitiesContent');
        
        if (entities.length === 0) {
            container.innerHTML = '<p>No entities found in this session.</p>';
            return;
        }

        const tableHTML = `
            <table class="entity-table">
                <thead>
                    <tr>
                        <th><input type="checkbox" onchange="app.toggleSelectAll('entities', this.checked)"></th>
                        <th>Name</th>
                        <th>Type</th>
                        <th>Confidence</th>
                        <th>Status</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    ${entities.map(entity => this.renderEntityRow(entity)).join('')}
                </tbody>
            </table>
        `;
        
        container.innerHTML = tableHTML;
    }

    renderEntityRow(entity) {
        const confidence = (entity.confidence || 0) * 100;
        const statusClass = `status-${entity.status || 'pending'}`;
        
        return `
            <tr class="entity-row">
                <td>
                    <input type="checkbox" class="entity-checkbox" 
                           value="${entity.id}" 
                           onchange="app.toggleEntitySelection('${entity.id}', this.checked)">
                </td>
                <td>
                    <strong>${entity.name || 'Unnamed'}</strong>
                    ${entity.edited ? '<i class="fas fa-edit" title="Edited"></i>' : ''}
                </td>
                <td>
                    <span class="entity-type">${entity.type || 'Unknown'}</span>
                </td>
                <td>
                    <div class="confidence-bar">
                        <div class="confidence-fill" style="width: ${confidence}%"></div>
                    </div>
                    <small>${confidence.toFixed(0)}%</small>
                </td>
                <td>
                    <span class="session-status ${statusClass}">${entity.status || 'pending'}</span>
                </td>
                <td>
                    <button class="btn btn-primary" onclick="app.editEntity('${entity.id}')" style="padding: 4px 8px; font-size: 0.8em;">
                        <i class="fas fa-edit"></i>
                    </button>
                    ${entity.status !== 'approved' ? `
                        <button class="btn btn-success" onclick="app.approveEntity('${entity.id}')" style="padding: 4px 8px; font-size: 0.8em;">
                            <i class="fas fa-check"></i>
                        </button>
                    ` : ''}
                    ${entity.status !== 'rejected' ? `
                        <button class="btn btn-secondary" onclick="app.rejectEntity('${entity.id}')" style="padding: 4px 8px; font-size: 0.8em;">
                            <i class="fas fa-times"></i>
                        </button>
                    ` : ''}
                </td>
            </tr>
        `;
    }

    renderRelationships(relationships) {
        const container = document.getElementById('relationshipsContent');
        
        if (relationships.length === 0) {
            container.innerHTML = '<p>No relationships found in this session.</p>';
            return;
        }

        const tableHTML = `
            <table class="entity-table">
                <thead>
                    <tr>
                        <th><input type="checkbox" onchange="app.toggleSelectAll('relationships', this.checked)"></th>
                        <th>Source</th>
                        <th>Relationship</th>
                        <th>Target</th>
                        <th>Confidence</th>
                        <th>Status</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    ${relationships.map(rel => this.renderRelationshipRow(rel)).join('')}
                </tbody>
            </table>
        `;
        
        container.innerHTML = tableHTML;
    }

    renderRelationshipRow(relationship) {
        const confidence = (relationship.confidence || 0) * 100;
        const statusClass = `status-${relationship.status || 'pending'}`;
        
        return `
            <tr class="entity-row">
                <td>
                    <input type="checkbox" class="relationship-checkbox" 
                           value="${relationship.id}" 
                           onchange="app.toggleRelationshipSelection('${relationship.id}', this.checked)">
                </td>
                <td>${relationship.source_entity || 'Unknown'}</td>
                <td>
                    <strong>${relationship.type || 'RELATED_TO'}</strong>
                    ${relationship.edited ? '<i class="fas fa-edit" title="Edited"></i>' : ''}
                </td>
                <td>${relationship.target_entity || 'Unknown'}</td>
                <td>
                    <div class="confidence-bar">
                        <div class="confidence-fill" style="width: ${confidence}%"></div>
                    </div>
                    <small>${confidence.toFixed(0)}%</small>
                </td>
                <td>
                    <span class="session-status ${statusClass}">${relationship.status || 'pending'}</span>
                </td>
                <td>
                    <button class="btn btn-primary" onclick="app.editRelationship('${relationship.id}')" style="padding: 4px 8px; font-size: 0.8em;">
                        <i class="fas fa-edit"></i>
                    </button>
                    ${relationship.status !== 'approved' ? `
                        <button class="btn btn-success" onclick="app.approveRelationship('${relationship.id}')" style="padding: 4px 8px; font-size: 0.8em;">
                            <i class="fas fa-check"></i>
                        </button>
                    ` : ''}
                    ${relationship.status !== 'rejected' ? `
                        <button class="btn btn-secondary" onclick="app.rejectRelationship('${relationship.id}')" style="padding: 4px 8px; font-size: 0.8em;">
                            <i class="fas fa-times"></i>
                        </button>
                    ` : ''}
                </td>
            </tr>
        `;
    }

    toggleEntitySelection(entityId, selected) {
        if (selected) {
            this.selectedEntities.add(entityId);
        } else {
            this.selectedEntities.delete(entityId);
        }
    }

    toggleRelationshipSelection(relationshipId, selected) {
        if (selected) {
            this.selectedRelationships.add(relationshipId);
        } else {
            this.selectedRelationships.delete(relationshipId);
        }
    }

    toggleSelectAll(type, selected) {
        const checkboxes = document.querySelectorAll(`.${type === 'entities' ? 'entity' : 'relationship'}-checkbox`);
        checkboxes.forEach(checkbox => {
            checkbox.checked = selected;
            if (type === 'entities') {
                this.toggleEntitySelection(checkbox.value, selected);
            } else {
                this.toggleRelationshipSelection(checkbox.value, selected);
            }
        });
    }

    selectAll(type) {
        this.toggleSelectAll(type, true);
    }

    showError(message) {
        const errorDiv = document.getElementById('error');
        errorDiv.textContent = message;
        errorDiv.style.display = 'block';
        setTimeout(() => {
            errorDiv.style.display = 'none';
        }, 5000);
    }

    showSuccess(message) {
        const successDiv = document.getElementById('success');
        successDiv.textContent = message;
        successDiv.style.display = 'block';
        setTimeout(() => {
            successDiv.style.display = 'none';
        }, 3000);
    }
}
