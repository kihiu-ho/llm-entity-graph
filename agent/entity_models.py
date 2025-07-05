"""
Entity models for the knowledge graph.
"""

from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class EntityType(str, Enum):
    """Entity type enumeration."""
    PERSON = "person"
    COMPANY = "company"
    LOCATION = "location"
    TECHNOLOGY = "technology"
    FINANCIAL_ENTITY = "financial_entity"
    CORPORATE_ROLE = "corporate_role"
    OWNERSHIP = "ownership"
    TRANSACTION = "transaction"
    PERSONAL_CONNECTION = "personal_connection"


class PersonType(str, Enum):
    """Person type enumeration."""
    EXECUTIVE = "executive"
    DIRECTOR = "director"
    EMPLOYEE = "employee"
    CONSULTANT = "consultant"
    INVESTOR = "investor"
    OTHER = "other"


class CompanyType(str, Enum):
    """Company type enumeration."""
    PUBLIC = "public"
    PRIVATE = "private"
    SUBSIDIARY = "subsidiary"
    PARTNERSHIP = "partnership"
    NON_PROFIT = "non_profit"
    GOVERNMENT = "government"
    OTHER = "other"


class BaseEntity(BaseModel):
    """Base entity model."""
    id: Optional[str] = None
    name: str = Field(..., description="Entity name")
    entity_type: EntityType = Field(..., description="Type of entity")
    aliases: List[str] = Field(default_factory=list, description="Alternative names")
    description: Optional[str] = Field(None, description="Entity description")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    source_documents: List[str] = Field(default_factory=list, description="Source document IDs")
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Extraction confidence")
    created_at: Optional[datetime] = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = Field(default_factory=datetime.now)


class Person(BaseEntity):
    """Person node model."""
    entity_type: EntityType = Field(default=EntityType.PERSON, frozen=True)
    person_type: Optional[PersonType] = Field(None, description="Type of person")
    full_name: Optional[str] = Field(None, description="Full legal name")
    first_name: Optional[str] = Field(None, description="First name")
    last_name: Optional[str] = Field(None, description="Last name")
    title: Optional[str] = Field(None, description="Professional title")
    email: Optional[str] = Field(None, description="Email address")
    phone: Optional[str] = Field(None, description="Phone number")
    linkedin: Optional[str] = Field(None, description="LinkedIn profile URL")
    birth_date: Optional[datetime] = Field(None, description="Date of birth")
    nationality: Optional[str] = Field(None, description="Nationality")
    education: List[str] = Field(default_factory=list, description="Educational background")
    skills: List[str] = Field(default_factory=list, description="Professional skills")
    languages: List[str] = Field(default_factory=list, description="Languages spoken")
    
    # Professional information
    current_company: Optional[str] = Field(None, description="Current employer")
    current_position: Optional[str] = Field(None, description="Current job title")
    previous_companies: List[str] = Field(default_factory=list, description="Previous employers")
    board_positions: List[str] = Field(default_factory=list, description="Board positions held")
    
    # Relationships
    reports_to: Optional[str] = Field(None, description="Manager/supervisor")
    direct_reports: List[str] = Field(default_factory=list, description="Direct reports")
    colleagues: List[str] = Field(default_factory=list, description="Professional colleagues")
    personal_connections: List[str] = Field(default_factory=list, description="Personal connections")


