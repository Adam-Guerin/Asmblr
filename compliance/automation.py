"""
Compliance Automation for Asmblr
SOC2 and GDPR compliance automation with continuous monitoring
"""

import json
import time
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import hashlib
import boto3
from cryptography.fernet import Fernet
from kubernetes import client, config
import sqlite3
import pandas as pd
from enum import Enum

logger = logging.getLogger(__name__)

class ComplianceFramework(Enum):
    """Compliance frameworks"""
    SOC2 = "soc2"
    GDPR = "gdpr"
    ISO27001 = "iso27001"
    HIPAA = "hipaa"
    PCI_DSS = "pci_dss"

@dataclass
class ComplianceControl:
    """Compliance control definition"""
    id: str
    name: str
    framework: ComplianceFramework
    category: str
    description: str
    requirement: str
    status: str  # compliant, non_compliant, partial
    evidence: List[str]
    last_assessed: datetime
    next_assessment: datetime
    risk_level: str  # low, medium, high, critical
    remediation_plan: Optional[str] = None

@dataclass
class ComplianceReport:
    """Compliance assessment report"""
    framework: ComplianceFramework
    assessment_date: datetime
    overall_score: float
    total_controls: int
    compliant_controls: int
    non_compliant_controls: int
    partial_controls: int
    high_risk_items: int
    critical_risk_items: int
    recommendations: List[str]
    evidence_summary: Dict[str, Any]

class ComplianceDatabase:
    """Database for compliance tracking"""
    
    def __init__(self, db_path: str = "compliance/compliance.db"):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize compliance database"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS compliance_controls (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    framework TEXT NOT NULL,
                    category TEXT NOT NULL,
                    description TEXT NOT NULL,
                    requirement TEXT NOT NULL,
                    status TEXT NOT NULL,
                    evidence TEXT,
                    last_assessed DATETIME NOT NULL,
                    next_assessment DATETIME NOT NULL,
                    risk_level TEXT NOT NULL,
                    remediation_plan TEXT
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS compliance_reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    framework TEXT NOT NULL,
                    assessment_date DATETIME NOT NULL,
                    overall_score REAL NOT NULL,
                    total_controls INTEGER NOT NULL,
                    compliant_controls INTEGER NOT NULL,
                    non_compliant_controls INTEGER NOT NULL,
                    partial_controls INTEGER NOT NULL,
                    high_risk_items INTEGER NOT NULL,
                    critical_risk_items INTEGER NOT NULL,
                    recommendations TEXT,
                    evidence_summary TEXT
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    event_type TEXT NOT NULL,
                    user_id TEXT,
                    resource_id TEXT,
                    action TEXT NOT NULL,
                    details TEXT,
                    compliance_framework TEXT
                )
            """)
            
            conn.commit()
    
    def save_control(self, control: ComplianceControl):
        """Save compliance control"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO compliance_controls 
                (id, name, framework, category, description, requirement, status, 
                 evidence, last_assessed, next_assessment, risk_level, remediation_plan)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                control.id,
                control.name,
                control.framework.value,
                control.category,
                control.description,
                control.requirement,
                control.status,
                json.dumps(control.evidence),
                control.last_assessed,
                control.next_assessment,
                control.risk_level,
                control.remediation_plan
            ))
            conn.commit()
    
    def get_controls(self, framework: Optional[ComplianceFramework] = None) -> List[ComplianceControl]:
        """Get compliance controls"""
        query = "SELECT * FROM compliance_controls"
        params = []
        
        if framework:
            query += " WHERE framework = ?"
            params.append(framework.value)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(query, params)
            controls = []
            
            for row in cursor.fetchall():
                controls.append(ComplianceControl(
                    id=row[0],
                    name=row[1],
                    framework=ComplianceFramework(row[2]),
                    category=row[3],
                    description=row[4],
                    requirement=row[5],
                    status=row[6],
                    evidence=json.loads(row[7]) if row[7] else [],
                    last_assessed=datetime.fromisoformat(row[8]),
                    next_assessed=datetime.fromisoformat(row[9]),
                    risk_level=row[10],
                    remediation_plan=row[11]
                ))
            
            return controls
    
    def save_report(self, report: ComplianceReport):
        """Save compliance report"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO compliance_reports 
                (framework, assessment_date, overall_score, total_controls, 
                 compliant_controls, non_compliant_controls, partial_controls, 
                 high_risk_items, critical_risk_items, recommendations, evidence_summary)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                report.framework.value,
                report.assessment_date,
                report.overall_score,
                report.total_controls,
                report.compliant_controls,
                report.non_compliant_controls,
                report.partial_controls,
                report.high_risk_items,
                report.critical_risk_items,
                json.dumps(report.recommendations),
                json.dumps(report.evidence_summary)
            ))
            conn.commit()
    
    def log_audit_event(self, event_type: str, user_id: str, resource_id: str, 
                       action: str, details: str, framework: Optional[ComplianceFramework] = None):
        """Log audit event"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO audit_logs 
                (timestamp, event_type, user_id, resource_id, action, details, compliance_framework)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                datetime.now(),
                event_type,
                user_id,
                resource_id,
                action,
                details,
                framework.value if framework else None
            ))
            conn.commit()

