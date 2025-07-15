/**
 * Web UI JavaScript for Agentic RAG with Knowledge Graph
 */

class AgenticRAGUI {
    constructor() {
        this.sessionId = null;
        this.userId = 'web_user';
        this.isStreaming = false;
        this.currentEventSource = null;
        
        this.initializeElements();
        this.bindEvents();
        this.checkHealth();
        this.loadDocuments();
    }
    
    initializeElements() {
        // Main elements
        this.messageInput = document.getElementById('message-input');
        this.sendBtn = document.getElementById('send-btn');
        this.chatMessages = document.getElementById('chat-messages');
        this.typingIndicator = document.getElementById('typing-indicator');
        
        // Status elements
        this.statusDot = document.getElementById('status-dot');
        this.statusText = document.getElementById('status-text');
        
        // Tools elements
        this.toolsDisplay = document.getElementById('tools-display');
        this.toolsContent = document.getElementById('tools-content');
        this.closeTools = document.getElementById('close-tools');
        
        // Action buttons
        this.clearChatBtn = document.getElementById('clear-chat');
        this.exportChatBtn = document.getElementById('export-chat');
        this.settingsBtn = document.getElementById('settings-btn');
        this.ingestionBtn = document.getElementById('ingestion-btn');

        // Settings modal elements
        this.settingsModal = document.getElementById('settings-modal');
        this.closeSettingsModal = document.getElementById('close-settings-modal');
        this.saveSettingsBtn = document.getElementById('save-settings');
        this.loadSettingsBtn = document.getElementById('load-settings');
        this.testDbBtn = document.getElementById('test-db-connection');
        this.testLlmBtn = document.getElementById('test-llm-connection');

        // Ingestion modal elements
        this.ingestionModal = document.getElementById('ingestion-modal');
        this.closeIngestionModal = document.getElementById('close-ingestion-modal');
        this.uploadArea = document.getElementById('upload-area');
        this.fileInput = document.getElementById('file-input');
        this.browseFilesBtn = document.getElementById('browse-files');
        this.startIngestionBtn = document.getElementById('start-ingestion');
        this.cancelIngestionBtn = document.getElementById('cancel-ingestion');

        // File management
        this.selectedFiles = [];
        this.isIngesting = false;
        
        // Documents
        this.documentsList = document.getElementById('documents-list');
        
        // Toast container
        this.toastContainer = document.getElementById('toast-container');
    }
    