class Company(BaseEntity):
    """Company node model."""
    entity_type: EntityType = Field(default=EntityType.COMPANY, frozen=True)
    company_type: Optional[CompanyType] = Field(None, description="Type of company")
    legal_name: Optional[str] = Field(None, description="Legal company name")
    trading_name: Optional[str] = Field(None, description="Trading/brand name")
    ticker_symbol: Optional[str] = Field(None, description="Stock ticker symbol")
    exchange: Optional[str] = Field(None, description="Stock exchange")
    registration_number: Optional[str] = Field(None, description="Company registration number")
    tax_id: Optional[str] = Field(None, description="Tax identification number")
    website: Optional[str] = Field(None, description="Company website")
    email: Optional[str] = Field(None, description="Contact email")
    phone: Optional[str] = Field(None, description="Contact phone")
    
    # Location information
    headquarters: Optional[str] = Field(None, description="Headquarters location")
    incorporation_country: Optional[str] = Field(None, description="Country of incorporation")
    operating_countries: List[str] = Field(default_factory=list, description="Countries of operation")
    addresses: List[str] = Field(default_factory=list, description="Business addresses")
    
    # Business information
    industry: Optional[str] = Field(None, description="Primary industry")
    sectors: List[str] = Field(default_factory=list, description="Business sectors")
    products: List[str] = Field(default_factory=list, description="Products/services")
    technologies: List[str] = Field(default_factory=list, description="Technologies used")
    founded_date: Optional[datetime] = Field(None, description="Date founded")
    employee_count: Optional[int] = Field(None, description="Number of employees")
    annual_revenue: Optional[float] = Field(None, description="Annual revenue")
    market_cap: Optional[float] = Field(None, description="Market capitalization")
    
    # Corporate structure
    parent_company: Optional[str] = Field(None, description="Parent company")
    subsidiaries: List[str] = Field(default_factory=list, description="Subsidiary companies")
    joint_ventures: List[str] = Field(default_factory=list, description="Joint ventures")
    partnerships: List[str] = Field(default_factory=list, description="Strategic partnerships")
    
    # Key personnel
    ceo: Optional[str] = Field(None, description="Chief Executive Officer")
    cfo: Optional[str] = Field(None, description="Chief Financial Officer")
    cto: Optional[str] = Field(None, description="Chief Technology Officer")
    board_members: List[str] = Field(default_factory=list, description="Board of directors")
    key_executives: List[str] = Field(default_factory=list, description="Key executives")
    
    # Financial information
    public_company: Optional[bool] = Field(None, description="Is publicly traded")
    ipo_date: Optional[datetime] = Field(None, description="IPO date")
    fiscal_year_end: Optional[str] = Field(None, description="Fiscal year end month")


class Relationship(BaseModel):
    """Relationship between entities."""
    id: Optional[str] = None
    source_entity_id: str = Field(..., description="Source entity ID")
    target_entity_id: str = Field(..., description="Target entity ID")
    relationship_type: str = Field(..., description="Type of relationship")
    description: Optional[str] = Field(None, description="Relationship description")
    strength: Optional[float] = Field(None, ge=0.0, le=1.0, description="Relationship strength")
    start_date: Optional[datetime] = Field(None, description="Relationship start date")
    end_date: Optional[datetime] = Field(None, description="Relationship end date")
    is_active: bool = Field(default=True, description="Is relationship currently active")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    source_documents: List[str] = Field(default_factory=list, description="Source document IDs")
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Extraction confidence")
    created_at: Optional[datetime] = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = Field(default_factory=datetime.now)

    def is_financial_relationship(self) -> bool:
        """Check if this is a financial relationship."""
        return self.relationship_type in RelationshipType.get_financial_relationships()

    def is_governance_relationship(self) -> bool:
        """Check if this is a corporate governance relationship."""
        return self.relationship_type in RelationshipType.get_governance_relationships()

    def is_person_to_person(self) -> bool:
        """Check if this is a person-to-person relationship."""
        return self.relationship_type in RelationshipType.get_person_to_person_relationships()

    def is_person_to_company(self) -> bool:
        """Check if this is a person-to-company relationship."""
        return self.relationship_type in RelationshipType.get_person_to_company_relationships()

    def is_company_to_company(self) -> bool:
        """Check if this is a company-to-company relationship."""
        return self.relationship_type in RelationshipType.get_company_to_company_relationships()


