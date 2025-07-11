# Entity Label Cleanup Solution

## Problem

Neo4j nodes were being created with both specific labels (e.g., "Person", "Company") and a generic "Entity" label, resulting in nodes like:
- `["Person", "Entity"]` instead of just `["Person"]`
- `["Company", "Entity"]` instead of just `["Company"]`

This was caused by Graphiti's default behavior of adding an "Entity" label to all extracted entities, even when custom entity types are specified.

## Solution

We've implemented an automatic cleanup system that runs after each document ingestion to remove unwanted "Entity" labels from Person and Company nodes.

## Components

### 1. Standalone Cleanup Utility (`cleanup_entity_labels.py`)

A comprehensive utility that can be run independently:

```bash
# Check for Entity labels without removing them
python cleanup_entity_labels.py --check-only

# Remove Entity labels from Person and Company nodes
python cleanup_entity_labels.py

# Quiet mode (minimal output)
python cleanup_entity_labels.py --quiet
```

**Features:**
- ✅ Checks for nodes with Entity labels
- ✅ Removes Entity labels from Person and Company nodes
- ✅ Verifies cleanup was successful
- ✅ Provides detailed statistics
- ✅ Safe error handling

### 2. Integrated Ingestion Pipeline (`ingest_with_cleanup.py`)

A wrapper script that runs document ingestion followed by automatic cleanup:

```bash
# Basic ingestion with automatic cleanup
python ingest_with_cleanup.py

# Ingest specific folder with cleanup
python ingest_with_cleanup.py --documents my_docs

# Fast mode (skip graph building and cleanup)
python ingest_with_cleanup.py --fast

# Clean existing data first, then ingest with cleanup
python ingest_with_cleanup.py --clean --verbose
```

**Features:**
- ✅ Runs standard document ingestion
- ✅ Automatically cleans up Entity labels after ingestion
- ✅ Provides comprehensive progress reporting
- ✅ Handles errors gracefully
- ✅ Skips cleanup when graph building is disabled

### 3. Modified Ingestion Pipeline

The original `ingestion/ingest.py` has been enhanced to include automatic cleanup after graph building:

```python
# Clean up Entity labels after graph building
try:
    logger.info("Cleaning up Entity labels from Person and Company nodes...")
    cleanup_result = await self._cleanup_entity_labels()
    if cleanup_result:
        logger.info(f"✅ Cleaned up Entity labels: {cleanup_result['person_nodes_fixed']} Person nodes, {cleanup_result['company_nodes_fixed']} Company nodes")
    else:
        logger.info("✅ No Entity labels found to clean up")
except Exception as cleanup_error:
    logger.warning(f"Entity label cleanup failed (non-critical): {cleanup_error}")
```

## Usage Examples

### Quick Cleanup
```bash
# Just clean up existing Entity labels
python cleanup_entity_labels.py
```

### Full Ingestion with Cleanup
```bash
# Ingest documents and automatically clean up Entity labels
python ingest_with_cleanup.py --documents documents --verbose
```

### Check Status
```bash
# Check if any nodes have Entity labels
python cleanup_entity_labels.py --check-only
```

## How It Works

1. **Detection**: The system queries Neo4j for nodes that have both specific labels (Person/Company) and the generic Entity label
2. **Cleanup**: Removes the Entity label while preserving the specific label
3. **Verification**: Confirms that no Entity labels remain on Person/Company nodes

### Cypher Queries Used

```cypher
-- Find Person nodes with Entity label
MATCH (n:Person:Entity)
RETURN count(n) as count

-- Remove Entity label from Person nodes
MATCH (n:Person:Entity)
REMOVE n:Entity
RETURN count(n) as fixed_count

-- Find Company nodes with Entity label
MATCH (n:Company:Entity)
RETURN count(n) as count

-- Remove Entity label from Company nodes
MATCH (n:Company:Entity)
REMOVE n:Entity
RETURN count(n) as fixed_count
```

## Benefits

✅ **Automatic**: Runs after each document ingestion
✅ **Safe**: Only removes Entity labels, preserves all other data
✅ **Fast**: Efficient Cypher queries
✅ **Reliable**: Includes verification and error handling
✅ **Flexible**: Can be run standalone or integrated
✅ **Non-disruptive**: Cleanup failures don't stop ingestion

## Configuration

The cleanup utility uses the same Neo4j connection settings as the main application:

```bash
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
```

## Monitoring

The cleanup process provides detailed logging:

```
INFO:__main__:🧹 Step 2: Running Entity label cleanup...
INFO:__main__:Found 21 nodes with Entity labels to clean up
INFO:cleanup_entity_labels:Removing Entity label from Person nodes...
INFO:cleanup_entity_labels:✅ Fixed 11 Person nodes
INFO:cleanup_entity_labels:Removing Entity label from Company nodes...
INFO:cleanup_entity_labels:✅ Fixed 10 Company nodes
INFO:__main__:✅ Cleanup complete: 21 nodes fixed
```

## Result

After implementing this solution:
- ✅ All existing nodes now have only specific labels (`["Person"]`, `["Company"]`)
- ✅ New document ingestion automatically cleans up any Entity labels
- ✅ The system maintains clean, consistent node labeling
- ✅ No manual intervention required

The solution ensures that your Neo4j database maintains the preferred labeling scheme where nodes have only specific labels like "Person" and "Company" without the generic "Entity" label.
