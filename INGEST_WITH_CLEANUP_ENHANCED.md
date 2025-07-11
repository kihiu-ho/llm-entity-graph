# Enhanced Ingest with Cleanup Script

## Overview

The `ingest_with_cleanup.py` script has been enhanced with comprehensive Neo4j database cleanup functionality. It now provides three main modes of operation:

1. **Standard Ingestion with Cleanup** - Ingest documents and clean up Entity labels
2. **Clean Before Ingestion** - Clean databases before ingesting new documents  
3. **Neo4j-Only Cleanup** - Clean Neo4j database without ingestion

## Features

### ✅ Comprehensive Database Cleanup
- **Knowledge Graph**: Removes all nodes and relationships from Neo4j
- **PostgreSQL**: Cleans documents, chunks, messages, and sessions tables
- **Entity Labels**: Removes unwanted Entity labels from Person/Company nodes
- **Statistics**: Provides detailed cleanup statistics

### ✅ Flexible Operation Modes
- **Full ingestion pipeline** with automatic cleanup
- **Database-only cleanup** without document processing
- **Validation** to prevent conflicting options

### ✅ Enhanced Error Handling
- **Graceful fallbacks** when components fail
- **Non-critical cleanup** doesn't stop ingestion
- **Detailed logging** for troubleshooting

## Usage Examples

### Standard Document Ingestion with Cleanup
```bash
# Basic ingestion with automatic Entity label cleanup
python ingest_with_cleanup.py

# Ingest specific folder with cleanup
python ingest_with_cleanup.py --documents my_docs --verbose

# Fast mode (skip graph building and cleanup)
python ingest_with_cleanup.py --fast
```

### Clean Before Ingestion
```bash
# Clean existing data first, then ingest with cleanup
python ingest_with_cleanup.py --clean --verbose

# Clean and ingest specific folder
python ingest_with_cleanup.py --documents my_docs --clean
```

### Neo4j-Only Cleanup
```bash
# Only clean Neo4j database (no ingestion)
python ingest_with_cleanup.py --clean-neo4j-only --verbose

# Clean Neo4j database quietly
python ingest_with_cleanup.py --clean-neo4j-only
```

## Command Line Options

| Option | Description |
|--------|-------------|
| `--documents, -d` | Documents folder path (default: documents) |
| `--clean, -c` | Clean existing data before ingestion |
| `--clean-neo4j-only` | Only clean Neo4j database (skip ingestion) |
| `--chunk-size` | Chunk size for splitting documents (default: 12000) |
| `--chunk-overlap` | Chunk overlap size (default: 1200) |
| `--no-semantic` | Disable semantic chunking |
| `--no-entities` | Disable entity extraction |
| `--fast, -f` | Fast mode: skip knowledge graph building |
| `--verbose, -v` | Enable verbose logging |

## Cleanup Process

### Neo4j-Only Cleanup Mode (`--clean-neo4j-only`)

**Step 1: Clear Knowledge Graph**
- Removes all nodes and relationships from Neo4j
- Uses `MATCH (n) DETACH DELETE n` query
- Reports number of nodes and relationships deleted

**Step 2: Clean PostgreSQL Database**
- Counts existing records before cleanup
- Deletes from: messages, sessions, chunks, documents tables
- Reports number of records removed from each table

**Step 3: Clean Entity Labels**
- Finds Person/Company nodes with Entity labels
- Removes Entity labels while preserving specific labels
- Reports number of nodes fixed

### Standard Ingestion Mode

**Document Processing**
- Processes documents according to configuration
- Extracts entities and builds knowledge graph
- Automatically runs Entity label cleanup after graph building

**Cleanup Integration**
- Runs after successful graph building
- Non-critical: failures don't stop ingestion
- Provides cleanup statistics in final summary

## Output Examples

### Neo4j-Only Cleanup
```
🧹 Starting Neo4j database cleanup only
🗑️  Starting comprehensive Neo4j database cleanup...
🧹 Step 1: Clearing knowledge graph...
✅ Knowledge graph cleared
🧹 Step 2: Cleaning PostgreSQL database...
Found 6 messages, 1 sessions, 54 chunks, 4 documents
✅ PostgreSQL database cleaned
🧹 Step 3: Cleaning up Entity labels...
✅ No Entity labels found to clean up
🎉 Neo4j database cleanup completed successfully!

============================================================
📊 FINAL SUMMARY
============================================================
Knowledge graph cleared: Yes
PostgreSQL cleaned: Yes
Documents removed: 4
Chunks removed: 54
Messages removed: 6
Sessions removed: 1
Entity labels fixed: 0
============================================================
✅ All operations completed successfully!
```

### Standard Ingestion with Cleanup
```
🚀 Starting document ingestion with automatic Entity label cleanup
📄 Step 1: Running document ingestion...
✅ Ingestion complete: 3 documents, 25 chunks, 15 entities, 8 episodes
🧹 Step 2: Running Entity label cleanup...
✅ Cleanup complete: 5 nodes fixed
🎉 Document ingestion with cleanup completed successfully!

============================================================
📊 FINAL SUMMARY
============================================================
Documents processed: 3
Chunks created: 25
Entities extracted: 15
Graph episodes: 8
Errors: 0
Entity cleanup performed: Yes
============================================================
✅ All operations completed successfully!
```

## Error Handling

### Validation
- Prevents using `--clean-neo4j-only` with `--clean` together
- Warns when `--fast` is used with `--clean-neo4j-only`
- Checks document folder exists (only for ingestion mode)

### Graceful Failures
- Cleanup failures are logged as warnings, not errors
- Ingestion continues even if cleanup fails
- Database connections are properly closed

### Logging Levels
- **INFO**: Standard operation messages
- **WARNING**: Non-critical issues (cleanup failures)
- **ERROR**: Critical failures that stop execution
- **DEBUG**: Detailed connection and query information (with `--verbose`)

## Integration with Existing Workflow

### Backward Compatibility
- All existing command-line options work unchanged
- Default behavior remains the same
- New options are additive, not breaking

### Automation Ready
- Exit codes: 0 for success, 1 for failure
- Machine-readable output available
- Can be integrated into CI/CD pipelines

### Monitoring
- Detailed statistics for tracking cleanup effectiveness
- Clear success/failure indicators
- Comprehensive logging for troubleshooting

## Benefits

### 🧹 Complete Database Reset
- One command cleans entire system
- Removes all data: nodes, relationships, documents, chunks
- Perfect for development and testing

### 🔄 Automated Maintenance
- Entity label cleanup runs automatically
- No manual intervention required
- Maintains clean database state

### 📊 Comprehensive Reporting
- Detailed statistics for all operations
- Clear success/failure indicators
- Helps track system usage and cleanup effectiveness

### 🛡️ Safe Operation
- Validates conflicting options
- Graceful error handling
- Non-destructive by default (requires explicit flags)

## Use Cases

### Development
```bash
# Reset everything for fresh start
python ingest_with_cleanup.py --clean-neo4j-only

# Ingest test data
python ingest_with_cleanup.py --documents test_docs
```

### Production Maintenance
```bash
# Clean up Entity labels without affecting data
python cleanup_entity_labels.py

# Full system reset (use with caution)
python ingest_with_cleanup.py --clean-neo4j-only
```

### Continuous Integration
```bash
# Clean environment before tests
python ingest_with_cleanup.py --clean-neo4j-only --quiet

# Run tests with fresh ingestion
python ingest_with_cleanup.py --documents test_data --clean
```

The enhanced script provides a comprehensive solution for managing both document ingestion and database cleanup in a single, easy-to-use tool.
