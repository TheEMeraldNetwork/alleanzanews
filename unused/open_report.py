import webbrowser
import os
from datetime import datetime

# List of possible report files
REPORT_FILES = ['insurance_news.html', 'news_results.html', 'sentiment_report.html']

def get_most_recent_report():
    existing_files = []
    for file in REPORT_FILES:
        if os.path.exists(file):
            existing_files.append({
                'file': file,
                'time': os.path.getmtime(file)
            })
    
    if existing_files:
        # Sort by modification time, most recent first
        existing_files.sort(key=lambda x: x['time'], reverse=True)
        return existing_files[0]['file']
    return None

# Get and open the most recent report
report_file = get_most_recent_report()
if report_file:
    print(f"Opening {report_file}...")
    webbrowser.open(report_file)
else:
    print("No report files found. Please run the news scanner first.") 