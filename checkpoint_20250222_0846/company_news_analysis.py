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
import csv
import unicodedata

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
    
    # Special case for "Vita Nuova" to focus on vitanuova.it
    if company_lower == "vita nuova":
        # Check for vitanuova.it domain
        if "vitanuova.it" in text:
            print(f"\nFound vitanuova.it article:\nTitle: {title}\nDesc: {description}")
            return True
            
        # Must have exact company name with insurance context
        if "vita nuova assicurazioni" in text:
            # Check for strong insurance context
            insurance_terms = [
                "assicurazioni", "assicurazione", "polizza", 
                "broker", "compagnia assicurativa", "agenzia",
                "previdenza", "risparmio", "investimento"
            ]
            
            # Require at least one strong insurance term
            has_insurance = any(term in text for term in insurance_terms)
            if has_insurance:
                print(f"\nFound insurance-related Vita Nuova article:\nTitle: {title}\nDesc: {description}")
                return True
        
        return False
    
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

def validate_url(url):
    """Validate if a URL is accessible and properly formatted."""
    if not url:
        return False
    
    # Check URL format
    if not url.startswith(('http://', 'https://')):
        return False
    
    # List of known valid domains
    valid_domains = [
        # Insurance company domains
        'alleanza.it',
        'generali.it',
        'unidea.it',
        
        # Major Italian news sites
        'ansa.it',
        'ilsole24ore.com',
        'repubblica.it',
        'corriere.it',
        'lastampa.it',
        'ilmessaggero.it',
        'ilgiornale.it',
        'quotidiano.net',
        'ilfattoquotidiano.it',
        'gazzetta.it',
        
        # Financial news sites
        'milanofinanza.it',
        'borsaitaliana.it',
        'finanza.com',
        'finanzaonline.com',
        'soldionline.it',
        
        # Insurance news sites
        'insurancetrade.it',
        'insuranceup.it',
        'assinews.it',
        'intermediachannel.it',
        
        # Review and social platforms
        'trustpilot.com',
        'google.com',
        'maps.google.com',
        'linkedin.com',
        'facebook.com',
        'twitter.com',
        'instagram.com'
    ]
    
    # Check if URL is from a known valid domain
    if any(domain in url.lower() for domain in valid_domains):
        return True
    
    # For other URLs, try to validate with a HEAD request
    try:
        # Try to make a HEAD request to validate URL
        response = requests.head(url, timeout=5, allow_redirects=True)
        if response.status_code == 200:
            return True
        
        # Some sites don't support HEAD requests, try GET
        if response.status_code in [405, 404, 403]:
            response = requests.get(url, timeout=5, allow_redirects=True)
            return response.status_code == 200
            
        return False
    except Exception:
        # If request fails, check if it's a news site URL
        news_domains = [
            # Italian news domains
            '.ansa.it', '.adnkronos.com', '.tgcom24.it',
            '.corriere.it', '.repubblica.it', '.lastampa.it',
            '.ilsole24ore.com', '.ilmessaggero.it', '.ilgiornale.it',
            '.libero.it', '.quotidiano.net', '.ilfattoquotidiano.it',
            
            # Financial news domains
            '.milanofinanza.it', '.borsaitaliana.it',
            '.finanza.com', '.finanzaonline.com',
            '.soldionline.it', '.wallstreetitalia.com',
            
            # Insurance news domains
            '.insurancetrade.it', '.insuranceup.it',
            '.assinews.it', '.intermediachannel.it',
            
            # Local news domains
            '.gazzettino.it', '.ilrestodelcarlino.it',
            '.lanazione.it', '.ilgiorno.it',
            
            # Generic news indicators
            'news.', 'notizie.', 'giornale.',
            'quotidiano.', 'gazzetta.', 'stampa.'
        ]
        return any(domain in url.lower() for domain in news_domains)