def create_person_from_name(
    name: str,
    person_type: Optional[PersonType] = None,
    current_company: Optional[str] = None,
    current_position: Optional[str] = None,
    **kwargs
) -> Person:
    """
    Create a Person entity from a name and optional attributes.

    Args:
        name: Person's name
        person_type: Type of person
        current_company: Current employer
        current_position: Current job title
        **kwargs: Additional person attributes

    Returns:
        Person entity
    """
    return Person(
        name=name,
        person_type=person_type or PersonType.OTHER,
        current_company=current_company,
        current_position=current_position,
        **kwargs
    )


def create_company_from_name(
    name: str,
    company_type: Optional[CompanyType] = None,
    industry: Optional[str] = None,
    headquarters: Optional[str] = None,
    **kwargs
) -> Company:
    """
    Create a Company entity from a name and optional attributes.

    Args:
        name: Company name
        company_type: Type of company
        industry: Primary industry
        headquarters: Headquarters location
        **kwargs: Additional company attributes

    Returns:
        Company entity
    """
    return Company(
        name=name,
        company_type=company_type or CompanyType.OTHER,
        industry=industry,
        headquarters=headquarters,
        **kwargs
    )


class EntityGraph(BaseModel):
    """Entity graph containing entities and relationships."""
    entities: List[Union[Person, Company, BaseEntity]] = Field(default_factory=list)
    relationships: List[Relationship] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[datetime] = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = Field(default_factory=datetime.now)
    
    def add_entity(self, entity: Union[Person, Company, BaseEntity]) -> None:
        """Add an entity to the graph."""
        # Check if entity already exists
        existing_entity = self.get_entity_by_name(entity.name)
        if existing_entity:
            # Update existing entity
            existing_entity.updated_at = datetime.now()
            # Merge metadata and other fields as needed
        else:
            self.entities.append(entity)
    
    def add_relationship(self, relationship: Relationship) -> None:
        """Add a relationship to the graph."""
        self.relationships.append(relationship)
    
    def get_entity_by_name(self, name: str) -> Optional[Union[Person, Company, BaseEntity]]:
        """Get entity by name."""
        for entity in self.entities:
            if entity.name.lower() == name.lower() or name.lower() in [alias.lower() for alias in entity.aliases]:
                return entity
        return None
    
    def get_entities_by_type(self, entity_type: EntityType) -> List[Union[Person, Company, BaseEntity]]:
        """Get entities by type."""
        return [entity for entity in self.entities if entity.entity_type == entity_type]
    
    def get_relationships_for_entity(self, entity_id: str) -> List[Relationship]:
        """Get all relationships for an entity."""
        return [
            rel for rel in self.relationships
            if rel.source_entity_id == entity_id or rel.target_entity_id == entity_id
        ]

    def add_entities_from_extraction(self, extracted_entities: Dict[str, Any]) -> None:
        """
        Add entities from extraction results, mapping them to proper Person/Company types.

        Args:
            extracted_entities: Dictionary of extracted entities by category
        """
        # Add people
        if 'people' in extracted_entities and extracted_entities['people']:
            for person_name in extracted_entities['people']:
                if isinstance(person_name, str) and person_name.strip():
                    person = create_person_from_name(
                        name=person_name.strip(),
                        person_type=PersonType.OTHER
                    )
                    self.add_entity(person)

        # Add companies
        if 'companies' in extracted_entities and extracted_entities['companies']:
            for company_name in extracted_entities['companies']:
                if isinstance(company_name, str) and company_name.strip():
                    company = create_company_from_name(
                        name=company_name.strip(),
                        company_type=CompanyType.OTHER
                    )
                    self.add_entity(company)

        # Add people from corporate roles
        if 'corporate_roles' in extracted_entities and extracted_entities['corporate_roles']:
            for role_type, role_list in extracted_entities['corporate_roles'].items():
                if isinstance(role_list, list):
                    for person_name in role_list:
                        if isinstance(person_name, str) and person_name.strip():
                            # Determine person type based on role
                            person_type = PersonType.EXECUTIVE if 'executive' in role_type.lower() else PersonType.DIRECTOR
                            person = create_person_from_name(
                                name=person_name.strip(),
                                person_type=person_type,
                                current_position=role_type.replace('_', ' ').title()
                            )
                            self.add_entity(person)

    def get_person_entities(self) -> List[Person]:
        """Get all Person entities."""
        return [entity for entity in self.entities if isinstance(entity, Person)]

    def get_company_entities(self) -> List[Company]:
        """Get all Company entities."""
        return [entity for entity in self.entities if isinstance(entity, Company)]


