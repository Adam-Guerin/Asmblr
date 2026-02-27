"""
Multi-Cloud Support for Asmblr
Advanced cloud abstraction layer with intelligent provider management and cost optimization
"""

import asyncio
import json
import time
from typing import Dict, Any, Optional, List, Union, Callable
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
import boto3
import azure.storage.blob
import google.cloud.storage
from loguru import logger
import redis.asyncio as redis

class CloudProvider(Enum):
    """Supported cloud providers"""
    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"
    DIGITAL_OCEAN = "digitalocean"
    VULTR = "vultr"
    LINODE = "linode"
    ORACLE = "oracle"
    IBM = "ibm"

class ResourceType(Enum):
    """Resource types that can be provisioned"""
    COMPUTE = "compute"
    STORAGE = "storage"
    DATABASE = "database"
    NETWORK = "network"
    LOAD_BALANCER = "load_balancer"
    DNS = "dns"
    CDN = "cdn"
    FIREWALL = "firewall"
    MONITORING = "monitoring"
    BACKUP = "backup"

class InstanceType(Enum):
    """Instance types for compute resources"""
    GENERAL_PURPOSE = "general_purpose"
    COMPUTE_OPTIMIZED = "compute_optimized"
    MEMORY_OPTIMIZED = "memory_optimized"
    STORAGE_OPTIMIZED = "storage_optimized"
    GPU = "gpu"
    BURSTABLE = "burstable"
    SPOT = "spot"

class StorageType(Enum):
    """Storage types"""
    STANDARD = "standard"
    INFREQUENT_ACCESS = "infrequent_access"
    ARCHIVE = "archive"
    COLD = "cold"
    HOT = "hot"

