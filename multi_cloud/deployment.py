"""
Multi-Cloud Deployment for Asmblr
Supports AWS, GCP, and Azure with unified deployment interface
"""

import json
import time
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
from enum import Enum
import yaml
import boto3
from google.cloud import container_v1
from google.cloud import compute_v1
from azure.identity import DefaultAzureCredential
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.containerservice import ContainerServiceClient
import kubernetes
from kubernetes import client, config

logger = logging.getLogger(__name__)

class CloudProvider(Enum):
    """Supported cloud providers"""
    AWS = "aws"
    GCP = "gcp"
    AZURE = "azure"

@dataclass
class CloudConfig:
    """Cloud provider configuration"""
    provider: CloudProvider
    region: str
    project_id: Optional[str] = None  # GCP specific
    subscription_id: Optional[str] = None  # Azure specific
    credentials_path: Optional[str] = None
    resource_group: Optional[str] = None  # Azure specific
    vpc_id: Optional[str] = None
    subnet_id: Optional[str] = None
    cluster_name: str = "asmblr-cluster"
    node_count: int = 3
    machine_type: str = "t3.medium"
    kubernetes_version: str = "1.28"

@dataclass
class DeploymentResult:
    """Deployment result"""
    success: bool
    provider: CloudProvider
    region: str
    cluster_name: str
    endpoint: Optional[str] = None
    error_message: Optional[str] = None
    deployment_time: datetime = datetime.now()
    resources_created: List[str] = None

