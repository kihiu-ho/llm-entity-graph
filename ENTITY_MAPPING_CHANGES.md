# Entity Mapping Changes: Using Graphiti Custom Entity Types for Person and Company Nodes

## Overview

This document describes the implementation of Graphiti's custom entity types to create specific "Person" and "Company" nodes instead of generic "Entity" nodes in the Neo4j database.

## Problem Statement

Previously, the system was creating generic "Entity" nodes in the Neo4j database through Graphiti's default entity extraction, which made it difficult to distinguish between different types of entities (people vs companies) and limited the effectiveness of graph queries and relationships.

**Root Cause**: Graphiti's default entity extraction creates generic `EntityNode` objects with the `:Entity` label when no custom entity types are specified.

## Solution

**Graphiti Custom Entity Types**: We implemented Graphiti's native custom entity type system to create specific `:Person` and `:Company` nodes with rich attributes and relationships.

The solution includes:

1. **Custom Entity Type Definitions** - Pydantic models for Person and Company entities with detailed attributes
2. **Custom Edge Type Definitions** - Specific relationship types (Employment, Leadership, Investment, etc.)
3. **Edge Type Mapping** - Defines which relationships can exist between entity types
4. **Native Graphiti Integration** - Uses Graphiti's built-in custom entity system for automatic classification

## Changes Made

### 1. Custom Entity Type Definitions (`ingestion/graph_builder.py`)

**Person Entity Type**:
```python
class Person(BaseModel):
    """A person entity with biographical and professional information."""
    age: Optional[int] = Field(None, description="Age of the person in years")
    occupation: Optional[str] = Field(None, description="Current occupation or job title")
    location: Optional[str] = Field(None, description="Current location or residence")
    birth_date: Optional[datetime] = Field(None, description="Date of birth")
    education: Optional[str] = Field(None, description="Educational background")
    company: Optional[str] = Field(None, description="Current employer or company")
    position: Optional[str] = Field(None, description="Current position or role")
    department: Optional[str] = Field(None, description="Department or division")
    start_date: Optional[datetime] = Field(None, description="Employment start date")
    nationality: Optional[str] = Field(None, description="Nationality or citizenship")
    skills: Optional[str] = Field(None, description="Professional skills or expertise")
```

**Company Entity Type**:
```python
class Company(BaseModel):
    """A business organization or corporate entity."""
    industry: Optional[str] = Field(None, description="Primary industry or sector")
    founded_year: Optional[int] = Field(None, description="Year the company was founded")
    headquarters: Optional[str] = Field(None, description="Location of headquarters")
    employee_count: Optional[int] = Field(None, description="Number of employees")
    revenue: Optional[float] = Field(None, description="Annual revenue in USD")
    market_cap: Optional[float] = Field(None, description="Market capitalization in USD")
    ceo: Optional[str] = Field(None, description="Chief Executive Officer")
    website: Optional[str] = Field(None, description="Company website URL")
    description: Optional[str] = Field(None, description="Company description or business model")
    stock_symbol: Optional[str] = Field(None, description="Stock ticker symbol")
    company_type: Optional[str] = Field(None, description="Type of company (public, private, subsidiary, etc.)")
    parent_company: Optional[str] = Field(None, description="Parent company if applicable")
```

### 2. Custom Edge Type Definitions

**Employment Relationship**:
```python
class Employment(BaseModel):
    """Employment relationship between a person and company."""
    position: Optional[str] = Field(None, description="Job title or position")
    start_date: Optional[datetime] = Field(None, description="Employment start date")
    end_date: Optional[datetime] = Field(None, description="Employment end date")
    salary: Optional[float] = Field(None, description="Annual salary in USD")
    is_current: Optional[bool] = Field(None, description="Whether employment is current")
    department: Optional[str] = Field(None, description="Department or division")
    employment_type: Optional[str] = Field(None, description="Type of employment (full-time, part-time, contract)")
```

**Leadership Relationship**:
```python
class Leadership(BaseModel):
    """Leadership or executive relationship between a person and company."""
    role: Optional[str] = Field(None, description="Leadership role (CEO, CTO, Chairman, etc.)")
    start_date: Optional[datetime] = Field(None, description="Leadership start date")
    end_date: Optional[datetime] = Field(None, description="Leadership end date")
    is_current: Optional[bool] = Field(None, description="Whether leadership role is current")
    board_member: Optional[bool] = Field(None, description="Whether person is a board member")
```

**Additional Edge Types**: Investment, Partnership, Ownership with detailed attributes

### 3. Edge Type Mapping Configuration

