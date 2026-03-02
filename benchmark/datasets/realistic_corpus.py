"""
Realistic corpus dataset - curated text samples packaged locally.
"""

import json
from pathlib import Path
from typing import List, Dict, Optional


class RealisticCorpusDataset:
    """Curated realistic text samples with ground truth annotations."""
    
    has_ground_truth = True
    size = 25
    
    def __init__(self, custom_path: Optional[str] = None):
        self.custom_path = custom_path
        self.data = None
    
    def load(self) -> List[Dict]:
        """Load the realistic corpus dataset."""
        if self.data is not None:
            return self.data
        
        if self.custom_path:
            # Load from custom path
            with open(self.custom_path, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
        else:
            # Use built-in dataset
            self.data = self._get_builtin_data()
        
        return self.data
    
    def _get_builtin_data(self) -> List[Dict]:
        """Get built-in realistic corpus dataset."""
        return [
            {
                "id": "realistic_001",
                "topic": "Healthcare Patient Data Management",
                "documents": [
                    {
                        "source": "healthcare_forum",
                        "url": "local://healthcare_patient_data",
                        "text": "Working in a small clinic, managing patient records is becoming increasingly complex. We have paper files, digital scans, and three different software systems that don't talk to each other. When patients come in, we spend more time finding their records than treating them. HIPAA compliance adds another layer of complexity. We need a unified system that's affordable for small practices."
                    },
                    {
                        "source": "medical_blog",
                        "url": "local://medical_blog_emr",
                        "text": "The electronic health record (EHR) market is dominated by expensive enterprise solutions that small clinics can't afford. These systems often require dedicated IT staff and extensive training. What's missing is a lightweight, HIPAA-compliant solution that focuses on the core needs of small practices: patient records, appointment scheduling, and basic billing integration."
                    }
                ],
                "ground_truth": {
                    "pains": [
                        {
                            "actor": "Small clinic staff",
                            "context": "Patient record management",
                            "problem": "Fragmented data across multiple incompatible systems",
                            "severity": 5
                        },
                        {
                            "actor": "Healthcare provider",
                            "context": "Compliance and operations",
                            "problem": "HIPAA compliance adds complexity to data management",
                            "severity": 4
                        },
                        {
                            "actor": "Small clinic owner",
                            "context": "Budget constraints",
                            "problem": "Enterprise EHR solutions too expensive for small practices",
                            "severity": 4
                        }
                    ],
                    "clusters": [
                        {
                            "label": "Data Integration Challenges",
                            "pain_ids": [0]
                        },
                        {
                            "label": "Cost and Compliance Barriers",
                            "pain_ids": [1, 2]
                        }
                    ],
                    "competitors": [
                        {
                            "name": "Epic Systems",
                            "positioning": "Comprehensive EHR for large healthcare organizations",
                            "pricing": "$1,200+ per provider per month"
                        },
                        {
                            "name": "Athenahealth",
                            "positioning": "Cloud-based healthcare solutions",
                            "pricing": "$140-300 per provider per month"
                        },
                        {
                            "name": "Practice Fusion",
                            "positioning": "EHR for small practices",
                            "pricing": "$149-349 per provider per month"
                        }
                    ],
                    "best_opportunity": {
                        "title": "Affordable EHR for Small Clinics",
                        "reason": "Clear market gap for cost-effective, simplified EHR solution"
                    },
                    "decision": "PASS",
                    "confidence": 0.8
                }
            },
            {
                "id": "realistic_002",
                "topic": "Construction Project Management",
                "documents": [
                    {
                        "source": "construction_forum",
                        "url": "local://construction_project_mgmt",
                        "text": "General contractor here. Managing construction projects is a constant battle against delays and cost overruns. We deal with multiple subcontractors, changing requirements, weather delays, and complex permitting processes. Most project management software is designed for software development, not construction. We need something that understands construction workflows, change orders, and subcontractor coordination."
                    },
                    {
                        "source": "industry_report",
                        "url": "local://construction_industry_analysis",
                        "text": "The construction industry suffers from persistent productivity issues, with projects typically running 20% over budget and 20% behind schedule. Key contributors include poor communication between stakeholders, fragmented information systems, and inadequate risk management. Digital adoption in construction remains low compared to other industries, creating opportunities for specialized solutions."
                    }
                ],
                "ground_truth": {
                    "pains": [
                        {
                            "actor": "General contractor",
                            "context": "Project execution",
                            "problem": "Difficulty coordinating multiple subcontractors and managing changes",
                            "severity": 4
                        },
                        {
                            "actor": "Construction project manager",
                            "context": "Budget and timeline management",
                            "problem": "Current project management tools not designed for construction workflows",
                            "severity": 4
                        },
                        {
                            "actor": "Construction company owner",
                            "context": "Industry challenges",
                            "problem": "Industry-wide productivity issues with cost overruns and delays",
                            "severity": 3
                        }
                    ],
                    "clusters": [
                        {
                            "label": "Project Coordination",
                            "pain_ids": [0, 1]
                        },
                        {
                            "label": "Industry Productivity",
                            "pain_ids": [2]
                        }
                    ],
                    "competitors": [
                        {
                            "name": "Procore",
                            "positioning": "Construction project management software",
                            "pricing": "$669-1,375 per month per company"
                        },
                        {
                            "name": "Autodesk Construction Cloud",
                            "positioning": "Integrated construction management platform",
                            "pricing": "$280-560 per month per user"
                        },
                        {
                            "name": "PlanGrid",
                            "positioning": "Construction field management software",
                            "pricing": "$39-59 per user per month"
                        }
                    ],
                    "best_opportunity": {
                        "title": "Construction-Specific Project Management",
                        "reason": "High-value market with clear pain points and expensive solutions"
                    },
                    "decision": "PASS",
                    "confidence": 0.7
                }
            },
            {
                "id": "realistic_003",
                "topic": "Nonprofit Volunteer Management",
                "documents": [
                    {
                        "source": "nonprofit_forum",
                        "url": "local://nonprofit_volunteer_mgmt",
                        "text": "Running a small nonprofit is challenging enough without wrestling with volunteer management. We rely on volunteers for everything from events to daily operations, but coordinating schedules, tracking hours, and keeping people engaged is manual and time-consuming. Most volunteer management tools are either too expensive for our budget or designed for large organizations with dedicated volunteer coordinators."
                    },
                    {
                        "source": "nonprofit_blog",
                        "url": "local://nonprofit_challenges",
                        "text": "Small nonprofits face unique operational challenges. With limited budgets and staff, they depend heavily on volunteers but lack tools designed for their scale. Volunteer turnover is high, and keeping volunteers engaged requires personal communication that's difficult to scale. The market needs affordable, simple volunteer management solutions that understand nonprofit constraints."
                    }
                ],
                "ground_truth": {
                    "pains": [
                        {
                            "actor": "Nonprofit director",
                            "context": "Volunteer coordination",
                            "problem": "Manual volunteer scheduling and hour tracking is time-consuming",
                            "severity": 4
                        },
                        {
                            "actor": "Nonprofit staff",
                            "context": "Budget constraints",
                            "problem": "Volunteer management tools too expensive for small nonprofits",
                            "severity": 4
                        },
                        {
                            "actor": "Volunteer coordinator",
                            "context": "Engagement and retention",
                            "problem": "Difficulty keeping volunteers engaged and preventing turnover",
                            "severity": 3
                        }
                    ],
                    "clusters": [
                        {
                            "label": "Operational Efficiency",
                            "pain_ids": [0]
                        },
                        {
                            "label": "Budget and Engagement",
                            "pain_ids": [1, 2]
                        }
                    ],
                    "competitors": [
                        {
                            "name": "VolunteerHub",
                            "positioning": "Volunteer management for organizations of all sizes",
                            "pricing": "$50-200 per month based on volunteers"
                        },
                        {
                            "name": "SignUpGenius",
                            "positioning": "Event and volunteer scheduling",
                            "pricing": "Free with paid plans starting at $25/month"
                        },
                        {
                            "name": "BetterImpact",
                            "positioning": "Volunteer management platform",
                            "pricing": "$39-99 per month"
                        }
                    ],
                    "best_opportunity": {
                        "title": "Affordable Volunteer Management for Small Nonprofits",
                        "reason": "Clear need for budget-friendly volunteer coordination tools"
                    },
                    "decision": "KILL",
                    "confidence": 0.4
                }
            },
            {
                "id": "realistic_004",
                "topic": "Legal Document Automation",
                "documents": [
                    {
                        "source": "legal_forum",
                        "url": "local://legal_document_automation",
                        "text": "Small law firm partner here. We spend countless hours on routine document preparation - contracts, NDAs, engagement letters, compliance forms. The big firms have document automation systems, but they cost hundreds of thousands of dollars. For small firms, we're stuck with templates and manual customization. There's got to be a middle ground for affordable document automation."
                    },
                    {
                        "source": "legal_tech_blog",
                        "url": "local://legaltech_document_analysis",
                        "text": "The legal document automation market is bifurcated. Enterprise solutions offer comprehensive features but are prohibitively expensive for small and medium firms. Meanwhile, smaller firms rely on manual document preparation and basic templates. This creates an opportunity for mid-market solutions that offer core automation features at accessible price points."
                    }
                ],
                "ground_truth": {
                    "pains": [
                        {
                            "actor": "Small law firm partner",
                            "context": "Document preparation",
                            "problem": "Manual document preparation is time-consuming and error-prone",
                            "severity": 4
                        },
                        {
                            "actor": "Law firm associate",
                            "context": "Technology adoption",
                            "problem": "Enterprise document automation too expensive for small firms",
                            "severity": 4
                        },
                        {
                            "actor": "Legal operations manager",
                            "context": "Firm efficiency",
                            "problem": "Lack of middle-ground solutions between basic templates and enterprise systems",
                            "severity": 3
                        }
                    ],
                    "clusters": [
                        {
                            "label": "Document Automation",
                            "pain_ids": [0, 1]
                        },
                        {
                            "label": "Market Gap",
                            "pain_ids": [2]
                        }
                    ],
                    "competitors": [
                        {
                            "name": "HotDocs",
                            "positioning": "Enterprise document automation",
                            "pricing": "$500+ per user per month"
                        },
                        {
                            "name": "LawGeex",
                            "positioning": "AI-powered legal document review",
                            "pricing": "$150-500 per month per firm"
                        },
                        {
                            "name": "Rocket Lawyer",
                            "positioning": "Legal document templates and services",
                            "pricing": "$39.99 per month for business"
                        }
                    ],
                    "best_opportunity": {
                        "title": "Mid-Market Legal Document Automation",
                        "reason": "Clear gap between enterprise solutions and basic templates"
                    },
                    "decision": "PASS",
                    "confidence": 0.6
                }
            },
            {
                "id": "realistic_005",
                "topic": "Manufacturing Quality Control",
                "documents": [
                    {
                        "source": "manufacturing_forum",
                        "url": "local://manufacturing_quality_control",
                        "text": "Quality control manager at mid-sized manufacturer. We're still doing too much quality inspection manually - visual checks, measurements, documentation. This leads to inconsistencies, human error, and slow feedback to production. The big automation systems are designed for huge plants and cost millions. We need something that works for our scale - maybe $50-100k range, not millions."
                    },
                    {
                        "source": "industry_report",
                        "url": "local://manufacturing_quality_trends",
                        "text": "Manufacturing quality control is undergoing digital transformation, but adoption is uneven. Large manufacturers invest heavily in automated inspection systems, while small to mid-sized manufacturers often rely on manual processes. This creates quality inconsistencies and competitive disadvantages. There's growing demand for scalable, affordable quality control solutions."
                    }
                ],
                "ground_truth": {
                    "pains": [
                        {
                            "actor": "Quality control manager",
                            "context": "Quality inspection processes",
                            "problem": "Manual quality inspection leads to inconsistencies and errors",
                            "severity": 4
                        },
                        {
                            "actor": "Manufacturing plant manager",
                            "context": "Technology investment",
                            "problem": "Automated quality control systems too expensive for mid-sized manufacturers",
                            "severity": 4
                        },
                        {
                            "actor": "Production supervisor",
                            "context": "Process improvement",
                            "problem": "Slow feedback loop between quality issues and production corrections",
                            "severity": 3
                        }
                    ],
                    "clusters": [
                        {
                            "label": "Quality Automation",
                            "pain_ids": [0, 1]
                        },
                        {
                            "label": "Process Efficiency",
                            "pain_ids": [2]
                        }
                    ],
                    "competitors": [
                        {
                            "name": "Keyence",
                            "positioning": "Industrial automation and inspection systems",
                            "pricing": "$100,000+ per system"
                        },
                        {
                            "name": "Cognex",
                            "positioning": "Machine vision and industrial sensors",
                            "pricing": "$50,000-500,000 per installation"
                        },
                        {
                            "name": "QualityLine",
                            "positioning": "Automated quality control for manufacturing",
                            "pricing": "$75,000-250,000 per system"
                        }
                    ],
                    "best_opportunity": {
                        "title": "Affordable Quality Control Automation",
                        "reason": "Strong market need for mid-priced quality automation solutions"
                    },
                    "decision": "ABORT",
                    "confidence": 0.3
                }
            }
        ]
    
    def get_schema(self) -> Dict:
        """Get dataset schema."""
        return {
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "topic": {"type": "string"},
                "documents": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "source": {"type": "string"},
                            "url": {"type": "string"},
                            "text": {"type": "string"}
                        }
                    }
                },
                "ground_truth": {
                    "type": "object",
                    "properties": {
                        "pains": {"type": "array"},
                        "clusters": {"type": "array"},
                        "competitors": {"type": "array"},
                        "best_opportunity": {"type": "object"},
                        "decision": {"type": "string"},
                        "confidence": {"type": "number"}
                    }
                }
            }
        }
