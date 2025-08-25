import streamlit as st
import asyncio
import json
import pandas as pd
import plotly.express as px
from pathlib import Path
import time
from datetime import datetime
import sys
import os

# Add src to path for imports
sys.path.append(str(Path(__file__).parent / "src"))

from src.main import UXAnalyzer
from src.config.config_manager import ConfigManager

# Page configuration
st.set_page_config(
    page_title="AI Agent UX Analyzer",
    page_icon="📱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 1rem 0;
    }
    .info-box {
        background-color: #e3f2fd;
        border: 1px solid #2196f3;
        border-radius: 0.5rem;
        padding: 1.5rem;
        margin: 1rem 0;
        color: #1565c0;
    }
    .info-box h3 {
        color: #0d47a1;
        margin-bottom: 1rem;
    }
    .info-box p, .info-box ul, .info-box ol {
        color: #1565c0;
        line-height: 1.6;
    }
    .cluster-card {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'analyzer' not in st.session_state:
    st.session_state.analyzer = None
if 'results' not in st.session_state:
    st.session_state.results = None
if 'analysis_complete' not in st.session_state:
    st.session_state.analysis_complete = False

def initialize_analyzer():
    """Initialize the UX Analyzer."""
    try:
        config_manager = ConfigManager()
        config = config_manager.get_config()
        return UXAnalyzer(config)
    except Exception as e:
        st.error(f"Failed to initialize analyzer: {str(e)}")
        return None







def display_cluster_details(clusters_data, reviews_data):
    """Display detailed cluster information."""
    if not clusters_data or 'clusters' not in clusters_data:
        return
    
    cluster_info = clusters_data['clusters']
    cluster_labels = cluster_info.get('cluster_labels', [])
    
    if not cluster_labels:
        return
    
    # Group reviews by cluster
    reviews_by_cluster = {}
    for i, label in enumerate(cluster_labels):
        if i < len(reviews_data):
            if label not in reviews_by_cluster:
                reviews_by_cluster[label] = []
            reviews_by_cluster[label].append(reviews_data[i])
    
    # Display each cluster
    for cluster_id, cluster_reviews in reviews_by_cluster.items():
        if not cluster_reviews:
            continue
        
        # Calculate cluster statistics
        ratings = [r.get('rating', 0) for r in cluster_reviews]
        avg_rating = sum(ratings) / len(ratings) if ratings else 0
        sentiments = [r.get('sentiment', 0) for r in cluster_reviews]
        avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0
        
        with st.expander(f"Cluster {cluster_id} - {len(cluster_reviews)} reviews"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Cluster Size", len(cluster_reviews))
            with col2:
                st.metric("Avg Rating", f"{avg_rating:.2f}/5")
            
            # Show sample reviews
            st.subheader("Sample Reviews")
            sample_reviews = cluster_reviews[:10]  # Show first 10 reviews
            
            for i, review in enumerate(sample_reviews):
                rating = review.get('rating', 0)
                text = review.get('text', '')
                
                st.markdown(f"""
                **Review {i+1}** (Rating: {rating}/5)
                > {text}
                """)

def display_recommendations(recommendations_data):
    """Display LLM-generated recommendations."""
    if not recommendations_data:
        return
    
    insights = recommendations_data.get('insights', '')
    recommendations = recommendations_data.get('recommendations', '')
    summary = recommendations_data.get('summary', '')
    
    # Display insights
    if insights:
        st.subheader("🔍 Key Insights")
        st.markdown(insights)
    
    # Display recommendations
    if recommendations:
        st.subheader("💡 Recommendations")
        st.markdown(recommendations)
    
    # Display summary
    if summary:
        st.subheader("📋 Executive Summary")
        st.markdown(summary)

async def run_analysis(category, max_apps, progress_bar, status_text):
    """Run the analysis with progress tracking."""
    try:
        # Initialize analyzer if not already done
        if st.session_state.analyzer is None:
            st.session_state.analyzer = initialize_analyzer()
            if st.session_state.analyzer is None:
                return False
        
        analyzer = st.session_state.analyzer
        
        # Step 1: Discover apps
        status_text.text("🔍 Discovering apps...")
        progress_bar.progress(0.1)
        
        apps = await analyzer.discover_apps(category, platform='google_play', limit=max_apps)
        if not apps:
            st.error("No apps found for this category")
            return False
        
        # Step 2: Collect reviews
        status_text.text("📥 Collecting reviews...")
        progress_bar.progress(0.3)
        
        all_reviews = []
        for i, app in enumerate(apps):
            status_text.text(f"📥 Collecting reviews for {app['name']}...")
            reviews = await analyzer.get_app_reviews(app['app_id'], 'google_play', limit=1000)
            all_reviews.extend(reviews)
            progress_bar.progress(0.3 + (0.3 * (i + 1) / len(apps)))
        
        # Step 3: Process data
        status_text.text("🔄 Processing data...")
        progress_bar.progress(0.7)
        
        processed_data = analyzer.data_processor.process_reviews(all_reviews)
        
        # Step 4: Clustering
        status_text.text("🎯 Performing clustering analysis...")
        progress_bar.progress(0.8)
        
        clusters = analyzer.cluster_analyzer.analyze(processed_data)
        
        # Step 5: Generate recommendations
        status_text.text("🤖 Generating recommendations...")
        progress_bar.progress(0.9)
        
        recommendations = await analyzer.llm_analyzer.generate_recommendations(
            processed_data, clusters, category
        )
        
        # Complete
        status_text.text("✅ Analysis complete!")
        progress_bar.progress(1.0)
        
        # Store results
        st.session_state.results = {
            'apps': apps,
            'reviews': all_reviews,
            'processed_data': processed_data,
            'clusters': clusters,
            'recommendations': recommendations,
            'category': category,
            'timestamp': datetime.now().isoformat()
        }
        
        st.session_state.analysis_complete = True
        return True
        
    except Exception as e:
        st.error(f"Analysis failed: {str(e)}")
        return False

def main():
    # Header
    st.markdown('<h1 class="main-header">🤖 AI Agent UX Analyzer</h1>', unsafe_allow_html=True)
    st.markdown("### Analyze user experience patterns and generate actionable UX insights across Google Play Store categories")
    
    # Sidebar
    st.sidebar.title("⚙️ Configuration")
    
    # Category selection
    categories = [
        "travel", "gaming", "finance", "social", "productivity", 
        "education", "health", "entertainment", "shopping", "food"
    ]
    selected_category = st.sidebar.selectbox("Select Category", categories, index=0)
    
    # Max apps
    max_apps = st.sidebar.slider("Maximum Apps to Analyze", 1, 10, 3)
    
    # Analysis button
    if st.sidebar.button("🚀 Start Analysis", type="primary"):
        # Initialize analyzer
        if st.session_state.analyzer is None:
            st.session_state.analyzer = initialize_analyzer()
        
        if st.session_state.analyzer:
            # Create progress tracking
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Run analysis
            success = asyncio.run(run_analysis(selected_category, max_apps, progress_bar, status_text))
            
            if success:
                st.success("Analysis completed successfully!")
                time.sleep(2)
                st.rerun()
    

    
    # Main content area
    if st.session_state.analysis_complete and st.session_state.results:
        results = st.session_state.results
        
        # Overview metrics
        st.subheader("📊 Analysis Overview")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Apps Analyzed", len(results['apps']))
        with col2:
            st.metric("Total Reviews", len(results['reviews']))
        with col3:
            st.metric("Category", results['category'].title())
        with col4:
            st.metric("Analysis Date", datetime.fromisoformat(results['timestamp']).strftime("%Y-%m-%d"))
        
        # Apps discovered
        st.subheader("📱 Apps Discovered")
        apps_df = pd.DataFrame(results['apps'])
        
        # Check what columns are available and display them
        available_columns = apps_df.columns.tolist()
        
        # Display the dataframe with available columns
        display_columns = ['name', 'app_id', 'rating']
        # Add 'reviews' if it exists
        if 'reviews' in available_columns:
            display_columns.append('reviews')
        
        st.dataframe(apps_df[display_columns], use_container_width=True)
        
        # Cluster details
        if results['clusters']:
            st.subheader("🎯 Cluster Analysis")
            display_cluster_details(results['clusters'], results['reviews'])
        
        # Recommendations
        if results['recommendations']:
            st.subheader("💡 AI-Generated Insights")
            display_recommendations(results['recommendations'])
        
        # Download results
        st.subheader("💾 Download Results")
        if st.button("📥 Download Analysis Results"):
            # Create downloadable JSON
            download_data = {
                'analysis_summary': {
                    'category': results['category'],
                    'apps_analyzed': len(results['apps']),
                    'total_reviews': len(results['reviews']),
                    'timestamp': results['timestamp']
                },
                'apps': results['apps'],
                'recommendations': results['recommendations']
            }
            
            st.download_button(
                label="📄 Download JSON",
                data=json.dumps(download_data, indent=2),
                file_name=f"ux_analysis_{results['category']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
    
    else:
        # Welcome message
        st.markdown("""
        <div class="info-box">
        <h3>🎯 Welcome to AI Agent UX Analyzer!</h3>
        <p>This tool helps you analyze user experience patterns across Google Play Store categories by:</p>
        <ul>
            <li>🔍 Discovering popular apps in your chosen category</li>
            <li>📥 Collecting user reviews and feedback</li>
            <li>🎯 Clustering similar UX feedback patterns</li>
            <li>🤖 Generating AI-powered UX insights and recommendations</li>
        </ul>
        <p><strong>Focus:</strong> We analyze user experience feedback to identify common patterns, pain points, and improvement opportunities across app categories.</p>
        <p><strong>To get started:</strong></p>
        <ol>
            <li>Select a category from the sidebar</li>
            <li>Choose the number of apps to analyze</li>
            <li>Click "Start Analysis" to begin</li>
        </ol>
        </div>
        """, unsafe_allow_html=True)
        
        # Example categories
        st.subheader("📋 Popular Categories")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**Travel & Navigation**")
            st.markdown("- Booking apps\n- Maps & navigation\n- Travel planning")
        
        with col2:
            st.markdown("**Gaming**")
            st.markdown("- Mobile games\n- Puzzle games\n- Action games")
        
        with col3:
            st.markdown("**Finance**")
            st.markdown("- Banking apps\n- Investment tools\n- Budget trackers")

if __name__ == "__main__":
    main() 