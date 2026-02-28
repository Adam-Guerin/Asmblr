"""
Global Edge Computing with CDN for Asmblr
Worldwide edge deployment, intelligent caching, and real-time optimization
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
import uuid
import hashlib
import aiohttp
import aiofiles
from fastapi import Request, Response
from fastapi.staticfiles import StaticFiles
import geoip2.database
import geoip2.errors

logger = logging.getLogger(__name__)

class EdgeLocation(Enum):
    """Edge computing locations"""
    NORTH_AMERICA = "north_america"
    EUROPE = "europe"
    ASIA_PACIFIC = "asia_pacific"
    SOUTH_AMERICA = "south_america"
    AFRICA = "africa"
    MIDDLE_EAST = "middle_east"
    OCEANIA = "oceania"

class CDNProvider(Enum):
    """CDN providers"""
    CLOUDFLARE = "cloudflare"
    FASTLY = "fastly"
    AKAMAI = "akamai"
    AWS_CLOUDFRONT = "aws_cloudfront"
    GOOGLE_CDN = "google_cdn"
    AZURE_CDN = "azure_cdn"
    VERIZON_EDGECAST = "verizon_edgecast"

class CacheStrategy(Enum):
    """Caching strategies"""
    TTL_BASED = "ttl_based"
    STALE_WHILE_REVALIDATE = "stale_while_revalidate"
    BYPASS_ON_COOKIE = "bypass_on_cookie"
    GEO_DISTRIBUTED = "geo_distributed"
    INTELLIGENT_PREDICTION = "intelligent_prediction"

@dataclass
class EdgeNode:
    """Edge computing node"""
    id: str
    location: EdgeLocation
    city: str
    country: str
    latitude: float
    longitude: float
    provider: CDNProvider
    endpoint: str
    capacity: int  # requests per second
    current_load: float
    cache_size: int  # GB
    cache_hit_rate: float
    latency: Dict[str, float]  # latency to other regions
    is_active: bool
    last_health_check: datetime

@dataclass
class CacheEntry:
    """Cache entry"""
    key: str
    content: bytes
    content_type: str
    cache_control: str
    etag: str
    last_modified: datetime
    expires_at: datetime
    access_count: int
    last_accessed: datetime
    size_bytes: int
    compression_ratio: float
    edge_nodes: List[str]  # nodes where this is cached

@dataclass
class GeoLocation:
    """Geographic location"""
    ip: str
    country: str
    city: str
    latitude: float
    longitude: float
    timezone: str
    asn: str
    organization: str

@dataclass
class CDNMetrics:
    """CDN performance metrics"""
    total_requests: int
    cache_hits: int
    cache_misses: int
    average_response_time: float
    bandwidth_saved: int  # GB
    error_rate: float
    geographic_distribution: Dict[str, int]
    top_edge_nodes: List[Dict[str, Any]]

class GlobalCDNManager:
    """Global CDN and edge computing manager"""
    
    def __init__(self, geoip_db_path: str = "data/GeoLite2-City.mmdb"):
        self.geoip_db_path = geoip_db_path
        self.edge_nodes: Dict[str, EdgeNode] = {}
        self.cache_entries: Dict[str, CacheEntry] = {}
        self.user_locations: Dict[str, GeoLocation] = {}
        self.metrics = CDNMetrics(
            total_requests=0,
            cache_hits=0,
            cache_misses=0,
            average_response_time=0.0,
            bandwidth_saved=0,
            error_rate=0.0,
            geographic_distribution={},
            top_edge_nodes=[]
        )
        
        # Initialize edge nodes
        self._initialize_edge_nodes()
        
        # Initialize GeoIP database
        self._initialize_geoip()
        
        # Start background tasks
        asyncio.create_task(self._health_check_loop())
        asyncio.create_task(self._cache_cleanup_loop())
        asyncio.create_task(self._metrics_collection_loop())
    
    def _initialize_edge_nodes(self):
        """Initialize global edge nodes"""
        edge_nodes_config = [
            # North America
            {
                "id": "edge-na-east-1",
                "location": EdgeLocation.NORTH_AMERICA,
                "city": "New York",
                "country": "USA",
                "latitude": 40.7128,
                "longitude": -74.0060,
                "provider": CDNProvider.CLOUDFLARE,
                "endpoint": "https://edge-na-east-1.asmblr-cdn.com",
                "capacity": 10000,
                "cache_size": 500
            },
            {
                "id": "edge-na-west-1",
                "location": EdgeLocation.NORTH_AMERICA,
                "city": "San Francisco",
                "country": "USA",
                "latitude": 37.7749,
                "longitude": -122.4194,
                "provider": CDNProvider.AWS_CLOUDFRONT,
                "endpoint": "https://edge-na-west-1.asmblr-cdn.com",
                "capacity": 8000,
                "cache_size": 400
            },
            {
                "id": "edge-na-central-1",
                "location": EdgeLocation.NORTH_AMERICA,
                "city": "Toronto",
                "country": "Canada",
                "latitude": 43.6532,
                "longitude": -79.3832,
                "provider": CDNProvider.FASTLY,
                "endpoint": "https://edge-na-central-1.asmblr-cdn.com",
                "capacity": 6000,
                "cache_size": 300
            },
            
            # Europe
            {
                "id": "edge-eu-west-1",
                "location": EdgeLocation.EUROPE,
                "city": "London",
                "country": "UK",
                "latitude": 51.5074,
                "longitude": -0.1278,
                "provider": CDNProvider.CLOUDFLARE,
                "endpoint": "https://edge-eu-west-1.asmblr-cdn.com",
                "capacity": 9000,
                "cache_size": 450
            },
            {
                "id": "edge-eu-central-1",
                "location": EdgeLocation.EUROPE,
                "city": "Frankfurt",
                "country": "Germany",
                "latitude": 50.1109,
                "longitude": 8.6821,
                "provider": CDNProvider.AKAMAI,
                "endpoint": "https://edge-eu-central-1.asmblr-cdn.com",
                "capacity": 7000,
                "cache_size": 350
            },
            {
                "id": "edge-eu-north-1",
                "location": EdgeLocation.EUROPE,
                "city": "Stockholm",
                "country": "Sweden",
                "latitude": 59.3293,
                "longitude": 18.0686,
                "provider": CDNProvider.FASTLY,
                "endpoint": "https://edge-eu-north-1.asmblr-cdn.com",
                "capacity": 5000,
                "cache_size": 250
            },
            
            # Asia Pacific
            {
                "id": "edge-ap-east-1",
                "location": EdgeLocation.ASIA_PACIFIC,
                "city": "Tokyo",
                "country": "Japan",
                "latitude": 35.6762,
                "longitude": 139.6503,
                "provider": CDNProvider.AWS_CLOUDFRONT,
                "endpoint": "https://edge-ap-east-1.asmblr-cdn.com",
                "capacity": 12000,
                "cache_size": 600
            },
            {
                "id": "edge-ap-southeast-1",
                "location": EdgeLocation.ASIA_PACIFIC,
                "city": "Singapore",
                "country": "Singapore",
                "latitude": 1.3521,
                "longitude": 103.8198,
                "provider": CDNProvider.CLOUDFLARE,
                "endpoint": "https://edge-ap-southeast-1.asmblr-cdn.com",
                "capacity": 8000,
                "cache_size": 400
            },
            {
                "id": "edge-ap-south-1",
                "location": EdgeLocation.ASIA_PACIFIC,
                "city": "Mumbai",
                "country": "India",
                "latitude": 19.0760,
                "longitude": 72.8777,
                "provider": CDNProvider.GOOGLE_CDN,
                "endpoint": "https://edge-ap-south-1.asmblr-cdn.com",
                "capacity": 6000,
                "cache_size": 300
            },
            
            # South America
            {
                "id": "edge-sa-east-1",
                "location": EdgeLocation.SOUTH_AMERICA,
                "city": "São Paulo",
                "country": "Brazil",
                "latitude": -23.5505,
                "longitude": -46.6333,
                "provider": CDNProvider.AZURE_CDN,
                "endpoint": "https://edge-sa-east-1.asmblr-cdn.com",
                "capacity": 4000,
                "cache_size": 200
            },
            
            # Oceania
            {
                "id": "edge-oc-east-1",
                "location": EdgeLocation.OCEANIA,
                "city": "Sydney",
                "country": "Australia",
                "latitude": -33.8688,
                "longitude": 151.2093,
                "provider": CDNProvider.CLOUDFLARE,
                "endpoint": "https://edge-oc-east-1.asmblr-cdn.com",
                "capacity": 5000,
                "cache_size": 250
            }
        ]
        
        for config in edge_nodes_config:
            node = EdgeNode(
                id=config["id"],
                location=config["location"],
                city=config["city"],
                country=config["country"],
                latitude=config["latitude"],
                "longitude=config["longitude"],
                provider=config["provider"],
                endpoint=config["endpoint"],
                capacity=config["capacity"],
                current_load=0.0,
                cache_size=config["cache_size"],
                cache_hit_rate=0.0,
                latency={},
                is_active=True,
                last_health_check=datetime.now()
            )
            
            self.edge_nodes[node.id] = node
        
        # Calculate latencies between nodes
        self._calculate_node_latencies()
        
        logger.info(f"Initialized {len(self.edge_nodes)} edge nodes")
    
    def _calculate_node_latencies(self):
        """Calculate latencies between edge nodes"""
        for node1_id, node1 in self.edge_nodes.items():
            for node2_id, node2 in self.edge_nodes.items():
                if node1_id != node2_id:
                    # Calculate distance-based latency (simplified)
                    distance = self._calculate_distance(
                        node1.latitude, node1.longitude,
                        node2.latitude, node2.longitude
                    )
                    
                    # Base latency + distance factor
                    latency = 10 + (distance / 1000) * 50  # ms
                    node1.latency[node2_id] = latency
    
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two coordinates"""
        from math import radians, sin, cos, sqrt, atan2
        
        R = 6371  # Earth's radius in km
        
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        
        return R * c
    
    def _initialize_geoip(self):
        """Initialize GeoIP database"""
        try:
            if Path(self.geoip_db_path).exists():
                self.geoip_reader = geoip2.database.Reader(self.geoip_db_path)
                logger.info("GeoIP database loaded successfully")
            else:
                self.geoip_reader = None
                logger.warning("GeoIP database not found, using IP-based detection")
        except Exception as e:
            logger.error(f"Error initializing GeoIP: {e}")
            self.geoip_reader = None
    
    def get_user_location(self, ip_address: str) -> GeoLocation:
        """Get user location from IP address"""
        try:
            # Check cache first
            if ip_address in self.user_locations:
                return self.user_locations[ip_address]
            
            # Use GeoIP database
            if self.geoip_reader:
                response = self.geoip_reader.city(ip_address)
                
                location = GeoLocation(
                    ip=ip_address,
                    country=response.country.name,
                    city=response.city.name,
                    latitude=response.location.latitude,
                    longitude=response.location.longitude,
                    timezone=response.location.time_zone,
                    asn=str(response.traits.autonomous_system_number),
                    organization=response.traits.autonomous_system_organization
                )
            else:
                # Fallback to IP-based detection (simplified)
                location = self._detect_location_from_ip(ip_address)
            
            # Cache location
            self.user_locations[ip_address] = location
            
            return location
            
        except Exception as e:
            logger.error(f"Error getting location for {ip_address}: {e}")
            # Return default location
            return GeoLocation(
                ip=ip_address,
                country="Unknown",
                city="Unknown",
                latitude=0.0,
                longitude=0.0,
                timezone="UTC",
                asn="",
                organization=""
            )
    
    def _detect_location_from_ip(self, ip_address: str) -> GeoLocation:
        """Detect location from IP address (simplified)"""
        # This is a simplified fallback - in production, use a proper IP geolocation service
        ip_parts = ip_address.split('.')
        
        # Simple heuristic based on first octet
        first_octet = int(ip_parts[0]) if ip_parts[0].isdigit() else 0
        
        if first_octet >= 1 and first_octet <= 126:
            # Likely US/Europe
            if first_octet <= 50:
                return GeoLocation(
                    ip=ip_address,
                    country="USA",
                    city="New York",
                    latitude=40.7128,
                    longitude=-74.0060,
                    timezone="America/New_York",
                    asn="",
                    organization=""
                )
            else:
                return GeoLocation(
                    ip=ip_address,
                    country="UK",
                    city="London",
                    latitude=51.5074,
                    longitude=-0.1278,
                    timezone="Europe/London",
                    asn="",
                    organization=""
                )
        else:
            # Default to US
            return GeoLocation(
                ip=ip_address,
                country="USA",
                city="San Francisco",
                latitude=37.7749,
                longitude=-122.4194,
                timezone="America/Los_Angeles",
                asn="",
                organization=""
            )
    
    def find_optimal_edge_node(self, user_location: GeoLocation, 
                             content_type: str = "static") -> EdgeNode:
        """Find optimal edge node for user"""
        try:
            # Filter active nodes
            active_nodes = [node for node in self.edge_nodes.values() if node.is_active]
            
            if not active_nodes:
                # Fallback to any node
                return list(self.edge_nodes.values())[0]
            
            # Calculate scores for each node
            node_scores = []
            
            for node in active_nodes:
                score = self._calculate_node_score(node, user_location, content_type)
                node_scores.append((node, score))
            
            # Sort by score (highest first)
            node_scores.sort(key=lambda x: x[1], reverse=True)
            
            # Return best node
            return node_scores[0][0]
            
        except Exception as e:
            logger.error(f"Error finding optimal edge node: {e}")
            # Return first available node
            return list(self.edge_nodes.values())[0]
    
    def _calculate_node_score(self, node: EdgeNode, user_location: GeoLocation, 
                             content_type: str) -> float:
        """Calculate score for edge node"""
        score = 0.0
        
        # Distance factor (closer is better)
        distance = self._calculate_distance(
            node.latitude, node.longitude,
            user_location.latitude, user_location.longitude
        )
        distance_score = max(0, 100 - distance / 100)  # 100 points max
        score += distance_score * 0.4
        
        # Load factor (less loaded is better)
        load_score = (1 - node.current_load) * 100
        score += load_score * 0.2
        
        # Cache hit rate (higher is better)
        cache_score = node.cache_hit_rate * 100
        score += cache_score * 0.2
        
        # Provider reliability (weighted)
        provider_weights = {
            CDNProvider.CLOUDFLARE: 0.95,
            CDNProvider.FASTLY: 0.90,
            CDNProvider.AKAMAI: 0.92,
            CDNProvider.AWS_CLOUDFRONT: 0.88,
            CDNProvider.GOOGLE_CDN: 0.85,
            CDNProvider.AZURE_CDN: 0.83,
            CDNProvider.VERIZON_EDGECAST: 0.80
        }
        provider_score = provider_weights.get(node.provider, 0.8) * 100
        score += provider_score * 0.1
        
        # Content type optimization
        if content_type == "static":
            # Prefer nodes with larger cache
            cache_size_score = min(100, node.cache_size / 10)
            score += cache_size_score * 0.1
        elif content_type == "dynamic":
            # Prefer nodes with higher capacity
            capacity_score = min(100, node.capacity / 100)
            score += capacity_score * 0.1
        
        return score
    
    async def cache_content(self, key: str, content: bytes, content_type: str,
                          cache_control: str, ttl: int = 3600, 
                          edge_nodes: Optional[List[str]] = None) -> bool:
        """Cache content on edge nodes"""
        try:
            # Determine which edge nodes to cache on
            if edge_nodes is None:
                # Cache on top performing nodes
                edge_nodes = self._get_best_cache_nodes(len(self.edge_nodes) // 2)
            
            # Create cache entry
            cache_entry = CacheEntry(
                key=key,
                content=content,
                content_type=content_type,
                cache_control=cache_control,
                etag=self._generate_etag(content),
                last_modified=datetime.now(),
                expires_at=datetime.now() + timedelta(seconds=ttl),
                access_count=0,
                last_accessed=datetime.now(),
                size_bytes=len(content),
                compression_ratio=1.0,
                edge_nodes=edge_nodes
            )
            
            # Compress content if beneficial
            if len(content) > 1024:  # Only compress if > 1KB
                compressed_content = await self._compress_content(content)
                if len(compressed_content) < len(content):
                    cache_entry.content = compressed_content
                    cache_entry.compression_ratio = len(compressed_content) / len(content)
            
            # Store cache entry
            self.cache_entries[key] = cache_entry
            
            # Update node cache metrics
            for node_id in edge_nodes:
                if node_id in self.edge_nodes:
                    node = self.edge_nodes[node_id]
                    node.current_load += 0.01  # Slight load increase
            
            logger.info(f"Cached content {key} on {len(edge_nodes)} edge nodes")
            return True
            
        except Exception as e:
            logger.error(f"Error caching content {key}: {e}")
            return False
    
    def _get_best_cache_nodes(self, count: int) -> List[str]:
        """Get best edge nodes for caching"""
        nodes = list(self.edge_nodes.values())
        
        # Sort by cache hit rate and capacity
        nodes.sort(key=lambda x: (x.cache_hit_rate, x.capacity), reverse=True)
        
        return [node.id for node in nodes[:count]]
    
    def _generate_etag(self, content: bytes) -> str:
        """Generate ETag for content"""
        content_hash = hashlib.md5(content).hexdigest()
        return f'"{content_hash}"'
    
    async def _compress_content(self, content: bytes) -> bytes:
        """Compress content using gzip"""
        try:
            import gzip
            return gzip.compress(content)
        except Exception as e:
            logger.error(f"Error compressing content: {e}")
            return content
    
    async def get_cached_content(self, key: str, user_location: GeoLocation) -> Optional[CacheEntry]:
        """Get cached content from optimal edge node"""
        try:
            cache_entry = self.cache_entries.get(key)
            if not cache_entry:
                return None
            
            # Check if expired
            if datetime.now() > cache_entry.expires_at:
                return None
            
            # Update access metrics
            cache_entry.access_count += 1
            cache_entry.last_accessed = datetime.now()
            
            # Find best edge node for this user
            optimal_node = self.find_optimal_edge_node(user_location)
            
            # Check if content is cached on this node
            if optimal_node.id in cache_entry.edge_nodes:
                # Update node metrics
                optimal_node.cache_hit_rate = (optimal_node.cache_hit_rate * 0.9) + 0.1
                optimal_node.current_load = max(0, optimal_node.current_load - 0.01)
                
                # Update metrics
                self.metrics.cache_hits += 1
                self.metrics.total_requests += 1
                
                return cache_entry
            else:
                # Cache miss for this node
                self.metrics.cache_misses += 1
                self.metrics.total_requests += 1
                
                return None
                
        except Exception as e:
            logger.error(f"Error getting cached content {key}: {e}")
            return None
    
    async def invalidate_cache(self, key: str) -> bool:
        """Invalidate cache entry"""
        try:
            if key in self.cache_entries:
                del self.cache_entries[key]
                logger.info(f"Invalidated cache entry {key}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error invalidating cache {key}: {e}")
            return False
    
    async def purge_cache_by_pattern(self, pattern: str) -> int:
        """Purge cache entries matching pattern"""
        try:
            import fnmatch
            
            keys_to_remove = []
            for key in self.cache_entries.keys():
                if fnmatch.fnmatch(key, pattern):
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                del self.cache_entries[key]
            
            logger.info(f"Purged {len(keys_to_remove)} cache entries matching {pattern}")
            return len(keys_to_remove)
            
        except Exception as e:
            logger.error(f"Error purging cache pattern {pattern}: {e}")
            return 0
    
    async def _health_check_loop(self):
        """Background health check for edge nodes"""
        while True:
            try:
                for node in self.edge_nodes.values():
                    # Simulate health check
                    is_healthy = await self._check_node_health(node)
                    
                    if is_healthy:
                        node.is_active = True
                        node.last_health_check = datetime.now()
                    else:
                        node.is_active = False
                        logger.warning(f"Edge node {node.id} marked as unhealthy")
                
                # Wait before next check
                await asyncio.sleep(300)  # 5 minutes
                
            except Exception as e:
                logger.error(f"Error in health check loop: {e}")
                await asyncio.sleep(60)
    
    async def _check_node_health(self, node: EdgeNode) -> bool:
        """Check health of edge node"""
        try:
            # Simulate health check with HTTP request
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                async with session.get(f"{node.endpoint}/health") as response:
                    if response.status == 200:
                        # Update node metrics
                        health_data = await response.json()
                        node.current_load = health_data.get("load", 0.0)
                        node.cache_hit_rate = health_data.get("cache_hit_rate", 0.0)
                        return True
                    else:
                        return False
        except Exception as e:
            logger.error(f"Health check failed for node {node.id}: {e}")
            return False
    
    async def _cache_cleanup_loop(self):
        """Background cache cleanup"""
        while True:
            try:
                current_time = datetime.now()
                expired_keys = []
                
                for key, entry in self.cache_entries.items():
                    if current_time > entry.expires_at:
                        expired_keys.append(key)
                    elif (current_time - entry.last_accessed).days > 7:
                        # Remove unused entries after 7 days
                        expired_keys.append(key)
                
                for key in expired_keys:
                    del self.cache_entries[key]
                
                if expired_keys:
                    logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")
                
                # Wait before next cleanup
                await asyncio.sleep(3600)  # 1 hour
                
            except Exception as e:
                logger.error(f"Error in cache cleanup loop: {e}")
                await asyncio.sleep(300)
    
    async def _metrics_collection_loop(self):
        """Background metrics collection"""
        while True:
            try:
                # Calculate metrics
                total_requests = self.metrics.total_requests
                cache_hits = self.metrics.cache_hits
                cache_misses = self.metrics.cache_misses
                
                # Calculate cache hit rate
                cache_hit_rate = (cache_hits / total_requests) if total_requests > 0 else 0
                
                # Calculate average response time (simulated)
                avg_response_time = 50 + (1 - cache_hit_rate) * 200  # ms
                
                # Calculate bandwidth saved
                bandwidth_saved = sum(
                    entry.size_bytes * (1 - entry.compression_ratio) * entry.access_count
                    for entry in self.cache_entries.values()
                ) / (1024**3)  # Convert to GB
                
                # Update metrics
                self.metrics = CDNMetrics(
                    total_requests=total_requests,
                    cache_hits=cache_hits,
                    cache_misses=cache_misses,
                    average_response_time=avg_response_time,
                    bandwidth_saved=bandwidth_saved,
                    error_rate=0.01,  # Simulated
                    geographic_distribution=self._get_geographic_distribution(),
                    top_edge_nodes=self._get_top_edge_nodes()
                )
                
                # Wait before next collection
                await asyncio.sleep(600)  # 10 minutes
                
            except Exception as e:
                logger.error(f"Error in metrics collection: {e}")
                await asyncio.sleep(60)
    
    def _get_geographic_distribution(self) -> Dict[str, int]:
        """Get geographic distribution of requests"""
        distribution = {}
        
        for location in self.user_locations.values():
            region = self._get_region_from_country(location.country)
            distribution[region] = distribution.get(region, 0) + 1
        
        return distribution
    
    def _get_region_from_country(self, country: str) -> str:
        """Get region from country"""
        region_mapping = {
            "USA": "north_america",
            "Canada": "north_america",
            "UK": "europe",
            "Germany": "europe",
            "France": "europe",
            "Italy": "europe",
            "Spain": "europe",
            "Japan": "asia_pacific",
            "China": "asia_pacific",
            "India": "asia_pacific",
            "Singapore": "asia_pacific",
            "Australia": "oceania",
            "Brazil": "south_america",
            "Argentina": "south_america"
        }
        
        return region_mapping.get(country, "other")
    
    def _get_top_edge_nodes(self) -> List[Dict[str, Any]]:
        """Get top performing edge nodes"""
        nodes = list(self.edge_nodes.values())
        
        # Sort by cache hit rate and total requests served
        nodes.sort(key=lambda x: (x.cache_hit_rate, x.capacity), reverse=True)
        
        top_nodes = []
        for node in nodes[:10]:
            top_nodes.append({
                "id": node.id,
                "location": node.location.value,
                "city": node.city,
                "cache_hit_rate": node.cache_hit_rate,
                "current_load": node.current_load,
                "is_active": node.is_active
            })
        
        return top_nodes
    
    def get_cdn_metrics(self) -> CDNMetrics:
        """Get CDN performance metrics"""
        return self.metrics
    
    def get_edge_node_status(self) -> Dict[str, Any]:
        """Get status of all edge nodes"""
        return {
            "total_nodes": len(self.edge_nodes),
            "active_nodes": len([n for n in self.edge_nodes.values() if n.is_active]),
            "total_capacity": sum(n.capacity for n in self.edge_nodes.values()),
            "current_load": sum(n.current_load for n in self.edge_nodes.values()),
            "average_cache_hit_rate": sum(n.cache_hit_rate for n in self.edge_nodes.values()) / len(self.edge_nodes),
            "nodes": [
                {
                    "id": node.id,
                    "location": node.location.value,
                    "city": node.city,
                    "country": node.country,
                    "provider": node.provider.value,
                    "capacity": node.capacity,
                    "current_load": node.current_load,
                    "cache_hit_rate": node.cache_hit_rate,
                    "is_active": node.is_active,
                    "last_health_check": node.last_health_check.isoformat()
                }
                for node in self.edge_nodes.values()
            ]
        }

# Global CDN manager
cdn_manager = GlobalCDNManager()

# Middleware for CDN
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

class CDNMiddleware(BaseHTTPMiddleware):
    """CDN middleware for edge caching"""
    
    async def dispatch(self, request: Request, call_next):
        try:
            # Get user location
            user_ip = request.client.host
            user_location = cdn_manager.get_user_location(user_ip)
            
            # Check if this is a static request
            if self._is_static_request(request):
                cache_key = self._generate_cache_key(request)
                
                # Try to get from cache
                cached_content = await cdn_manager.get_cached_content(cache_key, user_location)
                
                if cached_content:
                    # Return cached content
                    response = Response(
                        content=cached_content.content,
                        media_type=cached_content.content_type,
                        headers={
                            "Cache-Control": cached_content.cache_control,
                            "ETag": cached_content.etag,
                            "X-CDN-Cache": "HIT",
                            "X-CDN-Node": cdn_manager.find_optimal_edge_node(user_location).id
                        }
                    )
                    return response
            
            # Process request normally
            response = await call_next(request)
            
            # Cache static responses
            if self._is_static_request(request) and response.status_code == 200:
                cache_key = self._generate_cache_key(request)
                
                # Determine TTL based on content type
                ttl = self._get_ttl_for_content(request)
                
                # Cache the response
                await cdn_manager.cache_content(
                    cache_key,
                    response.body,
                    response.media_type,
                    response.headers.get("Cache-Control", "public, max-age=3600"),
                    ttl
                )
                
                # Add CDN headers
                response.headers["X-CDN-Cache"] = "MISS"
                response.headers["X-CDN-Node"] = cdn_manager.find_optimal_edge_node(user_location).id
            
            return response
            
        except Exception as e:
            logger.error(f"Error in CDN middleware: {e}")
            return await call_next(request)
    
    def _is_static_request(self, request: Request) -> bool:
        """Check if request is for static content"""
        static_extensions = ['.css', '.js', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.woff', '.woff2']
        url_path = request.url.path.lower()
        
        return any(url_path.endswith(ext) for ext in static_extensions) or \
               url_path.startswith('/static/') or \
               url_path.startswith('/assets/')
    
    def _generate_cache_key(self, request: Request) -> str:
        """Generate cache key for request"""
        key_parts = [
            request.method.lower(),
            request.url.path,
            str(sorted(request.query_params.items()))
        ]
        return hashlib.md5('|'.join(key_parts).encode()).hexdigest()
    
    def _get_ttl_for_content(self, request: Request) -> int:
        """Get TTL for content type"""
        url_path = request.url.path.lower()
        
        if url_path.endswith('.css') or url_path.endswith('.js'):
            return 86400  # 1 day
        elif url_path.endswith(('.png', '.jpg', '.jpeg', '.gif', '.svg')):
            return 604800  # 1 week
        elif url_path.endswith(('.woff', '.woff2')):
            return 2592000  # 30 days
        else:
            return 3600  # 1 hour

# API endpoints
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/cdn", tags=["cdn"])

class CacheRequest(BaseModel):
    key: str
    content: str  # Base64 encoded
    content_type: str
    cache_control: str = "public, max-age=3600"
    ttl: int = 3600
    edge_nodes: Optional[List[str]] = None

@router.get("/metrics")
async def get_cdn_metrics():
    """Get CDN performance metrics"""
    try:
        metrics = cdn_manager.get_cdn_metrics()
        return asdict(metrics)
    except Exception as e:
        logger.error(f"Error getting CDN metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/nodes/status")
async def get_edge_nodes_status():
    """Get edge nodes status"""
    try:
        status = cdn_manager.get_edge_node_status()
        return status
    except Exception as e:
        logger.error(f"Error getting edge nodes status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/location/{ip_address}")
async def get_user_location(ip_address: str):
    """Get user location from IP address"""
    try:
        location = cdn_manager.get_user_location(ip_address)
        return asdict(location)
    except Exception as e:
        logger.error(f"Error getting user location: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/cache")
async def cache_content(request: CacheRequest):
    """Cache content on edge nodes"""
    try:
        import base64
        
        # Decode content
        content = base64.b64decode(request.content)
        
        # Cache content
        success = await cdn_manager.cache_content(
            request.key,
            content,
            request.content_type,
            request.cache_control,
            request.ttl,
            request.edge_nodes
        )
        
        return {"success": success, "key": request.key}
    except Exception as e:
        logger.error(f"Error caching content: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/cache/{key}")
async def invalidate_cache(key: str):
    """Invalidate cache entry"""
    try:
        success = await cdn_manager.invalidate_cache(key)
        return {"success": success, "key": key}
    except Exception as e:
        logger.error(f"Error invalidating cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/cache/purge")
async def purge_cache(pattern: str):
    """Purge cache entries matching pattern"""
    try:
        count = await cdn_manager.purge_cache_by_pattern(pattern)
        return {"purged_count": count, "pattern": pattern}
    except Exception as e:
        logger.error(f"Error purging cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/optimal-node")
async def get_optimal_edge_node(ip_address: str, content_type: str = "static"):
    """Get optimal edge node for user"""
    try:
        user_location = cdn_manager.get_user_location(ip_address)
        optimal_node = cdn_manager.find_optimal_edge_node(user_location, content_type)
        
        return {
            "node_id": optimal_node.id,
            "location": optimal_node.location.value,
            "city": optimal_node.city,
            "country": optimal_node.country,
            "provider": optimal_node.provider.value,
            "endpoint": optimal_node.endpoint,
            "cache_hit_rate": optimal_node.cache_hit_rate,
            "current_load": optimal_node.current_load
        }
    except Exception as e:
        logger.error(f"Error getting optimal node: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check():
    """CDN health check"""
    try:
        metrics = cdn_manager.get_cdn_metrics()
        status = cdn_manager.get_edge_node_status()
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "total_requests": metrics.total_requests,
            "cache_hit_rate": (metrics.cache_hits / metrics.total_requests) if metrics.total_requests > 0 else 0,
            "active_nodes": status["active_nodes"],
            "total_nodes": status["total_nodes"]
        }
    except Exception as e:
        logger.error(f"Error in health check: {e}")
        raise HTTPException(status_code=500, detail=str(e))
