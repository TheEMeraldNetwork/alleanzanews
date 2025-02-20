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
from GoogleNews import GoogleNews
from textblob import TextBlob
from collections import Counter
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

class NewsScanner:
    def __init__(self):
        self.gnews = GoogleNews(lang='it', period='12m')  # Extended to 12 months
        self.companies = [
            "VitaNuova Assicurazioni",  # Fixed company name
            "Unidea Assicurazioni",
            "Alleanza Assicurazioni"
        ]
        self.article_counts = {}
        self.word_clouds = {}
        self.top_topics = {}
        self.articles = {}  # Store articles for search functionality
        
        # Download required NLTK data
        try:
            nltk.data.find('tokenizers/punkt')
            nltk.data.find('corpora/stopwords')
        except LookupError:
            nltk.download('punkt')
            nltk.download('stopwords')
        
        # Combine Italian and English stopwords
        self.stop_words = set(stopwords.words('italian') + stopwords.words('english'))
        # Add custom stopwords
        self.stop_words.update([
            'della', 'delle', 'degli', 'dell', 'dal', 'dalla', 'dai', 'dagli', 
            'del', 'alla', 'alle', 'agli', 'allo', 'nell', 'nella', 'nelle', 
            'negli', 'sul', 'sulla', 'sulle', 'sugli', 'con', 'per', 'tra',
            'fra', 'presso', 'dopo', 'prima', 'durante', 'oltre', 'attraverso',
            'mediante', 'tramite', 'verso', 'fino', 'assicurazioni', 'assicurazione',
            'company', 'companies', 'group', 'gruppo', 'società'
        ])

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

    def search_company_news(self, company):
        print(f"\nSearching news for {company}...")
        try:
            self.gnews.clear()
            print("  Making request to Google News...")
            self.gnews.search(company)
            print("  Fetching results...")
            results = self.gnews.results()
            
            # Verify results and filter out duplicates
            verified_results = []
            seen_titles = set()
            for result in results:
                if result.get('title') and result['title'] not in seen_titles:
                    verified_results.append(result)
                    seen_titles.add(result['title'])
            
            actual_count = len(verified_results)
            print(f"  Found {actual_count} unique articles")
            
            # Store article count and results
            self.article_counts[company] = actual_count
            self.articles[company] = verified_results
            
            # Extract texts for topic analysis
            texts = [f"{r['title']} {r.get('desc', '')}" for r in verified_results]
            
            print("  Analyzing topics...")
            # Get top topics
            self.top_topics[company] = self.extract_topics(texts)
            
            # Generate word cloud from titles and descriptions
            text = " ".join(texts)
            if text.strip():
                print("  Generating word cloud...")
                # Clean and filter text
                cleaned_text = self.clean_text_for_wordcloud(text, company)
                if cleaned_text.strip():
                    wordcloud = WordCloud(width=400, height=200, 
                                       background_color='white',
                                       min_word_length=4,  # Additional filter for word length
                                       collocations=False  # Avoid repeated word pairs
                                       ).generate(cleaned_text)
                    
                    # Convert word cloud to base64 image
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
                    print("  No words remained after filtering for word cloud")
                    self.word_clouds[company] = None
            else:
                print("  No text available for word cloud")
                self.word_clouds[company] = None
        except Exception as e:
            print(f"  Error processing {company}: {str(e)}")
            self.article_counts[company] = 0
            self.articles[company] = []
            self.top_topics[company] = []
            self.word_clouds[company] = None

    def search_combined_news(self, company1, company2):
        """Search for news mentioning both companies"""
        try:
            query = f'"{company1}" AND "{company2}"'
            print(f"\nSearching for articles mentioning both {company1} and {company2}...")
            self.gnews.clear()
            self.gnews.search(query)
            results = self.gnews.results()
            
            # Verify results and filter out duplicates
            verified_results = []
            seen_titles = set()
            for result in results:
                if result.get('title') and result['title'] not in seen_titles:
                    verified_results.append(result)
                    seen_titles.add(result['title'])
            
            count = len(verified_results)
            print(f"  Found {count} unique articles")
            return count
        except Exception as e:
            print(f"  Error searching combined news: {str(e)}")
            return 0

    def generate_venn_diagram(self):
        """Generate a Venn diagram showing topic overlaps between companies"""
        # Get topics for each company
        topics_by_company = {
            company: set(topic for topic, _ in self.top_topics.get(company, []))
            for company in self.companies
        }
        
        # Calculate overlaps
        company_names = [c.replace(' Assicurazioni', '') for c in self.companies]
        vita_topics = topics_by_company[self.companies[0]]
        unidea_topics = topics_by_company[self.companies[1]]
        alleanza_topics = topics_by_company[self.companies[2]]
        
        # Calculate all possible overlaps
        overlaps = {
            'vita_only': vita_topics - (unidea_topics | alleanza_topics),
            'unidea_only': unidea_topics - (vita_topics | alleanza_topics),
            'alleanza_only': alleanza_topics - (vita_topics | unidea_topics),
            'vita_unidea': vita_topics & unidea_topics - alleanza_topics,
            'vita_alleanza': vita_topics & alleanza_topics - unidea_topics,
            'unidea_alleanza': unidea_topics & alleanza_topics - vita_topics,
            'all': vita_topics & unidea_topics & alleanza_topics
        }
        
        # Create Venn diagram
        plt.figure(figsize=(6, 4))
        venn3([topics_by_company[company] for company in self.companies],
              set_labels=company_names,
              set_colors=('#8BA89B', '#9BB0A5', '#AEBFB4'))
        plt.title('Topic Overlaps Between Companies', pad=20, color='white')
        
        # Style the diagram
        plt.gca().set_facecolor('#1C2B2B')
        plt.gcf().set_facecolor('#1C2B2B')
        for text in plt.gca().texts:
            text.set_color('white')
        
        # Convert to base64
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', 
                   facecolor='#1C2B2B', 
                   bbox_inches='tight',
                   dpi=300)
        plt.close()
        img_buffer.seek(0)
        
        return base64.b64encode(img_buffer.getvalue()).decode(), overlaps

    def generate_html(self):
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        venn_diagram, overlaps = self.generate_venn_diagram()
        
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

        combinations = [
            ("VitaNuova Assicurazioni", "Alleanza Assicurazioni"),
            ("Unidea Assicurazioni", "Alleanza Assicurazioni"),
            ("VitaNuova Assicurazioni", "Unidea Assicurazioni")
        ]

        for company1, company2 in combinations:
            combined_count = self.search_combined_news(company1, company2)
            html += f"""
                <div class="stats">
                    Articles mentioning both {company1} and {company2}: {combined_count}
                    <a href="https://news.google.com/search?q={urllib.parse.quote(f'{company1} AND {company2}')}" 
                       class="cross-ref-btn" target="_blank">
                        Scopri le notizie combinate
                    </a>
                </div>
            """

        html += """
            </div>
            </div>
            <div class="sidebar">
                <div class="venn-diagram">
                    <h2>Topic Overlaps</h2>
                    <img src="data:image/png;base64,"""
        
        html += venn_diagram
        
        html += """" alt="Topic overlap Venn diagram">
                    <div class="overlap-details">
        """
        
        # Add overlap sections
        overlap_titles = {
            'vita_only': 'Topics unique to VitaNuova',
            'unidea_only': 'Topics unique to Unidea',
            'alleanza_only': 'Topics unique to Alleanza',
            'vita_unidea': 'Topics shared by VitaNuova and Unidea',
            'vita_alleanza': 'Topics shared by VitaNuova and Alleanza',
            'unidea_alleanza': 'Topics shared by Unidea and Alleanza',
            'all': 'Topics shared by all companies'
        }
        
        for key, title in overlap_titles.items():
            if overlaps[key]:
                html += f"""
                    <div class="overlap-section">
                        <div class="overlap-title">{title}:</div>
                        <div class="overlap-topics">
                """
                for topic in overlaps[key]:
                    html += f"""
                            <div class="tooltip">
                                <span class="overlap-topic" onclick="searchTopic('{topic}')">{topic}</span>
                                <span class="tooltiptext">Click to search news about this topic</span>
                            </div>
                    """
                html += """
                        </div>
                    </div>
                """
        
        html += """
                    </div>
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

if __name__ == "__main__":
    scanner = NewsScanner()
    scanner.run() 