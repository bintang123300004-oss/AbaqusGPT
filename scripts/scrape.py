"""Script to scrape Abaqus documentation"""
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.scraper import AbaqusCrawler
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def main():
    """Run the scraper"""
    # Configuration
    base_url = os.getenv('BASE_URL', 'http://130.149.89.49:2080/v2016/index.html')
    max_workers = int(os.getenv('MAX_WORKERS', '5'))
    request_delay = float(os.getenv('REQUEST_DELAY', '0.5'))
    
    print("=" * 60)
    print("Abaqus Documentation Scraper")
    print("=" * 60)
    print(f"Base URL: {base_url}")
    print(f"Workers: {max_workers}")
    print(f"Delay: {request_delay}s")
    print("=" * 60)
    print()
    print("This will scrape ALL Abaqus 2016 documentation pages.")
    print("This may take several hours depending on the size.")
    print()
    
    response = input("Continue? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("Aborted.")
        return
    
    # Create crawler
    crawler = AbaqusCrawler(
        base_url=base_url,
        max_workers=max_workers,
        request_delay=request_delay
    )
    
    # Start crawling
    try:
        crawler.crawl()
        print("\nScraping completed successfully!")
        print(f"Data saved to: data/scraped/abaqus_docs.jsonl")
        
    except KeyboardInterrupt:
        print("\n\nScraping interrupted by user.")
        print("Progress has been saved. You can resume later.")
        
    except Exception as e:
        print(f"\n\nError during scraping: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
