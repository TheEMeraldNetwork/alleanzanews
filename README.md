# Company News Analysis Tool

## Overview
This tool performs automated news analysis for multiple insurance companies by fetching news from both Google News and NewsAPI. It generates a comprehensive, interactive HTML report with sentiment analysis, word clouds, topic overlap visualization, and an integrated AI chatbot assistant.

## Features

### News Aggregation
- **Multi-source Integration**
  - Google News API (last 6 months)
  - NewsAPI (configurable time range)
  - Domain-specific search (e.g., vitanuova.it)
  - Automatic deduplication of articles
  - URL validation and correction

### Text Analysis
- **Word Clouds**
  - Minimum word length: 5 letters
  - Excludes company names and common terms
  - Custom stop words for Italian language
  - Maximum 30 most frequent words
  - Company-specific visualizations

- **Sentiment Analysis**
  - Sentiment scoring for each article (-1 to +1)
  - Color-coded sentiment indicators (green/red/gray)
  - Aggregate sentiment analysis per company
  - Real-time sentiment calculation

- **Topic Analysis**
  - Interactive Venn diagram for topic overlaps
  - Detailed topic breakdown by company:
    - Unique topics per company
    - Shared topics between pairs
    - Common themes across all companies
  - Topic frequency analysis
  - Minimum word length filtering

### Reviews Integration
- **Trustpilot Integration**
  - Rating aggregation
  - Review previews
  - Direct links to review pages
  - Customer feedback analysis

### Interactive HTML Report
- **Modern UI Design**
  - Responsive layout
  - Clean, professional theme
  - Mobile-friendly design
  - Interactive elements
  - Consistent section styling

- **Content Organization**
  - Company-specific sections
  - Latest news prioritization
  - Review previews with "View more" links
  - Direct links to source articles
  - Clear section separation

### AI-Powered Chatbot Assistant
- **Emerald Assistant Integration**
  - Real-time query processing
  - Context-aware responses
  - Source attribution for all information
  - Natural language interaction

- **Knowledge Base**
  - Access to all dashboard articles
  - Integration with review data
  - Company-specific information retrieval
  - Accurate source citations

- **User Interface**
  - Floating chat button
  - Clean chat window design
  - Message history
  - Loading indicators
  - Error handling
  - Mobile responsive

### Company-Specific Features
- **Alleanza Assicurazioni**
  - Ultra-strict filtering to exclude non-insurance "alleanza" mentions
  - Multiple insurance context validation
  - Company-specific term verification
  - Trustpilot reviews integration

- **Unidea Assicurazioni**
  - Insurance context validation
  - Specific term matching
  - Topic analysis

- **Vita Nuova**
  - Domain-specific search (vitanuova.it)
  - Insurance context validation
  - Strict filtering of "nuova vita" mentions

## Installation

1. Clone the repository:
```bash
git clone [repository-url]
cd [repository-name]
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file with your API keys:
```
NEWS_API_KEY=your_news_api_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here
```

## Usage

### Running the Dashboard
```bash
python company_news_analysis.py
```

### Starting the Chatbot Server
```bash
python app.py
```

Then open your browser and navigate to:
```
http://localhost:5000
```

## Configuration

### Company Settings (`config.py`)
- Company names and variations
- Search parameters
- Language settings
- Insurance-related terms

### API Settings
- NewsAPI configuration
- Google News parameters
- Review sources setup
- Rate limiting settings

## Dependencies
See `requirements.txt` for the complete list of dependencies.

## Project Structure
```
├── app.py                    # Flask server for chatbot
├── company_news_analysis.py  # Main analysis script
├── emerald_rag.py           # Chatbot assistant implementation
├── config.py                # Configuration settings
├── requirements.txt         # Python dependencies
├── .env                     # API keys and environment variables
├── sentiment_report.html    # Generated dashboard
├── validate_articles.py     # Article validation and title normalization
└── README.md               # Documentation
```

## Changelog

### Version 1.2.2 (2024-02-23)
- Added article validation script with improved title normalization:
  - Enhanced handling of accented characters
  - Better handling of ellipsis and subtitles
  - Improved duplicate detection
- Updated sentiment report with validated articles
- Added new logo assets and styling improvements
- Created backup checkpoint (20250223_1021)

### Version 1.2.1 (2024-02-23)
- Improved Cross-Analysis section UI:
  - Removed black backgrounds for better readability
  - Consistent styling between Topics Overlap and Topics by Company
  - Enhanced construction banner design
  - Optimized Venn diagram sizing
  - Better mobile responsiveness
- General UI improvements:
  - Cleaner white backgrounds throughout
  - More consistent section styling
  - Enhanced typography and spacing

### Version 1.2.0 (2024-02-22)
- Added AI-powered Emerald Assistant chatbot
  - Real-time query processing
  - Source attribution system
  - Integration with dashboard data
  - Modern chat interface
- Enhanced topic analysis filtering
- Improved URL validation system
- Added checkpoint system for backups

### Version 1.1.2 (2024-02-21)
- Improved topic analysis filtering
- Enhanced Venn diagram readability
- Fixed duplicate article handling
- Added URL validation system

### Version 1.1.1 (2024-02-20)
- Enhanced review section
- Improved URL validation
- Added backup system

### Version 1.1.0 (2024-02-19)
- Added Vita Nuova section
- Enhanced topic analysis
- Improved HTML report styling

### Version 1.0.0 (2024-02-18)
- Initial release
- Basic news aggregation
- Sentiment analysis
- Word cloud visualization

## Contributing
Contributions are welcome! Please read our contributing guidelines and submit pull requests for any improvements.

## License
[Specify License] 