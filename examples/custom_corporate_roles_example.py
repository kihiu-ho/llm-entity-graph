#!/usr/bin/env python3
"""
Example script demonstrating how to use the generalized corporate roles system.
This shows how to customize corporate roles extraction for different types of organizations.
"""

import asyncio
import logging
from typing import Dict, Any

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_public_company_config() -> Dict[str, Any]:
    """Configuration for public companies (default)."""
    return {
        "executive_roles": {
            "executive_directors": {
                "description": "Executive directors with full biographical details including age, tenure, qualifications, and career history",
                "format": "**SURNAME** Given Names - Qualifications | Title (aged X, additional details)",
                "examples": ["**LUI** Dennis Pok Man - BSc | Executive Deputy Chairman (aged 74, re-designated 11 December 2024)"]
            },
            "ceo_coo": {
                "description": "Chief executives and operating officers with career progression and experience",
                "format": "**SURNAME** Given Names - Qualifications | Title (aged X, since Date)",
                "examples": ["**KOO** Sing Fai - BSc Computer Science | Chief Executive Officer (aged 52, since August 2018)"]
            }
        },
        "board_roles": {
            "chairman": {
                "description": "Chairman with executive/non-executive status, age, and appointment history",
                "format": "**SURNAME** Given Names - Qualifications | Title (aged X, since Date)",
                "examples": ["**FOK** Kin Ning, Canning - BA, DFM, FCA (ANZ) | Chairman and Non-executive Director (aged 73, since March 2009)"]
            },
            "independent_directors": {
                "description": "Independent non-executive directors with professional background and committee roles",
                "format": "**SURNAME** Given Names - Qualifications | Title (aged X, since Date)",
                "examples": ["**CHAN** Tze Leung - BSc(Econ), MBA, FHKIOD | Independent Non-executive Director (aged 78, since 9 May 2024)"]
            }
        },
        "governance_structures": {
            "board_committees": {
                "description": "Extract all committee structures with member names and roles",
                "format": "Committee Name: **CHAIRMAN** Name (Chairman), **MEMBER** Name (member)",
                "examples": ["Audit Committee: **CHAN** Tze Leung (Chairman), **IM** Man Ieng (member)"]
            },
            "auditors": {
                "description": "External auditors with full firm names and certifications",
                "format": "Firm Name - Certifications and registrations",
                "examples": ["PricewaterhouseCoopers - Certified Public Accountants, Registered Public Interest Entity Auditor"]
            }
        }
    }


def get_nonprofit_config() -> Dict[str, Any]:
    """Configuration for non-profit organizations."""
    return {
        "leadership_roles": {
            "board_chair": {
                "description": "Board chairperson with tenure and background",
                "format": "**SURNAME** Given Names - Background | Board Chair (since Date)",
                "examples": ["**SMITH** John Michael - Former CEO, Tech Industry | Board Chair (since 2020)"]
            },
            "executive_director": {
                "description": "Executive director with organizational leadership experience",
                "format": "**SURNAME** Given Names - Qualifications | Executive Director (aged X, since Date)",
                "examples": ["**JOHNSON** Sarah Marie - MSW, MBA | Executive Director (aged 45, since 2019)"]
            },
            "program_directors": {
                "description": "Program directors and department heads",
                "format": "**SURNAME** Given Names - Qualifications | Title",
                "examples": ["**BROWN** Michael David - PhD Education | Program Director"]
            }
        },
        "governance": {
            "trustees": {
                "description": "Board trustees with professional backgrounds",
                "format": "**SURNAME** Given Names - Background | Trustee",
                "examples": ["**WILSON** Jennifer Anne - Attorney, Corporate Law | Trustee"]
            },
            "advisors": {
                "description": "Advisory board members and consultants",
                "format": "**SURNAME** Given Names - Expertise | Advisor",
                "examples": ["**DAVIS** Robert James - Financial Planning Expert | Financial Advisor"]
            },
            "committees": {
                "description": "Organizational committees and working groups",
                "format": "Committee Name: **CHAIR** Name (Chair), **MEMBER** Name (member)",
                "examples": ["Finance Committee: **WILSON** Jennifer (Chair), **DAVIS** Robert (member)"]
            }
        }
    }


