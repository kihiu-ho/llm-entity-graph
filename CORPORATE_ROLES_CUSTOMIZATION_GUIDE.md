# Corporate Roles Customization Guide

## Overview

The corporate roles extraction system has been generalized to support different types of organizations. Instead of being hardcoded for public companies, it now uses configurable templates that can be customized for various organization types.

## Key Benefits

✅ **Flexible Configuration**: Easily customize for different organization types
✅ **Reusable Templates**: Pre-built templates for common organization types
✅ **Consistent Formatting**: Standardized extraction patterns across all types
✅ **Easy Customization**: Simple API to modify or create new configurations

## Available Templates

### 1. Public Company (Default)
- Executive directors, non-executive directors, independent directors
- Chairman, deputy chairman, CEO/COO
- Company secretaries, board committees, auditors
- Management team and alternate directors

### 2. Private Company
- Owners and major shareholders
- Business partners and co-owners
- Management team and advisors

### 3. Non-Profit Organization
- Executive director and program directors
- Board chair and trustees
- Committees and advisory boards

### 4. Startup Company
- Founders with equity stakes
- C-suite executives and VPs
- Investors and board members
- Industry advisors

### 5. Government Agency
- Director and deputy directors
- Division chiefs and program managers
- Inspector General and oversight committees

### 6. Academic Institution
- President, provost, and deans
- Board of trustees/regents
- Faculty senate leadership

## Usage Examples

### Basic Usage (Default Public Company)

```python
from ingestion.graph_builder import GraphBuilder

# Uses default public company configuration
graph_builder = GraphBuilder()

result = await graph_builder.add_document_to_graph(
    chunks=document_chunks,
    document_title="Annual Report",
    document_source="company_report.pdf"
)
```

### Using Pre-built Templates

```python
from ingestion.graph_builder import GraphBuilder
from config.corporate_roles_templates import CorporateRolesTemplates

# Initialize graph builder
graph_builder = GraphBuilder()

# Use a pre-built template
nonprofit_config = CorporateRolesTemplates.get_template("nonprofit")
graph_builder.customize_corporate_roles_config(nonprofit_config)

# Process nonprofit documents
result = await graph_builder.add_document_to_graph(
    chunks=document_chunks,
    document_title="Nonprofit Annual Report",
    document_source="nonprofit_report.pdf"
)
```

### Creating Custom Configuration

```python
from ingestion.graph_builder import GraphBuilder

# Define custom configuration
custom_config = {
    "leadership": {
        "ceo": {
            "description": "Chief Executive Officer with industry experience",
            "format": "**SURNAME** Given Names - Background | CEO (since Date)",
            "examples": ["**SMITH** John Michael - Former Tech Executive | CEO (since 2020)"]
        },
        "founders": {
            "description": "Company founders with equity information",
            "format": "**SURNAME** Given Names - Background | Founder (equity: X%)",
            "examples": ["**CHEN** Lisa Wei - Former Google | Co-Founder (equity: 30%)"]
        }
    },
    "governance": {
        "board_members": {
            "description": "Board of directors with backgrounds",
            "format": "**SURNAME** Given Names - Background | Board Member",
            "examples": ["**WILSON** Jennifer - Former McKinsey | Board Member"]
        }
    }
}

# Apply custom configuration
graph_builder = GraphBuilder()
graph_builder.customize_corporate_roles_config(custom_config)
```

### Multiple Organization Types

```python
from ingestion.graph_builder import GraphBuilder
from config.corporate_roles_templates import CorporateRolesTemplates

async def process_different_org_types():
    # Process public company documents
    graph_builder = GraphBuilder()
    public_config = CorporateRolesTemplates.get_template("public_company")
    graph_builder.customize_corporate_roles_config(public_config)
    
    await graph_builder.add_document_to_graph(
        chunks=public_company_chunks,
        document_title="Public Company Report",
        document_source="public_report.pdf"
    )
    await graph_builder.close()
    
    # Process startup documents
    graph_builder = GraphBuilder()
    startup_config = CorporateRolesTemplates.get_template("startup")
    graph_builder.customize_corporate_roles_config(startup_config)
    
    await graph_builder.add_document_to_graph(
        chunks=startup_chunks,
        document_title="Startup Pitch Deck",
        document_source="pitch_deck.pdf"
    )
    await graph_builder.close()
```

