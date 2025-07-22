// Review Interface JavaScript

// Global variables
let currentSessionId = sessionId;
let loadingModal;

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    loadingModal = new bootstrap.Modal(document.getElementById('loadingModal'));
    initializeEventListeners();
    updateStatistics();
});

// Initialize event listeners
function initializeEventListeners() {
    // Auto-save on input changes
    document.querySelectorAll('.entity-name, .entity-type').forEach(element => {
        element.addEventListener('change', function() {
            const entityId = this.getAttribute('data-entity-id');
            autoSaveEntity(entityId);
        });
    });

    document.querySelectorAll('.relationship-source, .relationship-target, .relationship-type').forEach(element => {
        element.addEventListener('change', function() {
            const relationshipId = this.getAttribute('data-relationship-id');
            autoSaveRelationship(relationshipId);
        });
    });
}

// Entity management functions
function approveEntity(entityId) {
    updateEntityStatus(entityId, 'approved');
}

function rejectEntity(entityId) {
    updateEntityStatus(entityId, 'rejected');
}

function editEntity(entityId) {
    const row = document.getElementById(`entity-${entityId}`);
    const nameInput = row.querySelector('.entity-name');
    const typeSelect = row.querySelector('.entity-type');
    
    // Focus on name input for editing
    nameInput.focus();
    nameInput.select();
}

function updateEntityStatus(entityId, status) {
    showLoading();
    
    fetch(`/api/review/entity/${entityId}/status`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            session_id: currentSessionId,
            status: status
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            updateEntityRowStatus(entityId, status);
            updateStatistics();
            showAlert('Entity status updated successfully', 'success');
        } else {
            showAlert('Failed to update entity status: ' + data.error, 'danger');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('Error updating entity status', 'danger');
    })
    .finally(() => {
        hideLoading();
    });
}

function autoSaveEntity(entityId) {
    const row = document.getElementById(`entity-${entityId}`);
    const name = row.querySelector('.entity-name').value;
    const type = row.querySelector('.entity-type').value;
    
    const updatedData = {
        name: name,
        type: type,
        edited: true
    };
    
    fetch(`/api/review/entity/${entityId}/update`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            session_id: currentSessionId,
            updated_data: updatedData
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Visual feedback for auto-save
            row.classList.add('status-change');
            setTimeout(() => row.classList.remove('status-change'), 500);
        }
    })
    .catch(error => {
        console.error('Auto-save error:', error);
    });
}

// Relationship management functions
function approveRelationship(relationshipId) {
    updateRelationshipStatus(relationshipId, 'approved');
}

function rejectRelationship(relationshipId) {
    updateRelationshipStatus(relationshipId, 'rejected');
}

function editRelationship(relationshipId) {
    const row = document.getElementById(`relationship-${relationshipId}`);
    const sourceInput = row.querySelector('.relationship-source');
    
    // Focus on source input for editing
    sourceInput.focus();
    sourceInput.select();
}

function updateRelationshipStatus(relationshipId, status) {
    showLoading();
    
    fetch(`/api/review/relationship/${relationshipId}/status`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            session_id: currentSessionId,
            status: status
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            updateRelationshipRowStatus(relationshipId, status);
            updateStatistics();
            showAlert('Relationship status updated successfully', 'success');
        } else {
            showAlert('Failed to update relationship status: ' + data.error, 'danger');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('Error updating relationship status', 'danger');
    })
    .finally(() => {
        hideLoading();
    });
}

function autoSaveRelationship(relationshipId) {
    const row = document.getElementById(`relationship-${relationshipId}`);
    const source = row.querySelector('.relationship-source').value;
    const target = row.querySelector('.relationship-target').value;
    const type = row.querySelector('.relationship-type').value;
    
    const updatedData = {
        source: source,
        target: target,
        type: type,
        edited: true
    };
    
    fetch(`/api/review/relationship/${relationshipId}/update`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            session_id: currentSessionId,
            updated_data: updatedData
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Visual feedback for auto-save
            row.classList.add('status-change');
            setTimeout(() => row.classList.remove('status-change'), 500);
        }
    })
    .catch(error => {
        console.error('Auto-save error:', error);
    });
}