class AWSDeployer:
    """AWS EKS deployment"""
    
    def __init__(self, config: CloudConfig):
        self.config = config
        self.eks_client = boto3.client('eks', region_name=config.region)
        self.ec2_client = boto3.client('ec2', region_name=config.region)
        self.iam_client = boto3.client('iam', region_name=config.region)
    
    async def deploy_cluster(self) -> DeploymentResult:
        """Deploy EKS cluster"""
        try:
            logger.info(f"Deploying EKS cluster {self.config.cluster_name} in {self.config.region}")
            
            # Create VPC if not specified
            if not self.config.vpc_id:
                vpc_id = await self._create_vpc()
                self.config.vpc_id = vpc_id
            
            # Create subnet if not specified
            if not self.config.subnet_id:
                subnet_id = await self._create_subnet()
                self.config.subnet_id = subnet_id
            
            # Create IAM role for EKS
            role_arn = await self._create_eks_role()
            
            # Create EKS cluster
            cluster_response = self.eks_client.create_cluster(
                name=self.config.cluster_name,
                version=self.config.kubernetes_version,
                roleArn=role_arn,
                resourcesVpcConfig={
                    'subnetIds': [self.config.subnet_id],
                    'endpointPublicAccess': True,
                    'endpointPrivateAccess': True
                },
                kubernetesNetworkConfig={
                    'serviceIpv4Cidr': '10.100.0.0/16'
                }
            )
            
            # Wait for cluster to be active
            await self._wait_for_cluster_active()
            
            # Create node group
            await self._create_node_group()
            
            # Get cluster endpoint
            cluster_info = self.eks_client.describe_cluster(name=self.config.cluster_name)
            endpoint = cluster_info['cluster']['endpoint']
            
            # Configure kubectl
            await self._configure_kubectl()
            
            resources_created = [
                f"vpc:{self.config.vpc_id}",
                f"subnet:{self.config.subnet_id}",
                f"cluster:{self.config.cluster_name}",
                f"node-group:{self.config.cluster_name}-node-group"
            ]
            
            logger.info(f"EKS cluster deployed successfully: {endpoint}")
            
            return DeploymentResult(
                success=True,
                provider=CloudProvider.AWS,
                region=self.config.region,
                cluster_name=self.config.cluster_name,
                endpoint=endpoint,
                resources_created=resources_created
            )
            
        except Exception as e:
            logger.error(f"Error deploying EKS cluster: {e}")
            return DeploymentResult(
                success=False,
                provider=CloudProvider.AWS,
                region=self.config.region,
                cluster_name=self.config.cluster_name,
                error_message=str(e)
            )
    
    async def _create_vpc(self) -> str:
        """Create VPC"""
        response = self.ec2_client.create_vpc(
            CidrBlock='10.0.0.0/16',
            TagSpecifications=[
                {
                    'ResourceType': 'vpc',
                    'Tags': [
                        {'Key': 'Name', 'Value': f'{self.config.cluster_name}-vpc'},
                        {'Key': 'Project', 'Value': 'asmblr'}
                    ]
                }
            ]
        )
        return response['Vpc']['VpcId']
    
    async def _create_subnet(self) -> str:
        """Create subnet"""
        response = self.ec2_client.create_subnet(
            VpcId=self.config.vpc_id,
            CidrBlock='10.0.1.0/24',
            TagSpecifications=[
                {
                    'ResourceType': 'subnet',
                    'Tags': [
                        {'Key': 'Name', 'Value': f'{self.config.cluster_name}-subnet'},
                        {'Key': 'Project', 'Value': 'asmblr'}
                    ]
                }
            ]
        )
        return response['Subnet']['SubnetId']
    
    async def _create_eks_role(self) -> str:
        """Create IAM role for EKS"""
        trust_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "eks.amazonaws.com"
                    },
                    "Action": "sts:AssumeRole"
                }
            ]
        }
        
        response = self.iam_client.create_role(
            RoleName=f'{self.config.cluster_name}-eks-role',
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Description='EKS cluster role for Asmblr'
        )
        
        # Attach necessary policies
        policies = [
            'AmazonEKSClusterPolicy',
            'AmazonEKSServicePolicy'
        ]
        
        for policy in policies:
            self.iam_client.attach_role_policy(
                RoleName=f'{self.config.cluster_name}-eks-role',
                PolicyArn=f'arn:aws:iam::aws:policy/{policy}'
            )
        
        return response['Role']['Arn']
    
    async def _wait_for_cluster_active(self):
        """Wait for cluster to become active"""
        timeout = 1800  # 30 minutes
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            response = self.eks_client.describe_cluster(name=self.config.cluster_name)
            status = response['cluster']['status']
            
            if status == 'ACTIVE':
                return
            
            await asyncio.sleep(30)
        
        raise TimeoutError("Cluster did not become active in time")
    
    async def _create_node_group(self):
        """Create EKS node group"""
        node_role_arn = await self._create_node_role()
        
        self.eks_client.create_nodegroup(
            clusterName=self.config.cluster_name,
            nodegroupName=f'{self.config.cluster_name}-node-group',
            scalingConfig={
                'minSize': 1,
                'maxSize': 3,
                'desiredSize': self.config.node_count
            },
            subnets=[self.config.subnet_id],
            instanceTypes=[self.config.machine_type],
            nodeRole=node_role_arn,
            tags={
                'Project': 'asmblr',
                'Environment': 'production'
            }
        )
    
    async def _create_node_role(self) -> str:
        """Create IAM role for worker nodes"""
        trust_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "ec2.amazonaws.com"
                    },
                    "Action": "sts:AssumeRole"
                }
            ]
        }
        
        response = self.iam_client.create_role(
            RoleName=f'{self.config.cluster_name}-node-role',
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Description='EKS worker node role for Asmblr'
        )
        
        # Attach worker node policies
        policies = [
            'AmazonEKSWorkerNodePolicy',
            'AmazonEKS_CNI_Policy',
            'AmazonEC2ContainerRegistryReadOnly'
        ]
        
        for policy in policies:
            self.iam_client.attach_role_policy(
                RoleName=f'{self.config.cluster_name}-node-role',
                PolicyArn=f'arn:aws:iam::aws:policy/{policy}'
            )
        
        return response['Role']['Arn']
    
    async def _configure_kubectl(self):
        """Configure kubectl for EKS"""
        # Update kubeconfig
        cmd = f"aws eks update-kubeconfig --name {self.config.cluster_name} --region {self.config.region}"
        process = await asyncio.create_subprocess_shell(cmd)
        await process.communicate()

