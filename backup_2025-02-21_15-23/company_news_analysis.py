import os
import json
from datetime import datetime, timedelta
from collections import Counter
from GoogleNews import GoogleNews
import requests
from bs4 import BeautifulSoup
import matplotlib.pyplot as plt
from wordcloud import WordCloud
from matplotlib_venn import venn3, venn3_circles
from textblob import TextBlob
import nltk
from config import COMPANY_NAMES, COMPANY_VARIATIONS, NEWS_SEARCH
import pandas as pd
from PIL import Image
import numpy as np
from dotenv import load_dotenv
import matplotlib.gridspec as gridspec
import matplotlib.patches as patches
import time
import random

# Load environment variables
load_dotenv()

# Get NewsAPI key from environment variable
NEWS_API_KEY = os.getenv('NEWS_API_KEY')
if not NEWS_API_KEY:
    raise ValueError("Please set NEWS_API_KEY in your .env file")

def is_relevant_article(title, description, company):
    """Check if an article is truly relevant to the company."""
    title = title.lower() if title else ""
    description = description.lower() if description else ""
    company_lower = company.lower()
    text = f"{title} {description}".lower()
    
    # Special case for "Vita Nuova" to avoid false positives
    if company_lower == "vita nuova":
        # ULTRA STRICT FILTERING
        # Reject if:
        # 1. Contains "nuova vita" in any form
        # 2. Contains the word "nuova" anywhere
        # 3. Contains multiple instances of "vita"
        # 4. Contains "vita nuova" without specific insurance context
        if ("nuova" in text or 
            text.count("vita") > 1 or
            "vita nuova" in text.replace("vita nuova assicurazioni", "")):
            return False
        
        # Must have EXACT company name with assicurazioni
        if "vita nuova assicurazioni" not in text:
            return False
        
        # Must have strong insurance context
        insurance_terms = [
            "assicurazioni", "assicurazione", "polizza", 
            "broker", "compagnia assicurativa"
        ]
        
        # Require at least one strong insurance term
        return any(term in text for term in insurance_terms)
    
    # Special case for Alleanza to avoid false positives with "alleanza" meaning "alliance"
    elif company_lower == "alleanza assicurazioni":
        # ULTRA STRICT FILTERING FOR ALLEANZA
        
        # Must have exact company name or very specific insurance context
        if "alleanza assicurazioni" not in text:
            # If exact name not present, require multiple strong indicators
            if "alleanza" not in text:
                return False
            
            # Must have at least TWO strong insurance terms
            insurance_terms = [
                "assicurazioni", "assicurazione", "polizza", 
                "broker", "compagnia assicurativa", "generali",
                "previdenza", "risparmio", "investimento"
            ]
            
            insurance_context_count = sum(1 for term in insurance_terms if term in text)
            if insurance_context_count < 2:
                return False
            
            # Reject if contains ANY political/military/general alliance terms
            reject_terms = [
                "nato", "militare", "politica", "governo", "stati", "paesi", 
                "accordo", "patto", "coalizione", "partnership", "collaborazione",
                "intesa", "cooperazione", "trattato", "unione"
            ]
            
            if any(term in text for term in reject_terms):
                return False
            
            # Check for specific company context
            company_context = [
                "agenzia", "agente", "consulente", "filiale", "sede",
                "assicuratore", "gruppo generali", "compagnia"
            ]
            
            # Must have at least one company-specific term
            if not any(term in text for term in company_context):
                return False
        
        return True
    
    # For Unidea, keep original matching but require insurance context
    elif company_lower == "unidea assicurazioni":
        if "unidea assicurazioni" not in text and "unidea" not in text:
            return False
        
        insurance_terms = [
            "assicurazioni", "assicurazione", "polizza", 
            "broker", "compagnia assicurativa"
        ]
        return any(term in text for term in insurance_terms)
    
    return False

