# Direct website URLs and RSS feeds
TARGET_URLS = [
    # Italian Financial News RSS Feeds
    'https://www.ansa.it/sito/notizie/economia/economia_rss.xml',
    'https://www.ilsole24ore.com/rss/economia.xml',
    'https://www.repubblica.it/rss/economia/rss2.0.xml',
    'https://www.assinews.it/feed/',
    'https://www.insurancetrade.it/insurance/rss/rss.xml',
    # Insurance News Sites
    'https://www.assinews.it/',
    'https://www.insurancetrade.it/',
    'https://www.intermediachannel.it/'
]

# Keywords to track (can be expanded)
KEYWORDS = [
    'Alleanza Assicurazioni',
    'Unidea Assicurazioni',
    'Vita Nuova',
    'mercato assicurativo',
    'compagnie assicurative',
    'assicurazioni vita',
    'partnership assicurativa',
    'accordo assicurativo',
    'fusione assicurativa',
    'acquisizione assicurativa'
]

# Company names for cross-reference (exact matches)
COMPANY_NAMES = [
    'Alleanza Assicurazioni',
    'Unidea Assicurazioni',
    'Vita Nuova'
]

# Required company combinations (at least two must be present)
REQUIRED_COMBINATIONS = [
    ('Alleanza Assicurazioni', 'Unidea Assicurazioni'),
    ('Alleanza Assicurazioni', 'Vita Nuova'),
    ('Unidea Assicurazioni', 'Vita Nuova')
]

# News search parameters
NEWS_SEARCH = {
    'days_back': 365,  # Look back one year
    'min_companies_mentioned': 2,  # At least two companies must be mentioned
    'language': 'it',
    'country': 'IT'
}

# Scraping settings
SCRAPING_DELAY = 3  # seconds between requests
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'

# Language settings
LANGUAGE = 'it'  # Italian

# Sentiment analysis settings
SENTIMENT_THRESHOLD_POSITIVE = 0.1
SENTIMENT_THRESHOLD_NEGATIVE = -0.1

# File settings
OUTPUT_DIR = 'results'
REPORT_FILE = 'sentiment_report.html'

# Alternative company names and variations
COMPANY_VARIATIONS = {
    'Unidea Assicurazioni': ['Unidea', 'Unidea Ass.', 'Unidea Assicurazioni S.p.A.'],
    'Vita Nuova': ['VitaNuova', 'Vita-Nuova', 'Vita Nuova Assicurazioni'],
    'Alleanza Assicurazioni': ['Alleanza', 'Alleanza Ass.', 'Alleanza Assicurazioni S.p.A.']
} 