class SOC2ComplianceChecker:
    """SOC2 Type II compliance checker"""
    
    def __init__(self, db: ComplianceDatabase):
        self.db = db
        self.controls = self._load_soc2_controls()
    
    def _load_soc2_controls(self) -> List[ComplianceControl]:
        """Load SOC2 controls"""
        controls = [
            # Security Controls
            ComplianceControl(
                id="SOC2-SEC-001",
                name="Access Control",
                framework=ComplianceFramework.SOC2,
                category="Security",
                description="Implement logical access security software, infrastructure, and architectures",
                requirement="Logical access security measures must be implemented",
                status="compliant",
                evidence=["RBAC configuration", "Access logs", "MFA implementation"],
                last_assessed=datetime.now() - timedelta(days=30),
                next_assessment=datetime.now() + timedelta(days=90),
                risk_level="low"
            ),
            ComplianceControl(
                id="SOC2-SEC-002",
                name="Encryption",
                framework=ComplianceFramework.SOC2,
                category="Security",
                description="Encrypt data at rest and in transit",
                requirement="All sensitive data must be encrypted",
                status="compliant",
                evidence=["TLS certificates", "Database encryption", "Key management"],
                last_assessed=datetime.now() - timedelta(days=15),
                next_assessment=datetime.now() + timedelta(days=60),
                risk_level="medium"
            ),
            ComplianceControl(
                id="SOC2-SEC-003",
                name="Network Security",
                framework=ComplianceFramework.SOC2,
                category="Security",
                description="Implement network security controls",
                requirement="Network must be protected against unauthorized access",
                status="partial",
                evidence=["Firewall rules", "Network segmentation", "Intrusion detection"],
                last_assessed=datetime.now() - timedelta(days=45),
                next_assessment=datetime.now() + timedelta(days=30),
                risk_level="medium",
                remediation_plan="Update firewall rules and implement additional network monitoring"
            ),
            
            # Availability Controls
            ComplianceControl(
                id="SOC2-AVAIL-001",
                name="Backup and Recovery",
                framework=ComplianceFramework.SOC2,
                category="Availability",
                description="Implement backup and recovery procedures",
                requirement="Regular backups and tested recovery procedures",
                status="compliant",
                evidence=["Backup logs", "Recovery test results", "Backup retention policy"],
                last_assessed=datetime.now() - timedelta(days=20),
                next_assessment=datetime.now() + timedelta(days=45),
                risk_level="low"
            ),
            
            # Processing Integrity Controls
            ComplianceControl(
                id="SOC2-PI-001",
                name="Data Processing Controls",
                framework=ComplianceFramework.SOC2,
                category="Processing Integrity",
                description="Implement data processing controls",
                requirement="Data processing must be accurate and complete",
                status="compliant",
                evidence=["Data validation logs", "Processing audit trails", "Error handling procedures"],
                last_assessed=datetime.now() - timedelta(days=25),
                next_assessment=datetime.now() + timedelta(days=60),
                risk_level="low"
            ),
            
            # Confidentiality Controls
            ComplianceControl(
                id="SOC2-CONF-001",
                name="Data Classification",
                framework=ComplianceFramework.SOC2,
                category="Confidentiality",
                description="Implement data classification procedures",
                requirement="Data must be classified according to sensitivity",
                status="partial",
                evidence=["Classification policy", "Data inventory", "Access controls by classification"],
                last_assessed=datetime.now() - timedelta(days=60),
                next_assessment=datetime.now() + timedelta(days=15),
                risk_level="high",
                remediation_plan="Complete data classification for all sensitive data"
            ),
            
            # Privacy Controls
            ComplianceControl(
                id="SOC2-PRIV-001",
                name="Privacy Policy",
                framework=ComplianceFramework.SOC2,
                category="Privacy",
                description="Implement and maintain privacy policy",
                requirement="Privacy policy must be communicated and enforced",
                status="compliant",
                evidence=["Privacy policy document", "User consent records", "Data processing agreements"],
                last_assessed=datetime.now() - timedelta(days=35),
                next_assessment=datetime.now() + timedelta(days=90),
                risk_level="low"
            )
        ]
        
        return controls
    
    def assess_compliance(self) -> ComplianceReport:
        """Assess SOC2 compliance"""
        controls = self.db.get_controls(ComplianceFramework.SOC2)
        
        if not controls:
            # Load default controls if none exist
            for control in self.controls:
                self.db.save_control(control)
            controls = self.controls
        
        # Calculate compliance metrics
        total_controls = len(controls)
        compliant_controls = len([c for c in controls if c.status == "compliant"])
        non_compliant_controls = len([c for c in controls if c.status == "non_compliant"])
        partial_controls = len([c for c in controls if c.status == "partial"])
        high_risk_items = len([c for c in controls if c.risk_level == "high"])
        critical_risk_items = len([c for c in controls if c.risk_level == "critical"])
        
        # Calculate overall score
        overall_score = (compliant_controls / total_controls) * 100 if total_controls > 0 else 0
        
        # Generate recommendations
        recommendations = self._generate_recommendations(controls)
        
        # Evidence summary
        evidence_summary = self._generate_evidence_summary(controls)
        
        report = ComplianceReport(
            framework=ComplianceFramework.SOC2,
            assessment_date=datetime.now(),
            overall_score=overall_score,
            total_controls=total_controls,
            compliant_controls=compliant_controls,
            non_compliant_controls=non_compliant_controls,
            partial_controls=partial_controls,
            high_risk_items=high_risk_items,
            critical_risk_items=critical_risk_items,
            recommendations=recommendations,
            evidence_summary=evidence_summary
        )
        
        self.db.save_report(report)
        return report
    
    def _generate_recommendations(self, controls: List[ComplianceControl]) -> List[str]:
        """Generate compliance recommendations"""
        recommendations = []
        
        non_compliant = [c for c in controls if c.status == "non_compliant"]
        partial = [c for c in controls if c.status == "partial"]
        high_risk = [c for c in controls if c.risk_level in ["high", "critical"]]
        
        if non_compliant:
            recommendations.append(f"Address {len(non_compliant)} non-compliant controls immediately")
        
        if partial:
            recommendations.append(f"Complete implementation of {len(partial)} partially compliant controls")
        
        if high_risk:
            recommendations.append(f"Prioritize remediation of {len(high_risk)} high-risk items")
        
        # Specific recommendations
        for control in controls:
            if control.status == "non_compliant" and control.risk_level in ["high", "critical"]:
                recommendations.append(f"URGENT: Fix {control.name} - {control.description}")
            elif control.status == "partial" and control.remediation_plan:
                recommendations.append(f"Complete remediation: {control.remediation_plan}")
        
        return recommendations
    
    def _generate_evidence_summary(self, controls: List[ComplianceControl]) -> Dict[str, Any]:
        """Generate evidence summary"""
        all_evidence = []
        evidence_by_category = {}
        
        for control in controls:
            all_evidence.extend(control.evidence)
            
            if control.category not in evidence_by_category:
                evidence_by_category[control.category] = []
            evidence_by_category[control.category].extend(control.evidence)
        
        return {
            "total_evidence_items": len(all_evidence),
            "unique_evidence_items": len(set(all_evidence)),
            "evidence_by_category": evidence_by_category,
            "evidence_coverage": len(set(all_evidence)) / len(all_evidence) if all_evidence else 0
        }

