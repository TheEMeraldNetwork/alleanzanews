from GoogleNews import GoogleNews
from config import COMPANY_NAMES, NEWS_SEARCH

def is_relevant_article(title, description, company):
    """Check if an article is truly relevant to the company."""
    title = title.lower() if title else ""
    description = description.lower() if description else ""
    company_lower = company.lower()
    
    # Special case for "Vita Nuova" to avoid false positives
    if company_lower == "vita nuova":
        text = f"{title} {description}".lower()
        print(f"\nChecking article:\nTitle: {title}\nDesc: {description}")
        
        # Check for insurance context
        insurance_terms = [
            "assicurazioni", "assicurazione", "polizza", "broker", "finanziaria",
            "previdenza", "risparmio", "protezione", "pensione", "investimento",
            "compagnia", "agenzia", "consulente", "consulenza", "premio"
        ]
        has_insurance_context = any(term in text for term in insurance_terms)
        print(f"Has insurance context: {has_insurance_context}")
        
        # Debug the filtering conditions
        contains_nuova_vita = "nuova vita" in text
        contains_vita_nuova = "vita nuova" in text
        contains_nuova = text.count("nuova") > 0
        contains_multiple_vita = text.count("vita") > 1
        
        print(f"Contains 'nuova vita': {contains_nuova_vita}")
        print(f"Contains 'vita nuova': {contains_vita_nuova}")
        print(f"Contains 'nuova': {contains_nuova}")
        print(f"Contains multiple 'vita': {contains_multiple_vita}")
        
        if not has_insurance_context:
            print("Article REJECTED: No insurance context\n")
            return False
            
        if (contains_nuova_vita or 
            (contains_vita_nuova and not has_insurance_context) or 
            contains_multiple_vita):
            print("Article REJECTED due to filtering conditions\n")
            return False
            
        print("Article PASSED filtering conditions\n")
        return True
    
    return False

# Initialize GoogleNews
gn = GoogleNews(lang=NEWS_SEARCH["language"], region=NEWS_SEARCH["region"])

# Search for Vita Nuova articles with insurance context
print("Searching for Vita Nuova insurance articles...")
search_queries = [
    '"Vita Nuova" assicurazioni',
    '"Vita Nuova" polizza',
    '"Vita Nuova" agenzia',
    '"Vita Nuova" compagnia'
]

all_results = []
for query in search_queries:
    print(f"\nTrying search query: {query}")
    gn.search(query)
    results = gn.results()
    if results:
        all_results.extend(results)
        print(f"Found {len(results)} results")
    gn.clear()

# Remove duplicates based on title
seen_titles = set()
unique_results = []
for article in all_results:
    title = article.get("title", "")
    if title not in seen_titles:
        seen_titles.add(title)
        unique_results.append(article)

# Check the unique articles
print(f"\nAnalyzing {len(unique_results)} unique articles:")
for article in unique_results:
    title = article.get("title", "")
    desc = article.get("desc", "")
    is_relevant = is_relevant_article(title, desc, "Vita Nuova") 