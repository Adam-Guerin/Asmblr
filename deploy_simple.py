#!/usr/bin/env python
"""
Script de déploiement simple pour les micro-services Asmblr
Phase 2: Déploiement de l'architecture micro-services
"""

import os
import sys
import time
import subprocess
import requests

def log(message, level='INFO'):
    """Logger avec timestamps"""
    timestamp = time.strftime('%H:%M:%S')
    print(f"[{timestamp}] {level}: {message}")

def run_command(command, check=True):
    """Exécute une commande shell"""
    try:
        subprocess.run(command, shell=True, check=check)
    except subprocess.CalledProcessError as e:
        log(f"Command failed: {command}", 'ERROR')
        log(f"Error: {e}", 'ERROR')
        return False
    return True

def check_docker():
    """Vérifie si Docker est disponible"""
    log("Vérification de Docker...")
    
    try:
        result = subprocess.run("docker --version", shell=True, capture_output=True, text=True, check=True)
        log(f"Docker version: {result.stdout.strip()}")
        return True
    except:
        log("Docker n'est pas disponible", 'ERROR')
        return False

def deploy_infrastructure():
    """Déploie l'infrastructure de base"""
    log("Déploiement de l'infrastructure...")
    
    # PostgreSQL
    log("Déploiement de PostgreSQL...")
    postgres_cmd = """docker run -d --name asmblr-postgres --network asmblr-network -e POSTGRES_DB=asmblr -e POSTGRES_USER=asmblr -e POSTGRES_PASSWORD=asmblr_secure_password -p 5432:5432 postgres:15-alpine"""
    run_command(postgres_cmd)
    
    # Redis
    log("Déploiement de Redis...")
    redis_cmd = """docker run -d --name asmblr-redis --network asmblr-network -p 6379:6379 redis:7-alpine"""
    run_command(redis_cmd)
    
    # Ollama
    log("Déploiement d'Ollama...")
    ollama_cmd = """docker run -d --name asmblr-ollama --network asmblr-network -p 11434:11434 ollama/ollama"""
    run_command(ollama_cmd)
    
    log("Infrastructure déployée avec succès")

def wait_for_infrastructure():
    """Attend que l'infrastructure soit prête"""
    log("Attente de l'infrastructure...")
    
    # Attendre PostgreSQL (30 secondes max)
    log("Attente de PostgreSQL...")
    for i in range(30):
        try:
            result = subprocess.run("docker exec asmblr-postgres pg_isready -U asmblr", shell=True, capture_output=True, text=True, check=False)
            if 'accepting connections' in result.stdout:
                log("PostgreSQL prêt")
                break
        except:
            pass
        time.sleep(1)
    else:
        log("PostgreSQL n'est pas prêt après 30 secondes", 'WARNING')
    
    # Attendre Redis (10 secondes max)
    log("Attente de Redis...")
    for i in range(10):
        try:
            result = subprocess.run("docker exec asmblr-redis redis-cli ping", shell=True, capture_output=True, text=True, check=False)
            if 'PONG' in result.stdout:
                log("Redis prêt")
                break
        except:
            pass
        time.sleep(1)
    else:
        log("Redis n'est pas prêt après 10 secondes", 'WARNING')
    
    # Attendre Ollama (30 secondes max)
    log("Attente d'Ollama...")
    for i in range(30):
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=2)
            if response.status_code == 200:
                log("Ollama prêt")
                break
        except:
            pass
        time.sleep(1)
    else:
        log("Ollama n'est pas prêt après 30 secondes", 'WARNING')

def pull_ollama_models():
    """Télécharge les modèles Ollama requis"""
    log("Téléchargement des modèles Ollama...")
    
    models = ['llama3.1:8b', 'qwen2.5-coder:7b']
    
    for model in models:
        log(f"Téléchargement du modèle: {model}")
        try:
            result = subprocess.run(f"docker exec asmblr-ollama ollama pull {model}", shell=True, capture_output=True, text=True, check=False)
            if result.stderr and 'error' in result.stderr.lower():
                log(f"Erreur téléchargement {model}: {result.stderr}", 'ERROR')
            else:
                log(f"Modèle {model} téléchargé avec succès")
        except Exception as e:
            log(f"Erreur téléchargement {model}: {e}", 'ERROR')

def build_core_service():
    """Construit et déploie le service core"""
    log("Construction et déploiement du service core...")
    
    # Construire l'image
    build_cmd = "docker build -t asmblr-core:latest ./asmblr-core"
    if not run_command(build_cmd):
        return False
    
    # Déployer le service
    deploy_cmd = """docker run -d --name asmblr-core --network asmblr-network -e DATABASE_URL=postgresql://asmblr:asmblr_secure_password@postgres:5432/asmblr -e REDIS_URL=redis://redis:6379/0 -e API_HOST=0.0.0.0 -e API_PORT=8001 -p 8001:8000 asmblr-core:latest"""
    run_command(deploy_cmd)
    
    return True

