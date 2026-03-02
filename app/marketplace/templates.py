"""
Template Marketplace for Asmblr
Pre-configured MVP templates with instant deployment
"""

import json
import logging
from datetime import datetime
from typing import Any
from dataclasses import dataclass, asdict
from pathlib import Path
from enum import Enum
import uuid
import shutil
import yaml

logger = logging.getLogger(__name__)

class TemplateCategory(Enum):
    """Template categories"""
    SAAS = "saas"
    MARKETPLACE = "marketplace"
    ECOMMERCE = "ecommerce"
    FINTECH = "fintech"
    HEALTHCARE = "healthcare"
    EDUCATION = "education"
    SOCIAL = "social"
    PRODUCTIVITY = "productivity"
    GAMING = "gaming"
    IOT = "iot"

class TemplateDifficulty(Enum):
    """Template difficulty levels"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"

class PricingModel(Enum):
    """Template pricing models"""
    FREE = "free"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"

@dataclass
class TemplateFeature:
    """Template feature"""
    name: str
    description: str
    included: bool
    category: str

@dataclass
class TemplateTech:
    """Template technology stack"""
    frontend: list[str]
    backend: list[str]
    database: list[str]
    deployment: list[str]
    integrations: list[str]

@dataclass
class TemplateMetrics:
    """Template metrics"""
    downloads: int
    rating: float
    reviews_count: int
    active_installs: int
    last_updated: datetime

@dataclass
class Template:
    """MVP template"""
    id: str
    name: str
    description: str
    category: TemplateCategory
    difficulty: TemplateDifficulty
    pricing: PricingModel
    author: str
    author_id: str
    version: str
    tags: list[str]
    features: list[TemplateFeature]
    tech_stack: TemplateTech
    screenshots: list[str]
    demo_url: str | None
    documentation_url: str | None
    support_url: str | None
    github_url: str | None
    metrics: TemplateMetrics
    created_at: datetime
    updated_at: datetime
    is_featured: bool = False
    is_verified: bool = False

class TemplateManager:
    """Template marketplace manager"""
    
    def __init__(self, templates_dir: str = "templates"):
        self.templates_dir = Path(templates_dir)
        self.templates_dir.mkdir(exist_ok=True)
        self.templates: dict[str, Template] = {}
        self.featured_templates: list[str] = []
        
        # Load existing templates
        self._load_templates()
        
        # Initialize default templates
        self._initialize_default_templates()
    
    def _load_templates(self):
        """Load existing templates from disk"""
        try:
            for template_dir in self.templates_dir.iterdir():
                if template_dir.is_dir():
                    metadata_file = template_dir / "template.yaml"
                    if metadata_file.exists():
                        with open(metadata_file) as f:
                            metadata = yaml.safe_load(f)
                        
                        template = self._create_template_from_metadata(metadata)
                        self.templates[template.id] = template
                        
                        if template.is_featured:
                            self.featured_templates.append(template.id)
            
            logger.info(f"Loaded {len(self.templates)} templates")
            
        except Exception as e:
            logger.error(f"Error loading templates: {e}")
    
    def _create_template_from_metadata(self, metadata: dict[str, Any]) -> Template:
        """Create template from metadata"""
        # Convert features
        features = []
        for feature_data in metadata.get("features", []):
            features.append(TemplateFeature(**feature_data))
        
        # Convert tech stack
        tech_data = metadata.get("tech_stack", {})
        tech_stack = TemplateTech(
            frontend=tech_data.get("frontend", []),
            backend=tech_data.get("backend", []),
            database=tech_data.get("database", []),
            deployment=tech_data.get("deployment", []),
            integrations=tech_data.get("integrations", [])
        )
        
        # Convert metrics
        metrics_data = metadata.get("metrics", {})
        metrics = TemplateMetrics(
            downloads=metrics_data.get("downloads", 0),
            rating=metrics_data.get("rating", 0.0),
            reviews_count=metrics_data.get("reviews_count", 0),
            active_installs=metrics_data.get("active_installs", 0),
            last_updated=datetime.fromisoformat(metrics_data.get("last_updated", datetime.now().isoformat()))
        )
        
        return Template(
            id=metadata["id"],
            name=metadata["name"],
            description=metadata["description"],
            category=TemplateCategory(metadata["category"]),
            difficulty=TemplateDifficulty(metadata["difficulty"]),
            pricing=PricingModel(metadata["pricing"]),
            author=metadata["author"],
            author_id=metadata["author_id"],
            version=metadata["version"],
            tags=metadata.get("tags", []),
            features=features,
            tech_stack=tech_stack,
            screenshots=metadata.get("screenshots", []),
            demo_url=metadata.get("demo_url"),
            documentation_url=metadata.get("documentation_url"),
            support_url=metadata.get("support_url"),
            github_url=metadata.get("github_url"),
            metrics=metrics,
            created_at=datetime.fromisoformat(metadata["created_at"]),
            updated_at=datetime.fromisoformat(metadata["updated_at"]),
            is_featured=metadata.get("is_featured", False),
            is_verified=metadata.get("is_verified", False)
        )
    
    def _initialize_default_templates(self):
        """Initialize default templates"""
        if not self.templates:
            self._create_saas_template()
            self._create_marketplace_template()
            self._create_ecommerce_template()
            self._create_fintech_template()
            self._create_healthcare_template()
    
    def _create_saas_template(self):
        """Create SaaS template"""
        template_id = "saas-starter"
        if template_id not in self.templates:
            template = Template(
                id=template_id,
                name="SaaS Starter Kit",
                description="Complete SaaS application with user authentication, billing, analytics, and admin dashboard",
                category=TemplateCategory.SAAS,
                difficulty=TemplateDifficulty.INTERMEDIATE,
                pricing=PricingModel.FREE,
                author="Asmblr Team",
                author_id="asmblr",
                version="1.0.0",
                tags=["saas", "subscription", "billing", "analytics", "admin"],
                features=[
                    TemplateFeature("User Authentication", "Complete auth system with JWT", True, "auth"),
                    TemplateFeature("Subscription Billing", "Recurring payments with Stripe", True, "billing"),
                    TemplateFeature("Analytics Dashboard", "User behavior and business metrics", True, "analytics"),
                    TemplateFeature("Admin Panel", "User and content management", True, "admin"),
                    TemplateFeature("Email Notifications", "Transactional and marketing emails", True, "notifications"),
                    TemplateFeature("API Rate Limiting", "Protect your API endpoints", True, "security"),
                    TemplateFeature("Multi-tenant", "Support multiple organizations", False, "enterprise"),
                    TemplateFeature("White-label", "Custom branding options", False, "enterprise")
                ],
                tech_stack=TemplateTech(
                    frontend=["React", "TypeScript", "Tailwind CSS"],
                    backend=["Node.js", "Express", "PostgreSQL"],
                    database=["PostgreSQL", "Redis"],
                    deployment=["Docker", "Kubernetes", "AWS"],
                    integrations=["Stripe", "SendGrid", "Google Analytics"]
                ),
                screenshots=[
                    "/templates/saas-starter/screenshots/dashboard.png",
                    "/templates/saas-starter/screenshots/billing.png",
                    "/templates/saas-starter/screenshots/analytics.png"
                ],
                demo_url="https://demo.asmblr.com/saas-starter",
                documentation_url="https://docs.asmblr.com/templates/saas-starter",
                support_url="https://support.asmblr.com",
                github_url="https://github.com/asmblr/saas-starter",
                metrics=TemplateMetrics(
                    downloads=1250,
                    rating=4.8,
                    reviews_count=89,
                    active_installs=340,
                    last_updated=datetime.now()
                ),
                created_at=datetime.now(),
                updated_at=datetime.now(),
                is_featured=True,
                is_verified=True
            )
            
            self.templates[template_id] = template
            self.featured_templates.append(template_id)
            self._save_template_to_disk(template)
    
    def _create_marketplace_template(self):
        """Create marketplace template"""
        template_id = "marketplace-platform"
        if template_id not in self.templates:
            template = Template(
                id=template_id,
                name="Marketplace Platform",
                description="Full-featured marketplace with vendor management, product catalog, and payment processing",
                category=TemplateCategory.MARKETPLACE,
                difficulty=TemplateDifficulty.ADVANCED,
                pricing=PricingModel.PREMIUM,
                author="Asmblr Team",
                author_id="asmblr",
                version="1.0.0",
                tags=["marketplace", "ecommerce", "vendors", "payments", "reviews"],
                features=[
                    TemplateFeature("Multi-vendor Support", "Multiple sellers on one platform", True, "core"),
                    TemplateFeature("Product Catalog", "Advanced product management", True, "catalog"),
                    TemplateFeature("Review System", "Customer reviews and ratings", True, "social"),
                    TemplateFeature("Commission Management", "Automated commission calculation", True, "billing"),
                    TemplateFeature("Search & Filters", "Advanced product search", True, "search"),
                    TemplateFeature("Order Management", "Complete order processing", True, "orders"),
                    TemplateFeature("Inventory Management", "Stock tracking and alerts", False, "inventory"),
                    TemplateFeature("Shipping Integration", "Multiple shipping providers", False, "logistics")
                ],
                tech_stack=TemplateTech(
                    frontend=["Vue.js", "TypeScript", "Bootstrap"],
                    backend=["Python", "Django", "PostgreSQL"],
                    database=["PostgreSQL", "Elasticsearch", "Redis"],
                    deployment=["Docker", "Kubernetes", "AWS"],
                    integrations=["Stripe", "PayPal", "Shippo", "SendGrid"]
                ),
                screenshots=[
                    "/templates/marketplace-platform/screenshots/home.png",
                    "/templates/marketplace-platform/screenshots/vendor.png",
                    "/templates/marketplace-platform/screenshots/product.png"
                ],
                demo_url="https://demo.asmblr.com/marketplace-platform",
                documentation_url="https://docs.asmblr.com/templates/marketplace-platform",
                github_url="https://github.com/asmblr/marketplace-platform",
                metrics=TemplateMetrics(
                    downloads=890,
                    rating=4.6,
                    reviews_count=67,
                    active_installs=210,
                    last_updated=datetime.now()
                ),
                created_at=datetime.now(),
                updated_at=datetime.now(),
                is_featured=True,
                is_verified=True
            )
            
            self.templates[template_id] = template
            self.featured_templates.append(template_id)
            self._save_template_to_disk(template)
    
    def _create_ecommerce_template(self):
        """Create ecommerce template"""
        template_id = "ecommerce-store"
        if template_id not in self.templates:
            template = Template(
                id=template_id,
                name="E-commerce Store",
                description="Modern online store with shopping cart, inventory management, and payment processing",
                category=TemplateCategory.ECOMMERCE,
                difficulty=TemplateDifficulty.BEGINNER,
                pricing=PricingModel.FREE,
                author="Asmblr Team",
                author_id="asmblr",
                version="1.0.0",
                tags=["ecommerce", "store", "shopping", "payments", "inventory"],
                features=[
                    TemplateFeature("Product Catalog", "Manage products and categories", True, "catalog"),
                    TemplateFeature("Shopping Cart", "Add to cart and checkout", True, "cart"),
                    TemplateFeature("Payment Processing", "Multiple payment methods", True, "payments"),
                    TemplateFeature("Order Management", "Track and manage orders", True, "orders"),
                    TemplateFeature("Customer Accounts", "User registration and profiles", True, "users"),
                    TemplateFeature("Inventory Tracking", "Stock level monitoring", True, "inventory"),
                    TemplateFeature("Discount Codes", "Promotional codes and coupons", False, "marketing"),
                    TemplateFeature("Wishlist", "Save favorite items", False, "features")
                ],
                tech_stack=TemplateTech(
                    frontend=["React", "TypeScript", "Material-UI"],
                    backend=["Node.js", "Express", "MongoDB"],
                    database=["MongoDB", "Redis"],
                    deployment=["Docker", "Vercel", "AWS"],
                    integrations=["Stripe", "PayPal", "Mailchimp"]
                ),
                screenshots=[
                    "/templates/ecommerce-store/screenshots/home.png",
                    "/templates/ecommerce-store/screenshots/product.png",
                    "/templates/ecommerce-store/screenshots/cart.png"
                ],
                demo_url="https://demo.asmblr.com/ecommerce-store",
                documentation_url="https://docs.asmblr.com/templates/ecommerce-store",
                github_url="https://github.com/asmblr/ecommerce-store",
                metrics=TemplateMetrics(
                    downloads=2100,
                    rating=4.7,
                    reviews_count=156,
                    active_installs=580,
                    last_updated=datetime.now()
                ),
                created_at=datetime.now(),
                updated_at=datetime.now(),
                is_featured=True,
                is_verified=True
            )
            
            self.templates[template_id] = template
            self.featured_templates.append(template_id)
            self._save_template_to_disk(template)
    
    def _create_fintech_template(self):
        """Create fintech template"""
        template_id = "fintech-app"
        if template_id not in self.templates:
            template = Template(
                id=template_id,
                name="FinTech Application",
                description="Secure financial application with transactions, accounts, and compliance",
                category=TemplateCategory.FINTECH,
                difficulty=TemplateDifficulty.ADVANCED,
                pricing=PricingModel.ENTERPRISE,
                author="Asmblr Team",
                author_id="asmblr",
                version="1.0.0",
                tags=["fintech", "banking", "transactions", "compliance", "security"],
                features=[
                    TemplateFeature("Account Management", "User accounts and balances", True, "accounts"),
                    TemplateFeature("Transaction Processing", "Secure money transfers", True, "transactions"),
                    TemplateFeature("Compliance Reporting", "Regulatory compliance features", True, "compliance"),
                    TemplateFeature("Security & Encryption", "Bank-level security", True, "security"),
                    TemplateFeature("Analytics Dashboard", "Financial insights and reports", True, "analytics"),
                    TemplateFeature("API Integration", "Connect to banking APIs", True, "integrations"),
                    TemplateFeature("Fraud Detection", "AI-powered fraud prevention", False, "security"),
                    TemplateFeature("Multi-currency", "Support multiple currencies", False, "features")
                ],
                tech_stack=TemplateTech(
                    frontend=["Angular", "TypeScript", "Angular Material"],
                    backend=["Java", "Spring Boot", "PostgreSQL"],
                    database=["PostgreSQL", "Redis", "Cassandra"],
                    deployment=["Docker", "Kubernetes", "AWS"],
                    integrations=["Plaid", "Stripe", "Twilio", "AWS KMS"]
                ),
                screenshots=[
                    "/templates/fintech-app/screenshots/dashboard.png",
                    "/templates/fintech-app/screenshots/transactions.png",
                    "/templates/fintech-app/screenshots/analytics.png"
                ],
                demo_url="https://demo.asmblr.com/fintech-app",
                documentation_url="https://docs.asmblr.com/templates/fintech-app",
                github_url="https://github.com/asmblr/fintech-app",
                metrics=TemplateMetrics(
                    downloads=450,
                    rating=4.9,
                    reviews_count=34,
                    active_installs=89,
                    last_updated=datetime.now()
                ),
                created_at=datetime.now(),
                updated_at=datetime.now(),
                is_featured=False,
                is_verified=True
            )
            
            self.templates[template_id] = template
            self._save_template_to_disk(template)
    
    def _create_healthcare_template(self):
        """Create healthcare template"""
        template_id = "healthcare-platform"
        if template_id not in self.templates:
            template = Template(
                id=template_id,
                name="Healthcare Platform",
                description="HIPAA-compliant healthcare platform with patient management and telemedicine",
                category=TemplateCategory.HEALTHCARE,
                difficulty=TemplateDifficulty.ADVANCED,
                pricing=PricingModel.ENTERPRISE,
                author="Asmblr Team",
                author_id="asmblr",
                version="1.0.0",
                tags=["healthcare", "hipaa", "patients", "telemedicine", "appointments"],
                features=[
                    TemplateFeature("Patient Management", "Complete patient records", True, "patients"),
                    TemplateFeature("Appointment Scheduling", "Book and manage appointments", True, "appointments"),
                    TemplateFeature("Telemedicine", "Video consultations", True, "telehealth"),
                    TemplateFeature("HIPAA Compliance", "Medical data protection", True, "compliance"),
                    TemplateFeature("Prescription Management", "Digital prescriptions", True, "prescriptions"),
                    TemplateFeature("Billing System", "Medical billing and insurance", True, "billing"),
                    TemplateFeature("Lab Integration", "Connect with labs", False, "integrations"),
                    TemplateFeature("Mobile App", "iOS and Android apps", False, "mobile")
                ],
                tech_stack=TemplateTech(
                    frontend=["React", "TypeScript", "Ant Design"],
                    backend=["Python", "Django", "PostgreSQL"],
                    database=["PostgreSQL", "Redis", "AWS S3"],
                    deployment=["Docker", "Kubernetes", "AWS"],
                    integrations=["Twilio", "Zoom", "Stripe", "AWS HealthLake"]
                ),
                screenshots=[
                    "/templates/healthcare-platform/screenshots/dashboard.png",
                    "/templates/healthcare-platform/screenshots/patients.png",
                    "/templates/healthcare-platform/screenshots/telemedicine.png"
                ],
                demo_url="https://demo.asmblr.com/healthcare-platform",
                documentation_url="https://docs.asmblr.com/templates/healthcare-platform",
                github_url="https://github.com/asmblr/healthcare-platform",
                metrics=TemplateMetrics(
                    downloads=320,
                    rating=4.8,
                    reviews_count=28,
                    active_installs=67,
                    last_updated=datetime.now()
                ),
                created_at=datetime.now(),
                updated_at=datetime.now(),
                is_featured=False,
                is_verified=True
            )
            
            self.templates[template_id] = template
            self._save_template_to_disk(template)
    
    def _save_template_to_disk(self, template: Template):
        """Save template to disk"""
        template_dir = self.templates_dir / template.id
        template_dir.mkdir(exist_ok=True)
        
        # Save metadata
        metadata = {
            "id": template.id,
            "name": template.name,
            "description": template.description,
            "category": template.category.value,
            "difficulty": template.difficulty.value,
            "pricing": template.pricing.value,
            "author": template.author,
            "author_id": template.author_id,
            "version": template.version,
            "tags": template.tags,
            "features": [asdict(f) for f in template.features],
            "tech_stack": {
                "frontend": template.tech_stack.frontend,
                "backend": template.tech_stack.backend,
                "database": template.tech_stack.database,
                "deployment": template.tech_stack.deployment,
                "integrations": template.tech_stack.integrations
            },
            "screenshots": template.screenshots,
            "demo_url": template.demo_url,
            "documentation_url": template.documentation_url,
            "support_url": template.support_url,
            "github_url": template.github_url,
            "metrics": {
                "downloads": template.metrics.downloads,
                "rating": template.metrics.rating,
                "reviews_count": template.metrics.reviews_count,
                "active_installs": template.metrics.active_installs,
                "last_updated": template.metrics.last_updated.isoformat()
            },
            "created_at": template.created_at.isoformat(),
            "updated_at": template.updated_at.isoformat(),
            "is_featured": template.is_featured,
            "is_verified": template.is_verified
        }
        
        with open(template_dir / "template.yaml", 'w') as f:
            yaml.dump(metadata, f, default_flow_style=False)
    
    async def get_templates(self, category: str | None = None, 
                          difficulty: str | None = None,
                          pricing: str | None = None,
                          featured: bool = False,
                          search: str | None = None) -> list[Template]:
        """Get templates with filters"""
        templates = list(self.templates.values())
        
        # Apply filters
        if category:
            try:
                cat_enum = TemplateCategory(category)
                templates = [t for t in templates if t.category == cat_enum]
            except ValueError:
                pass
        
        if difficulty:
            try:
                diff_enum = TemplateDifficulty(difficulty)
                templates = [t for t in templates if t.difficulty == diff_enum]
            except ValueError:
                pass
        
        if pricing:
            try:
                price_enum = PricingModel(pricing)
                templates = [t for t in templates if t.pricing == price_enum]
            except ValueError:
                pass
        
        if featured:
            templates = [t for t in templates if t.is_featured]
        
        if search:
            search_lower = search.lower()
            templates = [
                t for t in templates 
                if search_lower in t.name.lower() or 
                   search_lower in t.description.lower() or
                   any(search_lower in tag.lower() for tag in t.tags)
            ]
        
        # Sort by rating and downloads
        templates.sort(key=lambda t: (t.metrics.rating, t.metrics.downloads), reverse=True)
        
        return templates
    
    async def get_template(self, template_id: str) -> Template | None:
        """Get specific template"""
        return self.templates.get(template_id)
    
    async def install_template(self, template_id: str, project_name: str, 
                            user_id: str, customizations: dict[str, Any] = None) -> dict[str, Any]:
        """Install template for user"""
        template = await self.get_template(template_id)
        if not template:
            raise ValueError(f"Template {template_id} not found")
        
        # Create project directory
        project_dir = Path("projects") / user_id / project_name
        project_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy template files
        template_dir = self.templates_dir / template_id
        if template_dir.exists():
            shutil.copytree(template_dir, project_dir / "template", dirs_exist_ok=True)
        
        # Generate project files
        project_config = {
            "project_name": project_name,
            "template_id": template_id,
            "template_version": template.version,
            "created_at": datetime.now().isoformat(),
            "user_id": user_id,
            "customizations": customizations or {}
        }
        
        with open(project_dir / "project.json", 'w') as f:
            json.dump(project_config, f, indent=2)
        
        # Update template metrics
        template.metrics.downloads += 1
        template.metrics.active_installs += 1
        template.metrics.last_updated = datetime.now()
        await self._update_template_metrics(template)
        
        # Generate deployment files
        await self._generate_deployment_files(project_dir, template, customizations)
        
        return {
            "project_id": str(uuid.uuid4()),
            "project_name": project_name,
            "template_id": template_id,
            "status": "installed",
            "next_steps": [
                "Review project structure",
                "Customize configuration",
                "Run local development server",
                "Deploy to production"
            ]
        }
    
    async def _update_template_metrics(self, template: Template):
        """Update template metrics"""
        self._save_template_to_disk(template)
    
    async def _generate_deployment_files(self, project_dir: Path, template: Template, 
                                      customizations: dict[str, Any]):
        """Generate deployment files"""
        # Generate Dockerfile
        dockerfile_content = self._generate_dockerfile(template)
        with open(project_dir / "Dockerfile", 'w') as f:
            f.write(dockerfile_content)
        
        # Generate docker-compose.yml
        compose_content = self._generate_docker_compose(template, customizations)
        with open(project_dir / "docker-compose.yml", 'w') as f:
            f.write(compose_content)
        
        # Generate Kubernetes manifests
        k8s_dir = project_dir / "k8s"
        k8s_dir.mkdir(exist_ok=True)
        
        deployment_content = self._generate_k8s_deployment(template, customizations)
        with open(k8s_dir / "deployment.yaml", 'w') as f:
            f.write(deployment_content)
        
        service_content = self._generate_k8s_service(template)
        with open(k8s_dir / "service.yaml", 'w') as f:
            f.write(service_content)
        
        # Generate README
        readme_content = self._generate_readme(template, customizations)
        with open(project_dir / "README.md", 'w') as f:
            f.write(readme_content)
    
    def _generate_dockerfile(self, template: Template) -> str:
        """Generate Dockerfile for template"""
        if "Node.js" in template.tech_stack.backend:
            return """FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci --only=production

