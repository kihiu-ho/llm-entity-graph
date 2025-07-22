# Entity & Relationship Review System

## Overview

A comprehensive web-based review system that allows users to review, edit, and approve extracted entities and relationships before they are ingested into Graphiti. This ensures high data quality and gives users complete control over what gets added to their knowledge graph.

## ✅ Implementation Complete

### Key Features

1. **📋 Staging System**: Extracted entities and relationships are stored in a staging area for review
2. **🖥️ Web UI Interface**: Intuitive interface for reviewing and editing extracted data
3. **✏️ Inline Editing**: Edit entity names, types, and relationship details directly in the interface
4. **✅ Approval Workflow**: Approve, reject, or edit individual items or use bulk operations
5. **📊 Progress Tracking**: Visual progress indicators and statistics
6. **🔄 Batch Processing**: Ingest only approved items into Graphiti

### Architecture

```
Document Upload → Entity Extraction → Staging → Review UI → Approval → Graphiti Ingestion
```

## 🚀 How to Use

### 1. Access the Review Dashboard

- Start the web UI: `cd web_ui && python3 app.py`
- Navigate to: `http://localhost:5000/review`
- Or click "Review Dashboard" in the main interface

### 2. Upload Document for Review

1. Click "Upload Document for Review" section
2. Select a document file (.txt, .md, .pdf, .docx)
3. Optionally provide a custom title
4. Click "Extract & Review"
5. Wait for entity extraction to complete

### 3. Review Extracted Data

**Entity Review:**
- View all extracted entities in a table format
- Edit entity names and types inline
- See confidence scores and source text
- Approve ✅, reject ❌, or edit ✏️ individual entities

**Relationship Review:**
- Review extracted relationships between entities
- Edit source, target, and relationship types
- See confidence scores and source context
- Approve ✅, reject ❌, or edit ✏️ individual relationships

### 4. Bulk Operations

- **Approve All**: Approve all pending entities and relationships
- **Reject All**: Reject all pending entities and relationships
- **Ingest Approved**: Send approved items to Graphiti

### 5. Track Progress

- View statistics: total, approved, rejected counts
- Progress bars show completion percentage
- Color-coded status indicators

## 📁 File Structure

```
staging/
├── __init__.py
├── staging_manager.py      # Core staging data management
├── staging_ingestion.py    # Document processing for review
└── data/                   # JSON files storing staging sessions

web_ui/
├── templates/
│   ├── review_dashboard.html  # Main review dashboard
│   └── review.html           # Individual session review
├── static/
│   ├── css/review.css        # Review interface styling
│   └── js/review.js          # Review interface JavaScript
└── app.py                    # Updated with review routes
```

## 🔧 Technical Details

### Staging Data Format

Each staging session is stored as a JSON file:

```json
{
  "session_id": "uuid",
  "document_title": "Document Name",
  "created_at": "2025-01-21T10:00:00Z",
  "status": "pending_review|ingested",
  "entities": [
    {
      "id": "entity_uuid",
      "name": "John Smith",
      "type": "Person",
      "attributes": {...},
      "status": "pending|approved|rejected",
      "confidence": 0.9,
      "source_text": "Context where entity was found"
    }
  ],
  "relationships": [
    {
      "id": "rel_uuid",
      "source": "John Smith",
      "target": "TechCorp",
      "type": "Employment",
      "attributes": {...},
      "status": "pending|approved|rejected",
      "confidence": 0.9,
      "source_text": "Context where relationship was found"
    }
  ],
  "statistics": {
    "total_entities": 10,
    "approved_entities": 7,
    "total_relationships": 5,
    "approved_relationships": 4
  }
}
```

### API Endpoints

- `GET /review` - Review dashboard
- `GET /review/<session_id>` - Individual session review
- `POST /api/review/upload` - Upload document for review
- `POST /api/review/entity/<id>/status` - Update entity status
- `POST /api/review/entity/<id>/update` - Update entity data
- `POST /api/review/relationship/<id>/status` - Update relationship status
- `POST /api/review/relationship/<id>/update` - Update relationship data
- `POST /api/review/bulk-approve` - Approve all items
- `POST /api/review/bulk-reject` - Reject all items
- `POST /api/review/ingest` - Ingest approved items
- `DELETE /api/review/session/<id>` - Delete session

## 🎯 Benefits

### 1. Quality Control
- **Manual Review**: Human oversight ensures accuracy
- **Error Correction**: Fix extraction mistakes before ingestion
- **Confidence Filtering**: Review low-confidence extractions

### 2. Flexibility
- **Selective Ingestion**: Choose exactly what to add to the graph
- **Batch Processing**: Process multiple documents efficiently
- **Iterative Refinement**: Improve extraction over time

### 3. User Experience
- **Visual Interface**: Easy-to-use web interface
- **Real-time Editing**: Immediate feedback and updates
- **Progress Tracking**: Clear visibility into review status

### 4. Data Integrity
- **Staging Isolation**: Extracted data doesn't affect production graph
- **Audit Trail**: Track what was approved/rejected and when
- **Rollback Capability**: Can delete sessions if needed

## 🧪 Testing

Run the test script to verify the system:

```bash
python3 test_review_system.py
```

This tests:
- ✅ Staging manager functionality
- ✅ Document processing for review
- ✅ Entity and relationship staging
- ✅ Status updates and approval workflow
- ✅ Session management
- ✅ Approved items ingestion

## 🔄 Workflow Example

1. **Upload**: User uploads "company_report.pdf"
2. **Extract**: System extracts 15 entities, 8 relationships
3. **Review**: User reviews in web interface
   - Approves 12 entities, rejects 3
   - Edits 2 entity names for accuracy
   - Approves 6 relationships, rejects 2
4. **Ingest**: System adds 12 entities + 6 relationships to Graphiti
5. **Complete**: Session marked as "ingested"

## 🎉 Success Metrics

- **100% User Control**: Users decide what gets ingested
- **High Data Quality**: Manual review eliminates extraction errors
- **Efficient Workflow**: Bulk operations for large documents
- **Clear Visibility**: Progress tracking and statistics
- **Flexible Processing**: Handle any document type

## 🚀 Next Steps

The review system is fully functional and ready for use. Users can now:

1. Upload documents for entity extraction
2. Review and edit extracted data in a user-friendly interface
3. Approve only high-quality entities and relationships
4. Ingest approved items into Graphiti with confidence

This ensures that only accurate, verified data enters the knowledge graph, maintaining high data quality while giving users complete control over the ingestion process.
