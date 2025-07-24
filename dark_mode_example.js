// Dark Mode Toggle Implementation
// Add this to web_ui/static/js/approval.js

class DarkModeToggle {
    constructor() {
        this.isDarkMode = localStorage.getItem('darkMode') === 'true';
        this.init();
    }

    init() {
        // Apply saved theme
        if (this.isDarkMode) {
            document.body.setAttribute('data-theme', 'dark');
        }
        
        // Create toggle button
        this.createToggleButton();
    }

    createToggleButton() {
        const toggleBtn = document.createElement('button');
        toggleBtn.id = 'dark-mode-toggle';
        toggleBtn.className = 'nav-btn';
        toggleBtn.innerHTML = `<i class="fas fa-${this.isDarkMode ? 'sun' : 'moon'}"></i>`;
        toggleBtn.title = `Switch to ${this.isDarkMode ? 'light' : 'dark'} mode`;
        
        // Add to navigation
        const nav = document.querySelector('.approval-nav');
        nav.insertBefore(toggleBtn, nav.firstChild);
        
        // Add click handler
        toggleBtn.addEventListener('click', () => this.toggle());
    }

    toggle() {
        this.isDarkMode = !this.isDarkMode;
        
        if (this.isDarkMode) {
            document.body.setAttribute('data-theme', 'dark');
        } else {
            document.body.removeAttribute('data-theme');
        }
        
        // Update button icon
        const toggleBtn = document.getElementById('dark-mode-toggle');
        toggleBtn.innerHTML = `<i class="fas fa-${this.isDarkMode ? 'sun' : 'moon'}"></i>`;
        toggleBtn.title = `Switch to ${this.isDarkMode ? 'light' : 'dark'} mode`;
        
        // Save preference
        localStorage.setItem('darkMode', this.isDarkMode.toString());
    }
}

// Add to existing ApprovalDashboard constructor
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
        
        // Initialize dark mode toggle
        this.darkModeToggle = new DarkModeToggle();
        
        this.init();
    }
    
    // ... rest of existing methods
}