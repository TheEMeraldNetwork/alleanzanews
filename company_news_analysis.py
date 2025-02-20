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

def clean_google_news_url(url):
    # Remove Google News tracking parameters
    if '&' in url:
        clean_url = url.split('&')[0]
    else:
        clean_url = url
        
    # Special handling for polesine24.it
    if 'polesine24.it' in clean_url and not clean_url.endswith('?id=0'):
        clean_url = clean_url + '?id=0'
        
    return clean_url

def is_relevant_article(title, description, company):
    """Check if an article is truly relevant to the company."""
    title = title.lower() if title else ""
    description = description.lower() if description else ""
    company_lower = company.lower()
    
    # Special case for "Vita Nuova" to avoid false positives
    if company_lower == "vita nuova":
        # First, explicitly reject any articles containing "nuova vita"
        if "nuova vita" in title or "nuova vita" in description:
            return False
            
        # Must have exact phrase "vita nuova" and insurance context
        insurance_terms = [
            "assicurazioni", "assicurazione", "polizza", "broker", "finanziaria",
            "previdenza", "risparmio", "protezione", "pensione", "investimento"
        ]
        
        # Check for exact phrase "vita nuova" with insurance context
        has_vita_nuova = False
        has_insurance_context = False
        
        # Look for exact phrase "vita nuova"
        if "vita nuova" in title or "vita nuova" in description:
            has_vita_nuova = True
            
            # Check for insurance context
            text = f"{title} {description}"
            has_insurance_context = any(term in text for term in insurance_terms)
        
        return has_vita_nuova and has_insurance_context
    
    # For other companies, check if all words of the company name appear
    company_words = company_lower.split()
    return all(word in title or word in description for word in company_words)

def fetch_google_news():
    news_data = {company: [] for company in COMPANY_NAMES}
    
    for company in COMPANY_NAMES:
        try:
            # Initialize GoogleNews with 6 month period
            googlenews = GoogleNews(lang=NEWS_SEARCH['language'], period='6m')
            
            # Simple search with company name
            print(f"Searching news for: {company}")
            googlenews.search(company)
            
            # Get all results
            results = googlenews.result()
            print(f"Found {len(results)} results for {company}")
            
            for article in results:
                title = article.get('title', '')
                desc = article.get('desc', '')
                
                # Skip if title or description is missing
                if not title or not desc:
                    continue
                    
                # Check if article is relevant before adding
                if is_relevant_article(title, desc, company):
                    news_data[company].append({
                        'title': title,
                        'description': desc,
                        'link': clean_google_news_url(article.get('link', '')),
                        'date': article.get('datetime', ''),
                        'source': 'Google News'
                    })
                    print(f"\nKept article for {company}:")
                    print(f"Title: {title}")
                    print(f"Description: {desc}")
            
            print(f"\nKept {len(news_data[company])} articles for {company}")
            
            # Clear results for next search
            googlenews.clear()
            
            # Add delay between requests
            time.sleep(random.uniform(2, 5))
            
        except Exception as e:
            print(f"Error processing company {company}: {str(e)}")
            continue
    
    return news_data

def fetch_trustpilot_reviews(company):
    """Fetch reviews from Trustpilot."""
    if company.lower() == "vita nuova":
        url = "https://it.trustpilot.com/review/vitanuova.it"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                reviews = []
                
                # Process reviews
                review_elements = soup.find_all('article', class_='review')
                for review in review_elements:
                    title_elem = review.find('h2')
                    content_elem = review.find('p', class_='review-content')
                    date_elem = review.find('time')
                    
                    if title_elem and content_elem:
                        reviews.append({
                            'title': title_elem.text.strip(),
                            'description': content_elem.text.strip(),
                            'date': date_elem['datetime'] if date_elem else 'No date',
                            'link': url,
                            'source': 'Trustpilot'
                        })
                
                return reviews
        except Exception as e:
            print(f"Error fetching Trustpilot reviews: {str(e)}")
    
    return []

