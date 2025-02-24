# Company News Analysis Tool

## Overview
This tool performs automated news analysis for multiple insurance companies by fetching news from both Google News and NewsAPI. It generates a comprehensive, interactive HTML report with sentiment analysis, word clouds, topic overlap visualization, and an integrated AI chatbot assistant.

View the live dashboard: [Interstellar Company Radar](https://theemeraldnetwork.github.io/interstellar/sentiment_report.html)

## Features

### News Aggregation
- **Multi-source Integration**
  - Google News API (last 6 months)
  - NewsAPI (configurable time range)
  - Domain-specific search (e.g., vitanuova.it)
  - Automatic deduplication of articles
  - URL validation and correction
  - CSV-based article validation system
  - Title normalization for accurate duplicate detection

### Text Analysis
- **Word Clouds**
  - Generated from validated unique articles
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
  - 9 validated unique articles

- **Unidea Assicurazioni**
  - Insurance context validation
  - Specific term matching
  - Topic analysis
  - 6 validated unique articles

- **Vita Nuova**
  - Domain-specific search (vitanuova.it)
  - Insurance context validation
  - Strict filtering of "nuova vita" mentions
  - 2 validated unique articles

## Article Validation Workflow
1. **CSV Management**
   - Articles stored in `url_analysis.csv`
   - Each article has unique ID and validation status
   - Master URL for HTML field tracks canonical URLs
   - Duplicate detection through title normalization

2. **Title Normalization**
   - Removes special characters and accents
   - Handles ellipsis variations
   - Normalizes whitespace
   - Removes subtitles after dash or pipe
   - Ensures consistent comparison

3. **Validation Process**
   - Articles marked with flag=1 are considered valid
   - Duplicates marked with flag=0 and "DUPLICATE" note
   - False positives marked with "FALSE_POSITIVE"
   - Each company has fixed number of valid articles:
     - Alleanza Assicurazioni: 9 articles
     - Unidea Assicurazioni: 6 articles
     - Vita Nuova: 2 articles

4. **HTML Report Generation**
   - Only validated articles appear in HTML
   - Word clouds generated from validated articles
   - Automatic validation script ensures consistency

## Installation

1. Clone the repository:
```bash
git clone https://github.com/TheEmeraldNetwork/interstellar.git
cd interstellar
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

### Validating Articles
```bash
python validate_articles.py
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
├── url_analysis.csv        # Master source for validated articles
└── README.md               # Documentation
```

## Changelog

### Version 1.2.4 (2024-02-24)
- Migrated repository to interstellar:
  - Updated all repository URLs and references
  - Updated HTML redirects and base URLs
  - Created backup checkpoint (20250224_1024)
  - Enhanced security by removing sensitive files
  - Updated documentation with new repository information

### Version 1.2.3 (2024-02-24)
- Enhanced article validation system:
  - Improved title normalization for better duplicate detection
  - Added "valid article and URL" flag in CSV
  - Fixed duplicate handling between articles 22 and 28
  - Updated word clouds to reflect validated articles only
  - Created backup checkpoint (20250224_0925)

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