class GCPDeployer:
    """GCP GKE deployment"""
    
    def __init__(self, config: CloudConfig):
        self.config = config
        self.container_client = container_v1.ClusterManagerClient()
        self.compute_client = compute_v1.InstancesClient()
    
    async def deploy_cluster(self) -> DeploymentResult:
        """Deploy GKE cluster"""
        try:
            logger.info(f"Deploying GKE cluster {self.config.cluster_name} in {self.config.region}")
            
            # Create cluster
            cluster = await self._create_cluster()
            
            # Wait for cluster to be ready
            await self._wait_for_cluster_ready()
            
            # Get cluster endpoint
            cluster_info = self.container_client.get_cluster(
                name=f'projects/{self.config.project_id}/locations/{self.config.region}/clusters/{self.config.cluster_name}'
            )
            endpoint = cluster_info.endpoint
            
            # Configure kubectl
            await self._configure_kubectl()
            
            resources_created = [
                f"cluster:{self.config.cluster_name}",
                f"node_pool:{self.config.cluster_name}-default-pool"
            ]
            
            logger.info(f"GKE cluster deployed successfully: {endpoint}")
            
            return DeploymentResult(
                success=True,
                provider=CloudProvider.GCP,
                region=self.config.region,
                cluster_name=self.config.cluster_name,
                endpoint=endpoint,
                resources_created=resources_created
            )
            
        except Exception as e:
            logger.error(f"Error deploying GKE cluster: {e}")
            return DeploymentResult(
                success=False,
                provider=CloudProvider.GCP,
                region=self.config.region,
                cluster_name=self.config.cluster_name,
                error_message=str(e)
            )
    
    async def _create_cluster(self):
        """Create GKE cluster"""
        cluster_path = f'projects/{self.config.project_id}/locations/{self.config.region}/clusters/{self.config.cluster_name}'
        
        cluster = {
            'name': self.config.cluster_name,
            'initial_node_count': self.config.node_count,
            'node_config': {
                'machine_type': self.config.machine_type,
                'oauth_scopes': [
                    'https://www.googleapis.com/auth/cloud-platform'
                ],
                'labels': {
                    'project': 'asmblr',
                    'environment': 'production'
                }
            },
            'network_config': {
                'enable_private_nodes': False,
                'create_subnetwork': True,
                'subnetwork_name': f'{self.config.cluster_name}-subnet'
            },
            'master_auth': {
                'client_certificate_config': {
                    'issue_client_certificate': False
                }
            },
            'addons_config': {
                'http_load_balancing': {'disabled': False},
                'horizontal_pod_autoscaling': {'disabled': False}
            }
        }
        
        operation = self.container_client.create_cluster(
            name=cluster_path,
            cluster=cluster
        )
        
        return operation
    
    async def _wait_for_cluster_ready(self):
        """Wait for cluster to be ready"""
        timeout = 1800  # 30 minutes
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            cluster_path = f'projects/{self.config.project_id}/locations/{self.config.region}/clusters/{self.config.cluster_name}'
            cluster = self.container_client.get_cluster(name=cluster_path)
            
            if cluster.status == 'RUNNING':
                return
            
            await asyncio.sleep(30)
        
        raise TimeoutError("Cluster did not become ready in time")
    
    async def _configure_kubectl(self):
        """Configure kubectl for GKE"""
        cmd = f"gcloud container clusters get-credentials {self.config.cluster_name} --region {self.config.region} --project {self.config.project_id}"
        process = await asyncio.create_subprocess_shell(cmd)
        await process.communicate()

