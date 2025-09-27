"""
Test the duplicate prevention and persistent storage system
"""

import sys
import os

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scraper import StackOverflowScraper

def test_persistent_scraping():
    """Test the persistent scraping with ID tracking"""
    
    print("Testing Stack Overflow persistent scraper...")
    print("=" * 60)
    
    # Create scraper instance
    scraper = StackOverflowScraper(
        headless=True,  # Run in headless mode for testing
        timeout=15
    )
    
    try:
        # First run - should scrape some questions
        print("\n🧪 TEST RUN 1: Initial scraping")
        results1 = scraper.scrape_continuous(
            max_questions_total=3,  # Small number for testing
            max_questions_per_page=2,
            start_page=1,
            max_pages=3,
            save_json=False,
            save_csv=False,
            display_results=False
        )
        
        print(f"\n📊 First run results: {len(results1)} questions scraped")
        
        # Create a new scraper instance to simulate restarting the script
        scraper2 = StackOverflowScraper(
            headless=True,
            timeout=15
        )
        
        print("\n🧪 TEST RUN 2: Restart simulation (should skip duplicates)")
        results2 = scraper2.scrape_continuous(
            max_questions_total=5,  # Try to get more, but should skip existing ones
            max_questions_per_page=3,
            start_page=1,
            max_pages=3,
            save_json=False,
            save_csv=False,
            display_results=False
        )
        
        print(f"\n📊 Second run results: {len(results2)} new questions scraped")
        print(f"📚 Check files:")
        print(f"  - scraped_question_ids.txt (Question ID log)")
        print(f"  - stackoverflow_questions_persistent.json (Persistent database)")
        
        # Show the content of the ID log file
        try:
            with open("scraped_question_ids.txt", "r") as f:
                ids = f.read().strip().split('\n')
                print(f"📝 Question IDs logged: {len(ids)} total")
                print(f"   Sample IDs: {ids[:5]}")  # Show first 5
        except FileNotFoundError:
            print("📝 No ID log file found")
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")

if __name__ == "__main__":
    test_persistent_scraping()