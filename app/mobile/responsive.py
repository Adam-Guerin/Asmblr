"""
Mobile Responsive Design for Asmblr
Progressive Web App with mobile-first design and offline capabilities
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
from fastapi import Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

logger = logging.getLogger(__name__)

class DeviceType(Enum):
    """Device types"""
    MOBILE = "mobile"
    TABLET = "tablet"
    DESKTOP = "desktop"
    UNKNOWN = "unknown"

class ScreenSize(Enum):
    """Screen size categories"""
    XS = "xs"  # < 576px
    SM = "sm"  # 576px - 768px
    MD = "md"  # 768px - 992px
    LG = "lg"  # 992px - 1200px
    XL = "xl"  # 1200px - 1400px
    XXL = "xxl" # > 1400px

@dataclass
class DeviceInfo:
    """Device information"""
    user_agent: str
    device_type: DeviceType
    screen_size: ScreenSize
    screen_width: int
    screen_height: int
    pixel_ratio: float
    is_touch: bool
    is_mobile: bool
    browser: str
    os: str
    supports_pwa: bool
    supports_offline: bool

@dataclass
class ResponsiveConfig:
    """Responsive configuration"""
    breakpoints: Dict[str, int]
    grid_columns: Dict[str, int]
    font_sizes: Dict[str, Dict[str, str]]
    spacing: Dict[str, Dict[str, str]]
    components: Dict[str, Dict[str, Any]]

class ResponsiveDesignManager:
    """Mobile responsive design manager"""
    
    def __init__(self):
        self.templates = Jinja2Templates(directory="templates")
        self.responsive_config = self._initialize_responsive_config()
        self.pwa_config = self._initialize_pwa_config()
        
    def _initialize_responsive_config(self) -> ResponsiveConfig:
        """Initialize responsive configuration"""
        return ResponsiveConfig(
            breakpoints={
                "xs": 0,
                "sm": 576,
                "md": 768,
                "lg": 992,
                "xl": 1200,
                "xxl": 1400
            },
            grid_columns={
                "xs": 1,
                "sm": 2,
                "md": 3,
                "lg": 4,
                "xl": 6,
                "xxl": 12
            },
            font_sizes={
                "xs": {"h1": "2rem", "h2": "1.5rem", "h3": "1.25rem", "body": "0.875rem"},
                "sm": {"h1": "2.5rem", "h2": "2rem", "h3": "1.5rem", "body": "1rem"},
                "md": {"h1": "3rem", "h2": "2.5rem", "h3": "1.75rem", "body": "1.125rem"},
                "lg": {"h1": "3.5rem", "h2": "3rem", "h3": "2rem", "body": "1.25rem"},
                "xl": {"h1": "4rem", "h2": "3.5rem", "h3": "2.25rem", "body": "1.5rem"}
            },
            spacing={
                "xs": {"padding": "0.5rem", "margin": "0.25rem", "gap": "0.5rem"},
                "sm": {"padding": "1rem", "margin": "0.5rem", "gap": "1rem"},
                "md": {"padding": "1.5rem", "margin": "1rem", "gap": "1.5rem"},
                "lg": {"padding": "2rem", "margin": "1.5rem", "gap": "2rem"},
                "xl": {"padding": "3rem", "margin": "2rem", "gap": "3rem"}
            },
            components={
                "navigation": {
                    "xs": {"collapsible": True, "hamburger": True, "sticky": False},
                    "sm": {"collapsible": True, "hamburger": True, "sticky": False},
                    "md": {"collapsible": False, "hamburger": False, "sticky": True},
                    "lg": {"collapsible": False, "hamburger": False, "sticky": True}
                },
                "sidebar": {
                    "xs": {"visible": False, "overlay": True, "width": "100%"},
                    "sm": {"visible": False, "overlay": True, "width": "80%"},
                    "md": {"visible": True, "overlay": False, "width": "280px"},
                    "lg": {"visible": True, "overlay": False, "width": "320px"}
                },
                "cards": {
                    "xs": {"columns": 1, "height": "auto", "elevation": 2},
                    "sm": {"columns": 2, "height": "auto", "elevation": 4},
                    "md": {"columns": 3, "height": "auto", "elevation": 6},
                    "lg": {"columns": 4, "height": "auto", "elevation": 8}
                },
                "forms": {
                    "xs": {"layout": "vertical", "full_width": True, "stacked": True},
                    "sm": {"layout": "vertical", "full_width": True, "stacked": True},
                    "md": {"layout": "horizontal", "full_width": False, "stacked": False},
                    "lg": {"layout": "horizontal", "full_width": False, "stacked": False}
                }
            }
        )
    
    def _initialize_pwa_config(self) -> Dict[str, Any]:
        """Initialize PWA configuration"""
        return {
            "name": "Asmblr - AI MVP Generator",
            "short_name": "Asmblr",
            "description": "AI-powered MVP generation platform",
            "theme_color": "#3B82F6",
            "background_color": "#ffffff",
            "display": "standalone",
            "orientation": "portrait-primary",
            "scope": "/",
            "start_url": "/",
            "icons": [
                {
                    "src": "/icons/icon-72x72.png",
                    "sizes": "72x72",
                    "type": "image/png"
                },
                {
                    "src": "/icons/icon-96x96.png",
                    "sizes": "96x96",
                    "type": "image/png"
                },
                {
                    "src": "/icons/icon-128x128.png",
                    "sizes": "128x128",
                    "type": "image/png"
                },
                {
                    "src": "/icons/icon-144x144.png",
                    "sizes": "144x144",
                    "type": "image/png"
                },
                {
                    "src": "/icons/icon-152x152.png",
                    "sizes": "152x152",
                    "type": "image/png"
                },
                {
                    "src": "/icons/icon-192x192.png",
                    "sizes": "192x192",
                    "type": "image/png"
                },
                {
                    "src": "/icons/icon-384x384.png",
                    "sizes": "384x384",
                    "type": "image/png"
                },
                {
                    "src": "/icons/icon-512x512.png",
                    "sizes": "512x512",
                    "type": "image/png"
                }
            ],
            "shortcuts": [
                {
                    "name": "Create MVP",
                    "short_name": "Create",
                    "description": "Start creating your MVP",
                    "url": "/create",
                    "icons": [{"src": "/icons/create-96x96.png", "sizes": "96x96"}]
                },
                {
                    "name": "Templates",
                    "short_name": "Templates",
                    "description": "Browse MVP templates",
                    "url": "/templates",
                    "icons": [{"src": "/icons/templates-96x96.png", "sizes": "96x96"}]
                },
                {
                    "name": "Analytics",
                    "short_name": "Analytics",
                    "description": "View analytics dashboard",
                    "url": "/analytics",
                    "icons": [{"src": "/icons/analytics-96x96.png", "sizes": "96x96"}]
                }
            ],
            "screenshots": [
                {
                    "src": "/screenshots/desktop-1.png",
                    "sizes": "1280x720",
                    "type": "image/png",
                    "form_factor": "wide",
                    "label": "Desktop view"
                },
                {
                    "src": "/screenshots/mobile-1.png",
                    "sizes": "640x1136",
                    "type": "image/png",
                    "form_factor": "narrow",
                    "label": "Mobile view"
                }
            ]
        }
    
    def detect_device(self, request: Request) -> DeviceInfo:
        """Detect device information from request"""
        user_agent = request.headers.get("user-agent", "")
        
        # Parse user agent
        device_type = self._parse_device_type(user_agent)
        browser = self._parse_browser(user_agent)
        os = self._parse_os(user_agent)
        
        # Get screen dimensions from headers or defaults
        screen_width = int(request.headers.get("screen-width", 1024))
        screen_height = int(request.headers.get("screen-height", 768))
        pixel_ratio = float(request.headers.get("pixel-ratio", 1.0))
        
        # Determine screen size category
        screen_size = self._get_screen_size(screen_width)
        
        # Check touch support
        is_touch = "touch" in user_agent.lower() or screen_width <= 768
        
        # Check PWA support
        supports_pwa = self._supports_pwa(user_agent)
        supports_offline = supports_pwa and "service-worker" in user_agent.lower()
        
        return DeviceInfo(
            user_agent=user_agent,
            device_type=device_type,
            screen_size=screen_size,
            screen_width=screen_width,
            screen_height=screen_height,
            pixel_ratio=pixel_ratio,
            is_touch=is_touch,
            is_mobile=device_type == DeviceType.MOBILE,
            browser=browser,
            os=os,
            supports_pwa=supports_pwa,
            supports_offline=supports_offline
        )
    
    def _parse_device_type(self, user_agent: str) -> DeviceType:
        """Parse device type from user agent"""
        user_agent_lower = user_agent.lower()
        
        mobile_indicators = ["mobile", "android", "iphone", "ipod", "blackberry", "opera mini", "windows phone"]
        tablet_indicators = ["ipad", "tablet", "android 3", "android 4"]
        
        if any(indicator in user_agent_lower for indicator in mobile_indicators):
            return DeviceType.MOBILE
        elif any(indicator in user_agent_lower for indicator in tablet_indicators):
            return DeviceType.TABLET
        elif "mozilla" in user_agent_lower or "chrome" in user_agent_lower or "safari" in user_agent_lower:
            return DeviceType.DESKTOP
        
        return DeviceType.UNKNOWN
    
    def _parse_browser(self, user_agent: str) -> str:
        """Parse browser from user agent"""
        user_agent_lower = user_agent.lower()
        
        if "chrome" in user_agent_lower and "edg" not in user_agent_lower:
            return "Chrome"
        elif "firefox" in user_agent_lower:
            return "Firefox"
        elif "safari" in user_agent_lower and "chrome" not in user_agent_lower:
            return "Safari"
        elif "edg" in user_agent_lower:
            return "Edge"
        elif "opera" in user_agent_lower or "opr" in user_agent_lower:
            return "Opera"
        elif "msie" in user_agent_lower or "trident" in user_agent_lower:
            return "Internet Explorer"
        
        return "Unknown"
    
    def _parse_os(self, user_agent: str) -> str:
        """Parse operating system from user agent"""
        user_agent_lower = user_agent.lower()
        
        if "windows" in user_agent_lower:
            return "Windows"
        elif "mac os" in user_agent_lower or "macos" in user_agent_lower:
            return "macOS"
        elif "linux" in user_agent_lower:
            return "Linux"
        elif "android" in user_agent_lower:
            return "Android"
        elif "ios" in user_agent_lower or "iphone" in user_agent_lower or "ipad" in user_agent_lower:
            return "iOS"
        elif "ubuntu" in user_agent_lower:
            return "Ubuntu"
        
        return "Unknown"
    
    def _get_screen_size(self, width: int) -> ScreenSize:
        """Get screen size category from width"""
        if width < self.responsive_config.breakpoints["sm"]:
            return ScreenSize.XS
        elif width < self.responsive_config.breakpoints["md"]:
            return ScreenSize.SM
        elif width < self.responsive_config.breakpoints["lg"]:
            return ScreenSize.MD
        elif width < self.responsive_config.breakpoints["xl"]:
            return ScreenSize.LG
        elif width < self.responsive_config.breakpoints["xxl"]:
            return ScreenSize.XL
        else:
            return ScreenSize.XXL
    
    def _supports_pwa(self, user_agent: str) -> bool:
        """Check if browser supports PWA"""
        user_agent_lower = user_agent.lower()
        
        # Modern browsers support PWA
        if any(browser in user_agent_lower for browser in ["chrome", "firefox", "safari", "edg"]):
            return True
        
        return False
    
    def get_responsive_classes(self, device_info: DeviceInfo) -> Dict[str, str]:
        """Get responsive CSS classes for device"""
        classes = {}
        
        # Device-specific classes
        if device_info.is_mobile:
            classes["device"] = "mobile"
            classes["layout"] = "mobile-layout"
        elif device_info.device_type == DeviceType.TABLET:
            classes["device"] = "tablet"
            classes["layout"] = "tablet-layout"
        else:
            classes["device"] = "desktop"
            classes["layout"] = "desktop-layout"
        
        # Touch support
        if device_info.is_touch:
            classes["touch"] = "touch-enabled"
        else:
            classes["touch"] = "touch-disabled"
        
        # Screen size classes
        classes["screen"] = device_info.screen_size.value
        
        # Browser-specific classes
        classes["browser"] = device_info.browser.lower()
        
        # OS-specific classes
        classes["os"] = device_info.os.lower().replace(" ", "-")
        
        # PWA support
        if device_info.supports_pwa:
            classes["pwa"] = "pwa-supported"
        
        return classes
    
    def get_component_config(self, component_name: str, device_info: DeviceInfo) -> Dict[str, Any]:
        """Get component configuration for device"""
        component_configs = self.responsive_config.components.get(component_name, {})
        screen_size = device_info.screen_size.value
        
        # Get config for current screen size or fallback to smaller size
        config = component_configs.get(screen_size)
        if not config:
            # Fallback to smaller screen sizes
            size_order = ["xs", "sm", "md", "lg", "xl", "xxl"]
            size_index = size_order.index(screen_size)
            
            for i in range(size_index, -1, -1):
                fallback_size = size_order[i]
                config = component_configs.get(fallback_size)
                if config:
                    break
        
        return config or {}
    
    def generate_responsive_css(self, device_info: DeviceInfo) -> str:
        """Generate responsive CSS for device"""
        screen_size = device_info.screen_size.value
        
        # Get font sizes for current screen size
        font_sizes = self.responsive_config.font_sizes.get(screen_size, {})
        spacing = self.responsive_config.spacing.get(screen_size, {})
        
        css_rules = []
        
        # Typography
        for tag, size in font_sizes.items():
            css_rules.append(f".{tag} {{ font-size: {size}; }}")
        
        # Spacing
        css_rules.append(".container {{ padding: {spacing['padding']}; }}")
        css_rules.append(".card {{ margin: {spacing['margin']}; }}")
        css_rules.append(".grid {{ gap: {spacing['gap']}; }}")
        
        # Device-specific styles
        if device_info.is_mobile:
            css_rules.extend([
                ".navigation { position: fixed; bottom: 0; width: 100%; }",
                ".content { padding-bottom: 80px; }",
                ".sidebar { transform: translateX(-100%); transition: transform 0.3s; }",
                ".sidebar.open { transform: translateX(0); }"
            ])
        else:
            css_rules.extend([
                ".navigation { position: sticky; top: 0; }",
                ".sidebar { position: fixed; left: 0; }",
                ".content { margin-left: 280px; }"
            ])
        
        # Touch-specific styles
        if device_info.is_touch:
            css_rules.extend([
                ".button { min-height: 44px; min-width: 44px; }",
                ".link { padding: 8px; }",
                ".input { min-height: 44px; }"
            ])
        
        return "\n".join(css_rules)
    
    def generate_service_worker(self) -> str:
        """Generate service worker for PWA"""
        return '''
// Service Worker for Asmblr PWA
const CACHE_NAME = 'asmblr-v1';
const urlsToCache = [
  '/',
  '/static/css/main.css',
  '/static/js/main.js',
  '/static/icons/icon-192x192.png',
  '/offline.html'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(urlsToCache))
  );
});

self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request)
      .then(response => {
        // Cache hit - return response
        if (response) {
          return response;
        }

        return fetch(event.request).then(response => {
          // Check if valid response
          if (!response || response.status !== 200 || response.type !== 'basic') {
            return response;
          }

          // IMPORTANT: Clone the response. A response is a stream
          // and because we want the browser to consume the response
          // as well as the cache consuming the response, we need
          // to clone it so we have two streams.
          var responseToCache = response.clone();

          caches.open(CACHE_NAME)
            .then(cache => {
              cache.put(event.request, responseToCache);
            });

          return response;
        });
      })
  );
});

self.addEventListener('activate', event => {
  const cacheWhitelist = ['asmblr-v1'];
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheWhitelist.indexOf(cacheName) === -1) {
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
});
'''
    
    def generate_manifest_json(self) -> str:
        """Generate PWA manifest JSON"""
        return json.dumps(self.pwa_config, indent=2)
    
    async def render_responsive_page(self, template_name: str, request: Request, **context) -> Response:
        """Render responsive page with device-specific optimizations"""
        try:
            # Detect device
            device_info = self.detect_device(request)
            
            # Get responsive classes and config
            responsive_classes = self.get_responsive_classes(device_info)
            component_configs = {}
            
            # Generate responsive CSS
            responsive_css = self.generate_responsive_css(device_info)
            
            # Add device info to context
            context.update({
                "device_info": asdict(device_info),
                "responsive_classes": responsive_classes,
                "component_configs": component_configs,
                "responsive_css": responsive_css,
                "is_mobile": device_info.is_mobile,
                "is_tablet": device_info.device_type == DeviceType.TABLET,
                "supports_pwa": device_info.supports_pwa
            })
            
            # Render template
            response = self.templates.TemplateResponse(template_name, context)
            
            # Add PWA headers if supported
            if device_info.supports_pwa:
                response.headers["Cache-Control"] = "no-cache"
                response.headers["Service-Worker-Allowed"] = "/"
            
            return response
            
        except Exception as e:
            logger.error(f"Error rendering responsive page: {e}")
            raise

class MobileOptimizer:
    """Mobile performance optimizer"""
    
    def __init__(self):
        self.optimization_config = self._initialize_optimization_config()
    
    def _initialize_optimization_config(self) -> Dict[str, Any]:
        """Initialize optimization configuration"""
        return {
            "image_optimization": {
                "mobile_max_width": 800,
                "quality": 80,
                "format": "webp",
                "lazy_loading": True
            },
            "performance": {
                "mobile_timeout": 5000,
                "desktop_timeout": 3000,
                "max_connections": 6,
                "enable_compression": True
            },
            "offline": {
                "cache_duration": 86400,  # 24 hours
                "max_cache_size": 50 * 1024 * 1024,  # 50MB
                "offline_pages": ["/", "/templates", "/analytics"]
            }
        }
    
    def optimize_images_for_mobile(self, html_content: str, device_info: DeviceInfo) -> str:
        """Optimize images for mobile devices"""
        if not device_info.is_mobile:
            return html_content
        
        # Add responsive image attributes
        import re
        
        # Find img tags and add responsive attributes
        img_pattern = r'<img([^>]*?)>'
        
        def replace_img(match):
            img_attrs = match.group(1)
            
            # Add loading="lazy" if not present
            if 'loading=' not in img_attrs:
                img_attrs += ' loading="lazy"'
            
            # Add srcset for responsive images
            if 'src=' in img_attrs and 'srcset=' not in img_attrs:
                src_match = re.search(r'src="([^"]*)"', img_attrs)
                if src_match:
                    src = src_match.group(1)
                    # Generate srcset for different screen sizes
                    srcset = f"{src} 800w, {src}?size=medium 400w, {src}?size=small 200w"
                    img_attrs += f' srcset="{srcset}"'
            
            # Add sizes attribute
            if 'sizes=' not in img_attrs:
                img_attrs += ' sizes="(max-width: 800px) 100vw, 800px"'
            
            return f'<img{img_attrs}>'
        
        return re.sub(img_pattern, replace_img, html_content)
    
    def add_mobile_meta_tags(self, html_content: str, device_info: DeviceInfo) -> str:
        """Add mobile-specific meta tags"""
        mobile_meta = """
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <meta name="mobile-web-app-capable" content="yes">
        <meta name="apple-mobile-web-app-capable" content="yes">
        <meta name="apple-mobile-web-app-status-bar-style" content="default">
        <meta name="apple-mobile-web-app-title" content="Asmblr">
        <meta name="application-name" content="Asmblr">
        <meta name="msapplication-TileColor" content="#3B82F6">
        <meta name="theme-color" content="#3B82F6">
        """
        
        # Insert meta tags after <head>
        head_pattern = r'<head>'
        if head_pattern in html_content:
            html_content = html_content.replace(head_pattern, f'<head>{mobile_meta}')
        else:
            html_content = f'<head>{mobile_meta}</head>' + html_content
        
        return html_content
    
    def add_pwa_meta_tags(self, html_content: str, device_info: DeviceInfo) -> str:
        """Add PWA meta tags"""
        if not device_info.supports_pwa:
            return html_content
        
        pwa_meta = """
        <link rel="manifest" href="/manifest.json">
        <link rel="apple-touch-icon" sizes="180x180" href="/icons/apple-touch-icon.png">
        <link rel="icon" type="image/png" sizes="32x32" href="/icons/favicon-32x32.png">
        <link rel="icon" type="image/png" sizes="16x16" href="/icons/favicon-16x16.png">
        <link rel="mask-icon" href="/icons/safari-pinned-tab.svg" color="#3B82F6">
        <meta name="msapplication-TileImage" content="/icons/mstile-144x144.png">
        """
        
        # Insert PWA meta tags
        head_pattern = r'</head>'
        if head_pattern in html_content:
            html_content = html_content.replace(head_pattern, f'{pwa_meta}</head>')
        
        return html_content
    
    def add_touch_gestures(self, html_content: str, device_info: DeviceInfo) -> str:
        """Add touch gesture support"""
        if not device_info.is_touch:
            return html_content
        
        touch_script = """
        <script>
        // Touch gesture support
        let touchStartX = 0;
        let touchStartY = 0;
        
        document.addEventListener('touchstart', function(e) {
            touchStartX = e.touches[0].clientX;
            touchStartY = e.touches[0].clientY;
        });
        
        document.addEventListener('touchend', function(e) {
            const touchEndX = e.changedTouches[0].clientX;
            const touchEndY = e.changedTouches[0].clientY;
            
            const deltaX = touchEndX - touchStartX;
            const deltaY = touchEndY - touchStartY;
            
            // Handle swipe gestures
            if (Math.abs(deltaX) > 50) {
                // Horizontal swipe
                if (deltaX > 0) {
                    console.log('Swipe right');
                } else {
                    console.log('Swipe left');
                }
            }
            
            if (Math.abs(deltaY) > 50) {
                // Vertical swipe
                if (deltaY > 0) {
                    console.log('Swipe down');
                } else {
                    console.log('Swipe up');
                }
            }
        });
        </script>
        """
        
        # Insert touch script before </body>
        body_pattern = r'</body>'
        if body_pattern in html_content:
            html_content = html_content.replace(body_pattern, f'{touch_script}</body>')
        
        return html_content

# Global instances
responsive_manager = ResponsiveDesignManager()
mobile_optimizer = MobileOptimizer()

# API endpoints
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/mobile", tags=["mobile"])

@router.get("/manifest.json")
async def get_manifest():
    """Get PWA manifest"""
    try:
        manifest_content = responsive_manager.generate_manifest_json()
        return Response(
            content=manifest_content,
            media_type="application/json",
            headers={"Cache-Control": "public, max-age=86400"}
        )
    except Exception as e:
        logger.error(f"Error generating manifest: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/service-worker.js")
async def get_service_worker():
    """Get service worker"""
    try:
        sw_content = responsive_manager.generate_service_worker()
        return Response(
            content=sw_content,
            media_type="application/javascript",
            headers={"Cache-Control": "no-cache", "Service-Worker-Allowed": "/"}
        )
    except Exception as e:
        logger.error(f"Error generating service worker: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/device-info")
async def get_device_info(request: Request):
    """Get device information"""
    try:
        device_info = responsive_manager.detect_device(request)
        return asdict(device_info)
    except Exception as e:
        logger.error(f"Error getting device info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/responsive-config")
async def get_responsive_config(request: Request):
    """Get responsive configuration"""
    try:
        device_info = responsive_manager.detect_device(request)
        
        config = {
            "device_info": asdict(device_info),
            "responsive_classes": responsive_manager.get_responsive_classes(device_info),
            "breakpoints": responsive_manager.responsive_config.breakpoints,
            "component_configs": {
                name: responsive_manager.get_component_config(name, device_info)
                for name in responsive_manager.responsive_config.components.keys()
            }
        }
        
        return config
    except Exception as e:
        logger.error(f"Error getting responsive config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/optimize-content")
async def optimize_content(request: Request, content: str):
    """Optimize content for mobile"""
    try:
        device_info = responsive_manager.detect_device(request)
        
        # Apply mobile optimizations
        optimized_content = content
        optimized_content = mobile_optimizer.add_mobile_meta_tags(optimized_content, device_info)
        optimized_content = mobile_optimizer.add_pwa_meta_tags(optimized_content, device_info)
        optimized_content = mobile_optimizer.optimize_images_for_mobile(optimized_content, device_info)
        optimized_content = mobile_optimizer.add_touch_gestures(optimized_content, device_info)
        
        return {
            "optimized_content": optimized_content,
            "device_info": asdict(device_info),
            "optimizations_applied": [
                "mobile_meta_tags",
                "pwa_meta_tags" if device_info.supports_pwa else None,
                "image_optimization" if device_info.is_mobile else None,
                "touch_gestures" if device_info.is_touch else None
            ]
        }
    except Exception as e:
        logger.error(f"Error optimizing content: {e}")
        raise HTTPException(status_code=500, detail=str(e))
