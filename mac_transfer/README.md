# Insurance News Analysis Tool

A sophisticated news analysis tool that tracks and visualizes news coverage for insurance companies, featuring semantic topic analysis, word clouds, and cross-reference analysis.

## Setup on Mac OS

1. **Python Environment Setup**
   ```bash
   # Create a virtual environment
   python3 -m venv .venv
   
   # Activate the virtual environment
   source .venv/bin/activate
   
   # Install dependencies
   pip install -r requirements.txt
   ```

2. **Required Dependencies**
   - Python 3.8+
   - All packages listed in requirements.txt
   - NLTK data will be downloaded automatically on first run

3. **Running the Tool**
   ```bash
   python simple_search.py
   ```

## Project Structure
```
insurance-news-analysis/
├── README.md
├── requirements.txt
├── simple_search.py
└── .venv/
```

## Features
- News tracking for multiple insurance companies
- Semantic topic analysis
- Interactive word clouds
- Topic overlap visualization
- Cross-reference analysis
- Armani-inspired UI design

## Output
- Generates an HTML report with:
  - News article summaries
  - Topic analysis
  - Word clouds
  - Cross-reference analysis
  - Venn diagram of topic overlaps

## Notes
- The tool searches news from the last 12 months
- Results are filtered for unique articles
- Word clouds show top 20 most frequent terms
- Topics are categorized into detailed business areas 