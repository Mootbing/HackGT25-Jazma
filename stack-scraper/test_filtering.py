"""
Test the scraper's answer filtering functionality
"""

import sys
import os

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scraper import StackOverflowScraper

def test_answer_filtering():
    """Test that the scraper properly filters questions with 0 answers"""
    
    print("Testing Stack Overflow scraper answer filtering...")
    print("=" * 60)
    
    # Create scraper instance
    scraper = StackOverflowScraper(
        headless=True,  # Run in headless mode for testing
        timeout=15
    )
    
    try:
        # Run a small scrape to test filtering
        results = scraper.scrape(
            url="https://stackoverflow.com",
            max_questions=10,  # Test with 10 questions
            save_json=False,   # Don't save files during test
            save_csv=False,
            display_results=False  # Don't print full results
        )
        
        print(f"\n📊 Test Results:")
        print(f"Questions processed: {len(results)}")
        
        if results:
            print(f"\n✅ Successfully filtered questions with answers:")
            for i, q in enumerate(results[:3], 1):  # Show first 3
                print(f"{i}. {q['title'][:60]}... (Answers: {q['answers']})")
            
            # Verify all results have answers > 0
            zero_answer_questions = [q for q in results if q.get('answers') == '0']
            if zero_answer_questions:
                print(f"❌ ERROR: Found {len(zero_answer_questions)} questions with 0 answers!")
            else:
                print(f"✅ SUCCESS: All {len(results)} questions have answers > 0")
        else:
            print("⚠️  No questions were processed (all may have been filtered out)")
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")

if __name__ == "__main__":
    test_answer_filtering()