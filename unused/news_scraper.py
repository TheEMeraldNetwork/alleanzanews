import os
import time
from datetime import datetime, timedelta, timezone
import requests
from bs4 import BeautifulSoup
from newspaper import Article
from textblob import TextBlob
import pandas as pd
import logging
from config import *
import warnings
import urllib.parse
import feedparser
import html
import json

# Suppress pandas warnings
warnings.filterwarnings('ignore', category=FutureWarning)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('news_scraper.log'),
        logging.StreamHandler()
    ]
)

class NewsScanner:
    def __init__(self):
        # Specialized insurance news sources
        self.sources = [
            {
                'url': 'https://www.assinews.it/categoria/compagnie/',
                'title_selector': 'h2.entry-title',
                'content_selector': 'div.entry-content',
                'date_selector': 'time.entry-date',
                'link_selector': 'h2.entry-title a'
            },
            {
                'url': 'https://www.insuranceup.it/category/mercato/',
                'title_selector': 'h3.entry-title',
                'content_selector': 'div.entry-content',
                'date_selector': 'time.entry-date',
                'link_selector': 'h3.entry-title a'
            },
            {
                'url': 'https://www.intermediachannel.it/category/compagnie/',
                'title_selector': 'h2.entry-title',
                'content_selector': 'div.entry-content',
                'date_selector': 'time.entry-date',
                'link_selector': 'h2.entry-title a'
            },
            {
                'url': 'https://www.insurancetrade.it/insurance/sezioni/compagnie',
                'title_selector': 'div.title',
                'content_selector': 'div.abstract',
                'date_selector': 'div.date',
                'link_selector': 'div.title a'
            }
        ]
        
        # Company search terms
        self.search_terms = {
            'vita_nuova': [
                'vita nuova', 'vitanuova', 'vita nuova assicurazioni', 
                'vita nuova ass', 'vita-nuova', 'vita nuova spa', 
                'compagnia vita nuova', 'gruppo vita nuova',
                'vita nuova assicurazioni spa', 'vita nuova s.p.a.',
                'vita nuova assicurazione', 'assicurazioni vita nuova',
                'vita nuova group', 'gruppo assicurativo vita nuova'
            ],
            'unidea': [
                'unidea', 'unidea assicurazioni', 'unidea ass', 
                'unidea spa', 'compagnia unidea', 'uni-dea',
                'gruppo unidea', 'unidea assicurazioni spa',
                'unidea s.p.a.', 'compagnia assicurativa unidea',
                'unidea assicurazione', 'assicurazioni unidea',
                'unidea group', 'gruppo assicurativo unidea'
            ],
            'alleanza': [
                'alleanza assicurazioni', 'alleanza', 'alleanza ass',
                'alleanza generali', 'alleanza spa', 'compagnia alleanza',
                'gruppo alleanza', 'alleanza assicurazioni spa',
                'alleanza s.p.a.', 'compagnia assicurativa alleanza',
                'alleanza assicurazione', 'assicurazioni alleanza',
                'alleanza toro', 'gruppo alleanza generali',
                'alleanza group', 'gruppo assicurativo alleanza'
            ]
        }
        
        self.results = {
            'main_companies': [],  # Vita Nuova and Unidea news
            'alleanza': [],       # Alleanza news
            'scan_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'it-IT,it;q=0.8,en-US;q=0.5,en;q=0.3',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0'
        }

    def get_sentiment(self, text):
        try:
            analysis = TextBlob(text)
            score = analysis.sentiment.polarity
            if score > 0.1:
                return 'positive'
            elif score < -0.1:
                return 'negative'
            return 'neutral'
        except:
            return 'neutral'

    def clean_text(self, text):
        """Clean text content"""
        try:
            if not text:
                return ""
            
            # Remove extra whitespace
            text = ' '.join(text.split())
            return text.strip()
            
        except Exception as e:
            print(f"Error cleaning text: {str(e)}")
            return str(text)

    def check_company_mentions(self, text):
        text = text.lower()
        mentions = []
        
        # Check Vita Nuova and Unidea
        for company in ['vita_nuova', 'unidea']:
            if any(term in text for term in self.search_terms[company]):
                if company not in mentions:
                    mentions.append(company)
        
        # Check Alleanza
        if any(term in text for term in self.search_terms['alleanza']):
            mentions.append('alleanza')
        
        return mentions

    def scan_news(self):
        print(f"\nScanning {len(self.sources)} news sites...")
        
        for i, source in enumerate(self.sources, 1):
            try:
                print(f"\nProcessing site {i}/{len(self.sources)}: {source['url']}")
                response = requests.get(source['url'], headers=self.headers, timeout=15)
                
                if response.status_code != 200:
                    print(f"Error: Got status code {response.status_code}")
                    continue
                
                soup = BeautifulSoup(response.content, 'lxml')
                
                # Find all articles
                titles = soup.select(source['title_selector'])
                contents = soup.select(source['content_selector'])
                dates = soup.select(source['date_selector'])
                links = soup.select(source['link_selector'])
                
                print(f"Found {len(titles)} potential articles")
                
                if not titles:
                    print("No articles found with current selectors, trying alternative selectors...")
                    # Try some common alternative selectors
                    titles = soup.select('h2 a, h3 a, .article-title a, .title a')
                    contents = soup.select('.article-content, .content, .article-body, .body')
                    dates = soup.select('.date, .time, .published, .article-date')
                    links = titles  # Links are usually in the title elements
                
                processed = 0
                
                # Process each article
                for title_elem, content_elem, date_elem, link_elem in zip(titles[:20], contents[:20], dates[:20], links[:20]):  # Limit to first 20 articles
                    try:
                        title = self.clean_text(title_elem.text)
                        content = self.clean_text(content_elem.text)
                        date = self.clean_text(date_elem.text)
                        link = link_elem.get('href', '')
                        
                        # Make sure link is absolute
                        if link and not link.startswith('http'):
                            if link.startswith('//'):
                                link = 'https:' + link
                            elif link.startswith('/'):
                                base_url = '/'.join(source['url'].split('/')[:3])
                                link = base_url + link
                            else:
                                link = source['url'].rstrip('/') + '/' + link.lstrip('/')
                        
                        if not (title and content):
                            continue
                        
                        full_text = f"{title} {content}".lower()
                        
                        # Check for company mentions
                        mentions = self.check_company_mentions(full_text)
                        
                        if mentions:
                            news_item = {
                                'title': title,
                                'description': content[:300] + '...' if len(content) > 300 else content,
                                'link': link,
                                'date': date,
                                'source': source['url'],
                                'sentiment': self.get_sentiment(full_text)
                            }
                            
                            # Add to appropriate category
                            if 'alleanza' in mentions:
                                news_item['company'] = 'alleanza'
                                self.results['alleanza'].append(news_item)
                                processed += 1
                                print(f"Found Alleanza article: {title[:100]}...")
                            else:
                                news_item['company'] = 'main_companies'
                                self.results['main_companies'].append(news_item)
                                processed += 1
                                print(f"Found article about {', '.join(mentions)}: {title[:100]}...")
                    
                    except Exception as e:
                        print(f"Error processing article: {str(e)}")
                        continue
                
                print(f"Processed {processed} relevant articles from this site")
                time.sleep(2)  # Be nice to the servers
                
            except requests.exceptions.RequestException as e:
                print(f"Network error for {source['url']}: {str(e)}")
                continue
            except Exception as e:
                print(f"Error processing {source['url']}: {str(e)}")
                continue
        
        total_articles = len(self.results['main_companies']) + len(self.results['alleanza'])
        print(f"\nScan complete! Found {total_articles} relevant articles:")
        print(f"- {len(self.results['main_companies'])} about Vita Nuova & Unidea")
        print(f"- {len(self.results['alleanza'])} about Alleanza Assicurazioni")

    def generate_html(self):
        print("\nGenerating HTML report...")
        html = """
        <!DOCTYPE html>
        <html lang="it">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Insurance News Results</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    max-width: 1200px;
                    margin: 0 auto;
                    padding: 20px;
                    background: #f5f5f5;
                }
                .container {
                    background: white;
                    padding: 20px;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    margin-bottom: 20px;
                }
                h1, h2 {
                    color: #333;
                    border-bottom: 2px solid #eee;
                    padding-bottom: 10px;
                }
                .news-item {
                    margin-bottom: 20px;
                    padding: 15px;
                    border-left: 4px solid #ddd;
                    background: #f9f9f9;
                }
                .news-item:hover {
                    background: #f0f0f0;
                }
                .news-item h3 {
                    margin: 0 0 10px 0;
                    color: #2c3e50;
                }
                .news-item a {
                    color: #3498db;
                    text-decoration: none;
                }
                .news-item a:hover {
                    text-decoration: underline;
                }
                .sentiment {
                    display: inline-block;
                    padding: 3px 8px;
                    border-radius: 3px;
                    font-size: 0.8em;
                    margin-left: 10px;
                }
                .sentiment.positive { background: #d4edda; color: #155724; }
                .sentiment.negative { background: #f8d7da; color: #721c24; }
                .sentiment.neutral { background: #e2e3e5; color: #383d41; }
                .date {
                    color: #666;
                    font-size: 0.9em;
                }
                .source {
                    color: #666;
                    font-size: 0.9em;
                    margin-top: 5px;
                }
                .scan-info {
                    text-align: center;
                    color: #666;
                    font-style: italic;
                    margin-top: 30px;
                }
                .summary {
                    background: #e8f4f8;
                    padding: 15px;
                    border-radius: 5px;
                    margin-bottom: 20px;
                }
                .summary ul {
                    margin: 10px 0;
                    padding-left: 20px;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Insurance News Results</h1>
                
                <div class="summary">
                    <h3>Summary</h3>
                    <ul>
                        <li>{len(self.results['main_companies'])} articles about Vita Nuova & Unidea</li>
                        <li>{len(self.results['alleanza'])} articles about Alleanza Assicurazioni</li>
                    </ul>
                </div>
                
                <h2>Vita Nuova & Unidea News</h2>
                <div class="news-section">
        """
        
        # Add main companies news
        if self.results['main_companies']:
            for news in self.results['main_companies']:
                html += self._format_news_item(news)
        else:
            html += "<p>No articles found about Vita Nuova or Unidea</p>"
        
        html += """
                </div>
                
                <h2>Alleanza Assicurazioni News</h2>
                <div class="news-section">
        """
        
        # Add Alleanza news
        if self.results['alleanza']:
            for news in self.results['alleanza']:
                html += self._format_news_item(news)
        else:
            html += "<p>No articles found about Alleanza Assicurazioni</p>"
        
        html += f"""
                </div>
            </div>
            <div class="scan-info">
                Scan completed on {self.results['scan_date']}
            </div>
        </body>
        </html>
        """
        
        # Save HTML file
        with open('insurance_news.html', 'w', encoding='utf-8') as f:
            f.write(html)
        
        # Also save raw data as JSON for potential further processing
        with open('insurance_news.json', 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        
        print("Report generated! Check insurance_news.html for results")

    def _format_news_item(self, news):
        return f"""
            <div class="news-item">
                <h3>
                    <a href="{news['link']}" target="_blank">{news['title']}</a>
                    <span class="sentiment {news['sentiment']}">{news['sentiment']}</span>
                </h3>
                <p>{news['description']}</p>
                <div class="date">{news['date']}</div>
                <div class="source">Source: {news['source']}</div>
            </div>
        """

if __name__ == "__main__":
    scanner = NewsScanner()
    print("Starting news scan...")
    scanner.scan_news()
    print("Generating HTML report...")
    scanner.generate_html()
    print("Done! Check insurance_news.html for results") 