def get_startup_config() -> Dict[str, Any]:
    """Configuration for startup companies."""
    return {
        "founding_team": {
            "founders": {
                "description": "Company founders with background and equity stakes",
                "format": "**SURNAME** Given Names - Background | Co-Founder (equity: X%)",
                "examples": ["**CHEN** Lisa Wei - Former Google Engineer | Co-Founder & CTO (equity: 25%)"]
            },
            "ceo": {
                "description": "Chief Executive Officer with startup experience",
                "format": "**SURNAME** Given Names - Background | CEO (since Date)",
                "examples": ["**PATEL** Raj Kumar - Serial Entrepreneur | CEO (since founding, 2021)"]
            }
        },
        "leadership_team": {
            "c_suite": {
                "description": "C-level executives with startup experience",
                "format": "**SURNAME** Given Names - Background | Title (joined Date)",
                "examples": ["**GARCIA** Maria Elena - Former McKinsey | Chief Operating Officer (joined 2022)"]
            },
            "vp_level": {
                "description": "Vice Presidents and senior management",
                "format": "**SURNAME** Given Names - Background | Title",
                "examples": ["**THOMPSON** David Lee - Ex-Facebook | VP Engineering"]
            }
        },
        "investors": {
            "board_members": {
                "description": "Investor representatives on the board",
                "format": "**SURNAME** Given Names - Fund/Company | Board Member",
                "examples": ["**ANDERSON** Mark Steven - Sequoia Capital | Board Member"]
            },
            "advisors": {
                "description": "Industry advisors and mentors",
                "format": "**SURNAME** Given Names - Background | Advisor",
                "examples": ["**MARTINEZ** Carlos Jose - Former Uber Executive | Strategic Advisor"]
            }
        }
    }


def get_government_config() -> Dict[str, Any]:
    """Configuration for government agencies."""
    return {
        "executive_leadership": {
            "director": {
                "description": "Agency director or administrator",
                "format": "**SURNAME** Given Names - Background | Director (appointed Date)",
                "examples": ["**WILLIAMS** Janet Marie - Former Deputy Secretary | Agency Director (appointed 2021)"]
            },
            "deputy_directors": {
                "description": "Deputy directors and assistant administrators",
                "format": "**SURNAME** Given Names - Background | Deputy Director",
                "examples": ["**TAYLOR** Robert James - Career Civil Servant | Deputy Director"]
            }
        },
        "department_heads": {
            "division_chiefs": {
                "description": "Division and department chiefs",
                "format": "**SURNAME** Given Names - Background | Chief, Division Name",
                "examples": ["**MOORE** Patricia Ann - PhD Public Policy | Chief, Policy Division"]
            },
            "program_managers": {
                "description": "Program managers and coordinators",
                "format": "**SURNAME** Given Names - Background | Program Manager",
                "examples": ["**CLARK** Steven Michael - MBA | Program Manager, Operations"]
            }
        },
        "oversight": {
            "inspector_general": {
                "description": "Inspector General and oversight officials",
                "format": "**SURNAME** Given Names - Background | Inspector General",
                "examples": ["**LEWIS** Margaret Rose - Former FBI | Inspector General"]
            },
            "advisory_committees": {
                "description": "Advisory committees and external oversight",
                "format": "Committee Name: **CHAIR** Name (Chair), **MEMBER** Name (member)",
                "examples": ["Advisory Committee: **HARRIS** John (Chair), **WHITE** Susan (member)"]
            }
        }
    }