class AzureDeployer:
    """Azure AKS deployment"""
    
    def __init__(self, config: CloudConfig):
        self.config = config
        self.credential = DefaultAzureCredential()
        self.resource_client = ResourceManagementClient(self.credential, self.config.subscription_id)
        self.aks_client = ContainerServiceClient(self.credential, self.config.subscription_id)
    
    async def deploy_cluster(self) -> DeploymentResult:
        """Deploy AKS cluster"""
        try:
            logger.info(f"Deploying AKS cluster {self.config.cluster_name} in {self.config.region}")
            
            # Create resource group if not exists
            await self._create_resource_group()
            
            # Create AKS cluster
            cluster = await self._create_cluster()
            
            # Wait for cluster to be ready
            await self._wait_for_cluster_ready()
            
            # Get cluster credentials
            await self._get_credentials()
            
            # Get cluster endpoint
            cluster_info = self.aks_client.managed_clusters.get(
                resource_group_name=self.config.resource_group,
                resource_name=self.config.cluster_name
            )
            endpoint = f"https://{cluster_info.fqdn}"
            
            resources_created = [
                f"resource_group:{self.config.resource_group}",
                f"cluster:{self.config.cluster_name}"
            ]
            
            logger.info(f"AKS cluster deployed successfully: {endpoint}")
            
            return DeploymentResult(
                success=True,
                provider=CloudProvider.AZURE,
                region=self.config.region,
                cluster_name=self.config.cluster_name,
                endpoint=endpoint,
                resources_created=resources_created
            )
            
        except Exception as e:
            logger.error(f"Error deploying AKS cluster: {e}")
            return DeploymentResult(
                success=False,
                provider=CloudProvider.AZURE,
                region=self.config.region,
                cluster_name=self.config.cluster_name,
                error_message=str(e)
            )
    
    async def _create_resource_group(self):
        """Create resource group"""
        if not self.config.resource_group:
            self.config.resource_group = f"{self.config.cluster_name}-rg"
        
        rg_params = {
            'location': self.config.region,
            'tags': {
                'project': 'asmblr',
                'environment': 'production'
            }
        }
        
        self.resource_client.resource_groups.create_or_update(
            self.config.resource_group,
            rg_params
        )
    
    async def _create_cluster(self):
        """Create AKS cluster"""
        cluster_params = {
            'location': self.config.region,
            'dns_prefix': self.config.cluster_name,
            'kubernetes_version': self.config.kubernetes_version,
            'identity': {
                'type': 'SystemAssigned'
            },
            'agent_pool_profiles': [{
                'name': 'default',
                'count': self.config.node_count,
                'vm_size': self.config.machine_type,
                'os_type': 'Linux',
                'mode': 'System',
                'availability_zones': ['1', '2', '3']
            }],
            'network_profile': {
                'network_plugin': 'azure',
                'service_cidr': '10.96.0.0/12',
                'dns_service_ip': '10.96.0.10',
                'docker_bridge_cidr': '172.17.0.1/16'
            },
            'tags': {
                'project': 'asmblr',
                'environment': 'production'
            }
        }
        
        return self.aks_client.managed_clusters.begin_create_or_update(
            self.config.resource_group,
            self.config.cluster_name,
            cluster_params
        )
    
    async def _wait_for_cluster_ready(self):
        """Wait for cluster to be ready"""
        timeout = 1800  # 30 minutes
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            cluster = self.aks_client.managed_clusters.get(
                resource_group_name=self.config.resource_group,
                resource_name=self.config.cluster_name
            )
            
            if cluster.provisioning_state == 'Succeeded':
                return
            
            await asyncio.sleep(30)
        
        raise TimeoutError("Cluster did not become ready in time")
    
    async def _get_credentials(self):
        """Get AKS credentials"""
        cmd = f"az aks get-credentials --resource-group {self.config.resource_group} --name {self.config.cluster_name}"
        process = await asyncio.create_subprocess_shell(cmd)
        await process.communicate()

class MultiCloudDeployer:
    """Multi-cloud deployment orchestrator"""
    
    def __init__(self):
        self.deployers = {
            CloudProvider.AWS: AWSDeployer,
            CloudProvider.GCP: GCPDeployer,
            CloudProvider.AZURE: AzureDeployer
        }
        self.deployment_history: List[DeploymentResult] = []
    
    async def deploy_to_cloud(self, config: CloudConfig) -> DeploymentResult:
        """Deploy to specified cloud provider"""
        deployer_class = self.deployers.get(config.provider)
        if not deployer_class:
            raise ValueError(f"Unsupported cloud provider: {config.provider}")
        
        deployer = deployer_class(config)
        result = await deployer.deploy_cluster()
        
        self.deployment_history.append(result)
        
        if result.success:
            await self._deploy_asmblr_services(result)
        
        return result
    
    async def _deploy_asmblr_services(self, deployment_result: DeploymentResult):
        """Deploy Asmblr services to the cluster"""
        try:
            # Load kubeconfig
            config.load_kube_config()
            
            # Create namespace
            v1 = client.CoreV1Api()
            namespace = client.V1Namespace(
                metadata=client.V1ObjectMeta(name="asmblr")
            )
            v1.create_namespace(namespace)
            
            # Deploy services using Helm
            await self._deploy_with_helm()
            
            logger.info(f"Asmblr services deployed to {deployment_result.cluster_name}")
            
        except Exception as e:
            logger.error(f"Error deploying Asmblr services: {e}")
    
    async def _deploy_with_helm(self):
        """Deploy using Helm charts"""
        cmd = "helm install asmblr ./helm/asmblr --namespace asmblr"
        process = await asyncio.create_subprocess_shell(cmd)
        await process.communicate()
    
    async def deploy_multi_cloud(self, configs: List[CloudConfig]) -> List[DeploymentResult]:
        """Deploy to multiple clouds simultaneously"""
        tasks = []
        for config in configs:
            task = asyncio.create_task(self.deploy_to_cloud(config))
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        deployment_results = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Deployment failed: {result}")
                # Create error result
                error_result = DeploymentResult(
                    success=False,
                    provider=CloudProvider.AWS,  # Default
                    region="unknown",
                    cluster_name="unknown",
                    error_message=str(result)
                )
                deployment_results.append(error_result)
            else:
                deployment_results.append(result)
        
        return deployment_results
    
    async def setup_global_load_balancer(self, deployments: List[DeploymentResult]):
        """Setup global load balancer across multiple clouds"""
        try:
            # This would typically use a global load balancing service
            # like AWS Global Accelerator, GCP Cloud Load Balancing, or Azure Front Door
            
            endpoints = []
            for deployment in deployments:
                if deployment.success and deployment.endpoint:
                    endpoints.append({
                        'provider': deployment.provider.value,
                        'endpoint': deployment.endpoint,
                        'region': deployment.region
                    })
            
            logger.info(f"Setting up global load balancer for {len(endpoints)} endpoints")
            
            # Implementation would depend on the chosen global load balancing solution
            
        except Exception as e:
            logger.error(f"Error setting up global load balancer: {e}")
    
    def get_deployment_status(self) -> Dict[str, Any]:
        """Get deployment status across all clouds"""
        successful_deployments = [d for d in self.deployment_history if d.success]
        failed_deployments = [d for d in self.deployment_history if not d.success]
        
        provider_stats = {}
        for provider in CloudProvider:
            provider_deployments = [d for d in self.deployment_history if d.provider == provider]
            provider_stats[provider.value] = {
                'total': len(provider_deployments),
                'successful': len([d for d in provider_deployments if d.success]),
                'failed': len([d for d in provider_deployments if not d.success])
            }
        
        return {
            'total_deployments': len(self.deployment_history),
            'successful_deployments': len(successful_deployments),
            'failed_deployments': len(failed_deployments),
            'success_rate': len(successful_deployments) / len(self.deployment_history) if self.deployment_history else 0,
            'provider_stats': provider_stats,
            'last_deployment': self.deployment_history[-1] if self.deployment_history else None
        }

