"""
Neo4j schema definitions for Person and Company node types.
"""

import logging
from typing import Dict, List, Optional, Any
from neo4j import GraphDatabase
from datetime import datetime

logger = logging.getLogger(__name__)


class Neo4jSchemaManager:
    """Manages Neo4j schema definitions for Person and Company nodes."""
    
    def __init__(self, uri: str, username: str, password: str):
        """
        Initialize Neo4j schema manager.
        
        Args:
            uri: Neo4j database URI
            username: Database username
            password: Database password
        """
        self.driver = GraphDatabase.driver(uri, auth=(username, password))
        
    def close(self):
        """Close the database connection."""
        if self.driver:
            self.driver.close()
    
    def create_person_node_type(self):
        """Create Person node type with constraints and indexes."""
        with self.driver.session() as session:
            # Create unique constraint on Person name
            session.run("""
                CREATE CONSTRAINT person_name_unique IF NOT EXISTS
                FOR (p:Person) REQUIRE p.name IS UNIQUE
            """)
            
            # Create indexes for Person properties
            session.run("""
                CREATE INDEX person_full_name_index IF NOT EXISTS
                FOR (p:Person) ON (p.full_name)
            """)
            
            session.run("""
                CREATE INDEX person_current_company_index IF NOT EXISTS
                FOR (p:Person) ON (p.current_company)
            """)
            
            session.run("""
                CREATE INDEX person_current_position_index IF NOT EXISTS
                FOR (p:Person) ON (p.current_position)
            """)
            
            session.run("""
                CREATE INDEX person_email_index IF NOT EXISTS
                FOR (p:Person) ON (p.email)
            """)
            
            session.run("""
                CREATE INDEX person_type_index IF NOT EXISTS
                FOR (p:Person) ON (p.person_type)
            """)
            
            logger.info("Person node type constraints and indexes created")
    
    def create_company_node_type(self):
        """Create Company node type with constraints and indexes."""
        with self.driver.session() as session:
            # Create unique constraint on Company name
            session.run("""
                CREATE CONSTRAINT company_name_unique IF NOT EXISTS
                FOR (c:Company) REQUIRE c.name IS UNIQUE
            """)
            
            # Create indexes for Company properties
            session.run("""
                CREATE INDEX company_legal_name_index IF NOT EXISTS
                FOR (c:Company) ON (c.legal_name)
            """)
            
            session.run("""
                CREATE INDEX company_ticker_symbol_index IF NOT EXISTS
                FOR (c:Company) ON (c.ticker_symbol)
            """)
            
            session.run("""
                CREATE INDEX company_industry_index IF NOT EXISTS
                FOR (c:Company) ON (c.industry)
            """)
            
            session.run("""
                CREATE INDEX company_headquarters_index IF NOT EXISTS
                FOR (c:Company) ON (c.headquarters)
            """)
            
            session.run("""
                CREATE INDEX company_type_index IF NOT EXISTS
                FOR (c:Company) ON (c.company_type)
            """)
            
            session.run("""
                CREATE INDEX company_registration_number_index IF NOT EXISTS
                FOR (c:Company) ON (c.registration_number)
            """)
            
            logger.info("Company node type constraints and indexes created")
    
    def create_relationship_indexes(self):
        """Create indexes for relationship types."""
        with self.driver.session() as session:
            # Create index for relationship types
            session.run("""
                CREATE INDEX relationship_type_index IF NOT EXISTS
                FOR ()-[r]-() ON (r.relationship_type)
            """)
            
            session.run("""
                CREATE INDEX relationship_start_date_index IF NOT EXISTS
                FOR ()-[r]-() ON (r.start_date)
            """)
            
            session.run("""
                CREATE INDEX relationship_end_date_index IF NOT EXISTS
                FOR ()-[r]-() ON (r.end_date)
            """)
            
            session.run("""
                CREATE INDEX relationship_strength_index IF NOT EXISTS
                FOR ()-[r]-() ON (r.strength)
            """)
            
            logger.info("Relationship indexes created")
    
    def create_person_node(
        self,
        name: str,
        person_type: Optional[str] = None,
        full_name: Optional[str] = None,
        current_company: Optional[str] = None,
        current_position: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        linkedin: Optional[str] = None,
        nationality: Optional[str] = None,
        education: Optional[List[str]] = None,
        skills: Optional[List[str]] = None,
        languages: Optional[List[str]] = None,
        aliases: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create a Person node in Neo4j.
        
        Args:
            name: Person's name (required, unique)
            person_type: Type of person (executive, director, etc.)
            full_name: Full legal name
            current_company: Current employer
            current_position: Current job title
            email: Email address
            phone: Phone number
            linkedin: LinkedIn profile URL
            nationality: Nationality
            education: List of educational background
            skills: List of professional skills
            languages: List of languages spoken
            aliases: List of alternative names
            metadata: Additional metadata
        
        Returns:
            Node ID or identifier
        """
        with self.driver.session() as session:
            # Prepare properties
            properties = {
                "name": name,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            # Add optional properties
            if person_type:
                properties["person_type"] = person_type
            if full_name:
                properties["full_name"] = full_name
            if current_company:
                properties["current_company"] = current_company
            if current_position:
                properties["current_position"] = current_position
            if email:
                properties["email"] = email
            if phone:
                properties["phone"] = phone
            if linkedin:
                properties["linkedin"] = linkedin
            if nationality:
                properties["nationality"] = nationality
            if education:
                properties["education"] = education
            if skills:
                properties["skills"] = skills
            if languages:
                properties["languages"] = languages
            if aliases:
                properties["aliases"] = aliases
            if metadata:
                properties.update(metadata)
            
            # Create the node
            result = session.run("""
                CREATE (p:Person $properties)
                RETURN elementId(p) as node_id
            """, properties=properties)
            
            node_id = result.single()["node_id"]
            logger.info(f"Created Person node: {name} (ID: {node_id})")
            return node_id
    
    def create_company_node(
        self,
        name: str,
        company_type: Optional[str] = None,
        legal_name: Optional[str] = None,
        trading_name: Optional[str] = None,
        ticker_symbol: Optional[str] = None,
        exchange: Optional[str] = None,
        registration_number: Optional[str] = None,
        tax_id: Optional[str] = None,
        website: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        headquarters: Optional[str] = None,
        incorporation_country: Optional[str] = None,
        operating_countries: Optional[List[str]] = None,
        addresses: Optional[List[str]] = None,
        industry: Optional[str] = None,
        sectors: Optional[List[str]] = None,
        products: Optional[List[str]] = None,
        technologies: Optional[List[str]] = None,
        founded_date: Optional[str] = None,
        employee_count: Optional[int] = None,
        annual_revenue: Optional[float] = None,
        market_cap: Optional[float] = None,
        parent_company: Optional[str] = None,
        subsidiaries: Optional[List[str]] = None,
        key_executives: Optional[List[str]] = None,
        aliases: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create a Company node in Neo4j.
        
        Args:
            name: Company name (required, unique)
            company_type: Type of company (public, private, etc.)
            legal_name: Legal company name
            trading_name: Trading/brand name
            ticker_symbol: Stock ticker symbol
            exchange: Stock exchange
            registration_number: Company registration number
            tax_id: Tax identification number
            website: Company website
            email: Contact email
            phone: Contact phone
            headquarters: Headquarters location
            incorporation_country: Country of incorporation
            operating_countries: Countries of operation
            addresses: Business addresses
            industry: Primary industry
            sectors: Business sectors
            products: Products/services
            technologies: Technologies used
            founded_date: Date founded
            employee_count: Number of employees
            annual_revenue: Annual revenue
            market_cap: Market capitalization
            parent_company: Parent company
            subsidiaries: Subsidiary companies
            key_executives: Key executives
            aliases: Alternative names
            metadata: Additional metadata
        
        Returns:
            Node ID or identifier
        """
        with self.driver.session() as session:
            # Prepare properties
            properties = {
                "name": name,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            # Add optional properties
            if company_type:
                properties["company_type"] = company_type
            if legal_name:
                properties["legal_name"] = legal_name
            if trading_name:
                properties["trading_name"] = trading_name
            if ticker_symbol:
                properties["ticker_symbol"] = ticker_symbol
            if exchange:
                properties["exchange"] = exchange
            if registration_number:
                properties["registration_number"] = registration_number
            if tax_id:
                properties["tax_id"] = tax_id
            if website:
                properties["website"] = website
            if email:
                properties["email"] = email
            if phone:
                properties["phone"] = phone
            if headquarters:
                properties["headquarters"] = headquarters
            if incorporation_country:
                properties["incorporation_country"] = incorporation_country
            if operating_countries:
                properties["operating_countries"] = operating_countries
            if addresses:
                properties["addresses"] = addresses
            if industry:
                properties["industry"] = industry
            if sectors:
                properties["sectors"] = sectors
            if products:
                properties["products"] = products
            if technologies:
                properties["technologies"] = technologies
            if founded_date:
                properties["founded_date"] = founded_date
            if employee_count:
                properties["employee_count"] = employee_count
            if annual_revenue:
                properties["annual_revenue"] = annual_revenue
            if market_cap:
                properties["market_cap"] = market_cap
            if parent_company:
                properties["parent_company"] = parent_company
            if subsidiaries:
                properties["subsidiaries"] = subsidiaries
            if key_executives:
                properties["key_executives"] = key_executives
            if aliases:
                properties["aliases"] = aliases
            if metadata:
                properties.update(metadata)
            
            # Create the node
            result = session.run("""
                CREATE (c:Company $properties)
                RETURN elementId(c) as node_id
            """, properties=properties)
            
            node_id = result.single()["node_id"]
            logger.info(f"Created Company node: {name} (ID: {node_id})")
            return node_id
