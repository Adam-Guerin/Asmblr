"""
Shared Asset Management System for collaborative resource creation and reuse.
"""

from typing import Any
from dataclasses import dataclass, field
from enum import Enum
import json
from pathlib import Path
from datetime import datetime, UTC
from loguru import logger


class AssetType(Enum):
    """Types of shared assets."""
    LOGO = "logo"
    BANNER = "banner"
    ICON = "icon"
    SCREENSHOT = "screenshot"
    DEMO = "demo"
    VIDEO = "video"
    HOSTING_INFO = "hosting_info"
    CTA_TEMPLATE = "cta_template"
    LANDING_PAGE = "landing_page"
    BRAND_GUIDELINE = "brand_guideline"
    COLOR_PALETTE = "color_palette"
    TYPOGRAPHY = "typography"
    ILLUSTRATION = "illustration"
    PROTOTYPE = "prototype"
    DOCUMENTATION = "documentation"


class AssetStatus(Enum):
    """Status of shared assets."""
    DRAFT = "draft"
    REVIEW = "review"
    APPROVED = "approved"
    PUBLISHED = "published"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


class AssetFormat(Enum):
    """File formats for assets."""
    PNG = "png"
    JPG = "jpg"
    SVG = "svg"
    GIF = "gif"
    MP4 = "mp4"
    WEBM = "webm"
    HTML = "html"
    CSS = "css"
    JS = "js"
    JSON = "json"
    MD = "md"
    PDF = "pdf"
    Figma = "figma"
    PSD = "psd"


@dataclass
class AssetMetadata:
    """Metadata for shared assets."""
    asset_id: str
    name: str
    description: str
    asset_type: AssetType
    format: AssetFormat
    file_path: str
    file_size: int
    created_by: str
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    status: AssetStatus = AssetStatus.DRAFT
    tags: set[str] = field(default_factory=set)
    category: str = ""
    version: str = "1.0.0"
    license: str = "internal"
    usage_count: int = 0
    download_count: int = 0
    rating: float = 0.0
    rating_count: int = 0
    dependencies: list[str] = field(default_factory=list)
    compatible_with: list[str] = field(default_factory=list)
    technical_specs: dict[str, Any] = field(default_factory=dict)
    hosting_info: dict[str, Any] = field(default_factory=dict)
    cta_templates: list[dict[str, Any]] = field(default_factory=list)
    preview_url: str | None = None
    download_url: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def add_tag(self, tag: str) -> None:
        """Add a tag to this asset."""
        self.tags.add(tag.lower().strip())
        self.updated_at = datetime.now(UTC).isoformat()
    
    def record_usage(self) -> None:
        """Record usage of this asset."""
        self.usage_count += 1
        self.updated_at = datetime.now(UTC).isoformat()
    
    def record_download(self) -> None:
        """Record download of this asset."""
        self.download_count += 1
        self.updated_at = datetime.now(UTC).isoformat()
    
    def add_rating(self, rating: float) -> None:
        """Add a rating to this asset."""
        total_rating = self.rating * self.rating_count + rating
        self.rating_count += 1
        self.rating = total_rating / self.rating_count
        self.updated_at = datetime.now(UTC).isoformat()


