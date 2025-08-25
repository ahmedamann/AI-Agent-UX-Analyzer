"""
LLM Analyzer

This module handles generating insights and recommendations using large language models
based on clustered review data and analysis results.
"""

import asyncio
from typing import List, Dict, Any
from loguru import logger

try:
    from langchain_mistralai import ChatMistralAI
    MISTRAL_AVAILABLE = True
except ImportError:
    MISTRAL_AVAILABLE = False
    logger.warning("Mistral API not available (langchain-mistralai not found)")


class LLMAnalyzer:
    """
    Main class for generating insights and recommendations using LLMs.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the LLM analyzer with configuration.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.llm_config = config.get('llm_analysis', {})
        
        # Initialize LLM clients
        self._initialize_llm_clients()
        
        logger.debug("LLM Analyzer initialized")
    
    def _initialize_llm_clients(self):
        """Initialize LLM clients based on configuration."""
        self.llm = None
        
        # Initialize Mistral client
        if MISTRAL_AVAILABLE:
            mistral_config = self.config.get('api_keys', {}).get('mistral', {})
            mistral_api_key = mistral_config.get('api_key')
            model = mistral_config.get('model', 'mistral-medium-latest')
            
            if mistral_api_key:
                # Set environment variable for LangChain
                import os
                os.environ["MISTRAL_API_KEY"] = mistral_api_key
                
                # Initialize LangChain Mistral client
                self.llm = ChatMistralAI(
                    model=model,
                    temperature=self.llm_config.get('temperature', 0.7),
                    max_tokens=self.llm_config.get('max_tokens', 2000),
                    max_retries=self.llm_config.get('max_retries', 3)
                )
                logger.debug("LangChain Mistral client initialized")
            else:
                logger.warning("Mistral API key not found in configuration")
        else:
            logger.warning("Mistral API not available")
    
    async def generate_recommendations(
        self,
        processed_data: Dict[str, Any],
        clustering_results: Dict[str, Any],
        category: str
    ) -> Dict[str, Any]:
        """
        Generate comprehensive recommendations based on analysis results.
        
        Args:
            processed_data: Processed review data
            clustering_results: Clustering analysis results
            category: App category being analyzed
            
        Returns:
            Dictionary containing recommendations and insights
        """
        logger.info("Generating LLM-based recommendations")
        
        try:
            # Extract reviews directly
            reviews = processed_data.get('reviews', [])
            total_reviews = len(reviews)
            
            # Use clustering results for better coverage
            clusters = clustering_results.get('clusters', {})
            cluster_analysis = clustering_results.get('cluster_analysis', {})
            
            # Debug logging
            logger.debug(f"Clustering results structure: {list(clustering_results.keys())}")
            logger.debug(f"Clusters structure: {list(clusters.keys()) if isinstance(clusters, dict) else 'Not a dict'}")
            logger.debug(f"Number of clusters: {len(clusters) if isinstance(clusters, dict) else 0}")
            
            # Extract the actual cluster data from the nested structure
            actual_clusters = clusters.get('clusters', {}) if isinstance(clusters, dict) else {}
            logger.debug(f"Actual clusters keys: {list(actual_clusters.keys())}")
            
            # Create comprehensive analysis data using clustering
            analysis_data = {
                'category': category,
                'total_reviews': total_reviews,
                'clusters': self._prepare_cluster_summaries(actual_clusters, reviews),
                'cluster_statistics': cluster_analysis
            }
            
            # Single comprehensive LLM call with clustering data
            comprehensive_prompt = self._create_comprehensive_analysis_prompt(analysis_data)
            comprehensive_response = await self._call_llm(comprehensive_prompt, 'comprehensive_analysis')
            
            # Parse the comprehensive response into sections
            parsed_response = self._parse_comprehensive_response(comprehensive_response)
            
            return {
                'insights': parsed_response.get('insights', ''),
                'recommendations': parsed_response.get('recommendations', ''),
                'summary': parsed_response.get('summary', ''),
                'analysis_data': analysis_data,
                'generation_timestamp': asyncio.get_event_loop().time()
            }
            
        except Exception as e:
            logger.error(f"Failed to generate recommendations: {str(e)}")
            raise
    
    async def _call_llm(self, prompt: str, task_type: str) -> str:
        """
        Call the Mistral LLM using LangChain.
        
        Args:
            prompt: Prompt to send to LLM
            task_type: Type of task (insights, recommendations, summary)
            
        Returns:
            LLM response
        """
        if not self.llm:
            raise Exception("LangChain Mistral client not initialized")
        
        try:
            # Use LangChain's invoke method with proper message format
            messages = [("human", prompt)]
            response = await asyncio.to_thread(self.llm.invoke, messages)
            return response.content
        except Exception as e:
            logger.error(f"LangChain Mistral API call failed: {e}")
            raise
    
    def _prepare_cluster_summaries(self, clusters: Dict[str, Any], all_reviews: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prepare cluster summaries with representative reviews."""
        cluster_summaries = []
        
        logger.debug(f"Preparing cluster summaries. Clusters type: {type(clusters)}")
        logger.debug(f"All reviews count: {len(all_reviews)}")
        
        # Handle the actual clustering structure from cluster_analyzer
        if isinstance(clusters, dict):
            # Direct clusters dictionary from cluster_analyzer
            for cluster_id, cluster_data in clusters.items():
                cluster_reviews = cluster_data.get('reviews', [])
                if not cluster_reviews:
                    continue
                    
                # Get representative reviews (mix of different types)
                representative_reviews = cluster_reviews[:10]  # Use first 10 reviews as representative
                
                cluster_summaries.append({
                    'id': cluster_id,
                    'size': len(cluster_reviews),
                    'representative_reviews': [
                        {
                            'text': r.get('text', '')  # Use full review text, no ratings
                        }
                        for r in representative_reviews
                    ]
                })
        else:
            # Fallback: use simple approach with first few reviews
            cluster_summaries.append({
                'id': 'cluster_0',
                'size': len(all_reviews),
                'representative_reviews': [
                    {
                        'text': r.get('text', '')  # Use full review text, no ratings
                    }
                    for r in all_reviews[:10]  # Use first 10 reviews as representative
                ]
            })
        
        return cluster_summaries
    
    def _create_comprehensive_analysis_prompt(self, analysis_data: Dict[str, Any]) -> str:
        """Create a comprehensive prompt that analyzes user feedback and generates UX insights, recommendations, and summary."""
        category = analysis_data['category']
        clusters = analysis_data['clusters']
        
        # Build user feedback information without any grouping references
        user_feedback = ""
        review_counter = 1
        for cluster in clusters:
            for review in cluster['representative_reviews']:
                user_feedback += f"Review {review_counter}: \"{review['text']}\"\n"
                review_counter += 1
        
        prompt = f"""
You are a senior UX analyst conducting a comprehensive analysis of {category} app user feedback. Analyze the following user feedback data and provide actionable UX insights.

CRITICAL INSTRUCTIONS:
- Focus on USER EXPERIENCE patterns and insights
- ONLY analyze what is explicitly stated in the provided user feedback
- DO NOT make assumptions, inferences, or conclusions beyond what users have written
- Base all insights and recommendations ONLY on the actual user feedback provided
- If feedback doesn't mention something, do not assume it exists or doesn't exist
- DO NOT mention clusters, groups, or technical analysis methods in your response

OVERALL DATA:
- App Category: {category}
- Total user reviews analyzed: {analysis_data['total_reviews']}

USER FEEDBACK DATA:
{user_feedback}

Please provide a comprehensive UX analysis in the following format:

## 💡 UX INSIGHTS
[Provide 3-5 key insights about user experience patterns, common UX issues, and positive user feedback based ONLY on what users explicitly stated. Focus on user behavior, pain points, and satisfaction drivers.]

## 🎯 UX RECOMMENDATIONS
[Provide 5-7 specific, actionable UX recommendations with priority levels (High/Medium/Low) based ONLY on the explicit user feedback. Focus on improving user experience, interface design, and user satisfaction.]

## 📋 EXECUTIVE SUMMARY
[Provide a 2-3 paragraph executive summary highlighting key UX findings and most important user experience recommendations based ONLY on the actual user feedback content.]

IMPORTANT: 
- Every insight and recommendation must be directly supported by specific quotes or statements from the provided user feedback
- Focus on user experience, interface design, and user satisfaction
- Do not mention technical analysis methods, clusters, groups, or data processing
- Do not reference "User X" or "Group Y" in your analysis
- Write in a user-centered way that focuses on what users want and need
- Present insights as general patterns and trends without technical references
"""
        return prompt
    
    def _parse_comprehensive_response(self, response: str) -> Dict[str, str]:
        """Parse the comprehensive LLM response into separate sections."""
        sections = {
            'insights': '',
            'recommendations': '',
            'summary': ''
        }
        
        # Simple parsing based on section headers
        lines = response.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            if line.startswith('## 💡 UX INSIGHTS'):
                current_section = 'insights'
            elif line.startswith('## 🎯 UX RECOMMENDATIONS'):
                current_section = 'recommendations'
            elif line.startswith('## 📋 EXECUTIVE SUMMARY'):
                current_section = 'summary'
            elif current_section and line:
                sections[current_section] += line + '\n'
        
        # If parsing failed, return the full response as insights
        if not any(sections.values()):
            sections['insights'] = response
        
        return sections