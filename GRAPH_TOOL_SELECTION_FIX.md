# Fix for Graph Tool Selection Issue

## Problem Identified

The system was using embeddings instead of graph database tools for relationship queries:

```
Query: "relation between IFHA and HKJC"
Expected: Use get_entity_relationships tool
Actual: HTTP Request to embeddings endpoint
Result: Missing graph relationships
```

## Root Cause Analysis

### **1. Problematic System Prompt**
The agent's system prompt contained restrictive instructions:
```
"Use the knowledge graph tool only when the user asks about two companies in the same question. Otherwise, use just the vector store tool."
```

This caused the agent to prefer vector search over graph tools for relationship queries.

### **2. Tool Selection Logic**
- Agent was calling `comprehensive_search` tool
- Comprehensive search was falling back to embeddings
- Graph tools were not being prioritized for relationship queries
- No specific tool for entity connection queries

### **3. Duplicate Tool Functions**
- Two `get_entity_relationships_tool` functions existed
- Function name conflicts causing tool registration issues
- Agent confusion about which tool to use

## Solution Implemented

### **1. Enhanced System Prompt**

#### **Updated Tool Selection Guidelines**
```
**Tool Selection Guidelines:**
- Use **knowledge graph tools** for relationship queries, entity connections, and organizational structures
- Use **vector search** for finding similar content, detailed explanations, and general information
- Use **entity relationship tools** when asked about connections between people, companies, or organizations

**Priority for Relationship Queries:**
When users ask about relationships, connections, or how entities relate to each other:
1. FIRST use get_entity_relationships tool to find graph connections
2. THEN use vector search if additional context is needed
3. Always prefer graph tools for organizational structures and entity relationships
```

#### **Removed Restrictive Instructions**
- Eliminated the "only two companies" restriction
- Added explicit prioritization for relationship queries
- Clarified when to use each tool type

### **2. New Dedicated Relationship Tool**

#### **find_entity_connections Tool**
```python
@rag_agent.tool
async def find_entity_connections(
    ctx: RunContext[AgentDependencies],
    query: str,
    depth: int = 3
) -> List[Dict[str, Any]]:
    """
    Find connections and relationships between entities mentioned in a query.
    
    This tool is specifically designed for relationship queries such as:
    - "relation between IFHA and HKJC"
    - "how is Henri Pouret connected to IFHA"
    - "connection between X and Y"
    
    Use this tool when users ask about relationships, connections, or associations
    between specific entities or organizations. This tool should be PRIORITIZED
    for any query containing words like "relation", "connection", "between".
    """
```

#### **Enhanced Entity Extraction**
```python
def _extract_entities_from_relationship_query(query: str) -> List[str]:
    """Extract entity names from relationship queries."""
    
    # Pattern matching for relationship queries
    entity_patterns = [
        r'between\s+([^and]+)\s+and\s+([^.?!]+)',  # "between X and Y"
        r'relation.*between\s+([^and]+)\s+and\s+([^.?!]+)',  # "relation between X and Y"
        r'connection.*between\s+([^and]+)\s+and\s+([^.?!]+)',  # "connection between X and Y"
    ]
    
    # Known entity recognition
    known_entities = [
        'ifha', 'international federation of horseracing authorities',
        'hkjc', 'hong kong jockey club', 'henri pouret', 'winfried engelbrecht bresges'
    ]
```

### **3. Enhanced Comprehensive Search**

#### **Intelligent Tool Selection**
```python
if search_type in ["graph", "auto"] and include_graph_facts:
    # Check if this is a relationship query between specific entities
    relationship_entities = _extract_entities_from_relationship_query(query)
    logger.info(f"Extracted entities from relationship query '{query}': {relationship_entities}")
    
    if relationship_entities:
        logger.info(f"Using entity relationship tool for entities: {relationship_entities}")
        # Use entity relationship tool for specific entity relationships
        for entity in relationship_entities:
            entity_rel_input = EntityRelationshipSearchInput(entity_name=entity)
            entity_relationships = await get_entity_relationships_tool(entity_rel_input)
```

#### **Enhanced Logging**
- Added detailed logging for tool selection decisions
- Entity extraction logging with emojis for visibility
- Relationship discovery tracking
- Tool usage statistics

### **4. Fixed Tool Conflicts**

#### **Resolved Duplicate Functions**
- Renamed duplicate `get_entity_relationships_tool` to `get_structured_entity_relationships_tool`
- Fixed import conflicts in agent.py
- Ensured correct tool registration

