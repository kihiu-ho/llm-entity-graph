# Enhanced Entity Extraction for Organizational Content

## Overview

Enhanced the entity extraction system to better handle organizational content, particularly web pages and HTML content containing executive information, organizational charts, and member directories. The improvements specifically address cases like the International Federation of Horseracing Authorities (IFHA) organizational structure.

## Key Improvements

### 1. **Enhanced People Extraction**

#### **Improved Recognition Patterns**
- **Organizational hierarchies** (Chair, Vice-Chair, members)
- **Names in HTML/web content** including image alt text and captions
- **Navigation menus and directory listings**
- **Geographic/regional associations** (e.g., "Vice-Chair, Europe")
- **Committee and council structures**
- **Voting rights and representation** contexts

#### **Examples from IFHA Content**
```
Input: "Winfried Engelbrecht Bresges Chair"
Output: "Winfried Engelbrecht Bresges"

Input: "Henri Pouret Vice-Chair, Europe"
Output: "Henri Pouret"

Input: "Brant Dunshea British Horseracing Authority"
Output: "Brant Dunshea"
```

### 2. **Enhanced Company/Organization Extraction**

#### **Expanded Organizational Patterns**
- **International organizations and federations**
- **Regulatory authorities and boards**
- **Racing and sports organizations**
- **Industry associations and clubs**
- **Regional federations**
- **Entertainment and gaming companies**

#### **Examples from IFHA Content**
```
- "International Federation of Horseracing Authorities"
- "British Horseracing Authority"
- "The Hong Kong Jockey Club"
- "France Galop"
- "Horse Racing Ireland"
- "New Zealand Thoroughbred Racing"
```

### 3. **Enhanced Corporate Roles Extraction**

#### **New Organizational Role Categories**
- **Federation leadership**: International federation chairs, vice-chairs, executive council members
- **Regional representatives**: Regional vice-chairs and representatives (Europe, Asia, Americas)
- **Council members**: Executive council members with voting rights and regional representation
- **Rotating members**: Temporary or rotating positions representing specific constituencies
- **Organizational affiliations**: Person-to-organization connections with specific roles

#### **Examples of Role Extraction**
```
- "Winfried Engelbrecht Bresges" as "Chair" of "International Federation of Horseracing Authorities"
- "Henri Pouret" as "Vice-Chair, Europe" representing "France Galop"
- "Masayuki Goto" as "Vice-Chair, Asia" representing "The Japan Racing Association"
- "Jim Gagliano" as "Vice-Chair, Americas" representing "US Jockey Club"
```

### 4. **Enhanced Personal Connections**

#### **New Connection Types**
- **Organizational connections**: Professional relationships through shared organizational membership
- **Federation colleagues**: Connections through international federation or council membership
- **Industry relationships**: Connections within the same industry or sector
- **Regional associations**: Connections through regional representation or geographic proximity

#### **Connection Examples**
```
- "Winfried Engelbrecht Bresges" (HKJC CEO) connected to "Masayuki Goto" (JRA) through IFHA Executive Council
- "Henri Pouret" (France Galop) connected to "Brant Dunshea" (BHA) through European racing collaboration
- Regional vice-chairs connected through geographic representation and shared responsibilities
```

### 5. **HTML/Web Content Preprocessing**

#### **Content Processing Features**
- **HTML tag cleaning** while preserving organizational structure
- **Image alt text extraction** for names and titles
- **Title attribute preservation** for additional context
- **JavaScript and CSS removal** with content preservation
- **HTML entity conversion** for proper text processing
- **Structural element preservation** (headers, lists, tables)

#### **Preprocessing Examples**
```html
Input: <img alt="Winfried Engelbrecht Bresges Chair" src="...">
Processed: [Image: Winfried Engelbrecht Bresges Chair]

Input: <h3>Executive Council</h3><li>Henri Pouret Vice-Chair, Europe</li>
Processed: === Executive Council === • Henri Pouret Vice-Chair, Europe
```

## Technical Implementation

### **Enhanced Prompt Engineering**

#### **Specialized Instructions**
```
PEOPLE: Extract individual person names with enhanced context recognition.
- Extract from: organizational charts, executive lists, member directories, staff listings
- Handle: names in HTML/web content, image alt text, navigation menus
- Examples: "Winfried Engelbrecht Bresges" (from "Winfried Engelbrecht Bresges Chair")
```