COPY . .

EXPOSE 3000

CMD ["npm", "start"]"""
        elif "Python" in template.tech_stack.backend:
            return """FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]"""
        elif "Java" in template.tech_stack.backend:
            return """FROM openjdk:17-jdk-slim

WORKDIR /app

COPY ./target/*.jar app.jar

EXPOSE 8080

CMD ["java", "-jar", "app.jar"]"""
        else:
            return """# Add your Dockerfile configuration here
FROM alpine:latest

WORKDIR /app

COPY . .

CMD ["./start.sh"]"""
    
    def _generate_docker_compose(self, template: Template, customizations: dict[str, Any]) -> str:
        """Generate docker-compose.yml"""
        services = {
            "app": {
                "build": ".",
                "ports": ["3000:3000"],
                "environment": ["NODE_ENV=development"],
                "volumes": [".:/app", "/app/node_modules"],
                "depends_on": ["db", "redis"]
            },
            "db": {
                "image": "postgres:15",
                "environment": ["POSTGRES_DB=app", "POSTGRES_USER=app", "POSTGRES_PASSWORD=app"],
                "volumes": ["postgres_data:/var/lib/postgresql/data"]
            },
            "redis": {
                "image": "redis:7-alpine",
                "volumes": ["redis_data:/data"]
            }
        }
        
        return f"""version: '3.8'

services:
{yaml.dump(services, default_flow_style=False)}

volumes:
  postgres_data:
  redis_data:"""
    
    def _generate_k8s_deployment(self, template: Template, customizations: dict[str, Any]) -> str:
        """Generate Kubernetes deployment"""
        return f"""apiVersion: apps/v1
kind: Deployment
metadata:
  name: {template.id}-app
  labels:
    app: {template.id}
spec:
  replicas: 3
  selector:
    matchLabels:
      app: {template.id}
  template:
    metadata:
      labels:
        app: {template.id}
    spec:
      containers:
      - name: app
        image: {template.id}:latest
        ports:
        - containerPort: 3000
        env:
        - name: NODE_ENV
          value: "production"
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: {template.id}-secrets
              key: database-url"""
    
    def _generate_k8s_service(self, template: Template) -> str:
        """Generate Kubernetes service"""
        return f"""apiVersion: v1
kind: Service
metadata:
  name: {template.id}-service
spec:
  selector:
    app: {template.id}
  ports:
  - protocol: TCP
    port: 80
    targetPort: 3000
  type: LoadBalancer"""
    
    def _generate_readme(self, template: Template, customizations: dict[str, Any]) -> str:
        """Generate README.md"""
        return f"""# {template.name}

{template.description}

## Features

{chr(10).join(f"- {feature.name}: {feature.description}" for feature in template.features if feature.included)}

## Tech Stack

**Frontend:** {', '.join(template.tech_stack.frontend)}
**Backend:** {', '.join(template.tech_stack.backend)}
**Database:** {', '.join(template.tech_stack.database)}
**Deployment:** {', '.join(template.tech_stack.deployment)}

## Quick Start

1. Install dependencies:
```bash
npm install
```

2. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Start development server:
```bash
npm run dev
```

4. Build for production:
```bash
npm run build
```

## Deployment

### Docker
```bash
docker-compose up -d
```

### Kubernetes
```bash
kubectl apply -f k8s/
```

## Documentation

- [Template Documentation]({template.documentation_url})
- [Demo]({template.demo_url})
- [GitHub Repository]({template.github_url})

## Support

- [Support Center]({template.support_url})
- Community Forum

## License

MIT License - see LICENSE file for details.
"""
    
    async def rate_template(self, template_id: str, user_id: str, rating: int, review: str = "") -> bool:
        """Rate a template"""
        template = await self.get_template(template_id)
        if not template:
            return False
        
        # In a real implementation, store ratings in database
        # For now, update metrics
        template.metrics.reviews_count += 1
        # Simple average calculation - in production, use proper aggregation
        template.metrics.rating = (template.metrics.rating * (template.metrics.reviews_count - 1) + rating) / template.metrics.reviews_count
        
        await self._update_template_metrics(template)
        return True
    
    async def get_featured_templates(self, limit: int = 6) -> list[Template]:
        """Get featured templates"""
        featured_ids = self.featured_templates[:limit]
        return [self.templates[tid] for tid in featured_ids if tid in self.templates]
    
    async def search_templates(self, query: str, limit: int = 20) -> list[Template]:
        """Search templates"""
        return await self.get_templates(search=query)

# Global template manager
template_manager = TemplateManager()

# API endpoints
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/templates", tags=["templates"])

class TemplateResponse(BaseModel):
    id: str
    name: str
    description: str
    category: str
    difficulty: str
    pricing: str
    author: str
    version: str
    tags: list[str]
    features: list[dict[str, Any]]
    tech_stack: dict[str, list[str]]
    screenshots: list[str]
    demo_url: str | None
    documentation_url: str | None
    github_url: str | None
    metrics: dict[str, Any]
    is_featured: bool
    is_verified: bool

class InstallTemplateRequest(BaseModel):
    template_id: str
    project_name: str
    user_id: str
    customizations: dict[str, Any] = {}

class RateTemplateRequest(BaseModel):
    rating: int
    review: str = ""

@router.get("/", response_model=list[TemplateResponse])
async def get_templates(
    category: str | None = None,
    difficulty: str | None = None,
    pricing: str | None = None,
    featured: bool = False,
    search: str | None = None,
    limit: int = 50
):
    """Get templates with optional filters"""
    try:
        templates = await template_manager.get_templates(
            category=category,
            difficulty=difficulty,
            pricing=pricing,
            featured=featured,
            search=search
        )
        
        return [TemplateResponse(**asdict(template)) for template in templates[:limit]]
    except Exception as e:
        logger.error(f"Error getting templates: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/featured", response_model=list[TemplateResponse])
async def get_featured_templates(limit: int = 6):
    """Get featured templates"""
    try:
        templates = await template_manager.get_featured_templates(limit)
        return [TemplateResponse(**asdict(template)) for template in templates]
    except Exception as e:
        logger.error(f"Error getting featured templates: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{template_id}", response_model=TemplateResponse)
async def get_template(template_id: str):
    """Get specific template"""
    try:
        template = await template_manager.get_template(template_id)
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        
        return TemplateResponse(**asdict(template))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting template: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/install")
async def install_template(request: InstallTemplateRequest):
    """Install template for user"""
    try:
        result = await template_manager.install_template(
            request.template_id,
            request.project_name,
            request.user_id,
            request.customizations
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error installing template: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{template_id}/rate")
async def rate_template(template_id: str, user_id: str, request: RateTemplateRequest):
    """Rate a template"""
    try:
        success = await template_manager.rate_template(
            template_id, user_id, request.rating, request.review
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Template not found")
        
        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error rating template: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search")
async def search_templates(q: str, limit: int = 20):
    """Search templates"""
    try:
        templates = await template_manager.search_templates(q, limit)
        return [TemplateResponse(**asdict(template)) for template in templates]
    except Exception as e:
        logger.error(f"Error searching templates: {e}")
        raise HTTPException(status_code=500, detail=str(e))
