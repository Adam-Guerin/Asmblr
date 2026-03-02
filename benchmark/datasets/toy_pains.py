"""
Toy pains dataset - small, hand-labeled dataset for testing and development.
"""

import json
from pathlib import Path
from typing import List, Dict, Optional


class ToyPainsDataset:
    """Small hand-labeled dataset with clear ground truth for testing."""
    
    has_ground_truth = True
    size = 10
    
    def __init__(self, custom_path: Optional[str] = None):
        self.custom_path = custom_path
        self.data = None
    
    def load(self) -> List[Dict]:
        """Load the toy pains dataset."""
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
        """Get built-in toy dataset."""
        return [
            {
                "id": "toy_001",
                "topic": "Small Business Inventory Management",
                "documents": [
                    {
                        "source": "reddit",
                        "url": "local://reddit_smallbiz_inventory",
                        "text": "I run a small retail shop and keeping track of inventory is a nightmare. I'm using spreadsheets but constantly making mistakes. When items run out, I lose sales. When I overorder, I tie up cash. There must be a better way for small businesses to manage inventory without spending thousands on enterprise software."
                    },
                    {
                        "source": "forum",
                        "url": "local://forum_inventory_problems",
                        "text": "Small business owner here. The biggest pain point is inventory management. Current solutions are either too expensive or too complicated. I need something simple that can track products, alert when stock is low, and handle basic ordering. Integration with accounting would be nice but not essential."
                    }
                ],
                "ground_truth": {
                    "pains": [
                        {
                            "actor": "Small business owner",
                            "context": "Retail shop management",
                            "problem": "Inventory tracking using spreadsheets leads to errors and lost sales",
                            "severity": 4
                        },
                        {
                            "actor": "Small business owner", 
                            "context": "Inventory management",
                            "problem": "Enterprise software too expensive and complicated",
                            "severity": 3
                        }
                    ],
                    "clusters": [
                        {
                            "label": "Inventory Management Issues",
                            "pain_ids": [0, 1]
                        }
                    ],
                    "competitors": [
                        {
                            "name": "QuickBooks",
                            "positioning": "Comprehensive accounting and inventory for small business",
                            "pricing": "$25/month + setup fees"
                        },
                        {
                            "name": "Shopify",
                            "positioning": "E-commerce platform with inventory management",
                            "pricing": "$29/month basic plan"
                        }
                    ],
                    "best_opportunity": {
                        "title": "Simple Inventory Management for Small Retail",
                        "reason": "Clear unmet need for affordable, simple inventory solution"
                    },
                    "decision": "PASS",
                    "confidence": 0.8
                }
            },
            {
                "id": "toy_002", 
                "topic": "Freelancer Time Tracking",
                "documents": [
                    {
                        "source": "reddit",
                        "url": "local://reddit_freelancer_time",
                        "text": "As a freelancer, tracking time across multiple projects is painful. I forget to start timers, lose track of billable hours, and spend hours each month on invoicing. Existing tools either focus on employee time tracking or are too complex for solo freelancers."
                    }
                ],
                "ground_truth": {
                    "pains": [
                        {
                            "actor": "Freelancer",
                            "context": "Project management and billing",
                            "problem": "Forgetting to track time leads to lost billable hours",
                            "severity": 4
                        },
                        {
                            "actor": "Freelancer",
                            "context": "Administrative tasks", 
                            "problem": "Current time tracking tools too complex for solo use",
                            "severity": 3
                        }
                    ],
                    "clusters": [
                        {
                            "label": "Time Tracking Pain",
                            "pain_ids": [0, 1]
                        }
                    ],
                    "competitors": [
                        {
                            "name": "Toggl",
                            "positioning": "Simple time tracking for teams and individuals",
                            "pricing": "$10/month per user"
                        },
                        {
                            "name": "Harvest",
                            "positioning": "Time tracking and invoicing for businesses",
                            "pricing": "$12/month per person"
                        }
                    ],
                    "best_opportunity": {
                        "title": "Freelancer-First Time Tracking",
                        "reason": "Gap in market for simple solo freelancer time tracking"
                    },
                    "decision": "PASS",
                    "confidence": 0.7
                }
            },
            {
                "id": "toy_003",
                "topic": "Restaurant Staff Scheduling",
                "documents": [
                    {
                        "source": "forum",
                        "url": "local://forum_restaurant_scheduling",
                        "text": "Restaurant manager here. Scheduling staff is a weekly nightmare. I have to juggle availability, time-off requests, labor costs, and fair distribution. Current scheduling software is either too expensive or doesn't handle our specific needs like split shifts and tip sharing calculations."
                    }
                ],
                "ground_truth": {
                    "pains": [
                        {
                            "actor": "Restaurant manager",
                            "context": "Staff scheduling and labor management",
                            "problem": "Complex scheduling requirements not met by existing tools",
                            "severity": 4
                        },
                        {
                            "actor": "Restaurant manager",
                            "context": "Budget management",
                            "problem": "Scheduling software too expensive for small restaurants",
                            "severity": 3
                        }
                    ],
                    "clusters": [
                        {
                            "label": "Scheduling Complexity",
                            "pain_ids": [0, 1]
                        }
                    ],
                    "competitors": [
                        {
                            "name": "7shifts",
                            "positioning": "Restaurant scheduling and labor management",
                            "pricing": "$40/month per location"
                        },
                        {
                            "name": "Homebase",
                            "positioning": "Employee scheduling and time tracking",
                            "pricing": "$20/month per location"
                        }
                    ],
                    "best_opportunity": {
                        "title": "Affordable Restaurant Scheduling",
                        "reason": "Market need for cost-effective scheduling solution"
                    },
                    "decision": "KILL",
                    "confidence": 0.4
                }
            },
            {
                "id": "toy_004",
                "topic": "Student Study Group Coordination",
                "documents": [
                    {
                        "source": "reddit",
                        "url": "local://reddit_study_groups",
                        "text": "Trying to coordinate study groups for college courses is impossible. Everyone has different schedules, different learning styles, and different commitment levels. We try using WhatsApp and Discord but important messages get lost. Nobody wants to pay for coordination tools when we're already broke students."
                    }
                ],
                "ground_truth": {
                    "pains": [
                        {
                            "actor": "College student",
                            "context": "Academic collaboration",
                            "problem": "Difficulty coordinating study groups across different schedules",
                            "severity": 3
                        },
                        {
                            "actor": "College student",
                            "context": "Communication tools",
                            "problem": "Free messaging apps not optimized for study coordination",
                            "severity": 2
                        }
                    ],
                    "clusters": [
                        {
                            "label": "Study Group Coordination",
                            "pain_ids": [0, 1]
                        }
                    ],
                    "competitors": [
                        {
                            "name": "Discord",
                            "positioning": "Communication platform with some organization features",
                            "pricing": "Free with paid Nitro upgrades"
                        },
                        {
                            "name": "Slack",
                            "positioning": "Team communication and collaboration",
                            "pricing": "Free tier with paid plans"
                        }
                    ],
                    "best_opportunity": {
                        "title": "Student Study Group Platform",
                        "reason": "Students unwilling to pay makes business model challenging"
                    },
                    "decision": "ABORT",
                    "confidence": 0.3
                }
            },
            {
                "id": "toy_005",
                "topic": "Gym Member Engagement",
                "documents": [
                    {
                        "source": "forum",
                        "url": "local://forum_gym_engagement",
                        "text": "I run a small gym and keeping members engaged beyond January is tough. People sign up with good intentions but stop coming after a few weeks. We need better ways to track progress, create community, and motivate continued attendance without being annoying."
                    }
                ],
                "ground_truth": {
                    "pains": [
                        {
                            "actor": "Gym owner",
                            "context": "Member retention and engagement",
                            "problem": "High member dropout after initial motivation fades",
                            "severity": 4
                        },
                        {
                            "actor": "Gym member",
                            "context": "Fitness motivation",
                            "problem": "Lack of progress tracking and community support",
                            "severity": 3
                        }
                    ],
                    "clusters": [
                        {
                            "label": "Member Engagement",
                            "pain_ids": [0, 1]
                        }
                    ],
                    "competitors": [
                        {
                            "name": "MyFitnessPal",
                            "positioning": "Calorie tracking and basic fitness logging",
                            "pricing": "Free with Premium at $9.99/month"
                        },
                        {
                            "name": "Strava",
                            "positioning": "Social fitness tracking and challenges",
                            "pricing": "Free with Summit at $7.99/month"
                        }
                    ],
                    "best_opportunity": {
                        "title": "Gym Member Engagement Platform",
                        "reason": "Clear need for better member retention tools"
                    },
                    "decision": "PASS",
                    "confidence": 0.6
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
                        "pains": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "actor": {"type": "string"},
                                    "context": {"type": "string"},
                                    "problem": {"type": "string"},
                                    "severity": {"type": "integer", "minimum": 1, "maximum": 5}
                                }
                            }
                        },
                        "clusters": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "label": {"type": "string"},
                                    "pain_ids": {"type": "array", "items": {"type": "integer"}}
                                }
                            }
                        },
                        "competitors": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "positioning": {"type": "string"},
                                    "pricing": {"type": "string"}
                                }
                            }
                        },
                        "best_opportunity": {
                            "type": "object",
                            "properties": {
                                "title": {"type": "string"},
                                "reason": {"type": "string"}
                            }
                        },
                        "decision": {"type": "string", "enum": ["PASS", "KILL", "ABORT"]},
                        "confidence": {"type": "number", "minimum": 0, "maximum": 1}
                    }
                }
            }
        }