    bindEvents() {
        // Message input events
        this.messageInput.addEventListener('input', () => {
            this.adjustTextareaHeight();
            this.updateSendButton();
        });
        
        this.messageInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        // Send button
        this.sendBtn.addEventListener('click', () => this.sendMessage());
        
        // Tools display
        this.closeTools.addEventListener('click', () => {
            this.toolsDisplay.style.display = 'none';
        });
        
        // Action buttons
        this.clearChatBtn.addEventListener('click', () => this.clearChat());
        this.exportChatBtn.addEventListener('click', () => this.exportChat());
        this.settingsBtn.addEventListener('click', () => this.openSettingsModal());
        this.ingestionBtn.addEventListener('click', () => this.openIngestionModal());

        // Settings modal events
        this.closeSettingsModal.addEventListener('click', () => this.closeModal(this.settingsModal));
        this.saveSettingsBtn.addEventListener('click', () => this.saveSettings());
        this.loadSettingsBtn.addEventListener('click', () => this.loadSettings());
        this.testDbBtn.addEventListener('click', () => this.testDatabaseConnection());
        this.testLlmBtn.addEventListener('click', () => this.testLlmConnection());

        // Ingestion modal events
        this.closeIngestionModal.addEventListener('click', () => this.closeModal(this.ingestionModal));
        this.browseFilesBtn.addEventListener('click', () => this.fileInput.click());
        this.fileInput.addEventListener('change', (e) => this.handleFileSelection(e));
        this.startIngestionBtn.addEventListener('click', () => this.startIngestion());
        this.cancelIngestionBtn.addEventListener('click', () => this.cancelIngestion());

        // Clear files button
        document.addEventListener('click', (e) => {
            if (e.target.id === 'clear-files' || e.target.closest('#clear-files')) {
                this.clearSelectedFiles();
            }
        });

        // Ingestion mode change events
        document.querySelectorAll('input[name="ingestion-mode"]').forEach(radio => {
            radio.addEventListener('change', () => this.handleModeChange());
        });

        // Upload area drag and drop
        this.setupDragAndDrop();

        // Tab switching
        this.setupTabSwitching();
        
        // Example queries
        document.addEventListener('click', (e) => {
            if (e.target.closest('.example-queries li')) {
                const query = e.target.textContent.replace(/['"]/g, '');
                this.messageInput.value = query;
                this.updateSendButton();
                this.messageInput.focus();
            }
        });
    }
    
    adjustTextareaHeight() {
        this.messageInput.style.height = 'auto';
        this.messageInput.style.height = Math.min(this.messageInput.scrollHeight, 120) + 'px';
    }
    
    updateSendButton() {
        const hasText = this.messageInput.value.trim().length > 0;
        this.sendBtn.disabled = !hasText || this.isStreaming;
    }
    
    async checkHealth() {
        try {
            const response = await fetch('/health');
            const health = await response.json();
            
            this.updateHealthStatus(health);
        } catch (error) {
            console.error('Health check failed:', error);
            this.updateHealthStatus({ status: 'unhealthy', error: error.message });
        }
    }
    
    updateHealthStatus(health) {
        this.statusDot.className = `status-dot ${health.status}`;
        
        let statusText = '';
        switch (health.status) {
            case 'healthy':
                statusText = 'Connected';
                break;
            case 'degraded':
                statusText = 'Partially Connected';
                break;
            case 'unhealthy':
                statusText = 'Disconnected';
                break;
            default:
                statusText = 'Unknown';
        }
        
        this.statusText.textContent = statusText;
    }
    
    async loadDocuments() {
        try {
            const response = await fetch('/documents?limit=10');
            const data = await response.json();
            
            if (data.documents) {
                this.displayDocuments(data.documents);
            } else {
                this.documentsList.innerHTML = '<div class="loading">No documents found</div>';
            }
        } catch (error) {
            console.error('Failed to load documents:', error);
            this.documentsList.innerHTML = '<div class="loading">Failed to load documents</div>';
        }
    }
    
    displayDocuments(documents) {
        if (documents.length === 0) {
            this.documentsList.innerHTML = '<div class="loading">No documents available</div>';
            return;
        }
        
        this.documentsList.innerHTML = documents.map(doc => 
            `<div class="document-item" title="${doc.title || doc.filename}">
                <i class="fas fa-file-alt"></i> ${(doc.title || doc.filename || 'Untitled').substring(0, 30)}...
            </div>`
        ).join('');
    }
    
    async sendMessage() {
        const message = this.messageInput.value.trim();
        if (!message || this.isStreaming) return;
        
        // Add user message to chat
        this.addMessage('user', message);
        
        // Clear input and disable send button
        this.messageInput.value = '';
        this.adjustTextareaHeight();
        this.updateSendButton();
        
        // Show typing indicator
        this.showTypingIndicator();
        
        // Start streaming
        this.isStreaming = true;
        await this.streamChat(message);
        this.isStreaming = false;
        
        // Hide typing indicator and update send button
        this.hideTypingIndicator();
        this.updateSendButton();
    }
    
    async streamChat(message) {
        try {
            const response = await fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message,
                    session_id: this.sessionId,
                    user_id: this.userId
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            
            let assistantMessage = this.addMessage('assistant', '');
            let fullResponse = '';
            let toolsUsed = [];
            
            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                
                const chunk = decoder.decode(value);
                const lines = chunk.split('\n');
                
                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const data = JSON.parse(line.slice(6));
                            
                            switch (data.type) {
                                case 'session':
                                    this.sessionId = data.session_id;
                                    break;
                                    
                                case 'text':
                                    fullResponse += data.content;
                                    this.updateMessage(assistantMessage, fullResponse);
                                    break;
                                    
                                case 'tools':
                                    toolsUsed = data.tools;
                                    break;
                                    
                                case 'end':
                                    if (toolsUsed.length > 0) {
                                        this.showToolsUsed(toolsUsed);
                                    }
                                    return;
                                    
                                case 'error':
                                    this.updateMessage(assistantMessage, `Error: ${data.content}`);
                                    this.showToast('error', 'An error occurred while processing your message');
                                    return;
                            }
                        } catch (e) {
                            console.warn('Failed to parse SSE data:', line);
                        }
                    }
                }
            }
        } catch (error) {
            console.error('Stream chat failed:', error);
            this.showToast('error', `Connection error: ${error.message}`);
            this.addMessage('assistant', `I'm sorry, I encountered an error: ${error.message}`);
        }
    }
    
    addMessage(role, content) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        
        if (role === 'assistant') {
            const headerDiv = document.createElement('div');
            headerDiv.className = 'message-header';
            headerDiv.innerHTML = '<i class="fas fa-robot"></i> Assistant';
            contentDiv.appendChild(headerDiv);
        }
        
        const textDiv = document.createElement('div');
        textDiv.className = 'message-text';
        textDiv.textContent = content;
        contentDiv.appendChild(textDiv);
        
        messageDiv.appendChild(contentDiv);
        
        // Remove welcome message if it exists
        const welcomeMessage = this.chatMessages.querySelector('.welcome-message');
        if (welcomeMessage) {
            welcomeMessage.remove();
        }
        
        this.chatMessages.appendChild(messageDiv);
        this.scrollToBottom();
        
        return messageDiv;
    }
    
    updateMessage(messageElement, content) {
        const textDiv = messageElement.querySelector('.message-text');
        if (textDiv) {
            textDiv.textContent = content;
            this.scrollToBottom();
        }
    }
    
    scrollToBottom() {
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }
    
    showTypingIndicator() {
        this.typingIndicator.style.display = 'inline-flex';
    }
    
    hideTypingIndicator() {
        this.typingIndicator.style.display = 'none';
    }
    
    showToolsUsed(tools) {
        this.toolsContent.innerHTML = tools.map(tool => 
            `<div class="tool-item">
                <div class="tool-name">${tool.tool_name}</div>
                <div class="tool-args">${this.formatToolArgs(tool.args)}</div>
            </div>`
        ).join('');
        
        this.toolsDisplay.style.display = 'block';
        
        // Auto-hide after 10 seconds
        setTimeout(() => {
            this.toolsDisplay.style.display = 'none';
        }, 10000);
    }
    
    formatToolArgs(args) {
        if (!args || Object.keys(args).length === 0) {
            return 'No arguments';
        }
        
        return Object.entries(args)
            .map(([key, value]) => {
                if (typeof value === 'string' && value.length > 50) {
                    return `${key}: "${value.substring(0, 50)}..."`;
                }
                return `${key}: ${JSON.stringify(value)}`;
            })
            .join(', ');
    }
    


    
    clearChat() {
        this.chatMessages.innerHTML = `
            <div class="welcome-message">
                <div class="welcome-content">
                    <h2>Welcome to Agentic RAG! 🚀</h2>
                    <p>I'm an AI agent with access to vector search, knowledge graph, and hybrid search tools.</p>
                    <div class="example-queries">
                        <h4>Try asking me about:</h4>
                        <ul>
                            <li>"What are Google's AI initiatives?"</li>
                            <li>"Tell me about Microsoft's partnerships with OpenAI"</li>
                            <li>"Compare OpenAI and Anthropic's approaches to AI safety"</li>
                        </ul>
                    </div>
                </div>
            </div>
        `;
        this.sessionId = null;
        this.showToast('success', 'Chat cleared');
    }
    
    exportChat() {
        const messages = Array.from(this.chatMessages.querySelectorAll('.message')).map(msg => {
            const role = msg.classList.contains('user') ? 'User' : 'Assistant';
            const content = msg.querySelector('.message-text').textContent;
            return `${role}: ${content}`;
        });
        
        if (messages.length === 0) {
            this.showToast('warning', 'No messages to export');
            return;
        }
        
        const chatText = messages.join('\n\n');
        const blob = new Blob([chatText], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = `agentic-rag-chat-${new Date().toISOString().slice(0, 19)}.txt`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        this.showToast('success', 'Chat exported successfully');
    }
    
    showToast(type, message) {
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.textContent = message;

        this.toastContainer.appendChild(toast);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 5000);
    }

    // Settings Management
    openSettingsModal() {
        this.settingsModal.style.display = 'block';
        this.loadSettings();
    }

    closeModal(modal) {
        modal.style.display = 'none';
    }

    setupTabSwitching() {
        const tabBtns = document.querySelectorAll('.tab-btn');
        const tabPanes = document.querySelectorAll('.tab-pane');

        tabBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                const targetTab = btn.dataset.tab;

                // Update active tab button
                tabBtns.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');

                // Update active tab pane
                tabPanes.forEach(pane => pane.classList.remove('active'));
                document.getElementById(`${targetTab}-tab`).classList.add('active');
            });
        });
    }

    async loadSettings() {
        try {
            const response = await fetch('/api/settings');
            if (response.ok) {
                const settings = await response.json();
                this.populateSettingsForm(settings);
            } else {
                this.showToast('warning', 'Could not load current settings');
            }
        } catch (error) {
            console.error('Failed to load settings:', error);
            this.showToast('error', 'Failed to load settings');
        }
    }

    populateSettingsForm(settings) {
        // Database settings
        document.getElementById('database-url').value = settings.database_url || '';
        document.getElementById('neo4j-uri').value = settings.neo4j_uri || '';
        document.getElementById('neo4j-username').value = settings.neo4j_username || '';
        document.getElementById('neo4j-password').value = settings.neo4j_password || '';

        // LLM settings
        document.getElementById('llm-provider').value = settings.llm_provider || 'openai';
        document.getElementById('llm-api-key').value = settings.llm_api_key || '';
        document.getElementById('llm-model').value = settings.llm_model || '';
        document.getElementById('embedding-model').value = settings.embedding_model || '';

        // Ingestion settings
        document.getElementById('chunk-size').value = settings.chunk_size || 8000;
        document.getElementById('chunk-overlap').value = settings.chunk_overlap || 800;
        document.getElementById('extract-entities').checked = settings.extract_entities !== false;
        document.getElementById('clean-before-ingest').checked = settings.clean_before_ingest || false;
    }

    async saveSettings() {
        const settings = {
            database_url: document.getElementById('database-url').value,
            neo4j_uri: document.getElementById('neo4j-uri').value,
            neo4j_username: document.getElementById('neo4j-username').value,
            neo4j_password: document.getElementById('neo4j-password').value,
            llm_provider: document.getElementById('llm-provider').value,
            llm_api_key: document.getElementById('llm-api-key').value,
            llm_model: document.getElementById('llm-model').value,
            embedding_model: document.getElementById('embedding-model').value,
            chunk_size: parseInt(document.getElementById('chunk-size').value),
            chunk_overlap: parseInt(document.getElementById('chunk-overlap').value),
            extract_entities: document.getElementById('extract-entities').checked,
            clean_before_ingest: document.getElementById('clean-before-ingest').checked
        };

        try {
            const response = await fetch('/api/settings', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(settings)
            });

            if (response.ok) {
                this.showToast('success', 'Settings saved successfully');
                this.closeModal(this.settingsModal);
            } else {
                const error = await response.json();
                this.showToast('error', `Failed to save settings: ${error.detail}`);
            }
        } catch (error) {
            console.error('Failed to save settings:', error);
            this.showToast('error', 'Failed to save settings');
        }
    }

    async testDatabaseConnection() {
        const dbUrl = document.getElementById('database-url').value;
        const neo4jUri = document.getElementById('neo4j-uri').value;
        const neo4jUsername = document.getElementById('neo4j-username').value;
        const neo4jPassword = document.getElementById('neo4j-password').value;

        if (!dbUrl || !neo4jUri) {
            this.showToast('warning', 'Please fill in database connection details');
            return;
        }

        try {
            const response = await fetch('/api/test-connections', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    database_url: dbUrl,
                    neo4j_uri: neo4jUri,
                    neo4j_username: neo4jUsername,
                    neo4j_password: neo4jPassword
                })
            });

            const result = await response.json();

            if (result.database && result.neo4j) {
                this.showToast('success', 'Database connections successful');
            } else {
                const errors = [];
                if (!result.database) errors.push('PostgreSQL');
                if (!result.neo4j) errors.push('Neo4j');
                this.showToast('error', `Connection failed: ${errors.join(', ')}`);
            }
        } catch (error) {
            console.error('Connection test failed:', error);
            this.showToast('error', 'Connection test failed');
        }
    }

    async testLlmConnection() {
        const provider = document.getElementById('llm-provider').value;
        const apiKey = document.getElementById('llm-api-key').value;
        const model = document.getElementById('llm-model').value;

        if (!apiKey || !model) {
            this.showToast('warning', 'Please fill in LLM configuration');
            return;
        }

        try {
            const response = await fetch('/api/test-llm', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    provider: provider,
                    api_key: apiKey,
                    model: model
                })
            });

            const result = await response.json();

            if (result.success) {
                this.showToast('success', 'LLM connection successful');
            } else {
                this.showToast('error', `LLM test failed: ${result.error}`);
            }
        } catch (error) {
            console.error('LLM test failed:', error);
            this.showToast('error', 'LLM test failed');
        }
    }

    // Document Ingestion
    openIngestionModal() {
        this.ingestionModal.style.display = 'block';
        this.resetIngestionForm();
        this.handleModeChange(); // Initialize mode-specific UI
    }

    resetIngestionForm() {
        this.selectedFiles = [];
        this.updateFileList();
        this.hideIngestionProgress();
        this.hideIngestionResults();
        this.updateStartButtonState();
        this.isIngesting = false;
    }

    handleModeChange() {
        const selectedMode = document.querySelector('input[name="ingestion-mode"]:checked').value;

        // Update button text based on mode
        const modeTexts = {
            'basic': 'Start Basic Ingestion',
            'clean': 'Clean & Re-ingest All',
            'fast': 'Start Fast Processing'
        };

        this.startIngestionBtn.innerHTML = `<i class="fas fa-play"></i> ${modeTexts[selectedMode]}`;

        // Update button state
        this.updateStartButtonState();
    }

    updateStartButtonState() {
        // Always require files to be selected
        this.startIngestionBtn.disabled = this.selectedFiles.length === 0;
    }

    clearSelectedFiles() {
        this.selectedFiles = [];
        this.updateFileList();
        this.updateStartButtonState();
        this.showToast('info', 'All files cleared');
    }

    setupDragAndDrop() {
        this.uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            this.uploadArea.classList.add('dragover');
        });

        this.uploadArea.addEventListener('dragleave', (e) => {
            e.preventDefault();
            this.uploadArea.classList.remove('dragover');
        });

        this.uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            this.uploadArea.classList.remove('dragover');

            const files = Array.from(e.dataTransfer.files);
            this.addFiles(files);
        });

        this.uploadArea.addEventListener('click', () => {
            this.fileInput.click();
        });
    }

    handleFileSelection(event) {
        const files = Array.from(event.target.files);
        this.addFiles(files);
    }

    addFiles(files) {
        const validFiles = files.filter(file => {
            const isValid = file.name.endsWith('.md') || file.name.endsWith('.txt');
            if (!isValid) {
                this.showToast('warning', `Skipped ${file.name}: Only .md and .txt files are supported`);
            }
            return isValid;
        });

        // Add new files, avoiding duplicates
        validFiles.forEach(file => {
            if (!this.selectedFiles.some(f => f.name === file.name && f.size === file.size)) {
                this.selectedFiles.push(file);
            }
        });

        this.updateFileList();
        this.updateStartButtonState();
    }

    updateFileList() {
        const fileList = document.getElementById('file-list');
        const selectedFilesList = document.getElementById('selected-files');

        if (this.selectedFiles.length === 0) {
            fileList.style.display = 'none';
            return;
        }

        fileList.style.display = 'block';
        selectedFilesList.innerHTML = this.selectedFiles.map((file, index) => `
            <li>
                <span>${file.name} (${this.formatFileSize(file.size)})</span>
                <i class="fas fa-times file-remove" data-index="${index}"></i>
            </li>
        `).join('');

        // Add remove file event listeners
        selectedFilesList.querySelectorAll('.file-remove').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const index = parseInt(e.target.dataset.index);
                this.selectedFiles.splice(index, 1);
                this.updateFileList();
                this.updateStartButtonState();
            });
        });
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    async startIngestion() {
        const selectedMode = document.querySelector('input[name="ingestion-mode"]:checked').value;

        // Validate files are selected
        if (this.selectedFiles.length === 0) {
            this.showToast('warning', 'Please select files to ingest');
            return;
        }

        this.isIngesting = true;
        this.startIngestionBtn.disabled = true;
        this.cancelIngestionBtn.style.display = 'inline-block';

        this.showIngestionProgress();
        this.updateProgress(0, 'Preparing ingestion...');

        try {
            // Create FormData with uploaded files
            const formData = new FormData();
            this.selectedFiles.forEach(file => {
                formData.append('files', file);
            });

            // Enhanced ingestion configuration based on mode
            const config = this.getIngestionConfig(selectedMode);
            formData.append('config', JSON.stringify(config));

            // Start ingestion
            const response = await fetch('/api/ingest', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error(`Ingestion failed: ${response.statusText}`);
            }

            // Handle streaming response
            const reader = response.body.getReader();
            const decoder = new TextDecoder();

            while (true) {
                const { done, value } = await reader.read();

                if (done) break;

                const chunk = decoder.decode(value);
                const lines = chunk.split('\n');

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const data = JSON.parse(line.slice(6));
                            this.handleIngestionProgress(data);
                        } catch (e) {
                            console.error('Failed to parse progress data:', e);
                        }
                    }
                }

                if (!this.isIngesting) {
                    // Ingestion was cancelled
                    reader.cancel();
                    break;
                }
            }

        } catch (error) {
            console.error('Ingestion failed:', error);
            this.showToast('error', `Ingestion failed: ${error.message}`);
            this.updateProgress(0, 'Ingestion failed');
        } finally {
            this.isIngesting = false;
            this.startIngestionBtn.disabled = false;
            this.cancelIngestionBtn.style.display = 'none';
        }
    }

    handleIngestionProgress(data) {
        if (data.type === 'progress') {
            const percent = Math.round((data.current / data.total) * 100);
            this.updateProgress(percent, `Processing ${data.current}/${data.total} documents...`);
        } else if (data.type === 'result') {
            this.showIngestionResults(data.results);
            this.updateProgress(100, 'Ingestion completed');
            this.showToast('success', 'Document ingestion completed successfully');
        } else if (data.type === 'error') {
            this.showToast('error', `Ingestion error: ${data.message}`);
            this.updateProgress(0, 'Ingestion failed');
        }
    }

    updateProgress(percent, message) {
        const progressFill = document.getElementById('progress-fill');
        const progressText = document.getElementById('progress-text');

        progressFill.style.width = `${percent}%`;
        progressText.textContent = `${percent}% - ${message}`;
    }

    showIngestionProgress() {
        document.getElementById('ingestion-progress').style.display = 'block';
    }

    hideIngestionProgress() {
        document.getElementById('ingestion-progress').style.display = 'none';
    }

    showIngestionResults(results) {
        const resultsContainer = document.getElementById('ingestion-results');
        const resultsContent = document.getElementById('results-content');

        resultsContent.innerHTML = results.map(result => `
            <div class="result-item">
                <h6>${result.title}</h6>
                <div class="result-stats">
                    <span class="status-success">✓ ${result.chunks_created} chunks</span>
                    <span class="status-success">✓ ${result.entities_extracted} entities</span>
                    <span class="status-success">✓ ${result.relationships_created} relationships</span>
                    <span>⏱ ${result.processing_time_ms}ms</span>
                </div>
                ${result.errors.length > 0 ? `
                    <div class="result-errors">
                        ${result.errors.map(error => `<div class="status-error">⚠ ${error}</div>`).join('')}
                    </div>
                ` : ''}
            </div>
        `).join('');

        resultsContainer.style.display = 'block';
    }

    hideIngestionResults() {
        document.getElementById('ingestion-results').style.display = 'none';
    }

    getIngestionConfig(mode) {
        // Base configuration from settings (if available)
        const baseConfig = {
            chunk_size: parseInt(document.getElementById('chunk-size')?.value) || 8000,
            chunk_overlap: parseInt(document.getElementById('chunk-overlap')?.value) || 800,
            extract_entities: document.getElementById('extract-entities')?.checked !== false,
            clean_before_ingest: document.getElementById('clean-before-ingest')?.checked || false,
            use_semantic: true,
            verbose: false,
            mode: mode
        };

        // Mode-specific overrides
        switch (mode) {
            case 'basic':
                return {
                    ...baseConfig,
                    mode: 'basic'
                };

            case 'clean':
                return {
                    ...baseConfig,
                    clean_before_ingest: true,
                    mode: 'clean'
                };

            case 'fast':
                return {
                    ...baseConfig,
                    chunk_size: 800,
                    use_semantic: false,
                    extract_entities: false,
                    verbose: true,
                    mode: 'fast'
                };

            default:
                return baseConfig;
        }
    }

    cancelIngestion() {
        this.isIngesting = false;
        this.updateProgress(0, 'Ingestion cancelled');
        this.showToast('warning', 'Ingestion cancelled');
        this.startIngestionBtn.disabled = false;
        this.cancelIngestionBtn.style.display = 'none';
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new AgenticRAGUI();
});