async def demonstrate_custom_corporate_roles():
    """Demonstrate how to use custom corporate roles configurations."""
    
    logger.info("=== Demonstrating Custom Corporate Roles Configurations ===")
    
    try:
        from ingestion.graph_builder import GraphBuilder
        from ingestion.chunker import DocumentChunk
        
        # Sample texts for different organization types
        sample_texts = {
            "public_company": """
            Mr. John Michael Chen, aged 58, has been the Chairman and President and Executive Director of TechCorp Holdings Limited since January 2020. He is also an Independent Non-executive Director of DataFlow Systems Limited.
            
            The Audit Committee is chaired by Mr. David Wong, with members including Ms. Sarah Lee and Mr. Robert Kim. PricewaterhouseCoopers serves as the external auditor.
            """,
            
            "nonprofit": """
            Dr. Sarah Johnson, Executive Director of the Community Health Foundation since 2019, brings over 15 years of experience in public health administration. She holds an MSW from Columbia University and an MBA from Wharton.
            
            The Board of Trustees is chaired by Jennifer Wilson, a corporate attorney specializing in nonprofit law. The Finance Committee is led by Robert Davis, a certified financial planner.
            """,
            
            "startup": """
            Lisa Chen, Co-Founder and CTO of InnovateTech, previously worked as a senior engineer at Google for 8 years. She holds a 25% equity stake in the company.
            
            The company's CEO, Raj Patel, is a serial entrepreneur who founded two previous startups. Mark Anderson from Sequoia Capital serves on the board of directors.
            """,
            
            "government": """
            Janet Williams was appointed as Agency Director in 2021, bringing extensive experience from her previous role as Deputy Secretary. She oversees multiple divisions including the Policy Division, led by Dr. Patricia Moore.
            
            The Inspector General, Margaret Lewis, formerly served with the FBI for 20 years. The agency's Advisory Committee is chaired by John Harris.
            """
        }
        
        # Test each configuration
        configs = {
            "public_company": get_public_company_config(),
            "nonprofit": get_nonprofit_config(),
            "startup": get_startup_config(),
            "government": get_government_config()
        }
        
        for org_type, config in configs.items():
            logger.info(f"\n--- Testing {org_type.upper()} Configuration ---")
            
            # Initialize graph builder
            graph_builder = GraphBuilder()
            
            # Customize the corporate roles configuration
            graph_builder.customize_corporate_roles_config(config)
            
            # Create document chunk
            chunk = DocumentChunk(
                content=sample_texts[org_type],
                index=0,
                start_char=0,
                end_char=len(sample_texts[org_type]),
                metadata={},
                token_count=len(sample_texts[org_type].split())
            )
            
            try:
                # Extract entities using the custom configuration
                enriched_chunks = await graph_builder.extract_entities_from_document(
                    chunks=[chunk],
                    extract_companies=True,
                    extract_people=True,
                    extract_corporate_roles=True,
                    use_llm_for_corporate_roles=True
                )
                
                if enriched_chunks and hasattr(enriched_chunks[0], 'metadata'):
                    entities = enriched_chunks[0].metadata.get('entities', {})
                    corporate_roles = entities.get('corporate_roles', {})
                    
                    logger.info(f"Extracted corporate roles for {org_type}:")
                    for role_category, roles in corporate_roles.items():
                        if roles:
                            logger.info(f"  {role_category}: {roles}")
                
            except Exception as e:
                logger.error(f"Failed to extract entities for {org_type}: {e}")
            
            finally:
                await graph_builder.close()
    
    except Exception as e:
        logger.error(f"Demonstration failed: {e}")


def show_configuration_examples():
    """Show examples of different corporate roles configurations."""
    
    logger.info("\n=== Corporate Roles Configuration Examples ===")
    
    configs = {
        "Public Company": get_public_company_config(),
        "Non-Profit Organization": get_nonprofit_config(),
        "Startup Company": get_startup_config(),
        "Government Agency": get_government_config()
    }
    
    for org_type, config in configs.items():
        logger.info(f"\n{org_type} Configuration:")
        logger.info("-" * (len(org_type) + 15))
        
        for category_name, category_data in config.items():
            logger.info(f"\n{category_name.upper().replace('_', ' ')}:")
            for role_name, role_data in category_data.items():
                logger.info(f"  - {role_name}: {role_data['description']}")
                if 'examples' in role_data and role_data['examples']:
                    logger.info(f"    Example: {role_data['examples'][0]}")


async def main():
    """Run the corporate roles customization demonstration."""
    
    logger.info("Corporate Roles Generalization Example")
    logger.info("=" * 50)
    
    # Show configuration examples
    show_configuration_examples()
    
    # Demonstrate custom configurations in action
    await demonstrate_custom_corporate_roles()
    
    logger.info("\n" + "=" * 50)
    logger.info("Corporate Roles Customization Complete!")
    
    logger.info("\n🎯 KEY BENEFITS:")
    logger.info("✅ Configurable for different organization types")
    logger.info("✅ Customizable role categories and formats")
    logger.info("✅ Flexible extraction patterns")
    logger.info("✅ Reusable across different domains")
    
    logger.info("\n📚 USAGE:")
    logger.info("1. Define custom configuration dictionary")
    logger.info("2. Call graph_builder.customize_corporate_roles_config(custom_config)")
    logger.info("3. Extract entities as usual - custom roles will be used automatically")
    logger.info("4. Different configurations for different document types")


if __name__ == "__main__":
    asyncio.run(main())
