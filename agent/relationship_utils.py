"""
Utility functions for working with relationship types.
"""

from typing import List, Dict, Any, Optional, Tuple
from .entity_models import RelationshipType, EntityType


class RelationshipValidator:
    """Validates and suggests appropriate relationship types."""
    
    @staticmethod
    def validate_relationship_type(
        source_entity_type: EntityType,
        target_entity_type: EntityType,
        relationship_type: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate if a relationship type is appropriate for the given entity types.
        
        Args:
            source_entity_type: Type of source entity
            target_entity_type: Type of target entity
            relationship_type: Proposed relationship type
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Person to Person relationships
        if (source_entity_type == EntityType.PERSON and 
            target_entity_type == EntityType.PERSON):
            valid_types = RelationshipType.get_person_to_person_relationships()
            if relationship_type not in valid_types:
                return False, f"Invalid person-to-person relationship type. Valid types: {valid_types}"
        
        # Person to Company relationships
        elif (source_entity_type == EntityType.PERSON and 
              target_entity_type == EntityType.COMPANY):
            valid_types = RelationshipType.get_person_to_company_relationships()
            if relationship_type not in valid_types:
                return False, f"Invalid person-to-company relationship type. Valid types: {valid_types}"
        
        # Company to Company relationships
        elif (source_entity_type == EntityType.COMPANY and 
              target_entity_type == EntityType.COMPANY):
            valid_types = RelationshipType.get_company_to_company_relationships()
            if relationship_type not in valid_types:
                return False, f"Invalid company-to-company relationship type. Valid types: {valid_types}"
        
        # Company to Person relationships (reverse of person to company)
        elif (source_entity_type == EntityType.COMPANY and 
              target_entity_type == EntityType.PERSON):
            # For company to person, we need to check if there's a reverse relationship
            person_to_company_types = RelationshipType.get_person_to_company_relationships()
            reverse_mapping = RelationshipValidator.get_reverse_relationship_mapping()
            
            if relationship_type not in reverse_mapping.values():
                return False, f"Invalid company-to-person relationship type. Consider using person-to-company relationships instead."
        
        return True, None
    
    @staticmethod
    def suggest_relationship_types(
        source_entity_type: EntityType,
        target_entity_type: EntityType,
        context: Optional[str] = None
    ) -> List[str]:
        """
        Suggest appropriate relationship types based on entity types and context.
        
        Args:
            source_entity_type: Type of source entity
            target_entity_type: Type of target entity
            context: Optional context to help suggest specific relationships
        
        Returns:
            List of suggested relationship types
        """
        suggestions = []
        
        # Person to Person
        if (source_entity_type == EntityType.PERSON and 
            target_entity_type == EntityType.PERSON):
            suggestions = RelationshipType.get_person_to_person_relationships()
            
            if context:
                context_lower = context.lower()
                if any(word in context_lower for word in ['fund', 'money', 'investment']):
                    suggestions = [RelationshipType.PROVIDED_FUND_FOR] + suggestions
                elif any(word in context_lower for word in ['guarantee', 'surety']):
                    suggestions = [RelationshipType.PROVIDED_GUARANTEES_FOR] + suggestions
                elif any(word in context_lower for word in ['transaction', 'deal', 'business']):
                    suggestions = [RelationshipType.HAD_TRANSACTIONS_WITH] + suggestions
        
        # Person to Company
        elif (source_entity_type == EntityType.PERSON and 
              target_entity_type == EntityType.COMPANY):
            suggestions = RelationshipType.get_person_to_company_relationships()
            
            if context:
                context_lower = context.lower()
                if any(word in context_lower for word in ['chairman', 'president']):
                    suggestions = [RelationshipType.CHAIRMAN_AND_PRESIDENT_AND_EXECUTIVE_DIRECTOR_OF] + suggestions
                elif any(word in context_lower for word in ['vice', 'deputy']):
                    suggestions = [RelationshipType.VICECHAIRPERSON_AND_NON_EXECUTIVE_DIRECTOR_OF] + suggestions
                elif any(word in context_lower for word in ['executive director']):
                    suggestions = [RelationshipType.EXECUTIVE_DIRECTOR_OF] + suggestions
                elif any(word in context_lower for word in ['independent', 'non-executive']):
                    suggestions = [RelationshipType.INDEPENDENT_NON_EXECUTIVE_DIRECTOR_OF] + suggestions
                elif any(word in context_lower for word in ['secretary']):
                    suggestions = [RelationshipType.COMPANY_SECRETARY_OF] + suggestions
                elif any(word in context_lower for word in ['shares', 'shareholder']):
                    suggestions = [RelationshipType.SHAREHOLDER_OF] + suggestions
        
        # Company to Company
        elif (source_entity_type == EntityType.COMPANY and 
              target_entity_type == EntityType.COMPANY):
            suggestions = RelationshipType.get_company_to_company_relationships()
            
            if context:
                context_lower = context.lower()
                if any(word in context_lower for word in ['subsidiary', 'owned by']):
                    suggestions = [RelationshipType.SUBSIDIARY_OF] + suggestions
                elif any(word in context_lower for word in ['shares', 'shareholder']):
                    suggestions = [RelationshipType.SHAREHOLDER_OF_COMPANY] + suggestions
                elif any(word in context_lower for word in ['bonds', 'listed']):
                    suggestions = [RelationshipType.LIST_BONDS_ON] + suggestions
                elif any(word in context_lower for word in ['underwriter', 'underwriting']):
                    suggestions = [RelationshipType.UNDERWRITER_OF] + suggestions
                elif any(word in context_lower for word in ['guarantee']):
                    suggestions = [RelationshipType.PROVIDED_GUARANTEE_TO] + suggestions
                elif any(word in context_lower for word in ['purchase', 'acquisition']):
                    suggestions = [RelationshipType.HAD_PURCHASE_AGREEMENT_WITH] + suggestions
                elif any(word in context_lower for word in ['equity', 'transfer']):
                    suggestions = [RelationshipType.HAD_EQUITY_TRANSFER_AGREEMENT_WITH] + suggestions
                elif any(word in context_lower for word in ['loan']):
                    suggestions = [RelationshipType.HAD_LOAN_TRANSFER_AGREEMENT_WITH] + suggestions
                elif any(word in context_lower for word in ['facility', 'service']):
                    suggestions = [RelationshipType.HAD_FACILITY_AGREEMENT_WITH] + suggestions
        
        return suggestions
    
    @staticmethod
    def get_reverse_relationship_mapping() -> Dict[str, str]:
        """Get mapping of relationships to their reverse counterparts."""
        return {
            RelationshipType.SUBSIDIARY_OF: "parent_of",
            RelationshipType.SHAREHOLDER_OF: "owned_by",
            RelationshipType.SHAREHOLDER_OF_COMPANY: "owned_by",
            RelationshipType.UNDERWRITER_OF: "underwritten_by",
            RelationshipType.PROVIDED_GUARANTEE_TO: "guaranteed_by",
            RelationshipType.AGENTED_BY: "agent_of",
            # Add more reverse mappings as needed
        }
    
    @staticmethod
    def get_relationship_description(relationship_type: str) -> str:
        """Get a human-readable description of a relationship type."""
        descriptions = {
            # Person-to-Person
            RelationshipType.RELATED_TO: "General relationship between individuals",
            RelationshipType.PROVIDED_FUND_FOR: "One person provided funding to another",
            RelationshipType.PROVIDED_GUARANTEES_FOR: "One person provided guarantees for another",
            RelationshipType.HAD_TRANSACTIONS_WITH: "Business or financial transactions between individuals",
            
            # Person-to-Company
            RelationshipType.COMPANY_SECRETARY_OF: "Person serves as company secretary",
            RelationshipType.EXECUTIVE_OF: "Person holds executive position",
            RelationshipType.SHAREHOLDER_OF: "Person owns shares in the company",
            RelationshipType.CHAIRMAN_AND_PRESIDENT_AND_EXECUTIVE_DIRECTOR_OF: "Combined senior leadership role",
            RelationshipType.VICECHAIRPERSON_AND_NON_EXECUTIVE_DIRECTOR_OF: "Combined vice chair and director role",
            RelationshipType.EXECUTIVE_DIRECTOR_OF: "Person serves as executive director",
            RelationshipType.NON_EXECUTIVE_DIRECTOR_OF: "Person serves as non-executive director",
            RelationshipType.INDEPENDENT_NON_EXECUTIVE_DIRECTOR_OF: "Person serves as independent director",
            
            # Company-to-Company
            RelationshipType.SHAREHOLDER_OF_COMPANY: "Company owns shares in another company",
            RelationshipType.LIST_BONDS_ON: "Company has bonds listed on an exchange",
            RelationshipType.SUBSIDIARY_OF: "Company is a subsidiary of another",
            RelationshipType.AGENTED_BY: "Company is represented by an agent",
            RelationshipType.UNDERWRITER_OF: "Company underwrites another's securities",
            RelationshipType.PROVIDED_GUARANTEE_TO: "Company provided guarantee to another",
            RelationshipType.HAD_PURCHASE_AGREEMENT_WITH: "Purchase agreement between companies",
            RelationshipType.HAD_EQUITY_TRANSFER_AGREEMENT_WITH: "Equity transfer agreement",
            RelationshipType.HAD_LOAN_TRANSFER_AGREEMENT_WITH: "Loan transfer agreement",
            RelationshipType.HAD_FACILITY_AGREEMENT_WITH: "Facility or service agreement",
        }
        
        return descriptions.get(relationship_type, f"Relationship type: {relationship_type}")
    
    @staticmethod
    def categorize_relationships(relationships: List[str]) -> Dict[str, List[str]]:
        """Categorize a list of relationship types."""
        categories = {
            "financial": [],
            "governance": [],
            "person_to_person": [],
            "person_to_company": [],
            "company_to_company": [],
            "other": []
        }
        
        for rel_type in relationships:
            if rel_type in RelationshipType.get_financial_relationships():
                categories["financial"].append(rel_type)
            elif rel_type in RelationshipType.get_governance_relationships():
                categories["governance"].append(rel_type)
            elif rel_type in RelationshipType.get_person_to_person_relationships():
                categories["person_to_person"].append(rel_type)
            elif rel_type in RelationshipType.get_person_to_company_relationships():
                categories["person_to_company"].append(rel_type)
            elif rel_type in RelationshipType.get_company_to_company_relationships():
                categories["company_to_company"].append(rel_type)
            else:
                categories["other"].append(rel_type)
        
        return categories


# Convenience functions
def validate_relationship(source_type: EntityType, target_type: EntityType, rel_type: str) -> bool:
    """Quick validation of relationship type."""
    is_valid, _ = RelationshipValidator.validate_relationship_type(source_type, target_type, rel_type)
    return is_valid


def suggest_relationships(source_type: EntityType, target_type: EntityType, context: str = None) -> List[str]:
    """Quick suggestion of relationship types."""
    return RelationshipValidator.suggest_relationship_types(source_type, target_type, context)


def describe_relationship(rel_type: str) -> str:
    """Quick description of relationship type."""
    return RelationshipValidator.get_relationship_description(rel_type)
