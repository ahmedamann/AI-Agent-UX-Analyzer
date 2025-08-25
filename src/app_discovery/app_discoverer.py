"""
App Discoverer

This module handles discovering apps in specific categories across
Google Play Store and Apple App Store.
"""

import asyncio
from typing import List, Dict, Any, Optional
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
    
    async def discover_apps_all_platforms(
        self,
        category: str,
        limit_per_platform: int = 50
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Discover apps in a category across all enabled platforms.
        
        Args:
            category: App category to search
            limit_per_platform: Maximum number of apps per platform
            
        Returns:
            Dictionary mapping platform names to lists of apps
        """
        results = {}
        
        # Only Google Play is supported
        platforms = ['google_play'] if self.config['app_stores']['google_play']['enabled'] else []
        
        logger.info(f"Discovering apps on platforms: {platforms}")
        
        for platform in platforms:
            try:
                apps = await self.discover_apps(category, platform, limit_per_platform)
                results[platform] = apps
            except Exception as e:
                logger.warning(f"Failed to discover apps on {platform}: {e}")
                results[platform] = []
        
        return results
    
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
    
    def get_category_subcategories(self, category: str) -> List[str]:
        """
        Get subcategories for a specific category.
        
        Args:
            category: Category name
            
        Returns:
            List of subcategories
        """
        categories_config = self.config.get('categories', {})
        category_config = categories_config.get(category, {})
        return category_config.get('subcategories', [])
    
    def validate_category(self, category: str) -> bool:
        """
        Validate if a category is supported.
        
        Args:
            category: Category name to validate
            
        Returns:
            True if category is supported, False otherwise
        """
        categories_config = self.config.get('categories', {})
        return category in categories_config
    
    def get_supported_categories(self) -> List[str]:
        """
        Get list of supported categories.
        
        Returns:
            List of supported category names
        """
        categories_config = self.config.get('categories', {})
        return list(categories_config.keys()) 