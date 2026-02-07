"""Enhanced MVP builder with quality-first approach."""

import time
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from .quality_enhancer import MVPQualityEnhancer
from ..core.performance_monitor import performance_monitor
from ..core.quality_gates import QualityGateChecker

logger = logging.getLogger(__name__)


@dataclass
class MVPBuildResult:
    """Result of MVP building process."""
    success: bool
    mvp_path: Optional[Path]
    quality_score: float
    build_time: float
    improvements: List[str]
    issues_fixed: List[str]
    quality_report: Dict[str, Any]
    error_message: Optional[str] = None


class EnhancedMVPBuilder:
    """Enhanced MVP builder with quality gates and continuous improvement."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.quality_enhancer = MVPQualityEnhancer()
        self.quality_gate_checker = QualityGateChecker()
        self.max_iterations = config.get('MVP_MAX_IMPROVEMENT_ITERATIONS', 3)
        self.quality_threshold = config.get('MVP_QUALITY_THRESHOLD', 65)
        self.enable_auto_fixes = config.get('MVP_ENABLE_AUTO_FIXES', True)
    
    def build_enhanced_mvp(self, tech_spec: Dict[str, Any], prd_data: Dict[str, Any], 
                          output_path: Path) -> MVPBuildResult:
        """Build MVP with enhanced quality controls."""
        start_time = time.time()
        
        with performance_monitor.stage("mvp_enhanced_build"):
            try:
                # Initial MVP build
                mvp_path = self._build_initial_mvp(tech_spec, prd_data, output_path)
                
                # Quality enhancement loop
                quality_score = 0
                improvements = []
                issues_fixed = []
                
                for iteration in range(self.max_iterations):
                    logger.info(f"MVP quality enhancement iteration {iteration + 1}")
                    
                    # Run quality assessment
                    quality_report = self.quality_enhancer.enhance_mvp(mvp_path, tech_spec)
                    current_score = quality_report['quality_score']
                    
                    improvements.extend(quality_report.get('improvements', []))
                    issues_fixed.extend(quality_report.get('issues_fixed', []))
                    
                    if current_score >= self.quality_threshold:
                        logger.info(f"Target quality score {self.quality_threshold} reached: {current_score}")
                        quality_score = current_score
                        break
                    
                    if iteration < self.max_iterations - 1:
                        # Apply improvements
                        if self.enable_auto_fixes:
                            self._apply_auto_fixes(mvp_path, quality_report)
                    
                    quality_score = current_score
                
                # Final quality gates check
                quality_gates = self.quality_gate_checker.run_all_checks({
                    'tech': tech_spec,
                    'product': prd_data,
                    'mvp_quality': quality_score
                })
                
                build_time = time.time() - start_time
                
                return MVPBuildResult(
                    success=True,
                    mvp_path=mvp_path,
                    quality_score=quality_score,
                    build_time=build_time,
                    improvements=improvements,
                    issues_fixed=issues_fixed,
                    quality_report=quality_report
                )
                
            except Exception as e:
                logger.error(f"Enhanced MVP build failed: {e}")
                return MVPBuildResult(
                    success=False,
                    mvp_path=None,
                    quality_score=0,
                    build_time=time.time() - start_time,
                    improvements=[],
                    issues_fixed=[],
                    quality_report={},
                    error_message=str(e)
                )
    
    def _build_initial_mvp(self, tech_spec: Dict[str, Any], prd_data: Dict[str, Any], 
                          output_path: Path) -> Path:
        """Build the initial MVP structure."""
        with performance_monitor.stage("mvp_initial_build"):
            logger.info("Building initial MVP structure")
            
            # Create MVP directory structure
            mvp_path = output_path / "mvp_repo"
            mvp_path.mkdir(parents=True, exist_ok=True)
            
            # Determine tech stack based on preferences
            frontend = self.config.get('MVP_PREFERRED_FRONTEND', 'nextjs')
            backend = self.config.get('MVP_PREFERRED_BACKEND', 'fastapi')
            database = self.config.get('MVP_PREFERRED_DATABASE', 'sqlite')
            styling = self.config.get('MVP_PREFERRED_STYLING', 'tailwind')
            
            # Generate project structure based on tech stack
            self._create_project_structure(mvp_path, frontend, backend, database, styling)
            
            # Generate core files
            self._generate_core_files(mvp_path, tech_spec, prd_data, frontend, backend)
            
            # Generate UI components
            self._generate_ui_components(mvp_path, prd_data, frontend, styling)
            
            # Generate API endpoints
            self._generate_api_endpoints(mvp_path, tech_spec, backend)
            
            # Generate database schema
            self._generate_database_schema(mvp_path, tech_spec, database)
            
            # Generate configuration files
            self._generate_config_files(mvp_path, frontend, backend, database)
            
            # Generate documentation
            self._generate_documentation(mvp_path, tech_spec, prd_data)
            
            return mvp_path
    
    def _create_project_structure(self, mvp_path: Path, frontend: str, backend: str, 
                                database: str, styling: str) -> None:
        """Create the basic project structure."""
        # Frontend structure
        frontend_path = mvp_path / "frontend"
        frontend_path.mkdir(exist_ok=True)
        
        if frontend == "nextjs":
            (frontend_path / "pages").mkdir(exist_ok=True)
            (frontend_path / "components").mkdir(exist_ok=True)
            (frontend_path / "styles").mkdir(exist_ok=True)
            (frontend_path / "utils").mkdir(exist_ok=True)
        
        # Backend structure
        backend_path = mvp_path / "backend"
        backend_path.mkdir(exist_ok=True)
        
        if backend == "fastapi":
            (backend_path / "api").mkdir(exist_ok=True)
            (backend_path / "models").mkdir(exist_ok=True)
            (backend_path / "services").mkdir(exist_ok=True)
            (backend_path / "utils").mkdir(exist_ok=True)
        
        # Database structure
        if database == "sqlite":
            (mvp_path / "database").mkdir(exist_ok=True)
        
        # Documentation
        (mvp_path / "docs").mkdir(exist_ok=True)
        (mvp_path / "tests").mkdir(exist_ok=True)
    
    def _generate_core_files(self, mvp_path: Path, tech_spec: Dict[str, Any], 
                           prd_data: Dict[str, Any], frontend: str, backend: str) -> None:
        """Generate core application files."""
        # Package.json
        package_json = {
            "name": prd_data.get('product_name', 'mvp-app').lower().replace(' ', '-'),
            "version": "1.0.0",
            "description": prd_data.get('one_liner', 'Generated MVP'),
            "scripts": {
                "dev": "concurrently \"npm run dev:frontend\" \"npm run dev:backend\"",
                "dev:frontend": f"cd frontend && npm run dev",
                "dev:backend": f"cd backend && uvicorn main:app --reload --host 0.0.0.0 --port 8000",
                "build": "npm run build:frontend && npm run build:backend",
                "build:frontend": "cd frontend && npm run build",
                "build:backend": "cd backend && echo 'Backend build completed'",
                "test": "npm run test:frontend && npm run test:backend",
                "test:frontend": "cd frontend && npm test",
                "test:backend": "cd backend && python -m pytest"
            },
            "dependencies": {
                "concurrently": "^8.2.0"
            },
            "devDependencies": {
                "@types/node": "^20.0.0",
                "typescript": "^5.0.0",
                "eslint": "^8.0.0",
                "prettier": "^3.0.0"
            }
        }
        
        (mvp_path / "package.json").write_text(
            json.dumps(package_json, indent=2), encoding='utf-8'
        )
        
        # README.md
        readme_content = f"""# {prd_data.get('product_name', 'MVP Application')}

