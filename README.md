# AI Agent UX Analyzer

A Streamlit web application for analyzing user experience across Google Play Store categories by scraping reviews, clustering feedback, and generating actionable recommendations using Mistral AI.

## Features

- **Web Interface**: Beautiful Streamlit UI for easy interaction
- **App Discovery**: Find apps by category on Google Play Store
- **Review Scraping**: Collect user reviews from Google Play
- **Data Processing**: Clean, normalize, and structure review data
- **Clustering Analysis**: Group similar feedback patterns using TF-IDF and K-means
- **LLM Recommendations**: Generate actionable UX insights using Mistral AI with cited reviews
- **Cost-Efficient Analysis**: Single LLM call with representative reviews from each cluster
- **Interactive Visualizations**: Cluster analysis charts and data exploration

## Project Structure

```
AI Agent UX Analyzer/
├── src/
│   ├── app_discovery/          # Google Play app search and discovery
│   │   └── google_play_discoverer.py
│   ├── review_scrapers/        # Google Play review collection
│   │   └── google_play_review_scraper.py
│   ├── data_processing/        # Data cleaning and preprocessing
│   │   └── data_processor.py
│   ├── clustering/            # ML clustering algorithms
│   │   └── cluster_analyzer.py
│   ├── llm_analysis/          # Mistral AI integration and recommendations
│   │   └── llm_analyzer.py
│   └── config/                # Configuration management
│       └── config_manager.py
├── results/                   # Analysis results (JSON files)
├── logs/                     # Application logs
├── config.yaml               # Main configuration file
├── streamlit_app.py          # Streamlit web application
└── .gitignore               # Git ignore rules
```

## Quick Start

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/ahmedamann/AI-Agent-UX-Analyzer.git
   cd AI-Agent-UX-Analyzer
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure API Keys**:
   Edit `config.yaml` and add your Mistral AI API key:
   ```yaml
   api_keys:
     mistral:
       api_key: "your_mistral_api_key_here"
       model: "mistral-small-latest"
   ```

4. **Run the Web Application**:
   ```bash
   # Option 1: Direct streamlit command
   streamlit run streamlit_app.py
   
   # Option 2: Using the startup script
   python run_app.py
   ```

5. **Open Your Browser**:
   Navigate to `http://localhost:8501` to access the web interface

## How to Use

### 1. Launch the App
Run `streamlit run streamlit_app.py` and open your browser to the provided URL.

### 2. Configure Analysis
- **Category**: Select an app category (e.g., "travel", "gaming", "finance")
- **Max Apps**: Choose how many apps to analyze (1-10 recommended)
- **Max Reviews per App**: Set review collection limit (default: 1000)

### 3. Run Analysis
Click "🚀 Start Analysis" to begin the process:
- App discovery in the selected category
- Review collection from discovered apps
- Data processing and cleaning
- Clustering analysis
- LLM-powered insights generation

### 4. View Results
The app displays:
- **Apps Discovered**: List of found apps with ratings
- **Cluster Analysis**: Interactive visualization of feedback clusters
- **UX Insights**: AI-generated insights based on review content
- **Recommendations**: Actionable recommendations with priority levels
- **Executive Summary**: High-level findings and key takeaways

## How It Works

### 1. App Discovery
- Searches Google Play Store for apps in the specified category
- Uses `google-play-scraper` library for reliable app discovery
- Returns app IDs, names, ratings, and metadata

### 2. Review Collection
- Scrapes user reviews from Google Play Store
- Collects up to 1000 reviews per app
- Includes ratings, text, timestamps, and user info

### 3. Data Processing
- Cleans and normalizes review text
- Removes duplicates and short reviews (less than 20 characters, 3 words)
- Extracts keywords for clustering analysis

### 4. Clustering Analysis
- Uses **TF-IDF vectorization** to convert text to numerical features
- Applies **K-means clustering** with 8 clusters by default
- Identifies feedback patterns and groups similar reviews
- Calculates cluster statistics and keyword analysis

### 5. LLM Analysis
- **Smart Review Selection**: Picks representative reviews from each cluster
- **Single LLM Call**: Makes one comprehensive call to Mistral AI
- **Content-Focused**: Analyzes only review text content (no ratings)
- **Evidence-Based**: Generates insights based only on explicit review content
- **Structured Output**: Creates insights, recommendations, and executive summary

## Configuration

Edit `config.yaml` to configure:

### API Keys
```yaml
api_keys:
  mistral:
    api_key: "your_mistral_api_key_here"
    model: "mistral-small-latest"
```

### Clustering Settings
```yaml
clustering:
  algorithm: "kmeans"
  n_clusters: 8
  feature_extraction:
    method: "tfidf"
    max_features: 2000
    ngram_range: [1, 3]
```

### Data Processing
```yaml
data_processing:
  min_review_length: 20
  min_word_count: 3
  max_review_length: 1000
  remove_duplicates: true
```

## Technical Details

### Clustering Algorithm
- **Feature Extraction**: TF-IDF with 2000 features, n-gram range (1,3)
- **Clustering**: K-means with 8 clusters
- **Keyword Analysis**: Extracts common keywords from each cluster

### LLM Integration
- **Provider**: Mistral AI via LangChain wrapper
- **Model**: `mistral-small-latest` (cost-effective with good performance)
- **Content Focus**: Analyzes only review text, no rating bias
- **Evidence-Based**: Only conclusions from explicit review content

### Data Flow
1. **Input**: Category selection via web interface
2. **Discovery**: Find relevant apps on Google Play
3. **Collection**: Scrape reviews (up to 1000 per app)
4. **Processing**: Clean and structure data
5. **Clustering**: Group similar feedback patterns
6. **Analysis**: Generate insights using Mistral AI
7. **Output**: Interactive web display with visualizations

## API Requirements

- **Mistral AI API**: Requires Mistral AI API key for LLM analysis
- **Google Play Store**: Uses `google-play-scraper` library (no API key required)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request