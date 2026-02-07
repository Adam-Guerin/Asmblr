"""
Asset Management Tools for agents to create, share and reuse collaborative resources.
"""

from typing import Any, Dict, List, Optional
from loguru import logger

from app.agents.shared_assets import (
    SharedAssetManager,
    AssetMetadata,
    AssetType,
    AssetStatus,
    AssetFormat
)


class AssetManagementTools:
    """Tools for agents to interact with shared asset system."""
    
    def __init__(self, asset_manager: SharedAssetManager, agent_name: str):
        self.asset_manager = asset_manager
        self.agent_name = agent_name
    
    def create_logo(self, name: str, description: str, file_path: str,
                  tags: List[str] = None, brand_colors: List[str] = None,
                  style: str = "modern", variations: List[str] = None) -> Optional[str]:
        """Create a logo asset with brand-specific metadata."""
        try:
            technical_specs = {
                "style": style,
                "variations": variations or ["primary", "secondary", "icon"],
                "brand_colors": brand_colors or [],
                "scalable": True,
                "formats": ["svg", "png", "jpg"]
            }
            
            asset_id = self.asset_manager.create_asset(
                name=name,
                description=description,
                asset_type=AssetType.LOGO,
                format=AssetFormat.SVG,
                file_path=file_path,
                created_by=self.agent_name,
                category="brand_identity",
                tags=tags or ["logo", "brand", "identity"],
                technical_specs=technical_specs
            )
            
            logger.info(f"Created logo asset {asset_id}: {name}")
            return asset_id
            
        except Exception as e:
            logger.error(f"Failed to create logo asset: {e}")
            return None
    
    def create_hosting_info(self, name: str, description: str, url: str,
                         provider: str, plan: str = "basic", features: List[str] = None,
                         pricing: Dict[str, Any] = None, deployment_info: Dict[str, Any] = None) -> Optional[str]:
        """Create hosting information asset for CTA and deployment."""
        try:
            hosting_info = {
                "url": url,
                "provider": provider,
                "plan": plan,
                "features": features or [],
                "pricing": pricing or {},
                "deployment_info": deployment_info or {},
                "ssl_certificate": True,
                "cdn_enabled": True,
                "backup_frequency": "daily",
                "support_24_7": False,
                "uptime_guarantee": "99.9%"
            }
            
            asset_id = self.asset_manager.create_asset(
                name=name,
                description=description,
                asset_type=AssetType.HOSTING_INFO,
                format=AssetFormat.JSON,
                file_path="",  # No file for hosting info
                created_by=self.agent_name,
                category="infrastructure",
                tags=["hosting", "deployment", "infrastructure"],
                technical_specs={},
                hosting_info=hosting_info
            )
            
            logger.info(f"Created hosting info asset {asset_id}: {name}")
            return asset_id
            
        except Exception as e:
            logger.error(f"Failed to create hosting info asset: {e}")
            return None
    
    def create_cta_template(self, name: str, description: str, platform: str,
                          template_type: str, copy: str, design_specs: Dict[str, Any] = None,
                          targeting: Dict[str, Any] = None, analytics: Dict[str, Any] = None) -> Optional[str]:
        """Create a CTA template for different platforms and use cases."""
        try:
            cta_template = {
                "platform": platform,
                "template_type": template_type,
                "copy": copy,
                "design_specs": design_specs or {
                    "button_style": "primary",
                    "color_scheme": "brand_primary",
                    "animation": "subtle_hover",
                    "responsive": True
                },
                "targeting": targeting or {
                    "audience": "general",
                    "placement": "below_content",
                    "urgency": "normal"
                },
                "analytics": analytics or {
                    "track_clicks": True,
                    "track_conversions": True,
                    "a_b_test_enabled": False
                }
            }
            
            asset_id = self.asset_manager.create_asset(
                name=name,
                description=description,
                asset_type=AssetType.CTA_TEMPLATE,
                format=AssetFormat.JSON,
                file_path="",  # No file for CTA template
                created_by=self.agent_name,
                category="marketing",
                tags=["cta", "template", "conversion", platform],
                technical_specs={},
                cta_templates=[cta_template]
            )
            
            logger.info(f"Created CTA template asset {asset_id}: {name}")
            return asset_id
            
        except Exception as e:
            logger.error(f"Failed to create CTA template asset: {e}")
            return None
    
    def search_assets(self, asset_type: str = None, category: str = None,
                    tags: List[str] = None, limit: int = 20,
                    sort_by: str = "usage_count") -> List[Dict[str, Any]]:
        """Search for assets based on criteria."""
        try:
            asset_type_enum = AssetType(asset_type) if asset_type else None
            
            assets = self.asset_manager.search_assets(
                asset_type=asset_type_enum,
                category=category,
                tags=tags,
                limit=limit,
                sort_by=sort_by
            )
            
            return [
                {
                    "asset_id": asset.asset_id,
                    "name": asset.name,
                    "description": asset.description,
                    "asset_type": asset.asset_type.value,
                    "format": asset.format.value,
                    "file_path": asset.file_path,
                    "created_by": asset.created_by,
                    "created_at": asset.created_at,
                    "updated_at": asset.updated_at,
                    "status": asset.status.value,
                    "tags": list(asset.tags),
                    "category": asset.category,
                    "usage_count": asset.usage_count,
                    "download_count": asset.download_count,
                    "rating": asset.rating,
                    "file_size": asset.file_size,
                    "preview_url": asset.preview_url,
                    "download_url": asset.download_url,
                    "technical_specs": asset.technical_specs,
                    "hosting_info": asset.hosting_info,
                    "cta_templates": asset.cta_templates
                }
                for asset in assets
            ]
            
        except Exception as e:
            logger.error(f"Failed to search assets: {e}")
            return []
    
    def get_asset_details(self, asset_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific asset."""
        try:
            asset = self.asset_manager.get_asset(asset_id)
            if not asset:
                return None
            
            return {
                "asset_id": asset.asset_id,
                "name": asset.name,
                "description": asset.description,
                "asset_type": asset.asset_type.value,
                "format": asset.format.value,
                "file_path": asset.file_path,
                "created_by": asset.created_by,
                "created_at": asset.created_at,
                "updated_at": asset.updated_at,
                "status": asset.status.value,
                "tags": list(asset.tags),
                "category": asset.category,
                "version": asset.version,
                "license": asset.license,
                "usage_count": asset.usage_count,
                "download_count": asset.download_count,
                "rating": asset.rating,
                "rating_count": asset.rating_count,
                "dependencies": asset.dependencies,
                "compatible_with": asset.compatible_with,
                "technical_specs": asset.technical_specs,
                "hosting_info": asset.hosting_info,
                "cta_templates": asset.cta_templates,
                "preview_url": asset.preview_url,
                "download_url": asset.download_url,
                "metadata": asset.metadata
            }
            
        except Exception as e:
            logger.error(f"Failed to get asset details {asset_id}: {e}")
            return None
    
    def use_asset(self, asset_id: str, usage_context: str = "") -> bool:
        """Record usage of an asset."""
        try:
            success = self.asset_manager.record_asset_usage(asset_id, self.agent_name)
            
            if success:
                asset = self.asset_manager.get_asset(asset_id)
                logger.info(f"Agent {self.agent_name} used asset {asset_id}: {asset.name} - {usage_context}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to record asset usage {asset_id}: {e}")
            return False
    
    def get_logos_for_brand(self, brand_name: str = None) -> List[Dict[str, Any]]:
        """Get available logos for brand filtering."""
        try:
            logos = self.asset_manager.get_assets_by_type(AssetType.LOGO)
            
            if brand_name:
                logos = [logo for logo in logos 
                         if brand_name.lower() in logo.name.lower() or 
                            brand_name.lower() in " ".join(logo.tags).lower()]
            
            return [
                {
                    "asset_id": logo.asset_id,
                    "name": logo.name,
                    "description": logo.description,
                    "file_path": logo.file_path,
                    "format": logo.format.value,
                    "created_by": logo.created_by,
                    "created_at": logo.created_at,
                    "status": logo.status.value,
                    "tags": list(logo.tags),
                    "usage_count": logo.usage_count,
                    "technical_specs": logo.technical_specs,
                    "preview_url": logo.preview_url,
                    "download_url": logo.download_url
                }
                for logo in logos
            ]
            
        except Exception as e:
            logger.error(f"Failed to get logos for brand {brand_name}: {e}")
            return []
    
    def get_hosting_options(self, provider: str = None, plan_type: str = None) -> List[Dict[str, Any]]:
        """Get available hosting options."""
        try:
            hosting_assets = self.asset_manager.get_assets_by_type(AssetType.HOSTING_INFO)
            
            if provider:
                hosting_assets = [h for h in hosting_assets 
                               if h.hosting_info.get("provider", "").lower() == provider.lower()]
            
            if plan_type:
                hosting_assets = [h for h in hosting_assets 
                               if h.hosting_info.get("plan", "").lower() == plan_type.lower()]
            
            return [
                {
                    "asset_id": asset.asset_id,
                    "name": asset.name,
                    "description": asset.description,
                    "hosting_info": asset.hosting_info,
                    "created_by": asset.created_by,
                    "created_at": asset.created_at,
                    "status": asset.status.value,
                    "usage_count": asset.usage_count,
                    "rating": asset.rating
                }
                for asset in hosting_assets
            ]
            
        except Exception as e:
            logger.error(f"Failed to get hosting options: {e}")
            return []
    
    def get_cta_templates(self, platform: str = None, template_type: str = None) -> List[Dict[str, Any]]:
        """Get available CTA templates."""
        try:
            cta_assets = self.asset_manager.get_assets_by_type(AssetType.CTA_TEMPLATE)
            
            templates = []
            for asset in cta_assets:
                for template in asset.cta_templates:
                    if platform and template.get("platform", "").lower() != platform.lower():
                        continue
                    if template_type and template.get("template_type", "").lower() != template_type.lower():
                        continue
                    
                    templates.append({
                        "asset_id": asset.asset_id,
                        "template_name": asset.name,
                        "platform": template.get("platform"),
                        "template_type": template.get("template_type"),
                        "copy": template.get("copy"),
                        "design_specs": template.get("design_specs"),
                        "targeting": template.get("targeting"),
                        "analytics": template.get("analytics"),
                        "created_by": asset.created_by,
                        "usage_count": asset.usage_count
                    })
            
            return templates
            
        except Exception as e:
            logger.error(f"Failed to get CTA templates: {e}")
            return []
    
    def get_asset_statistics(self) -> Dict[str, Any]:
        """Get asset management statistics."""
        try:
            return self.asset_manager.get_asset_statistics()
        except Exception as e:
            logger.error(f"Failed to get asset statistics: {e}")
            return {}
    
    def approve_asset(self, asset_id: str) -> bool:
        """Approve an asset for publication."""
        try:
            return self.asset_manager.approve_asset(asset_id, self.agent_name)
        except Exception as e:
            logger.error(f"Failed to approve asset {asset_id}: {e}")
            return False
    
    def publish_asset(self, asset_id: str) -> bool:
        """Publish an asset making it available to all agents."""
        try:
            return self.asset_manager.publish_asset(asset_id)
        except Exception as e:
            logger.error(f"Failed to publish asset {asset_id}: {e}")
            return False


def create_asset_management_prompts() -> Dict[str, str]:
    """Create specialized prompts for asset-aware agents."""
    
    return {
        "asset_aware_agent": """
You are working in an ASSET-SHARED ENVIRONMENT with collaborative resource management.

ASSET MANAGEMENT RESPONSIBILITIES:
1. Before creating resources: Search for existing assets to reuse
2. When creating assets: Use create_logo(), create_hosting_info(), create_cta_template()
3. Make assets discoverable: Use proper tags, categories, and descriptions
4. Share assets strategically: Create resources that benefit multiple agents
5. Use assets consistently: Record usage when reusing shared resources

ASSET CREATION GUIDELINES:
- Create reusable, high-quality assets that save time for other agents
- Use standard formats and specifications for compatibility
- Include comprehensive metadata for easy discovery and reuse
- Consider brand consistency and technical requirements
- Provide multiple variations when appropriate (logos, CTAs, etc.)

ASSET REUSE STRATEGY:
- Search for existing assets before creating new ones
- Use get_logos_for_brand() to find brand assets
- Use get_hosting_options() to find deployment information
- Use get_cta_templates() to find conversion-optimized CTAs
- Record asset usage with use_asset() for tracking and analytics

COLLABORATIVE RESOURCE SHARING:
- Contribute assets that solve common problems across agents
- Share successful design patterns and templates
- Create hosting and deployment guides for reproducible setups
- Provide CTA templates optimized for different platforms and audiences
- Help build a comprehensive asset library for the entire system

Your goal is to BUILD AND SHARE VALUABLE ASSETS that accelerate development for all agents.
""",
        
        "asset_curator": """
You are the ASSET CURATOR responsible for managing the shared asset ecosystem.

CURATION RESPONSIBILITIES:
1. Review and approve asset submissions for quality and relevance
2. Organize assets into logical categories and tagging systems
3. Ensure assets meet technical standards and compatibility requirements
4. Monitor asset usage and popularity to identify high-value resources
5. Maintain asset library health and remove outdated or low-quality assets

QUALITY ASSURANCE:
- Ensure all assets meet minimum quality standards
- Validate technical specifications and compatibility
- Check for proper licensing and usage rights
- Review asset metadata for completeness and accuracy
- Test assets for functionality and performance

ORGANIZATION OPTIMIZATION:
- Maintain consistent categorization and tagging systems
- Identify and fill gaps in the asset library
- Create collections and featured asset sets
- Optimize search and discovery mechanisms
- Generate usage analytics and popularity metrics

RESOURCE GOVERNANCE:
- Establish asset creation guidelines and standards
- Monitor asset lifecycle and manage deprecation
- Facilitate asset versioning and update processes
- Ensure assets support diverse use cases and platforms
- Generate insights on asset effectiveness and adoption

Your role is to ensure the SHARED ASSET LIBRARY remains a HIGH-QUALITY, WELL-ORGANIZED resource for all agents.
""",
        
        "brand_asset_manager": """
You are a BRAND ASSET MANAGER focused on creating and maintaining brand assets.

BRAND ASSET RESPONSIBILITIES:
1. Create comprehensive logo suites with multiple variations
2. Develop brand guidelines and asset usage standards
3. Ensure brand consistency across all created assets
4. Provide brand assets in multiple formats for different use cases
5. Create brand-specific hosting and CTA templates

BRAND CONSISTENCY:
- Maintain consistent color palettes, typography, and design language
- Ensure all brand assets work together harmoniously
- Create scalable assets that work across different sizes and contexts
- Provide clear usage guidelines and brand standards
- Consider brand application across different platforms and media

ASSET DELIVERABLES:
- Logo variations (primary, secondary, icon, monogram)
- Color palette definitions and usage guidelines
- Typography specifications and pairing rules
- Brand application examples and templates
- Platform-specific adaptations and requirements

COLLABORATIVE BRAND DEVELOPMENT:
- Share brand assets with other agents for consistent application
- Provide brand guidelines for proper asset usage
- Create brand-specific templates for common use cases
- Ensure brand assets support diverse marketing needs
- Maintain brand versioning and update processes

Your goal is to CREATE COMPREHENSIVE BRAND ASSETS that ensure consistent, professional brand representation across all applications.
"""
    }
