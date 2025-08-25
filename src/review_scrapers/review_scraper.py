"""
Review Scraper

This module handles collecting reviews from Google Play Store and Apple App Store
using various scraping techniques and APIs.
"""

import asyncio
from typing import List, Dict, Any
from loguru import logger

from .google_play_review_scraper import GooglePlayReviewScraper


class ReviewScraper:
    """
    Main class for scraping reviews from app stores.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the review scraper with configuration.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.google_play_scraper = GooglePlayReviewScraper(config)
        
        logger.debug("Review Scraper initialized")
    
    async def get_reviews(
        self,
        app_id: str,
        platform: str,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Get reviews for a specific app.
        
        Args:
            app_id: App identifier
            platform: Platform the app is on ('google_play' or 'app_store')
            limit: Maximum number of reviews to fetch
            
        Returns:
            List of review dictionaries
        """
        logger.info(f"Fetching reviews for app {app_id} on {platform}")
        
        try:
            if platform == 'google_play':
                reviews = await self.google_play_scraper.get_reviews(app_id, limit)
            else:
                raise ValueError(f"Unsupported platform: {platform}. Only 'google_play' is supported.")
            
            logger.info(f"Fetched {len(reviews)} reviews from {platform}")
            return reviews
            
        except Exception as e:
            logger.error(f"Failed to fetch reviews from {platform}: {str(e)}")
            raise 