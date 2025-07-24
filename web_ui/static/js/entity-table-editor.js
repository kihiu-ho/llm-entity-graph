/**
 * Entity Table Editor - Advanced table management with inline editing
 * Provides sortable, filterable, and editable table functionality
 */

class EntityTableEditor {
    constructor(tableId, options = {}) {
        this.tableId = tableId;
        this.table = document.getElementById(tableId);
        this.tbody = this.table.querySelector('tbody');
        this.thead = this.table.querySelector('thead');
        
        // Configuration
        this.options = {
            sortable: true,
            filterable: true,
            editable: true,
            selectable: true,
            pagination: false,
            pageSize: 50,
            realTimeValidation: true,
            ...options
        };
        
        // State
        this.data = [];
        this.filteredData = [];
        this.selectedRows = new Set();
        this.sortColumn = null;
        this.sortDirection = 'asc';
        this.currentPage = 1;
        this.editingCell = null;
        
        // Callbacks
        this.onDataChange = options.onDataChange || (() => {});
        this.onSelectionChange = options.onSelectionChange || (() => {});
        this.onEdit = options.onEdit || (() => {});
        this.onValidation = options.onValidation || (() => {});
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.setupSorting();
        this.setupSelection();
        this.setupInlineEditing();
        this.setupKeyboardNavigation();
    }
    
    setupEventListeners() {
        // Global click handler for closing edit mode
        document.addEventListener('click', (e) => {
            if (this.editingCell && !this.editingCell.contains(e.target)) {
                this.cancelEdit();
            }
        });
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey || e.metaKey) {
                switch (e.key) {
                    case 'a':
                        if (e.target.closest(`#${this.tableId}`)) {
                            e.preventDefault();
                            this.selectAll();
                        }
                        break;
                    case 's':
                        if (this.editingCell) {
                            e.preventDefault();
                            this.saveEdit();
                        }
                        break;
                }
            }
            
