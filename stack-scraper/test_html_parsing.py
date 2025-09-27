"""
Test script to verify answer count extraction from Stack Overflow HTML
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time

def test_answer_extraction():
    """Test answer count extraction from actual SO HTML structure"""
    
    # Set up headless Chrome
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        # Navigate to Stack Overflow
        driver.get("https://stackoverflow.com")
        time.sleep(3)
        
        # Find questions
        questions = driver.find_elements(By.CSS_SELECTOR, ".s-post-summary")
        
        print(f"Found {len(questions)} questions")
        
        for i, question in enumerate(questions[:5]):  # Test first 5 questions
            try:
                # Try different selectors for answer count
                selectors_to_test = [
                    ".s-post-summary--stats-item[title*='answer'] .s-post-summary--stats-item-number",
                    ".s-post-summary--stats-item:nth-child(2) .s-post-summary--stats-item-number",
                ]
                
                answer_count = "N/A"
                used_selector = "None"
                
                for selector in selectors_to_test:
                    try:
                        element = question.find_element(By.CSS_SELECTOR, selector)
                        answer_count = element.text.strip()
                        used_selector = selector
                        break
                    except:
                        continue
                
                # Get title for context
                try:
                    title_element = question.find_element(By.CSS_SELECTOR, "h3.s-post-summary--content-title a")
                    title = title_element.text.strip()[:50] + "..."
                except:
                    title = "Unknown title"
                
                print(f"Question {i+1}: {title}")
                print(f"  Answer count: {answer_count} (using: {used_selector})")
                print(f"  Will be {'SKIPPED' if answer_count == '0' else 'PROCESSED'}")
                print("-" * 60)
                
            except Exception as e:
                print(f"Error processing question {i+1}: {e}")
    
    finally:
        driver.quit()

if __name__ == "__main__":
    test_answer_extraction()