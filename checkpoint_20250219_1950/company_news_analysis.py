import os
import json
from datetime import datetime, timedelta
from collections import Counter
from GoogleNews import GoogleNews
import requests
from bs4 import BeautifulSoup
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import matplotlib_venn
from textblob import TextBlob
import nltk
from config import COMPANY_NAMES, COMPANY_VARIATIONS, NEWS_SEARCH
import pandas as pd
from PIL import Image
import numpy as np
from dotenv import load_dotenv

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

def fetch_google_news():
    news_data = {company: [] for company in COMPANY_NAMES}
    
    for company in COMPANY_NAMES:
        try:
            # Initialize GoogleNews
            googlenews = GoogleNews()
            googlenews.set_lang(NEWS_SEARCH['language'])
            googlenews.set_period('7d')  # Last 7 days
            
            # Search for news
            print(f"Searching news for: {company}")
            googlenews.search(company)
            results = googlenews.result()
            
            if results:
                print(f"Found {len(results)} results for {company}")
            
            for item in results:
                try:
                    # Get the text content
                    title = str(item.get('title', '')).lower()
                    desc = str(item.get('desc', '')).lower()
                    
                    # Clean the URL
                    link = clean_google_news_url(str(item.get('link', '#')))
                    
                    # Check if the article mentions the company or its variations
                    if any(var.lower() in title or var.lower() in desc
                          for var in [company] + COMPANY_VARIATIONS.get(company, [])):
                        news_data[company].append({
                            'title': str(item.get('title', 'No title available')),
                            'description': str(item.get('desc', 'No description available')),
                            'link': link,
                            'date': str(item.get('datetime', 'No date available')),
                            'source': 'Google News'
                        })
                except Exception as e:
                    print(f"Error processing news item for {company}: {str(e)}")
                    continue
                    
            # Clear search results for next company
            googlenews.clear()
            
        except Exception as e:
            print(f"Error fetching news for {company}: {str(e)}")
            continue
    
    return news_data

def fetch_newsapi_news():
    news_data = {company: [] for company in COMPANY_NAMES}
    
    for company in COMPANY_NAMES:
        url = f"https://newsapi.org/v2/everything?q={company}&language={NEWS_SEARCH['language']}&sortBy=publishedAt&apiKey={NEWS_API_KEY}"
        response = requests.get(url)
        
        if response.status_code == 200:
            articles = response.json().get('articles', [])
            for article in articles:
                if any(var.lower() in article['title'].lower() or var.lower() in article['description'].lower() 
                      for var in [company] + COMPANY_VARIATIONS.get(company, [])):
                    news_data[company].append({
                        'title': article['title'],
                        'description': article['description'],
                        'link': article['url'],
                        'date': article['publishedAt'],
                        'source': 'NewsAPI'
                    })
    
    return news_data

def analyze_sentiment(text):
    blob = TextBlob(text)
    return blob.sentiment.polarity

def generate_word_cloud(text, min_word_length=5):
    # Filter words with at least 5 letters
    words = ' '.join([word for word in text.split() if len(word) >= min_word_length])
    wordcloud = WordCloud(width=800, height=400, background_color='white', min_word_length=min_word_length).generate(words)
    return wordcloud

