#!/usr/bin/env python3
"""
Example: Customize UI Button Labels and Icons
"""

# To customize button labels, edit web_ui/templates/approval.html

# Original buttons (lines 105-119):
original_buttons = """
<button id="bulk-approve-btn" class="btn success" disabled>
    <i class="fas fa-check-double"></i> Bulk Approve
</button>
<button id="approve-all-btn" class="btn success">
    <i class="fas fa-check-circle"></i> Approve All
</button>
<button id="clean-pending-btn" class="btn warning">
    <i class="fas fa-trash-alt"></i> Clean Pending
</button>
<button id="open-ingestion-panel-btn" class="btn primary">
    <i class="fas fa-database"></i> Neo4j Ingestion
</button>
<button id="refresh-data-btn" class="btn secondary">
    <i class="fas fa-sync"></i> Refresh Data
</button>
"""

# Customized version with business-friendly labels:
customized_buttons = """
<button id="bulk-approve-btn" class="btn success" disabled>
    <i class="fas fa-thumbs-up"></i> Accept Selected
</button>
<button id="approve-all-btn" class="btn success">
    <i class="fas fa-check-double"></i> Accept All Items
</button>
<button id="clean-pending-btn" class="btn warning">
    <i class="fas fa-broom"></i> Clear Pending
</button>
<button id="open-ingestion-panel-btn" class="btn primary">
    <i class="fas fa-cloud-upload-alt"></i> Publish to Database
</button>
<button id="refresh-data-btn" class="btn secondary">
    <i class="fas fa-redo"></i> Reload
</button>
"""

# Technical version for developers:
technical_buttons = """
<button id="bulk-approve-btn" class="btn success" disabled>
    <i class="fas fa-code-branch"></i> Merge Selected
</button>
<button id="approve-all-btn" class="btn success">
    <i class="fas fa-rocket"></i> Deploy All
</button>
<button id="clean-pending-btn" class="btn warning">
    <i class="fas fa-trash-restore"></i> Purge Queue
</button>
<button id="open-ingestion-panel-btn" class="btn primary">
    <i class="fas fa-server"></i> Neo4j Sync
</button>
<button id="refresh-data-btn" class="btn secondary">
    <i class="fas fa-sync-alt"></i> Refresh
</button>
"""

print("Button customization examples created!")
print("Choose one of the styles above and replace the buttons in web_ui/templates/approval.html")