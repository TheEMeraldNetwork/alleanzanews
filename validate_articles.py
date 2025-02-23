import csv
from collections import defaultdict
from bs4 import BeautifulSoup
import re

def count_articles_in_html():
    """Count articles in HTML file for each company."""
    with open('sentiment_report.html', 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')
        
    counts = {
        'Alleanza Assicurazioni': [],
        'Unidea Assicurazioni': [],
        'Vita Nuova': []
    }
    
    for company in counts.keys():
        company_section = soup.find('div', {'data-company': company.split()[0].lower()})
        if company_section:
            articles_section = company_section.find('div', {'data-content': 'articles'})
            if articles_section:
                articles = articles_section.find_all('div', class_='article')
                for article in articles:
                    title = article.find('h4').text.strip() if article.find('h4') else None
                    link = article.find('a')['href'] if article.find('a') else None
                    if title and link:
                        counts[company].append({
                            'title': title,
                            'url': link
                        })
    
    return counts

def normalize_title(title):
    """Normalize title for comparison by removing special characters, accents, and whitespace."""
    # Convert to lowercase
    title = title.lower()
    
    # Replace accented characters
    replacements = {
        'à': 'a', 'è': 'e', 'é': 'e', 'ì': 'i', 'ò': 'o', 'ù': 'u',
        'a\'': 'a', 'e\'': 'e', 'i\'': 'i', 'o\'': 'o', 'u\'': 'u',
        'aa': 'a', 'ee': 'e', 'ii': 'i', 'oo': 'o', 'uu': 'u'
    }
    for old, new in replacements.items():
        title = title.replace(old, new)
    
    # Remove ellipsis variations
    title = re.sub(r'\.{3,}$', '', title)
    title = re.sub(r'\s*\.\.\.$', '', title)
    title = re.sub(r'\s*…$', '', title)
    
    # Remove special characters but keep spaces between words
    title = re.sub(r'[^\w\s]', '', title)
    
    # Normalize whitespace
    title = ' '.join(title.split())
    
    # Remove common article variations
    title = re.sub(r'\s+\-\s+.*$', '', title)  # Remove subtitles after dash
    title = re.sub(r'\s+\|\s+.*$', '', title)  # Remove subtitles after pipe
    
    return title

def analyze_csv_articles():
    """Analyze CSV file for unique valid articles based on titles."""
    results = {
        'Alleanza Assicurazioni': {'articles': [], 'ids': []},
        'Unidea Assicurazioni': {'articles': [], 'ids': []},
        'Vita Nuova': {'articles': [], 'ids': []}
    }
    
    title_to_lowest_id = {}  # Track lowest ID for each normalized title
    title_to_data = {}  # Store full data for each title
    
    # First pass: Find lowest ID for each title
    with open('url_analysis.csv', 'r', encoding='utf-8', newline='') as f:
        reader = csv.DictReader(f, delimiter=';')
        for row in reader:
            if row['Master URL for HTML']:  # Only consider rows with Master URL
                title = normalize_title(row['Article Title'])
                current_id = int(row['ID'])
                if title not in title_to_lowest_id or current_id < title_to_lowest_id[title]:
                    title_to_lowest_id[title] = current_id
                    title_to_data[title] = {
                        'id': current_id,
                        'title': row['Article Title'],
                        'url': row['Master URL for HTML']
                    }

    # Second pass: Collect unique articles with lowest IDs
    with open('url_analysis.csv', 'r', encoding='utf-8', newline='') as f:
        reader = csv.DictReader(f, delimiter=';')
        for row in reader:
            company = row['Company']
            if company in results and row['Master URL for HTML']:
                title = normalize_title(row['Article Title'])
                current_id = int(row['ID'])
                
                # Only add if this is the lowest ID for this title
                if current_id == title_to_lowest_id[title]:
                    article_data = title_to_data[title]
                    results[company]['articles'].append(article_data)
                    results[company]['ids'].append(current_id)
    
    # Sort articles by ID
    for company in results:
        results[company]['articles'].sort(key=lambda x: x['id'])
    
    return results

def print_validation_report():
    """Print detailed validation report comparing CSV and HTML content."""
    print("\n=== ARTICLES VALIDATION REPORT ===\n")
    
    # Get counts from both sources
    html_articles = count_articles_in_html()
    csv_analysis = analyze_csv_articles()
    
    for company in csv_analysis:
        print(f"\n{company}:")
        print("-" * (len(company) + 1))
        
        csv_titles = {normalize_title(article['title']): article for article in csv_analysis[company]['articles']}
        html_titles = {normalize_title(article['title']): article for article in html_articles[company]}
        
        print(f"Articles in CSV (unique by title): {len(csv_titles)}")
        print(f"Articles in HTML: {len(html_titles)}")
        
        # Validation check
        is_valid = set(csv_titles.keys()) == set(html_titles.keys())
        print(f"Validation: {'✓ OK' if is_valid else '✗ MISMATCH'}")
        
        if not is_valid:
            print("\nDetailed Analysis:")
            missing_in_html = set(csv_titles.keys()) - set(html_titles.keys())
            extra_in_html = set(html_titles.keys()) - set(csv_titles.keys())
            
            if missing_in_html:
                print("\nMissing in HTML (should be added):")
                for title in missing_in_html:
                    article = csv_titles[title]
                    print(f"  - ID {article['id']}: {article['title']}\n    URL: {article['url']}")
            
            if extra_in_html:
                print("\nExtra in HTML (should be removed):")
                for title in extra_in_html:
                    article = html_titles[title]
                    print(f"  - Title: {article['title']}\n    URL: {article['url']}")
            
        print("\nValid articles from CSV:")
        for article in csv_analysis[company]['articles']:
            print(f"  - ID {article['id']}: {article['title']}")

if __name__ == "__main__":
    print_validation_report() 