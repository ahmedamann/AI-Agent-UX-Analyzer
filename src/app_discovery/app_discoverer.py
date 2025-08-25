"""
App Discoverer

This module handles discovering apps in specific categories across
Google Play Store and Apple App Store.
"""

import asyncio
from typing import List, Dict, Any
from loguru import logger

from .google_play_discoverer import GooglePlayDiscoverer


class AppDiscoverer:
    """
    Main class for discovering apps in specific categories across platforms.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the app discoverer with configuration.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.google_play_discoverer = GooglePlayDiscoverer(config)
        
        logger.debug("App Discoverer initialized")
    
    async def discover_apps(
        self,
        category: str,
        platform: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Discover apps in a specific category on a specific platform.
        
        Args:
            category: App category to search
            platform: Platform to search on ('google_play' or 'app_store')
            limit: Maximum number of apps to discover
            
        Returns:
            List of app dictionaries with basic information
        """
        logger.debug(f"Discovering apps in category '{category}' on {platform}")
        
        try:
            if platform == 'google_play':
                apps = await self.google_play_discoverer.discover_apps(category, limit)
            else:
                raise ValueError(f"Unsupported platform: {platform}. Only 'google_play' is supported.")
            
            logger.debug(f"Discovered {len(apps)} apps on {platform}")
            return apps
            
        except Exception as e:
            logger.error(f"Failed to discover apps on {platform}: {str(e)}")
            raise
    
    def get_category_keywords(self, category: str) -> List[str]:
        """
        Get keywords for a specific category.
        
        Args:
            category: Category name
            
        Returns:
            List of keywords for the category
        """
        categories_config = self.config.get('categories', {})
        category_config = categories_config.get(category, {})
        return category_config.get('keywords', [category]) 