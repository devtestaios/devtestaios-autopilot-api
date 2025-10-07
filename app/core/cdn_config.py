"""
CDN configuration and static asset optimization
"""

import os
from typing import Dict, List, Optional
from datetime import datetime, timedelta

class CDNManager:
    def __init__(self):
        self.cdn_enabled = os.getenv('CDN_ENABLED', 'false').lower() == 'true'
        self.cdn_base_url = os.getenv('CDN_BASE_URL', '')
        self.static_assets = self._define_static_assets()
        
    def _define_static_assets(self) -> Dict[str, Dict[str, any]]:
        """Define static assets and their CDN configuration"""
        return {
            "images": {
                "extensions": [".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"],
                "cache_duration": 2592000,  # 30 days
                "compression": True,
                "path_prefix": "/static/images/"
            },
            "css": {
                "extensions": [".css"],
                "cache_duration": 604800,   # 7 days
                "compression": True,
                "minification": True,
                "path_prefix": "/static/css/"
            },
            "javascript": {
                "extensions": [".js"],
                "cache_duration": 604800,   # 7 days
                "compression": True,
                "minification": True,
                "path_prefix": "/static/js/"
            },
            "fonts": {
                "extensions": [".woff", ".woff2", ".ttf", ".eot"],
                "cache_duration": 7776000,  # 90 days
                "compression": False,
                "path_prefix": "/static/fonts/"
            },
            "documents": {
                "extensions": [".pdf", ".doc", ".docx"],
                "cache_duration": 86400,    # 1 day
                "compression": True,
                "path_prefix": "/static/docs/"
            }
        }
    
    def get_asset_url(self, asset_path: str) -> str:
        """Get CDN URL for asset or fallback to local"""
        if not self.cdn_enabled or not self.cdn_base_url:
            return asset_path
        
        # Remove leading slash for CDN URL construction
        clean_path = asset_path.lstrip('/')
        return f"{self.cdn_base_url}/{clean_path}"
    
    def get_cache_headers(self, file_extension: str) -> Dict[str, str]:
        """Get appropriate cache headers for file type"""
        for asset_type, config in self.static_assets.items():
            if file_extension.lower() in config["extensions"]:
                return {
                    "Cache-Control": f"public, max-age={config['cache_duration']}",
                    "Expires": (datetime.utcnow() + timedelta(seconds=config['cache_duration'])).strftime('%a, %d %b %Y %H:%M:%S GMT'),
                    "ETag": f'"{hash(file_extension + str(datetime.utcnow().date()))}"'
                }
        
        # Default cache headers for unknown file types
        return {
            "Cache-Control": "public, max-age=3600",  # 1 hour
            "Expires": (datetime.utcnow() + timedelta(hours=1)).strftime('%a, %d %b %Y %H:%M:%S GMT')
        }
    
    def should_compress(self, file_extension: str) -> bool:
        """Check if file type should be compressed"""
        for asset_type, config in self.static_assets.items():
            if file_extension.lower() in config["extensions"]:
                return config.get("compression", False)
        return False
    
    def get_optimization_recommendations(self) -> List[Dict[str, any]]:
        """Get CDN and asset optimization recommendations"""
        recommendations = []
        
        if not self.cdn_enabled:
            recommendations.append({
                "type": "CDN Setup",
                "priority": "high",
                "title": "Enable CDN for Static Assets",
                "description": "Configure CDN to improve global performance and reduce server load",
                "benefits": [
                    "Reduced latency for global users",
                    "Lower bandwidth costs",
                    "Improved page load times",
                    "Better SEO performance"
                ],
                "implementation": [
                    "Set up CloudFront or similar CDN",
                    "Configure DNS for CDN domain",
                    "Update asset URLs to use CDN",
                    "Set up cache invalidation"
                ]
            })
        
        recommendations.extend([
            {
                "type": "Image Optimization",
                "priority": "medium",
                "title": "Implement WebP Format",
                "description": "Convert images to WebP format for better compression",
                "benefits": ["25-35% smaller file sizes", "Better user experience"],
                "implementation": ["Set up image processing pipeline", "Add WebP fallbacks"]
            },
            {
                "type": "Asset Minification",
                "priority": "medium", 
                "title": "Minify CSS and JavaScript",
                "description": "Reduce asset sizes through minification",
                "benefits": ["Faster downloads", "Reduced bandwidth usage"],
                "implementation": ["Set up build pipeline", "Configure minification tools"]
            },
            {
                "type": "HTTP/2 Push",
                "priority": "low",
                "title": "Implement HTTP/2 Server Push",
                "description": "Push critical assets before they're requested",
                "benefits": ["Faster initial page loads", "Better user experience"],
                "implementation": ["Configure server push headers", "Identify critical assets"]
            }
        ])
        
        return recommendations
    
    def get_performance_metrics(self) -> Dict[str, any]:
        """Get CDN and asset performance metrics"""
        return {
            "cdn_enabled": self.cdn_enabled,
            "cdn_base_url": self.cdn_base_url,
            "asset_types_configured": len(self.static_assets),
            "total_cache_duration_days": sum(
                config["cache_duration"] for config in self.static_assets.values()
            ) / 86400 / len(self.static_assets),
            "compression_enabled_types": [
                asset_type for asset_type, config in self.static_assets.items()
                if config.get("compression", False)
            ],
            "optimization_score": self._calculate_optimization_score()
        }
    
    def _calculate_optimization_score(self) -> int:
        """Calculate overall optimization score (0-100)"""
        score = 0
        
        # CDN enabled: +40 points
        if self.cdn_enabled:
            score += 40
        
        # Compression enabled: +30 points
        compression_enabled = sum(
            1 for config in self.static_assets.values()
            if config.get("compression", False)
        )
        score += min(30, compression_enabled * 6)
        
        # Appropriate cache durations: +30 points
        good_cache_configs = sum(
            1 for config in self.static_assets.values()
            if config["cache_duration"] >= 86400  # At least 1 day
        )
        score += min(30, good_cache_configs * 6)
        
        return min(100, score)

# Global CDN manager
cdn_manager = CDNManager()
