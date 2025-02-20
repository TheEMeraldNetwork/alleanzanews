from GoogleNews import GoogleNews
import requests
from bs4 import BeautifulSoup
import webbrowser
import os
from datetime import datetime, timedelta
import urllib.parse
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import matplotlib_venn
from matplotlib_venn import venn3
import io
import base64
from textblob import TextBlob
from collections import Counter
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import time
import random
from config import TARGET_URLS, COMPANY_VARIATIONS
import feedparser

class NewsScanner:
    def __init__(self):
        # User agents rotation first
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15'
        ]

        # Then initialize other attributes
        self.companies = [
            "VitaNuova Assicurazioni",
            "Unidea Assicurazioni",
            "Alleanza Assicurazioni"
        ]
        self.article_counts = {}
        self.word_clouds = {}
        self.top_topics = {}
        self.articles = {}
        
        # Load company variations from config
        self.company_variations = COMPANY_VARIATIONS
        
        # RSS feeds and direct URLs
        self.news_sources = {
            'assinews': {
                'rss': 'https://www.assinews.it/feed/',
                'search': 'https://www.assinews.it/?s={}'
            },
            'insurancetrade': {
                'rss': 'https://www.insurancetrade.it/insurance/rss/rss.xml',
                'search': 'https://www.insurancetrade.it/insurance/ricerca?q={}'
            },
            'intermediachannel': {
                'rss': None,
                'search': 'https://www.intermediachannel.it/?s={}'
            },
            'ansa_economia': {
                'rss': 'https://www.ansa.it/sito/notizie/economia/economia_rss.xml',
                'search': 'https://www.ansa.it/ricerca/ansait/search.shtml?query={}'
            },
            'ilsole24ore': {
                'rss': 'https://www.ilsole24ore.com/rss/economia.xml',
                'search': 'https://www.ilsole24ore.com/ricerca?q={}'
            },
            'alleanza': {
                'press': 'https://www.alleanza.it/contenuti/sala-stampa/'
            }
        }
        
        # Initialize feedparser with user agent
        feedparser.USER_AGENT = random.choice(self.user_agents)
        
        # Download required NLTK data
        try:
            nltk.data.find('tokenizers/punkt')
            nltk.data.find('corpora/stopwords')
        except LookupError:
            nltk.download('punkt')
            nltk.download('stopwords')
        
        # Combine Italian and English stopwords
        self.stop_words = set(stopwords.words('italian') + stopwords.words('english'))
        self.stop_words.update([
            'della', 'delle', 'degli', 'dell', 'dal', 'dalla', 'dai', 'dagli', 
            'del', 'alla', 'alle', 'agli', 'allo', 'nell', 'nella', 'nelle', 
            'negli', 'sul', 'sulla', 'sulle', 'sugli', 'con', 'per', 'tra',
            'fra', 'presso', 'dopo', 'prima', 'durante', 'oltre', 'attraverso',
            'mediante', 'tramite', 'verso', 'fino', 'assicurazioni', 'assicurazione',
            'company', 'companies', 'group', 'gruppo', 'società'
        ])

    def fetch_rss_feed(self, feed_url):
        """Fetch and parse an RSS feed."""
        try:
            feed = feedparser.parse(feed_url)
            return feed.entries
        except Exception as e:
            print(f"    Error fetching RSS feed: {str(e)}")
            return []

    def scrape_search_page(self, url, company):
        """Scrape a website's search results page with retry logic."""
        max_retries = 3
        base_delay = 5
        
        for attempt in range(max_retries):
            try:
                headers = {
                    'User-Agent': random.choice(self.user_agents),
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7',
                    'Cache-Control': 'no-cache',
                    'Pragma': 'no-cache'
                }
                
                # Add delay between attempts
                if attempt > 0:
                    delay = base_delay * (2 ** attempt)
                    print(f"    Retrying in {delay} seconds (attempt {attempt + 1}/{max_retries})...")
                    time.sleep(delay)
                
                response = requests.get(url.format(urllib.parse.quote(company)), headers=headers, timeout=15)
                
                # Handle different status codes
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    results = []
                    
                    # Common article selectors
                    article_selectors = [
                        '.post', '.article', '.news-item', 
                        'article', '.entry', '.risultato',
                        '.search-result', '.news-article',
                        '.search-results li', '.news-list li',
                        '.content-list-item'
                    ]
                    
                    for selector in article_selectors:
                        articles = soup.select(selector)
                        if articles:
                            for article in articles:
                                title_elem = article.find(['h1', 'h2', 'h3', 'h4', 'a'])
                                link_elem = article.find('a')
                                desc_elem = article.find(['p', '.excerpt', '.description', '.summary'])
                                
                                if title_elem and link_elem:
                                    title = title_elem.get_text().strip()
                                    link = link_elem.get('href', '')
                                    desc = desc_elem.get_text().strip() if desc_elem else ''
                                    
                                    if link.startswith('/'):
                                        parsed_url = urllib.parse.urlparse(url)
                                        link = f"{parsed_url.scheme}://{parsed_url.netloc}{link}"
                                    elif not link.startswith('http'):
                                        continue
                                    
                                    if title and link:
                                        results.append({
                                            'title': title,
                                            'link': link,
                                            'desc': desc
                                        })
                    
                    if results:
                        return results
                    continue  # Try next selector if no results
                    
                elif response.status_code in [429, 503, 520]:  # Rate limit or service unavailable
                    if attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt)
                        print(f"    Rate limited/Service unavailable, waiting {delay} seconds...")
                        time.sleep(delay)
                        continue
                    else:
                        print(f"    Max retries reached for {url}")
                        return []
                elif response.status_code == 404:
                    print(f"    Page not found: {url}")
                    return []
                else:
                    print(f"    Unexpected status code: {response.status_code}")
                    if attempt < max_retries - 1:
                        continue
                    return []
                    
            except requests.exceptions.Timeout:
                print(f"    Request timed out")
                if attempt < max_retries - 1:
                    continue
                return []
            except requests.exceptions.RequestException as e:
                print(f"    Request error: {str(e)}")
                if attempt < max_retries - 1:
                    continue
                return []
            except Exception as e:
                print(f"    Error scraping page: {str(e)}")
                if attempt < max_retries - 1:
                    continue
                return []
        
        return []

    def search_company_news(self, company):
        """Search news for a company using RSS feeds and direct website scraping."""
        print(f'\nSearching news for {company}...')
        verified_results = []
        seen_titles = set()
        
        # Get company variations
        variations = self.company_variations.get(company, [company])
        variations.append(company)  # Add the original name
        
        # Special handling for Alleanza Assicurazioni press releases
        if company == "Alleanza Assicurazioni":
            print("  Checking Alleanza press releases...")
            try:
                headers = {'User-Agent': random.choice(self.user_agents)}
                response = requests.get(self.news_sources['alleanza']['press'], headers=headers)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    press_items = soup.select('.press-item, .news-item, article')
                    
                    for item in press_items:
                        title_elem = item.find(['h1', 'h2', 'h3', 'h4'])
                        link_elem = item.find('a')
                        desc_elem = item.find(['p', '.excerpt', '.description'])
                        
                        if title_elem and link_elem:
                            title = title_elem.get_text().strip()
                            link = link_elem.get('href', '')
                            desc = desc_elem.get_text().strip() if desc_elem else ''
                            
                            if title and link and title not in seen_titles:
                                verified_results.append({
                                    'title': title,
                                    'link': link,
                                    'desc': desc,
                                    'date': ''
                                })
                                seen_titles.add(title)
            except Exception as e:
                print(f"    Error fetching press releases: {str(e)}")
        
        # Check RSS feeds first
        for source_name, source_info in self.news_sources.items():
            if source_info.get('rss'):
                print(f"  Checking {source_name} RSS feed...")
                entries = self.fetch_rss_feed(source_info['rss'])
                
                for entry in entries:
                    title = entry.get('title', '')
                    link = entry.get('link', '')
                    desc = entry.get('description', '')
                    
                    # Check if article mentions any company variation
                    if any(var.lower() in title.lower() or var.lower() in desc.lower() 
                          for var in variations):
                        if title and link and title not in seen_titles:
                            if self.validate_link(link):
                                verified_results.append({
                                    'title': title,
                                    'desc': desc,
                                    'link': link,
                                    'date': entry.get('published', '')
                                })
                                seen_titles.add(title)
                                print(f"    ✓ Found article: {title[:50]}...")
            
            # Then try search pages
            if source_info.get('search'):
                print(f"  Searching {source_name} website...")
                time.sleep(random.uniform(2, 4))  # Delay between searches
                
                for variation in variations:
                    results = self.scrape_search_page(source_info['search'], variation)
                    
                    for result in results:
                        title = result.get('title')
                        link = result.get('link')
                        desc = result.get('desc', '')
                        
                        if title and link and title not in seen_titles:
                            if self.validate_link(link):
                                verified_results.append({
                                    'title': title,
                                    'desc': desc,
                                    'link': link,
                                    'date': ''
                                })
                                seen_titles.add(title)
                                print(f"    ✓ Found article: {title[:50]}...")
                    
                    if len(verified_results) >= 5:
                        break
                
                if len(verified_results) >= 5:
                    break
        
        actual_count = len(verified_results)
        print(f'  Found {actual_count} valid articles')
        
        # Store article count and results
        self.article_counts[company] = actual_count
        self.articles[company] = verified_results
        
        # Extract texts for topic analysis
        texts = [f"{r['title']} {r.get('desc', '')}" for r in verified_results]
        
        if texts:
            print("  Analyzing topics...")
            self.top_topics[company] = self.extract_topics(texts)
            
            # Generate word cloud
            text = " ".join(texts)
            if text.strip():
                print("  Generating word cloud...")
                cleaned_text = self.clean_text_for_wordcloud(text, company)
                if cleaned_text.strip():
                    wordcloud = WordCloud(width=400, height=200,
                                        background_color='white',
                                        min_word_length=4,
                                        collocations=False
                                        ).generate(cleaned_text)
                    
                    img_buffer = io.BytesIO()
                    plt.figure(figsize=(4, 2))
                    plt.imshow(wordcloud, interpolation='bilinear')
                    plt.axis('off')
                    plt.tight_layout(pad=0)
                    plt.savefig(img_buffer, format='png', bbox_inches='tight')
                    plt.close()
                    img_buffer.seek(0)
                    self.word_clouds[company] = base64.b64encode(img_buffer.getvalue()).decode()
                else:
                    print("  No words remained for word cloud")
                    self.word_clouds[company] = None
            else:
                print("  No text available for word cloud")
                self.word_clouds[company] = None
        else:
            print("  No articles found for topic analysis and word cloud")
            self.top_topics[company] = []
            self.word_clouds[company] = None
        
        return verified_results

    def search_combined_news(self, company1, company2):
        """Search for news mentioning both companies using direct website scraping."""
        print(f"\nSearching for articles mentioning both {company1} and {company2}...")
        verified_results = []
        seen_titles = set()
        
        # Get company variations
        variations1 = self.company_variations.get(company1, [company1])
        variations1.append(company1)
        variations2 = self.company_variations.get(company2, [company2])
        variations2.append(company2)
        
        # Check RSS feeds first
        for source_name, source_info in self.news_sources.items():
            if source_info.get('rss'):
                print(f"  Checking {source_name} RSS feed...")
                entries = self.fetch_rss_feed(source_info['rss'])
                
                for entry in entries:
                    title = entry.get('title', '')
                    link = entry.get('link', '')
                    desc = entry.get('description', '')
                    
                    # Check if article mentions both companies
                    text = f"{title} {desc}".lower()
                    if (any(var.lower() in text for var in variations1) and 
                        any(var.lower() in text for var in variations2)):
                        if title and link and title not in seen_titles:
                            if self.validate_link(link):
                                verified_results.append({
                                    'title': title,
                                    'desc': desc,
                                    'link': link,
                                    'date': entry.get('published', '')
                                })
                                seen_titles.add(title)
                                print(f"    ✓ Found article: {title[:50]}...")
        
            # Then try search pages
            if source_info.get('search'):
                print(f"  Searching {source_name} website...")
                time.sleep(random.uniform(2, 4))  # Delay between searches
                
                # Try searching for each combination of variations
                for var1 in variations1:
                    for var2 in variations2:
                        query = f"{var1} {var2}"
                        results = self.scrape_search_page(source_info['search'], query)
                        
                        for result in results:
                            title = result.get('title')
                            link = result.get('link')
                            desc = result.get('desc', '')
                            
                            # Verify both companies are mentioned
                            text = f"{title} {desc}".lower()
                            if (any(var.lower() in text for var in variations1) and 
                                any(var.lower() in text for var in variations2)):
                                if title and link and title not in seen_titles:
                                    if self.validate_link(link):
                                        verified_results.append({
                                            'title': title,
                                            'desc': desc,
                                            'link': link,
                                            'date': ''
                                        })
                                        seen_titles.add(title)
                                        print(f"    ✓ Found article: {title[:50]}...")
                        
                        if len(verified_results) >= 5:
                            break
                    
                    if len(verified_results) >= 5:
                        break
        
        print(f"  Found {len(verified_results)} valid articles")
        return verified_results

    def clean_text_for_wordcloud(self, text, company):
        # Simple tokenization using split
        words = text.lower().split()
        # Remove company name words, stop words, and short words
        company_words = set(company.lower().split())
        # For VitaNuova, also add individual parts
        if "vitanuova" in company.lower():
            company_words.update(["vita", "nuova"])
        
        filtered_words = [
            word.strip('.,!?()[]{}":;') for word in words 
            if len(word) >= 4 and  # Only words with 4+ letters
            word.strip('.,!?()[]{}":;').isalpha() and  # Only alphabetic words
            word not in company_words and  # Remove company name words
            word not in self.stop_words  # Remove stop words
        ]
        
        # Count word frequencies and get top 20
        word_freq = Counter(filtered_words)
        top_words = [word for word, _ in word_freq.most_common(20)]
        return " ".join(top_words)

    def extract_topics(self, texts):
        """Extract main topics from a list of texts using semantic analysis"""
        # Combine all texts
        combined_text = " ".join(texts)
        
        # Define detailed topic categories with related terms
        topic_categories = {
            'Environmental': ['sostenibilità', 'ambiente', 'green', 'climate', 'energia', 'rinnovabile', 'emissioni', 'riciclo'],
            'Digital Innovation': ['innovazione', 'digitale', 'tecnologia', 'digital', 'startup', 'intelligenza', 'app', 'online'],
            'Investment': ['finanza', 'investimenti', 'risparmio', 'mercato', 'economia', 'finanziario', 'borsa', 'trading'],
            'Health Services': ['salute', 'sanitario', 'benessere', 'prevenzione', 'medico', 'assistenza', 'clinica', 'terapia'],
            'Community Support': ['sociale', 'comunità', 'welfare', 'solidarietà', 'inclusione', 'diversity', 'volontariato', 'donazioni'],
            'Business Growth': ['business', 'strategia', 'partnership', 'crescita', 'sviluppo', 'mercato', 'espansione', 'acquisizione'],
            'Customer Service': ['clienti', 'servizio', 'assistenza', 'supporto', 'soddisfazione', 'qualità', 'esperienza', 'consulenza'],
            'Product Innovation': ['prodotti', 'soluzioni', 'novità', 'lancio', 'offerta', 'polizza', 'copertura', 'protezione'],
            'Market Position': ['leadership', 'competitività', 'posizione', 'quota', 'presenza', 'network', 'distribuzione', 'canali'],
            'Risk Management': ['rischio', 'sicurezza', 'protezione', 'gestione', 'controllo', 'compliance', 'normativa', 'regolamento']
        }
        
        # Count occurrences of topic-related terms
        topic_scores = Counter()
        words = combined_text.lower().split()
        
        for word in words:
            for topic, terms in topic_categories.items():
                if any(term in word for term in terms):
                    topic_scores[topic] += 1
        
        # Get top 3 topics with their scores
        top_topics = topic_scores.most_common(3)
        return [(topic, score) for topic, score in top_topics if score > 0]

    def generate_venn_diagram(self):
        """Generate a Venn diagram showing overlapping news coverage."""
        try:
            # Get combined article counts
            combined_12 = len(self.search_combined_news(self.companies[0], self.companies[1]))
            combined_23 = len(self.search_combined_news(self.companies[1], self.companies[2]))
            combined_13 = len(self.search_combined_news(self.companies[0], self.companies[2]))
            
            # Create sets for Venn diagram
            # Note: We're using approximate set sizes since we can't determine exact overlaps
            sets = (
                self.article_counts[self.companies[0]],  # A
                self.article_counts[self.companies[1]],  # B
                self.article_counts[self.companies[2]],  # C
                combined_12,  # A&B
                combined_23,  # B&C
                combined_13,  # A&C
                min(combined_12, combined_23, combined_13)  # A&B&C (approximated)
            )
            
            # Create Venn diagram
            plt.figure(figsize=(6, 4))
            venn3(subsets=sets, set_labels=self.companies)
            plt.title('News Coverage Overlap')
            
            # Convert to base64 image
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', bbox_inches='tight')
            plt.close()
            img_buffer.seek(0)
            venn_image = base64.b64encode(img_buffer.getvalue()).decode()
            
            # Generate HTML for overlapping articles section
            html = '<div class="overlapping-articles">'
            html += '<h2>Overlapping Coverage</h2>'
            
            # Add Venn diagram
            html += f'<img src="data:image/png;base64,{venn_image}" alt="Venn diagram of news coverage overlap">'
            
            # Add cross-reference links for each pair
            for i, (company1, company2) in enumerate([
                (self.companies[0], self.companies[1]),
                (self.companies[1], self.companies[2]),
                (self.companies[0], self.companies[2])
            ]):
                combined_count = [combined_12, combined_23, combined_13][i]
                html += f"""
                    <div class="stats">
                        Articles mentioning both {company1} and {company2}: {combined_count}
                        <a href="https://news.google.com/search?q={urllib.parse.quote(f'{company1} AND {company2}')}" 
                           class="cross-ref-btn" target="_blank">
                            View Combined Coverage
                        </a>
                    </div>
                """
            
            html += '</div>'
            return html
            
        except Exception as e:
            print(f"Error generating Venn diagram: {str(e)}")
            return ""

    def generate_html(self):
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        venn_diagram = self.generate_venn_diagram()
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Insurance Company News Analysis</title>
            <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;500;600&display=swap" rel="stylesheet">
            <style>
                body {{ 
                    font-family: 'Montserrat', sans-serif;
                    margin: 0;
                    padding: 40px;
                    background-color: #1C2B2B;
                    color: white;
                }}
                .container {{
                    max-width: 1400px;
                    margin: 0 auto;
                    display: grid;
                    grid-template-columns: 2fr 1fr;
                    gap: 40px;
                }}
                .main-content {{
                    display: flex;
                    flex-direction: column;
                    gap: 30px;
                }}
                .sidebar {{
                    position: sticky;
                    top: 40px;
                    height: fit-content;
                }}
                .company-section {{ 
                    background-color: #1C2B2B;
                    padding: 30px;
                    margin-bottom: 30px;
                    position: relative;
                }}
                .company-section::after {{
                    content: '';
                    position: absolute;
                    bottom: 0;
                    left: 30px;
                    right: 30px;
                    height: 1px;
                    background: rgba(255,255,255,0.1);
                }}
                .company-header {{
                    margin-bottom: 20px;
                }}
                .stats {{
                    color: #B8C5C5;
                    font-size: 0.9em;
                    font-weight: 300;
                }}
                .topics {{
                    margin: 20px 0;
                    padding: 15px;
                    background: rgba(255,255,255,0.05);
                }}
                .topic-tag {{
                    display: inline-block;
                    padding: 6px 12px;
                    margin: 4px;
                    background: rgba(255,255,255,0.1);
                    border-radius: 20px;
                    font-size: 0.9em;
                    color: #fff;
                }}
                .topic-score {{
                    font-size: 0.8em;
                    color: #B8C5C5;
                    margin-left: 4px;
                }}
                .wordcloud {{
                    margin: 20px 0;
                    background: rgba(255,255,255,0.05);
                    padding: 20px;
                }}
                .view-news-btn {{ 
                    display: inline-flex;
                    align-items: center;
                    padding: 0;
                    color: white;
                    text-decoration: none;
                    margin-top: 20px;
                    font-size: 0.9em;
                    letter-spacing: 1px;
                    text-transform: uppercase;
                    font-weight: 300;
                    position: relative;
                }}
                .view-news-btn::after {{
                    content: '';
                    position: absolute;
                    width: 0;
                    height: 1px;
                    bottom: -2px;
                    left: 0;
                    background-color: white;
                    transition: width 0.3s ease;
                }}
                .view-news-btn:hover::after {{
                    width: 100%;
                }}
                .view-news-btn .cta {{
                    color: #B8C5C5;
                    font-size: 0.8em;
                    margin-left: 8px;
                    font-weight: 300;
                }}
                .cross-reference {{
                    background: #243535;
                    padding: 30px;
                }}
                h1, h2 {{ 
                    font-weight: 300;
                    letter-spacing: 1px;
                    margin: 0 0 20px 0;
                }}
                h1 {{ font-size: 2.2em; }}
                h2 {{ font-size: 1.8em; }}
                .venn-diagram {{
                    background: #243535;
                    padding: 30px;
                    margin-bottom: 30px;
                }}
                .venn-diagram img {{
                    width: 100%;
                    height: auto;
                }}
                .overlap-details {{
                    margin-top: 20px;
                    padding: 20px;
                    background: rgba(255,255,255,0.05);
                    border-radius: 4px;
                }}
                .overlap-section {{
                    margin: 15px 0;
                }}
                .overlap-title {{
                    font-size: 0.9em;
                    color: #B8C5C5;
                    margin-bottom: 8px;
                }}
                .overlap-topics {{
                    display: flex;
                    flex-wrap: wrap;
                    gap: 8px;
                }}
                .overlap-topic {{
                    background: rgba(255,255,255,0.1);
                    padding: 4px 12px;
                    border-radius: 15px;
                    font-size: 0.85em;
                    cursor: pointer;
                    transition: background-color 0.3s;
                }}
                .overlap-topic:hover {{
                    background: rgba(255,255,255,0.2);
                }}
                .tooltip {{
                    position: relative;
                    display: inline-block;
                }}
                .tooltip .tooltiptext {{
                    visibility: hidden;
                    width: 200px;
                    background-color: rgba(0,0,0,0.9);
                    color: #fff;
                    text-align: center;
                    padding: 5px;
                    border-radius: 4px;
                    position: absolute;
                    z-index: 1;
                    bottom: 125%;
                    left: 50%;
                    transform: translateX(-50%);
                    opacity: 0;
                    transition: opacity 0.3s;
                }}
                .tooltip:hover .tooltiptext {{
                    visibility: visible;
                    opacity: 1;
                }}
                .article-preview {{
                    margin: 25px 0;
                    padding: 0;
                }}
                .article-title {{
                    margin-bottom: 8px;
                }}
                .article-title a {{
                    color: white;
                    text-decoration: none;
                    position: relative;
                    font-size: 1.1em;
                    font-weight: 400;
                    letter-spacing: 0.3px;
                }}
                .article-title a::after {{
                    content: '';
                    position: absolute;
                    width: 0;
                    height: 1px;
                    bottom: -2px;
                    left: 0;
                    background-color: white;
                    transition: width 0.3s ease;
                }}
                .article-title a:hover::after {{
                    width: 100%;
                }}
                .article-desc {{
                    color: #B8C5C5;
                    font-size: 0.85em;
                    line-height: 1.4;
                    margin-bottom: 15px;
                }}
                .cross-ref-btn {{
                    display: inline-block;
                    padding: 0;
                    color: white;
                    text-decoration: none;
                    margin-left: 15px;
                    font-size: 0.9em;
                    letter-spacing: 1px;
                    text-transform: uppercase;
                    font-weight: 300;
                    position: relative;
                }}
                .cross-ref-btn::after {{
                    content: '';
                    position: absolute;
                    width: 0;
                    height: 1px;
                    bottom: -2px;
                    left: 0;
                    background-color: white;
                    transition: width 0.3s ease;
                }}
                .cross-ref-btn:hover::after {{
                    width: 100%;
                }}
                .cross-ref-btn:hover {{
                    color: white;
                }}
            </style>
            <script>
                function searchTopic(topic) {{
                    const searchUrl = `https://news.google.com/search?q=${{encodeURIComponent(topic + ' (VitaNuova OR Unidea OR Alleanza) Assicurazioni')}}&hl=it&gl=IT`;
                    window.open(searchUrl, '_blank');
                }}
            </script>
        </head>
        <body>
            <div class="container">
                <div class="main-content">
                    <h1>Insurance Company News Analysis</h1>
                    <div class="stats">
                        Generated on: {current_time}<br>
                        Analyzing news from the last 12 months
                    </div>
        """

        # Individual company sections
        for company in self.companies:
            html += f"""
            <div class="company-section">
                <div class="company-header">
                    <h2>{company}</h2>
                    <div class="stats">Articles found in the last 12 months: {self.article_counts[company]}</div>
                </div>
                <div class="topics">
                    <strong>Main Topics:</strong><br>
                    {' '.join(f'<span class="topic-tag">{topic}<span class="topic-score">({score})</span></span>' 
                             for topic, score in self.top_topics.get(company, []))}
                </div>
                <div class="article-preview">
                    <strong>Latest Articles:</strong><br>
                    {self.format_article_previews(company)}
                </div>
                <a href="https://news.google.com/search?q={company.replace(' ', '+')}" 
                   class="view-news-btn" target="_blank">
                    Scopri le notizie
                    <span class="cta">Click here to view all stories →</span>
                </a>
            """
            if self.word_clouds[company]:
                html += f"""
                <div class="wordcloud">
                    <img src="data:image/png;base64,{self.word_clouds[company]}" 
                         alt="Word cloud for {company}"
                         title="Top 20 most frequent words in {company} news">
                </div>
                """
            html += "</div>"

        # Cross-reference section
        html += """
            <div class="cross-reference">
                <h2>Cross-Referenced News</h2>
                <p class="stats">Articles mentioning multiple companies:</p>
        """

        html += venn_diagram

        html += """
            </div>
            </div>
        </div>
        </body>
        </html>
        """
        
        with open("news_analysis.html", "w", encoding="utf-8") as f:
            f.write(html)
        
        webbrowser.open('file://' + os.path.realpath("news_analysis.html"))

    def format_article_previews(self, company):
        """Format the latest articles for preview"""
        articles = self.articles.get(company, [])
        if not articles:
            return "<div class='article-desc'>No articles found</div>"
        
        html = ""
        for article in articles[:3]:  # Show top 3 articles
            title = article.get('title', 'No title')
            desc = article.get('desc', 'No description available')
            link = article.get('link', '#')
            html += f"""
                <div class="article-title">
                    <a href="{link}" target="_blank">{title}</a>
                </div>
                <div class="article-desc">{desc}</div>
                <br>
            """
        return html

    def run(self):
        print("\nStarting news analysis...")
        print("Period: Last 12 months")
        print("Companies:", ", ".join(self.companies))
        
        for company in self.companies:
            self.search_company_news(company)
        
        print("\nGenerating HTML report...")
        self.generate_html()
        print("Done! Opening report in your browser.")

    def validate_link(self, url):
        """Validate if a link is accessible with retry logic."""
        max_retries = 2
        base_delay = 3
        
        for attempt in range(max_retries):
            try:
                headers = {
                    'User-Agent': random.choice(self.user_agents),
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7'
                }
                
                # Add delay between attempts
                if attempt > 0:
                    delay = base_delay * (2 ** attempt)
                    time.sleep(delay)
                
                response = requests.head(url, headers=headers, timeout=10, allow_redirects=True)
                
                if response.status_code == 200:
                    return True
                elif response.status_code in [429, 503, 520]:  # Rate limit or service unavailable
                    if attempt < max_retries - 1:
                        continue
                return False
                
            except (requests.exceptions.RequestException, Exception):
                if attempt < max_retries - 1:
                    continue
                return False
        
        return False

if __name__ == "__main__":
    scanner = NewsScanner()
    scanner.run() 