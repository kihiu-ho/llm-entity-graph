# Node Types in the Neo4j Knowledge Graph

This document describes the structured node types defined in the Neo4j database, focusing on Person and Company nodes.

## Overview

The Neo4j knowledge graph supports two primary node types with rich metadata and relationships:

- **Person Node**: Individuals with professional and personal information
- **Company Node**: Organizations with business and corporate information
- **Relationships**: Typed connections between nodes

## Neo4j Node Type Definitions

### Person Node Type

The `Person` node type is defined in Neo4j with the following structure and constraints:

#### Neo4j Schema Definition
```cypher
// Create Person node type with unique constraint
CREATE CONSTRAINT person_name_unique IF NOT EXISTS
FOR (p:Person) REQUIRE p.name IS UNIQUE;

// Create indexes for efficient querying
CREATE INDEX person_full_name_index IF NOT EXISTS
FOR (p:Person) ON (p.full_name);

CREATE INDEX person_current_company_index IF NOT EXISTS
FOR (p:Person) ON (p.current_company);

CREATE INDEX person_current_position_index IF NOT EXISTS
FOR (p:Person) ON (p.current_position);

CREATE INDEX person_type_index IF NOT EXISTS
FOR (p:Person) ON (p.person_type);
```

#### Person Node Properties

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `name` | String | Yes | Person's name (unique identifier) |
| `person_type` | String | No | Type of person (executive, director, employee, etc.) |
| `full_name` | String | No | Full legal name |
| `current_company` | String | No | Current employer |
| `current_position` | String | No | Current job title |
| `email` | String | No | Email address |
| `phone` | String | No | Phone number |
| `linkedin` | String | No | LinkedIn profile URL |
| `nationality` | String | No | Nationality |
| `education` | List[String] | No | Educational background |
| `skills` | List[String] | No | Professional skills |
| `languages` | List[String] | No | Languages spoken |
| `aliases` | List[String] | No | Alternative names |
| `created_at` | DateTime | Auto | Node creation timestamp |
| `updated_at` | DateTime | Auto | Node last update timestamp |

#### Creating Person Nodes

```cypher
// Create a Person node
CREATE (p:Person {
    name: "John Smith",
    person_type: "executive",
    full_name: "John Michael Smith",
    current_company: "TechCorp Inc",
    current_position: "Chief Technology Officer",
    email: "john.smith@techcorp.com",
    education: ["MIT Computer Science", "Stanford MBA"],
    skills: ["Python", "Machine Learning", "Leadership"],
    aliases: ["John M. Smith", "J. Smith"],
    created_at: datetime(),
    updated_at: datetime()
})
```

#### Person Types
- `EXECUTIVE`: C-level executives and senior leadership
- `DIRECTOR`: Board members and directors
- `EMPLOYEE`: Regular employees
- `CONSULTANT`: External consultants
- `INVESTOR`: Investors and stakeholders
- `OTHER`: Other types of individuals

#### Key Attributes
- **Basic Info**: name, full_name, aliases, description
- **Contact**: email, phone, linkedin
- **Professional**: current_company, current_position, title
- **Background**: education, skills, languages, nationality
- **Relationships**: reports_to, direct_reports, colleagues

### Company Node Type

The `Company` node type is defined in Neo4j with the following structure and constraints:

#### Neo4j Schema Definition
```cypher
// Create Company node type with unique constraint
CREATE CONSTRAINT company_name_unique IF NOT EXISTS
FOR (c:Company) REQUIRE c.name IS UNIQUE;

// Create indexes for efficient querying
CREATE INDEX company_legal_name_index IF NOT EXISTS
FOR (c:Company) ON (c.legal_name);

CREATE INDEX company_ticker_symbol_index IF NOT EXISTS
FOR (c:Company) ON (c.ticker_symbol);

CREATE INDEX company_industry_index IF NOT EXISTS
FOR (c:Company) ON (c.industry);

CREATE INDEX company_headquarters_index IF NOT EXISTS
FOR (c:Company) ON (c.headquarters);

CREATE INDEX company_type_index IF NOT EXISTS
FOR (c:Company) ON (c.company_type);
```

