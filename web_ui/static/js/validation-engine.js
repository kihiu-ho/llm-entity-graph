/**
 * Validation Engine - Real-time validation for entity and relationship data
 * Provides client-side and server-side validation with visual feedback
 */

class ValidationEngine {
    constructor(options = {}) {
        this.options = {
            apiBaseUrl: '/api/validation',
            debounceDelay: 300,
            showSuggestions: true,
            showWarnings: true,
            ...options
        };
        
        // Validation rules cache
        this.validationRules = new Map();
        this.validationCache = new Map();
        
        // Debounce timers
        this.debounceTimers = new Map();
        
        this.init();
    }
    
    init() {
        this.setupGlobalValidation();
        this.loadValidationRules();
    }
    
    setupGlobalValidation() {
        // Add validation to all forms with validation class
        document.addEventListener('DOMContentLoaded', () => {
            const forms = document.querySelectorAll('.validation-enabled');
            forms.forEach(form => this.enableFormValidation(form));
        });
        
        // Handle dynamic form additions
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                mutation.addedNodes.forEach((node) => {
                    if (node.nodeType === Node.ELEMENT_NODE) {
                        const forms = node.querySelectorAll?.('.validation-enabled') || [];
                        forms.forEach(form => this.enableFormValidation(form));
                    }
                });
            });
        });
        
        observer.observe(document.body, { childList: true, subtree: true });
    }
    
    enableFormValidation(form) {
        const inputs = form.querySelectorAll('input, select, textarea');
        
        inputs.forEach(input => {
            // Real-time validation on input
            input.addEventListener('input', (e) => {
                this.validateFieldRealTime(e.target);
            });
            
            // Validation on blur
            input.addEventListener('blur', (e) => {
                this.validateField(e.target);
            });
            
            // Clear validation on focus
            input.addEventListener('focus', (e) => {
                this.clearFieldValidation(e.target);
            });
        });
        
        // Form submission validation
        form.addEventListener('submit', (e) => {
            if (!this.validateForm(form)) {
                e.preventDefault();
            }
        });
    }
    
    validateFieldRealTime(field) {
        const fieldName = field.name || field.id;
        
        // Clear existing timer
        if (this.debounceTimers.has(fieldName)) {
            clearTimeout(this.debounceTimers.get(fieldName));
        }
        
        // Set new timer
        const timer = setTimeout(() => {
            this.validateField(field, true);
        }, this.options.debounceDelay);
        
        this.debounceTimers.set(fieldName, timer);
    }
    
    async validateField(field, isRealTime = false) {
        const fieldName = field.name || field.id;
        const value = field.value.trim();
        const fieldType = this.getFieldType(field);
        
        // Show loading state
        this.setFieldState(field, 'validating');
        
        try {
            let validation;
            
            // Check cache first for real-time validation
            const cacheKey = `${fieldType}_${fieldName}_${value}`;
            if (isRealTime && this.validationCache.has(cacheKey)) {
                validation = this.validationCache.get(cacheKey);
            } else {
                // Perform validation
                validation = await this.performValidation(fieldType, fieldName, value, field);
                
                // Cache result
                if (isRealTime) {
                    this.validationCache.set(cacheKey, validation);
                }
            }
            
            // Update field state
            this.updateFieldValidation(field, validation);
            
            return validation;
            
        } catch (error) {
            console.error('Validation error:', error);
            this.setFieldState(field, 'error');
            return {
                isValid: false,
                errors: ['Validation failed'],
                warnings: [],
                suggestions: []
            };
        }
    }
    
    async performValidation(fieldType, fieldName, value, field) {
        // Client-side validation first
        const clientValidation = this.validateClientSide(fieldType, fieldName, value, field);
        
        // If client-side validation fails, don't call server
        if (!clientValidation.isValid) {
            return clientValidation;
        }
        
        // Server-side validation for complex rules
        if (this.needsServerValidation(fieldType, fieldName)) {
            const serverValidation = await this.validateServerSide(fieldType, fieldName, value, field);
            
            // Merge client and server validation results
            return this.mergeValidationResults(clientValidation, serverValidation);
        }
        
        return clientValidation;
    }
    
    validateClientSide(fieldType, fieldName, value, field) {
        const validation = {
            isValid: true,
            errors: [],
            warnings: [],
            suggestions: []
        };
        
        // Required field validation
        if (field.required && !value) {
            validation.isValid = false;
            validation.errors.push(`${this.getFieldLabel(field)} is required`);
            return validation;
        }
        
        // Skip further validation if empty and not required
        if (!value) {
            return validation;
        }
        
        // Field-specific validation
        switch (fieldType) {
            case 'entity':
                return this.validateEntityField(fieldName, value, field);
            case 'relationship':
                return this.validateRelationshipField(fieldName, value, field);
            default:
                return this.validateGenericField(fieldName, value, field);
        }
    }
    
    validateEntityField(fieldName, value, field) {
        const validation = {
            isValid: true,
            errors: [],
            warnings: [],
            suggestions: []
        };
        
        switch (fieldName) {
            case 'name':
                return this.validateEntityName(value);
            case 'type':
                return this.validateEntityType(value);
            case 'confidence':
                return this.validateConfidence(value);
            default:
                return validation;
        }
    }
    
    validateRelationshipField(fieldName, value, field) {
        const validation = {
            isValid: true,
            errors: [],
            warnings: [],
            suggestions: []
        };
        
        switch (fieldName) {
            case 'relationship_type':
                return this.validateRelationshipType(value);
            case 'source_entity_id':
            case 'target_entity_id':
                return this.validateEntityReference(value, fieldName);
            case 'confidence':
                return this.validateConfidence(value);
            default:
                return validation;
        }
    }
    
    validateEntityName(name) {
        const validation = {
            isValid: true,
            errors: [],
            warnings: [],
            suggestions: []
        };
        
        // Length validation
        if (name.length < 2) {
            validation.isValid = false;
            validation.errors.push('Entity name must be at least 2 characters long');
        }
        
        if (name.length > 200) {
            validation.isValid = false;
            validation.errors.push('Entity name must be less than 200 characters');
        }
        
        // Pattern validation
        if (/[<>{}[\]\\|`~]/.test(name)) {
            validation.warnings.push('Entity name contains potentially problematic characters');
        }
        
        // Suggestions based on patterns
        if (/^[A-Z][a-z]+ [A-Z][a-z]+$/.test(name)) {
            validation.suggestions.push('This looks like a person name - consider setting type to "Person"');
        } else if (/\b(Ltd|Limited|Inc|Corporation|Corp|LLC|LLP)\b/i.test(name)) {
            validation.suggestions.push('This looks like a company name - consider setting type to "Company"');
        }
        
        return validation;
    }
    
    validateEntityType(type) {
        const validation = {
            isValid: true,
            errors: [],
            warnings: [],
            suggestions: []
        };
        
        const validTypes = ['Person', 'Company', 'Organization', 'Location', 'Technology'];
        const normalizedType = type.charAt(0).toUpperCase() + type.slice(1).toLowerCase();
        
        // Check if it's a valid type
        if (!validTypes.includes(normalizedType)) {
            // Check for similar types
            const similar = this.findSimilarStrings(type, validTypes);
            if (similar.length > 0) {
                validation.suggestions.push(`Did you mean "${similar[0]}"?`);
            }
        } else if (type !== normalizedType) {
            validation.suggestions.push(`Consider using standard capitalization: "${normalizedType}"`);
        }
        
        return validation;
    }
    
    validateRelationshipType(type) {
        const validation = {
            isValid: true,
            errors: [],
            warnings: [],
            suggestions: []
        };
        
        const validTypes = [
            'CEO_OF', 'CHAIRMAN_OF', 'DIRECTOR_OF', 'EMPLOYEE_OF', 'SHAREHOLDER_OF',
            'SUBSIDIARY_OF', 'PARTNER_OF', 'RELATED_TO', 'OWNS', 'MANAGES'
        ];
        
        const upperType = type.toUpperCase();
        
        if (!validTypes.includes(upperType)) {
            const similar = this.findSimilarStrings(upperType, validTypes);
            if (similar.length > 0) {
                validation.suggestions.push(`Did you mean "${similar[0]}"?`);
            }
        }
        
        return validation;
    }
    
    validateConfidence(confidence) {
        const validation = {
            isValid: true,
            errors: [],
            warnings: [],
            suggestions: []
        };
        
        const value = parseFloat(confidence);
        
        if (isNaN(value)) {
            validation.isValid = false;
            validation.errors.push('Confidence must be a number');
            return validation;
        }
        
        if (value < 0 || value > 1) {
            validation.isValid = false;
            validation.errors.push('Confidence must be between 0 and 1');
            return validation;
        }
        
        if (value < 0.5) {
            validation.warnings.push('Low confidence score - consider reviewing this item');
        }
        
        return validation;
    }
    
    validateEntityReference(entityId, fieldName) {
        const validation = {
            isValid: true,
            errors: [],
            warnings: [],
            suggestions: []
        };
        
        // This would typically check against available entities
        // For now, just validate format
        if (!entityId) {
            validation.isValid = false;
            validation.errors.push(`${fieldName.replace('_', ' ')} is required`);
        }
        
        return validation;
    }
    
    async validateServerSide(fieldType, fieldName, value, field) {
        const sessionId = this.getCurrentSessionId();
        const endpoint = fieldType === 'entity' ? '/entity' : '/relationship';
        
        const data = {
            [`${fieldType}_data`]: { [fieldName]: value },
            session_id: sessionId
        };
        
        try {
            const response = await fetch(`${this.options.apiBaseUrl}${endpoint}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });
            
            const result = await response.json();
            
            if (result.success) {
                return result.validation;
            } else {
                throw new Error(result.error || 'Server validation failed');
            }
        } catch (error) {
            console.error('Server validation error:', error);
            return {
                isValid: true, // Fail gracefully
                errors: [],
                warnings: ['Server validation unavailable'],
                suggestions: []
            };
        }
    }
    
    needsServerValidation(fieldType, fieldName) {
        // Define which fields need server-side validation
        const serverValidationFields = {
            entity: ['name'], // Check for duplicates
            relationship: ['source_entity_id', 'target_entity_id'] // Check entity existence
        };
        
        return serverValidationFields[fieldType]?.includes(fieldName) || false;
    }
    
    mergeValidationResults(client, server) {
        return {
            isValid: client.isValid && server.isValid,
            errors: [...client.errors, ...server.errors],
            warnings: [...client.warnings, ...server.warnings],
            suggestions: [...client.suggestions, ...server.suggestions]
        };
    }
    
    updateFieldValidation(field, validation) {
        // Clear previous state
        this.clearFieldValidation(field);
        
        // Set new state
        if (validation.isValid) {
            this.setFieldState(field, 'valid');
        } else {
            this.setFieldState(field, 'invalid');
        }
        
        // Show feedback
        this.showValidationFeedback(field, validation);
    }
    
    setFieldState(field, state) {
        // Remove all state classes
        field.classList.remove('field-valid', 'field-invalid', 'field-validating', 'field-error');
        
        // Add new state class
        if (state !== 'none') {
            field.classList.add(`field-${state}`);
        }
    }
    
    clearFieldValidation(field) {
        this.setFieldState(field, 'none');
        this.hideValidationFeedback(field);
    }
    
    showValidationFeedback(field, validation) {
        const container = this.getOrCreateFeedbackContainer(field);
        container.innerHTML = '';
        
        // Show errors
        validation.errors.forEach(error => {
            const errorEl = document.createElement('div');
            errorEl.className = 'validation-feedback validation-error';
            errorEl.textContent = error;
            container.appendChild(errorEl);
        });
        
        // Show warnings if enabled
        if (this.options.showWarnings) {
            validation.warnings.forEach(warning => {
                const warningEl = document.createElement('div');
                warningEl.className = 'validation-feedback validation-warning';
                warningEl.textContent = warning;
                container.appendChild(warningEl);
            });
        }
        
        // Show suggestions if enabled
        if (this.options.showSuggestions) {
            validation.suggestions.forEach(suggestion => {
                const suggestionEl = document.createElement('div');
                suggestionEl.className = 'validation-feedback validation-suggestion';
                suggestionEl.textContent = suggestion;
                container.appendChild(suggestionEl);
            });
        }
    }
    
    hideValidationFeedback(field) {
        const container = this.getFeedbackContainer(field);
        if (container) {
            container.innerHTML = '';
        }
    }
    
    getOrCreateFeedbackContainer(field) {
        let container = this.getFeedbackContainer(field);
        
        if (!container) {
            container = document.createElement('div');
            container.className = 'validation-feedback-container';
            
            // Insert after the field or its parent form group
            const formGroup = field.closest('.form-group');
            const insertAfter = formGroup || field;
            insertAfter.parentNode.insertBefore(container, insertAfter.nextSibling);
        }
        
        return container;
    }
    
    getFeedbackContainer(field) {
        const formGroup = field.closest('.form-group');
        const parent = formGroup || field.parentNode;
        return parent.querySelector('.validation-feedback-container');
    }
    
    validateForm(form) {
        const inputs = form.querySelectorAll('input, select, textarea');
        const validationPromises = Array.from(inputs).map(input => this.validateField(input));
        
        return Promise.all(validationPromises).then(results => {
            return results.every(result => result.isValid);
        });
    }
    
    // Utility methods
    
    getFieldType(field) {
        // Determine field type from form context or data attributes
        const form = field.closest('form');
        if (form) {
            if (form.id.includes('entity')) return 'entity';
            if (form.id.includes('relationship')) return 'relationship';
        }
        
        return field.dataset.fieldType || 'generic';
    }
    
    getFieldLabel(field) {
        const label = field.closest('.form-group')?.querySelector('label');
        return label?.textContent.replace('*', '').trim() || field.name || field.id;
    }
    
    getCurrentSessionId() {
        // Get current session ID from URL, form, or global variable
        const urlParams = new URLSearchParams(window.location.search);
        return urlParams.get('session_id') || 
               document.querySelector('[data-session-id]')?.dataset.sessionId ||
               window.currentSessionId;
    }
    
    findSimilarStrings(target, candidates, threshold = 0.7) {
        return candidates
            .map(candidate => ({
                string: candidate,
                similarity: this.calculateSimilarity(target.toLowerCase(), candidate.toLowerCase())
            }))
            .filter(item => item.similarity >= threshold)
            .sort((a, b) => b.similarity - a.similarity)
            .map(item => item.string);
    }
    
    calculateSimilarity(str1, str2) {
        const longer = str1.length > str2.length ? str1 : str2;
        const shorter = str1.length > str2.length ? str2 : str1;
        
        if (longer.length === 0) return 1.0;
        
        const editDistance = this.levenshteinDistance(longer, shorter);
        return (longer.length - editDistance) / longer.length;
    }
    
    levenshteinDistance(str1, str2) {
        const matrix = [];
        
        for (let i = 0; i <= str2.length; i++) {
            matrix[i] = [i];
        }
        
        for (let j = 0; j <= str1.length; j++) {
            matrix[0][j] = j;
        }
        
        for (let i = 1; i <= str2.length; i++) {
            for (let j = 1; j <= str1.length; j++) {
                if (str2.charAt(i - 1) === str1.charAt(j - 1)) {
                    matrix[i][j] = matrix[i - 1][j - 1];
                } else {
                    matrix[i][j] = Math.min(
                        matrix[i - 1][j - 1] + 1,
                        matrix[i][j - 1] + 1,
                        matrix[i - 1][j] + 1
                    );
                }
            }
        }
        
        return matrix[str2.length][str1.length];
    }
    
    loadValidationRules() {
        // Load validation rules from server or configuration
        // This could be expanded to load dynamic rules
    }
}

// Create global instance
window.validationEngine = new ValidationEngine();

// Export for module use
window.ValidationEngine = ValidationEngine;