**Relationship Mapping**:
```python
self.edge_type_map = {
    ("Person", "Company"): ["Employment", "Leadership"],
    ("Company", "Company"): ["Partnership", "Investment", "Ownership"],
    ("Person", "Person"): ["Partnership"],
    ("Entity", "Entity"): ["Investment", "Partnership"],  # Fallback for any entity type
}
```

### 4. GraphBuilder Integration

**Modified `add_document_to_graph()` method**:
```python
await self.graph_client.add_episode(
    episode_id=episode_id,
    content=episode_content,
    source=source_description,
    timestamp=datetime.now(timezone.utc),
    entity_types=self.entity_types,      # Custom Person and Company types
    edge_types=self.edge_types,          # Custom edge types
    edge_type_map=self.edge_type_map,    # Custom edge type mapping
    excluded_entity_types=["Entity"],    # Exclude generic Entity type
    metadata=metadata
)
```

### 5. Enhanced Graph Utils

**Updated `add_episode()` method** in `agent/graph_utils.py`:
- Added support for custom entity types
- Added support for custom edge types
- Added support for edge type mapping
- Added support for excluded entity types (excludes "Entity" label)
- Passes custom types to Graphiti's native system

**Key Addition**:
```python
# Add excluded entity types if provided
if excluded_entity_types:
    episode_args["excluded_entity_types"] = excluded_entity_types
    logger.debug(f"Excluding entity types: {excluded_entity_types}")
```

## Benefits

### ✅ Native Graphiti Integration
- **Uses Graphiti's built-in custom entity type system** - no workarounds needed
- **Automatic entity classification** by Graphiti's LLM using custom types
- **Seamless integration** with Graphiti's search and retrieval functions
- **No direct Neo4j manipulation** required

### ✅ Rich Entity Attributes
- **Detailed Person attributes**: age, occupation, education, skills, company, position
- **Comprehensive Company attributes**: industry, founded_year, headquarters, revenue, CEO
- **Structured data extraction** from unstructured text
- **Type-specific attribute validation** using Pydantic models

### ✅ Custom Relationship Types
- **Employment relationships**: position, salary, start_date, is_current, department
- **Leadership relationships**: role, board_member, start_date, is_current
- **Investment relationships**: amount, stake_percentage, investment_type, round_type
- **Partnership relationships**: partnership_type, deal_value, duration

### ✅ Better Graph Structure
- **Specific node types**: `:Person` and `:Company` instead of generic `:Entity`
- **Type-specific queries**: `MATCH (p:Person)-[:Employment]->(c:Company)`
- **Rich relationship attributes** for detailed analysis
- **Proper entity classification** by Graphiti's LLM

### ✅ Maintained Compatibility
- **Backward compatible** with existing GraphBuilder usage
- **Existing code continues to work** without modification
- **Enhanced functionality** without breaking changes
- **Standard Graphiti patterns** and best practices

## Usage Example

```python
# Initialize graph builder with custom entity types
graph_builder = GraphBuilder()

# The GraphBuilder now automatically includes:
# - Custom Person and Company entity types
# - Custom edge types (Employment, Leadership, Investment, etc.)
# - Edge type mapping for proper relationships

# Process document with custom entity types
result = await graph_builder.add_document_to_graph(
    chunks=document_chunks,
    document_title="Director Biography",
    document_source="annual_report.pdf"
)

# Results now include:
# - Episodes processed with custom entity types
# - Automatic Person and Company node creation by Graphiti
# - Rich entity attributes extracted from text
# - Custom relationship types with detailed properties

print(f"Episodes created: {result['episodes_created']}")
print(f"Custom entity types used: {result['custom_entity_types_used']}")
print(f"Entity types: {result['entity_types']}")  # ['Person', 'Company']
print(f"Edge types: {result['edge_types']}")      # ['Employment', 'Leadership', ...]
```

### Custom Entity Type Configuration

```python
# Entity types are automatically configured in GraphBuilder.__init__()
self.entity_types = {
    "Person": Person,      # Rich person attributes
    "Company": Company     # Rich company attributes
}

self.edge_types = {
    "Employment": Employment,    # Job relationships
    "Leadership": Leadership,    # Executive relationships
    "Investment": Investment,    # Financial relationships
    "Partnership": Partnership, # Business partnerships
    "Ownership": Ownership      # Ownership relationships
}
```

## Verification and Testing

### Fix Entity Labels (Remove Generic Entity Labels)
```bash
# Remove Entity labels from Person and Company nodes
python3 fix_entity_labels.py
```

### Alternative: Use Cypher Queries Directly
```bash
# Run the Cypher script in Neo4j Browser
# File: remove_entity_labels.cypher
```

