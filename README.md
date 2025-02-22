# Company News Analysis Tool

## Overview
This tool performs automated news analysis for multiple insurance companies by fetching news from both Google News and NewsAPI. It generates a comprehensive, interactive HTML report with sentiment analysis, word clouds, and topic overlap visualization.

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

### RAG-Powered Assistant (Coming Soon)
- **Knowledge-Base First Approach**
  - Prioritizes dashboard's existing knowledge base
  - Sources answers from saved articles and reviews
  - Provides direct references to source materials
  - Clear distinction between local and web sources

- **Strict RAG Implementation**
  - Focused on retrieval and citation
  - No general-purpose LLM responses
  - Mandatory source attribution
  - Verifiable information only

- **Integration**
  - Emerald-styled chat interface
  - Real-time article access
  - Review data integration
  - Web search capabilities when needed

## Known Limitations and Pending Improvements

### Current Issues
1. **Review Sources**
   - Google Maps links need replacement with proper review search
   - Review source consolidation needed

2. **URL Validation**
   - Some news article URLs may be invalid
   - URL correction system being implemented
   - Enhanced validation in progress

### Planned Fixes
1. **Review System Enhancement**
   - Implementing direct Google search for reviews
   - Focusing on Trustpilot as primary review source
   - Improving review link validation

2. **URL System Improvement**
   - Adding URL correction mechanisms
   - Enhancing validation logic
   - Implementing URL testing before inclusion

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

3. Create a `.env` file with your NewsAPI key:
```
NEWS_API_KEY=your_api_key_here
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

## Usage

Run the main analysis:
```bash
python company_news_analysis.py
```

The script will:
1. Fetch news from multiple sources
2. Process and analyze articles
3. Generate visualizations
4. Create an interactive HTML report

## Output Files

- `sentiment_report.html`: Main interactive report
- `wordcloud_*.png`: Word cloud visualizations
- `venn_diagram.png`: Topic overlap analysis
- Additional analysis files in backup directories

## Dependencies
See `requirements.txt` for the complete list of dependencies.

## Contributing
Contributions are welcome! Please read our contributing guidelines and submit pull requests for any improvements.

## License
[Specify License]

## Changelog

### Version 1.2.0 (Planned)
- Adding RAG-powered Emerald Assistant
  - Knowledge base integration
  - Source attribution system
  - Web search capabilities
  - Emerald-styled chat interface

### Version 1.1.2 (2024-02-22)
- Improved topic analysis filtering
  - Removed common terms and adverbs
  - Enhanced punctuation handling
  - Better exclusion of generic business terms
- Enhanced Venn diagram readability with wrapped labels
- Implemented robust backup system with timestamped directories
- Fixed duplicate article handling in reports
- Added URL validation and master URL system
- Improved CSV-based data persistence

### Version 1.1.1 (2024-02-21)
- Removing Google Maps review links
- Implementing proper Google review search
- Enhancing URL validation system
- Improving review source handling
- Adding URL correction mechanisms

### Version 1.1.0 (2024-02-21)
- Added Vita Nuova section with domain-specific search
- Enhanced topic analysis with detailed breakdowns
- Improved review section with preview and links
- Added backup system with timestamps
- Updated filtering logic for all companies
- Enhanced HTML report styling and organization

### Version 1.0.0 (2024-02-20)
- Initial release
- Basic news aggregation
- Sentiment analysis
- Word cloud visualization
- Interactive HTML report 