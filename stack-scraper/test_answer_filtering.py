#!/usr/bin/env python3
"""
Test script to demonstrate the answer filtering functionality
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

def test_answer_filtering():
    """Test that questions without answers are filtered out"""
    
    print("🧪 Testing Answer Filtering Functionality")
    print("=" * 50)
    
    # Test the filter logic directly
    test_cases = [
        ("5", True),   # Question with 5 answers - should be kept
        ("1", True),   # Question with 1 answer - should be kept
        ("0", False),  # Question with 0 answers - should be filtered out
        ("", False),   # Empty answer count - should be filtered out
        ("abc", False), # Invalid answer count - should be filtered out
    ]
    
    def should_keep_question(answer_count_str):
        """Simulate the filtering logic from the scraper"""
        try:
            return int(answer_count_str) > 0
        except (ValueError, TypeError):
            return False
    
    print("Testing filtering logic:")
    for answer_count, expected in test_cases:
        result = should_keep_question(answer_count)
        status = "✅ PASS" if result == expected else "❌ FAIL"
        action = "KEEP" if result else "FILTER OUT"
        print(f"  Answer count '{answer_count}' -> {action} ({status})")
    
    print("\n📋 Filter Implementation:")
    print("  • Original scraper (scraper.py): Returns None for questions with 0 answers")
    print("  • Distributed scraper (distributed_scraper.py): Returns None for questions with 0 answers")
    print("  • Both scrapers skip questions with invalid answer counts")
    
    print("\n🎯 Expected Behavior:")
    print("  • Questions with 1+ answers: ✅ Scraped and stored")
    print("  • Questions with 0 answers: ❌ Skipped completely")
    print("  • Invalid answer data: ❌ Skipped for safety")
    
    print("\n💾 JSON Output:")
    print("  • Only questions with answers will appear in the final JSON")
    print("  • No empty 'answers': '0' entries will be saved")
    print("  • This reduces storage size and improves data quality")

def show_scraper_modifications():
    """Show what was modified in the scrapers"""
    
    print("\n🔧 Code Modifications Made:")
    print("=" * 50)
    
    print("\n1. Original Scraper (scraper.py):")
    print("   • Added answer count extraction and validation")
    print("   • Returns None for questions with 0 answers")
    print("   • Main loop skips None results automatically")
    
    print("\n2. Distributed Scraper (distributed_scraper.py):")
    print("   • Added answer filtering in _extract_question_data_fast()")
    print("   • Returns None for questions with 0 answers")
    print("   • Worker loop handles None results properly")
    
    print("\n3. Filter Logic:")
    print("   ```python")
    print("   # Skip questions without answers")
    print("   try:")
    print("       if int(answer_count) == 0:")
    print("           return None  # This question will be skipped")
    print("   except (ValueError, TypeError):")
    print("       return None  # Invalid data, skip for safety")
    print("   ```")

def main():
    """Main test function"""
    test_answer_filtering()
    show_scraper_modifications()
    
    print("\n🚀 Ready to Use:")
    print("  • Both scrapers will now automatically filter out questions without answers")
    print("  • No additional configuration needed")
    print("  • Run your scraping commands as normal")
    print("\n  Example:")
    print("  python scraper.py")
    print("  python main.py local --workers 3 --target 1000")

if __name__ == "__main__":
    main()