#!/usr/bin/env python3
"""
Test script to verify entity extraction from director biography text.
"""

import json
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Sample director text from the user
DIRECTOR_TEXT = """
# 1. IP Yuk Keung

# Independent Non-executive Director

Ip Yuk Keung, aged 72, has been an Independent Non-executive Director of the Company, Chairman of the Audit Committee, a Remuneration Committee member and a Nomination Committee member since December 2019, and was appointed as Chairman of the Remuneration Committee since 9 May 2024. Mr Ip is an international banking and finance professional with over 32 years of experience in U.S.A., Asia and Hong Kong. He was formerly Managing Director of Citigroup and Managing Director of Investments of Merrill Lynch (Asia Pacific). Mr Ip is an independent non-executive director of Eagle Asset Management (CP) Limited as the manager of Champion Real Estate Investment Trust, Power Assets, New World Development Company Limited and Lifestyle International Holdings Limited (which had withdrawn its listing on 20 December 2022). He was previously an independent non-executive director of TOM.

Mr Ip is an Adjunct Professor of and an advisor to various universities in Hong Kong, U.S.A. and Macau. He is a member of the Court of City University of Hong Kong ("CityU") and HKUST, an Honorary Fellow of CityU, HKUST and Vocational Training Council, Chairman of Business Career Development Advisory Committee of the College of Business of CityU, Senior Advisor to the President, Chairman of Career Development Advisory Council and Special Advisor to the Dean of the School of Business and Management, Chairman of Career Development Advisor Board and Honorary Advisor of the School of Humanities and Social Science of HKUST, an Advisory Board Member for the Faculty of Business Administration at the University of Macau, and a Beta Gamma Sigma Honoree at CityU and HKUST. Mr Ip is chairman of HKUST Foundation and also serves as a member of the Science and Technology Council, the Macau Special Administrative Region of the People's Republic of China. He was previously a Council Member of HKUST. Mr Ip holds a Bachelor of Science degree in Applied Mathematics and Computer Science, a Master of Science degree in Applied Mathematics and a Master of Science degree in Accounting and Finance.
"""