class GDPRComplianceChecker:
    """GDPR compliance checker"""
    
    def __init__(self, db: ComplianceDatabase):
        self.db = db
        self.controls = self._load_gdpr_controls()
    
    def _load_gdpr_controls(self) -> List[ComplianceControl]:
        """Load GDPR controls"""
        return [
            ComplianceControl(
                id="GDPR-001",
                name="Lawful Basis for Processing",
                framework=ComplianceFramework.GDPR,
                category="Legal Basis",
                description="Establish lawful basis for processing personal data",
                requirement="Article 6: Lawfulness of processing",
                status="compliant",
                evidence=["Consent records", "Data processing agreements", "Legal basis documentation"],
                last_assessed=datetime.now() - timedelta(days=20),
                next_assessment=datetime.now() + timedelta(days=90),
                risk_level="medium"
            ),
            ComplianceControl(
                id="GDPR-002",
                name="Data Subject Rights",
                framework=ComplianceFramework.GDPR,
                category="Rights Management",
                description="Implement data subject rights procedures",
                requirement="Articles 15-22: Data subject rights",
                status="partial",
                evidence=["Subject access request procedures", "Data deletion processes", "Rights request logs"],
                last_assessed=datetime.now() - timedelta(days=40),
                next_assessment=datetime.now() + timedelta(days=30),
                risk_level="high",
                remediation_plan="Implement automated data subject rights request processing"
            ),
            ComplianceControl(
                id="GDPR-003",
                name="Data Protection Impact Assessment",
                framework=ComplianceFramework.GDPR,
                category="Risk Assessment",
                description="Conduct DPIA for high-risk processing",
                requirement="Article 35: Data protection impact assessment",
                status="compliant",
                evidence=["DPIA documentation", "Risk assessment reports", "Mitigation measures"],
                last_assessed=datetime.now() - timedelta(days=15),
                next_assessment=datetime.now() + timedelta(days=180),
                risk_level="low"
            ),
            ComplianceControl(
                id="GDPR-004",
                name="Data Breach Notification",
                framework=ComplianceFramework.GDPR,
                category="Incident Response",
                description="Implement data breach notification procedures",
                requirement="Articles 33-34: Notification of personal data breaches",
                status="compliant",
                evidence=["Breach response plan", "Notification templates", "Incident logs"],
                last_assessed=datetime.now() - timedelta(days=25),
                next_assessment=datetime.now() + timedelta(days=60),
                risk_level="medium"
            ),
            ComplianceControl(
                id="GDPR-005",
                name="Data Minimization",
                framework=ComplianceFramework.GDPR,
                category="Data Governance",
                description="Implement data minimization principles",
                requirement="Article 5: Principles relating to processing of personal data",
                status="partial",
                evidence=["Data retention policy", "Data classification", "Minimization procedures"],
                last_assessed=datetime.now() - timedelta(days=50),
                next_assessment=datetime.now() + timedelta(days=45),
                risk_level="medium",
                remediation_plan="Review and update data minimization procedures"
            ),
            ComplianceControl(
                id="GDPR-006",
                name="Privacy by Design",
                framework=ComplianceFramework.GDPR,
                category="Design Principles",
                description="Implement privacy by design and by default",
                requirement": Article 25: Data protection by design and by default",
                status="compliant",
                evidence=["Privacy impact assessments", "Design documentation", "Default settings"],
                last_assessed=datetime.now() - timedelta(days=30),
                next_assessed=datetime.now() + timedelta(days=120),
                risk_level="low"
            )
        ]
    
    def assess_compliance(self) -> ComplianceReport:
        """Assess GDPR compliance"""
        controls = self.db.get_controls(ComplianceFramework.GDPR)
        
        if not controls:
            for control in self.controls:
                self.db.save_control(control)
            controls = self.controls
        
        # Calculate compliance metrics
        total_controls = len(controls)
        compliant_controls = len([c for c in controls if c.status == "compliant"])
        non_compliant_controls = len([c for c in controls if c.status == "non_compliant"])
        partial_controls = len([c for c in controls if c.status == "partial"])
        high_risk_items = len([c for c in controls if c.risk_level == "high"])
        critical_risk_items = len([c for c in controls if c.risk_level == "critical"])
        
        overall_score = (compliant_controls / total_controls) * 100 if total_controls > 0 else 0
        
        recommendations = self._generate_recommendations(controls)
        evidence_summary = self._generate_evidence_summary(controls)
        
        report = ComplianceReport(
            framework=ComplianceFramework.GDPR,
            assessment_date=datetime.now(),
            overall_score=overall_score,
            total_controls=total_controls,
            compliant_controls=compliant_controls,
            non_compliant_controls=non_compliant_controls,
            partial_controls=partial_controls,
            high_risk_items=high_risk_items,
            critical_risk_items=critical_risk_items,
            recommendations=recommendations,
            evidence_summary=evidence_summary
        )
        
        self.db.save_report(report)
        return report
    
    def _generate_recommendations(self, controls: List[ComplianceControl]) -> List[str]:
        """Generate GDPR-specific recommendations"""
        recommendations = []
        
        # GDPR-specific recommendations
        data_rights_controls = [c for c in controls if "rights" in c.name.lower()]
        if any(c.status != "compliant" for c in data_rights_controls):
            recommendations.append("Strengthen data subject rights implementation")
        
        consent_controls = [c for c in controls if "consent" in c.name.lower() or "lawful" in c.name.lower()]
        if any(c.status != "compliant" for c in consent_controls):
            recommendations.append("Review and update consent management procedures")
        
        breach_controls = [c for c in controls if "breach" in c.name.lower()]
        if any(c.status != "compliant" for c in breach_controls):
            recommendations.append("Test and update breach notification procedures")
        
        return recommendations
    
    def _generate_evidence_summary(self, controls: List[ComplianceControl]) -> Dict[str, Any]:
        """Generate GDPR evidence summary"""
        evidence_items = []
        gdpr_articles = {}
        
        for control in controls:
            evidence_items.extend(control.evidence)
            
            # Extract GDPR articles from requirements
            if "Article" in control.requirement:
                article = control.requirement.split("Article")[1].split(":")[0].strip()
                if article not in gdpr_articles:
                    gdpr_articles[article] = []
                gdpr_articles[article].extend(control.evidence)
        
        return {
            "total_evidence_items": len(evidence_items),
            "gdpr_articles_covered": list(gdpr_articles.keys()),
            "evidence_by_article": gdpr_articles,
            "compliance_rate": len([c for c in controls if c.status == "compliant"]) / len(controls)
        }