// Bulk operations
function approveAll() {
    if (confirm('Are you sure you want to approve all entities and relationships?')) {
        showLoading();
        
        fetch(`/api/review/bulk-approve`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                session_id: currentSessionId
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                location.reload(); // Refresh to show updated statuses
            } else {
                showAlert('Failed to approve all items: ' + data.error, 'danger');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showAlert('Error approving all items', 'danger');
        })
        .finally(() => {
            hideLoading();
        });
    }
}

function rejectAll() {
    if (confirm('Are you sure you want to reject all entities and relationships?')) {
        showLoading();
        
        fetch(`/api/review/bulk-reject`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                session_id: currentSessionId
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                location.reload(); // Refresh to show updated statuses
            } else {
                showAlert('Failed to reject all items: ' + data.error, 'danger');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showAlert('Error rejecting all items', 'danger');
        })
        .finally(() => {
            hideLoading();
        });
    }
}

// Ingest approved items
function ingestApproved() {
    const approvedEntities = document.querySelectorAll('.entity-row[data-status="approved"]').length;
    const approvedRelationships = document.querySelectorAll('.relationship-row[data-status="approved"]').length;
    
    if (approvedEntities === 0 && approvedRelationships === 0) {
        showAlert('No approved items to ingest', 'warning');
        return;
    }
    
    if (confirm(`Ingest ${approvedEntities} entities and ${approvedRelationships} relationships into Graphiti?`)) {
        showLoading();
        document.getElementById('ingestBtn').disabled = true;
        
        fetch(`/api/review/ingest`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                session_id: currentSessionId
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showAlert(`Successfully ingested ${data.entities_ingested} entities and ${data.relationships_ingested} relationships`, 'success');
                // Redirect to dashboard after successful ingestion
                setTimeout(() => {
                    window.location.href = '/review';
                }, 2000);
            } else {
                showAlert('Failed to ingest approved items: ' + data.error, 'danger');
                document.getElementById('ingestBtn').disabled = false;
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showAlert('Error ingesting approved items', 'danger');
            document.getElementById('ingestBtn').disabled = false;
        })
        .finally(() => {
            hideLoading();
        });
    }
}

// UI helper functions
function updateEntityRowStatus(entityId, status) {
    const row = document.getElementById(`entity-${entityId}`);
    const badge = row.querySelector('.status-badge');
    
    row.setAttribute('data-status', status);
    badge.className = `badge status-badge status-${status}`;
    badge.textContent = status.charAt(0).toUpperCase() + status.slice(1);
    
    row.classList.add('status-change');
    setTimeout(() => row.classList.remove('status-change'), 500);
}

function updateRelationshipRowStatus(relationshipId, status) {
    const row = document.getElementById(`relationship-${relationshipId}`);
    const badge = row.querySelector('.status-badge');
    
    row.setAttribute('data-status', status);
    badge.className = `badge status-badge status-${status}`;
    badge.textContent = status.charAt(0).toUpperCase() + status.slice(1);
    
    row.classList.add('status-change');
    setTimeout(() => row.classList.remove('status-change'), 500);
}

function updateStatistics() {
    const approvedEntities = document.querySelectorAll('.entity-row[data-status="approved"]').length;
    const approvedRelationships = document.querySelectorAll('.relationship-row[data-status="approved"]').length;
    
    document.getElementById('approvedEntities').textContent = approvedEntities;
    document.getElementById('approvedRelationships').textContent = approvedRelationships;
}

function showLoading() {
    loadingModal.show();
}

function hideLoading() {
    loadingModal.hide();
}

function showAlert(message, type) {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show alert-floating`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(alertDiv);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 5000);
}