def build_agents_service():
    """Construit et déploie le service agents"""
    log("Construction et déploiement du service agents...")
    
    # Construire l'image
    build_cmd = "docker build -t asmblr-agents:latest ./asmblr-agents"
    if not run_command(build_cmd):
        return False
    
    # Déployer le service
    deploy_cmd = """docker run -d --name asmblr-agents --network asmblr-network -e REDIS_URL=redis://redis:6379/0 -e OLLAMA_BASE_URL=http://ollama:11434 -e DEFAULT_MODEL=llama3.1:8b -e API_HOST=0.0.0.0 -e API_PORT=8002 -p 8002:8000 asmblr-agents:latest"""
    run_command(deploy_cmd)
    
    return True

def check_services():
    """Vérifie le statut des services"""
    log("Vérification des services...")
    
    services = [
        ("API Gateway", "http://localhost:8000/api/v1/health"),
        ("Core Service", "http://localhost:8001/api/v1/health"),
        ("Agents Service", "http://localhost:8002/api/v1/health")
    ]
    
    for service_name, url in services:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                log(f"✅ {service_name} - OK")
            else:
                log(f"❌ {service_name} - Status {response.status_code}")
        except Exception as e:
            log(f"❌ {service_name} - Error: {e}")

def show_status():
    """Affiche le statut des services"""
    log("Statut des services déployés:")
    print("=" * 50)
    
    services_info = [
        ("PostgreSQL", 5432, "asmblr-postgres"),
        ("Redis", 6379, "asmblr-redis"),
        ("Ollama", 11434, "asmblr-ollama"),
        ("Core Service", 8001, "asmblr-core"),
        ("Agents Service", 8002, "asmblr-agents")
    ]
    
    for service_name, port, container_name in services_info:
        try:
            result = subprocess.run(f"docker ps -f name={container_name}", shell=True, capture_output=True, text=True, check=False)
            if container_name in result.stdout:
                status = "RUNNING"
            else:
                status = "STOPPED"
        except:
            status = "UNKNOWN"
        
        print(f"  {service_name:15} | Port: {port:5} | Status: {status}")
    
    print("=" * 50)
    
    # URLs d'accès
    print("\n🌐 URLs d'accès:")
    print("  Core Service: http://localhost:8001")
    print("  Agents Service: http://localhost:8002")
    print("  Ollama: http://localhost:11434")
    print("  PostgreSQL: localhost:5432")
    print("  Redis: localhost:6379")

def cleanup():
    """Nettoie les containers existants"""
    log("Nettoyage des containers existants...")
    
    containers = ["asmblr-agents", "asmblr-core", "asmblr-ollama", "asmblr-redis", "asmblr-postgres"]
    
    for container in containers:
        run_command(f"docker stop {container}", check=False)
        run_command(f"docker rm {container}", check=False)
    
    run_command("docker network rm asmblr-network", check=False)

def main():
    """Point d'entrée principal"""
    if len(sys.argv) > 1 and sys.argv[1] == '--cleanup':
        # Mode nettoyage
        cleanup()
        print("Nettoyage terminé")
    else:
        # Mode déploiement
        log("🚀 Déploiement des micro-services Asmblr - Phase 2")
        print("=" * 50)
        
        try:
            # Étape 1: Vérification Docker
            if not check_docker():
                log("Docker n'est pas disponible, arrêt du déploiement", 'ERROR')
                return False
            
            # Étape 2: Création du réseau
            log("Création du réseau Docker...")
            run_command("docker network create asmblr-network", check=False)
            
            # Étape 3: Déploiement infrastructure
            deploy_infrastructure()
            
            # Étape 4: Attente infrastructure
            wait_for_infrastructure()
            
            # Étape 5: Téléchargement modèles
            pull_ollama_models()
            
            # Étape 6: Déploiement services
            if not build_core_service():
                log("Échec construction service core", 'ERROR')
                return False
            
            if not build_agents_service():
                log("Échec construction service agents", 'ERROR')
                return False
            
            # Étape 7: Vérification services
            time.sleep(5)  # Attendre que les services démarrent
            check_services()
            
            # Étape 8: Affichage statut
            show_status()
            
            log("🎉 Déploiement terminé avec succès !", 'SUCCESS')
            return True
            
        except Exception as e:
            log(f"Erreur lors du déploiement: {e}", 'ERROR')
            return False

if __name__ == "__main__":
    success = main()
    
    if success:
        print("\n🎯 Prochaines étapes:")
        print("1. Accédez au Core Service: http://localhost:8001")
        print("2. Accédez au Agents Service: http://localhost:8002")
        print("3. Consultez la documentation: http://localhost:8001/docs")
        print("4. Surveillez les logs: docker logs asmblr-core")
    else:
        print("\n❌ Déploiement échoué. Consultez les logs ci-dessus.")
        sys.exit(1)