class SharedAssetManager:
    """Manages shared assets for agent collaboration."""
    
    def __init__(self, assets_dir: Path):
        self.assets_dir = assets_dir
        self.assets_dir.mkdir(parents=True, exist_ok=True)
        self.assets: dict[str, AssetMetadata] = {}
        self.categories: set[str] = set()
        self.tags: set[str] = set()
        self._load_assets()
    
    def create_asset(self, name: str, description: str, asset_type: AssetType,
                   format: AssetFormat, file_path: str, created_by: str,
                   category: str = "", tags: list[str] = None,
                   technical_specs: dict[str, Any] = None,
                   hosting_info: dict[str, Any] = None,
                   cta_templates: list[dict[str, Any]] = None) -> str | None:
        """Create a new shared asset."""
        try:
            # Generate unique asset ID
            asset_id = f"asset_{asset_type.value}_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}_{len(self.assets)}"
            
            # Get file size
            full_path = self.assets_dir / file_path
            file_size = full_path.stat().st_size if full_path.exists() else 0
            
            # Create asset metadata
            asset = AssetMetadata(
                asset_id=asset_id,
                name=name,
                description=description,
                asset_type=asset_type,
                format=format,
                file_path=file_path,
                file_size=file_size,
                created_by=created_by,
                category=category,
                tags=set(tags or []),
                technical_specs=technical_specs or {},
                hosting_info=hosting_info or {},
                cta_templates=cta_templates or []
            )
            
            self.assets[asset_id] = asset
            self.categories.add(category)
            self.tags.update(asset.tags)
            
            # Save asset metadata
            self._save_asset(asset)
            
            logger.info(f"Created asset {asset_id}: {name} by {created_by}")
            return asset_id
            
        except Exception as e:
            logger.error(f"Failed to create asset: {e}")
            return None
    
    def get_asset(self, asset_id: str) -> AssetMetadata | None:
        """Get a specific asset by ID."""
        return self.assets.get(asset_id)
    
    def search_assets(self, asset_type: AssetType = None, category: str = None,
                    tags: list[str] = None, created_by: str = None,
                    status: AssetStatus = None, format: AssetFormat = None,
                    limit: int = 50, sort_by: str = "created_at") -> list[AssetMetadata]:
        """Search assets based on criteria."""
        results = []
        
        for asset in self.assets.values():
            # Filter by asset type
            if asset_type and asset.asset_type != asset_type:
                continue
            
            # Filter by category
            if category and asset.category != category:
                continue
            
            # Filter by creator
            if created_by and asset.created_by != created_by:
                continue
            
            # Filter by status
            if status and asset.status != status:
                continue
            
            # Filter by format
            if format and asset.format != format:
                continue
            
            # Filter by tags
            if tags and not any(tag.lower() in asset.tags for tag in tags):
                continue
            
            results.append(asset)
        
        # Sort results
        if sort_by == "created_at":
            results.sort(key=lambda x: x.created_at, reverse=True)
        elif sort_by == "updated_at":
            results.sort(key=lambda x: x.updated_at, reverse=True)
        elif sort_by == "usage_count":
            results.sort(key=lambda x: x.usage_count, reverse=True)
        elif sort_by == "rating":
            results.sort(key=lambda x: x.rating, reverse=True)
        elif sort_by == "download_count":
            results.sort(key=lambda x: x.download_count, reverse=True)
        
        return results[:limit]
    
    def get_assets_by_type(self, asset_type: AssetType) -> list[AssetMetadata]:
        """Get all assets of a specific type."""
        return [asset for asset in self.assets.values() if asset.asset_type == asset_type]
    
    def get_popular_assets(self, limit: int = 20) -> list[AssetMetadata]:
        """Get most popular assets by usage and downloads."""
        return sorted(
            self.assets.values(),
            key=lambda x: (x.usage_count * 0.7 + x.download_count * 0.3),
            reverse=True
        )[:limit]
    
    def get_recent_assets(self, limit: int = 20) -> list[AssetMetadata]:
        """Get most recently created assets."""
        return sorted(
            self.assets.values(),
            key=lambda x: x.created_at,
            reverse=True
        )[:limit]
    
    def update_asset(self, asset_id: str, updates: dict[str, Any]) -> bool:
        """Update an existing asset."""
        if asset_id not in self.assets:
            logger.error(f"Asset {asset_id} not found")
            return False
        
        try:
            asset = self.assets[asset_id]
            
            # Update allowed fields
            for key, value in updates.items():
                if hasattr(asset, key):
                    setattr(asset, key, value)
            
            asset.updated_at = datetime.now(UTC).isoformat()
            self._save_asset(asset)
            
            logger.info(f"Updated asset {asset_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update asset {asset_id}: {e}")
            return False
    
    def approve_asset(self, asset_id: str, approved_by: str) -> bool:
        """Approve an asset for publication."""
        return self.update_asset(asset_id, {
            "status": AssetStatus.APPROVED,
            "metadata": {"approved_by": approved_by, "approved_at": datetime.now(UTC).isoformat()}
        })
    
    def publish_asset(self, asset_id: str) -> bool:
        """Publish an asset making it available to all agents."""
        asset = self.get_asset(asset_id)
        if not asset or asset.status != AssetStatus.APPROVED:
            logger.error(f"Asset {asset_id} must be approved before publishing")
            return False
        
        return self.update_asset(asset_id, {
            "status": AssetStatus.PUBLISHED,
            "metadata": {"published_at": datetime.now(UTC).isoformat()}
        })
    
    def record_asset_usage(self, asset_id: str, used_by: str) -> bool:
        """Record usage of an asset."""
        asset = self.get_asset(asset_id)
        if not asset:
            return False
        
        asset.record_usage()
        
        # Add usage record to metadata
        usage_records = asset.metadata.get("usage_records", [])
        usage_records.append({
            "used_by": used_by,
            "used_at": datetime.now(UTC).isoformat()
        })
        asset.metadata["usage_records"] = usage_records
        
        return self._save_asset(asset)
    
    def get_asset_statistics(self) -> dict[str, Any]:
        """Get asset management statistics."""
        stats = {
            "total_assets": len(self.assets),
            "by_type": {},
            "by_status": {},
            "by_category": {},
            "total_creators": len(set(asset.created_by for asset in self.assets.values())),
            "total_usage": sum(asset.usage_count for asset in self.assets.values()),
            "total_downloads": sum(asset.download_count for asset in self.assets.values()),
            "average_rating": 0.0,
            "most_popular": [],
            "most_recent": [],
            "top_creators": {}
        }
        
        if not self.assets:
            return stats
        
        # Calculate statistics
        for asset in self.assets.values():
            # By type
            asset_type = asset.asset_type.value
            stats["by_type"][asset_type] = stats["by_type"].get(asset_type, 0) + 1
            
            # By status
            status = asset.status.value
            stats["by_status"][status] = stats["by_status"].get(status, 0) + 1
            
            # By category
            if asset.category:
                stats["by_category"][asset.category] = stats["by_category"].get(asset.category, 0) + 1
            
            # Top creators
            creator = asset.created_by
            stats["top_creators"][creator] = stats["top_creators"].get(creator, 0) + 1
        
        # Average rating
        rated_assets = [a for a in self.assets.values() if a.rating_count > 0]
        if rated_assets:
            stats["average_rating"] = sum(a.rating for a in rated_assets) / len(rated_assets)
        
        # Most popular
        stats["most_popular"] = self.get_popular_assets(10)
        
        # Most recent
        stats["most_recent"] = self.get_recent_assets(10)
        
        return stats
    
    def get_hosting_info_for_asset(self, asset_id: str) -> dict[str, Any] | None:
        """Get hosting information for a specific asset."""
        asset = self.get_asset(asset_id)
        if not asset:
            return None
        
        return asset.hosting_info
    
    def get_cta_templates_for_asset(self, asset_id: str) -> list[dict[str, Any]]:
        """Get CTA templates for a specific asset."""
        asset = self.get_asset(asset_id)
        if not asset:
            return []
        
        return asset.cta_templates
    
    def _save_asset(self, asset: AssetMetadata) -> None:
        """Save asset metadata to file."""
        try:
            asset_file = self.assets_dir / f"{asset.asset_id}.json"
            
            # Convert to serializable format
            asset_data = {
                "asset_id": asset.asset_id,
                "name": asset.name,
                "description": asset.description,
                "asset_type": asset.asset_type.value,
                "format": asset.format.value,
                "file_path": asset.file_path,
                "file_size": asset.file_size,
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
            
            asset_file.write_text(json.dumps(asset_data, indent=2), encoding="utf-8")
            
        except Exception as e:
            logger.error(f"Failed to save asset {asset.asset_id}: {e}")
    
    def _load_assets(self) -> None:
        """Load all assets from files."""
        try:
            for asset_file in self.assets_dir.glob("asset_*.json"):
                try:
                    asset_data = json.loads(asset_file.read_text(encoding="utf-8"))
                    
                    # Convert back to AssetMetadata
                    asset = AssetMetadata(
                        asset_id=asset_data["asset_id"],
                        name=asset_data["name"],
                        description=asset_data["description"],
                        asset_type=AssetType(asset_data["asset_type"]),
                        format=AssetFormat(asset_data["format"]),
                        file_path=asset_data["file_path"],
                        file_size=asset_data["file_size"],
                        created_by=asset_data["created_by"],
                        created_at=asset_data.get("created_at"),
                        updated_at=asset_data.get("updated_at"),
                        status=AssetStatus(asset_data.get("status", "draft")),
                        tags=set(asset_data.get("tags", [])),
                        category=asset_data.get("category", ""),
                        version=asset_data.get("version", "1.0.0"),
                        license=asset_data.get("license", "internal"),
                        usage_count=asset_data.get("usage_count", 0),
                        download_count=asset_data.get("download_count", 0),
                        rating=asset_data.get("rating", 0.0),
                        rating_count=asset_data.get("rating_count", 0),
                        dependencies=asset_data.get("dependencies", []),
                        compatible_with=asset_data.get("compatible_with", []),
                        technical_specs=asset_data.get("technical_specs", {}),
                        hosting_info=asset_data.get("hosting_info", {}),
                        cta_templates=asset_data.get("cta_templates", []),
                        preview_url=asset_data.get("preview_url"),
                        download_url=asset_data.get("download_url"),
                        metadata=asset_data.get("metadata", {})
                    )
                    
                    self.assets[asset.asset_id] = asset
                    
                    if asset.category:
                        self.categories.add(asset.category)
                    
                    self.tags.update(asset.tags)
                    
                except Exception as e:
                    logger.error(f"Failed to load asset {asset_file}: {e}")
            
            logger.info(f"Loaded {len(self.assets)} shared assets")
            
        except Exception as e:
            logger.error(f"Failed to load assets: {e}")
