# Entity Review & Approval System

A comprehensive web UI for reviewing and approving extracted entities and relationships before they are ingested into Graphiti.

## 🎯 Overview

The Entity Review System provides a staging workflow where:

1. **Entity Extraction** - Graph builder extracts entities using LLM
2. **Staging** - Entities are saved to staging area for review
3. **Review & Editing** - Web UI allows line-by-line review and editing
4. **Approval** - Entities can be approved, rejected, or edited
5. **Ingestion** - Only approved entities are ingested to Graphiti

## 🏗️ Architecture

### Backend Components

- **Staging API** (`web_ui/app.py`) - REST endpoints for entity management
- **Graph Builder** (`ingestion/graph_builder.py`) - Modified to use staging
- **Staging Storage** (`staging/data/`) - JSON files for staging sessions

### Frontend Components

- **Entity Review UI** (`web_ui/templates/entity_review.html`) - Main interface
- **JavaScript App** (`web_ui/static/js/entity_review.js`) - Interactive functionality

## 🚀 Getting Started

### 1. Start the Web UI

```bash
cd web_ui
python start.py
```

### 2. Access Entity Review

Open your browser to:
- **Main Chat**: http://localhost:5001/
- **Entity Review**: http://localhost:5001/entity-review

### 3. Test the System

```bash
python test_entity_staging.py
```

## 📋 Features

### Entity Management

- **View All Sessions** - List all staging sessions with statistics
- **Entity Review** - Review extracted entities line by line
- **Relationship Review** - Review extracted relationships
- **Batch Operations** - Approve/reject multiple items at once
- **Individual Actions** - Approve, reject, or edit single entities

### Editing Capabilities

- **Entity Editing** - Modify entity names, types, and attributes
- **Relationship Editing** - Modify relationship types and connections
- **Confidence Scores** - Visual confidence indicators
- **Status Tracking** - Pending, approved, rejected, ingested

### Approval Workflow

- **Selective Approval** - Choose which entities to approve
- **Batch Approval** - Approve all entities in a session
- **Review Statistics** - Track approval progress
- **Final Ingestion** - Ingest approved entities to Graphiti

## 🔧 API Endpoints

### Session Management

```http
GET /api/staging/sessions
GET /api/staging/sessions/{session_id}
GET /api/staging/sessions/{session_id}/entities
GET /api/staging/sessions/{session_id}/relationships
```

### Entity Operations

```http
PUT /api/staging/entities/{entity_id}
PUT /api/staging/relationships/{relationship_id}
```

### Batch Operations

```http
POST /api/staging/batch-approve
POST /api/staging/batch-reject
POST /api/staging/ingest
```

## 📊 Data Structure

### Staging Session

```json
{
  "session_id": "uuid",
  "document_title": "Document Name",
  "document_source": "file.md",
  "created_at": "2025-01-01T00:00:00Z",
  "status": "pending_review",
  "entities": [...],
  "relationships": [...],
  "statistics": {
    "total_entities": 10,
    "approved_entities": 5,
    "rejected_entities": 2,
    "pending_entities": 3
  }
}
```

### Entity Structure

```json
{
  "id": "uuid",
  "name": "John Smith",
  "type": "Person",
  "attributes": {
    "entity_type": "person",
    "role_type": "executive",
    "position": "CEO",
    "company": "TechCorp"
  },
  "confidence": 0.9,
  "status": "pending",
  "edited": false,
  "created_at": "2025-01-01T00:00:00Z",
  "source_text": "John Smith is the CEO..."
}
```

## 🔄 Workflow

### 1. Document Ingestion

When documents are ingested with staging enabled:

```python
# In ingestion/ingest.py
use_staging = True  # Default behavior
graph_result = await graph_builder.stage_document_entities(
    chunks=chunks,
    document_title=title,
    document_source=source,
    use_staging=use_staging
)
```

### 2. Entity Review

1. Navigate to `/entity-review`
2. Select a staging session
3. Review entities and relationships
4. Edit, approve, or reject items
5. Use batch operations for efficiency

### 3. Final Ingestion

After review, approved entities are ingested:

```javascript
// Ingest approved entities to Graphiti
await fetch('/api/staging/ingest', {
    method: 'POST',
    body: JSON.stringify({ session_id: sessionId })
});
```

## 🎨 User Interface

### Session Dashboard

- **Grid Layout** - Visual cards for each staging session
- **Status Indicators** - Color-coded status badges
- **Statistics** - Entity and relationship counts
- **Quick Actions** - Review, approve all, or ingest

### Entity Review Modal

- **Tabbed Interface** - Separate tabs for entities and relationships
- **Table View** - Sortable table with checkboxes
- **Batch Actions** - Toolbar for bulk operations
- **Individual Actions** - Edit, approve, reject buttons
- **Confidence Bars** - Visual confidence indicators

### Editing Interface

- **Inline Editing** - Edit entity names and types
- **Attribute Editing** - Modify entity attributes
- **Relationship Editing** - Change relationship types and connections
- **Validation** - Client-side validation for required fields

## 🔧 Configuration

### Enable/Disable Staging

```python
# In ingestion config
use_entity_staging = True  # Use staging (default)
use_entity_staging = False  # Direct ingestion (legacy)
```

### Staging Directory

```python
# Staging files are stored in:
staging/data/{session_id}.json
```

## 🧪 Testing

### Run Tests

```bash
# Test entity staging
python test_entity_staging.py

# Test web UI endpoints
curl http://localhost:5001/api/staging/sessions
```

### Sample Data

The test script creates sample entities for testing:

- **People**: John Smith (CEO), Mary Johnson (CTO)
- **Companies**: TechCorp Inc., Microsoft, Google, Apple Inc.
- **Relationships**: Employment, partnerships, funding

## 🚀 Deployment

### Production Setup

1. **Environment Variables**
   ```bash
   export USE_ENTITY_STAGING=true
   export STAGING_DIR=/app/staging/data
   ```

2. **Persistent Storage**
   - Mount staging directory for persistence
   - Consider database storage for production

3. **Security**
   - Add authentication for entity review
   - Implement role-based access control

## 🔮 Future Enhancements

### Planned Features

- **Entity Editing Modal** - Rich editing interface
- **Relationship Visualization** - Graph view of relationships
- **Approval Workflows** - Multi-step approval process
- **Audit Trail** - Track all changes and approvals
- **Export/Import** - Backup and restore staging data
- **Integration** - Connect with external review systems

### Advanced Features

- **AI-Assisted Review** - Suggest corrections and improvements
- **Confidence Thresholds** - Auto-approve high-confidence entities
- **Duplicate Detection** - Identify and merge duplicate entities
- **Validation Rules** - Custom validation for entity types
- **Bulk Import** - Import entities from external sources

## 📚 Documentation

- **API Reference** - Detailed endpoint documentation
- **User Guide** - Step-by-step usage instructions
- **Developer Guide** - Extension and customization
- **Troubleshooting** - Common issues and solutions

## 🤝 Contributing

1. **Fork the repository**
2. **Create feature branch**
3. **Add tests for new features**
4. **Submit pull request**

## 📄 License

This project is licensed under the MIT License.