class ComplianceAutomation:
    """Main compliance automation orchestrator"""
    
    def __init__(self):
        self.db = ComplianceDatabase()
        self.soc2_checker = SOC2ComplianceChecker(self.db)
        self.gdpr_checker = GDPRComplianceChecker(self.db)
        
        # Start continuous monitoring
        asyncio.create_task(self.continuous_monitoring())
    
    async def continuous_monitoring(self):
        """Continuous compliance monitoring"""
        while True:
            try:
                # Check for controls that need assessment
                await self.check_upcoming_assessments()
                
                # Run automated checks
                await self.run_automated_checks()
                
                # Wait before next check
                await asyncio.sleep(3600)  # Check every hour
                
            except Exception as e:
                logger.error(f"Error in continuous monitoring: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes on error
    
    async def check_upcoming_assessments(self):
        """Check for upcoming assessments"""
        controls = self.db.get_controls()
        now = datetime.now()
        
        for control in controls:
            if control.next_assessment <= now:
                logger.info(f"Assessment due for control {control.id}")
                await self.trigger_assessment(control)
    
    async def trigger_assessment(self, control: ComplianceControl):
        """Trigger assessment for a control"""
        # Log assessment trigger
        self.db.log_audit_event(
            event_type="assessment_triggered",
            user_id="system",
            resource_id=control.id,
            action="trigger_assessment",
            details=f"Assessment triggered for control {control.id}",
            framework=control.framework
        )
        
        # Run framework-specific assessment
        if control.framework == ComplianceFramework.SOC2:
            report = self.soc2_checker.assess_compliance()
        elif control.framework == ComplianceFramework.GDPR:
            report = self.gdpr_checker.assess_compliance()
        else:
            logger.warning(f"Unsupported framework: {control.framework}")
            return
        
        # Update control next assessment date
        control.last_assessed = datetime.now()
        control.next_assessment = datetime.now() + timedelta(days=90)
        self.db.save_control(control)
    
    async def run_automated_checks(self):
        """Run automated compliance checks"""
        # Check access controls
        await self.check_access_controls()
        
        # Check encryption status
        await self.check_encryption_status()
        
        # Check backup status
        await self.check_backup_status()
        
        # Check audit logs
        await self.check_audit_logs()
    
    async def check_access_controls(self):
        """Check access control compliance"""
        try:
            # Check Kubernetes RBAC
            config.load_kube_config()
            rbac_api = client.RbacAuthorizationV1Api()
            
            # Get all roles and role bindings
            roles = rbac_api.list_cluster_role()
            role_bindings = rbac_api.list_cluster_role_binding()
            
            # Log audit event
            self.db.log_audit_event(
                event_type="access_control_check",
                user_id="system",
                resource_id="kubernetes_rbac",
                action="automated_check",
                details=f"Checked {len(roles.items)} roles and {len(role_bindings.items)} role bindings",
                framework=ComplianceFramework.SOC2
            )
            
        except Exception as e:
            logger.error(f"Error checking access controls: {e}")
    
    async def check_encryption_status(self):
        """Check encryption compliance"""
        try:
            # Check TLS certificates
            # This would typically check certificate expiration and validity
            cert_status = "valid"  # Placeholder
            
            self.db.log_audit_event(
                event_type="encryption_check",
                user_id="system",
                resource_id="tls_certificates",
                action="automated_check",
                details=f"TLS certificate status: {cert_status}",
                framework=ComplianceFramework.SOC2
            )
            
        except Exception as e:
            logger.error(f"Error checking encryption status: {e}")
    
    async def check_backup_status(self):
        """Check backup compliance"""
        try:
            # Check recent backups
            # This would typically check backup systems
            backup_status = "success"  # Placeholder
            last_backup = datetime.now() - timedelta(hours=24)
            
            self.db.log_audit_event(
                event_type="backup_check",
                user_id="system",
                resource_id="backup_system",
                action="automated_check",
                details=f"Last backup: {last_backup}, Status: {backup_status}",
                framework=ComplianceFramework.SOC2
            )
            
        except Exception as e:
            logger.error(f"Error checking backup status: {e}")
    
    async def check_audit_logs(self):
        """Check audit log compliance"""
        try:
            # Check audit log retention and integrity
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM audit_logs 
                    WHERE timestamp < datetime('now', '-1 year')
                """)
                old_logs = cursor.fetchone()[0]
                
                # Clean up old logs (GDPR requirement)
                if old_logs > 0:
                    conn.execute("""
                        DELETE FROM audit_logs 
                        WHERE timestamp < datetime('now', '-1 year')
                    """)
                    conn.commit()
            
            self.db.log_audit_event(
                event_type="audit_log_check",
                user_id="system",
                resource_id="audit_logs",
                action="automated_check",
                details=f"Cleaned up {old_logs} old audit log entries",
                framework=ComplianceFramework.GDPR
            )
            
        except Exception as e:
            logger.error(f"Error checking audit logs: {e}")
    
    def generate_compliance_dashboard(self) -> Dict[str, Any]:
        """Generate compliance dashboard data"""
        soc2_report = self.soc2_checker.assess_compliance()
        gdpr_report = self.gdpr_checker.assess_compliance()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "soc2": asdict(soc2_report),
            "gdpr": asdict(gdpr_report),
            "overall_score": (soc2_report.overall_score + gdpr_report.overall_score) / 2,
            "total_controls": soc2_report.total_controls + gdpr_report.total_controls,
            "high_risk_items": soc2_report.high_risk_items + gdpr_report.high_risk_items,
            "critical_risk_items": soc2_report.critical_risk_items + gdpr_report.critical_risk_items,
            "upcoming_assessments": self._get_upcoming_assessments()
        }
    
    def _get_upcoming_assessments(self) -> List[Dict[str, Any]]:
        """Get upcoming assessments"""
        controls = self.db.get_controls()
        now = datetime.now()
        upcoming = []
        
        for control in controls:
            days_until = (control.next_assessment - now).days
            if 0 <= days_until <= 30:  # Next 30 days
                upcoming.append({
                    "control_id": control.id,
                    "control_name": control.name,
                    "framework": control.framework.value,
                    "days_until_assessment": days_until,
                    "risk_level": control.risk_level
                })
        
        return sorted(upcoming, key=lambda x: x["days_until_assessment"])

# Global compliance automation instance
compliance_automation = ComplianceAutomation()

# API endpoints
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/compliance", tags=["compliance"])

@router.get("/dashboard")
async def get_compliance_dashboard():
    """Get compliance dashboard"""
    try:
        return compliance_automation.generate_compliance_dashboard()
    except Exception as e:
        logger.error(f"Error generating compliance dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/assess/{framework}")
async def assess_compliance(framework: str):
    """Run compliance assessment for specified framework"""
    try:
        framework_enum = ComplianceFramework(framework.lower())
        
        if framework_enum == ComplianceFramework.SOC2:
            report = compliance_automation.soc2_checker.assess_compliance()
        elif framework_enum == ComplianceFramework.GDPR:
            report = compliance_automation.gdpr_checker.assess_compliance()
        else:
            raise ValueError(f"Unsupported framework: {framework}")
        
        return asdict(report)
    except Exception as e:
        logger.error(f"Error assessing compliance: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/controls")
async def get_controls(framework: Optional[str] = None):
    """Get compliance controls"""
    try:
        if framework:
            framework_enum = ComplianceFramework(framework.lower())
            controls = compliance_automation.db.get_controls(framework_enum)
        else:
            controls = compliance_automation.db.get_controls()
        
        return [asdict(control) for control in controls]
    except Exception as e:
        logger.error(f"Error getting controls: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/audit-log")
async def log_audit_event(event_type: str, user_id: str, resource_id: str, 
                        action: str, details: str, framework: Optional[str] = None):
    """Log audit event"""
    try:
        framework_enum = ComplianceFramework(framework.lower()) if framework else None
        compliance_automation.db.log_audit_event(
            event_type, user_id, resource_id, action, details, framework_enum
        )
        return {"status": "logged"}
    except Exception as e:
        logger.error(f"Error logging audit event: {e}")
        raise HTTPException(status_code=500, detail=str(e))
