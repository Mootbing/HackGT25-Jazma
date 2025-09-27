"""
Unit test for enhanced Stack Overflow scraper - Single Question Test
Tests the scraper's capability to extract full content from a specific question
"""

import unittest
import json
from scraper import StackOverflowScraper


class TestSingleQuestionScraper(unittest.TestCase):
    """Test class for single question scraping functionality"""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.scraper = StackOverflowScraper(
            headless=False,  # Set to True to run silently
            timeout=20
        )
        self.test_url = "https://stackoverflow.com/questions/8114355/loop-until-a-specific-user-input?noredirect=1&lq=1"
        
    def tearDown(self):
        """Tear down test fixtures after each test method."""
        if self.scraper:
            self.scraper.cleanup()
    
    def test_scrape_full_question_content(self):
        """Test scraping full question and answer content from specific URL"""
        print(f"\n🧪 Testing enhanced scraper on specific question:")
        print(f"📍 URL: {self.test_url}")
        print("=" * 80)
        
        try:
            # Initialize driver
            self.scraper.driver = self.scraper.setup_driver()
            
            # Navigate directly to the question
            print("🌐 Navigating to question page...")
            self.scraper.driver.get(self.test_url)
            
            # Extract full content using the enhanced method
            print("📊 Extracting full question and answer content...")
            full_data = self.scraper.scrape_full_question_and_answer(self.test_url)
            
            # Verify we got data
            self.assertIsInstance(full_data, dict, "Should return a dictionary")
            
            # Test question content extraction
            print(f"\n📝 Question Content Length: {len(full_data.get('question_content', ''))}")
            if full_data.get('question_content'):
                print(f"✅ Question content extracted successfully")
                print(f"🔤 Preview: {full_data['question_content'][:200]}...")
            else:
                print("❌ No question content found")
            
            # Test question code blocks
            question_code_count = len(full_data.get('question_code', []))
            print(f"\n💻 Question Code Blocks: {question_code_count}")
            if question_code_count > 0:
                print("✅ Code blocks found in question")
                for i, code in enumerate(full_data['question_code'][:2], 1):  # Show first 2
                    print(f"   Code Block {i}: {code[:100]}...")
            
            # Test top answer extraction
            print(f"\n🎯 Top Answer Content Length: {len(full_data.get('top_answer_content', ''))}")
            if full_data.get('top_answer_content'):
                print(f"✅ Top answer extracted successfully")
                print(f"📊 Answer Votes: {full_data.get('top_answer_votes', 'N/A')}")
                print(f"✅ Accepted: {full_data.get('top_answer_accepted', False)}")
                print(f"🔤 Preview: {full_data['top_answer_content'][:200]}...")
            else:
                print("❌ No top answer content found")
            
            # Test answer code blocks
            answer_code_count = len(full_data.get('top_answer_code', []))
            print(f"\n💻 Answer Code Blocks: {answer_code_count}")
            if answer_code_count > 0:
                print("✅ Code blocks found in answer")
                for i, code in enumerate(full_data['top_answer_code'][:2], 1):  # Show first 2
                    print(f"   Code Block {i}: {code[:100]}...")
            
            # Save test results to JSON
            timestamp = "test_single"
            filename = f"test_question_data_{timestamp}.json"
            
            # Create complete question data structure for testing
            complete_question_data = {
                "index": 1,
                "title": "Asking the user for input until they give a valid response",
                "link": self.test_url,
                "votes": "extracted_from_page",
                "answers": "extracted_from_page", 
                "views": "extracted_from_page",
                "tags": ["extracted_from_page"],
                "author": "extracted_from_page",
                "excerpt": "Test question for validation",
                "timestamp": "test_run",
                "scraped_at": "test_timestamp"
            }
            
            # Merge with extracted content
            complete_question_data.update(full_data)
            
            # Save to file
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump([complete_question_data], f, indent=2, ensure_ascii=False)
            
            print(f"\n💾 Test results saved to: {filename}")
            
            # Assertions
            self.assertGreater(len(full_data.get('question_content', '')), 0, 
                             "Question content should not be empty")
            
            self.assertGreater(len(full_data.get('top_answer_content', '')), 0,
                             "Top answer content should not be empty")
            
            # This specific question should have code blocks
            self.assertGreater(len(full_data.get('question_code', [])), 0,
                             "This question should contain code blocks")
            
            self.assertGreater(len(full_data.get('top_answer_code', [])), 0,
                             "The top answer should contain code blocks")
            
            print(f"\n🎉 All tests passed! Scraper successfully extracted full content.")
            
            return full_data
            
        except Exception as e:
            self.fail(f"Test failed with error: {str(e)}")


def run_single_test():
    """Run the single question test directly"""
    print("🧪 Stack Overflow Enhanced Scraper - Single Question Test")
    print("=" * 80)
    
    # Create test instance
    test = TestSingleQuestionScraper()
    test.setUp()
    
    try:
        # Run the test
        result = test.test_scrape_full_question_content()
        print(f"\n✅ Test completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        
    finally:
        test.tearDown()


if __name__ == "__main__":
    # You can run this in two ways:
    
    # Option 1: Run as unit test
    # unittest.main()
    
    # Option 2: Run direct test with detailed output
    run_single_test()