#### **Content Type Recognition**
```
CONTENT TYPE RECOGNITION:
- Web pages with organizational information and HTML content
- Executive biographies and leadership pages
- Member directories and council listings
- Corporate governance documents and annual reports
- Navigation menus and organizational charts
- Image alt text and captions with person/organization names
```

### **Preprocessing Pipeline**

#### **HTML Content Processing**
1. **Extract important attributes** (alt text, titles)
2. **Remove scripts and styles** while preserving content
3. **Convert HTML entities** to readable text
4. **Preserve structural elements** with meaningful formatting
5. **Clean whitespace** and normalize text

#### **Organizational Structure Preservation**
- Headers converted to section markers
- List items preserved with bullet points
- Table cells separated with pipe characters
- Member divs specially marked for recognition

## Usage Examples

### **IFHA Organizational Structure**

#### **Input Content**
```html
International Federation of Horseracing Authorities
<img alt="Winfried Engelbrecht Bresges" src="...">
Winfried Engelbrecht Bresges
Chair

<img alt="Henri Pouret" src="...">
Henri Pouret
Vice-Chair, Europe

EUROPE France (1 vote) Great Britain (1 vote) Ireland (1 vote)
Henri Pouret France Galop
Brant Dunshea British Horseracing Authority
```

#### **Expected Extraction Results**
```json
{
  "people": [
    "Winfried Engelbrecht Bresges",
    "Henri Pouret", 
    "Brant Dunshea"
  ],
  "companies": [
    "International Federation of Horseracing Authorities",
    "France Galop",
    "British Horseracing Authority"
  ],
  "corporate_roles": {
    "federation_leadership": [
      "Winfried Engelbrecht Bresges - Chair",
      "Henri Pouret - Vice-Chair, Europe"
    ],
    "regional_representatives": [
      "Henri Pouret - France Galop",
      "Brant Dunshea - British Horseracing Authority"
    ]
  },
  "personal_connections": {
    "organizational_connections": [
      "Winfried Engelbrecht Bresges connected to Henri Pouret through IFHA Executive Council",
      "Henri Pouret connected to Brant Dunshea through European racing collaboration"
    ]
  }
}
```

### **Relationship Queries**

#### **Query**: "How is Masayuki Goto connected to David Sun?"

#### **Expected Answer**:
```
Masayuki Goto is connected to David Sun via Winfried Engelbrecht Bresges.
- Masayuki Goto works with Winfried Engelbrecht Bresges in IFHA (International Federation of Horseracing Authorities)
- David Sun works with Winfried Engelbrecht Bresges in HKJC (The Hong Kong Jockey Club)
- Winfried Engelbrecht Bresges serves as Chair of IFHA and CEO of HKJC, creating the connection
```

## Benefits

### **Improved Accuracy**
- ✅ **Better name recognition** from HTML/web content
- ✅ **Enhanced organizational context** understanding
- ✅ **Improved role and relationship extraction**
- ✅ **Better handling of complex organizational structures**

### **Enhanced Connectivity**
- ✅ **Cross-organizational relationships** properly identified
- ✅ **Regional and industry connections** captured
- ✅ **Federation and council memberships** recognized
- ✅ **Professional networks** mapped effectively

### **Robust Processing**
- ✅ **HTML content handling** without information loss
- ✅ **Structural preservation** for better context
- ✅ **Multi-format support** (web pages, documents, reports)
- ✅ **Scalable extraction** for large organizational datasets

## Configuration

### **Enable Enhanced Extraction**
```python
# Use enhanced entity extraction for organizational content
enriched_chunks = await graph_builder.extract_entities_from_document(
    chunks,
    extract_companies=True,
    extract_people=True,
    extract_corporate_roles=True,
    extract_personal_connections=True,
    use_llm=True,
    use_llm_for_people=True,
    use_llm_for_corporate_roles=True,
    use_llm_for_personal_connections=True
)
```

### **Custom Organizational Roles**
```python
# Customize for specific organization types
custom_config = {
    "federation_leadership": {
        "chair": {"description": "Federation chairperson"},
        "vice_chair": {"description": "Regional vice-chairperson"}
    },
    "regional_representatives": {
        "europe": {"description": "European representative"},
        "asia": {"description": "Asian representative"}
    }
}
graph_builder.customize_corporate_roles_config(custom_config)
```

The enhanced entity extraction system now provides comprehensive support for organizational content, enabling accurate extraction of people, organizations, roles, and relationships from complex web-based and HTML content like the IFHA organizational structure.
