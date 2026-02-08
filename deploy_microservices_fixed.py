#!/usr/bin/env python
"""
Script de déploiement automatisé pour les micro-services Asmblr
Phase 2: Déploiement de l'architecture micro-services
"""

import os
import sys
import time
import subprocess
import requests
from pathlib import Path

class MicroservicesDeployer:
    def __init__(self):
        self.services = {
            'postgres': {
                'name': 'asmblr-postgres',
                'port': 5432,
                'image': 'postgres:15-alpine',
                'env_vars': {
                    'POSTGRES_DB': 'asmblr',
                    'POSTGRES_USER': 'asmblr',
                    'POSTGRES_PASSWORD': 'asmblr_secure_password'
                }
            },
            'redis': {
                'name': 'asmblr-redis',
                'port': 6379,
                'image': 'redis:7-alpine',
                'env_vars': {}
            },
            'ollama': {
                'name': 'asmblr-ollama',
                'port': 11434,
                'image': 'ollama/ollama',
                'env_vars': {
                    'OLLAMA_HOST': '0.0.0.0'
                }
            },
            'core': {
                'name': 'asmblr-core',
                'port': 8001,
                'build_context': './asmblr-core',
                'health_url': 'http://localhost:8001/api/v1/health'
            },
            'agents': {
                'name': 'asmblr-agents',
                'port': 8002,
                'build_context': './asmblr-agents',
                'health_url': 'http://localhost:8002/api/v1/health'
            },
            'media': {
                'name': 'asmblr-media',
                'port': 8003,
                'build_context': './asmblr-media',
                'health_url': 'http://localhost:8003/api/v1/health'
            },
            'gateway': {
                'name': 'asmblr-gateway',
                'port': 8000,
                'build_context': './orchestrator',
                'health_url': 'http://localhost:8000/api/v1/health'
            }
        }
        
        self.network_name = 'asmblr-network'
        
    def log(self, message, level='INFO'):
        """Logger avec timestamps"""
        timestamp = time.strftime('%H:%M:%S')
        print(f"[{timestamp}] {level}: {message}")
    
    def run_command(self, command, check=True, capture_output=False):
        """Exécute une commande shell"""
        try:
            if capture_output:
                result = subprocess.run(command, shell=True, capture_output=True, text=True, check=check)
                return result.stdout.strip(), result.stderr.strip()
            else:
                subprocess.run(command, shell=True, check=check)
                return None, None
        except subprocess.CalledProcessError as e:
            self.log(f"Command failed: {command}", 'ERROR')
            self.log(f"Error: {e}", 'ERROR')
            return None, str(e)
    
    def check_docker(self):
        """Vérifie si Docker est disponible"""
        self.log("Vérification de Docker...")
        
        stdout, stderr = self.run_command("docker --version", capture_output=True)
        if stdout:
            self.log(f"Docker version: {stdout}")
            return True
        else:
            self.log("Docker n'est pas disponible", 'ERROR')
            return False
    
    def create_network(self):
        """Crée le réseau Docker"""
        self.log("Création du réseau Docker...")
        
        stdout, stderr = self.run_command(f"docker network create {self.network_name}", check=False, capture_output=True)
        if 'already exists' in stderr:
            self.log("Réseau déjà existant")
        else:
            self.log("Réseau créé avec succès")
    
    def deploy_infrastructure(self):
        """Déploie l'infrastructure de base (PostgreSQL, Redis, Ollama)"""
        self.log("Déploiement de l'infrastructure...")
        
        # PostgreSQL
        self.log("Déploiement de PostgreSQL...")
        postgres_cmd = f"""docker run -d --name {self.services['postgres']['name']} --network {self.network_name} -e POSTGRES_DB={self.services['postgres']['env_vars']['POSTGRES_DB']} -e POSTGRES_USER={self.services['postgres']['env_vars']['POSTGRES_USER']} -e POSTGRES_PASSWORD={self.services['postgres']['env_vars']['POSTGRES_PASSWORD']} -p {self.services['postgres']['port']}:5432 {self.services['postgres']['image']}"""
        self.run_command(postgres_cmd)
        
        # Redis
        self.log("Déploiement de Redis...")
        redis_cmd = f"""docker run -d --name {self.services['redis']['name']} --network {self.network_name} -p {self.services['redis']['port']}:6379 {self.services['redis']['image']}"""
        self.run_command(redis_cmd)
        
        # Ollama
        self.log("Déploiement d'Ollama...")
        ollama_cmd = f"""docker run -d --name {self.services['ollama']['name']} --network {self.network_name} -p {self.services['ollama']['port']}:11434 {self.services['ollama']['image']}"""
        self.run_command(ollama_cmd)
        
        self.log("Infrastructure déployée avec succès")
    
    def wait_for_infrastructure(self):
        """Attend que l'infrastructure soit prête"""
        self.log("Attente de l'infrastructure...")
        
        # Attendre PostgreSQL
        self.log("Attente de PostgreSQL...")
        for i in range(30):  # 30 secondes max
            stdout, stderr = self.run_command(f"docker exec {self.services['postgres']['name']} pg_isready -U {self.services['postgres']['env_vars']['POSTGRES_USER']}", check=False, capture_output=True)
            if 'accepting connections' in stdout:
                self.log("PostgreSQL prêt")
                break
            time.sleep(1)
        else:
            self.log("PostgreSQL n'est pas prêt après 30 secondes", 'WARNING')
        
        # Attendre Redis
        self.log("Attente de Redis...")
        for i in range(10):  # 10 secondes max
            stdout, stderr = self.run_command(f"docker exec {self.services['redis']['name']} redis-cli ping", check=False, capture_output=True)
            if 'PONG' in stdout:
                self.log("Redis prêt")
                break
            time.sleep(1)
        else:
            self.log("Redis n'est pas prêt après 10 secondes", 'WARNING')
        
        # Attendre Ollama
        self.log("Attente d'Ollama...")
        for i in range(30):  # 30 secondes max
            try:
                response = requests.get(f"http://localhost:{self.services['ollama']['port']}/api/tags", timeout=2)
                if response.status_code == 200:
                    self.log("Ollama prêt")
                    break
            except:
                pass
            time.sleep(1)
        else:
            self.log("Ollama n'est pas prêt après 30 secondes", 'WARNING')
    
    def pull_ollama_models(self):
        """Télécharge les modèles Ollama requis"""
        self.log("Téléchargement des modèles Ollama...")
        
        models = ['llama3.1:8b', 'qwen2.5-coder:7b']
        
        for model in models:
            self.log(f"Téléchargement du modèle: {model}")
            stdout, stderr = self.run_command(f"docker exec {self.services['ollama']['name']} ollama pull {model}", check=False, capture_output=True)
            if stderr and 'error' in stderr.lower():
                self.log(f"Erreur téléchargement {model}: {stderr}", 'ERROR')
            else:
                self.log(f"Modèle {model} téléchargé avec succès")
    
    def build_service(self, service_name):
        """Construit l'image Docker d'un service"""
        service = self.services[service_name]
        if 'build_context' not in service:
            return True
        
        self.log(f"Construction de l'image {service_name}...")
        
        build_cmd = f"docker build -t asmblr-{service_name}:latest {service['build_context']}"
        stdout, stderr = self.run_command(build_cmd, check=False, capture_output=True)
        
        if stderr and 'error' in stderr.lower():
            self.log(f"Erreur construction {service_name}: {stderr}", 'ERROR')
            return False
        else:
            self.log(f"Image {service_name} construite avec succès")
            return True
    
    def deploy_service(self, service_name):
        """Déploie un service spécifique"""
        service = self.services[service_name]
        
        self.log(f"Déploiement du service {service_name}...")
        
        if 'build_context' in service:
            # Service avec build
            deploy_cmd = f"""docker run -d --name {service['name']} --network {self.network_name} -p {service['port']}:8000 asmblr-{service_name}:latest"""
        else:
            # Service avec image directe
            env_vars = ' '.join([f"-e {k}={v}" for k, v in service.get('env_vars', {}).items()])
            deploy_cmd = f"""docker run -d --name {service['name']} --network {self.network_name} -p {service['port']}:5432 {env_vars} {service['image']}"""
        
        self.run_command(deploy_cmd)
        self.log(f"Service {service_name} déployé avec succès")
    
    def check_service_health(self, service_name):
        """Vérifie le health check d'un service"""
        service = self.services[service_name]
        
        if 'health_url' not in service:
            return True
        
        self.log(f"Vérification du service {service_name}...")
        
        for i in range(30):  # 30 secondes max
            try:
                response = requests.get(service['health_url'], timeout=2)
                if response.status_code == 200:
                    self.log(f"Service {service_name} prêt")
                    return True
            except:
                pass
            time.sleep(1)
        
        self.log(f"Service {service_name} n'est pas prêt après 30 secondes", 'WARNING')
        return False
    
    def deploy_all_services(self):
        """Déploie tous les services dans le bon ordre"""
        services_order = ['postgres', 'redis', 'ollama', 'core', 'agents', 'media', 'gateway']
        
        for service_name in services_order:
            if service_name in ['postgres', 'redis', 'ollama']:
                continue  # Déjà déployé dans l'infrastructure
            
            # Construire l'image
            if not self.build_service(service_name):
                self.log(f"Échec construction {service_name}, arrêt du déploiement", 'ERROR')
                return False
            
            # Déployer le service
            self.deploy_service(service_name)
            
            # Attendre que le service soit prêt
            if not self.check_service_health(service_name):
                self.log(f"Service {service_name} n'est pas prêt, continuation...", 'WARNING')
        
        return True
    
    def run_integration_tests(self):
        """Exécute les tests d'intégration"""
        self.log("Exécution des tests d'intégration...")
        
        # Test 1: Health checks
        self.log("Test 1: Health checks de tous les services")
        health_urls = [
            ('API Gateway', 'http://localhost:8000/api/v1/health'),
            ('Core Service', 'http://localhost:8001/api/v1/health'),
            ('Agents Service', 'http://localhost:8002/api/v1/health'),
            ('Media Service', 'http://localhost:8003/api/v1/health')
        ]
        
        for service_name, url in health_urls:
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    self.log(f"✅ {service_name} - OK")
                else:
                    self.log(f"❌ {service_name} - Status {response.status_code}")
            except Exception as e:
                self.log(f"❌ {service_name} - Error: {e}")
        
        # Test 2: Communication inter-services
        self.log("Test 2: Communication inter-services")
        try:
            # Test création de pipeline via API Gateway
            response = requests.post(
                'http://localhost:8000/api/v1/core/pipelines',
                json={"topic": "Test integration", "config": {"mode": "test"}},
                timeout=5
            )
            if response.status_code == 201:
                self.log("✅ Communication API Gateway → Core - OK")
            else:
                self.log(f"❌ Communication API Gateway → Core - Status {response.status_code}")
        except Exception as e:
            self.log(f"❌ Communication inter-services - Error: {e}")
    
    def show_status(self):
        """Affiche le statut de tous les services"""
        self.log("Statut des services déployés:")
        print("=" * 60)
        
        services_order = ['postgres', 'redis', 'ollama', 'core', 'agents', 'media', 'gateway']
        
        for service_name in services_order:
            service = self.services[service_name]
            
            # Vérifier si le container existe
            stdout, stderr = self.run_command(f"docker ps -f name={service['name']} --format 'table {{{{.Status}}}'", capture_output=True)
            
            if service['name'] in stdout:
                status = stdout.split('\n')[1].strip()
                port = service['port']
                service_display = f"{service_name.upper():15}"
                port_display = f"Port: {port:5}"
                status_display = f"Status: {status}"
                print(f"  {service_display} | {port_display} | {status_display}")
            else:
                service_display = f"{service_name.upper():15}"
                port_display = f"Port: {service['port']:5}"
                status_display = "Status: NOT RUNNING"
                print(f"  {service_display} | {port_display} | {status_display}")
        
        print("=" * 60)
        
        # URLs d'accès
        print("\n🌐 URLs d'accès:")
        print("  API Gateway: http://localhost:8000")
        print("  Core Service: http://localhost:8001")
        print("  Agents Service: http://localhost:8002")
        print("  Media Service: http://localhost:8003")
        print("  UI: http://localhost:3000")
        print("  Ollama: http://localhost:11434")
        print("  PostgreSQL: localhost:5432")
        print("  Redis: localhost:6379")
    
    def cleanup(self):
        """Nettoie les containers existants"""
        self.log("Nettoyage des containers existants...")
        
        services_order = ['gateway', 'media', 'agents', 'core', 'ollama', 'redis', 'postgres']
        
        for service_name in services_order:
            service = self.services[service_name]
            self.run_command(f"docker stop {service['name']}", check=False)
            self.run_command(f"docker rm {service['name']}", check=False)
        
        self.run_command(f"docker network rm {self.network_name}", check=False)
    
    def deploy(self):
        """Méthode principale de déploiement"""
        self.log("🚀 Déploiement des micro-services Asmblr - Phase 2")
        print("=" * 60)
        
        try:
            # Étape 1: Vérification Docker
            if not self.check_docker():
                self.log("Docker n'est pas disponible, arrêt du déploiement", 'ERROR')
                return False
            
            # Étape 2: Création du réseau
            self.create_network()
            
            # Étape 3: Déploiement infrastructure
            self.deploy_infrastructure()
            
            # Étape 4: Attente infrastructure
            self.wait_for_infrastructure()
            
            # Étape 5: Téléchargement modèles
            self.pull_ollama_models()
            
            # Étape 6: Déploiement services
            if not self.deploy_all_services():
                self.log("Échec déploiement services", 'ERROR')
                return False
            
            # Étape 7: Tests d'intégration
            self.run_integration_tests()
            
            # Étape 8: Affichage statut
            self.show_status()
            
            self.log("🎉 Déploiement terminé avec succès !", 'SUCCESS')
            return True
            
        except Exception as e:
            self.log(f"Erreur lors du déploiement: {e}", 'ERROR')
            return False

def main():
    """Point d'entrée principal"""
    if len(sys.argv) > 1 and sys.argv[1] == '--cleanup':
        # Mode nettoyage
        deployer = MicroservicesDeployer()
        deployer.cleanup()
        print("Nettoyage terminé")
    else:
        # Mode déploiement
        deployer = MicroservicesDeployer()
        success = deployer.deploy()
        
        if success:
            print("\n🎯 Prochaines étapes:")
            print("1. Accédez à l'API Gateway: http://localhost:8000")
            print("2. Accédez à l'UI: http://localhost:3000")
            print("3. Consultez la documentation: http://localhost:8000/docs")
            print("4. Surveillez les logs: docker logs asmblr-gateway")
        else:
            print("\n❌ Déploiement échoué. Consultez les logs ci-dessus.")
            sys.exit(1)

if __name__ == "__main__":
    main()