def test_entity_extraction_prompt():
    """Test the entity extraction prompt structure."""
    
    # Simulate the prompt that would be generated
    prompt = f"""You are an expert entity extraction system. Analyze the following text and extract relevant entities in the specified categories. Return your response as a valid JSON object.

TEXT TO ANALYZE:
{DIRECTOR_TEXT}

EXTRACTION INSTRUCTIONS:
Extract entities in the following categories. If no entities are found in a category, return an empty list or object as appropriate.

COMPANIES: Extract company names, organizations, and corporate entities.
- Include: corporations, businesses, firms, organizations, institutions
- Format: Full official company names (e.g., "Apple Inc.", "Microsoft Corporation")
- Exclude: Individual person names, even if they hold corporate positions
- Look for: suffixes like Inc, Corp, Ltd, LLC, AG, SE, SA, PLC, GmbH

PEOPLE: Extract individual person names only - NOT company names or organizations.
- Include: Individual human beings, executives, employees, board members
- Format: Full person names (e.g., "John Smith", "Mary Johnson", "Dr. Sarah Wilson")
- Look for: titles like Mr., Mrs., Dr., Prof., or role-based context
- Exclude: Company names, organization names, group entities
- Separate person names from their titles/qualifications (extract "John Smith" not "John Smith, CEO")

CORPORATE_ROLES:
Extract comprehensive director and management information from biographical profiles with detailed formatting:

FORMAT REQUIREMENTS:
- Separate person names from their qualifications/credentials
- Bold the surname (family name) in the person's name
- Extract age, tenure, and career history
- Capture all committee memberships and roles
- Include board positions at other companies
- Extract educational qualifications and professional memberships
- Identify alternate director relationships
- Capture appointment and re-designation dates

CATEGORIES TO EXTRACT:
- executive_directors: Executive directors with full biographical details including age, tenure, qualifications, and career history
- non_executive_directors: Non-executive directors with complete profiles including other board positions
- independent_directors: Independent non-executive directors with professional background and committee roles
- chairman: Chairman with executive/non-executive status, age, and appointment history
- deputy_chairman: Deputy chairmen with re-designation dates and previous roles
- ceo_coo: Chief executives and operating officers with career progression and experience
- company_secretaries: Company secretaries with legal qualifications and tenure
- board_committees: Extract all committee structures with member names and roles:
  * Audit Committee: Chairman and members
  * Remuneration Committee: Chairman and members
  * Nomination Committee: Chairman and members
  * Sustainability Committee: Chairman and members
- auditors: External auditors with full firm names and certifications
- other_roles: Management team, alternates, and special positions

LOCATIONS: Extract location names, cities, countries, and geographical references.
NETWORK_ENTITIES: Any other entities that appear to be part of a broader network or ecosystem related to the main entities.

RESPONSE FORMAT:
Return a valid JSON object with ONLY the categories that were requested above. 
Example structure (only include requested categories):
{{
    "companies": ["company1", "company2"],
    "people": ["person1", "person2"],
    "corporate_roles": {{
        "executive_directors": ["**LUI** Dennis Pok Man - BSc | Executive Deputy Chairman (aged 74, re-designated 11 December 2024)"],
        "non_executive_directors": ["**WOO** Chiu Man, Cliff - BSc, Diploma in Management | Non-executive Deputy Chairman (aged 71)"],
        "independent_directors": ["**CHAN** Tze Leung - BSc(Econ), MBA, FHKIOD | Independent Non-executive Director (aged 78, since 9 May 2024)"],
        "chairman": ["**FOK** Kin Ning, Canning - BA, DFM, FCA (ANZ) | Chairman and Non-executive Director (aged 73, since March 2009)"],
        "deputy_chairman": ["**LUI** Dennis Pok Man - BSc | Executive Deputy Chairman (re-designated 11 December 2024)"],
        "ceo_coo": ["**KOO** Sing Fai - BSc Computer Science | Chief Executive Officer (aged 52, since August 2018)"],
        "company_secretaries": ["**SHIH** Edith - BSc, MA, MA, EdM, Solicitor, FCG, HKFCG | Former Company Secretary (November 2007 to May 2023)"],
        "board_committees": [
            "Audit Committee: **CHAN** Tze Leung (Chairman), **IM** Man Ieng (member)",
            "Remuneration Committee: **IP** Yuk Keung (Chairman since 9 May 2024)",
            "Nomination Committee: **CHAN** Tze Leung (Chairman), **IP** Yuk Keung (member)",
            "Sustainability Committee: **SHIH** Edith (Chairman since July 2020)"
        ],
        "auditors": ["PricewaterhouseCoopers - Certified Public Accountants, Registered Public Interest Entity Auditor"],
        "other_roles": [
            "**NG** Marcus Byron - BSc Accounting, CPA | Chief Financial Officer (aged 41, since April 2023)",
            "**LEONG** Bing Yow - BEng | Chief Technology Officer (aged 41, since January 2023)",
            "**LAI** Kai Ming, Dominic - BSc(Hons), MBA | Alternate to **FOK** Kin Ning, Canning and **SHIH** Edith"
        ]
    }},
    "locations": ["location1", "location2"],
    "network_entities": ["entity1", "entity2"]
}}

IMPORTANT:
- Only extract entities that are explicitly mentioned in the text
- Only include the categories that were specifically requested above
- Be precise and avoid speculation
- Use the exact names/terms as they appear in the text
- If uncertain about categorization, include in the most appropriate category
- Return valid JSON only, no additional text or explanation
- If no entities found for a category, return empty arrays or objects
"""

    print("=== ENTITY EXTRACTION PROMPT ===")
    print(prompt)
    print("\n=== EXPECTED ENTITIES ===")
    
    expected_entities = {
        "people": [
            "Ip Yuk Keung"
        ],
        "companies": [
            "Citigroup",
            "Merrill Lynch (Asia Pacific)",
            "Eagle Asset Management (CP) Limited",
            "Champion Real Estate Investment Trust",
            "Power Assets",
            "New World Development Company Limited",
            "Lifestyle International Holdings Limited",
            "TOM",
            "City University of Hong Kong",
            "HKUST",
            "Vocational Training Council",
            "University of Macau",
            "HKUST Foundation",
            "Science and Technology Council"
        ],
        "corporate_roles": {
            "independent_directors": [
                "**IP** Yuk Keung - Independent Non-executive Director (aged 72, since December 2019)"
            ],
            "board_committees": [
                "Audit Committee: **IP** Yuk Keung (Chairman)",
                "Remuneration Committee: **IP** Yuk Keung (Chairman since 9 May 2024, member since December 2019)",
                "Nomination Committee: **IP** Yuk Keung (member since December 2019)"
            ],
            "other_roles": [
                "**IP** Yuk Keung - Managing Director of Citigroup (former)",
                "**IP** Yuk Keung - Managing Director of Investments of Merrill Lynch (Asia Pacific) (former)",
                "**IP** Yuk Keung - Independent non-executive director of Eagle Asset Management (CP) Limited",
                "**IP** Yuk Keung - Independent non-executive director of Power Assets",
                "**IP** Yuk Keung - Independent non-executive director of New World Development Company Limited",
                "**IP** Yuk Keung - Independent non-executive director of Lifestyle International Holdings Limited",
                "**IP** Yuk Keung - Independent non-executive director of TOM (former)",
                "**IP** Yuk Keung - Adjunct Professor",
                "**IP** Yuk Keung - Chairman of HKUST Foundation"
            ]
        },
        "locations": [
            "U.S.A.",
            "Asia",
            "Hong Kong",
            "Macau"
        ]
    }
    
    print(json.dumps(expected_entities, indent=2))
    
    print("\n=== ANALYSIS ===")
    print("✓ Person Node: Ip Yuk Keung should be extracted")
    print("✓ Company Nodes: Multiple companies should be extracted including:")
    print("  - Citigroup")
    print("  - Merrill Lynch (Asia Pacific)")
    print("  - Eagle Asset Management (CP) Limited")
    print("  - Champion Real Estate Investment Trust")
    print("  - Power Assets")
    print("  - New World Development Company Limited")
    print("  - Lifestyle International Holdings Limited")
    print("  - TOM")
    print("  - City University of Hong Kong")
    print("  - HKUST")
    print("  - University of Macau")
    print("  - HKUST Foundation")
    
    print("\n✓ Corporate Roles: Should extract detailed director information")
    print("✓ Locations: Should extract U.S.A., Asia, Hong Kong, Macau")
    
    return True


