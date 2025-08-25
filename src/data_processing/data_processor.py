"""
Data Processor

This module handles cleaning, preprocessing, and structuring review data
for analysis and clustering.
"""

import re
import pandas as pd
from typing import List, Dict, Any
from loguru import logger

try:
    import nltk
    from nltk.corpus import stopwords
    from nltk.tokenize import word_tokenize
    from nltk.stem import WordNetLemmatizer
    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False
    logger.warning("NLTK not available, using basic text processing")


class DataProcessor:
    """
    Main class for processing and cleaning review data.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the data processor with configuration.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.processing_config = config.get('data_processing', {})
        
        # Initialize NLTK components if available
        if NLTK_AVAILABLE:
            self._initialize_nltk()
        
        logger.debug("Data Processor initialized")
    
    def _initialize_nltk(self):
        """Initialize NLTK components."""
        try:
            # Download required NLTK data
            nltk.download('punkt', quiet=True)
            nltk.download('stopwords', quiet=True)
            nltk.download('wordnet', quiet=True)
            nltk.download('averaged_perceptron_tagger', quiet=True)
            
            self.stop_words = set(stopwords.words('english'))
            self.lemmatizer = WordNetLemmatizer()
            
        except Exception as e:
            logger.warning(f"Failed to initialize NLTK: {e}")
            NLTK_AVAILABLE = False
    
    def process_reviews(self, reviews: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Process a list of reviews through the complete pipeline.
        
        Args:
            reviews: List of review dictionaries
            
        Returns:
            Dictionary containing processed data and metadata
        """
        logger.info(f"Processing {len(reviews)} reviews")
        
        try:
            # Step 1: Clean and validate reviews
            cleaned_reviews = self.clean_reviews(reviews)
            
            # Step 2: Extract features
            processed_reviews = self.extract_features(cleaned_reviews)
            
            # Step 3: Create structured data
            structured_data = self.create_structured_data(processed_reviews)
            
            return {
                'reviews': processed_reviews,
                'structured_data': structured_data,
                'processing_config': self.processing_config
            }
            
        except Exception as e:
            logger.error(f"Failed to process reviews: {str(e)}")
            raise
    
    def clean_reviews(self, reviews: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Clean and validate review data.
        
        Args:
            reviews: List of review dictionaries
            
        Returns:
            List of cleaned review dictionaries
        """
        cleaned_reviews = []
        
        min_length = self.processing_config.get('min_review_length', 20)
        max_length = self.processing_config.get('max_review_length', 1000)
        min_word_count = self.processing_config.get('min_word_count', 3)
        
        for review in reviews:
            try:
                # Extract text
                text = review.get('text', '').strip()
                
                # Skip if text is too short or too long
                if len(text) < min_length or len(text) > max_length:
                    continue
                
                # Clean text
                cleaned_text = self.clean_text(text)
                
                # Check word count after cleaning
                word_count = len(cleaned_text.split())
                if word_count < min_word_count:
                    continue
                
                if len(cleaned_text) < min_length:
                    continue
                
                # Create cleaned review
                cleaned_review = review.copy()
                cleaned_review['text'] = cleaned_text
                cleaned_review['text_length'] = len(cleaned_text)
                cleaned_review['word_count'] = len(cleaned_text.split())
                
                cleaned_reviews.append(cleaned_review)
                
            except Exception as e:
                logger.warning(f"Failed to clean review: {e}")
                continue
        
        logger.info(f"Cleaned {len(reviews)} reviews to {len(cleaned_reviews)}")
        return cleaned_reviews
    
    def clean_text(self, text: str) -> str:
        """
        Clean and normalize text.
        
        Args:
            text: Raw text to clean
            
        Returns:
            Cleaned text
        """
        # Convert to lowercase
        text = text.lower()
        
        # Remove URLs
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        
        # Remove email addresses
        text = re.sub(r'\S+@\S+', '', text)
        
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s\.\!\?\,\;\:\-\(\)]', '', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove leading/trailing whitespace
        text = text.strip()
        
        return text
    
    def extract_features(self, reviews: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extract features from cleaned reviews.
        
        Args:
            reviews: List of cleaned review dictionaries
            
        Returns:
            List of reviews with extracted features
        """
        processed_reviews = []
        
        for review in reviews:
            try:
                processed_review = review.copy()
                text = review['text']
                
                # Extract keywords (used by clustering)
                keywords = self.extract_keywords(text)
                processed_review['keywords'] = keywords
                
                processed_reviews.append(processed_review)
                
            except Exception as e:
                logger.warning(f"Failed to extract features from review: {e}")
                processed_reviews.append(review)
        
        return processed_reviews
    
    def extract_keywords(self, text: str) -> List[str]:
        """
        Extract keywords from text.
        
        Args:
            text: Text to analyze
            
        Returns:
            List of keywords
        """
        if not NLTK_AVAILABLE:
            # Simple keyword extraction
            words = text.split()
            return [word for word in words if len(word) > 3][:10]
        
        try:
            # Tokenize and lemmatize
            tokens = word_tokenize(text.lower())
            
            # Remove stop words and short words
            keywords = []
            for token in tokens:
                if (token not in self.stop_words and 
                    len(token) > 3 and 
                    token.isalpha()):
                    lemmatized = self.lemmatizer.lemmatize(token)
                    keywords.append(lemmatized)
            
            # Return top keywords
            return keywords[:10]
            
        except Exception as e:
            logger.warning(f"Failed to extract keywords: {e}")
            return []
    
    def create_structured_data(self, reviews: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create structured data for analysis.
        
        Args:
            reviews: List of processed reviews
            
        Returns:
            Dictionary containing structured data
        """
        # Convert to DataFrame for easier analysis
        df = pd.DataFrame(reviews)
        
        # Create text corpus
        texts = [review['text'] for review in reviews]
        
        return {
            'dataframe': df,
            'texts': texts,
            'total_reviews': len(reviews)
        } 