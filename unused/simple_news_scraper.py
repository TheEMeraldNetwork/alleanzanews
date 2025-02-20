import requests
from bs4 import BeautifulSoup, Comment
from datetime import datetime
import time
from textblob import TextBlob
import json
import re

class SimpleNewsScanner:
    def __init__(self):
        # Simple list of Italian news sources
        self.sources = [
            'https://www.ansa.it/sito/notizie/economia/economia_rss.xml',
            'https://www.assinews.it/feed/',
            'https://www.insuranceup.it/feed/',
            'https://www.ilsole24ore.com/rss/finanza.xml',
            'https://www.borsaitaliana.it/borsa/notizie/radiocor/finanza/rss.xml',
            'https://www.teleborsa.it/feed/news',
            'https://www.soldionline.it/feed',
            'https://www.wallstreetitalia.com/feed/',
            'https://www.trend-online.com/feed/',
            'https://www.investireoggi.it/feed/'
        ]
        
        self.companies = {
            'vita_nuova': [
                'vita nuova', 'vitanuova', 'vita nuova assicurazioni', 
                'vita nuova ass', 'vita-nuova', 'vita nuova spa', 
                'compagnia vita nuova', 'gruppo vita nuova',
                'vita nuova assicurazioni spa', 'vita nuova s.p.a.',
                'vita nuova assicurazione', 'assicurazioni vita nuova'
            ],
            'unidea': [
                'unidea', 'unidea assicurazioni', 'unidea ass', 
                'unidea spa', 'compagnia unidea', 'uni-dea',
                'gruppo unidea', 'unidea assicurazioni spa',
                'unidea s.p.a.', 'compagnia assicurativa unidea',
                'unidea assicurazione', 'assicurazioni unidea'
            ],
            'alleanza': [
                'alleanza assicurazioni', 'alleanza', 'alleanza ass',
                'alleanza generali', 'alleanza spa', 'compagnia alleanza',
                'gruppo alleanza', 'alleanza assicurazioni spa',
                'alleanza s.p.a.', 'compagnia assicurativa alleanza',
                'alleanza assicurazione', 'assicurazioni alleanza',
                'alleanza toro', 'gruppo alleanza generali'
            ]
        }
        
        self.results = {
            'main_companies': [],  # Vita Nuova and Unidea news
            'alleanza': [],       # Alleanza news
            'scan_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

    def clean_html_content(self, html_content):
        """Clean HTML content and extract text"""
        try:
            if not html_content:
                return ""
            
            # If content is a list of dictionaries with 'value' key, get the value
            if isinstance(html_content, list) and len(html_content) > 0 and isinstance(html_content[0], dict):
                html_content = html_content[0].get('value', '')
            
            # Convert to string if not already
            if not isinstance(html_content, str):
                html_content = str(html_content)
            
            # Remove common RSS/HTML artifacts
            html_content = html_content.replace('[CDATA[', '').replace(']]>', '')
            
            # Create BeautifulSoup object with lxml parser
            soup = BeautifulSoup(html_content, 'lxml')
            
            # Remove script, style, and iframe elements
            for element in soup(['script', 'style', 'iframe']):
                element.decompose()
            
            # Remove all HTML comments
            for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
                comment.extract()
            
            # Get text and clean whitespace
            text = soup.get_text(separator=' ')
            text = ' '.join(text.split())
            
            # Remove URLs
            text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
            
            # Clean up extra whitespace and punctuation
            text = re.sub(r'\s+', ' ', text)
            text = re.sub(r'[^\w\s.,!?-]', '', text)
            text = text.strip()
            
            return text
        except Exception as e:
            print(f"Error cleaning HTML content: {str(e)}")
            return str(html_content)

    def scan_news(self):
        print(f"\nScanning {len(self.sources)} news sources...")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        for i, source in enumerate(self.sources, 1):
            try:
                print(f"\nProcessing source {i}/{len(self.sources)}: {source}")
                response = requests.get(source, headers=headers, timeout=10)
                
                if response.status_code != 200:
                    print(f"Error: Got status code {response.status_code}")
                    continue
                
                # Try different parsers if the first one fails
                for parser in ['xml', 'lxml', 'html.parser']:
                    try:
                        soup = BeautifulSoup(response.content, parser)
                        items = soup.find_all(['item', 'entry'])
                        if items:
                            break
                    except:
                        continue
                
                if not items:
                    print("No news items found")
                    continue
                
                print(f"Found {len(items)} news items")
                processed = 0
                
                for item in items:
                    try:
                        # Get title
                        title = ''
                        title_elem = item.find('title')
                        if title_elem:
                            title = self.clean_html_content(title_elem.text)
                        
                        # Get description/content
                        description = ''
                        for desc_tag in ['description', 'summary', 'content', 'content:encoded']:
                            desc_elem = item.find(desc_tag)
                            if desc_elem:
                                description = self.clean_html_content(desc_elem.text)
                                if description:
                                    break
                        
                        # Get link
                        link = ''
                        link_elem = item.find('link')
                        if link_elem:
                            link = link_elem.text if link_elem.text else link_elem.get('href', '')
                        
                        # Get date
                        pub_date = ''
                        for date_tag in ['pubDate', 'published', 'updated', 'dc:date']:
                            date_elem = item.find(date_tag)
                            if date_elem:
                                pub_date = date_elem.text
                                break
                        
                        if not (title or description):
                            continue
                        
                        content = f"{title} {description}".lower()
                        
                        # Check for company mentions
                        news_item = {
                            'title': title,
                            'description': description[:300] + '...' if len(description) > 300 else description,
                            'link': link,
                            'date': pub_date,
                            'sentiment': self.get_sentiment(content)
                        }
                        
                        # Check main companies (Vita Nuova and Unidea)
                        for company, variations in list(self.companies.items())[:2]:
                            if any(var.lower() in content for var in variations):
                                news_item['company'] = company
                                self.results['main_companies'].append(news_item)
                                processed += 1
                                print(f"Found article about {company}: {title[:50]}...")
                                break
                        
                        # Check Alleanza separately
                        if any(var.lower() in content for var in self.companies['alleanza']):
                            news_item['company'] = 'alleanza'
                            self.results['alleanza'].append(news_item)
                            processed += 1
                            print(f"Found article about Alleanza: {title[:50]}...")
                    
                    except Exception as e:
                        print(f"Error processing news item: {str(e)}")
                        continue
                
                print(f"Processed {processed} relevant articles from this source")
                time.sleep(1)  # Reduced delay to be more responsive
                
            except requests.exceptions.RequestException as e:
                print(f"Network error for {source}: {str(e)}")
                continue
            except Exception as e:
                print(f"Error processing {source}: {str(e)}")
                continue
        
        total_articles = len(self.results['main_companies']) + len(self.results['alleanza'])
        print(f"\nScan complete! Found {total_articles} relevant articles:")
        print(f"- {len(self.results['main_companies'])} about Vita Nuova & Unidea")
        print(f"- {len(self.results['alleanza'])} about Alleanza Assicurazioni")

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

    def generate_html(self):
        print("\nGenerating HTML report...")
        html = """
        <!DOCTYPE html>
        <html lang="it">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>News Scanner Results</title>
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
                <h1>News Scanner Results</h1>
                
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
        with open('news_results.html', 'w', encoding='utf-8') as f:
            f.write(html)
        
        # Also save raw data as JSON for potential further processing
        with open('news_results.json', 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        
        print("Report generated! Check news_results.html for results")

    def _format_news_item(self, news):
        return f"""
            <div class="news-item">
                <h3>
                    <a href="{news['link']}" target="_blank">{news['title']}</a>
                    <span class="sentiment {news['sentiment']}">{news['sentiment']}</span>
                </h3>
                <p>{news['description']}</p>
                <div class="date">{news['date']}</div>
            </div>
        """

if __name__ == "__main__":
    scanner = SimpleNewsScanner()
    print("Scanning news sources...")
    scanner.scan_news()
    print("Generating HTML report...")
    scanner.generate_html()
    print("Done! Check news_results.html for results") 