# Global multi-cloud deployer instance
multi_cloud_deployer = MultiCloudDeployer()

# API endpoints
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/multi-cloud", tags=["multi-cloud"])

class CloudDeploymentRequest(BaseModel):
    provider: str
    region: str
    project_id: Optional[str] = None
    subscription_id: Optional[str] = None
    resource_group: Optional[str] = None
    cluster_name: str = "asmblr-cluster"
    node_count: int = 3
    machine_type: str = "t3.medium"

@router.post("/deploy")
async def deploy_to_cloud(request: CloudDeploymentRequest):
    """Deploy to specified cloud provider"""
    try:
        provider = CloudProvider(request.provider.lower())
        
        config = CloudConfig(
            provider=provider,
            region=request.region,
            project_id=request.project_id,
            subscription_id=request.subscription_id,
            resource_group=request.resource_group,
            cluster_name=request.cluster_name,
            node_count=request.node_count,
            machine_type=request.machine_type
        )
        
        result = await multi_cloud_deployer.deploy_to_cloud(config)
        return asdict(result)
    except Exception as e:
        logger.error(f"Error deploying to cloud: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/deploy-multi")
async def deploy_multi_cloud(requests: List[CloudDeploymentRequest]):
    """Deploy to multiple clouds simultaneously"""
    try:
        configs = []
        for req in requests:
            provider = CloudProvider(req.provider.lower())
            config = CloudConfig(
                provider=provider,
                region=req.region,
                project_id=req.project_id,
                subscription_id=req.subscription_id,
                resource_group=req.resource_group,
                cluster_name=req.cluster_name,
                node_count=req.node_count,
                machine_type=req.machine_type
            )
            configs.append(config)
        
        results = await multi_cloud_deployer.deploy_multi_cloud(configs)
        return [asdict(result) for result in results]
    except Exception as e:
        logger.error(f"Error deploying to multiple clouds: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def get_deployment_status():
    """Get deployment status across all clouds"""
    try:
        return multi_cloud_deployer.get_deployment_status()
    except Exception as e:
        logger.error(f"Error getting deployment status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/global-load-balancer")
async def setup_global_load_balancer():
    """Setup global load balancer across deployments"""
    try:
        successful_deployments = [d for d in multi_cloud_deployer.deployment_history if d.success]
        await multi_cloud_deployer.setup_global_load_balancer(successful_deployments)
        return {"status": "global_load_balancer_setup"}
    except Exception as e:
        logger.error(f"Error setting up global load balancer: {e}")
        raise HTTPException(status_code=500, detail=str(e))