def create_venn_diagram(sets, labels):
    plt.figure(figsize=(15, 10))
    
    # Create the Venn diagram
    venn = matplotlib_venn.venn3(sets, labels)
    plt.title("Topic Overlap Between Companies")
    
    # Calculate intersections and unique words
    all_intersections = {
        '100': sets[0] - sets[1] - sets[2],  # Unique to first company
        '010': sets[1] - sets[0] - sets[2],  # Unique to second company
        '001': sets[2] - sets[0] - sets[1],  # Unique to third company
        '110': sets[0] & sets[1] - sets[2],  # Overlap between first and second
        '101': sets[0] & sets[2] - sets[1],  # Overlap between first and third
        '011': sets[1] & sets[2] - sets[0],  # Overlap between second and third
        '111': sets[0] & sets[1] & sets[2]   # Overlap between all three
    }
    
    # Add text boxes with word lists
    bbox_props = dict(boxstyle="round,pad=0.3", fc="white", ec="gray", alpha=0.8)
    
    # Position for text boxes
    positions = {
        '100': (-0.5, 0.5),   # Left
        '010': (0.5, 0.5),    # Right
        '001': (0, -0.5),     # Bottom
        '110': (0, 0.7),      # Top
        '101': (-0.3, -0.3),  # Bottom left
        '011': (0.3, -0.3),   # Bottom right
        '111': (0, 0)         # Center
    }
    
    # Add text boxes with top words from each section
    for region, words in all_intersections.items():
        if words:
            # Get top 5 words
            top_words = list(words)[:5]
            word_text = '\n'.join(top_words)
            
            # Create label based on region
            if region == '100':
                label = f"Only in {labels[0]}:"
            elif region == '010':
                label = f"Only in {labels[1]}:"
            elif region == '001':
                label = f"Only in {labels[2]}:"
            elif region == '110':
                label = f"In {labels[0]} & {labels[1]}:"
            elif region == '101':
                label = f"In {labels[0]} & {labels[2]}:"
            elif region == '011':
                label = f"In {labels[1]} & {labels[2]}:"
            else:
                label = "In all companies:"
            
            # Add text box
            pos_x, pos_y = positions[region]
            plt.annotate(f"{label}\n{word_text}",
                        xy=(pos_x, pos_y), xycoords='axes fraction',
                        bbox=bbox_props, ha='center', va='center',
                        fontsize=8)
    
    plt.savefig('results/venn_diagram.png', bbox_inches='tight', dpi=300)
    plt.close()

def generate_report(google_news, newsapi_news):
    # Create results directory if it doesn't exist
    os.makedirs('results', exist_ok=True)
    
    # Combine news from both sources
    combined_news = {company: google_news[company] + newsapi_news[company] for company in COMPANY_NAMES}
    
    # Generate word clouds
    for company in COMPANY_NAMES:
        text = ' '.join([f"{item['title']} {item['description']}" for item in combined_news[company]])
        wordcloud = generate_word_cloud(text)
        plt.figure(figsize=(10, 5))
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis('off')
        plt.title(f'Word Cloud - {company}')
        plt.savefig(f'results/wordcloud_{company.replace(" ", "_")}.png')
        plt.close()
    
    # Prepare Venn diagram data
    company_words = {}
    for company in COMPANY_NAMES:
        text = ' '.join([f"{item['title']} {item['description']}" for item in combined_news[company]])
        words = set(word.lower() for word in text.split() if len(word) >= 5)
        company_words[company] = words
    
    venn_sets = [company_words[company] for company in COMPANY_NAMES]
    create_venn_diagram(venn_sets, COMPANY_NAMES)
    
    # Generate HTML report
    html_content = f"""
    <html>
    <head>
        <title>Company News Analysis Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .news-item {{ margin-bottom: 20px; padding: 10px; border: 1px solid #ddd; }}
            .positive {{ background-color: #e6ffe6; }}
            .negative {{ background-color: #ffe6e6; }}
            .neutral {{ background-color: #f5f5f5; }}
            img {{ max-width: 100%; height: auto; margin: 20px 0; }}
        </style>
    </head>
    <body>
        <h1>Company News Analysis Report</h1>
        <p>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    """
    
    for company in COMPANY_NAMES:
        html_content += f"<h2>{company}</h2>"
        html_content += f"<img src='wordcloud_{company.replace(' ', '_')}.png' alt='Word Cloud'><br>"
        
        for item in combined_news[company]:
            sentiment = analyze_sentiment(f"{item['title']} {item['description']}")
            sentiment_class = 'positive' if sentiment > 0.1 else 'negative' if sentiment < -0.1 else 'neutral'
            
            html_content += f"""
            <div class="news-item {sentiment_class}">
                <h3>{item['title']}</h3>
                <p>{item['description']}</p>
                <p>Source: {item['source']} | Date: {item['date']}</p>
                <p>Sentiment Score: {sentiment:.2f}</p>
                <a href="{item['link']}" target="_blank">Read more</a>
            </div>
            """
    
    html_content += """
        <h2>Topic Overlap Analysis</h2>
        <img src='venn_diagram.png' alt='Venn Diagram'>
    </body>
    </html>
    """
    
    with open('results/sentiment_report.html', 'w', encoding='utf-8') as f:
        f.write(html_content)

def main():
    print("Fetching news from Google News...")
    google_news = fetch_google_news()
    
    print("Fetching news from NewsAPI...")
    newsapi_news = fetch_newsapi_news()
    
    print("Generating report...")
    generate_report(google_news, newsapi_news)
    print("Report generated successfully! Check the 'results' directory.")

if __name__ == "__main__":
    main() 