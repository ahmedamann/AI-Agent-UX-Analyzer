"""
Review Scraper

This module handles collecting reviews from Google Play Store and Apple App Store
using various scraping techniques and APIs.
"""

import asyncio
from typing import List, Dict, Any, Optional
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
    
    async def get_reviews_batch(
        self,
        apps: List[Dict[str, Any]],
        limit_per_app: int = 1000
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get reviews for multiple apps in batch.
        
        Args:
            apps: List of app dictionaries with 'app_id' and 'platform' keys
            limit_per_app: Maximum number of reviews per app
            
        Returns:
            Dictionary mapping app_id to list of reviews
        """
        logger.info(f"Fetching reviews for {len(apps)} apps in batch")
        
        results = {}
        
        for app in apps:
            try:
                app_id = app['app_id']
                platform = app['platform']
                
                reviews = await self.get_reviews(app_id, platform, limit_per_app)
                results[app_id] = reviews
                
                # Rate limiting between apps
                await asyncio.sleep(self.config['rate_limiting']['delay_between_requests'])
                
            except Exception as e:
                logger.warning(f"Failed to fetch reviews for app {app.get('app_id', 'unknown')}: {e}")
                results[app.get('app_id', 'unknown')] = []
        
        return results
    
    def filter_reviews(
        self,
        reviews: List[Dict[str, Any]],
        min_rating: Optional[int] = None,
        max_rating: Optional[int] = None,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        language: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Filter reviews based on various criteria.
        
        Args:
            reviews: List of review dictionaries
            min_rating: Minimum rating (1-5)
            max_rating: Maximum rating (1-5)
            min_length: Minimum review text length
            max_length: Maximum review text length
            language: Language code to filter by
            
        Returns:
            Filtered list of reviews
        """
        filtered_reviews = []
        
        for review in reviews:
            # Rating filter
            if min_rating is not None and review.get('rating', 0) < min_rating:
                continue
            if max_rating is not None and review.get('rating', 0) > max_rating:
                continue
            
            # Length filter
            text_length = len(review.get('text', ''))
            if min_length is not None and text_length < min_length:
                continue
            if max_length is not None and text_length > max_length:
                continue
            
            # Language filter
            if language is not None and review.get('language') != language:
                continue
            
            filtered_reviews.append(review)
        
        logger.info(f"Filtered {len(reviews)} reviews to {len(filtered_reviews)}")
        return filtered_reviews
    
    def get_review_statistics(self, reviews: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate statistics for a list of reviews.
        
        Args:
            reviews: List of review dictionaries
            
        Returns:
            Dictionary containing review statistics
        """
        if not reviews:
            return {
                'total_reviews': 0,
                'average_rating': 0,
                'rating_distribution': {},
                'average_length': 0,
                'language_distribution': {}
            }
        
        # Calculate statistics
        total_reviews = len(reviews)
        ratings = [review.get('rating', 0) for review in reviews]
        average_rating = sum(ratings) / len(ratings) if ratings else 0
        
        # Rating distribution
        rating_distribution = {}
        for rating in range(1, 6):
            rating_distribution[rating] = ratings.count(rating)
        
        # Average text length
        text_lengths = [len(review.get('text', '')) for review in reviews]
        average_length = sum(text_lengths) / len(text_lengths) if text_lengths else 0
        
        # Language distribution
        language_distribution = {}
        for review in reviews:
            lang = review.get('language', 'unknown')
            language_distribution[lang] = language_distribution.get(lang, 0) + 1
        
        return {
            'total_reviews': total_reviews,
            'average_rating': round(average_rating, 2),
            'rating_distribution': rating_distribution,
            'average_length': round(average_length, 2),
            'language_distribution': language_distribution
        } 