@dataclass
class CloudResource:
    """Cloud resource definition"""
    id: str
    name: str
    provider: CloudProvider
    resource_type: ResourceType
    instance_type: Optional[InstanceType] = None
    storage_type: Optional[StorageType] = None
    region: str = "us-east-1"
    size: str = "medium"
    count: int = 1
    tags: Dict[str, str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = {}
        if self.metadata is None:
            self.metadata = {}

@dataclass
class CloudCost:
    """Cloud cost information"""
    provider: CloudProvider
    resource_type: ResourceType
    hourly_cost: float
    monthly_cost: float
    currency: str = "USD"
    region: str = "us-east-1"
    instance_type: Optional[InstanceType] = None
    storage_type: Optional[StorageType] = None
    size: str = "medium"
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class CloudMetrics:
    """Cloud performance metrics"""
    provider: CloudProvider
    resource_id: str
    cpu_utilization: float
    memory_utilization: float
    disk_utilization: float
    network_in: float
    network_out: float
    request_count: int
    error_rate: float
    uptime_percentage: float
    timestamp: datetime
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class CloudProviderAdapter:
    """Base adapter for cloud providers"""
    
    def __init__(self, provider: CloudProvider, config: Dict[str, Any]):
        self.provider = provider
        self.config = config
        self.client = None
        self.initialized = False
    
    async def initialize(self):
        """Initialize provider client"""
        raise NotImplementedError
    
    async def create_resource(self, resource: CloudResource) -> Dict[str, Any]:
        """Create a cloud resource"""
        raise NotImplementedError
    
    async def delete_resource(self, resource_id: str) -> bool:
        """Delete a cloud resource"""
        raise NotImplementedError
    
    async def get_resource(self, resource_id: str) -> Dict[str, Any]:
        """Get resource information"""
        raise NotImplementedError
    
    async def list_resources(self, resource_type: ResourceType) -> List[Dict[str, Any]]:
        """List resources of a given type"""
        raise NotImplementedError
    
    async def get_metrics(self, resource_id: str) -> CloudMetrics:
        """Get resource metrics"""
        raise NotImplementedError
    
    async def scale_resource(self, resource_id: str, target_count: int) -> bool:
        """Scale a resource"""
        raise NotImplementedError
    
    async def get_cost_estimate(self, resource: CloudResource) -> CloudCost:
        """Get cost estimate for a resource"""
        raise NotImplementedError
    
    async def shutdown(self):
        """Shutdown provider client"""
        if self.client:
            # Provider-specific shutdown logic
            pass

class AWSAdapter(CloudProviderAdapter):
    """AWS cloud provider adapter"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(CloudProvider.AWS, config)
        self.session = None
    
    async def initialize(self):
        """Initialize AWS client"""
        try:
            self.session = boto3.Session(
                aws_access_key_id=self.config.get('aws_access_key_id'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY', self.config.get('aws_secret_access_key')),
                region_name=self.config.get('region', 'us-east-1')
            )
            self.initialized = True
            logger.info("AWS adapter initialized")
        except Exception as e:
            logger.error(f"Failed to initialize AWS adapter: {e}")
            raise
    
    async def create_resource(self, resource: CloudResource) -> Dict[str, Any]:
        """Create AWS resource"""
        try:
            if resource.resource_type == ResourceType.COMPUTE:
                return await self._create_ec2_instance(resource)
            elif resource.resource_type == ResourceType.STORAGE:
                return await self._create_s3_bucket(resource)
            elif resource.resource_type == ResourceType.DATABASE:
                return await self._create_rds_instance(resource)
            elif resource.resource_type == ResourceType.NETWORK:
                return await self._create_vpc(resource)
            else:
                raise ValueError(f"Unsupported resource type: {resource.resource_type}")
                
        except Exception as e:
            logger.error(f"Failed to create AWS resource: {e}")
            raise
    
    async def _create_ec2_instance(self, resource: CloudResource) -> Dict[str, Any]:
        """Create EC2 instance"""
        try:
            ec2 = self.session.client('ec2')
            
            # Map instance type to AWS instance type
            instance_mapping = {
                InstanceType.GENERAL_PURPOSE: 't3.medium',
                InstanceType.COMPUTE_OPTIMIZED: 'c5.large',
                InstanceType.MEMORY_OPTIMIZED: 'r5.large',
                InstanceType.GPU: 'p3.2xlarge',
                InstanceType.BURSTABLE: 't3.medium',
                InstanceType.SPOT: 't3.micro'
            }
            
            instance_type = instance_mapping.get(resource.instance_type, 't3.medium')
            
            # Create instance
            response = ec2.run_instances(
                ImageId='ami-0c553e8b9a3f4d6e8c',
                MinCount=resource.count,
                MaxCount=resource.count,
                InstanceType=instance_type,
                TagSpecifications=[
                    {
                        'Key': 'Name',
                        'Value': resource.name,
                        'ResourceType': resource.resource_type.value
                    }
                ]
            )
            
            instances = response['Instances']
            if instances:
                return {
                    'resource_id': instances[0]['InstanceId'],
                    'instance_type': instances[0]['InstanceType'],
                    'state': instances[0]['State']['Name'],
                    'region': instances[0]['Placement']['AvailabilityZone'],
                    'tags': instances[0]['Tags']
                }
            else:
                raise Exception("No instances created")
                
        except Exception as e:
            logger.error(f"Failed to create EC2 instance: {e}")
            raise
    
    async def _create_s3_bucket(self, resource: CloudResource) -> Dict[str, Any]:
        """Create S3 bucket"""
        try:
            s3 = self.session.client('s3')
            
            # Create bucket
            s3.create_bucket(Bucket=resource.name)
            
            return {
                'resource_id': resource.name,
                'bucket_name': resource.name,
                'region': self.config.get('region', 'us-east-1'),
                'created': True
            }
            
        except Exception as e:
            logger.error(f"Failed to create S3 bucket: {e}")
            raise
    
    async def _create_rds_instance(self, resource: CloudResource) -> Dict[str, Any]:
        """Create RDS instance"""
        try:
            rds = self.session.client('rds')
            
            # Create RDS instance
            response = rds.create_db_instance(
                DBInstanceIdentifier=resource.name,
                DBInstanceClass='db.t3.medium',
                Engine='postgres',
                MasterUsername='postgres',
                MasterUserPassword=os.getenv('RDS_MASTER_PASSWORD', 'change_me_in_production'),
                AllocatedStorage=20,
                StorageType='gp2',
                StorageEncrypted=True,
                MultiAZ=True,
                Tags=[
                    {
                        'Key': 'Name',
                        'Value': resource.name,
                        'ResourceType': resource.resource_type.value
                    }
                ]
            )
            
            return {
                'resource_id': response['DBInstance']['DBInstanceIdentifier'],
                'engine': response['DBInstance']['Engine'],
                'status': response['DBInstance']['DBInstanceStatus'],
                'region': self.config.get('region', 'us-east-1'),
                'created': True
            }
            
        except Exception as e:
            logger.error(f"Failed to create RDS instance: {e}")
            raise
    
    async def _create_vpc(self, resource: CloudResource) -> Dict[str, Any]:
        """Create VPC"""
        try:
            ec2 = self.session.client('ec2')
            
            # Create VPC
            response = ec2.create_vpc(
                CidrBlock='10.0.0.0/16',
                TagSpecifications=[
                    {
                        'Key': 'Name',
                        'Value': resource.name,
                        'ResourceType': resource.resource_type.value
                    }
                ]
            )
            
            return {
                'resource_id': response['Vpc']['VpcId'],
                'cidr_block': response['Vpc']['CidrBlock'],
                'state': response['Vpc']['State'],
                'region': self.config.get('region', 'us-east-1'),
                'created': True
            }
            
        except Exception as e:
            logger.error(f"Failed to create VPC: {e}")
            raise
    
    async def delete_resource(self, resource_id: str) -> bool:
        """Delete AWS resource"""
        try:
            # Implementation would depend on resource type
            # This is a simplified version
            logger.info(f"Deleting AWS resource: {resource_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete AWS resource: {e}")
            return False
    
    async def get_resource(self, resource_id: str) -> Dict[str, Any]:
        """Get resource information"""
        try:
            # Implementation would depend on resource type
            logger.info(f"Getting AWS resource: {resource_id}")
            return {'resource_id': resource_id, 'status': 'active'}
            
        except Exception as e:
            logger.error(f"Failed to get AWS resource: {e}")
            return {}
    
    async def list_resources(self, resource_type: ResourceType) -> List[Dict[str, Any]]:
        """List resources of a given type"""
        try:
            if resource_type == ResourceType.COMPUTE:
                ec2 = self.session.client('ec2')
                response = ec2.describe_instances()
                return [
                    {
                        'resource_id': instance['InstanceId'],
                        'instance_type': instance['InstanceType'],
                        'state': instance['State']['Name'],
                        'region': instance['Placement']['AvailabilityZone']
                    }
                    for instance in response['Instances']
                ]
            # Add other resource types as needed
            return []
            
        except Exception as e:
            logger.error(f"Failed to list AWS resources: {e}")
            return []
    
    async def get_metrics(self, resource_id: str) -> CloudMetrics:
        """Get resource metrics"""
        try:
            # Implementation would use CloudWatch
            logger.info(f"Getting metrics for AWS resource: {resource_id}")
            
            return CloudMetrics(
                provider=CloudProvider.AWS,
                resource_id=resource_id,
                cpu_utilization=0.0,
                memory_utilization=0.0,
                disk_utilization=0.0,
                network_in=0.0,
                network_out=0.0,
                request_count=0,
                error_rate=0.0,
                uptime_percentage=100.0,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Failed to get AWS metrics: {e}")
            return CloudMetrics(
                provider=CloudProvider.AWS,
                resource_id=resource_id,
                timestamp=datetime.now()
            )
    
    async def scale_resource(self, resource_id: str, target_count: int) -> bool:
        """Scale a resource"""
        try:
            if resource_id.startswith('i-'):
                ec2 = self.session.client('ec2')
                response = ec2.modify_instance_count(
                    InstanceId=resource_id,
                    MinCount=1,
                    MaxCount=target_count
                )
                return response['Successful']
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to scale AWS resource: {e}")
            return False
    
    async def get_cost_estimate(self, resource: CloudResource) -> CloudCost:
        """Get cost estimate for a resource"""
        try:
            # Simplified cost calculation
            base_costs = {
                ResourceType.COMPUTE: {
                    InstanceType.GENERAL_PURPOSE: 0.1,
                    InstanceType.COMPUTE_OPTIMIZED: 0.2,
                    InstanceType.MEMORY_OPTIMIZED: 0.15,
                    InstanceType.GPU: 0.8,
                    InstanceType.BURSTABLE: 0.05,
                    InstanceType.SPOT: 0.01
                },
                ResourceType.STORAGE: {
                    StorageType.STANDARD: 0.023,
                    StorageType.INFREQUENT_ACCESS: 0.025,
                    StorageType.ARCHIVE: 0.01,
                    StorageType.COLD: 0.004,
                    StorageType.HOT: 1.0
                },
                ResourceType.DATABASE: {
                    'db.t3.medium': 0.2,
                    'db.r5.large': 0.5,
                    'db.t3.large': 0.3
                }
            }
            
            if resource.resource_type in base_costs:
                if resource.resource_type == ResourceType.COMPUTE:
                    hourly_cost = base_costs[resource.resource_type].get(resource.instance_type, 0.1)
                elif resource.resource_type == ResourceType.STORAGE:
                    hourly_cost = base_costs[resource.resource_type].get(resource.storage_type, 0.023)
                else:
                    hourly_cost = base_costs[resource.resource_type].get('default', 0.1)
            else:
                hourly_cost = 0.1
            
            monthly_cost = hourly_cost * 24 * 30
            
            return CloudCost(
                provider=CloudProvider.AWS,
                resource_type=resource.resource_type,
                hourly_cost=hourly_cost,
                monthly_cost=monthly_cost,
                instance_type=resource.instance_type,
                storage_type=resource.storage_type,
                size=resource.size
            )
            
        except Exception as e:
            logger.error(f"Failed to get AWS cost estimate: {e}")
            return CloudCost(
                provider=CloudProvider.AWS,
                resource_type=resource.resource_type,
                hourly_cost=0.1,
                monthly_cost=72.0
            )
    
    async def shutdown(self):
        """Shutdown AWS client"""
        if self.session:
            self.session.close()

class AzureAdapter(CloudProviderAdapter):
    """Azure cloud provider adapter"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(CloudProvider.AZURE, config)
        self.blob_client = None
    
    async def initialize(self):
        """Initialize Azure client"""
        try:
            self.blob_client = azure.storage.blob.BlobServiceClient(
                connection_string=self.config.get('azure_connection_string')
            )
            self.initialized = True
            logger.info("Azure adapter initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Azure adapter: {e}")
            raise

class GCPAdapter(CloudProviderAdapter):
    """GCP cloud provider adapter"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(CloudProvider.GCP, config)
        self.storage_client = None
    
    async def initialize(self):
        """Initialize GCP client"""
        try:
            self.storage_client = google.cloud.storage.Client(
                project=self.config.get('gcp_project_id')
            )
            self.initialized = True
            logger.info("GCP adapter initialized")
        except Exception as e:
            logger.error(f"Failed to initialize GCP adapter: {e}")
            raise

class MultiCloudManager:
    """Multi-cloud management system"""
    
    def __init__(self):
        self.adapters = {}
        self.resources = {}
        self.costs = {}
        self.metrics = {}
        
        # Configuration
        self.default_provider = CloudProvider.AWS
        self.auto_failover = True
        self.cost_optimization = True
        self.disaster_recovery = True
        
        # Redis for distributed coordination
        self.redis_client = None
        self.redis_enabled = False
        
        # Performance tracking
        self.operation_history = []
        self.cost_history = []
        
    async def initialize(self):
        """Initialize multi-cloud manager"""
        try:
            # Initialize Redis connection
            try:
                self.redis_client = redis.from_url(
                    "redis://localhost:6379/12",
                    max_connections=20
                )
                await self.redis_client.ping()
                self.redis_enabled = True
                logger.info("Redis connection established for multi-cloud management")
            except Exception as e:
                logger.warning(f"Redis not available, using local multi-cloud management: {e}")
            
            # Initialize adapters for configured providers
            await self._initialize_adapters()
            
            logger.info("Multi-cloud manager initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize multi-cloud manager: {e}")
            raise
    
    async def _initialize_adapters(self):
        """Initialize cloud provider adapters"""
        try:
            # Initialize AWS adapter
            if 'aws' in self.config.get('providers', []):
                aws_config = self.config.get('aws', {})
                aws_adapter = AWSAdapter(aws_config)
                await aws_adapter.initialize()
                self.adapters[CloudProvider.AWS] = aws_adapter
            
            # Initialize Azure adapter
            if 'azure' in self.config.get('providers', []):
                azure_config = self.config.get('azure', {})
                azure_adapter = AzureAdapter(azure_config)
                await azure_adapter.initialize()
                self.adapters[CloudProvider.AZURE] = azure_adapter
            
            # Initialize GCP adapter
            if 'gcp' in self.config.get('providers', []):
                gcp_config = self.config.get('gcp', {})
                gcp_adapter = GCPAdapter(gcp_config)
                await gcp_adapter.initialize()
                self.adapters[CloudProvider.GCP] = gcp_adapter
            
            logger.info(f"Initialized {len(self.adapters)} cloud adapters")
            
        except Exception as e:
            logger.error(f"Failed to initialize adapters: {e}")
    
    async def create_resource(
        self,
        resource: CloudResource,
        preferred_providers: Optional[List[CloudProvider]] = None
    ) -> Dict[str, Any]:
        """Create a cloud resource with multi-cloud optimization"""
        try:
            # Select optimal provider
            provider = await self._select_optimal_provider(resource, preferred_providers)
            
            # Create resource using selected provider
            adapter = self.adapters[provider]
            result = await adapter.create_resource(resource)
            
            # Store resource
            self.resources[result['resource_id']] = {
                'resource': resource,
                'provider': provider,
                'created_at': datetime.now(),
                'status': 'active'
            }
            
            # Get cost estimate
            cost = await adapter.get_cost_estimate(resource)
            self.costs[result['resource_id']] = cost
            
            # Record operation
            self.operation_history.append({
                'operation': 'create_resource',
                'provider': provider.value,
                'resource_id': result['resource_id'],
                'timestamp': datetime.now(),
                'success': True
            })
            
            logger.info(f"Created resource {result['resource_id']} on {provider.value}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to create resource: {e}")
            raise
    
    async def delete_resource(self, resource_id: str) -> bool:
        """Delete a cloud resource"""
        try:
            if resource_id not in self.resources:
                logger.warning(f"Resource {resource_id} not found")
                return False
            
            resource_info = self.resources[resource_id]
            provider = resource_info['provider']
            adapter = self.adapters[provider]
            
            # Delete resource
            success = await adapter.delete_resource(resource_id)
            
            if success:
                # Remove from resources
                del self.resources[resource_id]
                
                # Remove from costs
                if resource_id in self.costs:
                    del self.costs[resource_id]
                
                # Record operation
                self.operation_history.append({
                    'operation': 'delete_resource',
                    'provider': provider.value,
                    'resource_id': resource_id,
                    'timestamp': datetime.now(),
                    'success': True
                })
                
                logger.info(f"Deleted resource {resource_id} from {provider.value}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to delete resource {resource_id}: {e}")
            return False
    
    async def get_resource(self, resource_id: str) -> Optional[Dict[str, Any]]:
        """Get resource information"""
        try:
            if resource_id not in self.resources:
                return None
            
            resource_info = self.resources[resource_id]
            provider = resource_info['provider']
            adapter = self.adapters[provider]
            
            # Get resource details
            result = await adapter.get_resource(resource_id)
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get resource {resource_id}: {e}")
            return None
    
    async def list_resources(self, resource_type: ResourceType, provider: Optional[CloudProvider] = None) -> List[Dict[str, Any]]:
        """List resources by type and optionally provider"""
        try:
            results = []
            
            if provider:
                # List from specific provider
                if provider in self.adapters:
                    adapter = self.adapters[provider]
                    results = await adapter.list_resources(resource_type)
            else:
                # List from all providers
                for prov, adapter in self.adapters.items():
                    try:
                        provider_results = await adapter.list_resources(resource_type)
                        for result in provider_results:
                            result['provider'] = prov.value
                            results.append(result)
                    except Exception as e:
                        logger.warning(f"Failed to list resources from {prov.value}: {e}")
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to list resources: {e}")
            return []
    
    async def scale_resource(self, resource_id: str, target_count: int) -> bool:
        """Scale a resource"""
        try:
            if resource_id not in self.resources:
                logger.warning(f"Resource {resource_id} not found")
                return False
            
            resource_info = self.resources[resource_id]
            provider = resource_info['provider']
            adapter = self.adapters[provider]
            
            # Scale resource
            success = await adapter.scale_resource(resource_id, target_count)
            
            if success:
                # Update resource count
                self.resources[resource_id]['resource'].count = target_count
                
                # Record operation
                self.operation_history.append({
                    'operation': 'scale_resource',
                    'provider': provider.value,
                    'resource_id': resource_id,
                    'timestamp': datetime.now(),
                    'success': True
                })
                
                logger.info(f"Scaled resource {resource_id} to {target_count} instances on {provider.value}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to scale resource {resource_id}: {e}")
            return False
    
    async def get_metrics(self, resource_id: str) -> Optional[CloudMetrics]:
        """Get resource metrics"""
        try:
            if resource_id not in self.resources:
                return None
            
            resource_info = self.resources[resource_id]
            provider = resource_info['provider']
            adapter = self.adapters[provider]
            
            # Get metrics
            metrics = await adapter.get_metrics(resource_id)
            
            # Store metrics
            self.metrics[resource_id] = metrics
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to get metrics for {resource_id}: {e}")
            return None
    
    async def _select_optimal_provider(
        self,
        resource: CloudResource,
        preferred_providers: Optional[List[CloudProvider]]
    ) -> CloudProvider:
        """Select optimal provider for resource"""
        try:
            candidates = preferred_providers or list(self.adapters.keys())
            
            # Get cost estimates for each candidate
            provider_scores = []
            for provider in candidates:
                if provider in self.adapters:
                    adapter = self.adapters[provider]
                    cost = await adapter.get_cost_estimate(resource)
                    
                    # Calculate score based on cost and availability
                    score = self._calculate_provider_score(provider, resource, cost)
                    provider_scores.append((provider, score))
            
            # Sort by score (lower is better)
            provider_scores.sort(key=lambda x: x[1])
            
            return provider_scores[0][0]
            
        except Exception as e:
            logger.error(f"Failed to select optimal provider: {e}")
            return self.default_provider
    
    def _calculate_provider_score(self, provider: CloudProvider, resource: CloudResource, cost: CloudCost) -> float:
        """Calculate provider score for resource"""
        try:
            score = 0.0
            
            # Cost factor (lower is better)
            max_cost = 1.0  # Would be calculated from actual costs
            cost_factor = 1.0 - (cost.hourly_cost / max_cost)
            score += cost_factor * 0.4
            
            # Availability factor
            availability_scores = {
                CloudProvider.AWS: 0.95,
                CloudProvider.AZURE: 0.90,
                CloudProvider.GCP: 0.85,
                CloudProvider.DIGITAL_OCEAN: 0.75,
                CloudProvider.VULTR: 0.70,
                CloudProvider.LINODE: 0.65,
                CloudProvider.ORACLE: 0.80,
                CloudProvider.IBM: 0.75
            }
            score += availability_scores.get(provider, 0.5) * 0.3
            
            # Feature factor
            feature_scores = {
                CloudProvider.AWS: 0.95,
                CloudProvider.AZURE: 0.90,
                CloudProvider.GCP: 0.85,
                CloudProvider.DIGITAL_OCEAN: 0.70,
                CloudProvider.VULTR: 0.65,
                CloudProvider.LINODE: 0.60,
                CloudProvider.ORACLE: 0.80,
                CloudProvider.IBM: 0.75
            }
            score += feature_scores.get(provider, 0.5) * 0.3
            
            return score
            
        except Exception as e:
            logger.error(f"Failed to calculate provider score: {e}")
            return 0.5
    
    async def get_cost_optimization_suggestions(self) -> List[str]:
        """Get cost optimization suggestions"""
        try:
            suggestions = []
            
            # Analyze current costs
            total_monthly_cost = sum(cost.monthly_cost for cost in self.costs.values())
            
            if total_monthly_cost > 1000:
                suggestions.append("Consider using spot instances for non-critical workloads")
            
            if total_monthly_cost > 500:
                suggestions.append("Implement auto-scaling to reduce costs during low usage")
            
            # Check for underutilized resources
            for resource_id, resource_info in self.resources.items():
                metrics = await self.get_metrics(resource_id)
                if metrics and metrics.cpu_utilization < 0.2:
                    suggestions.append(f"Consider downscaling resource {resource_id}")
            
            # Check for expensive resources
            expensive_resources = [
                resource_id for resource_id, cost in self.costs.items()
                if cost.hourly_cost > 0.5
            ]
            
            if expensive_resources:
                suggestions.append(f"Review expensive resources: {', '.join(expensive_resources[:5])}")
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Failed to generate cost optimization suggestions: {e}")
            return []
    
    async def get_disaster_recovery_plan(self) -> Dict[str, Any]:
        """Get disaster recovery plan"""
        try:
            plan = {
                'primary_provider': self.default_provider.value,
                'backup_providers': [p.value for p in self.adapters.keys() if p != self.default_provider],
                'recovery_steps': [
                    "1. Switch to backup provider",
                    "2. Restore from backups",
                    "3. Update DNS records",
                    "4. Update configuration",
                    "5. Verify all services"
                ],
                'rto': 15,  # 15 minutes
                'data_backup': True,
                'infrastructure_backup': True
            }
            
            return plan
            
        except Exception as e:
            logger.error(f"Failed to create disaster recovery plan: {e}")
            return {}
    
    async def get_multi_cloud_summary(self) -> Dict[str, Any]:
        """Get multi-cloud summary"""
        try:
            summary = {
                'total_resources': len(self.resources),
                'total_providers': len(self.adapters),
                'providers': list(self.adapters.keys()),
                'total_monthly_cost': sum(cost.monthly_cost for cost in self.costs.values()),
                'resource_types': {
                    resource_type.value: len([r for r in self.resources.values() if r['resource'].resource_type == resource_type])
                    for resource_type in ResourceType
                },
                'providers_usage': {
                    provider.value: len([r for r in self.resources.values() if r['provider'] == provider])
                    for provider in self.adapters.keys()
                },
                'cost_distribution': {
                    provider.value: sum(cost.monthly_cost for cost in self.costs.values() if cost.provider == provider)
                    for provider in self.adapters.keys()
                },
                'last_operation': self.operation_history[-1] if self.operation_history else None
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Failed to get multi-cloud summary: {e}")
            return {}
    
    async def cleanup_old_resources(self, older_than_days: int = 30):
        """Clean up old resources"""
        try:
            cutoff_time = datetime.now() - timedelta(days=older_than_days)
            
            resources_to_delete = []
            for resource_id, resource_info in self.resources.items():
                if resource_info['created_at'] < cutoff_time:
                    resources_to_delete.append(resource_id)
            
            for resource_id in resources_to_delete:
                await self.delete_resource(resource_id)
            
            logger.info(f"Cleaned up {len(resources_to_delete)} old resources")
            
        except Exception as e:
            logger.error(f"Failed to cleanup old resources: {e}")
    
    async def shutdown(self):
        """Shutdown multi-cloud manager"""
        try:
            logger.info("Shutting down multi-cloud manager...")
            
            # Shutdown all adapters
            for adapter in self.adapters.values():
                await adapter.shutdown()
            
            # Close Redis connection
            if self.redis_client:
                await self.redis_client.close()
            
            logger.info("Multi-cloud manager shutdown complete")
            
        except Exception as e:
            logger.error(f"Multi-cloud manager shutdown error: {e}")

# Global multi-cloud manager instance
multi_cloud_manager = MultiCloudManager()