#### Company Node Properties

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `name` | String | Yes | Company name (unique identifier) |
| `company_type` | String | No | Type of company (public, private, subsidiary, etc.) |
| `legal_name` | String | No | Legal company name |
| `trading_name` | String | No | Trading/brand name |
| `ticker_symbol` | String | No | Stock ticker symbol |
| `exchange` | String | No | Stock exchange |
| `registration_number` | String | No | Company registration number |
| `tax_id` | String | No | Tax identification number |
| `website` | String | No | Company website |
| `email` | String | No | Contact email |
| `phone` | String | No | Contact phone |
| `headquarters` | String | No | Headquarters location |
| `incorporation_country` | String | No | Country of incorporation |
| `industry` | String | No | Primary industry |
| `sectors` | List[String] | No | Business sectors |
| `products` | List[String] | No | Products/services |
| `founded_date` | Date | No | Date founded |
| `employee_count` | Integer | No | Number of employees |
| `annual_revenue` | Float | No | Annual revenue |
| `market_cap` | Float | No | Market capitalization |
| `key_executives` | List[String] | No | Key executives |
| `aliases` | List[String] | No | Alternative names |
| `created_at` | DateTime | Auto | Node creation timestamp |
| `updated_at` | DateTime | Auto | Node last update timestamp |

#### Creating Company Nodes

```cypher
// Create a Company node
CREATE (c:Company {
    name: "TechCorp Inc",
    company_type: "public",
    legal_name: "TechCorp Incorporated",
    industry: "Technology",
    headquarters: "San Francisco, CA",
    website: "https://techcorp.com",
    ticker_symbol: "TECH",
    products: ["AI Software", "Cloud Services"],
    key_executives: ["John Smith", "Jane Doe"],
    employee_count: 5000,
    created_at: datetime(),
    updated_at: datetime()
})
```

#### Company Types
- `PUBLIC`: Publicly traded companies
- `PRIVATE`: Private companies
- `SUBSIDIARY`: Subsidiary companies
- `PARTNERSHIP`: Partnerships
- `NON_PROFIT`: Non-profit organizations
- `GOVERNMENT`: Government entities
- `OTHER`: Other types of organizations

#### Key Attributes
- **Basic Info**: name, legal_name, trading_name, aliases
- **Business**: industry, sectors, products, technologies
- **Location**: headquarters, incorporation_country, addresses
- **Financial**: ticker_symbol, market_cap, annual_revenue
- **Structure**: parent_company, subsidiaries, partnerships
- **Personnel**: ceo, cfo, cto, board_members, key_executives

### Relationships in Neo4j

Relationships connect nodes and define their interactions with typed relationships:

#### Neo4j Relationship Schema
```cypher
// Create indexes for relationship properties
CREATE INDEX relationship_type_index IF NOT EXISTS
FOR ()-[r]-() ON (r.relationship_type);

CREATE INDEX relationship_start_date_index IF NOT EXISTS
FOR ()-[r]-() ON (r.start_date);

CREATE INDEX relationship_strength_index IF NOT EXISTS
FOR ()-[r]-() ON (r.strength);
```

#### Relationship Properties

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `relationship_type` | String | Yes | Specific type of relationship |
| `description` | String | No | Relationship description |
| `strength` | Float | No | Relationship strength (0.0-1.0) |
| `start_date` | Date | No | Relationship start date |
| `end_date` | Date | No | Relationship end date |
| `is_active` | Boolean | No | Is relationship currently active |
| `created_at` | DateTime | Auto | Relationship creation timestamp |
| `updated_at` | DateTime | Auto | Relationship last update timestamp |

#### Creating Relationships

```cypher
// Create a relationship between Person and Company
MATCH (p:Person {name: "John Smith"})
MATCH (c:Company {name: "TechCorp Inc"})
CREATE (p)-[r:RELATED {
    relationship_type: "Executive_OF",
    description: "John Smith is the CTO of TechCorp Inc",
    strength: 0.9,
    start_date: date("2020-01-15"),
    is_active: true,
    created_at: datetime(),
    updated_at: datetime()
}]->(c)
```

#### Specific Relationship Types

**Person-to-Person Relationships:**
- `Related_TO`: General relationship between individuals
- `Provided_Fund_FOR`: One person provided funding to another
- `Provided_Guarantees_FOR`: One person provided guarantees for another
- `Had_Transactions_WITH`: Business or financial transactions between individuals

**Person-to-Company Relationships:**
- `Company_Secretary_OF`: Person serves as company secretary
- `Executive_OF`: Person holds executive position
- `Shareholder_OF`: Person owns shares in the company
- `Chairman_AND_President_AND_Executive_Director_OF`: Combined senior leadership role
- `ViceChairperson_AND_Non_Executive_Director_OF`: Combined vice chair and director role
- `Executive_Director_OF`: Person serves as executive director
- `Non_Executive_Director_OF`: Person serves as non-executive director
- `Independent_Non_Executive_Director_OF`: Person serves as independent director

**Company-to-Company Relationships:**
- `Shareholder_OF`: Company owns shares in another company
- `List_Bonds_ON`: Company has bonds listed on an exchange
- `Subsidiary_OF`: Company is a subsidiary of another
- `Agented_BY`: Company is represented by an agent
- `Underwriter_OF`: Company underwrites another's securities
- `Provided_Guarantee_TO`: Company provided guarantee to another
- `Had_Purchase_Agreement_WITH`: Purchase agreement between companies
- `Had_Equity_Transfer_Agreement_WITH`: Equity transfer agreement
- `Had_Loan_Transfer_Agreement_WITH`: Loan transfer agreement
- `Had_Facility_Agreement_WITH`: Facility or service agreement