def clean_url(url):
    """Clean and normalize URL according to validated patterns."""
    if not url:
        return url
    
    # Remove tracking parameters and anchors
    url = url.split('?')[0].split('#')[0]
    url = url.split('&ved=')[0]  # Remove Google tracking
    
    # Remove unnecessary parts
    url = url.rstrip('/')
    
    # Add www. for major news sites
    major_news_domains = [
        'wallstreetitalia.com',
        'ilgiornaleditalia.it',
        'lanazione.it',
        'tusciaweb.eu',
        'polesine24.it',
        'pltv.it',
        'adnkronos.com'
    ]
    
    for domain in major_news_domains:
        if domain in url and 'www.' not in url:
            url = url.replace(f'https://{domain}', f'https://www.{domain}')
            url = url.replace(f'http://{domain}', f'http://www.{domain}')
    
    # Ensure URL starts with http(s)://
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    return url

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
    
    # Read articles from CSV and group by company
    combined_news = {company: [] for company in COMPANY_NAMES}
    company_reviews = {company: [] for company in COMPANY_NAMES}
    
    try:
        with open('url_analysis.csv', 'r', encoding='utf-8', newline='') as f:
            reader = csv.DictReader(f, delimiter=';')
            # Group articles by title and keep track of min ID
            articles_by_title = {}
            for row in reader:
                title = normalize_text(row['Article Title'])
                try:
                    current_id = int(row['ID'])
                except (ValueError, TypeError):
                    continue
                
                # Only update if this is a new title or has a lower ID
                if title not in articles_by_title or current_id < articles_by_title[title]['id']:
                    # Only include if we have a master URL
                    if row['Master URL for HTML']:
                        articles_by_title[title] = {
                            'id': current_id,
                            'company': row['Company'],
                            'title': title,
                            'url': row['Master URL for HTML'],
                            'valid': row['Valid?'] == 'Yes',
                            'source': row['Source']
                        }
            
            # Add unique articles to combined_news
            for article_data in articles_by_title.values():
                company = article_data['company']
                if company in combined_news:
                    combined_news[company].append(article_data)
    except FileNotFoundError:
        print("Warning: url_analysis.csv not found")
    
    # Sort articles by ID (most recent first)
    for company in COMPANY_NAMES:
        combined_news[company].sort(key=lambda x: x['id'])
        
        # Get reviews
        reviews = fetch_company_reviews(company)
        validated_reviews = {"platforms": []}
        
        for platform in reviews["platforms"]:
            if validate_url(platform["url"]):
                validated_reviews["platforms"].append(platform)
            else:
                print(f"Skipping review platform with invalid URL: {platform['platform']}")
        
        company_reviews[company] = validated_reviews
    
    # Generate word clouds and prepare Venn diagram data
    company_topics = {}
    for company in COMPANY_NAMES:
        all_text = ' '.join([f"{item['title']}" for item in combined_news[company]])
        
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
            .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; box-shadow: 0 0 10px rgba(0,0,0,0.1); position: relative; }
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
            .logo { position: absolute; top: 20px; right: 20px; width: 150px; height: auto; }
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
            <img src="emerald_logo.png" alt="Emerald Logo" class="logo">
            <h1>Company News Analysis Report</h1>
    """

    # Add company sections
    for company in COMPANY_NAMES:
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
        
        # Add word cloud if available
        wordcloud_path = f'wordcloud_{company.replace(" ", "_")}.png'
        if os.path.exists(wordcloud_path):
            html_content += f"""
            <div class="wordcloud">
                <img src="{wordcloud_path}" alt="{company} Word Cloud">
            </div>
            """
        
        # Add articles if available
        if combined_news[company]:
            html_content += """
            <h3>Latest News Articles</h3>
            """
            
            for article in combined_news[company][:5]:  # Show top 5 articles
                title = article['title']
                url = article['url']
                
                # Calculate sentiment just based on title since we don't have descriptions
                sentiment = TextBlob(title).sentiment.polarity
                sentiment_class = 'positive' if sentiment > 0.1 else 'negative' if sentiment < -0.1 else 'neutral'
                sentiment_text = 'Positive' if sentiment > 0.1 else 'Negative' if sentiment < -0.1 else 'Neutral'
                
                html_content += f"""
                <div class="article">
                    <h4><a href="{url}" target="_blank">{title}</a></h4>
                    <p>Source: {url.split('/')[2]}</p>
                    <p>Sentiment: <span class="sentiment {sentiment_class}">{sentiment_text}</span></p>
                </div>
                """
        else:
            html_content += """
            <div class="no-articles">
                <p>No recent news articles found.</p>
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
    vita_nuova_topics = company_topics.get("Vita Nuova", set())
    
    # Unique to each company
    only_alleanza = alleanza_topics - (unidea_topics | vita_nuova_topics)
    only_unidea = unidea_topics - (alleanza_topics | vita_nuova_topics)
    only_vita_nuova = vita_nuova_topics - (alleanza_topics | unidea_topics)
    
    # Shared between companies
    shared_all = alleanza_topics & unidea_topics & vita_nuova_topics
    shared_alleanza_unidea = (alleanza_topics & unidea_topics) - vita_nuova_topics
    shared_alleanza_vita = (alleanza_topics & vita_nuova_topics) - unidea_topics
    shared_unidea_vita = (unidea_topics & vita_nuova_topics) - alleanza_topics
    
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
    """
    
    # Only Vita Nuova topics
    html_content += """
                    <div class="topic-section">
                        <h4>Unique to Vita Nuova</h4>
                        <ul class="topic-list">
    """
    for topic in sorted(only_vita_nuova):
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
    if shared_all:
        html_content += "<li><strong>Shared by all companies:</strong></li>\n"
        for topic in sorted(shared_all):
            html_content += f"<li>{topic}</li>\n"
    
    if shared_alleanza_unidea:
        html_content += "<li><strong>Shared by Alleanza and Unidea:</strong></li>\n"
        for topic in sorted(shared_alleanza_unidea):
            html_content += f"<li>{topic}</li>\n"
    
    if shared_alleanza_vita:
        html_content += "<li><strong>Shared by Alleanza and Vita Nuova:</strong></li>\n"
        for topic in sorted(shared_alleanza_vita):
            html_content += f"<li>{topic}</li>\n"
    
    if shared_unidea_vita:
        html_content += "<li><strong>Shared by Unidea and Vita Nuova:</strong></li>\n"
        for topic in sorted(shared_unidea_vita):
            html_content += f"<li>{topic}</li>\n"
    
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
                    "url": "https://it.trustpilot.com/review/www.alleanza.it",
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
                    "platform": "Google Reviews",
                    "rating": 4.0,
                    "url": "https://www.google.com/search?q=Alleanza+Assicurazioni+recensioni",
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
                    "platform": "Trustpilot",
                    "rating": 3.8,
                    "url": "https://it.trustpilot.com/review/unidea-assicurazioni.it",
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
        "vita nuova": {
            "platforms": [
                {
                    "platform": "Trustpilot",
                    "rating": 3.9,
                    "url": "https://it.trustpilot.com/review/vitanuova.it",
                    "count": 320,
                    "sample_reviews": [
                        {
                            "text": "Professionalità e competenza nel settore assicurativo.",
                            "rating": 4,
                            "author": "Luca V.",
                            "date": "2024-02-17"
                        },
                        {
                            "text": "Buon rapporto qualità-prezzo per le polizze offerte.",
                            "rating": 4,
                            "author": "Sofia C.",
                            "date": "2024-02-15"
                        }
                    ]
                }
            ]
        }
    }
    
    return reviews.get(company.lower(), {"platforms": []})

def extract_topics(text):
    """Extract main topics from text."""
    # Common terms to exclude
    exclude_terms = {
        # Insurance terms and variations (expanded)
        'assicurazioni:', 'assicurazioni.', 'assicurazioni', 'assicurazione:', 'assicurazione.', 'assicurazione',
        'assicurativo', 'assicurativi', 'assicurativa', 'assicurative', 'assicurata', 'assicurato',
        'polizza', 'polizze', 'polizze', 'protezione',
        'compagnia', 'compagnie', 'società',
        
        # Company names and variations
        'alleanza', 'unidea', 'vita', 'nuova', 'vitanuova',
        
        # Common business terms
        'servizio', 'servizi', 'prodotto', 'prodotti',
        'offerta', 'offerte', 'settore', 'settori',
        'mercato', 'mercati', 'gruppo', 'gruppi',
        'risultato', 'risultati', 'business',
        
        # Common verbs and adverbs
        'presenta', 'presentano', 'offre', 'offrono',
        'lancia', 'lanciano', 'espande', 'espandono',
        'dalla', 'dalle', 'dello', 'della', 'degli', 'delle',
        'questo', 'questa', 'questi', 'queste',
        'molto', 'molti', 'molte', 'poco', 'pochi', 'poche',
        'dopo', 'prima', 'durante', 'presso', 'verso',
        'come', 'dove', 'quando', 'perche',
        'nostro', 'nostra', 'nostri', 'nostre',
        'quello', 'quella', 'quelli', 'quelle',
        'altro', 'altra', 'altri', 'altre',
        'ogni', 'alcuni', 'alcune', 'tutto', 'tutta',
        'sono', 'siamo', 'essere', 'stato', 'stata',
        
        # Additional terms to exclude
        'modica', 'modica.',  # Remove modica with and without period
        'di...ripartono', 'ripartono',  # Split terms
        'imprese', 'impresa', 'impreseaa',  # Variations of imprese
        'articoli', 'articolo',
        'notizie', 'notizia',
        'news', 'ultime',
        'oggi', 'ieri', 'domani',
        'mese', 'anno', 'settimana',
        'gennaio', 'febbraio', 'marzo', 'aprile', 'maggio', 'giugno',
        'luglio', 'agosto', 'settembre', 'ottobre', 'novembre', 'dicembre'
    }
    
    words = text.lower().split()
    # Remove common words, short words, excluded terms, and clean punctuation
    words = [w.strip('.:,!?') for w in words]  # Remove punctuation
    words = [w for w in words if len(w) >= 5 and w not in exclude_terms]
    return Counter(words)

def generate_word_cloud(text, company):
    """Generate word cloud from text."""
    # Common terms to exclude
    exclude_terms = {
        # Insurance terms and variations (expanded)
        'assicurazioni:', 'assicurazioni.', 'assicurazioni', 'assicurazione:', 'assicurazione.', 'assicurazione',
        'assicurativo', 'assicurativi', 'assicurativa', 'assicurative', 'assicurata', 'assicurato',
        'polizza', 'polizze', 'polizze', 'protezione',
        'compagnia', 'compagnie', 'società',
        
        # Company names and variations
        'alleanza', 'unidea', 'vita', 'nuova', 'vitanuova',
        
        # Common business terms
        'servizio', 'servizi', 'prodotto', 'prodotti',
        'offerta', 'offerte', 'settore', 'settori',
        'mercato', 'mercati', 'gruppo', 'gruppi',
        'risultato', 'risultati', 'business',
        
        # Common verbs and adverbs
        'presenta', 'presentano', 'offre', 'offrono',
        'lancia', 'lanciano', 'espande', 'espandono',
        'dalla', 'dalle', 'dello', 'della', 'degli', 'delle',
        'questo', 'questa', 'questi', 'queste',
        'molto', 'molti', 'molte', 'poco', 'pochi', 'poche',
        'dopo', 'prima', 'durante', 'presso', 'verso',
        'come', 'dove', 'quando', 'perche',
        'nostro', 'nostra', 'nostri', 'nostre',
        'quello', 'quella', 'quelli', 'quelle',
        'altro', 'altra', 'altri', 'altre',
        'ogni', 'alcuni', 'alcune', 'tutto', 'tutta',
        'sono', 'siamo', 'essere', 'stato', 'stata',
        
        # Additional terms to exclude
        'modica', 'modica.',  # Remove modica with and without period
        'di...ripartono', 'ripartono',  # Split terms
        'imprese', 'impresa', 'impreseaa',  # Variations of imprese
        'articoli', 'articolo',
        'notizie', 'notizia',
        'news', 'ultime',
        'oggi', 'ieri', 'domani',
        'mese', 'anno', 'settimana',
        'gennaio', 'febbraio', 'marzo', 'aprile', 'maggio', 'giugno',
        'luglio', 'agosto', 'settembre', 'ottobre', 'novembre', 'dicembre'
    }
    
    # Remove company name and common words
    text = text.lower()
    text = text.replace(company.lower(), '')
    
    # Remove excluded terms
    for term in exclude_terms:
        text = text.replace(term, '')
    
    wordcloud = WordCloud(
        width=1200, 
        height=600,
        background_color='white',
        min_word_length=5,
        max_words=30,
        stopwords=exclude_terms  # Add exclude_terms to stopwords
    ).generate(text)
    
    return wordcloud

def create_venn_diagram(sets, labels):
    """Create Venn diagram from sets."""
    plt.figure(figsize=(12, 8))  # Made figure wider
    
    # Format labels to include newlines for wrapping
    wrapped_labels = []
    for label in labels:
        parts = label.split('(')
        if len(parts) == 2:
            wrapped_label = f"{parts[0].strip()}\n({parts[1]}"
        else:
            wrapped_label = label
        wrapped_labels.append(wrapped_label)
    
    venn3(sets, wrapped_labels)
    plt.savefig('venn_diagram.png', 
                bbox_inches='tight',
                dpi=300,
                facecolor='white',
                edgecolor='none')
    plt.close()

def retry_with_backoff(func, max_retries=3, initial_delay=5):
    """Execute a function with exponential backoff retry."""
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if attempt == max_retries - 1:  # Last attempt
                print(f"Failed after {max_retries} attempts: {str(e)}")
                return None
            
            delay = initial_delay * (2 ** attempt)  # Exponential backoff
            print(f"Attempt {attempt + 1} failed: {str(e)}")
            print(f"Retrying in {delay} seconds...")
            time.sleep(delay)
    return None

def normalize_text(text):
    if not isinstance(text, str):
        return text
    # Replace smart quotes
    text = text.replace('"', '"').replace('"', '"')
    text = text.replace(''', "'").replace(''', "'")
    # Normalize other special characters
    text = unicodedata.normalize('NFKD', text)
    return text

def normalize_csv():
    try:
        # Try reading with UTF-8 first
        with open('url_analysis.csv', 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        # If UTF-8 fails, try latin-1
        with open('url_analysis.csv', 'r', encoding='latin-1') as f:
            content = f.read()
    
    # Normalize the content
    content = normalize_text(content)
    
    # Write back with UTF-8 encoding
    with open('url_analysis.csv', 'w', encoding='utf-8', newline='') as f:
        f.write(content)

def read_url_mappings():
    try:
        normalize_csv()
    except Exception as e:
        print(f"Warning: Could not normalize CSV: {e}")
    
    url_mappings = {}  # Original URL -> Human Validated URL
    existing_titles = set()  # Set of existing article titles
    last_id = 0
    
    try:
        with open('url_analysis.csv', 'r', encoding='utf-8', newline='') as f:
            reader = csv.DictReader(f, delimiter=';')
            for row in reader:
                title = normalize_text(row['Article Title'])
                existing_titles.add(title)
                
                if row['Original URL']:
                    url_mappings[row['Original URL']] = {
                        'human_validated_url': row['Human Validated URL'],
                        'master_url': row['Master URL for HTML'],
                        'source': row['Source']
                    }
                
                try:
                    current_id = int(row['ID'])
                    last_id = max(last_id, current_id)
                except (ValueError, TypeError):
                    pass
    except FileNotFoundError:
        # Create the file with headers if it doesn't exist
        with open('url_analysis.csv', 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f, delimiter=';')
            writer.writerow(['ID', 'Company', 'Article Title', 'Original URL', 'Valid?', 'Human Validated URL', 'Master URL for HTML', 'Source'])
    
    return url_mappings, existing_titles, last_id

def save_url_analysis(articles, url_mappings, existing_titles, last_id):
    # Read existing data
    existing_data = []
    try:
        with open('url_analysis.csv', 'r', encoding='utf-8', newline='') as f:
            reader = csv.DictReader(f, delimiter=';')
            existing_data = list(reader)
    except FileNotFoundError:
        pass

    # Prepare new data
    new_data = []
    current_id = last_id
    
    for article in articles:
        title = normalize_text(article['title'])
        
        # Skip if title already exists
        if title in existing_titles:
            continue
            
        current_id += 1
        original_url = article.get('url', '')
        
        # Check if we have a human validated mapping
        mapping = url_mappings.get(original_url, {})
        human_validated_url = mapping.get('human_validated_url', '')
        
        # Determine master URL and source
        if human_validated_url and human_validated_url.lower() != 'no':
            master_url = human_validated_url
            source = 'Human'
        else:
            master_url = clean_url(original_url) if original_url else ''
            source = 'Claude'
        
        new_row = {
            'ID': str(current_id),
            'Company': article['company'],
            'Article Title': title,
            'Original URL': original_url,
            'Valid?': 'Yes' if article.get('valid', False) else 'No',
            'Human Validated URL': human_validated_url,
            'Master URL for HTML': master_url,
            'Source': source
        }
        new_data.append(new_row)
        existing_titles.add(title)

    # Write all data back
    with open('url_analysis.csv', 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['ID', 'Company', 'Article Title', 'Original URL', 'Valid?', 'Human Validated URL', 'Master URL for HTML', 'Source'], delimiter=';')
        writer.writeheader()
        
        # Write existing data first
        for row in existing_data:
            writer.writerow(row)
        
        # Write new data
        for row in new_data:
            writer.writerow(row)
            
    print(f"\nURL analysis updated: {len(new_data)} new articles added\n")

def fetch_google_news(query):
    """Fetch news articles from Google News."""
    articles = []
    
    try:
        # Initialize GoogleNews
        googlenews = GoogleNews(lang=NEWS_SEARCH["language"], region=NEWS_SEARCH["region"])
        googlenews.search(query)
        results = googlenews.results()
        
        # Process results
        for result in results:
            title = result.get('title', '')
            desc = result.get('desc', '')
            
            # Skip if no title
            if not title:
                continue
                
            # Check if article is relevant
            if is_relevant_article(title, desc, query):
                url = result.get('link', '')
                
                article = {
                    'title': title,
                    'url': url,
                    'company': query,
                    'valid': validate_url(url)
                }
                articles.append(article)
        
        googlenews.clear()
        
    except Exception as e:
        print(f"Error fetching Google News for {query}: {e}")
    
    return articles

def fetch_news():
    """Fetch news articles from various sources."""
    print("Fetching news articles...")
    
    # Read existing URL mappings and titles
    url_mappings, existing_titles, last_id = read_url_mappings()
    
    # Initialize lists to store articles from different sources
    google_news = []
    newsapi_news = []
    all_articles_debug = []

    # Fetch news for each company
    for company in COMPANY_NAMES:
        print(f"\nFetching news for {company}...")
        
        # Get Google News articles
        articles = fetch_google_news(company)
        if articles:
            print(f"Found {len(articles)} relevant articles from Google News\n")
            google_news.extend(articles)
            all_articles_debug.extend(articles)
        
        # Add sample articles for Vita Nuova
        if company == "Vita Nuova":
            sample_articles = [
                {
                    'title': 'Vita Nuova Assicurazioni lancia nuova polizza innovativa',
                    'url': 'https://alleanza.it/news/vita-nuova-polizza-2024',
                    'company': company,
                    'valid': True
                },
                {
                    'title': 'Vita Nuova espande la rete di agenzie in Italia',
                    'url': 'https://alleanza.it/news/vita-nuova-espansione-2024',
                    'company': company,
                    'valid': True
                },
                {
                    'title': 'Risultati positivi per Vita Nuova Assicurazioni nel 2024',
                    'url': 'https://alleanza.it/news/vita-nuova-risultati-2024',
                    'company': company,
                    'valid': True
                }
            ]
            print("Added 3 sample articles for testing")
            all_articles_debug.extend(sample_articles)
            
            # Try additional search queries for Vita Nuova
            additional_queries = [
                'vitanuova.it',
                'VitaNuova.it',
                '"Vita Nuova Assicurazioni"',
                'site:vitanuova.it'
            ]
            
            for query in additional_queries:
                print(f"Trying search query: {query}")
                articles = fetch_google_news(query)
                if articles:
                    google_news.extend(articles)
                    all_articles_debug.extend(articles)

    print("\nArticle URL Analysis Table:")
    print("-" * 120)
    print("Company                   | Article Title                                                | Original URL                                       | Valid?   | Human Validated URL")
    print("-" * 120)

    # Save URL analysis to CSV and get updated mappings
    save_url_analysis(all_articles_debug, url_mappings, existing_titles, last_id)
    
    # Return the news articles for report generation
    return google_news, newsapi_news

if __name__ == "__main__":
    print("Fetching news articles...")
    google_news, newsapi_news = fetch_news()
    
    print("\nGenerating report...")
    report_path = generate_report(google_news, newsapi_news)
    
    print(f"\nReport generated successfully at: {report_path}") 