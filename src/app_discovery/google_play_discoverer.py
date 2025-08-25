"""
Google Play Store App Discoverer

This module handles discovering apps in specific categories on Google Play Store
using the Google Play Console API and web scraping techniques.
"""

import asyncio
import aiohttp
from typing import List, Dict, Any, Optional
from loguru import logger

try:
    from google_play_scraper import search, app
    GOOGLE_PLAY_SCRAPER_AVAILABLE = True
except ImportError:
    GOOGLE_PLAY_SCRAPER_AVAILABLE = False
    logger.error("google-play-scraper not available - required for Google Play discovery")


class GooglePlayDiscoverer:
    """
    Discovers apps in Google Play Store categories.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the Google Play discoverer.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.country = config['app_stores']['google_play']['country']
        self.language = config['app_stores']['google_play']['language']
        self.max_apps = config['app_stores']['google_play']['max_apps_per_category']
        
        # Rate limiting
        self.requests_per_minute = config['rate_limiting']['requests_per_minute']
        self.delay_between_requests = config['rate_limiting']['delay_between_requests']
        
        logger.debug("Google Play Discoverer initialized")
    
    async def discover_apps(
        self,
        category: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Discover apps in a specific category.
        
        Args:
            category: App category to search
            limit: Maximum number of apps to discover
            
        Returns:
            List of app dictionaries
        """
        logger.debug(f"Discovering Google Play apps in category: {category}")
        
        try:
            # Get category keywords
            keywords = self._get_category_keywords(category)
            
            apps = []
            for keyword in keywords:
                if len(apps) >= limit:
                    break
                
                try:
                    keyword_apps = await self._search_apps_by_keyword(keyword, limit - len(apps))
                    apps.extend(keyword_apps)
                    
                    # Rate limiting
                    await asyncio.sleep(self.delay_between_requests)
                    
                except Exception as e:
                    logger.warning(f"Failed to search for keyword '{keyword}': {e}")
                    continue
            
            # Remove duplicates and limit results
            unique_apps = self._remove_duplicates(apps)
            return unique_apps[:limit]
            
        except Exception as e:
            logger.error(f"Failed to discover Google Play apps: {str(e)}")
            raise
    
    async def _search_apps_by_keyword(
        self,
        keyword: str,
        limit: int
    ) -> List[Dict[str, Any]]:
        """
        Search for apps using a specific keyword.
        
        Args:
            keyword: Search keyword
            limit: Maximum number of apps to return
            
        Returns:
            List of app dictionaries
        """
        if not GOOGLE_PLAY_SCRAPER_AVAILABLE:
            raise ImportError("google-play-scraper is required but not available")
        
        try:
            results = await asyncio.to_thread(
                search,
                keyword,
                lang=self.language,
                country=self.country,
                n_hits=limit
            )
            
            apps = []
            for result in results:
                app_data = {
                    'app_id': result['appId'],
                    'name': result['title'],
                    'developer': result['developer'],
                    'rating': result.get('score', 0),
                    'rating_count': result.get('reviews', 0),
                    'category': result.get('genre', ''),
                    'platform': 'google_play',
                    'url': f"https://play.google.com/store/apps/details?id={result['appId']}"
                }
                apps.append(app_data)
            
            return apps
                
        except Exception as e:
            logger.error(f"Failed to search apps by keyword '{keyword}': {str(e)}")
            raise
    

    
    def _get_category_keywords(self, category: str) -> List[str]:
        """
        Get keywords for a specific category.
        
        Args:
            category: Category name
            
        Returns:
            List of keywords
        """
        categories_config = self.config.get('categories', {})
        category_config = categories_config.get(category, {})
        keywords = category_config.get('keywords', [category])
        
        # Add category name itself as a keyword
        if category not in keywords:
            keywords.insert(0, category)
        
        return keywords
    
    def _remove_duplicates(self, apps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Remove duplicate apps based on app_id.
        
        Args:
            apps: List of app dictionaries
            
        Returns:
            List of unique apps
        """
        seen = set()
        unique_apps = []
        
        for app in apps:
            app_id = app.get('app_id')
            if app_id and app_id not in seen:
                seen.add(app_id)
                unique_apps.append(app)
        
        return unique_apps
    
    async def get_app_details(self, app_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific app.
        
        Args:
            app_id: Google Play app ID
            
        Returns:
            App details dictionary or None if not found
        """
        try:
            if 'google_play_scraper' in globals():
                app_info = app(app_id, lang=self.language, country=self.country)
                
                return {
                    'app_id': app_info['appId'],
                    'name': app_info['title'],
                    'developer': app_info['developer'],
                    'rating': app_info.get('score', 0),
                    'rating_count': app_info.get('reviews', 0),
                    'category': app_info.get('genre', ''),
                    'description': app_info.get('description', ''),
                    'platform': 'google_play',
                    'url': f"https://play.google.com/store/apps/details?id={app_id}"
                }
            else:
                logger.warning("google-play-scraper not available for detailed app info")
                return None
                
        except Exception as e:
            logger.error(f"Failed to get app details for {app_id}: {str(e)}")
            return None 