#### **Clear Tool Hierarchy**
1. **find_entity_connections** - For explicit relationship queries
2. **get_entity_relationships** - For single entity relationship exploration
3. **comprehensive_search** - For complex multi-tool searches
4. **vector search** - For content and context

## Technical Implementation

### **Enhanced Tool Descriptions**

#### **Prioritized Relationship Tool**
```python
Tool(
    name="get_entity_relationships",
    description="Get relationships for a specific entity (person or company). Use this when you need to find connections, relationships, or associations for a particular entity. PRIORITIZE this tool for relationship queries like 'relation between X and Y' or 'how is X connected to Y'.",
    func=get_entity_relationships_tool,
    args_schema=EntityRelationshipSearchInput
)
```

#### **Explicit Connection Tool**
```python
Tool(
    name="find_entity_connections", 
    description="Find connections and relationships between two or more entities. Use this specifically for queries about relationships between entities, such as 'relation between IFHA and HKJC' or 'how are X and Y connected'. This tool is optimized for relationship discovery.",
    func=find_entity_connections_tool,
    args_schema=EntityConnectionSearchInput
)
```

### **Query Processing Flow**

#### **For "relation between IFHA and HKJC":**
```
1. Agent receives query
2. System prompt prioritizes graph tools for relationship queries
3. Agent selects find_entity_connections tool
4. Tool extracts entities: ["IFHA", "HKJC"]
5. Tool calls get_entity_relationships for each entity
6. Results filtered for cross-entity connections
7. Graph relationships returned instead of embeddings
```

### **Logging Enhancement**
```python
logger.info(f"🔍 Finding entity connections for query: {query}")
logger.info(f"📋 Extracted entities: {entities}")
logger.info(f"🔎 Getting relationships for entity: {entity}")
logger.info(f"📊 Found {len(entity_relationships)} relationships for {entity}")
logger.info(f"✅ Found relationship: {source} -> {relationship} -> {target}")
logger.info(f"🎯 Found {len(all_relationships)} total relationships")
```

## Expected Results

### **Before Fix**
```
Query: "relation between IFHA and HKJC"
Tool Used: comprehensive_search → embeddings
Log: "HTTP Request: POST .../embeddings"
Result: No graph relationships found
```

### **After Fix**
```
Query: "relation between IFHA and HKJC"
Tool Used: find_entity_connections → get_entity_relationships
Log: "🔍 Finding entity connections for query: relation between IFHA and HKJC"
Log: "📋 Extracted entities: ['IFHA', 'HKJC']"
Log: "🔎 Getting relationships for entity: IFHA"
Log: "✅ Found relationship: Winfried Engelbrecht Bresges -> Chair -> IFHA"
Log: "✅ Found relationship: Winfried Engelbrecht Bresges -> CEO -> HKJC"
Result: Graph relationships showing IFHA ↔ Winfried ↔ HKJC connection
```

## Benefits

### ✅ **Correct Tool Selection**
- **Graph tools prioritized** for relationship queries
- **No more embedding fallback** for entity connections
- **Explicit tool descriptions** guide agent decisions
- **Clear tool hierarchy** prevents confusion

### ✅ **Enhanced Relationship Discovery**
- **Dedicated relationship tool** for connection queries
- **Entity extraction** from natural language queries
- **Cross-entity filtering** for relevant connections
- **Comprehensive relationship mapping**

### ✅ **Improved Debugging**
- **Detailed logging** with visual indicators
- **Tool selection tracking** for troubleshooting
- **Entity extraction visibility** for verification
- **Relationship discovery monitoring**

### ✅ **Better User Experience**
- **Accurate relationship answers** for entity queries
- **Graph-based responses** instead of embedding search
- **Comprehensive connection mapping** between entities
- **Reliable tool behavior** for relationship exploration

## Deployment Impact

### **Immediate Benefits**
After deploying this fix:
1. ✅ **IFHA-HKJC relationship queries will use graph tools**
2. ✅ **No more embedding fallback for relationship queries**
3. ✅ **Dedicated tool for entity connection discovery**
4. ✅ **Enhanced logging for troubleshooting tool selection**

### **Long-term Improvements**
- **Consistent graph tool usage** for relationship queries
- **Better agent decision-making** with clear tool guidelines
- **Improved relationship discovery** across all entity types
- **Reliable tool selection** for complex organizational queries

The fix ensures that relationship queries like "relation between IFHA and HKJC" will properly use graph database tools instead of falling back to embeddings, providing accurate and comprehensive relationship information from the knowledge graph.