            if (e.key === 'Escape' && this.editingCell) {
                this.cancelEdit();
            }
        });
    }
    
    setupSorting() {
        if (!this.options.sortable) return;
        
        const headers = this.thead.querySelectorAll('th.sortable');
        headers.forEach(header => {
            header.addEventListener('click', () => {
                const column = header.dataset.sort;
                this.sort(column);
            });
            
            header.style.cursor = 'pointer';
        });
    }
    
    setupSelection() {
        if (!this.options.selectable) return;
        
        // Select all checkbox
        const selectAllCheckbox = this.thead.querySelector('input[type="checkbox"]');
        if (selectAllCheckbox) {
            selectAllCheckbox.addEventListener('change', (e) => {
                if (e.target.checked) {
                    this.selectAll();
                } else {
                    this.deselectAll();
                }
            });
        }
    }
    
    setupInlineEditing() {
        if (!this.options.editable) return;
        
        this.tbody.addEventListener('dblclick', (e) => {
            const cell = e.target.closest('td.editable');
            if (cell && !this.editingCell) {
                this.startEdit(cell);
            }
        });
    }
    
    setupKeyboardNavigation() {
        this.table.addEventListener('keydown', (e) => {
            const currentCell = e.target.closest('td');
            if (!currentCell) return;
            
            const row = currentCell.parentElement;
            const cellIndex = Array.from(row.children).indexOf(currentCell);
            const rowIndex = Array.from(this.tbody.children).indexOf(row);
            
            let newRow, newCell;
            
            switch (e.key) {
                case 'ArrowUp':
                    e.preventDefault();
                    newRow = this.tbody.children[rowIndex - 1];
                    if (newRow) {
                        newCell = newRow.children[cellIndex];
                        newCell?.focus();
                    }
                    break;
                    
                case 'ArrowDown':
                    e.preventDefault();
                    newRow = this.tbody.children[rowIndex + 1];
                    if (newRow) {
                        newCell = newRow.children[cellIndex];
                        newCell?.focus();
                    }
                    break;
                    
                case 'ArrowLeft':
                    e.preventDefault();
                    newCell = currentCell.previousElementSibling;
                    newCell?.focus();
                    break;
                    
                case 'ArrowRight':
                    e.preventDefault();
                    newCell = currentCell.nextElementSibling;
                    newCell?.focus();
                    break;
                    
                case 'Enter':
                    if (currentCell.classList.contains('editable') && !this.editingCell) {
                        e.preventDefault();
                        this.startEdit(currentCell);
                    }
                    break;
            }
        });
    }
    
    setData(data) {
        this.data = [...data];
        this.filteredData = [...data];
        this.render();
        this.updateStats();
    }
    
    addRow(rowData) {
        this.data.push(rowData);
        this.applyFilters();
        this.render();
        this.updateStats();
        this.onDataChange(this.data);
    }
    
    updateRow(rowId, newData) {
        const index = this.data.findIndex(row => row.id === rowId);
        if (index !== -1) {
            this.data[index] = { ...this.data[index], ...newData };
            this.applyFilters();
            this.render();
            this.updateStats();
            this.onDataChange(this.data);
        }
    }
    
    deleteRow(rowId) {
        this.data = this.data.filter(row => row.id !== rowId);
        this.selectedRows.delete(rowId);
        this.applyFilters();
        this.render();
        this.updateStats();
        this.onDataChange(this.data);
        this.onSelectionChange(Array.from(this.selectedRows));
    }
    
    deleteSelected() {
        const selectedIds = Array.from(this.selectedRows);
        this.data = this.data.filter(row => !selectedIds.includes(row.id));
        this.selectedRows.clear();
        this.applyFilters();
        this.render();
        this.updateStats();
        this.onDataChange(this.data);
        this.onSelectionChange([]);
    }
    
    sort(column) {
        if (this.sortColumn === column) {
            this.sortDirection = this.sortDirection === 'asc' ? 'desc' : 'asc';
        } else {
            this.sortColumn = column;
            this.sortDirection = 'asc';
        }
        
        this.filteredData.sort((a, b) => {
            let aVal = a[column];
            let bVal = b[column];
            
            // Handle different data types
            if (typeof aVal === 'string') {
                aVal = aVal.toLowerCase();
                bVal = bVal.toLowerCase();
            }
            
            if (aVal < bVal) return this.sortDirection === 'asc' ? -1 : 1;
            if (aVal > bVal) return this.sortDirection === 'asc' ? 1 : -1;
            return 0;
        });
        
        this.render();
        this.updateSortIndicators();
    }
    
    updateSortIndicators() {
        // Clear all sort indicators
        this.thead.querySelectorAll('th.sortable').forEach(th => {
            th.classList.remove('sorted-asc', 'sorted-desc');
        });
        
        // Add indicator to current sort column
        if (this.sortColumn) {
            const header = this.thead.querySelector(`th[data-sort="${this.sortColumn}"]`);
            if (header) {
                header.classList.add(`sorted-${this.sortDirection}`);
            }
        }
    }
    
    filter(filters) {
        this.filteredData = this.data.filter(row => {
            return Object.entries(filters).every(([key, value]) => {
                if (!value) return true;
                
                const rowValue = row[key];
                if (typeof rowValue === 'string') {
                    return rowValue.toLowerCase().includes(value.toLowerCase());
                }
                return rowValue === value;
            });
        });
        
        this.render();
        this.updateStats();
    }
    
    applyFilters() {
        // Re-apply current filters if any
        const event = new CustomEvent('applyFilters');
        document.dispatchEvent(event);
    }
    
    search(query) {
        if (!query) {
            this.filteredData = [...this.data];
        } else {
            this.filteredData = this.data.filter(row => {
                return Object.values(row).some(value => {
                    if (typeof value === 'string') {
                        return value.toLowerCase().includes(query.toLowerCase());
                    }
                    return false;
                });
            });
        }
        
        this.render();
        this.updateStats();
    }
    
    selectRow(rowId) {
        this.selectedRows.add(rowId);
        this.updateRowSelection(rowId, true);
        this.onSelectionChange(Array.from(this.selectedRows));
    }
    
    deselectRow(rowId) {
        this.selectedRows.delete(rowId);
        this.updateRowSelection(rowId, false);
        this.onSelectionChange(Array.from(this.selectedRows));
    }
    
    selectAll() {
        this.filteredData.forEach(row => {
            this.selectedRows.add(row.id);
        });
        this.updateAllRowSelections();
        this.onSelectionChange(Array.from(this.selectedRows));
    }
    
    deselectAll() {
        this.selectedRows.clear();
        this.updateAllRowSelections();
        this.onSelectionChange([]);
    }
    
    updateRowSelection(rowId, selected) {
        const row = this.tbody.querySelector(`tr[data-id="${rowId}"]`);
        if (row) {
            const checkbox = row.querySelector('input[type="checkbox"]');
            if (checkbox) {
                checkbox.checked = selected;
            }
            row.classList.toggle('selected', selected);
        }
    }
    
    updateAllRowSelections() {
        this.tbody.querySelectorAll('tr').forEach(row => {
            const rowId = row.dataset.id;
            const selected = this.selectedRows.has(rowId);
            const checkbox = row.querySelector('input[type="checkbox"]');
            if (checkbox) {
                checkbox.checked = selected;
            }
            row.classList.toggle('selected', selected);
        });
        
        // Update select all checkbox
        const selectAllCheckbox = this.thead.querySelector('input[type="checkbox"]');
        if (selectAllCheckbox) {
            const allSelected = this.filteredData.length > 0 && 
                               this.filteredData.every(row => this.selectedRows.has(row.id));
            selectAllCheckbox.checked = allSelected;
            selectAllCheckbox.indeterminate = this.selectedRows.size > 0 && !allSelected;
        }
    }
    
    startEdit(cell) {
        if (this.editingCell) {
            this.cancelEdit();
        }
        
        this.editingCell = cell;
        const originalValue = cell.textContent.trim();
        const fieldName = cell.dataset.field;
        const rowId = cell.closest('tr').dataset.id;
        
        // Create input element
        const input = document.createElement('input');
        input.type = 'text';
        input.value = originalValue;
        input.className = 'inline-editor';
        
        // Handle special field types
        if (fieldName === 'confidence') {
            input.type = 'number';
            input.min = '0';
            input.max = '1';
            input.step = '0.01';
        }
        
        // Replace cell content
        cell.innerHTML = '';
        cell.appendChild(input);
        cell.classList.add('editing');
        
        // Create edit controls
        const controls = document.createElement('div');
        controls.className = 'edit-controls';
        
        const saveBtn = document.createElement('button');
        saveBtn.className = 'edit-control-btn edit-save-btn';
        saveBtn.innerHTML = '<i class="fas fa-check"></i>';
        saveBtn.onclick = () => this.saveEdit();
        
        const cancelBtn = document.createElement('button');
        cancelBtn.className = 'edit-control-btn edit-cancel-btn';
        cancelBtn.innerHTML = '<i class="fas fa-times"></i>';
        cancelBtn.onclick = () => this.cancelEdit();
        
        controls.appendChild(saveBtn);
        controls.appendChild(cancelBtn);
        cell.appendChild(controls);
        
        // Focus input and select text
        input.focus();
        input.select();
        
        // Handle Enter and Escape keys
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                this.saveEdit();
            } else if (e.key === 'Escape') {
                e.preventDefault();
                this.cancelEdit();
            }
        });
        
        // Real-time validation if enabled
        if (this.options.realTimeValidation) {
            input.addEventListener('input', () => {
                this.validateField(input, fieldName, rowId);
            });
        }
        
        // Store original value for cancel
        cell.dataset.originalValue = originalValue;
    }
    
    async saveEdit() {
        if (!this.editingCell) return;
        
        const input = this.editingCell.querySelector('.inline-editor');
        const newValue = input.value.trim();
        const fieldName = this.editingCell.dataset.field;
        const rowId = this.editingCell.closest('tr').dataset.id;
        const originalValue = this.editingCell.dataset.originalValue;
        
        // Validate the new value
        const validation = await this.validateField(input, fieldName, rowId);
        if (!validation.isValid) {
            // Show validation error
            this.showValidationError(this.editingCell, validation.errors[0]);
            return;
        }
        
        // Update data
        const rowData = this.data.find(row => row.id === rowId);
        if (rowData) {
            const oldValue = rowData[fieldName];
            rowData[fieldName] = this.convertValue(newValue, fieldName);
            
            // Call edit callback
            this.onEdit({
                rowId,
                fieldName,
                oldValue,
                newValue: rowData[fieldName],
                rowData
            });
        }
        
        // Update cell display
        this.updateCellDisplay(this.editingCell, newValue, fieldName);
        this.finishEdit();
        
        // Trigger data change
        this.onDataChange(this.data);
    }
    
    cancelEdit() {
        if (!this.editingCell) return;
        
        const originalValue = this.editingCell.dataset.originalValue;
        const fieldName = this.editingCell.dataset.field;
        
        this.updateCellDisplay(this.editingCell, originalValue, fieldName);
        this.finishEdit();
    }
    
    finishEdit() {
        if (this.editingCell) {
            this.editingCell.classList.remove('editing');
            delete this.editingCell.dataset.originalValue;
            this.editingCell = null;
        }
    }
    
    updateCellDisplay(cell, value, fieldName) {
        cell.innerHTML = '';
        cell.classList.remove('editing');
        
        switch (fieldName) {
            case 'status':
                cell.innerHTML = this.createStatusBadge(value);
                break;
            case 'confidence':
                cell.innerHTML = this.createConfidenceBar(parseFloat(value));
                break;
            default:
                cell.textContent = value;
        }
    }
    
    async validateField(input, fieldName, rowId) {
        const value = input.value.trim();
        
        // Remove previous validation classes
        input.classList.remove('field-valid', 'field-invalid', 'field-validating');
        
        // Show validating state
        input.classList.add('field-validating');
        
        try {
            // Call validation callback
            const validation = await this.onValidation({
                fieldName,
                value,
                rowId,
                allData: this.data
            });
            
            // Update input state
            input.classList.remove('field-validating');
            if (validation.isValid) {
                input.classList.add('field-valid');
            } else {
                input.classList.add('field-invalid');
            }
            
            return validation;
        } catch (error) {
            input.classList.remove('field-validating');
            input.classList.add('field-invalid');
            return {
                isValid: false,
                errors: ['Validation error occurred']
            };
        }
    }
    
    showValidationError(cell, message) {
        // Remove existing error
        const existingError = cell.querySelector('.validation-error');
        if (existingError) {
            existingError.remove();
        }
        
        // Create error element
        const error = document.createElement('div');
        error.className = 'validation-error';
        error.textContent = message;
        error.style.cssText = `
            position: absolute;
            top: 100%;
            left: 0;
            background: #dc3545;
            color: white;
            padding: 5px 10px;
            border-radius: 4px;
            font-size: 0.8em;
            z-index: 1000;
            white-space: nowrap;
        `;
        
        cell.style.position = 'relative';
        cell.appendChild(error);
        
        // Remove error after 3 seconds
        setTimeout(() => {
            error.remove();
        }, 3000);
    }
    
    convertValue(value, fieldName) {
        switch (fieldName) {
            case 'confidence':
                return parseFloat(value);
            default:
                return value;
        }
    }
    
    createStatusBadge(status) {
        return `<span class="status-badge status-${status.toLowerCase()}">${status}</span>`;
    }
    
    createConfidenceBar(confidence) {
        const percentage = Math.round(confidence * 100);
        let colorClass = 'confidence-low';
        
        if (confidence >= 0.7) colorClass = 'confidence-high';
        else if (confidence >= 0.4) colorClass = 'confidence-medium';
        
        return `
            <div class="confidence-bar">
                <div class="confidence-fill ${colorClass}" style="width: ${percentage}%"></div>
            </div>
            <div class="confidence-text">${percentage}%</div>
        `;
    }
    
    updateStats() {
        // Update table statistics
        const totalCount = document.getElementById('totalCount');
        const selectedCount = document.getElementById('selectedCount');
        const pendingCount = document.getElementById('pendingCount');
        const approvedCount = document.getElementById('approvedCount');
        
        if (totalCount) totalCount.textContent = this.filteredData.length;
        if (selectedCount) selectedCount.textContent = this.selectedRows.size;
        
        if (pendingCount) {
            const pending = this.filteredData.filter(row => row.status === 'pending').length;
            pendingCount.textContent = pending;
        }
        
        if (approvedCount) {
            const approved = this.filteredData.filter(row => row.status === 'approved').length;
            approvedCount.textContent = approved;
        }
    }
    
    render() {
        // This method should be implemented by subclasses
        // or provided as a callback option
        console.warn('render() method not implemented');
    }
}

// Export for use in other modules
window.EntityTableEditor = EntityTableEditor;
