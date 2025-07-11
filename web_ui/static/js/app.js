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
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new AgenticRAGUI();
});