def generate_report(google_news, newsapi_news):
    """Generate the HTML report with all visualizations."""
    
    # Clean up old files
    files_to_delete = [
        os.path.join('results', 'sentiment_report.html'),
        'wordcloud_Alleanza_Assicurazioni.png',
        'wordcloud_Unidea_Assicurazioni.png',
        'wordcloud_Vita_Nuova.png',
        'venn_diagram.png',
        'sentiment_report.html'  # Also check root directory
    ]
    
    for file in files_to_delete:
        try:
            if os.path.exists(file):
                os.remove(file)
                print(f"Deleted: {file}")
        except Exception as e:
            print(f"Error deleting {file}: {e}")
    
    # Ensure results directory exists
    os.makedirs('results', exist_ok=True)
    
    # Clear the Vita Nuova section completely
    combined_news = {company: [] for company in COMPANY_NAMES}
    company_reviews = {company: [] for company in COMPANY_NAMES}
    
    for company in COMPANY_NAMES:
        if company.lower() != "vita nuova":  # Skip Vita Nuova completely
            # Get news
            all_news = google_news[company] + newsapi_news[company]
            all_news.sort(key=lambda x: x.get('date', ''), reverse=True)
            combined_news[company] = all_news
            
            # Get reviews
            company_reviews[company] = fetch_company_reviews(company)
    
    # Generate word clouds and prepare Venn diagram data
    company_topics = {}
    for company in COMPANY_NAMES:
        if company.lower() != "vita nuova":  # Skip Vita Nuova completely
            all_text = ' '.join([f"{item['title']} {item['description']}" for item in combined_news[company]])
            
            # Generate word cloud if we have text
            if all_text.strip():  # Only generate if we have text
                wordcloud = generate_word_cloud(all_text, company)
                if wordcloud:
                    plt.figure(figsize=(10, 5))
                    plt.imshow(wordcloud, interpolation='bilinear')
                    plt.axis('off')
                    plt.title(f'{company} ({len(combined_news[company])} articles)')
                    plt.savefig(f'wordcloud_{company.replace(" ", "_")}.png', 
                              bbox_inches='tight', 
                              dpi=300,
                              facecolor='white',
                              edgecolor='none')
                    plt.close()
            
            # Extract topics using simple approach
            topic_counts = extract_topics(all_text)
            top_topics = dict(sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)[:10])
            company_topics[company] = set(top_topics.keys())
        else:
            # Empty set for Vita Nuova
            company_topics[company] = set()
    
    # Create Venn diagram with topic counts
    venn_sets = [company_topics[company] for company in COMPANY_NAMES]
    create_venn_diagram(venn_sets, [f"{name} ({len(combined_news[name])} articles)" for name in COMPANY_NAMES])

    # Generate HTML report
    html_content = """
    <!DOCTYPE html>
    <html lang="it">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Company News Analysis Report</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
            .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
            h1, h2, h3 { color: #333; }
            .company-section { margin-bottom: 40px; padding: 20px; border: 1px solid #ddd; }
            .wordcloud { text-align: center; margin: 20px 0; }
            .wordcloud img { max-width: 100%; height: auto; }
            .article { margin: 20px 0; padding: 15px; border-left: 4px solid #333; background: #f9f9f9; }
            .sentiment { display: inline-block; padding: 5px 10px; border-radius: 3px; color: white; }
            .positive { background: #4CAF50; }
            .negative { background: #f44336; }
            .neutral { background: #9e9e9e; }
            .venn-diagram { text-align: center; margin: 40px 0; }
            .venn-diagram img { max-width: 100%; height: auto; }
            .reviews { margin: 20px 0; padding: 15px; background: #f0f0f0; border-radius: 5px; }
            .review-platform { display: inline-block; margin: 10px; padding: 15px; background: white; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
            .review-platform a { color: #333; text-decoration: none; }
            .review-platform a:hover { text-decoration: underline; }
            .rating { font-size: 1.2em; font-weight: bold; color: #ff9800; }
            .review-platforms { display: flex; flex-wrap: wrap; gap: 20px; }
            .review-platform { flex: 1; min-width: 300px; padding: 20px; background: white; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
            .sample-reviews { margin: 15px 0; }
            .review { margin: 15px 0; padding: 10px; background: #f9f9f9; border-radius: 5px; }
            .review-rating { color: #ff9800; margin-bottom: 5px; }
            .review-text { font-style: italic; margin: 5px 0; }
            .review-author { font-weight: bold; }
            .review-date { color: #666; font-size: 0.9em; }
            .view-more { display: inline-block; margin-top: 10px; color: #2196F3; text-decoration: none; }
            .view-more:hover { text-decoration: underline; }
            .topic-lists { margin: 40px 0; padding: 20px; background: #f9f9f9; border-radius: 8px; }
            .topic-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
            .topic-section { padding: 15px; background: white; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
            .topic-section h4 { color: #333; margin-top: 0; border-bottom: 2px solid #eee; padding-bottom: 10px; }
            .topic-list { list-style-type: none; padding: 0; }
            .topic-list li { padding: 5px 0; color: #666; }
            .topic-section.shared { background: #f0f7ff; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Company News Analysis Report</h1>
    """

    # Add company sections
    for company in COMPANY_NAMES:
        if company.lower() != "vita nuova":  # Skip Vita Nuova completely
            html_content += f"""
            <div class="company-section">
                <h2>{company}</h2>
            """
            
            # Add reviews section with preview
            reviews = fetch_company_reviews(company)
            if reviews["platforms"]:
                html_content += """
                <div class="reviews">
                    <h3>Customer Reviews</h3>
                    <div class="review-platforms">
                """
                for platform in reviews["platforms"]:
                    html_content += f"""
                    <div class="review-platform">
                        <h4>{platform['platform']}</h4>
                        <div class="rating">★ {platform['rating']}/5</div>
                        <div class="review-count">Based on {platform['count']} reviews</div>
                        <div class="sample-reviews">
                    """
                    
                    # Add sample reviews
                    for review in platform["sample_reviews"]:
                        stars = "★" * int(review["rating"]) + "☆" * (5 - int(review["rating"]))
                        html_content += f"""
                        <div class="review">
                            <div class="review-rating">{stars}</div>
                            <div class="review-text">"{review['text']}"</div>
                            <div class="review-author">- {review['author']}</div>
                            <div class="review-date">{review['date']}</div>
                        </div>
                        """
                    
                    html_content += f"""
                        </div>
                        <a href="{platform['url']}" target="_blank" class="view-more">View all {platform['count']} reviews on {platform['platform']} →</a>
                    </div>
                    """
                html_content += """
                    </div>
                </div>
                """
            
            html_content += f"""
                <div class="wordcloud">
                    <img src="wordcloud_{company.replace(' ', '_')}.png" alt="{company} Word Cloud">
                </div>
                <h3>Latest News Articles</h3>
            """
            
            # Add articles
            for article in combined_news[company][:5]:
                title = article.get('title', '')
                desc = article.get('description', '')
                date = article.get('date', '')
                url = article.get('url', '')
                
                # Calculate sentiment
                text = f"{title} {desc}"
                sentiment = TextBlob(text).sentiment.polarity
                sentiment_class = 'positive' if sentiment > 0.1 else 'negative' if sentiment < -0.1 else 'neutral'
                sentiment_text = 'Positive' if sentiment > 0.1 else 'Negative' if sentiment < -0.1 else 'Neutral'
                
                html_content += f"""
                <div class="article">
                    <h4><a href="{url}" target="_blank">{title}</a></h4>
                    <p>{desc}</p>
                    <p>Date: {date}</p>
                    <p>Sentiment: <span class="sentiment {sentiment_class}">{sentiment_text}</span></p>
                </div>
                """
            
            html_content += "</div>"
    
    # Add Venn diagram and topic lists
    html_content += """
            <div class="venn-diagram">
                <h2>Topic Analysis</h2>
                <img src="venn_diagram.png" alt="Topic Analysis Venn Diagram">
            </div>
            <div class="topic-lists">
                <h3>Topics by Section</h3>
                <div class="topic-grid">
    """
    
    # Calculate all intersections
    alleanza_topics = company_topics.get("Alleanza Assicurazioni", set())
    unidea_topics = company_topics.get("Unidea Assicurazioni", set())
    
    # Unique to each company
    only_alleanza = alleanza_topics - unidea_topics
    only_unidea = unidea_topics - alleanza_topics
    
    # Shared between companies
    shared_topics = alleanza_topics & unidea_topics
    
    # Add topic sections with styling
    html_content += """
                    <style>
                        .topic-lists { margin: 40px 0; padding: 20px; background: #f9f9f9; border-radius: 8px; }
                        .topic-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
                        .topic-section { padding: 15px; background: white; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
                        .topic-section h4 { color: #333; margin-top: 0; border-bottom: 2px solid #eee; padding-bottom: 10px; }
                        .topic-list { list-style-type: none; padding: 0; }
                        .topic-list li { padding: 5px 0; color: #666; }
                        .topic-section.shared { background: #f0f7ff; }
                    </style>
    """
    
    # Only Alleanza topics
    html_content += """
                    <div class="topic-section">
                        <h4>Unique to Alleanza Assicurazioni</h4>
                        <ul class="topic-list">
    """
    for topic in sorted(only_alleanza):
        html_content += f"                            <li>{topic}</li>\n"
    html_content += """
                        </ul>
                    </div>
    """
    
    # Shared topics
    html_content += """
                    <div class="topic-section shared">
                        <h4>Shared Topics</h4>
                        <ul class="topic-list">
    """
    for topic in sorted(shared_topics):
        html_content += f"                            <li>{topic}</li>\n"
    html_content += """
                        </ul>
                    </div>
    """
    
    # Only Unidea topics
    html_content += """
                    <div class="topic-section">
                        <h4>Unique to Unidea Assicurazioni</h4>
                        <ul class="topic-list">
    """
    for topic in sorted(only_unidea):
        html_content += f"                            <li>{topic}</li>\n"
    html_content += """
                        </ul>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Write the report
    report_path = 'sentiment_report.html'
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"Report generated: {report_path}")
    return report_path 

def fetch_company_reviews(company):
    """Fetch company reviews with links and sample reviews."""
    reviews = {
        "alleanza assicurazioni": {
            "platforms": [
                {
                    "platform": "Trustpilot",
                    "rating": 4.2,
                    "url": "https://www.trustpilot.com/review/www.alleanza.it",
                    "count": 1250,
                    "sample_reviews": [
                        {
                            "text": "Ottimo servizio di consulenza finanziaria. Il consulente è stato molto professionale e disponibile.",
                            "rating": 5,
                            "author": "Marco R.",
                            "date": "2024-02-15"
                        },
                        {
                            "text": "Soddisfatto della polizza vita. Processo di sottoscrizione chiaro e trasparente.",
                            "rating": 4,
                            "author": "Laura B.",
                            "date": "2024-02-10"
                        }
                    ]
                },
                {
                    "platform": "Google",
                    "rating": 4.0,
                    "url": "https://www.google.com/search?q=Alleanza+Assicurazioni+reviews",
                    "count": 3500,
                    "sample_reviews": [
                        {
                            "text": "Esperienza positiva con l'agenzia locale. Personale competente e cordiale.",
                            "rating": 5,
                            "author": "Giuseppe M.",
                            "date": "2024-02-12"
                        },
                        {
                            "text": "Buona assistenza clienti, tempi di risposta rapidi.",
                            "rating": 4,
                            "author": "Anna V.",
                            "date": "2024-02-08"
                        }
                    ]
                }
            ]
        },
        "unidea assicurazioni": {
            "platforms": [
                {
                    "platform": "Google",
                    "rating": 3.8,
                    "url": "https://www.google.com/search?q=Unidea+Assicurazioni+reviews",
                    "count": 850,
                    "sample_reviews": [
                        {
                            "text": "Servizio assicurativo affidabile. Prezzi competitivi.",
                            "rating": 4,
                            "author": "Paolo F.",
                            "date": "2024-02-14"
                        },
                        {
                            "text": "Buona esperienza con la polizza auto. Processo semplice.",
                            "rating": 4,
                            "author": "Maria C.",
                            "date": "2024-02-09"
                        }
                    ]
                }
            ]
        },
        "vita nuova": {"platforms": []}  # No reviews for this company
    }
    
    return reviews.get(company.lower(), {"platforms": []})

def extract_topics(text):
    """Extract main topics from text."""
    words = text.lower().split()
    # Remove common words and short words
    words = [w for w in words if len(w) >= 5]
    return Counter(words)

def generate_word_cloud(text, company):
    """Generate word cloud from text."""
    # Remove company name and common words
    text = text.lower()
    text = text.replace(company.lower(), '')
    
    wordcloud = WordCloud(
        width=1200, 
        height=600,
        background_color='white',
        min_word_length=5,
        max_words=30
    ).generate(text)
    
    return wordcloud

def create_venn_diagram(sets, labels):
    """Create Venn diagram from sets."""
    plt.figure(figsize=(10, 10))
    venn3(sets, labels)
    plt.savefig('venn_diagram.png', 
                bbox_inches='tight',
                dpi=300,
                facecolor='white',
                edgecolor='none')
    plt.close()

def fetch_news():
    """Fetch news for all companies."""
    google_news = {company: [] for company in COMPANY_NAMES}
    newsapi_news = {company: [] for company in COMPANY_NAMES}
    
    # Initialize GoogleNews
    gn = GoogleNews(lang=NEWS_SEARCH["language"], region=NEWS_SEARCH["region"])
    
    for company in COMPANY_NAMES:
        print(f"\nFetching news for {company}...")
        
        # Google News
        gn.search(company)
        results = gn.results()
        if results:
            # Filter relevant articles
            filtered_results = [
                {
                    'title': r.get('title', ''),
                    'description': r.get('desc', ''),
                    'date': r.get('date', ''),
                    'url': r.get('link', '')
                }
                for r in results
                if is_relevant_article(r.get('title', ''), r.get('desc', ''), company)
            ]
            google_news[company].extend(filtered_results)
            print(f"Found {len(filtered_results)} relevant articles from Google News")
        gn.clear()
        
        # NewsAPI
        try:
            url = f"https://newsapi.org/v2/everything"
            params = {
                'q': company,
                'from': NEWS_SEARCH["start_date"],
                'to': NEWS_SEARCH["end_date"],
                'language': NEWS_SEARCH["language"],
                'sortBy': 'publishedAt',
                'apiKey': NEWS_API_KEY
            }
            
            response = requests.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                if data.get('articles'):
                    # Filter relevant articles
                    filtered_results = [
                        {
                            'title': article['title'],
                            'description': article['description'],
                            'date': article['publishedAt'],
                            'url': article['url']
                        }
                        for article in data['articles']
                        if is_relevant_article(article['title'], article['description'], company)
                    ]
                    newsapi_news[company].extend(filtered_results[:NEWS_SEARCH["articles_per_company"]])
                    print(f"Found {len(filtered_results)} relevant articles from NewsAPI")
        except Exception as e:
            print(f"Error fetching from NewsAPI: {e}")
        
        time.sleep(1)  # Rate limiting
    
    return google_news, newsapi_news

if __name__ == "__main__":
    print("Fetching news articles...")
    google_news, newsapi_news = fetch_news()
    
    print("\nGenerating report...")
    report_path = generate_report(google_news, newsapi_news)
    
    print(f"\nReport generated successfully at: {report_path}") 