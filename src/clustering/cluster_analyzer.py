"""
Cluster Analyzer

This module handles clustering review data to identify similar feedback patterns
and group related issues or features.
"""

import numpy as np
from typing import List, Dict, Any
from loguru import logger

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.cluster import KMeans
    CLUSTERING_AVAILABLE = True
except ImportError:
    CLUSTERING_AVAILABLE = False
    logger.error("scikit-learn is required for clustering analysis!")


class ClusterAnalyzer:
    """
    Main class for clustering review data and identifying patterns.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the cluster analyzer with configuration.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.clustering_config = config.get('clustering', {})
        
        if not CLUSTERING_AVAILABLE:
            raise ImportError("scikit-learn is required for clustering analysis")
        
        logger.debug("Cluster Analyzer initialized")
    
    def analyze(self, processed_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform clustering analysis on processed review data.
        
        Args:
            processed_data: Dictionary containing processed review data
            
        Returns:
            Dictionary containing clustering results
        """
        logger.info("Starting clustering analysis")
        
        # Extract texts and features
        reviews = processed_data.get('reviews', [])
        texts = [review.get('text', '') for review in reviews]
        
        if not texts:
            raise ValueError("No text data available for clustering")
        
        # Step 1: Feature extraction
        features = self._extract_features(texts)
        
        # Step 2: Perform clustering
        clusters = self._perform_clustering(features, texts, reviews)
        
        # Step 3: Analyze clusters
        cluster_analysis = self._analyze_clusters(clusters, reviews)
        
        return {
            'clusters': clusters,
            'cluster_analysis': cluster_analysis,
            'features': features,
            'clustering_config': self.clustering_config
        }
    
    def _extract_features(self, texts: List[str]) -> Dict[str, Any]:
        """
        Extract features from text data for clustering.
        
        Args:
            texts: List of text strings
            
        Returns:
            Dictionary containing extracted features
        """
        feature_config = self.clustering_config.get('feature_extraction', {})
        max_features = feature_config.get('max_features', 1500)
        ngram_range = tuple(feature_config.get('ngram_range', [1, 3]))
        
        vectorizer = TfidfVectorizer(
            max_features=max_features,
            ngram_range=ngram_range,
            stop_words='english',
            min_df=2,
            max_df=0.95
        )
        
        feature_matrix = vectorizer.fit_transform(texts)
        feature_names = vectorizer.get_feature_names_out()
        
        return {
            'matrix': feature_matrix,
            'feature_names': feature_names,
            'vectorizer': vectorizer,
            'method': 'tfidf'
        }
    
    def _perform_clustering(
        self,
        features: Dict[str, Any],
        texts: List[str],
        reviews: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Perform clustering on the extracted features using K-means.
        
        Args:
            features: Dictionary containing extracted features
            texts: List of text strings
            reviews: List of review dictionaries
            
        Returns:
            Dictionary containing clustering results
        """
        n_clusters = self.clustering_config.get('n_clusters', 8)
        feature_matrix = features['matrix']
        
        # Convert sparse matrix to dense for K-means
        if hasattr(feature_matrix, 'toarray'):
            feature_matrix_dense = feature_matrix.toarray()
        else:
            feature_matrix_dense = feature_matrix
        
        # Perform K-means clustering
        kmeans = KMeans(
            n_clusters=n_clusters,
            random_state=42,
            n_init=10
        )
        cluster_labels = kmeans.fit_predict(feature_matrix_dense)
        
        # Create cluster results
        clusters = {}
        unique_labels = set(cluster_labels)
        
        for label in unique_labels:
            cluster_indices = np.where(cluster_labels == label)[0]
            cluster_reviews = [reviews[idx] for idx in cluster_indices]
            cluster_texts = [texts[idx] for idx in cluster_indices]
            
            clusters[f'cluster_{label}'] = {
                'id': label,
                'size': len(cluster_indices),
                'reviews': cluster_reviews,
                'texts': cluster_texts,
                'indices': cluster_indices.tolist()
            }
        
        logger.info(f"K-means found {len(clusters)} clusters")
        
        return {
            'algorithm': 'kmeans',
            'n_clusters': len(clusters),
            'cluster_labels': cluster_labels.tolist(),
            'clusters': clusters,
            'model': kmeans
        }
    
    def _analyze_clusters(
        self,
        clustering_results: Dict[str, Any],
        reviews: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze the clustering results.
        
        Args:
            clustering_results: Results from clustering
            reviews: List of review dictionaries
            
        Returns:
            Dictionary containing cluster analysis
        """
        clusters = clustering_results.get('clusters', {})
        
        analysis = {
            'total_clusters': len(clusters),
            'cluster_sizes': [],
            'cluster_keywords': {}
        }
        
        for cluster_id, cluster_data in clusters.items():
            cluster_reviews = cluster_data.get('reviews', [])
            
            # Cluster size
            analysis['cluster_sizes'].append(len(cluster_reviews))
            
            # Common keywords
            all_keywords = []
            for review in cluster_reviews:
                keywords = review.get('keywords', [])
                all_keywords.extend(keywords)
            
            from collections import Counter
            keyword_counts = Counter(all_keywords)
            analysis['cluster_keywords'][cluster_id] = dict(keyword_counts.most_common(10))
        
        return analysis 