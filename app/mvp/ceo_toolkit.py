"""
CEO Toolkit - Unlimited Tool Access
Donne au CEO orchestrator accès à TOUS les outils disponibles pour faire ce qu'il veut.
Aucune restriction, aucune limite, liberté totale.
"""

import asyncio
import json
import subprocess
import os
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable, Union
from datetime import datetime
from dataclasses import dataclass, field
import httpx
import sqlite3
import tempfile

from loguru import logger
from app.core.config import Settings
from app.core.llm import LLMClient


@dataclass
class ToolExecution:
    """Résultat d'exécution d'un outil"""
    tool_name: str
    success: bool
    result: Any = None
    error: Optional[str] = None
    execution_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class CEOToolkit:
    """
    Toolkit CEO - Accès illimité à tous les outils
    
    Le CEO peut utiliser n'importe quel outil disponible dans le système :
    - Création/modification de fichiers
    - Exécution de commandes système
    - Appels API externes
    - Gestion de base de données
    - Déploiement
    - Tests
    - Et bien plus...
    
    AUCUNE RESTRICTION. LIBERTÉ TOTALE.
    """
    
    def __init__(
        self,
        settings: Settings,
        llm_client: LLMClient,
        run_dir: Path
    ):
        self.settings = settings
        self.llm_client = llm_client
        self.run_dir = run_dir
        self.execution_log: List[ToolExecution] = []
        self.tool_permissions = {
            "file_operations": True,
            "command_execution": True,
            "api_calls": True,
            "database_operations": True,
            "network_operations": True,
            "system_modifications": True,
            "deployment": True,
            "testing": True,
            "ai_generation": True,
            "code_execution": True
        }
    
    async def execute_tool(
        self,
        tool_name: str,
        tool_func: Callable,
        *args,
        **kwargs
    ) -> ToolExecution:
        """
        Exécute un outil avec logging complet
        
        Args:
            tool_name: Nom de l'outil
            tool_func: Fonction de l'outil
            *args, **kwargs: Arguments de la fonction
            
        Returns:
            ToolExecution avec le résultat
        """
        start_time = datetime.utcnow()
        
        try:
            logger.info(f"🔧 CEO TOOL: {tool_name} - Executing...")
            
            # Exécuter l'outil
            if asyncio.iscoroutinefunction(tool_func):
                result = await tool_func(*args, **kwargs)
            else:
                result = tool_func(*args, **kwargs)
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            execution = ToolExecution(
                tool_name=tool_name,
                success=True,
                result=result,
                execution_time=execution_time,
                metadata={"timestamp": start_time.isoformat()}
            )
            
            logger.info(f"✅ CEO TOOL: {tool_name} - Success ({execution_time:.2f}s)")
            
        except Exception as exc:
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            execution = ToolExecution(
                tool_name=tool_name,
                success=False,
                error=str(exc),
                execution_time=execution_time,
                metadata={"timestamp": start_time.isoformat()}
            )
            
            logger.error(f"❌ CEO TOOL: {tool_name} - Failed: {exc}")
        
        self.execution_log.append(execution)
        return execution
    
    # ============================================
    # FILE OPERATIONS - Création/Modification de fichiers
    # ============================================
    
    async def create_file(
        self,
        path: Union[str, Path],
        content: str,
        encoding: str = "utf-8"
    ) -> ToolExecution:
        """Crée un fichier avec du contenu"""
        
        async def _create():
            path = Path(path)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding=encoding)
            return {"path": str(path), "size": len(content)}
        
        return await self.execute_tool("create_file", _create, path, content, encoding)
    
    async def read_file(
        self,
        path: Union[str, Path],
        encoding: str = "utf-8"
    ) -> ToolExecution:
        """Lit un fichier"""
        
        async def _read():
            path = Path(path)
            if not path.exists():
                raise FileNotFoundError(f"File not found: {path}")
            return path.read_text(encoding=encoding)
        
        return await self.execute_tool("read_file", _read, path, encoding)
    
    async def modify_file(
        self,
        path: Union[str, Path],
        old_content: str,
        new_content: str,
        encoding: str = "utf-8"
    ) -> ToolExecution:
        """Modifie un fichier (remplace old_content par new_content)"""
        
        async def _modify():
            path = Path(path)
            content = path.read_text(encoding=encoding)
            if old_content not in content:
                raise ValueError(f"Old content not found in file")
            new_file_content = content.replace(old_content, new_content, 1)
            path.write_text(new_file_content, encoding=encoding)
            return {"path": str(path), "changes": 1}
        
        return await self.execute_tool("modify_file", _modify, path, old_content, new_content, encoding)
    
    async def delete_file(
        self,
        path: Union[str, Path]
    ) -> ToolExecution:
        """Supprime un fichier"""
        
        async def _delete():
            path = Path(path)
            if path.exists():
                path.unlink()
                return {"path": str(path), "deleted": True}
            return {"path": str(path), "deleted": False}
        
        return await self.execute_tool("delete_file", _delete, path)
    
    async def copy_file(
        self,
        src: Union[str, Path],
        dst: Union[str, Path]
    ) -> ToolExecution:
        """Copie un fichier"""
        
        async def _copy():
            src = Path(src)
            dst = Path(dst)
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            return {"src": str(src), "dst": str(dst)}
        
        return await self.execute_tool("copy_file", _copy, src, dst)
    
    async def move_file(
        self,
        src: Union[str, Path],
        dst: Union[str, Path]
    ) -> ToolExecution:
        """Déplace un fichier"""
        
        async def _move():
            src = Path(src)
            dst = Path(dst)
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dst))
            return {"src": str(src), "dst": str(dst)}
        
        return await self.execute_tool("move_file", _move, src, dst)
    
    async def list_directory(
        self,
        path: Union[str, Path],
        recursive: bool = False
    ) -> ToolExecution:
        """Liste les fichiers dans un répertoire"""
        
        async def _list():
            path = Path(path)
            if not path.exists():
                raise FileNotFoundError(f"Directory not found: {path}")
            
            if recursive:
                files = [str(p) for p in path.rglob("*") if p.is_file()]
            else:
                files = [str(p) for p in path.iterdir() if p.is_file()]
            
            return {"path": str(path), "files": files, "count": len(files)}
        
        return await self.execute_tool("list_directory", _list, path, recursive)
    
    # ============================================
    # COMMAND EXECUTION - Exécution de commandes système
    # ============================================
    
    async def execute_command(
        self,
        command: str,
        cwd: Optional[Union[str, Path]] = None,
        timeout: int = 300,
        shell: bool = True
    ) -> ToolExecution:
        """
        Exécute une commande système
        
        ATTENTION: Le CEO peut exécuter n'importe quelle commande !
        """
        
        async def _execute():
            if cwd:
                cwd = str(cwd)
            
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )
                
                return {
                    "command": command,
                    "return_code": process.returncode,
                    "stdout": stdout.decode("utf-8", errors="ignore"),
                    "stderr": stderr.decode("utf-8", errors="ignore"),
                    "cwd": cwd
                }
            except asyncio.TimeoutError:
                process.kill()
                raise TimeoutError(f"Command timed out after {timeout}s")
        
        return await self.execute_tool("execute_command", _execute, command, cwd, timeout, shell)
    
    async def execute_python(
        self,
        code: str,
        cwd: Optional[Union[str, Path]] = None
    ) -> ToolExecution:
        """Exécute du code Python"""
        
        async def _execute_python():
            # Créer un fichier temporaire
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            try:
                # Exécuter le fichier
                result = await self.execute_command(
                    f"python {temp_file}",
                    cwd=cwd
                )
                
                return {
                    "code": code,
                    "output": result.result.get("stdout", ""),
                    "error": result.result.get("stderr", "")
                }
            finally:
                # Nettoyer
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
        
        return await self.execute_tool("execute_python", _execute_python, code, cwd)
    
    async def run_npm_command(
        self,
        command: str,
        cwd: Optional[Union[str, Path]] = None
    ) -> ToolExecution:
        """Exécute une commande npm"""
        
        async def _run_npm():
            return await self.execute_command(f"npm {command}", cwd=cwd)
        
        return await self.execute_tool("run_npm_command", _run_npm, command, cwd)
    
    async def run_git_command(
        self,
        command: str,
        cwd: Optional[Union[str, Path]] = None
    ) -> ToolExecution:
        """Exécute une commande git"""
        
        async def _run_git():
            return await self.execute_command(f"git {command}", cwd=cwd)
        
        return await self.execute_tool("run_git_command", _run_git, command, cwd)
    
    # ============================================
    # API CALLS - Appels API externes
    # ============================================
    
    async def make_api_call(
        self,
        url: str,
        method: str = "GET",
        headers: Optional[Dict[str, str]] = None,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        timeout: int = 30
    ) -> ToolExecution:
        """Effectue un appel API"""
        
        async def _call():
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=data,
                    params=params
                )
                
                return {
                    "url": url,
                    "method": method,
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "body": response.text,
                    "json": response.json() if response.headers.get("content-type", "").startswith("application/json") else None
                }
        
        return await self.execute_tool("make_api_call", _call, url, method, headers, data, params, timeout)
    
    async def fetch_webpage(
        self,
        url: str
    ) -> ToolExecution:
        """Récupère le contenu d'une page web"""
        
        async def _fetch():
            response = await self.make_api_call(url)
            if not response.success:
                raise Exception(f"Failed to fetch webpage: {response.error}")
            return response.result.get("body", "")
        
        return await self.execute_tool("fetch_webpage", _fetch, url)
    
    async def call_openai_api(
        self,
        prompt: str,
        model: str = "gpt-4",
        max_tokens: int = 2000
    ) -> ToolExecution:
        """Appelle l'API OpenAI (si configuré)"""
        
        async def _call_openai():
            # Placeholder pour OpenAI API
            # Le CEO peut utiliser n'importe quel LLM disponible
            result = await self.llm_client.generate_async(prompt)
            return {"prompt": prompt, "response": result}
        
        return await self.execute_tool("call_openai_api", _call_openai, prompt, model, max_tokens)
    
    # ============================================
    # DATABASE OPERATIONS - Gestion de base de données
    # ============================================
    
    async def execute_sql(
        self,
        query: str,
        db_path: Optional[Union[str, Path]] = None,
        params: Optional[tuple] = None
    ) -> ToolExecution:
        """Exécute une requête SQL"""
        
        async def _execute_sql():
            if db_path is None:
                # Créer une DB temporaire
                db_path = self.run_dir / "temp.db"
            
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            
            try:
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                
                conn.commit()
                
                # Récupérer les résultats si c'est un SELECT
                if query.strip().upper().startswith("SELECT"):
                    rows = cursor.fetchall()
                    columns = [desc[0] for desc in cursor.description]
                    results = [dict(zip(columns, row)) for row in rows]
                else:
                    results = {"rows_affected": cursor.rowcount}
                
                return {"query": query, "results": results}
            finally:
                conn.close()
        
        return await self.execute_tool("execute_sql", _execute_sql, query, db_path, params)
    
    async def create_database(
        self,
        db_path: Union[str, Path],
        schema: Optional[str] = None
    ) -> ToolExecution:
        """Crée une base de données avec un schéma"""
        
        async def _create_db():
            db_path = Path(db_path)
            db_path.parent.mkdir(parents=True, exist_ok=True)
            
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            
            if schema:
                cursor.executescript(schema)
            
            conn.commit()
            conn.close()
            
            return {"db_path": str(db_path), "schema_provided": schema is not None}
        
        return await self.execute_tool("create_database", _create_db, db_path, schema)
    
    # ============================================
    # NETWORK OPERATIONS - Opérations réseau
    # ============================================
    
    async def check_url(
        self,
        url: str,
        timeout: int = 10
    ) -> ToolExecution:
        """Vérifie si une URL est accessible"""
        
        async def _check():
            try:
                response = await self.make_api_call(url, timeout=timeout)
                return {
                    "url": url,
                    "accessible": response.success and response.result.get("status_code") == 200,
                    "status_code": response.result.get("status_code")
                }
            except Exception:
                return {"url": url, "accessible": False, "status_code": None}
        
        return await self.execute_tool("check_url", _check, url, timeout)
    
    async def download_file(
        self,
        url: str,
        destination: Union[str, Path]
    ) -> ToolExecution:
        """Télécharge un fichier depuis une URL"""
        
        async def _download():
            destination = Path(destination)
            destination.parent.mkdir(parents=True, exist_ok=True)
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url)
                response.raise_for_status()
                destination.write_bytes(response.content)
            
            return {
                "url": url,
                "destination": str(destination),
                "size": len(destination.read_bytes())
            }
        
        return await self.execute_tool("download_file", _download, url, destination)
    
    # ============================================
    # AI GENERATION - Génération avec IA
    # ============================================
    
    async def generate_code(
        self,
        prompt: str,
        language: str = "python"
    ) -> ToolExecution:
        """Génère du code avec l'IA"""
        
        async def _generate():
            enhanced_prompt = f"""
            Generate {language} code for: {prompt}
            
            Requirements:
            - Clean, modern code
            - Best practices
            - Error handling
            - Comments where needed
            - Production ready
            """
            
            result = await self.llm_client.generate_async(enhanced_prompt)
            return {"prompt": prompt, "language": language, "code": result}
        
        return await self.execute_tool("generate_code", _generate, prompt, language)
    
    async def generate_content(
        self,
        prompt: str,
        content_type: str = "general"
    ) -> ToolExecution:
        """Génère du contenu avec l'IA"""
        
        async def _generate_content():
            enhanced_prompt = f"""
            Generate {content_type} content for: {prompt}
            
            Requirements:
            - Engaging and compelling
            - Clear and concise
            - Professional tone
            - Optimized for the target audience
            """
            
            result = await self.llm_client.generate_async(enhanced_prompt)
            return {"prompt": prompt, "content_type": content_type, "content": result}
        
        return await self.execute_tool("generate_content", _generate_content, prompt, content_type)
    
    async def analyze_with_ai(
        self,
        content: str,
        analysis_type: str = "general"
    ) -> ToolExecution:
        """Analyse du contenu avec l'IA"""
        
        async def _analyze():
            prompt = f"""
            Analyze the following content as {analysis_type}:
            
            {content}
            
            Provide detailed analysis with:
            - Key insights
            - Recommendations
            - Action items
            - Potential issues
            """
            
            result = await self.llm_client.generate_async(prompt)
            return {"content": content[:500] + "...", "analysis_type": analysis_type, "analysis": result}
        
        return await self.execute_tool("analyze_with_ai", _analyze, content, analysis_type)
    
    # ============================================
    # DEPLOYMENT - Déploiement
    # ============================================
    
    async def deploy_application(
        self,
        repo_path: Union[str, Path],
        platform: str = "netlify",
        config: Optional[Dict[str, Any]] = None
    ) -> ToolExecution:
        """Déploie une application"""
        
        async def _deploy():
            # Placeholder pour déploiement
            # Le CEO peut déployer sur différentes plateformes
            return {
                "repo_path": str(repo_path),
                "platform": platform,
                "config": config,
                "status": "deployment_initiated",
                "message": "Deployment would be executed here"
            }
        
        return await self.execute_tool("deploy_application", _deploy, repo_path, platform, config)
    
    async def run_tests(
        self,
        repo_path: Union[str, Path],
        test_type: str = "all"
    ) -> ToolExecution:
        """Exécute des tests"""
        
        async def _run_tests():
            repo_path = Path(repo_path)
            
            if test_type == "all":
                command = "npm test"
            elif test_type == "unit":
                command = "npm run test:unit"
            elif test_type == "integration":
                command = "npm run test:integration"
            elif test_type == "e2e":
                command = "npm run test:e2e"
            else:
                command = "npm test"
            
            result = await self.execute_command(command, cwd=repo_path)
            return result.result
        
        return await self.execute_tool("run_tests", _run_tests, repo_path, test_type)
    
    async def build_application(
        self,
        repo_path: Union[str, Path],
        build_type: str = "production"
    ) -> ToolExecution:
        """Build une application"""
        
        async def _build():
            repo_path = Path(repo_path)
            
            if build_type == "production":
                command = "npm run build"
            elif build_type == "development":
                command = "npm run build:dev"
            else:
                command = "npm run build"
            
            result = await self.execute_command(command, cwd=repo_path)
            return result.result
        
        return await self.execute_tool("build_application", _build, repo_path, build_type)
    
    # ============================================
    # SYSTEM OPERATIONS - Opérations système
    # ============================================
    
    async def get_system_info(self) -> ToolExecution:
        """Récupère les informations système"""
        
        async def _get_info():
            import platform
            import psutil
            
            return {
                "os": platform.system(),
                "os_version": platform.version(),
                "python_version": platform.python_version(),
                "cpu_count": psutil.cpu_count(),
                "memory_gb": psutil.virtual_memory().total / (1024**3),
                "disk_usage": {
                    "total": psutil.disk_usage('/').total,
                    "used": psutil.disk_usage('/').used,
                    "free": psutil.disk_usage('/').free
                }
            }
        
        return await self.execute_tool("get_system_info", _get_info)
    
    async def create_directory(
        self,
        path: Union[str, Path]
    ) -> ToolExecution:
        """Crée un répertoire"""
        
        async def _create():
            path = Path(path)
            path.mkdir(parents=True, exist_ok=True)
            return {"path": str(path), "created": True}
        
        return await self.execute_tool("create_directory", _create, path)
    
    async def get_execution_log(self) -> List[ToolExecution]:
        """Récupère le log d'exécution"""
        return self.execution_log
    
    async def get_tool_statistics(self) -> Dict[str, Any]:
        """Récupère les statistiques d'utilisation des outils"""
        
        stats = {}
        for execution in self.execution_log:
            tool_name = execution.tool_name
            if tool_name not in stats:
                stats[tool_name] = {
                    "total": 0,
                    "success": 0,
                    "failed": 0,
                    "total_time": 0.0
                }
            
            stats[tool_name]["total"] += 1
            if execution.success:
                stats[tool_name]["success"] += 1
            else:
                stats[tool_name]["failed"] += 1
            stats[tool_name]["total_time"] += execution.execution_time
        
        return stats


# Fonction utilitaire pour créer un toolkit CEO
async def create_ceo_toolkit(
    settings: Settings,
    llm_client: LLMClient,
    run_dir: Path
) -> CEOToolkit:
    """
    Crée un toolkit CEO avec accès illimité
    
    Args:
        settings: Configuration Asmblr
        llm_client: Client LLM
        run_dir: Répertoire de travail
        
    Returns:
        CEOToolkit avec tous les outils disponibles
    """
    
    toolkit = CEOToolkit(
        settings=settings,
        llm_client=llm_client,
        run_dir=run_dir
    )
    
    logger.info("🔧 CEO Toolkit created - Unlimited tool access granted")
    
    return toolkit
