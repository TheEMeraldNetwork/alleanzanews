# Company News Analysis Tool

## Overview
This tool performs automated news analysis for multiple insurance companies by fetching news from both Google News and NewsAPI. It generates a comprehensive, interactive HTML report with sentiment analysis, word clouds, and topic overlap visualization.

## Features

### News Aggregation
- **Multi-source Integration**
  - Google News API (last 6 months)
  - NewsAPI (configurable time range)
  - Automatic deduplication of articles
  - URL cleaning and normalization

### Text Analysis
- **Word Clouds**
  - Minimum word length: 5 letters
  - Excludes company names and insurance-related terms
  - Custom stop words for Italian language
  - Maximum 30 most frequent words

- **Sentiment Analysis**
  - Sentiment scoring for each article (-1 to +1)
  - Color-coded sentiment indicators
  - Aggregate sentiment analysis per company

- **Topic Analysis**
  - Interactive Venn diagram for topic overlaps
  - Top topics per company
  - Common themes identification
  - Topic frequency analysis

### Reviews Integration
- **Multiple Sources**
  - Google Reviews integration
  - Trustpilot reviews
  - Rating aggregation
  - Customer feedback analysis

### Interactive HTML Report
- **Modern UI Design**
  - Responsive layout
  - Armani-style grayscale theme
  - Mobile-friendly design
  - Interactive elements

- **Content Organization**
  - Company-specific sections
  - Latest news prioritization
  - "Show More" functionality
  - Direct links to source articles

- **Visualizations**
  - Word clouds per company
  - Topic overlap Venn diagram
  - Sentiment trend visualization
  - Review rating distribution

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

3. Download required NLTK data:
```bash
python download_nltk_data.py
```

4. Create a `.env` file with your NewsAPI key:
```
NEWS_API_KEY=your_api_key_here
```

## Configuration

### Company Settings
Configure target companies in `config.py`:
- Company names
- Name variations
- Search parameters
- Language settings

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

- `results/sentiment_report.html`: Main interactive report
- `results/wordcloud_*.png`: Word cloud visualizations
- `results/venn_diagram.png`: Topic overlap analysis
- Additional analysis files in the results directory

## Current Limitations

- NewsAPI free tier limitations (time range, request quota)
- Manual review data for demonstration
- Single language support (Italian)
- Limited sentiment analysis model

## Future Improvements

### Short-term
- [ ] Add more news sources
- [ ] Implement automated review scraping
- [ ] Enhance sentiment analysis accuracy
- [ ] Add export options (PDF, CSV)

### Medium-term
- [ ] Multi-language support
- [ ] Custom sentiment models
- [ ] Historical trend analysis
- [ ] API rate limiting optimization

### Long-term
- [ ] Machine learning classification
- [ ] Real-time updates
- [ ] Advanced NLP features
- [ ] Competitor analysis

## Technical Details

### Word Cloud Generation
- Minimum word length: 5 characters
- Excluded terms: company names, common insurance terms
- Custom stop words
- Maximum words: 30
- Font: Arial
- Resolution: 1200x600

### Venn Diagram
- Three-set visualization
- Topic frequency weighting
- Custom positioning
- Armani-style color scheme

### HTML Report
- Modern CSS Grid layout
- Responsive design
- Interactive JavaScript elements
- Custom typography

## Dependencies
```
requests==2.31.0
beautifulsoup4==4.12.2
textblob==0.17.1
feedparser==6.0.10
transformers==4.37.2
torch==2.2.0
wordcloud==1.9.3
matplotlib==3.8.2
GoogleNews==1.6.12
pillow==10.2.0
python-dotenv==1.0.1
```

## Contributing
Contributions are welcome! Please read our contributing guidelines and submit pull requests for any improvements.

## License
[Specify License]

## Contact
[Your Contact Information]

## Changelog

### Version 1.0.0 (2024-02-20)
- Initial release
- Basic news aggregation
- Sentiment analysis
- Word cloud visualization
- Interactive HTML report

### Version 1.1.0 (2024-02-20)
- Added minimum word length (5 letters) for word clouds
- Enhanced topic analysis
- Improved HTML report styling
- Added company reviews section 