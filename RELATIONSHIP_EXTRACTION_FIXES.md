# Relationship Extraction Fixes

## Problem
The agent tools in `agent.py` were failing to extract relationships from graph search because they were not consistent with the format used during ingestion. The relationship extraction logic was not properly handling the exact format that Graphiti uses to store relationship episodes.

## Root Cause
During ingestion, relationships are stored in Graphiti using specific formats:

1. **Direct relationships**: `"Relationship: source_entity relationship_type target_entity"`
2. **Entity facts**: `"PERSON: name"` or `"COMPANY: name"` with structured attributes
3. **Natural language**: Graphiti's LLM processes episodes and may create various natural language formats

However, the agent tools were using generic extraction patterns that didn't match these specific formats.

## Solution

### 1. Created Ingestion-Specific Extraction Function
- **New function**: `_extract_relationships_from_graphiti_fact()`
- **Purpose**: Handles the exact format used during ingestion
- **Location**: `agent/tools.py`

### 2. Enhanced Relationship Line Parsing
- **New function**: `_parse_ingestion_relationship_line()`
- **Purpose**: Parses relationship lines in the exact format: "source relationship_type target"
- **Handles**: Relationship types with underscores (e.g., "Executive_OF", "Employee_OF")

### 3. Improved Search Strategy
- **Enhanced function**: `get_enhanced_entity_relationships()`
- **Multiple search queries**: Uses various query patterns to find relationships
- **Better deduplication**: Removes duplicate relationships more effectively
- **Comprehensive coverage**: Searches for both direct relationships and entity facts

### 4. Updated Agent Tools
- **Modified**: `get_entity_relationships_tool()` in `agent/tools.py`
- **Modified**: `graph_search()` tool in `agent.py`
- **Added**: Better logging and debugging information
- **Added**: Debug information when no relationships are found

### 5. Consistent Extraction Across Modules
- **Updated**: `graph_utils.py` to use the same extraction logic
- **Ensures**: Consistency between different parts of the system

## Key Changes Made

### agent/tools.py
1. **New extraction function** that specifically handles ingestion format
2. **Enhanced search queries** that match how relationships are stored
3. **Better error handling** and logging
4. **Improved deduplication** logic

### agent/agent.py
1. **Updated graph search tool** to use new extraction function
2. **Added relationship type summaries** in search results
3. **Better debugging information** for relationship extraction

### agent/graph_utils.py
1. **Updated to use consistent extraction** logic from tools module
2. **Fallback implementation** if import fails

## Supported Relationship Formats

### 1. Direct Relationship Format (from ingestion)
```
Relationship: John Chen Executive_OF TechCorp Holdings
Description: John Chen serves as Executive Director
Strength: 1.0
Active: True
```

### 2. Structured Entity Format (from ingestion)
```
PERSON: Sarah Chen
Entity Type: Person
Current company: TechCorp Inc
Current position: CEO
```

### 3. Company Entity Format (from ingestion)
```
COMPANY: DataFlow Systems
Entity Type: Company
Key executives: Michael Wong, Lisa Tan
Industry: Data Analytics
```

### 4. Natural Language Patterns
- Employment relationships: "X works as Y at Z"
- Executive relationships: "X CEO of Y"
- Ownership relationships: "X owns Y"
- Corporate structure: "X subsidiary of Y"

## Testing

### Test Scripts Created
1. **test_ingestion_consistency.py**: Tests extraction with exact ingestion format
2. **test_fixed_relationships.py**: Tests the fixed agent tools
3. **test_relationship_extraction.py**: General relationship extraction testing

### Test Coverage
- Direct relationship format parsing
- Structured entity fact extraction
- Natural language pattern matching
- Agent tool integration
- Graph search tool functionality

## Expected Results

After these fixes, the agent tools should:

1. **Successfully extract relationships** from the knowledge graph
2. **Handle the exact format** used during ingestion
3. **Provide consistent results** across different search methods
4. **Give better debugging information** when relationships are not found
5. **Support all relationship types** defined in the system

## Usage

The fixed tools can be used in the same way as before:

```python
from agent.tools import get_entity_relationships_tool, EntityRelationshipSearchInput

# Search for relationships
input_data = EntityRelationshipSearchInput(
    entity_name="John Chen",
    entity_type="person",
    limit=10
)

relationships = await get_entity_relationships_tool(input_data)
```

The tools will now properly extract relationships that were created during document ingestion.