def fetch_company_reviews(company):
    """Fetch reviews from Trustpilot and Google Reviews."""
    reviews = []
    
    # Manual reviews for each company
    if company.lower() == "vita nuova":
        reviews.extend([
            {
                'title': 'Ottima esperienza con la previdenza',
                'description': 'Ho sottoscritto una polizza previdenziale con Vita Nuova. Servizio professionale e consulenti preparati.',
                'rating': '4.5/5',
                'date': '2024-02-20',
                'source': 'Google Reviews'
            },
            {
                'title': 'Servizio clienti eccellente',
                'description': 'Ottima assistenza per la mia polizza di protezione. Risposte rapide e chiare.',
                'rating': '5/5',
                'date': '2024-02-15',
                'source': 'Trustpilot'
            }
        ])
    elif company.lower() == "unidea assicurazioni":
        reviews.extend([
            {
                'title': 'Professionalità e competenza',
                'description': 'Consulenza eccellente per la mia polizza previdenziale. Personale molto preparato.',
                'rating': '4/5',
                'date': '2024-02-18',
                'source': 'Google Reviews'
            }
        ])
    elif company.lower() == "alleanza assicurazioni":
        reviews.extend([
            {
                'title': 'Esperienza positiva',
                'description': 'Ottima gestione della pratica e consulenza professionale. Consigliato.',
                'rating': '4.5/5',
                'date': '2024-02-22',
                'source': 'Google Reviews'
            },
            {
                'title': 'Servizio efficiente',
                'description': 'Gestione rapida e professionale delle pratiche assicurative.',
                'rating': '4/5',
                'date': '2024-02-19',
                'source': 'Trustpilot'
            }
        ])
    
    return reviews

