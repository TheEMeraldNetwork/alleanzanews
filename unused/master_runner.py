import os
import sys
import time
import logging
import signal
import json
from datetime import datetime
import pandas as pd
from news_scraper import NewsScraperAnalyzer
import webbrowser

class MasterRunner:
    def __init__(self):
        self.setup_logging()
        self.running = True
        self.scrapers = {}
        self.stats = {
            'start_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_articles': 0,
            'errors': 0,
            'last_run': None
        }
        self.setup_signal_handlers()
        
    def setup_logging(self):
        # Create logs directory if it doesn't exist
        if not os.path.exists('logs'):
            os.makedirs('logs')
            
        # Set up master logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/master_runner.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('MasterRunner')
        
    def setup_signal_handlers(self):
        signal.signal(signal.SIGINT, self.handle_shutdown)
        signal.signal(signal.SIGTERM, self.handle_shutdown)
        
    def handle_shutdown(self, signum, frame):
        self.logger.info("Shutdown signal received. Cleaning up...")
        self.running = False
        self.save_stats()
        
    def initialize_scrapers(self):
        self.logger.info("Initializing scrapers...")
        try:
            # Initialize news scraper
            self.scrapers['news_scraper'] = NewsScraperAnalyzer()
            self.logger.info("News scraper initialized successfully")
            
            # Here we can add more scrapers as we develop them
            # self.scrapers['other_scraper'] = OtherScraperClass()
            
        except Exception as e:
            self.logger.error(f"Error initializing scrapers: {str(e)}")
            self.stats['errors'] += 1
            raise
            
    def run_scraping_cycle(self):
        self.logger.info("Starting scraping cycle...")
        try:
            # Run news scraper
            if 'news_scraper' in self.scrapers:
                self.scrapers['news_scraper'].scrape_and_analyze()
                
            # Update statistics
            self.update_stats()
            
            # Generate and open report
            self.generate_and_open_report()
            
        except Exception as e:
            self.logger.error(f"Error in scraping cycle: {str(e)}")
            self.stats['errors'] += 1
            
    def update_stats(self):
        """Update running statistics"""
        try:
            # Count total articles from all CSV files
            csv_files = [f for f in os.listdir() if f.startswith('news_analysis_') and f.endswith('.csv')]
            total_articles = 0
            for csv_file in csv_files:
                df = pd.read_csv(csv_file)
                total_articles += len(df)
            
            self.stats['total_articles'] = total_articles
            self.stats['last_run'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Save updated stats
            self.save_stats()
            
        except Exception as e:
            self.logger.error(f"Error updating stats: {str(e)}")
            self.stats['errors'] += 1
            
    def save_stats(self):
        """Save running statistics to file"""
        try:
            with open('scraping_stats.json', 'w', encoding='utf-8') as f:
                json.dump(self.stats, f, indent=4)
        except Exception as e:
            self.logger.error(f"Error saving stats: {str(e)}")
            
    def consolidate_results(self):
        """Consolidate all CSV files into a single master file"""
        try:
            csv_files = [f for f in os.listdir() if f.startswith('news_analysis_') and f.endswith('.csv')]
            if not csv_files:
                return
                
            all_dfs = []
            for csv_file in csv_files:
                df = pd.read_csv(csv_file)
                all_dfs.append(df)
                
            if all_dfs:
                master_df = pd.concat(all_dfs, ignore_index=True)
                master_df.drop_duplicates(subset=['url'], keep='last', inplace=True)
                master_df.to_csv('master_results.csv', index=False, encoding='utf-8-sig')
                self.logger.info("Results consolidated into master_results.csv")
                
        except Exception as e:
            self.logger.error(f"Error consolidating results: {str(e)}")
            self.stats['errors'] += 1
            
    def generate_and_open_report(self):
        """Generate the HTML report and open it in the default web browser"""
        try:
            from report_generator import generate_html_report
            generate_html_report()
            webbrowser.open(REPORT_FILE)
        except Exception as e:
            self.logger.error(f"Error generating or opening report: {str(e)}")
            
    def run(self):
        self.logger.info("Starting Master Runner...")
        try:
            self.initialize_scrapers()
            
            while self.running:
                self.run_scraping_cycle()
                self.consolidate_results()
                
                # Wait for 6 hours before next cycle
                for _ in range(360):  # 6 hours * 60 minutes
                    if not self.running:
                        break
                    time.sleep(60)  # Check every minute if we should continue
                    
        except KeyboardInterrupt:
            self.logger.info("Keyboard interrupt received")
        except Exception as e:
            self.logger.error(f"Critical error in master runner: {str(e)}")
        finally:
            self.cleanup()
            
    def cleanup(self):
        self.logger.info("Cleaning up...")
        self.save_stats()
        self.consolidate_results()
        self.logger.info("Master Runner shutdown complete")
        
def main():
    master = MasterRunner()
    master.run()

if __name__ == "__main__":
    main() 