"""
Motion Design System V2 pour Asmblr - Création de campagnes marketing animées
"""

import json
import random
from datetime import datetime
from typing import Any
from dataclasses import dataclass
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import io

from app.core.smart_logger import get_smart_logger, LogCategory, LogLevel
from app.core.error_handler_v2 import handle_errors


@dataclass
class MotionAsset:
    """Asset pour le motion design"""
    name: str
    type: str  # image, video, audio, font
    content: bytes
    metadata: dict[str, Any]
    created_at: datetime


@dataclass
class MotionScene:
    """Scene de motion design"""
    name: str
    duration: float  # en secondes
    assets: list[MotionAsset]
    transitions: list[dict[str, Any]]
    created_at: datetime


@dataclass
class Campaign:
    """Campagne marketing avec motion design"""
    name: str
    brand_guidelines: dict[str, Any]
    target_audience: str
    duration: float
    scenes: list[MotionScene]
    total_duration: float
    created_at: datetime
    status: str  # draft, in_progress, completed, published, archived


class MotionDesignSystemV2:
    """Systeme de motion design pour Asmblr"""
    
    def __init__(self, assets_dir: str = "assets/motion"):
        self.smart_logger = get_smart_logger()
        self.assets_dir = Path(assets_dir)
        self.assets_dir.mkdir(exist_ok=True)
        
        # Configuration par defaut
        self.default_brand_colors = {
            "primary": "#2563EB",
            "secondary": "#FF6B6B",
            "accent": "#FFC107",
            "text": "#FFFFFF",
            "background": "#F8F9FA",
            "warning": "#FFC107",
            "success": "#10B981"
        }
        
        self.default_fonts = {
            "modern": ["Inter", "Roboto", "Open Sans", "Montserrat"],
            "classic": ["Georgia", "Times New Roman", "Playfair Display"]
        }
        
        self.default_animations = [
            "fade_in", "slide_up", "slide_down", "zoom_in", "zoom_out", 
            "rotate", "bounce", "pulse", "shake", "typewriter"
        ]
    
    @handle_errors("asset_creation", reraise=False)
    def create_text_asset(self, text: str, font_name: str = None, 
                      font_size: int = 24, color: str = None) -> MotionAsset:
        """Cree un asset de texte"""
        try:
            # Utiliser une police par defaut si non specifiee
            if font_name is None:
                font_name = random.choice(self.default_fonts["modern"])
            
            # Utiliser une couleur par defaut si non specifiee
            if color is None:
                color = self.default_brand_colors["text"]
            
            # Creer l'image avec Pillow
            font = ImageFont.truetype(font_name, font_size)
            font_size = font_size or 24
            
            # Calculer la taille du texte
            lines = text.split('\n')
            max_width = max(len(line) for line in lines)
            
            # Creer l'image
            img = Image.new('RGBA', (max_width + 20, len(lines) * (font_size + 5)), (255, 255, 255, 0))
            draw = ImageDraw.Draw(img)
            
            # Dessiner le texte
            y_offset = 10
            for line in lines:
                draw.text((10, y_offset), line, font=font, fill=color)
                y_offset += font_size + 5
            
            # Convertir en bytes
            img_bytes = io.BytesIO()
            img.save(img_bytes, format='PNG')
            img_bytes.seek(0)
            
            content = img_bytes.getvalue()
            
            asset = MotionAsset(
                name=f"text_{font_name}_{len(text)}chars",
                type="image",
                content=content,
                metadata={
                    "font_name": font_name,
                    "font_size": font_size,
                    "color": color,
                    "text_length": len(text),
                    "image_size": img.size
                },
                created_at=datetime.utcnow()
            )
            
            self.smart_logger.info(
                LogCategory.SYSTEM,
                "asset_created",
                f"Asset texte cree: {asset.name}",
                metadata={"type": asset.type, "size": len(content)}
            )
            
            return asset
            
        except Exception as e:
            self.smart_logger.error(
                LogCategory.SYSTEM,
                "asset_creation_error",
                f"Erreur creation asset texte: {str(e)}"
            )
            raise
    
    @handle_errors("image_generation", reraise=False)
    def generate_logo_variants(self, brand_name: str, tagline: str = None) -> list[MotionAsset]:
        """Genere des variantes de logo"""
        assets = []
        
        try:
            # Logo principal
            logo_asset = self.create_text_asset(
                text=brand_name,
                font_name="Montserrat",
                font_size=32,
                color=self.default_brand_colors["primary"]
            )
            assets.append(logo_asset)
            
            # Logo avec tagline
            if tagline:
                tagline_asset = self.create_text_asset(
                    text=f"{brand_name}\n{tagline}",
                    font_name="Montserrat",
                    font_size=24,
                    color=self.default_brand_colors["secondary"]
                )
                assets.append(tagline_asset)
            
            # Variations de couleurs
            color_variants = [
                ("primary", self.default_brand_colors["primary"]),
                ("secondary", self.default_brand_colors["secondary"]),
                ("accent", self.default_brand_colors["accent"]),
                ("text", self.default_brand_colors["text"]),
                ("background", self.default_brand_colors["background"])
            ]
            
            for color_name, color in color_variants:
                color_asset = self.create_text_asset(
                    text=brand_name,
                    font_name="Inter",
                    font_size=28,
                    color=color
                )
                assets.append(color_asset)
            
            self.smart_logger.info(
                LogCategory.SYSTEM,
                "logo_variants_generated",
                f"{len(assets)} variantes de logo creees pour {brand_name}"
            )
            
            return assets
            
        except Exception as e:
            self.smart_logger.error(
                LogCategory.SYSTEM,
                "logo_generation_error",
                f"Erreur generation logos: {str(e)}"
            )
            raise
    
    @handle_errors("scene_creation", reraise=False)
    def create_scene(self, name: str, duration: float, assets: list[MotionAsset], 
                   transitions: list[dict[str, Any]] = None) -> MotionScene:
        """Cree une scene de motion design"""
        try:
            scene = MotionScene(
                name=name,
                duration=duration,
                assets=assets,
                transitions=transitions or [],
                created_at=datetime.utcnow()
            )
            
            self.smart_logger.info(
                LogCategory.SYSTEM,
                "scene_created",
                f"Scene cree: {name} ({duration}s, {len(assets)} assets)"
            )
            
            return scene
            
        except Exception as e:
            self.smart_logger.error(
                LogCategory.SYSTEM,
                "scene_creation_error",
                f"Erreur creation scene: {str(e)}"
            )
            raise
    
    @handle_errors("campaign_creation", reraise=False)
    def create_campaign(self, name: str, brand_name: str, target_audience: str, 
                     duration: float, brand_guidelines: dict[str, Any] = None) -> Campaign:
        """Cree une campagne marketing complete"""
        try:
            # Generation des assets de base
            logo_assets = self.generate_logo_variants(brand_name)
            
            # Creation des scenes
            scenes = []
            total_duration = 0
            
            # Scene 1: Logo anime
            logo_scene = self.create_scene(
                name="logo_intro",
                duration=2.0,
                assets=[logo_assets[0]],  # Logo principal
                transitions=[
                    {"type": "fade_in", "duration": 0.5, "easing": "ease-in-out"},
                    {"type": "zoom_in", "duration": 0.3, "easing": "ease-in-out"},
                    {"type": "zoom_out", "duration": 0.3, "easing": "ease-in-out"},
                    {"type": "pulse", "duration": 0.5, "easing": "ease-in-out"}
                ]
            )
            scenes.append(logo_scene)
            total_duration += 2.0
            
            # Scene 2: Texte anime
            text_scenes = [
                "Innovation",
                "Performance",
                "Reliability",
                "Security"
            ]
            
            for text in text_scenes:
                text_asset = self.create_text_asset(
                    text=text,
                    font_name="Roboto",
                    font_size=28,
                    color=self.default_brand_colors["text"]
                )
                
                text_scene = self.create_scene(
                    name=f"text_{text.lower()}",
                    duration=1.5,
                    assets=[text_asset],
                    transitions=[
                        {"type": "typewriter", "duration": 1.5, "easing": "ease-in-out"},
                        {"type": "fade_in", "duration": 0.5, "easing": "ease-in-out"},
                        {"type": "fade_out", "duration": 0.5, "easing": "ease-in-out"}
                    ]
                )
                scenes.append(text_scene)
                total_duration += 1.5
            
            # Scene 3: Call-to-action
            cta_assets = [
                self.create_text_asset(
                    text="Start Free Trial",
                    font_name="Inter",
                    font_size=20,
                    color=self.default_brand_colors["success"]
                )
            ]
            
            cta_scene = self.create_scene(
                name="call_to_action",
                duration=1.0,
                assets=[cta_assets[0]],
                transitions=[
                    {"type": "bounce", "duration": 0.5, "easing": "ease-in-out"},
                    {"type": "pulse", "duration": 0.3, "easing": "ease-in-out"}
                ]
            )
            scenes.append(cta_scene)
            total_duration += 1.0
            
            # Creer la campagne
            campaign = Campaign(
                name=name,
                brand_guidelines=brand_guidelines or self._get_default_brand_guidelines(),
                target_audience=target_audience,
                duration=total_duration,
                scenes=scenes,
                total_duration=total_duration,
                created_at=datetime.utcnow(),
                status="draft"
            )
            
            self.smart_logger.business(
                LogLevel.HIGH,
                "campaign_created",
                f"Campagne cree: {name} ({total_duration:.1f}s, {len(scenes)} scenes)",
                metadata={
                    "brand": brand_name,
                    "target_audience": target_audience,
                    "total_assets": len(logo_assets) + len(text_scenes) + len(cta_assets)
                }
            )
            
            return campaign
            
        except Exception as e:
            self.smart_logger.error(
                LogCategory.SYSTEM,
                "campaign_creation_error",
                f"Erreur creation campagne: {str(e)}"
            )
            raise
    
    def _get_default_brand_guidelines(self) -> dict[str, Any]:
        """Retourne les guidelines de marque par defaut"""
        return {
            "colors": self.default_brand_colors,
            "fonts": self.default_fonts,
            "animations": self.default_animations,
            "duration_recommendations": {
                "logo_intro": 2.0,
                "text_animation": 1.5,
                "call_to_action": 1.0
            },
            "aspect_ratios": {
                "logo": "1.0",
                "text": "16.9",
                "video": "16.9"
            }
        }
    
    def export_campaign(self, campaign: Campaign, format_type: str = "json") -> str:
        """Exporte une campagne"""
        try:
            export_data = {
                "campaign": {
                    "name": campaign.name,
                    "brand_guidelines": campaign.brand_guidelines,
                    "target_audience": campaign.target_audience,
                    "duration": campaign.total_duration,
                    "status": campaign.status,
                    "created_at": campaign.created_at.isoformat()
                },
                "scenes": [
                    {
                        "name": scene.name,
                        "duration": scene.duration,
                        "assets": [
                            {
                                "name": asset.name,
                                "type": asset.type,
                                "size": len(asset.content)
                            } for asset in scene.assets
                        ],
                        "transitions": scene.transitions
                    } for scene in campaign.scenes
                ]
            }
            
            if format_type == "json":
                return json.dumps(export_data, indent=2)
            elif format_type == "html":
                return self._export_html_campaign(campaign)
            else:
                raise ValueError(f"Format non supporte: {format_type}")
            
        except Exception as e:
            self.smart_logger.error(
                LogCategory.SYSTEM,
                "campaign_export_error",
                f"Erreur export campagne: {str(e)}"
            )
            raise
    
    def _export_html_campaign(self, campaign: Campaign) -> str:
        """Exporte une campagne en HTML"""
        html_template = f"""
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>{campaign.name} - Campagne Marketing</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #f8f9fa, #e3f2fd);
            color: #333;
            margin: 0;
            padding: 20px;
            line-height: 1.6;
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
            color: white;
        }}
        .campaign-title {{
            font-size: 2.5em;
            font-weight: bold;
            margin-bottom: 10px;
        }}
        .scene {{
            background: rgba(255, 255, 255, 0.9);
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            text-align: center;
            position: relative;
            overflow: hidden;
        }}
        .scene-title {{
            font-size: 1.5em;
            font-weight: bold;
            margin-bottom: 10px;
            color: {campaign.brand_guidelines["colors"]["text"]};
        }}
        .scene-content {{
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100px;
        }}
        .asset {{
            max-width: 200px;
            max-height: 200px;
            border-radius: 5px;
            object-fit: contain;
        }}
        .cta-button {{
            background: {campaign.brand_guidelines["colors"]["success"]};
            color: white;
            border: none;
            padding: 15px 30px;
            border-radius: 5px;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s ease;
        }}
        .cta-button:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .timeline {{
            max-width: 800px;
            margin: 0 auto;
            padding: 20px 0;
        }}
        .timeline-item {{
            background: rgba(255, 255, 255, 0.1);
            border-left: 4px solid {campaign.brand_guidelines["colors"]["accent"]};
            padding: 15px;
            margin-bottom: 10px;
            border-radius: 5px;
            position: relative;
        }}
        .timeline-content {{
            font-weight: bold;
            color: {campaign.brand_guidelines["colors"]["text"]};
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1 class="campaign-title">{campaign.name}</h1>
            <p>Campagne pour {campaign.target_audience}</p>
            <p>Duree totale: {campaign.total_duration:.1f}s</p>
        </div>
        
        <div class="timeline">
            {self._generate_timeline_html(campaign)}
        </div>
        
        <div class="campaign-footer">
            <button class="cta-button" onclick="window.location.href='#contact'">
                Commencer l'aventure
            </button>
        </div>
    </div>
</body>
</html>
        """
        
        return html_template
    
    def _generate_timeline_html(self, campaign: Campaign) -> str:
        """Genere le HTML pour la timeline"""
        timeline_html = ""
        
        current_time = 0.0
        
        for scene in campaign.scenes:
            timeline_html += f"""
            <div class="timeline-item">
                <div class="timeline-content">
                    <div class="scene-title">{scene.name}</div>
                    <div class="timeline-time">{current_time:.1f}s</div>
                </div>
            </div>
            """
            current_time += scene.duration
        
        return timeline_html
    
    def generate_video_script(self, campaign: Campaign) -> str:
        """Genere un script de video pour la campagne"""
        scenes_js = []
        
        for i, scene in enumerate(campaign.scenes):
            scene_js = f"""
                // Scene {i+1}: {scene.name}
                {self._generate_scene_js(scene, i+1)}
            """
            scenes_js.append(scene_js)
        
        # Script principal
        main_js = f"""
// Script de generation video pour {campaign.name}
class CampaignVideoGenerator {{
    constructor() {{
        this.scenes = {json.dumps(scenes_js, indent=2)};
        this.currentScene = 0;
        this.canvas = document.getElementById('video-canvas');
        this.ctx = this.canvas.getContext('2d');
        this.width = 1920;
        this.height = 1080;
        this.frameCount = 0;
        
        this.animate = function() {{
            this.clearCanvas();
            this.frameCount++;
            
            if (this.currentScene < this.scenes.length) {{
                eval(this.scenes[this.currentScene]);
                this.currentScene++;
            }} else {{
                this.currentScene = 0;
            }}
        }};
        
        this.animate();
        
        setInterval(this.animate, 1000/30); // 30 fps
    }}
    
    CampaignVideoGenerator();
        """
        
        return main_js
    
    def _generate_scene_js(self, scene: MotionScene, scene_number: int) -> str:
        """Genere le JavaScript pour une scene"""
        scene_js = f"""
        function renderScene{scene_number}() {{
            // Clear canvas
            this.ctx.clearRect(0, 0, this.width, this.height);
            
            // Set background
            this.ctx.fillStyle = '{campaign.brand_guidelines["colors"]["background"]}';
            this.ctx.fillRect(0, 0, this.width, this.height);
            
            // Render assets
            const assets = {json.dumps([asset.name for asset in scene.assets])};
            const transitions = {json.dumps(scene.transitions)};
            
            // Animation logic here
            // This would contain the actual animation code
            console.log('Rendering scene: {scene.name}');
        }}
        """
        
        return scene_js
    
    def get_campaign_summary(self, campaign: Campaign) -> dict[str, Any]:
        """Retourne un resume de la campagne"""
        return {
            "name": campaign.name,
            "brand": campaign.brand_guidelines["colors"]["primary"],
            "target_audience": campaign.target_audience,
            "total_duration": campaign.total_duration,
            "scenes_count": len(campaign.scenes),
            "total_assets": sum(len(scene.assets) for scene in campaign.scenes),
            "status": campaign.status,
            "created_at": campaign.created_at.isoformat()
        }


# Instance globale du systeme de motion design
motion_design_system_v2 = MotionDesignSystemV2()
