"""
Corporate Roles Configuration Templates

This module provides pre-defined templates for different types of organizations.
Users can select and customize these templates for their specific needs.
"""

from typing import Dict, Any


class CorporateRolesTemplates:
    """Collection of corporate roles templates for different organization types."""
    
    @staticmethod
    def public_company() -> Dict[str, Any]:
        """Template for publicly traded companies."""
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
                "deputy_chairman": {
                    "description": "Deputy chairmen with re-designation dates and previous roles",
                    "format": "**SURNAME** Given Names - Qualifications | Title (re-designated Date)",
                    "examples": ["**LUI** Dennis Pok Man - BSc | Executive Deputy Chairman (re-designated 11 December 2024)"]
                },
                "non_executive_directors": {
                    "description": "Non-executive directors with complete profiles including other board positions",
                    "format": "**SURNAME** Given Names - Qualifications | Title (aged X)",
                    "examples": ["**WOO** Chiu Man, Cliff - BSc, Diploma in Management | Non-executive Deputy Chairman (aged 71)"]
                },
                "independent_directors": {
                    "description": "Independent non-executive directors with professional background and committee roles",
                    "format": "**SURNAME** Given Names - Qualifications | Title (aged X, since Date)",
                    "examples": ["**CHAN** Tze Leung - BSc(Econ), MBA, FHKIOD | Independent Non-executive Director (aged 78, since 9 May 2024)"]
                }
            },
            "management_roles": {
                "company_secretaries": {
                    "description": "Company secretaries with legal qualifications and tenure",
                    "format": "**SURNAME** Given Names - Qualifications | Title (Service period)",
                    "examples": ["**SHIH** Edith - BSc, MA, MA, EdM, Solicitor, FCG, HKFCG | Former Company Secretary (November 2007 to May 2023)"]
                },
                "other_roles": {
                    "description": "Management team, alternates, and special positions",
                    "format": "**SURNAME** Given Names - Qualifications | Title (aged X, since Date)",
                    "examples": [
                        "**NG** Marcus Byron - BSc Accounting, CPA | Chief Financial Officer (aged 41, since April 2023)",
                        "**LEONG** Bing Yow - BEng | Chief Technology Officer (aged 41, since January 2023)"
                    ]
                }
            },
            "governance_structures": {
                "board_committees": {
                    "description": "Extract all committee structures with member names and roles",
                    "format": "Committee Name: **CHAIRMAN** Name (Chairman), **MEMBER** Name (member)",
                    "examples": [
                        "Audit Committee: **CHAN** Tze Leung (Chairman), **IM** Man Ieng (member)",
                        "Remuneration Committee: **IP** Yuk Keung (Chairman since 9 May 2024)"
                    ]
                },
                "auditors": {
                    "description": "External auditors with full firm names and certifications",
                    "format": "Firm Name - Certifications and registrations",
                    "examples": ["PricewaterhouseCoopers - Certified Public Accountants, Registered Public Interest Entity Auditor"]
                }
            }
        }
    
    @staticmethod
    def private_company() -> Dict[str, Any]:
        """Template for private companies."""
        return {
            "ownership": {
                "owners": {
                    "description": "Company owners and major shareholders",
                    "format": "**SURNAME** Given Names - Background | Owner (stake: X%)",
                    "examples": ["**SMITH** John Michael - Founder | Owner (stake: 60%)"]
                },
                "partners": {
                    "description": "Business partners and co-owners",
                    "format": "**SURNAME** Given Names - Background | Partner",
                    "examples": ["**JOHNSON** Sarah Marie - Co-Founder | Managing Partner"]
                }
            },
            "management": {
                "ceo": {
                    "description": "Chief Executive Officer",
                    "format": "**SURNAME** Given Names - Background | CEO",
                    "examples": ["**BROWN** Michael David - MBA, 15 years experience | CEO"]
                },
                "management_team": {
                    "description": "Senior management team",
                    "format": "**SURNAME** Given Names - Background | Title",
                    "examples": ["**WILSON** Jennifer Anne - CPA | Chief Financial Officer"]
                }
            },
            "advisory": {
                "board_of_advisors": {
                    "description": "Advisory board members",
                    "format": "**SURNAME** Given Names - Expertise | Advisor",
                    "examples": ["**DAVIS** Robert James - Industry Expert | Strategic Advisor"]
                }
            }
        }
    
    @staticmethod
    def nonprofit() -> Dict[str, Any]:
        """Template for non-profit organizations."""
        return {
            "leadership": {
                "executive_director": {
                    "description": "Executive director with organizational leadership experience",
                    "format": "**SURNAME** Given Names - Qualifications | Executive Director (since Date)",
                    "examples": ["**JOHNSON** Sarah Marie - MSW, MBA | Executive Director (since 2019)"]
                },
                "program_directors": {
                    "description": "Program directors and department heads",
                    "format": "**SURNAME** Given Names - Qualifications | Title",
                    "examples": ["**BROWN** Michael David - PhD Education | Program Director"]
                }
            },
            "governance": {
                "board_chair": {
                    "description": "Board chairperson with tenure and background",
                    "format": "**SURNAME** Given Names - Background | Board Chair (since Date)",
                    "examples": ["**SMITH** John Michael - Former CEO | Board Chair (since 2020)"]
                },
                "trustees": {
                    "description": "Board trustees with professional backgrounds",
                    "format": "**SURNAME** Given Names - Background | Trustee",
                    "examples": ["**WILSON** Jennifer Anne - Attorney | Trustee"]
                },
                "committees": {
                    "description": "Organizational committees and working groups",
                    "format": "Committee Name: **CHAIR** Name (Chair), **MEMBER** Name (member)",
                    "examples": ["Finance Committee: **WILSON** Jennifer (Chair), **DAVIS** Robert (member)"]
                }
            }
        }
    
    @staticmethod
    def startup() -> Dict[str, Any]:
        """Template for startup companies."""
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
                    "examples": ["**GARCIA** Maria Elena - Former McKinsey | COO (joined 2022)"]
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
    
    @staticmethod
    def government_agency() -> Dict[str, Any]:
        """Template for government agencies."""
        return {
            "executive_leadership": {
                "director": {
                    "description": "Agency director or administrator",
                    "format": "**SURNAME** Given Names - Background | Director (appointed Date)",
                    "examples": ["**WILLIAMS** Janet Marie - Former Deputy Secretary | Director (appointed 2021)"]
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
    
    @staticmethod
    def academic_institution() -> Dict[str, Any]:
        """Template for academic institutions."""
        return {
            "administration": {
                "president": {
                    "description": "University or college president",
                    "format": "**SURNAME** Given Names - Academic Background | President (since Date)",
                    "examples": ["**ANDERSON** Mary Elizabeth - PhD Physics, Former Provost | President (since 2020)"]
                },
                "provost": {
                    "description": "Provost and academic vice presidents",
                    "format": "**SURNAME** Given Names - Academic Background | Provost",
                    "examples": ["**THOMPSON** James Robert - PhD History | Provost and VP Academic Affairs"]
                },
                "deans": {
                    "description": "College and school deans",
                    "format": "**SURNAME** Given Names - Academic Background | Dean, School/College Name",
                    "examples": ["**GARCIA** Carlos Miguel - PhD Engineering | Dean, School of Engineering"]
                }
            },
            "governance": {
                "board_of_trustees": {
                    "description": "Board of trustees or regents",
                    "format": "**SURNAME** Given Names - Background | Trustee",
                    "examples": ["**WILSON** Patricia Ann - Former CEO | Board Chair"]
                },
                "faculty_senate": {
                    "description": "Faculty senate leadership",
                    "format": "**SURNAME** Given Names - Department | Faculty Senate Chair",
                    "examples": ["**BROWN** Michael David - Professor of Biology | Faculty Senate Chair"]
                }
            }
        }
    
    @staticmethod
    def get_template(organization_type: str) -> Dict[str, Any]:
        """
        Get a template by organization type.
        
        Args:
            organization_type: Type of organization
            
        Returns:
            Corporate roles configuration template
        """
        templates = {
            "public_company": CorporateRolesTemplates.public_company,
            "private_company": CorporateRolesTemplates.private_company,
            "nonprofit": CorporateRolesTemplates.nonprofit,
            "startup": CorporateRolesTemplates.startup,
            "government_agency": CorporateRolesTemplates.government_agency,
            "academic_institution": CorporateRolesTemplates.academic_institution
        }
        
        if organization_type in templates:
            return templates[organization_type]()
        else:
            raise ValueError(f"Unknown organization type: {organization_type}. Available types: {list(templates.keys())}")
    
    @staticmethod
    def list_available_templates() -> list:
        """List all available template types."""
        return [
            "public_company",
            "private_company", 
            "nonprofit",
            "startup",
            "government_agency",
            "academic_institution"
        ]
