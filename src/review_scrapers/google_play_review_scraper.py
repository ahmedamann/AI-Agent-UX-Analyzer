"""
Google Play Store Review Scraper

This module handles collecting reviews from Google Play Store
using various scraping techniques and APIs.
"""

import asyncio
from typing import List, Dict, Any, Optional
from loguru import logger

try:
    import google_play_scraper
    GOOGLE_PLAY_SCRAPER_AVAILABLE = True
except ImportError:
    GOOGLE_PLAY_SCRAPER_AVAILABLE = False
    logger.error("google-play-scraper not available - required for Google Play review scraping")


class GooglePlayReviewScraper:
    """
    Scrapes reviews from Google Play Store.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the Google Play review scraper.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.country = config['app_stores']['google_play']['country']
        self.language = config['app_stores']['google_play']['language']
        self.max_reviews = config['app_stores']['google_play']['max_reviews_per_app']
        
        # Rate limiting
        self.requests_per_minute = config['rate_limiting']['requests_per_minute']
        self.delay_between_requests = config['rate_limiting']['delay_between_requests']
        
        logger.debug("Google Play Review Scraper initialized")
    
    async def get_reviews(
        self,
        app_id: str,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Get reviews for a specific app.
        
        Args:
            app_id: Google Play app ID
            limit: Maximum number of reviews to fetch
            
        Returns:
            List of review dictionaries
        """
        logger.info(f"Fetching Google Play reviews for app: {app_id}")
        
        if not GOOGLE_PLAY_SCRAPER_AVAILABLE:
            raise ImportError("google-play-scraper is required but not available")
        
        try:
            return await self._scrape_with_library(app_id, limit)
                
        except Exception as e:
            logger.error(f"Failed to fetch Google Play reviews for {app_id}: {str(e)}")
            raise
    
    async def _scrape_with_library(
        self,
        app_id: str,
        limit: int
    ) -> List[Dict[str, Any]]:
        """
        Scrape reviews using the google-play-scraper library.
        
        Args:
            app_id: Google Play app ID
            limit: Maximum number of reviews to fetch
            
        Returns:
            List of review dictionaries
        """
        try:
            # Use the library to fetch reviews
            review_results, _ = google_play_scraper.reviews(
                app_id,
                lang=self.language,
                country=self.country,
                count=limit
            )
            
            # Convert to our standard format
            review_list = []
            for review in review_results:
                review_data = {
                    'review_id': review.get('reviewId', ''),
                    'text': review.get('content', ''),
                    'rating': review.get('score', 0),
                    'author': review.get('userName', ''),
                    'date': review.get('at', ''),
                    'platform': 'google_play',
                    'app_id': app_id,
                    'helpful_count': review.get('thumbsUpCount', 0),
                    'reply_text': review.get('replyContent', ''),
                    'reply_date': review.get('repliedAt', '')
                }
                review_list.append(review_data)
            
            logger.info(f"Fetched {len(review_list)} reviews using library")
            return review_list
            
        except Exception as e:
            logger.error(f"Library scraping failed: {e}")
            raise
    

    
    async def get_reviews_batch(
        self,
        app_ids: List[str],
        limit_per_app: int = 1000
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get reviews for multiple apps in batch.
        
        Args:
            app_ids: List of app IDs
            limit_per_app: Maximum reviews per app
            
        Returns:
            Dictionary mapping app_id to list of reviews
        """
        logger.info(f"Fetching reviews for {len(app_ids)} apps in batch")
        
        results = {}
        
        for app_id in app_ids:
            try:
                reviews = await self.get_reviews(app_id, limit_per_app)
                results[app_id] = reviews
                
                # Rate limiting between apps
                await asyncio.sleep(self.delay_between_requests)
                
            except Exception as e:
                logger.warning(f"Failed to fetch reviews for app {app_id}: {e}")
                results[app_id] = []
        
        return results
    
    def filter_reviews(
        self,
        reviews: List[Dict[str, Any]],
        min_rating: Optional[int] = None,
        max_rating: Optional[int] = None,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Filter reviews based on various criteria.
        
        Args:
            reviews: List of review dictionaries
            min_rating: Minimum rating (1-5)
            max_rating: Maximum rating (1-5)
            min_length: Minimum review text length
            max_length: Maximum review text length
            
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
                'helpful_reviews': 0
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
        
        # Helpful reviews (reviews with replies or high helpful count)
        helpful_reviews = sum(1 for review in reviews if review.get('helpful_count', 0) > 5 or review.get('reply_text'))
        
        return {
            'total_reviews': total_reviews,
            'average_rating': round(average_rating, 2),
            'rating_distribution': rating_distribution,
            'average_length': round(average_length, 2),
            'helpful_reviews': helpful_reviews
        } 