# Common relationship types
class RelationshipType:
    """Common relationship types."""

    # Person-Person relationships
    RELATED_TO = "Related_TO"
    PROVIDED_FUND_FOR = "Provided_Fund_FOR"
    PROVIDED_GUARANTEES_FOR = "Provided_Guarantees_FOR"
    HAD_TRANSACTIONS_WITH = "Had_Transactions_WITH"
    REPORTS_TO = "reports_to"
    MANAGES = "manages"
    COLLEAGUE_OF = "colleague_of"
    FRIEND_OF = "friend_of"
    FAMILY_OF = "family_of"
    MENTOR_OF = "mentor_of"
    MENTORED_BY = "mentored_by"

    # Person-Company relationships
    COMPANY_SECRETARY_OF = "Company_Secretary_OF"
    EXECUTIVE_OF = "Executive_OF"
    SHAREHOLDER_OF = "Shareholder_OF"
    CHAIRMAN_AND_PRESIDENT_AND_EXECUTIVE_DIRECTOR_OF = "Chairman_AND_President_AND_Executive_Director_OF"
    VICECHAIRPERSON_AND_NON_EXECUTIVE_DIRECTOR_OF = "ViceChairperson_AND_Non_Executive_Director_OF"
    EXECUTIVE_DIRECTOR_OF = "Executive_Director_OF"
    NON_EXECUTIVE_DIRECTOR_OF = "Non_Executive_Director_OF"
    INDEPENDENT_NON_EXECUTIVE_DIRECTOR_OF = "Independent_Non_Executive_Director_OF"
    EMPLOYED_BY = "employed_by"
    DIRECTOR_OF = "director_of"
    FOUNDER_OF = "founder_of"
    INVESTOR_IN = "investor_in"
    CONSULTANT_TO = "consultant_to"

    # Company-Company relationships
    SHAREHOLDER_OF_COMPANY = "Shareholder_OF"  # Note: Different from person shareholder
    LIST_BONDS_ON = "List_Bonds_ON"
    SUBSIDIARY_OF = "Subsidiary_OF"
    AGENTED_BY = "Agented_BY"
    UNDERWRITER_OF = "Underwriter_OF"
    PROVIDED_GUARANTEE_TO = "Provided_Guarantee_TO"
    HAD_PURCHASE_AGREEMENT_WITH = "Had_Purchase_Agreement_WITH"
    HAD_EQUITY_TRANSFER_AGREEMENT_WITH = "Had_Equity_Transfer_Agreement_WITH"
    HAD_LOAN_TRANSFER_AGREEMENT_WITH = "Had_Loan_Transfer_Agreement_WITH"
    HAD_FACILITY_AGREEMENT_WITH = "Had_Facility_Agreement_WITH"
    PARENT_OF = "parent_of"
    PARTNER_WITH = "partner_with"
    COMPETITOR_OF = "competitor_of"
    SUPPLIER_TO = "supplier_to"
    CUSTOMER_OF = "customer_of"
    ACQUIRED_BY = "acquired_by"
    MERGED_WITH = "merged_with"

    # General relationships
    OWNS = "owns"
    OWNED_BY = "owned_by"
    LOCATED_IN = "located_in"
    OPERATES_IN = "operates_in"
    USES_TECHNOLOGY = "uses_technology"
    DEVELOPED_BY = "developed_by"

    @classmethod
    def get_person_to_person_relationships(cls) -> List[str]:
        """Get all person-to-person relationship types."""
        return [
            cls.RELATED_TO,
            cls.PROVIDED_FUND_FOR,
            cls.PROVIDED_GUARANTEES_FOR,
            cls.HAD_TRANSACTIONS_WITH,
            cls.REPORTS_TO,
            cls.MANAGES,
            cls.COLLEAGUE_OF,
            cls.FRIEND_OF,
            cls.FAMILY_OF,
            cls.MENTOR_OF,
            cls.MENTORED_BY
        ]

    @classmethod
    def get_person_to_company_relationships(cls) -> List[str]:
        """Get all person-to-company relationship types."""
        return [
            cls.COMPANY_SECRETARY_OF,
            cls.EXECUTIVE_OF,
            cls.SHAREHOLDER_OF,
            cls.CHAIRMAN_AND_PRESIDENT_AND_EXECUTIVE_DIRECTOR_OF,
            cls.VICECHAIRPERSON_AND_NON_EXECUTIVE_DIRECTOR_OF,
            cls.EXECUTIVE_DIRECTOR_OF,
            cls.NON_EXECUTIVE_DIRECTOR_OF,
            cls.INDEPENDENT_NON_EXECUTIVE_DIRECTOR_OF,
            cls.EMPLOYED_BY,
            cls.DIRECTOR_OF,
            cls.FOUNDER_OF,
            cls.INVESTOR_IN,
            cls.CONSULTANT_TO
        ]

    @classmethod
    def get_company_to_company_relationships(cls) -> List[str]:
        """Get all company-to-company relationship types."""
        return [
            cls.SHAREHOLDER_OF_COMPANY,
            cls.LIST_BONDS_ON,
            cls.SUBSIDIARY_OF,
            cls.AGENTED_BY,
            cls.UNDERWRITER_OF,
            cls.PROVIDED_GUARANTEE_TO,
            cls.HAD_PURCHASE_AGREEMENT_WITH,
            cls.HAD_EQUITY_TRANSFER_AGREEMENT_WITH,
            cls.HAD_LOAN_TRANSFER_AGREEMENT_WITH,
            cls.HAD_FACILITY_AGREEMENT_WITH,
            cls.PARENT_OF,
            cls.PARTNER_WITH,
            cls.COMPETITOR_OF,
            cls.SUPPLIER_TO,
            cls.CUSTOMER_OF,
            cls.ACQUIRED_BY,
            cls.MERGED_WITH
        ]

    @classmethod
    def get_financial_relationships(cls) -> List[str]:
        """Get all financial/transaction relationship types."""
        return [
            cls.PROVIDED_FUND_FOR,
            cls.PROVIDED_GUARANTEES_FOR,
            cls.HAD_TRANSACTIONS_WITH,
            cls.SHAREHOLDER_OF,
            cls.SHAREHOLDER_OF_COMPANY,
            cls.LIST_BONDS_ON,
            cls.UNDERWRITER_OF,
            cls.PROVIDED_GUARANTEE_TO,
            cls.HAD_PURCHASE_AGREEMENT_WITH,
            cls.HAD_EQUITY_TRANSFER_AGREEMENT_WITH,
            cls.HAD_LOAN_TRANSFER_AGREEMENT_WITH,
            cls.HAD_FACILITY_AGREEMENT_WITH,
            cls.INVESTOR_IN
        ]

    @classmethod
    def get_governance_relationships(cls) -> List[str]:
        """Get all corporate governance relationship types."""
        return [
            cls.COMPANY_SECRETARY_OF,
            cls.EXECUTIVE_OF,
            cls.CHAIRMAN_AND_PRESIDENT_AND_EXECUTIVE_DIRECTOR_OF,
            cls.VICECHAIRPERSON_AND_NON_EXECUTIVE_DIRECTOR_OF,
            cls.EXECUTIVE_DIRECTOR_OF,
            cls.NON_EXECUTIVE_DIRECTOR_OF,
            cls.INDEPENDENT_NON_EXECUTIVE_DIRECTOR_OF,
            cls.DIRECTOR_OF
        ]