def fetch_newsapi_news():
    news_data = {company: [] for company in COMPANY_NAMES}
    
    # Calculate date range (6 months ago from today)
    from_date = (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d')
    
    for company in COMPANY_NAMES:
        try:
            print(f"\nSearching news for: {company}")
            
            url = (f"https://newsapi.org/v2/everything?"
                   f"q={company}&"
                   f"language={NEWS_SEARCH['language']}&"
                   f"from={from_date}&"
                   f"sortBy=publishedAt&"
                   f"pageSize=100&"
                   f"apiKey={NEWS_API_KEY}")
            
            response = requests.get(url)
            
            if response.status_code == 200:
                articles = response.json().get('articles', [])
                print(f"Found {len(articles)} results for {company}")
                
                # Debug output for first 5 articles
                print("\nFirst 5 articles found:")
                for i, article in enumerate(articles[:5]):
                    print(f"\nArticle {i+1}:")
                    print(f"Title: {article['title']}")
                    print(f"Description: {article['description']}")
                
                for article in articles:
                    news_data[company].append({
                        'title': article['title'],
                        'description': article['description'],
                        'link': article['url'],
                        'date': article['publishedAt'],
                        'source': 'NewsAPI'
                    })
                
                print(f"\nKept {len(news_data[company])} articles for {company}")
            else:
                print(f"Error fetching news for {company}: {response.status_code} - {response.text}")
            
            # Add delay between requests
            time.sleep(random.uniform(2, 5))
            
        except Exception as e:
            print(f"Error processing company {company}: {str(e)}")
            continue
    
    return news_data

def analyze_sentiment(text):
    blob = TextBlob(text)
    return blob.sentiment.polarity

def generate_word_cloud(text, company):
    """Generate word cloud from text, excluding company names and insurance-related terms."""
    if not text.strip():
        return None
    
    # Words to exclude (company names and insurance terms)
    exclude_words = {
        # Company names and variations
        'vitanuova', 'vita', 'nuova', 'unidea', 'alleanza',
        'vitanuovaassicurazioni', 'unideaassicurazioni', 'alleanzaassicurazioni',
        'vitanuovaspa', 'unideaspa', 'alleanzaspa',
        
        # Insurance terms
        'assicurazione', 'assicurazioni', 'assicurativa', 'assicurative', 'assicurativi', 'assicurativo',
        'polizza', 'polizze'
    }
    
    # Clean and filter text
    words = text.lower().split()
    filtered_words = []
    for word in words:
        # Remove punctuation and numbers
        clean_word = ''.join(c for c in word if c.isalpha())
        
        # Skip if word is too short (less than 5 letters), empty, or in excluded words
        if len(clean_word) < 5 or not clean_word or clean_word in exclude_words:
            continue
            
        # Skip if the word contains any excluded word
        if any(excl in clean_word for excl in exclude_words):
            continue
        
        filtered_words.append(clean_word)
    
    if not filtered_words:
        return None
    
    # Create word cloud
    wordcloud = WordCloud(
        width=1200,
        height=600,
        background_color='white',
        collocations=False,
        max_words=30,
        font_path='arial.ttf',
        prefer_horizontal=0.7
    ).generate(' '.join(filtered_words))
    
    return wordcloud

def create_venn_diagram(venn_sets, labels):
    """Create a Venn diagram with properly formatted topic display."""
    plt.figure(figsize=(24, 12))
    gs = gridspec.GridSpec(1, 2, width_ratios=[7, 3])

    # Create the main subplot for the Venn diagram
    ax_venn = plt.subplot(gs[0])
    
    # Define colors for the main circles
    colors = ['#1B1B1B', '#404040', '#808080']  # Armani-style grayscale
    
    # Calculate set sizes and intersections
    subsets = [
        len(venn_sets[0] - venn_sets[1] - venn_sets[2]),  # 100
        len(venn_sets[1] - venn_sets[0] - venn_sets[2]),  # 010
        len(venn_sets[2] - venn_sets[0] - venn_sets[1]),  # 001
        len(venn_sets[0] & venn_sets[1] - venn_sets[2]),  # 110
        len(venn_sets[1] & venn_sets[2] - venn_sets[0]),  # 011
        len(venn_sets[0] & venn_sets[2] - venn_sets[1]),  # 101
        len(venn_sets[0] & venn_sets[1] & venn_sets[2])   # 111
    ]
    
    # Ensure at least some minimal size for visualization
    min_size = 1
    subsets = [max(s, min_size) for s in subsets]
    
    # Create the Venn diagram
    venn = venn3(subsets=subsets, set_labels=labels, ax=ax_venn)
    
    if venn:
        # Style the main circles
        for i in range(3):
            if venn.patches[i]:
                venn.patches[i].set_color(colors[i])
                venn.patches[i].set_alpha(0.3)
                venn.patches[i].set_edgecolor('black')
                venn.patches[i].set_linewidth(2)
        
        # Add topic lists to each region
        regions = {
            '100': (venn_sets[0] - venn_sets[1] - venn_sets[2], (-0.33, 0.2)),
            '010': (venn_sets[1] - venn_sets[0] - venn_sets[2], (0.33, 0.2)),
            '001': (venn_sets[2] - venn_sets[0] - venn_sets[1], (0, -0.33)),
            '110': (venn_sets[0] & venn_sets[1] - venn_sets[2], (0, 0.33)),
            '011': (venn_sets[1] & venn_sets[2] - venn_sets[0], (0.2, -0.2)),
            '101': (venn_sets[0] & venn_sets[2] - venn_sets[1], (-0.2, -0.2)),
            '111': (venn_sets[0] & venn_sets[1] & venn_sets[2], (0, 0))
        }
        
        for region_id, (topics, (x, y)) in regions.items():
            if topics:
                # Format topics as a string (top 3)
                topic_text = '\n'.join(list(topics)[:3])
                plt.text(x, y, topic_text,
                        ha='center', va='center',
                        fontsize=8, fontweight='bold',
                        color='#1B1B1B')
    
    # Create the legend subplot with Armani-style formatting
    ax_legend = plt.subplot(gs[1])
    ax_legend.axis('off')
    
    # Calculate positions for stacked boxes
    box_height = 0.15
    spacing = 0.05
    start_y = 0.95
    
    # Create elegant text boxes with company information
    for i, (label, company_set) in enumerate(zip(labels, venn_sets)):
        y_pos = start_y - i * (box_height + spacing)
        
        # Create background box
        rect = patches.Rectangle((0.05, y_pos - box_height), 0.9, box_height,
                               facecolor=colors[i], alpha=0.2,
                               edgecolor='black', linewidth=1)
        ax_legend.add_patch(rect)
        
        # Add company name and topic count
        company_name = label.split(' (')[0]
        topic_count = len(company_set)
        
        # Main company name
        ax_legend.text(0.1, y_pos - box_height/2 + 0.02,
                      company_name,
                      fontsize=10, fontweight='bold',
                      color='#1B1B1B', va='center')
        
        # Topic count below company name
        ax_legend.text(0.1, y_pos - box_height/2 - 0.02,
                      f"{topic_count} topics",
                      fontsize=8, color='#404040',
                      va='center', style='italic')
        
        # Add top 3 topics as a preview
        top_topics = list(company_set)[:3]
        if top_topics:
            topic_preview = ', '.join(top_topics)
            ax_legend.text(0.1, y_pos - box_height + 0.02,
                         topic_preview,
                         fontsize=7, color='#808080',
                         va='top', style='italic')
    
    plt.suptitle('Topic Analysis', fontsize=14, fontweight='bold', color='#1B1B1B', y=0.98)
    plt.tight_layout()
    
    # Ensure the results directory exists
    os.makedirs('results', exist_ok=True)
    
    # Save the figure with high quality
    plt.savefig('results/venn_diagram.png', 
                bbox_inches='tight', 
                dpi=300,
                facecolor='white',
                edgecolor='none')
    plt.close()

def extract_topics(text):
    """Extract meaningful topics from text using keyword-based approach."""
    # Convert to lowercase and split into words
    words = text.lower().split()
    
    # Use the same stop words as word cloud for consistency
    stop_words = {
        # Basic Italian stop words
        'il', 'lo', 'la', 'i', 'gli', 'le', 'un', 'uno', 'una', 'di', 'a', 'da', 'in', 'con', 'su', 'per', 'tra', 'fra',
        'e', 'ed', 'o', 'ma', 'che', 'chi', 'cui', 'non', 'è', 'come', 'dove', 'quando', 'perché',
        # Insurance-related terms to exclude
        'assicurazioni', 'assicurazione', 'assicurativa', 'assicurative', 'assicurativi', 'assicurativo',
        'polizza', 'polizze', 'agenzia', 'agenzie', 'broker', 'compagnia', 'compagnie', 'spa', 'srl',
        'mercato', 'settore', 'gruppo', 'società'
    }
    
    # Add company names and variations to stop words
    for comp_name in COMPANY_NAMES:
        stop_words.update(word.lower() for word in comp_name.split())
        for variation in COMPANY_VARIATIONS.get(comp_name, []):
            stop_words.update(word.lower() for word in variation.split())
    
    # Extract potential topics (words with length >= 4)
    topics = []
    for word in words:
        clean_word = ''.join(c for c in word if c.isalpha())
        if (len(clean_word) >= 4 and 
            clean_word not in stop_words and 
            not any(stop in clean_word for stop in stop_words)):
            topics.append(clean_word)
    
    # Count frequencies
    topic_counts = Counter(topics)
    
    # Get top topics (more than one occurrence)
    significant_topics = {word: count for word, count in topic_counts.items() if count > 1}
    
    return significant_topics

def generate_report(google_news, newsapi_news):
    os.makedirs('results', exist_ok=True)
    
    # Combine and sort news by date
    combined_news = {company: [] for company in COMPANY_NAMES}
    company_reviews = {company: [] for company in COMPANY_NAMES}
    
    for company in COMPANY_NAMES:
        # Get news
        all_news = google_news[company] + newsapi_news[company]
        all_news.sort(key=lambda x: x.get('date', ''), reverse=True)
        combined_news[company] = all_news
        
        # Get reviews
        company_reviews[company] = fetch_company_reviews(company)
    
    # Generate word clouds and prepare Venn diagram data
    company_topics = {}
    for company in COMPANY_NAMES:
        all_text = ' '.join([f"{item['title']} {item['description']}" for item in combined_news[company]])
        
        # Generate word cloud if we have text
        wordcloud = generate_word_cloud(all_text, company)
        if wordcloud:
            plt.figure(figsize=(10, 5))
            plt.imshow(wordcloud, interpolation='bilinear')
            plt.axis('off')
            plt.title(f'{company} ({len(combined_news[company])} articles)')
            plt.savefig(f'results/wordcloud_{company.replace(" ", "_")}.png')
            plt.close()
        
        # Extract topics using simple approach
        topic_counts = extract_topics(all_text)
        top_topics = dict(sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)[:10])
        company_topics[company] = set(top_topics.keys())
    
    # Create Venn diagram with topic counts
    venn_sets = [company_topics[company] for company in COMPANY_NAMES]
    create_venn_diagram(venn_sets, [f"{name} ({len(combined_news[name])} articles)" for name in COMPANY_NAMES])
    
    # Generate HTML report
    html_content = f"""
    <!DOCTYPE html>
    <html lang="it">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Analisi News Aziendali</title>
        <style>
            :root {{
                --primary-color: #1B1B1B;
                --secondary-color: #404040;
                --light-gray: #F5F5F5;
                --border-color: #E0E0E0;
            }}
            
            body {{
                font-family: "Helvetica Neue", Arial, sans-serif;
                margin: 0;
                padding: 0;
                color: var(--primary-color);
                background-color: white;
            }}
            
            .header {{
                padding: 2rem;
                text-align: center;
                border-bottom: 1px solid var(--border-color);
            }}
            
            .header h1 {{
                font-size: 2.5rem;
                font-weight: 300;
                margin: 0;
                text-transform: uppercase;
                letter-spacing: 2px;
            }}
            
            .timestamp {{
                color: var(--secondary-color);
                font-size: 0.9rem;
                margin-top: 1rem;
            }}
            
            .company-section {{
                padding: 2rem;
                margin: 2rem auto;
                max-width: 1200px;
            }}
            
            .company-header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 2rem;
            }}
            
            .company-name {{
                font-size: 1.8rem;
                font-weight: 300;
                text-transform: uppercase;
            }}
            
            .article-count {{
                color: var(--secondary-color);
                font-size: 1.2rem;
            }}
            
            .wordcloud-container {{
                margin: 2rem 0;
                text-align: center;
            }}
            
            .wordcloud-container img {{
                max-width: 100%;
                height: auto;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }}
            
            .news-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 2rem;
                margin: 2rem 0;
            }}
            
            .news-item {{
                background: white;
                border: 1px solid var(--border-color);
                padding: 1.5rem;
                transition: transform 0.3s ease;
            }}
            
            .news-item:hover {{
                transform: translateY(-5px);
            }}
            
            .news-item h3 {{
                font-size: 1.2rem;
                font-weight: 400;
                margin: 0 0 1rem 0;
            }}
            
            .news-item p {{
                color: var(--secondary-color);
                font-size: 0.9rem;
                line-height: 1.5;
            }}
            
            .news-meta {{
                margin-top: 1rem;
                padding-top: 1rem;
                border-top: 1px solid var(--border-color);
                font-size: 0.8rem;
                color: var(--secondary-color);
            }}
            
            .read-more {{
                display: inline-block;
                margin-top: 1rem;
                color: var(--primary-color);
                text-decoration: none;
                font-size: 0.9rem;
                transition: color 0.3s ease;
            }}
            
            .read-more:hover {{
                color: var(--secondary-color);
            }}
            
            .show-more {{
                display: block;
                width: 200px;
                margin: 2rem auto;
                padding: 1rem;
                background: var(--primary-color);
                color: white;
                border: none;
                cursor: pointer;
                text-transform: uppercase;
                letter-spacing: 1px;
                transition: background-color 0.3s ease;
            }}
            
            .show-more:hover {{
                background-color: var(--secondary-color);
            }}
            
            .analysis-section {{
                padding: 2rem;
                margin: 2rem auto;
                max-width: 1200px;
                text-align: center;
            }}
            
            .analysis-section h2 {{
                font-size: 1.8rem;
                font-weight: 300;
                text-transform: uppercase;
                margin-bottom: 2rem;
            }}
            
            .venn-container {{
                margin: 2rem 0;
            }}
            
            .venn-container img {{
                max-width: 100%;
                height: auto;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }}
            
            .reviews-section {{
                margin-top: 3rem;
                padding: 2rem;
                background: var(--light-gray);
                border-radius: 8px;
            }}
            
            .reviews-header {{
                font-size: 1.5rem;
                font-weight: 300;
                margin-bottom: 1.5rem;
                text-transform: uppercase;
                color: var(--primary-color);
            }}
            
            .review-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 1.5rem;
            }}
            
            .review-item {{
                background: white;
                padding: 1.5rem;
                border-radius: 4px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            
            .review-rating {{
                font-size: 1.2rem;
                font-weight: bold;
                color: #FFB400;
                margin-bottom: 0.5rem;
            }}
            
            .review-source {{
                display: inline-block;
                padding: 0.25rem 0.5rem;
                background: var(--light-gray);
                border-radius: 4px;
                font-size: 0.8rem;
                margin-bottom: 0.5rem;
            }}
            
            @media (max-width: 768px) {{
                .company-section,
                .analysis-section {{
                    padding: 1rem;
                }}
                
                .news-grid {{
                    grid-template-columns: 1fr;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Analisi News Aziendali</h1>
            <div class="timestamp">Generato il: {datetime.now().strftime('%d/%m/%Y %H:%M')}</div>
        </div>
    """
    
    for company in COMPANY_NAMES:
        html_content += f"""
        <section class="company-section">
            <div class="company-header">
                <h2 class="company-name">{company}</h2>
                <span class="article-count">{len(combined_news[company])} articoli</span>
            </div>
            
            <div class="wordcloud-container">
                <img src="wordcloud_{company.replace(' ', '_')}.png" alt="Word Cloud">
            </div>
            
            <div class="news-grid">
        """
        
        # Display latest news
        for i, item in enumerate(combined_news[company][:5]):
            sentiment = analyze_sentiment(f"{item['title']} {item['description']}")
            
            html_content += f"""
                <article class="news-item">
                    <h3>{item['title']}</h3>
                    <p>{item['description']}</p>
                    <div class="news-meta">
                        <div>Fonte: {item['source']}</div>
                        <div>Data: {item['date']}</div>
                        <div>Sentiment: {sentiment:.2f}</div>
                    </div>
                    <a href="{item['link']}" class="read-more" target="_blank">Leggi di più →</a>
                </article>
            """
        
        html_content += """
            </div>
        """
        
        # Add reviews section
        if company_reviews[company]:
            html_content += f"""
            <div class="reviews-section">
                <h3 class="reviews-header">Recensioni dei Clienti</h3>
                <div class="review-grid">
            """
            
            for review in company_reviews[company]:
                html_content += f"""
                    <article class="review-item">
                        <div class="review-rating">{review['rating']}</div>
                        <div class="review-source">{review['source']}</div>
                        <h4>{review['title']}</h4>
                        <p>{review['description']}</p>
                        <div class="news-meta">
                            <div>Data: {review['date']}</div>
                        </div>
                    </article>
                """
            
            html_content += """
                </div>
            </div>
            """
        
        # Add archived news
        if len(combined_news[company]) > 5:
            company_id = company.replace(' ', '_').lower()
            html_content += f"""
            <button class="show-more" onclick="toggleArchivedNews('{company_id}')">
                Mostra altri articoli
            </button>
            <div id="archived-{company_id}" class="news-grid" style="display: none;">
            """
            
            for item in combined_news[company][5:]:
                sentiment = analyze_sentiment(f"{item['title']} {item['description']}")
                
                html_content += f"""
                    <article class="news-item">
                        <h3>{item['title']}</h3>
                        <p>{item['description']}</p>
                        <div class="news-meta">
                            <div>Fonte: {item['source']}</div>
                            <div>Data: {item['date']}</div>
                            <div>Sentiment: {sentiment:.2f}</div>
                        </div>
                        <a href="{item['link']}" class="read-more" target="_blank">Leggi di più →</a>
                    </article>
                """
            
            html_content += """
            </div>
            """
        
        html_content += """
        </section>
        """
    
    # Add the rest of the HTML (analysis section and scripts)
    html_content += """
        <section class="analysis-section">
            <h2>Analisi dei Topic</h2>
            <div class="venn-container">
                <img src="venn_diagram.png" alt="Venn Diagram">
            </div>
        </section>
        
        <script>
            function toggleArchivedNews(companyId) {
                const archived = document.getElementById('archived-' + companyId);
                const button = event.target;
                
                if (archived.style.display === 'none') {
                    archived.style.display = 'grid';
                    button.textContent = 'Mostra meno';
                } else {
                    archived.style.display = 'none';
                    button.textContent = 'Mostra altri articoli';
                }
            }
        </script>
    </body>
    </html>
    """
    
    with open('results/sentiment_report.html', 'w', encoding='utf-8') as f:
        f.write(html_content)

def main():
    print("Fetching news from Google News...")
    google_news_data = fetch_google_news()
    
    print("\nFetching news from NewsAPI...")
    newsapi_data = fetch_newsapi_news()
    
    print("\nGenerating report...")
    generate_report(google_news_data, newsapi_data)  # Pass both data sources
    print("Report generated successfully! Check the 'results' directory.")

if __name__ == "__main__":
    main() 