#### Relationship Categories

The system provides helper methods to categorize relationships:

```python
# Check relationship type
relationship = Relationship(
    source_entity_id="John Smith",
    target_entity_id="TechCorp",
    relationship_type=RelationshipType.EXECUTIVE_DIRECTOR_OF
)

# Category checks
print(relationship.is_governance_relationship())  # True
print(relationship.is_financial_relationship())   # False
print(relationship.is_person_to_company())       # True
```

**Financial Relationships:** Include funding, guarantees, transactions, shareholding, bonds, underwriting, and various agreements.

**Governance Relationships:** Include all director positions, company secretary roles, and executive positions.

**Operational Relationships:** Include subsidiary relationships, agency arrangements, and facility agreements.

## Usage Examples

### Working with Neo4j Nodes

#### Adding Nodes to the Graph

```python
from agent.neo4j_schema import create_neo4j_schema_manager

# Initialize schema manager
schema_manager = create_neo4j_schema_manager(
    uri="bolt://localhost:7687",
    username="neo4j",
    password="password"
)

# Add a person node
person_id = schema_manager.create_person_node(
    name="Alice Johnson",
    person_type="executive",
    current_company="DataCorp",
    current_position="CEO",
    email="alice@datacorp.com"
)

# Add a company node
company_id = schema_manager.create_company_node(
    name="DataCorp",
    company_type="private",
    industry="Data Analytics",
    headquarters="New York, NY",
    website="https://datacorp.com"
)
```

#### Direct Neo4j Queries

```cypher
// Add a Person node
CREATE (p:Person {
    name: "Alice Johnson",
    person_type: "executive",
    current_company: "DataCorp",
    current_position: "CEO",
    email: "alice@datacorp.com",
    created_at: datetime()
})

// Add a Company node
CREATE (c:Company {
    name: "DataCorp",
    company_type: "private",
    industry: "Data Analytics",
    headquarters: "New York, NY",
    website: "https://datacorp.com",
    created_at: datetime()
})
```

### Searching Nodes

#### Using Python API

```python
# Search for person nodes
people = schema_manager.search_person_nodes(
    name_query="Alice",
    company="DataCorp",
    position="CEO"
)

# Search for company nodes
companies = schema_manager.search_company_nodes(
    name_query="DataCorp",
    industry="Technology",
    location="New York"
)
```

#### Using Neo4j Queries

```cypher
// Search for Person nodes
MATCH (p:Person)
WHERE p.name CONTAINS "Alice"
  AND p.current_company CONTAINS "DataCorp"
  AND p.current_position CONTAINS "CEO"
RETURN p
LIMIT 10;

// Search for Company nodes
MATCH (c:Company)
WHERE c.name CONTAINS "DataCorp"
  AND c.industry CONTAINS "Technology"
  AND c.headquarters CONTAINS "New York"
RETURN c
LIMIT 10;

// Get all Person nodes
MATCH (p:Person)
RETURN p.name, p.current_company, p.current_position
ORDER BY p.name;

// Get all Company nodes
MATCH (c:Company)
RETURN c.name, c.industry, c.headquarters
ORDER BY c.name;
```

## Neo4j Schema Initialization

### Setting Up the Schema

Before using the Person and Company node types, initialize the Neo4j schema:

```python
from agent.neo4j_schema import create_neo4j_schema_manager

# Create schema manager
schema_manager = create_neo4j_schema_manager(
    uri="bolt://localhost:7687",
    username="neo4j",
    password="your_password"
)

# Initialize the complete schema
schema_manager.initialize_schema()

# This creates:
# - Person node type with constraints and indexes
# - Company node type with constraints and indexes
# - Relationship indexes
```

### Manual Schema Setup

You can also set up the schema manually using Cypher queries:

```cypher
// Person node constraints and indexes
CREATE CONSTRAINT person_name_unique IF NOT EXISTS
FOR (p:Person) REQUIRE p.name IS UNIQUE;

CREATE INDEX person_full_name_index IF NOT EXISTS
FOR (p:Person) ON (p.full_name);

CREATE INDEX person_current_company_index IF NOT EXISTS
FOR (p:Person) ON (p.current_company);

CREATE INDEX person_current_position_index IF NOT EXISTS
FOR (p:Person) ON (p.current_position);

CREATE INDEX person_type_index IF NOT EXISTS
FOR (p:Person) ON (p.person_type);

// Company node constraints and indexes
CREATE CONSTRAINT company_name_unique IF NOT EXISTS
FOR (c:Company) REQUIRE c.name IS UNIQUE;

CREATE INDEX company_legal_name_index IF NOT EXISTS
FOR (c:Company) ON (c.legal_name);

CREATE INDEX company_ticker_symbol_index IF NOT EXISTS
FOR (c:Company) ON (c.ticker_symbol);

CREATE INDEX company_industry_index IF NOT EXISTS
FOR (c:Company) ON (c.industry);

CREATE INDEX company_headquarters_index IF NOT EXISTS
FOR (c:Company) ON (c.headquarters);

CREATE INDEX company_type_index IF NOT EXISTS
FOR (c:Company) ON (c.company_type);

// Relationship indexes
CREATE INDEX relationship_type_index IF NOT EXISTS
FOR ()-[r]-() ON (r.relationship_type);

CREATE INDEX relationship_start_date_index IF NOT EXISTS
FOR ()-[r]-() ON (r.start_date);

CREATE INDEX relationship_strength_index IF NOT EXISTS
FOR ()-[r]-() ON (r.strength);
```

### Getting Relationships

#### Using Python API

```python
# Create relationships
schema_manager.create_relationship(
    source_node_name="Alice Johnson",
    source_node_type="Person",
    target_node_name="DataCorp",
    target_node_type="Company",
    relationship_type="Executive_OF",
    description="Alice Johnson is CEO of DataCorp",
    strength=1.0,
    is_active=True
)
```

#### Using Neo4j Queries

```cypher
// Create relationships between Person and Company
MATCH (p:Person {name: "Alice Johnson"})
MATCH (c:Company {name: "DataCorp"})
CREATE (p)-[r:RELATED {
    relationship_type: "Executive_OF",
    description: "Alice Johnson is CEO of DataCorp",
    strength: 1.0,
    is_active: true,
    created_at: datetime()
}]->(c);

// Get all relationships for a person
MATCH (p:Person {name: "Alice Johnson"})-[r]->(target)
RETURN p.name, r.relationship_type, target.name, labels(target)[0] as target_type;

// Get all relationships for a company
MATCH (source)-[r]->(c:Company {name: "DataCorp"})
RETURN source.name, r.relationship_type, c.name, labels(source)[0] as source_type;

// Find all executives
MATCH (p:Person)-[r:RELATED]->(c:Company)
WHERE r.relationship_type CONTAINS "Executive"
RETURN p.name, r.relationship_type, c.name;

// Find all people in a specific company
MATCH (p:Person)-[r:RELATED]->(c:Company {name: "DataCorp"})
RETURN p.name, p.current_position, r.relationship_type;
```

## Integration with Document Processing

The entity types integrate seamlessly with the document ingestion pipeline:

1. **Entity Extraction**: During document processing, entities are extracted and converted to structured types
2. **Graph Storage**: Entities are stored in the knowledge graph with full metadata
3. **Search and Retrieval**: Entities can be searched and retrieved using the agent tools
4. **Relationship Discovery**: Relationships between entities are automatically discovered and stored

### Example Integration

```python
# In your document processing pipeline
from agent.entity_models import Person, Company, EntityGraph

def process_document(text: str, document_id: str):
    # Extract entities (using NLP/LLM)
    entities = extract_entities_from_text(text)
    
    # Create structured entities
    graph = EntityGraph()
    
    for entity_data in entities:
        if entity_data['type'] == 'person':
            person = Person(
                name=entity_data['name'],
                person_type=PersonType.EXECUTIVE,
                current_company=entity_data.get('company'),
                current_position=entity_data.get('position')
            )
            graph.add_entity(person)
    
    # Add to knowledge graph
    for entity in graph.entities:
        if isinstance(entity, Person):
            await add_person_to_graph(
                name=entity.name,
                person_type=entity.person_type,
                current_company=entity.current_company,
                source_document=document_id
            )
```

## Benefits

1. **Structured Data**: Rich, structured representation of entities
2. **Type Safety**: Pydantic models ensure data validation
3. **Relationship Modeling**: Explicit relationship types and metadata
4. **Search Capabilities**: Advanced search and filtering options
5. **Integration**: Seamless integration with existing pipeline
6. **Extensibility**: Easy to add new entity types and attributes

## Testing

Run the test scripts to see the entity types in action:

```bash
# Test entity models and basic operations
python test_entities.py

# Run comprehensive example
python examples/entity_extraction_example.py
```

## Next Steps

1. **Enhanced Extraction**: Improve entity extraction using advanced NLP models
2. **Additional Types**: Add more entity types (Location, Technology, etc.)
3. **Relationship Inference**: Automatically infer relationships from text
4. **Validation**: Add more sophisticated validation rules
5. **Visualization**: Create tools to visualize the entity graph