{prd_data.get('one_liner', 'Generated MVP application')}

## Features

{chr(10).join(f"- {feature}" for feature in prd_data.get('key_features', []))}

## Tech Stack

- **Frontend**: {frontend.title()}
- **Backend**: {backend.title()}
- **Database**: {database.title()}
- **Styling**: {styling.title()}

## Installation

```bash
npm install
cd frontend && npm install
cd ../backend && pip install -r requirements.txt
```

## Usage

```bash
npm run dev
```

The application will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## Development

- Frontend development: `npm run dev:frontend`
- Backend development: `npm run dev:backend`
- Run tests: `npm test`

## Built with Asmblr

This MVP was generated using [Asmblr](https://github.com/your-org/asmblr) - AI-powered MVP generator.
"""
        
        (mvp_path / "README.md").write_text(readme_content, encoding='utf-8')
    
    def _generate_ui_components(self, mvp_path: Path, prd_data: Dict[str, Any], 
                              frontend: str, styling: str) -> None:
        """Generate UI components based on PRD requirements."""
        frontend_path = mvp_path / "frontend"
        
        if frontend == "nextjs":
            # Generate main page
            main_page = f"""import {{ Head }} from 'next/document'
import '../styles/globals.css'

export default function App({{ Component, pageProps }}) {{
  return (
    <>
      <Head>
        <title>{{prd_data.get('product_name', 'MVP App')}}</title>
        <meta name="description" content="{{prd_data.get('one_liner', 'Generated MVP')}}" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
      </Head>
      <Component {{...pageProps}} />
    </>
  )
}}
"""
            (frontend_path / "pages" / "_app.js").write_text(main_page, encoding='utf-8')
            
            # Generate index page
            index_page = f"""export default function Home() {{
  return (
    <div className="container">
      <header>
        <h1>{{prd_data.get('product_name', 'MVP Application')}}</h1>
        <p>{{prd_data.get('one_liner', 'Welcome to your MVP')}}</p>
      </header>
      
      <main>
        <section className="features">
          <h2>Features</h2>
          {chr(10).join(f'          <div className="feature"><h3>{feature}</h3><p>Feature description</p></div>' for feature in prd_data.get('key_features', []))}
        </section>
      </main>
    </div>
  )
}}
"""
            (frontend_path / "pages" / "index.js").write_text(index_page, encoding='utf-8')
            
            # Generate global styles with Tailwind
            if styling == "tailwind":
                globals_css = """@tailwind base;
@tailwind components;
@tailwind utilities;

.container {
  @apply max-w-7xl mx-auto px-4 sm:px-6 lg:px-8;
}

.feature {
  @apply bg-white p-6 rounded-lg shadow-md mb-4;
}

.feature h3 {
  @apply text-xl font-semibold mb-2;
}
"""
                (frontend_path / "styles" / "globals.css").write_text(globals_css, encoding='utf-8')
    
    def _generate_api_endpoints(self, mvp_path: Path, tech_spec: Dict[str, Any], 
                              backend: str) -> None:
        """Generate API endpoints based on technical specifications."""
        backend_path = mvp_path / "backend"
        
        if backend == "fastapi":
            # Generate main FastAPI app
            main_app = '''from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api import routes

app = FastAPI(
    title="MVP API",
    description="Generated MVP API",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(routes.router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "MVP API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
'''
            (backend_path / "main.py").write_text(main_app, encoding='utf-8')
            
            # Generate API routes
            routes = '''from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class FeatureRequest(BaseModel):
    name: str
    description: str

@router.get("/features")
async def get_features():
    """Get all features"""
    return [
        {"id": 1, "name": "Feature 1", "description": "Description 1"},
        {"id": 2, "name": "Feature 2", "description": "Description 2"}
    ]

@router.post("/features")
async def create_feature(feature: FeatureRequest):
    """Create a new feature"""
    return {"id": 3, "name": feature.name, "description": feature.description}
'''
            (backend_path / "api" / "routes.py").write_text(routes, encoding='utf-8')
            
            # Generate requirements.txt
            requirements = '''fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
python-multipart==0.0.6
'''
            (backend_path / "requirements.txt").write_text(requirements, encoding='utf-8')
    
    def _generate_database_schema(self, mvp_path: Path, tech_spec: Dict[str, Any], 
                                database: str) -> None:
        """Generate database schema based on requirements."""
        if database == "sqlite":
            db_path = mvp_path / "database"
            
            # Generate SQLite schema
            schema_sql = '''
-- MVP Database Schema
CREATE TABLE IF NOT EXISTS features (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    name TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert sample data
INSERT INTO features (name, description) VALUES 
    ('Feature 1', 'Description for feature 1'),
    ('Feature 2', 'Description for feature 2');
'''
            (db_path / "schema.sql").write_text(schema_sql, encoding='utf-8')
    
    def _generate_config_files(self, mvp_path: Path, frontend: str, backend: str, 
                             database: str) -> None:
        """Generate configuration files."""
        # Docker configuration
        dockerfile = '''FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./
COPY frontend/package*.json ./frontend/
COPY backend/requirements.txt ./backend/

# Install dependencies
RUN npm install
RUN cd frontend && npm install
RUN cd backend && pip install -r requirements.txt

# Copy source code
COPY . .

# Expose ports
EXPOSE 3000 8000

# Start the application
CMD ["npm", "run", "dev"]
'''
        (mvp_path / "Dockerfile").write_text(dockerfile, encoding='utf-8')
        
        # Docker Compose
        docker_compose = f'''version: '3.8'

services:
  app:
    build: .
    ports:
      - "3000:3000"
      - "8000:8000"
    environment:
      - NODE_ENV=development
    volumes:
      - .:/app
      - /app/node_modules
    depends_on:
      - db

  db:
    image: sqlite:latest
    volumes:
      - ./database:/database
'''
        (mvp_path / "docker-compose.yml").write_text(docker_compose, encoding='utf-8')
    
    def _generate_documentation(self, mvp_path: Path, tech_spec: Dict[str, Any], 
                             prd_data: Dict[str, Any]) -> None:
        """Generate comprehensive documentation."""
        docs_path = mvp_path / "docs"
        
        # API documentation
        api_docs = f'''# API Documentation

## Overview

This document describes the API endpoints for {prd_data.get('product_name', 'MVP Application')}.

## Base URL

```
http://localhost:8000/api/v1
```

## Endpoints

### GET /features
Get all features.

**Response:**
```json
[
    {{
        "id": 1,
        "name": "Feature 1",
        "description": "Description 1"
    }}
]
```

### POST /features
Create a new feature.

**Request Body:**
```json
{{
    "name": "Feature Name",
    "description": "Feature Description"
}}
```

## Authentication

Currently, no authentication is required for this MVP.

## Error Handling

All endpoints return appropriate HTTP status codes and error messages.
'''
        (docs_path / "api.md").write_text(api_docs, encoding='utf-8')
    
    def _apply_auto_fixes(self, mvp_path: Path, quality_report: Dict[str, Any]) -> None:
        """Apply automatic fixes based on quality assessment."""
        with performance_monitor.stage("mvp_auto_fixes"):
            logger.info("Applying automatic fixes to improve MVP quality")
            
            # Fix common issues based on quality report
            issues_fixed = quality_report.get('issues_fixed', [])
            
            for issue in issues_fixed:
                if "Missing documentation" in issue:
                    self._add_missing_documentation(mvp_path)
                elif "Missing error handling" in issue:
                    self._add_error_handling(mvp_path)
                elif "Missing accessibility" in issue:
                    self._add_accessibility_features(mvp_path)
    
    def _add_missing_documentation(self, mvp_path: Path) -> None:
        """Add missing documentation files."""
        # Add CONTRIBUTING.md
        contributing = '''# Contributing to this MVP

## Getting Started

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## Development Guidelines

- Follow the existing code style
- Add comments for complex logic
- Update documentation as needed
'''
        (mvp_path / "CONTRIBUTING.md").write_text(contributing, encoding='utf-8')
    
    def _add_error_handling(self, mvp_path: Path) -> None:
        """Add error handling to JavaScript/TypeScript files."""
        js_files = list(mvp_path.rglob("*.js")) + list(mvp_path.rglob("*.ts"))
        
        for js_file in js_files:
            content = js_file.read_text(encoding='utf-8')
            if 'try' not in content and 'catch' not in content:
                # Add basic error handling wrapper
                enhanced_content = f'''// Error handling wrapper
function withErrorHandling(fn) {{
  return async (...args) => {{
    try {{
      return await fn(...args);
    }} catch (error) {{
      console.error('Error in {{fn.name}}:', error);
      throw error;
    }}
  }};
}}

{content}'''
                js_file.write_text(enhanced_content, encoding='utf-8')
    
    def _add_accessibility_features(self, mvp_path: Path) -> None:
        """Add accessibility features to HTML files."""
        html_files = list(mvp_path.rglob("*.html"))
        
        for html_file in html_files:
            content = html_file.read_text(encoding='utf-8')
            
            # Add accessibility attributes
            if 'lang=' not in content:
                content = content.replace('<html', '<html lang="en">')
            
            if 'alt=' not in content:
                # Add alt attributes to images without them
                import re
                content = re.sub(r'<img(?![^>]*alt=)', '<img alt=""', content)
            
            html_file.write_text(content, encoding='utf-8')
