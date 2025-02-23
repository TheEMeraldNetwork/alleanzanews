import os
import csv
from dotenv import load_dotenv
from anthropic import Anthropic

# Load environment variables
load_dotenv()

# Set Anthropic API key as environment variable
os.environ["ANTHROPIC_API_KEY"] = os.getenv('ANTHROPIC_API_KEY', '')

class EmeraldAssistant:
    def __init__(self):
        # Initialize Anthropic client
        self.anthropic = Anthropic()
        
        # Load dashboard data
        self.dashboard_data = self.load_dashboard_data()
        
    def load_dashboard_data(self):
        """Load articles and reviews from our dashboard."""
        data = {
            'articles': [],
            'reviews': []
        }
        
        # Load articles from CSV
        try:
            with open('url_analysis.csv', 'r', encoding='utf-8', newline='') as f:
                reader = csv.DictReader(f, delimiter=';')
                for row in reader:
                    if row['Valid?'] == 'Yes' and row['Master URL for HTML']:
                        article = {
                            'title': row['Article Title'],
                            'company': row['Company'],
                            'url': row['Master URL for HTML']
                        }
                        data['articles'].append(article)
        except FileNotFoundError:
            print("Warning: url_analysis.csv not found")
        
        # Load reviews (using the existing review data)
        companies = ["Alleanza Assicurazioni", "Unidea Assicurazioni", "Vita Nuova"]
        for company in companies:
            reviews = self.fetch_company_reviews(company)
            for platform in reviews.get('platforms', []):
                for review in platform.get('sample_reviews', []):
                    review_data = {
                        'company': company,
                        'platform': platform['platform'],
                        'rating': review['rating'],
                        'text': review['text'],
                        'author': review['author'],
                        'date': review['date']
                    }
                    data['reviews'].append(review_data)
        
        print(f"Loaded {len(data['articles'])} articles and {len(data['reviews'])} reviews")
        return data

    def fetch_company_reviews(self, company):
        """Fetch company reviews (using existing review data)."""
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
                            }
                        ]
                    }
                ]
            }
        }
        return reviews.get(company.lower(), {"platforms": []})

    def create_context(self, query):
        """Create relevant context from dashboard data based on the query."""
        # Convert query to lowercase for matching
        query_lower = query.lower()
        
        context = []
        
        # Find relevant articles
        for article in self.dashboard_data['articles']:
            if (article['company'].lower() in query_lower or 
                any(word in article['title'].lower() for word in query_lower.split())):
                context.append(f"Article: {article['title']} (Company: {article['company']}, Source: {article['url']})")
        
        # Find relevant reviews
        for review in self.dashboard_data['reviews']:
            if review['company'].lower() in query_lower:
                context.append(
                    f"Review on {review['platform']}: \"{review['text']}\" - "
                    f"{review['author']} ({review['date']}, Rating: {review['rating']}/5)"
                )
        
        return context

    def get_response(self, query):
        """Get a response from Claude using dashboard data as context."""
        try:
            # Get relevant context
            context = self.create_context(query)
            
            if not context:
                return {
                    "response": (
                        "I don't have any specific information from our dashboard to answer your question. "
                        "I can only provide information about Alleanza Assicurazioni, Unidea Assicurazioni, "
                        "or Vita Nuova based on our collected news and reviews."
                    ),
                    "sources": []
                }
            
            # Create prompt for Claude
            prompt = f"""You are the Emerald Assistant, a helpful AI that provides information about insurance companies based on our dashboard data. You must ALWAYS cite your sources and ONLY use the information provided in the context below.

Context from dashboard:
{chr(10).join(context)}

Important instructions:
1. ONLY use information from the provided context
2. If you can't answer from the context, say so clearly
3. ALWAYS cite your sources using [Source: X]
4. Keep responses focused and relevant
5. Maintain a professional tone

User question: {query}

Please provide a well-structured answer with appropriate citations:"""

            # Get response from Claude
            response = self.anthropic.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=1024,
                temperature=0,
                system="You are the Emerald Assistant, an AI that provides information about insurance companies. You MUST cite sources and ONLY use provided context.",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            return {
                "response": response.content[0].text,
                "sources": context
            }
            
        except Exception as e:
            return {
                "response": f"I apologize, but I encountered an error: {str(e)}. Please try again later.",
                "sources": []
            }

def interactive_mode():
    """Interactive mode to test the Emerald Assistant."""
    assistant = EmeraldAssistant()
    
    print("\nEmerald Assistant Ready!")
    print("Ask me anything about Alleanza Assicurazioni, Unidea Assicurazioni, or Vita Nuova.")
    print("Type 'exit' to quit.\n")
    
    while True:
        query = input("\nYour question: ").strip()
        if query.lower() == 'exit':
            print("\nGoodbye!")
            break
            
        print("\nSearching and analyzing...")
        response = assistant.get_response(query)
        
        print("\nResponse:")
        print(response['response'])
        
        if response['sources']:
            print("\nSources:")
            for source in response['sources']:
                print(f"- {source}")
        print("\n" + "-" * 80)

if __name__ == "__main__":
    interactive_mode() 