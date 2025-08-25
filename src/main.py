"""
Main UX Analyzer Class

This module contains the main UXAnalyzer class that orchestrates the entire
analysis pipeline from app discovery to recommendation generation.
"""

import asyncio
from typing import List, Dict, Any
from loguru import logger

from .app_discovery.app_discoverer import AppDiscoverer
from .review_scrapers.review_scraper import ReviewScraper
from .data_processing.data_processor import DataProcessor
from .clustering.cluster_analyzer import ClusterAnalyzer
from .llm_analysis.llm_analyzer import LLMAnalyzer
from .config.config_manager import ConfigManager


class UXAnalyzer:
    """
    Main class for analyzing user experience across app store categories.
    
    This class orchestrates the entire pipeline:
    1. App discovery in specified categories
    2. Review scraping from app stores
    3. Data processing and cleaning
    4. Clustering analysis
    5. LLM-based recommendation generation
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the UX Analyzer with configuration.
        
        Args:
            config: Configuration dictionary containing all settings
        """
        self.config = config
        self.config_manager = ConfigManager()
        
        # Initialize components
        self.app_discoverer = AppDiscoverer(config)
        self.review_scraper = ReviewScraper(config)
        self.data_processor = DataProcessor(config)
        self.cluster_analyzer = ClusterAnalyzer(config)
        self.llm_analyzer = LLMAnalyzer(config)
        
        logger.info("UX Analyzer initialized successfully")
    
    async def analyze_category(
        self,
        category: str,
        platforms: List[str] = None,
        max_apps: int = 50,
        max_reviews_per_app: int = 1000
    ) -> Dict[str, Any]:
        """
        Perform complete analysis of a category across specified platforms.
        
        Args:
            category: App category to analyze (e.g., 'travel', 'finance')
            platforms: List of platforms to analyze ('google_play', 'app_store')
            max_apps: Maximum number of apps to analyze per platform
            max_reviews_per_app: Maximum reviews to fetch per app
            
        Returns:
            Dictionary containing analysis results
        """
        if platforms is None:
            platforms = ['google_play']
        
        # Validate platforms
        if not all(p == 'google_play' for p in platforms):
            raise ValueError("Only 'google_play' platform is supported")
        
        logger.info(f"Starting analysis for category: {category}")
        logger.debug(f"Platforms: {platforms}")
        logger.debug(f"Max apps: {max_apps}")
        
        results = {
            'category': category,
            'platforms': platforms,
            'analysis_timestamp': None,
            'apps_discovered': {},
            'reviews_collected': {},
            'clusters': {},
            'recommendations': {},
            'metadata': {}
        }
        
        try:
            # Step 1: Discover apps in the category
            logger.info("Step 1: Discovering apps...")
            apps_by_platform = {}
            
            for platform in platforms:
                if self.config['app_stores'][platform]['enabled']:
                    apps = await self.discover_apps(category, platform, max_apps)
                    apps_by_platform[platform] = apps
                    results['apps_discovered'][platform] = apps
                    logger.debug(f"Discovered {len(apps)} apps on {platform}")
            
            # Step 2: Collect reviews for discovered apps
            logger.info("Step 2: Collecting reviews...")
            all_reviews = []
            
            for platform, apps in apps_by_platform.items():
                platform_reviews = []
                
                for app in apps:
                    try:
                        reviews = await self.get_app_reviews(
                            app['app_id'],
                            platform,
                            max_reviews_per_app
                        )
                        platform_reviews.extend(reviews)
                        logger.debug(f"Collected {len(reviews)} reviews for {app['name']}")
                    except Exception as e:
                        logger.warning(f"Failed to collect reviews for {app['name']}: {e}")
                
                results['reviews_collected'][platform] = platform_reviews
                all_reviews.extend(platform_reviews)
            
            # Step 3: Process and clean the data
            logger.info("Step 3: Processing data...")
            processed_data = self.data_processor.process_reviews(all_reviews)
            results['processed_data'] = processed_data
            
            # Step 4: Perform clustering analysis
            logger.info("Step 4: Performing clustering analysis...")
            clusters = self.cluster_analyzer.analyze(processed_data)
            results['clusters'] = clusters
            
            # Step 5: Generate LLM recommendations
            logger.info("Step 5: Generating recommendations...")
            recommendations = await self.llm_analyzer.generate_recommendations(
                processed_data, clusters, category
            )
            results['recommendations'] = recommendations
            
            # Add metadata
            results['analysis_timestamp'] = asyncio.get_event_loop().time()
            results['metadata'] = {
                'total_apps': sum(len(apps) for apps in apps_by_platform.values()),
                'total_reviews': len(all_reviews),
                'clusters_found': len(clusters)
            }
            
            logger.success(f"Analysis completed successfully for {category}")
            return results
            
        except Exception as e:
            logger.error(f"Analysis failed: {str(e)}")
            raise
    
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
            apps = await self.app_discoverer.discover_apps(category, platform, limit)
            logger.info(f"Discovered {len(apps)} apps")
            return apps
        except Exception as e:
            logger.error(f"App discovery failed: {str(e)}")
            raise
    
    async def get_app_reviews(
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
            reviews = await self.review_scraper.get_reviews(app_id, platform, limit)
            logger.info(f"Fetched {len(reviews)} reviews")
            return reviews
        except Exception as e:
            logger.error(f"Review fetching failed: {str(e)}")
            raise
    
 