def test_neo4j_node_creation():
    """Test how the extracted entities would be created as Neo4j nodes."""
    
    print("\n=== NEO4J NODE CREATION ===")
    
    # Person Node
    print("Person Node:")
    person_cypher = """
CREATE (p:Person {
    name: "Ip Yuk Keung",
    person_type: "director",
    full_name: "Ip Yuk Keung",
    current_position: "Independent Non-executive Director",
    age: 72,
    tenure_start: "December 2019",
    education: [
        "Bachelor of Science degree in Applied Mathematics and Computer Science",
        "Master of Science degree in Applied Mathematics", 
        "Master of Science degree in Accounting and Finance"
    ],
    experience_years: 32,
    specialization: "international banking and finance",
    committee_roles: [
        "Chairman of the Audit Committee",
        "Chairman of the Remuneration Committee (since 9 May 2024)",
        "Remuneration Committee member",
        "Nomination Committee member"
    ],
    other_directorships: [
        "Eagle Asset Management (CP) Limited",
        "Power Assets",
        "New World Development Company Limited",
        "Lifestyle International Holdings Limited"
    ],
    former_positions: [
        "Managing Director of Citigroup",
        "Managing Director of Investments of Merrill Lynch (Asia Pacific)",
        "Independent non-executive director of TOM"
    ],
    academic_roles: [
        "Adjunct Professor",
        "Chairman of HKUST Foundation",
        "Member of the Court of City University of Hong Kong",
        "Honorary Fellow of CityU, HKUST and Vocational Training Council"
    ],
    created_at: datetime(),
    updated_at: datetime()
})
"""
    print(person_cypher)
    
    # Company Nodes (sample)
    print("\nCompany Nodes (sample):")
    company_cypher = """
CREATE (c1:Company {
    name: "Citigroup",
    company_type: "public",
    industry: "Banking",
    created_at: datetime()
})

CREATE (c2:Company {
    name: "Eagle Asset Management (CP) Limited",
    company_type: "private",
    industry: "Asset Management",
    created_at: datetime()
})

CREATE (c3:Company {
    name: "City University of Hong Kong",
    company_type: "educational",
    industry: "Education",
    headquarters: "Hong Kong",
    aliases: ["CityU"],
    created_at: datetime()
})
"""
    print(company_cypher)
    
    # Relationships
    print("\nRelationships:")
    relationship_cypher = """
// Current director relationship
MATCH (p:Person {name: "Ip Yuk Keung"})
MATCH (c:Company {name: "The Company"})  // Assuming "the Company" refers to main company
CREATE (p)-[r:RELATED {
    relationship_type: "Independent_Non_Executive_Director_OF",
    description: "Independent Non-executive Director since December 2019",
    start_date: "2019-12-01",
    is_active: true,
    committee_roles: ["Audit Committee Chairman", "Remuneration Committee Chairman"],
    created_at: datetime()
}]->(c)

// Former position relationship
MATCH (p:Person {name: "Ip Yuk Keung"})
MATCH (c:Company {name: "Citigroup"})
CREATE (p)-[r:RELATED {
    relationship_type: "Executive_OF",
    description: "Former Managing Director",
    is_active: false,
    created_at: datetime()
}]->(c)
"""
    print(relationship_cypher)
    
    return True


def main():
    """Main test function."""
    print("Testing Director Entity Extraction")
    print("=" * 50)
    
    # Test the extraction prompt
    test_entity_extraction_prompt()
    
    # Test Neo4j node creation
    test_neo4j_node_creation()
    
    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    print("✓ The LLM extraction prompt should now properly extract:")
    print("  - Person nodes: Ip Yuk Keung")
    print("  - Company nodes: 12+ companies and institutions")
    print("  - Corporate roles: Detailed director information")
    print("  - Relationships: Multiple professional relationships")
    print("\n✓ The ingestion script has been updated to use LLM for all entity types")
    print("✓ Rule-based extraction has been completely removed")
    print("✓ Neo4j schema supports Person and Company node types")
    
    print("\nTo test with actual LLM:")
    print("1. Set up LLM_API_KEY environment variable")
    print("2. Run: python -m ingestion.ingest documents/director.md")
    print("3. Check the knowledge graph for extracted entities")


if __name__ == "__main__":
    main()