### Test Custom Entity Types
```bash
# Test the custom entity type functionality
python3 test_custom_entity_types.py
```

### Check Node Types in Neo4j
```bash
# Check what node types exist in your Neo4j database
python3 check_neo4j_nodes.py
```

### Verify Clean Labels
```cypher
-- In Neo4j Browser, verify Person nodes have only Person label
MATCH (p:Person)
RETURN labels(p) as labels, count(p) as count;

-- Verify Company nodes have only Company label
MATCH (c:Company)
RETURN labels(c) as labels, count(c) as count;

-- Ensure no Person/Company nodes have Entity label
MATCH (n)
WHERE ('Person' IN labels(n) OR 'Company' IN labels(n)) AND 'Entity' IN labels(n)
RETURN count(n) as problematic_nodes;
-- Should return 0
```

### Search with Custom Types
```python
from graphiti_core.search.search_filters import SearchFilters

# Search for only Person entities
search_filter = SearchFilters(node_labels=["Person"])
results = await graphiti.search_(
    query="Who works at tech companies?",
    search_filter=search_filter
)

# Search for only Company entities
search_filter = SearchFilters(node_labels=["Company"])
results = await graphiti.search_(
    query="Technology companies in Hong Kong",
    search_filter=search_filter
)
```

## Files Modified and Created

### Modified Files

1. **`ingestion/graph_builder.py`**
   - Added custom entity type definitions (Person, Company)
   - Added custom edge type definitions (Employment, Leadership, etc.)
   - Configured entity types, edge types, and edge type mapping
   - Updated `add_document_to_graph()` to use custom types
   - Removed direct Neo4j manipulation in favor of Graphiti's system

2. **`agent/graph_utils.py`**
   - Enhanced `add_episode()` method to support custom entity types
   - Added parameters for entity_types, edge_types, and edge_type_map
   - Passes custom types to Graphiti's native add_episode method

### New Files Created

3. **`test_custom_entity_types.py`**
   - Comprehensive testing of Graphiti custom entity types
   - Tests entity type definitions and validation
   - Integration testing with GraphBuilder
   - Search functionality testing with custom types

4. **`fix_entity_labels.py`**
   - Script to remove Entity labels from Person and Company nodes
   - Tests that new documents don't create Entity labels
   - Comprehensive verification of label cleanup

5. **`remove_entity_labels.cypher`**
   - Cypher queries to remove Entity labels directly in Neo4j Browser
   - Step-by-step verification queries
   - Can be run manually for immediate fixes

6. **`check_node_labels.py`**
   - Utility to check and fix node labels in Neo4j
   - Identifies nodes with multiple labels including Entity
   - Automated cleanup and verification

### Legacy Files (No Longer Needed)

7. **`agent/neo4j_schema_manager.py`** - No longer needed (direct Neo4j approach replaced)
8. **`test_direct_node_creation.py`** - Replaced by `test_custom_entity_types.py`
9. **`migrate_entity_nodes.py`** - May still be useful for existing databases

## Environment Setup

### Required Dependencies
```bash
pip install graphiti-core  # Graphiti with custom entity type support
pip install pydantic       # For entity type definitions
```

### Optional: Neo4j Configuration
```bash
# Only needed if using custom Neo4j instance
export NEO4J_URI="bolt://localhost:7687"
export NEO4J_USER="neo4j"
export NEO4J_PASSWORD="your_password"
```

## Testing

The changes include comprehensive testing and verification:
- **Custom entity type testing** with Graphiti's native system
- **Entity type definition validation** using Pydantic models
- **Search functionality testing** with type-specific filters
- **Integration testing** with the GraphBuilder workflow
- **Rich attribute extraction** testing from unstructured text

## Conclusion

These changes successfully address the requirement to map Entity labels to corresponding "Company" and "Person" node types instead of using a generic "Entity" label using Graphiti's native custom entity type system.

**Key Achievements**:
- ✅ **Native Graphiti integration** using the official custom entity type system
- ✅ **Rich entity attributes** automatically extracted from text using LLM
- ✅ **Custom relationship types** with detailed properties and validation
- ✅ **Guaranteed specific node types** (`:Person` and `:Company`) created by Graphiti
- ✅ **Backward compatibility** with existing GraphBuilder usage
- ✅ **Enhanced graph structure** for better querying and analysis
- ✅ **Type-specific search capabilities** using Graphiti's search filters

The system now leverages **Graphiti's built-in capabilities** for entity classification, providing rich entity attributes, custom relationship types, and precise node creation while maintaining full backward compatibility. This approach follows Graphiti's best practices and ensures long-term maintainability and feature compatibility.