## Configuration Structure

Each configuration follows this structure:

```python
{
    "category_name": {
        "role_name": {
            "description": "Detailed description of the role",
            "format": "**SURNAME** Given Names - Format pattern",
            "examples": ["Example extraction with proper formatting"]
        }
    }
}
```

### Configuration Elements

- **category_name**: Groups related roles (e.g., "executive_roles", "board_roles")
- **role_name**: Specific role type (e.g., "ceo", "chairman", "trustees")
- **description**: What to extract for this role type
- **format**: Expected output format with placeholders
- **examples**: Sample extractions showing the expected format

## Formatting Guidelines

### Standard Format Pattern
```
"**SURNAME** Given Names - Qualifications | Title (additional details)"
```

### Key Formatting Rules

1. **Bold Surnames**: Always use `**SURNAME**` format
2. **Qualifications**: Separate with ` - ` (space-dash-space)
3. **Title Separator**: Use ` | ` (space-pipe-space)
4. **Additional Details**: Include in parentheses
5. **Dates**: Use consistent date formats
6. **Ages**: Include when available: `(aged X)`
7. **Tenure**: Include appointment dates: `(since Date)`

### Examples by Organization Type

**Public Company**:
```
"**FOK** Kin Ning, Canning - BA, DFM, FCA (ANZ) | Chairman and Non-executive Director (aged 73, since March 2009)"
```

**Startup**:
```
"**CHEN** Lisa Wei - Former Google Engineer | Co-Founder & CTO (equity: 25%)"
```

**Non-Profit**:
```
"**JOHNSON** Sarah Marie - MSW, MBA | Executive Director (since 2019)"
```

**Government**:
```
"**WILLIAMS** Janet Marie - Former Deputy Secretary | Agency Director (appointed 2021)"
```

## Advanced Customization

### Adding New Role Categories

```python
custom_config = existing_config.copy()
custom_config["new_category"] = {
    "new_role": {
        "description": "Description of new role type",
        "format": "**SURNAME** Given Names - Background | Title",
        "examples": ["**EXAMPLE** Name - Background | New Role Title"]
    }
}
```

### Modifying Existing Templates

```python
# Start with existing template
config = CorporateRolesTemplates.get_template("startup")

# Add new role to existing category
config["founding_team"]["technical_cofounder"] = {
    "description": "Technical co-founders with engineering background",
    "format": "**SURNAME** Given Names - Technical Background | Technical Co-Founder",
    "examples": ["**SMITH** John Michael - Former Apple Engineer | Technical Co-Founder"]
}

# Apply modified configuration
graph_builder.customize_corporate_roles_config(config)
```

## Best Practices

1. **Use Appropriate Templates**: Start with the closest pre-built template
2. **Consistent Formatting**: Follow the established format patterns
3. **Clear Descriptions**: Write specific descriptions for each role type
4. **Good Examples**: Provide realistic examples that match your data
5. **Test Thoroughly**: Test with sample documents before production use
6. **Document Changes**: Keep track of customizations for future reference

## Troubleshooting

### Common Issues

1. **No Extractions**: Check that role names match your document content
2. **Wrong Format**: Verify format patterns match your examples
3. **Missing Roles**: Ensure all relevant roles are included in configuration
4. **Inconsistent Results**: Review examples and descriptions for clarity

### Debugging Tips

1. **Start Simple**: Begin with basic roles and add complexity gradually
2. **Check Examples**: Ensure examples match actual document content
3. **Test Incrementally**: Test each role category separately
4. **Review Logs**: Check extraction logs for insights

## Migration from Hardcoded System

If you're migrating from the previous hardcoded system:

1. **Identify Current Roles**: List all roles currently being extracted
2. **Choose Template**: Select the closest pre-built template
3. **Customize as Needed**: Modify template to match your specific needs
4. **Test Thoroughly**: Verify extractions match previous results
5. **Update Documentation**: Document any customizations made

The new system provides the same functionality as before but with much greater flexibility and reusability across different organization types.
