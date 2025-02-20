import pandas as pd
import os
from datetime import datetime

RESULTS_DIR = '.'  # Directory where CSV results are stored
REPORT_FILE = 'sentiment_report.html'

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sentiment Analysis Report</title>
    <style>
        body {{font-family: Arial, sans-serif; margin: 20px; line-height: 1.6;}}
        table {{width: 100%; border-collapse: collapse; margin-bottom: 20px;}}
        th, td {{border: 1px solid #ddd; padding: 8px; text-align: left;}}
        th {{background-color: #f2f2f2;}}
        tr:nth-child(even) {{background-color: #f9f9f9;}}
        .positive {{color: green;}}
        .negative {{color: red;}}
        .neutral {{color: gray;}}
        .section {{margin-bottom: 30px;}}
        .highlight {{background-color: #fff3cd; padding: 10px; border-radius: 5px;}}
        .content-preview {{
            font-size: 0.9em;
            color: #666;
            margin-top: 5px;
        }}
    </style>
</head>
<body>
    <h1>Sentiment Analysis Report</h1>
    <p>Generated on: {date}</p>
    
    <div class="section">
        <h2>Summary</h2>
        <p>Total articles processed: {total_articles}</p>
        <p>Positive articles: {positive_count}</p>
        <p>Negative articles: {negative_count}</p>
        <p>Neutral articles: {neutral_count}</p>
    </div>

    <div class="section">
        <h2>Source Analysis</h2>
        <div class="highlight">
            <h3>Sources Found:</h3>
            {source_counts}
        </div>
    </div>

    <div class="section">
        <h2>Detailed Analysis</h2>
        <table>
            <tr>
                <th>Date</th>
                <th>Source</th>
                <th>Title</th>
                <th>Sentiment</th>
                <th>Preview</th>
                <th>URL</th>
            </tr>
            {rows}
        </table>
    </div>
</body>
</html>
'''

ROW_TEMPLATE = '''
<tr>
    <td>{date}</td>
    <td>{source}</td>
    <td>{title}</td>
    <td class="{sentiment_class}">{sentiment_label} ({sentiment_score:.2f})</td>
    <td><div class="content-preview">{content_preview}</div></td>
    <td><a href="{url}" target="_blank">Link</a></td>
</tr>
'''

def generate_html_report():
    # Find the most recent CSV file
    csv_files = [f for f in os.listdir() if f.startswith('news_analysis_') and f.endswith('.csv')]
    if not csv_files:
        print("No analysis files found")
        return
    
    latest_file = max(csv_files)
    df = pd.read_csv(latest_file)
    
    # Count sentiments
    sentiment_counts = df['sentiment_label'].value_counts()
    
    # Count sources
    source_counts = df['source'].value_counts()
    
    # Generate rows for the HTML table
    rows = ''
    for _, row in df.iterrows():
        sentiment_class = row['sentiment_label'].lower()
        content_preview = row['content'][:200] + '...' if len(row['content']) > 200 else row['content']
        
        rows += ROW_TEMPLATE.format(
            date=row['date'],
            source=row['source'],
            title=row['title'],
            sentiment_class=sentiment_class,
            sentiment_label=row['sentiment_label'].capitalize(),
            sentiment_score=row['sentiment_score'],
            content_preview=content_preview,
            url=row['url']
        )
    
    # Fill the HTML template
    html_content = HTML_TEMPLATE.format(
        date=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        total_articles=len(df),
        positive_count=sentiment_counts.get('positive', 0),
        negative_count=sentiment_counts.get('negative', 0),
        neutral_count=sentiment_counts.get('neutral', 0),
        source_counts=''.join(f"<p><strong>{source}:</strong> {count} articles</p>" for source, count in source_counts.items()),
        rows=rows
    )
    
    # Write to the HTML file
    with open(REPORT_FILE, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"Report generated: {REPORT_FILE}")

if __name__ == "__main__":
    generate_html_report() 