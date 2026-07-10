import os
import sys
from dotenv import load_dotenv

# Load env variables
load_dotenv()

# Ensure src/ is in the python path
sys.path.insert(0, os.path.abspath('src'))
from toku_radar.tools.resilient_scraper import ResilientScraper

def run_scrape():
    scraper = ResilientScraper()
    # Attempting to scrape the main page of Toku
    urls_to_scrape = [
        "https://trytoku.com/"
    ]
    
    with open("scratch/toku_scrape_results.txt", "w", encoding="utf-8") as f:
        for url in urls_to_scrape:
            print(f"Scraping {url}...")
            result = scraper.scrape_url(url)
            f.write(f"=== {url} ===\n\n{result}\n\n")
            print("Done.")

if __name__ == "__main__":
    run_scrape()
