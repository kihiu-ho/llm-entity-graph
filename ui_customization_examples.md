# Web UI Customization Guide

## 1. Color Theme Customization

### Change Header Gradient
In `web_ui/static/css/approval.css`, modify line 5:
```css
/* Current purple gradient */
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);

/* Option 1: Blue gradient */
background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);

/* Option 2: Green gradient */
background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);

/* Option 3: Dark theme */
background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
```

### Change Button Colors
Modify button classes in the same file:
```css
/* Success buttons (green) */
.btn.success {
    background-color: #28a745; /* Current green */
    background-color: #00b894; /* Teal green */
    background-color: #6c5ce7; /* Purple */
}

/* Warning buttons (orange) */
.btn.warning {
    background-color: #ffc107; /* Current yellow/orange */
    background-color: #fd79a8; /* Pink */
    background-color: #e17055; /* Orange-red */
}

/* Primary buttons (blue) */
.btn.primary {
    background-color: #007bff; /* Current blue */
    background-color: #00cec9; /* Turquoise */
    background-color: #6c5ce7; /* Purple */
}
```

## 2. Layout Adjustments

### Change Page Title
In `web_ui/templates/approval.html`, lines 6 and 16:
```html
<!-- Current title -->
<title>🔍 Entity Approval Dashboard</title>
<h1><i class="fas fa-clipboard-check"></i> Entity Approval Dashboard</h1>

<!-- Custom titles -->
<title>📊 Document Review Center</title>
<h1><i class="fas fa-file-check"></i> Document Review Center</h1>

<title>🎯 Content Validation Hub</title>
<h1><i class="fas fa-tasks"></i> Content Validation Hub</h1>
```

### Modify Control Panel Buttons
In `web_ui/templates/approval.html`, lines 105-119:
```html
<!-- Current buttons -->
<button id="bulk-approve-btn" class="btn success" disabled>
    <i class="fas fa-check-double"></i> Bulk Approve
</button>
<button id="approve-all-btn" class="btn success">
    <i class="fas fa-check-circle"></i> Approve All
</button>

<!-- Custom button text/icons -->
<button id="bulk-approve-btn" class="btn success" disabled>
    <i class="fas fa-thumbs-up"></i> Accept Selected
</button>
<button id="approve-all-btn" class="btn success">
    <i class="fas fa-check-double"></i> Accept All Items
</button>
```

### Add Custom Buttons
Add new buttons to the control-actions div:
```html
<button id="export-data-btn" class="btn secondary">
    <i class="fas fa-download"></i> Export Data
</button>
<button id="import-data-btn" class="btn secondary">
    <i class="fas fa-upload"></i> Import Data
</button>
```

## 3. Table Customization

### Change Column Headers
In `web_ui/templates/approval.html`, lines 160-165:
```html
<!-- Current headers -->
<th class="type-col">Type</th>
<th class="name-col">Name</th>
<th class="properties-col">Properties</th>
<th class="status-col">Status</th>
<th class="actions-col">Actions</th>

<!-- Custom headers -->
<th class="type-col">Category</th>
<th class="name-col">Entity Name</th>
<th class="properties-col">Attributes</th>
<th class="status-col">Review Status</th>
<th class="actions-col">Controls</th>
```

### Add New Columns
Add after existing columns:
```html
<th class="confidence-col">Confidence</th>
<th class="source-col">Source</th>
<th class="date-col">Created</th>
```

## 4. Statistics Panel

### Customize Statistics Cards
In `web_ui/templates/approval.html`, lines 69-96:
```html
<!-- Current stats -->
<div class="stat-card">
    <div class="stat-icon"><i class="fas fa-list"></i></div>
    <div class="stat-content">
        <div class="stat-value" id="total-entities">0</div>
        <div class="stat-label">Total Entities</div>
    </div>
</div>

<!-- Add custom stats -->
<div class="stat-card processing">
    <div class="stat-icon"><i class="fas fa-cog"></i></div>
    <div class="stat-content">
        <div class="stat-value" id="processing-count">0</div>
        <div class="stat-label">Processing</div>
    </div>
</div>
```

## 5. Modal Customization

### Entity Detail Modal
The modal for entity details can be customized in lines 218-284:
```html
<!-- Change modal title -->
<h3><i class="fas fa-user"></i> Entity Details</h3>
<!-- to -->
<h3><i class="fas fa-info-circle"></i> Item Information</h3>

<!-- Add custom fields -->
<div class="form-group">
    <label for="priority-level">Priority Level:</label>
    <select id="priority-level">
        <option value="high">High</option>
        <option value="medium">Medium</option>
        <option value="low">Low</option>
    </select>
</div>
```

## 6. Notification Styles

### Custom Notification Types
In `web_ui/static/js/approval.js`, you can add custom notification types:
```javascript
// Current types: success, error, warning, info
this.showNotification('Custom message', 'custom');

// Add CSS for custom type in approval.css:
.notification.custom {
    background-color: #e67e22;
    border-left-color: #d35400;
}
```

## 7. Responsive Design

### Mobile Adjustments
Add to `approval.css`:
```css
@media (max-width: 768px) {
    .control-actions {
        flex-direction: column;
        gap: 0.5rem;
    }
    
    .control-actions button {
        width: 100%;
    }
    
    .header-content {
        flex-direction: column;
        text-align: center;
    }
}
```

## 8. Dark Mode Support

### Add Dark Theme Toggle
```css
/* Dark theme variables */
:root[data-theme="dark"] {
    --bg-color: #2c3e50;
    --text-color: #ecf0f1;
    --card-bg: #34495e;
    --border-color: #4a5a6b;
}

/* Apply dark theme */
body[data-theme="dark"] {
    background-color: var(--bg-color);
    color: var(--text-color);
}

body[data-theme="dark"] .dashboard-section {
    background-color: var(--card-bg);
    border: 1px solid var(--border-color);
}
```

## 9. Custom Icons

### Change FontAwesome Icons
Replace any `fas fa-*` classes with different icons:
```html
<!-- Current -->
<i class="fas fa-clipboard-check"></i>

<!-- Alternatives -->
<i class="fas fa-chart-line"></i>     <!-- Analytics -->
<i class="fas fa-shield-alt"></i>     <!-- Security -->
<i class="fas fa-cogs"></i>           <!-- Settings -->
<i class="fas fa-database"></i>       <!-- Data -->
<i class="fas fa-users"></i>          <!-- People -->
```

## 10. Performance Indicators

### Add Loading States
```css
.loading-state {
    opacity: 0.6;
    pointer-events: none;
    position: relative;
}

.loading-state::after {
    content: "";
    position: absolute;
    top: 50%;
    left: 50%;
    width: 20px;
    height: 20px;
    margin: -10px 0 0 -10px;
    border: 2px solid #f3f3f3;
    border-top: 2px solid #007bff;
    border-radius: 50%;
    animation: spin 1s linear infinite;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}
```