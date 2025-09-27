"""
Stack Overflow Web Scraper
A comprehensive Selenium-based scraper for extracting data from Stack Overflow
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException
import json
import csv
import time
import random
from datetime import datetime
from typing import List, Dict, Optional


class StackOverflowScraper:
    """Main scraper class for Stack Overflow"""
    
    def __init__(self, headless: bool = False, timeout: int = 15):
        """
        Initialize the scraper
        
        Args:
            headless: Run browser in headless mode
            timeout: Default timeout for WebDriver waits
        """
        self.headless = headless
        self.timeout = timeout
        self.driver = None
        self.wait = None
        
    def setup_driver(self) -> webdriver.Chrome:
        """Create and configure Chrome WebDriver"""
        chrome_options = Options()
        
        # Headless mode
        if self.headless:
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--window-size=1920,1080")
        
        # Performance and compatibility options
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--disable-features=VizDisplayCompositor")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        
        # Suppress Chrome error messages and unnecessary features
        chrome_options.add_argument("--disable-logging")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-plugins")
        chrome_options.add_argument("--disable-images")  # Speed up loading by not loading images
        chrome_options.add_argument("--silent")
        chrome_options.add_argument("--log-level=3")  # Only show fatal errors
        chrome_options.add_argument("--disable-background-timer-throttling")
        chrome_options.add_argument("--disable-backgrounding-occluded-windows")
        chrome_options.add_argument("--disable-renderer-backgrounding")
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Anti-detection measures (combined with logging suppression above)
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        try:
            driver = webdriver.Chrome(options=chrome_options)
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            })
            
            self.wait = WebDriverWait(driver, self.timeout)
            return driver
            
        except Exception as e:
            raise WebDriverException(f"Failed to initialize Chrome driver: {str(e)}")
    
    def navigate_to_stackoverflow(self, url: str = "https://stackoverflow.com") -> bool:
        """
        Navigate to Stack Overflow
        
        Args:
            url: Stack Overflow URL to navigate to
            
        Returns:
            bool: Success status
        """
        try:
            print(f"Navigating to {url}...")
            self.driver.get(url)
            
            # Wait for page to load
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            
            print(f"Successfully loaded: {self.driver.title}")
            return True
            
        except TimeoutException:
            print(f"Timeout while loading {url}")
            return False
        except Exception as e:
            print(f"Error navigating to {url}: {str(e)}")
            return False
    
    def extract_questions(self, max_questions: int = 10) -> List[Dict]:
        """
        Extract questions from the current page
        
        Args:
            max_questions: Maximum number of questions to extract
            
        Returns:
            List of question dictionaries
        """
        questions_data = []
        
        try:
            # Wait for questions to load
            print("Waiting for questions to load...")
            
            # Try multiple selectors for questions - updated for current SO structure
            question_selectors = [
                ".s-post-summary",
                "div[data-post-id]",
                ".question-summary",
                "div.s-post-summary--content"
            ]
            
            questions = None
            for selector in question_selectors:
                try:
                    questions = self.wait.until(
                        EC.presence_of_all_elements_located((By.CSS_SELECTOR, selector))
                    )
                    print(f"Found questions using selector: {selector}")
                    break
                except TimeoutException:
                    continue
            
            if not questions:
                print("No questions found with any selector")
                return questions_data
            
            print(f"Processing {min(len(questions), max_questions)} questions...")
            
            for i, question in enumerate(questions[:max_questions]):
                try:
                    question_data = self._extract_question_data(question, i + 1)
                    if question_data and question_data.get('link') != 'N/A':
                        # Scrape full question and answer content
                        print(f"  🔗 Clicking on question {i + 1}: {question_data['title'][:60]}...")
                        full_content = self.scrape_full_question_and_answer(question_data['link'])
                        
                        # Merge full content with basic data
                        question_data.update(full_content)
                        questions_data.append(question_data)
                        
                        # Random delay between questions
                        delay = random.uniform(3, 7)
                        print(f"  ⏰ Waiting {delay:.1f}s before next question...")
                        time.sleep(delay)
                        
                except Exception as e:
                    print(f"Error extracting question {i + 1}: {str(e)}")
                    continue
            
            return questions_data
            
        except Exception as e:
            print(f"Error extracting questions: {str(e)}")
            return questions_data
    
    def _extract_question_data(self, question_element, index: int) -> Optional[Dict]:
        """
        Extract data from a single question element
        
        Args:
            question_element: Selenium WebElement for the question
            index: Question index number
            
        Returns:
            Dictionary with question data or None if extraction fails
        """
        try:
            # Extract title and link - updated selectors for current SO structure
            title_selectors = [
                "h3.s-post-summary--content-title a",
                ".s-post-summary--content h3 a",
                ".s-post-summary--content-title a", 
                "h3 a.s-link",
                ".question-hyperlink",
                "a.s-link"
            ]
            
            title_element = None
            title = "N/A"
            link = "N/A"
            
            for selector in title_selectors:
                try:
                    title_element = question_element.find_element(By.CSS_SELECTOR, selector)
                    title = title_element.get_attribute("title") or title_element.text.strip()
                    link = title_element.get_attribute("href") or "N/A"
                    break
                except:
                    continue
            
            # Extract additional metadata - updated for current SO structure
            vote_count = self._safe_extract_text(question_element, [
                ".s-post-summary--stats-item-number",
                ".vote-count-post",
                "[title*='vote']",
                ".js-vote-count"
            ], "0")
            
            answer_count = self._safe_extract_text(question_element, [
                ".s-post-summary--stats-item:nth-child(2) .s-post-summary--stats-item-number",
                ".status strong",
                "[title*='answer']",
                ".js-answer-count"
            ], "0")
            
            view_count = self._safe_extract_text(question_element, [
                ".s-post-summary--stats-item:nth-child(3) .s-post-summary--stats-item-number",
                ".views",
                "[title*='view']",
                ".js-view-count"
            ], "0")
            
            # Extract tags - updated for current SO structure  
            tags = []
            try:
                tag_selectors = [
                    ".s-tag.post-tag",
                    ".s-tag",
                    ".post-tag",
                    "a[href*='/questions/tagged/']",
                    ".js-tagname-python, .js-tagname-javascript, .js-tagname-html, .js-tagname-css"
                ]
                
                for selector in tag_selectors:
                    try:
                        tag_elements = question_element.find_elements(By.CSS_SELECTOR, selector)
                        if tag_elements:
                            tags = [tag.text.strip() for tag in tag_elements if tag.text.strip()]
                            if tags:  # If we found tags, break
                                break
                    except:
                        continue
            except:
                pass
            
            # Extract author info - updated for s-user-card structure
            author = self._safe_extract_text(question_element, [
                ".s-user-card--link a",
                ".s-user-card--info .s-user-card--link a", 
                ".s-user-card--link",
                ".user-details a",
                "a[href*='/users/']"
            ], "Anonymous")
            
            # Extract excerpt/description
            excerpt = self._safe_extract_text(question_element, [
                ".s-post-summary--content-excerpt",
                ".excerpt",
                ".summary"
            ], "")
            
            # Extract timestamp
            timestamp = self._safe_extract_text(question_element, [
                ".s-user-card--time .relativetime",
                ".relativetime",
                "time[title]"
            ], "")
            
            return {
                "index": index,
                "title": title,
                "link": link,
                "votes": vote_count,
                "answers": answer_count,
                "views": view_count,
                "tags": tags,
                "author": author,
                "excerpt": excerpt[:200] + "..." if len(excerpt) > 200 else excerpt,  # Limit excerpt length
                "timestamp": timestamp,
                "scraped_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"Error extracting question data: {str(e)}")
            return None
    
    def scrape_full_question_and_answer(self, question_url: str) -> Dict:
        """
        Navigate to a question page and scrape full content including top answer
        
        Args:
            question_url: URL of the question page
            
        Returns:
            Dictionary with full question and answer data
        """
        full_data = {
            "question_content": "",
            "question_code": [],
            "top_answer_content": "",
            "top_answer_code": [],
            "top_answer_votes": "0",
            "top_answer_accepted": False
        }
        
        try:
            print(f"  📖 Loading question page: {question_url}")
            self.driver.get(question_url)
            
            # Random delay to appear more human-like
            delay = random.uniform(2, 5)
            time.sleep(delay)
            
            # Wait for page to load
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            
            # Extract full question content - improved selectors
            question_selectors = [
                ".question .s-prose.js-post-body",
                ".postcell .s-prose.js-post-body", 
                ".post-layout--right .s-prose.js-post-body",
                ".s-prose.js-post-body",
                ".question .post-text",
                "[data-s-prose-element='true']"
            ]
            
            for selector in question_selectors:
                try:
                    question_body = self.driver.find_element(By.CSS_SELECTOR, selector)
                    # Extract text content
                    full_data["question_content"] = question_body.text.strip()
                    
                    # Extract code blocks with multiple selector strategies
                    code_selectors = [
                        "pre.lang-py code",  # Python-specific
                        "pre code", 
                        "code.hljs",
                        ".s-code-block code",
                        "code"  # fallback
                    ]
                    
                    all_code_blocks = []
                    for code_sel in code_selectors:
                        try:
                            code_elements = question_body.find_elements(By.CSS_SELECTOR, code_sel)
                            for code_elem in code_elements:
                                code_text = code_elem.text.strip()
                                # Only add substantial code blocks (not inline single words)
                                if code_text and len(code_text) > 3 and code_text not in all_code_blocks:
                                    all_code_blocks.append(code_text)
                        except:
                            continue
                    
                    full_data["question_code"] = all_code_blocks
                    
                    print(f"    ✅ Found question content (length: {len(full_data['question_content'])})")
                    print(f"    💻 Question code blocks found: {len(full_data['question_code'])}")
                    break
                except Exception as e:
                    print(f"    ❌ Question extraction error with {selector}: {str(e)}")
                    continue
            
            # Extract top answer - Updated selectors based on current HTML structure
            answer_selectors = [
                "#answers .answer:first-of-type",
                ".answer.js-answer:first-of-type",
                "[data-answerid]:first-of-type",
                "#answer-8114405"  # fallback for specific answer ID pattern
            ]
            
            for selector in answer_selectors:
                try:
                    top_answer = self.driver.find_element(By.CSS_SELECTOR, selector)
                    
                    # Check if answer is accepted - updated selectors
                    try:
                        accepted_selectors = [
                            ".js-accepted-answer-indicator",
                            ".accepted-answer",
                            "[class*='accepted']"
                        ]
                        for acc_sel in accepted_selectors:
                            accepted_check = top_answer.find_element(By.CSS_SELECTOR, acc_sel)
                            # Check if it's visible (not d-none)
                            if "d-none" not in accepted_check.get_attribute("class"):
                                full_data["top_answer_accepted"] = True
                                break
                    except:
                        pass
                    
                    # Get answer votes - updated selectors for current structure
                    vote_selectors = [
                        ".js-vote-count[data-value]",
                        ".votecell .js-vote-count",
                        "[data-score]",
                        ".js-voting-container .js-vote-count"
                    ]
                    
                    for vote_sel in vote_selectors:
                        try:
                            vote_element = top_answer.find_element(By.CSS_SELECTOR, vote_sel)
                            vote_value = vote_element.get_attribute("data-value") or vote_element.text.strip()
                            if vote_value:
                                full_data["top_answer_votes"] = vote_value
                                break
                        except:
                            continue
                    
                    # Get answer content - updated selectors for current structure
                    answer_content_selectors = [
                        ".answercell .s-prose.js-post-body",
                        ".post-layout--right .s-prose.js-post-body",
                        ".s-prose.js-post-body",
                        ".answercell .post-text"
                    ]
                    
                    for content_sel in answer_content_selectors:
                        try:
                            answer_body = top_answer.find_element(By.CSS_SELECTOR, content_sel)
                            full_data["top_answer_content"] = answer_body.text.strip()
                            
                            # Extract code blocks from answer - updated selectors
                            code_selectors = [
                                "pre.lang-py code",  # Python-specific code blocks
                                "pre code",
                                "code.hljs",
                                ".s-code-block code"
                            ]
                            
                            all_code_blocks = []
                            for code_sel in code_selectors:
                                try:
                                    code_elements = answer_body.find_elements(By.CSS_SELECTOR, code_sel)
                                    for code_elem in code_elements:
                                        code_text = code_elem.text.strip()
                                        if code_text and code_text not in all_code_blocks:
                                            all_code_blocks.append(code_text)
                                except:
                                    continue
                            
                            full_data["top_answer_code"] = all_code_blocks
                            break
                        except:
                            continue
                    
                    # If we found the answer element but no content, try alternative extraction
                    if not full_data["top_answer_content"]:
                        try:
                            # Try getting all text from the answer cell
                            answer_cell = top_answer.find_element(By.CSS_SELECTOR, ".answercell, .post-layout--right")
                            full_text = answer_cell.text.strip()
                            if full_text:
                                # Split by common answer section separators and take the main content
                                main_content = full_text.split("Share")[0].split("Improve")[0].split("Follow")[0]
                                full_data["top_answer_content"] = main_content.strip()
                        except:
                            pass
                    
                    print(f"    ✅ Found answer with {full_data['top_answer_votes']} votes")
                    if full_data["top_answer_accepted"]:
                        print(f"    ✅ Answer is accepted!")
                    print(f"    📝 Content length: {len(full_data['top_answer_content'])}")
                    print(f"    💻 Code blocks found: {len(full_data['top_answer_code'])}")
                    
                    break
                except Exception as e:
                    print(f"    ❌ Error with selector {selector}: {str(e)}")
                    continue
                    
        except Exception as e:
            print(f"  ❌ Error scraping full content: {str(e)}")
        
        return full_data
    
    def _safe_extract_text(self, parent_element, selectors: List[str], default: str = "N/A") -> str:
        """
        Safely extract text using multiple selectors
        
        Args:
            parent_element: Parent WebElement to search within
            selectors: List of CSS selectors to try
            default: Default value if extraction fails
            
        Returns:
            Extracted text or default value
        """
        for selector in selectors:
            try:
                element = parent_element.find_element(By.CSS_SELECTOR, selector)
                # Try different text extraction methods
                text = element.text.strip()
                if not text:
                    text = element.get_attribute('textContent').strip() if element.get_attribute('textContent') else ""
                if not text:
                    text = element.get_attribute('innerHTML').strip() if element.get_attribute('innerHTML') else ""
                if text:
                    return text
            except Exception as e:
                # Uncomment for debugging: print(f"Selector '{selector}' failed: {str(e)}")
                continue
        return default
    
    def save_to_json(self, data: List[Dict], filename: str = None) -> str:
        """Save data to JSON file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"stackoverflow_enhanced_questions_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"✅ Enhanced data saved to {filename}")
            print(f"📊 File includes full question content, code blocks, and top answers")
            return filename
        except Exception as e:
            print(f"Error saving to JSON: {str(e)}")
            return ""
    
    def save_to_csv(self, data: List[Dict], filename: str = None) -> str:
        """Save data to CSV file"""
        if not data:
            print("No data to save")
            return ""
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"stackoverflow_questions_{timestamp}.csv"
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=data[0].keys())
                writer.writeheader()
                for row in data:
                    # Convert lists to strings for CSV
                    csv_row = row.copy()
                    csv_row['tags'] = ', '.join(row.get('tags', []))
                    writer.writerow(csv_row)
            print(f"Data saved to {filename}")
            return filename
        except Exception as e:
            print(f"Error saving to CSV: {str(e)}")
            return ""
    
    def print_results(self, questions: List[Dict]) -> None:
        """Print scraped results to console"""
        if not questions:
            print("No questions found to display")
            return
        
        print(f"\n{'='*80}")
        print(f"📊 ENHANCED SCRAPING: {len(questions)} QUESTIONS WITH FULL CONTENT")
        print(f"{'='*80}")
        
        for q in questions:
            print(f"\n{q['index']}. 🔥 {q['title']}")
            print(f"   🔗 URL: {q['link']}")
            print(f"   📈 Votes: {q['votes']} | Answers: {q['answers']} | Views: {q['views']}")
            if q['tags']:
                print(f"   🏷️  Tags: {', '.join(q['tags'])}")
            print(f"   👤 Author: {q['author']}")
            if q.get('timestamp'):
                print(f"   📅 Posted: {q['timestamp']}")
            
            # Show question content preview
            if q.get('question_content'):
                content_preview = q['question_content'][:200] + "..." if len(q['question_content']) > 200 else q['question_content']
                print(f"   📝 Question: {content_preview}")
            
            # Show code blocks count
            if q.get('question_code'):
                print(f"   💻 Code blocks in question: {len(q['question_code'])}")
            
            # Show top answer info
            if q.get('top_answer_content'):
                answer_preview = q['top_answer_content'][:150] + "..." if len(q['top_answer_content']) > 150 else q['top_answer_content']
                accepted = " ✅ (Accepted)" if q.get('top_answer_accepted') else ""
                print(f"   🎯 Top Answer ({q.get('top_answer_votes', '0')} votes{accepted}): {answer_preview}")
                
                if q.get('top_answer_code'):
                    print(f"   💻 Code blocks in answer: {len(q['top_answer_code'])}")
            
            print("-" * 80)
        
        print(f"\n🎉 Complete enhanced data saved to JSON file with full content!")
    
    def scrape(self, 
               url: str = "https://stackoverflow.com",
               max_questions: int = 10,
               save_json: bool = True,
               save_csv: bool = False,
               display_results: bool = True) -> List[Dict]:
        """
        Main scraping method
        
        Args:
            url: URL to scrape
            max_questions: Maximum number of questions to extract
            save_json: Save results to JSON file
            save_csv: Save results to CSV file
            display_results: Print results to console
            
        Returns:
            List of scraped question data
        """
        questions = []
        
        try:
            print("🚀 Starting Stack Overflow scraper...")
            print(f"Target: {url}")
            print(f"Max questions: {max_questions}")
            print(f"Headless mode: {self.headless}")
            
            # Initialize driver
            self.driver = self.setup_driver()
            
            # Navigate to Stack Overflow
            if not self.navigate_to_stackoverflow(url):
                return questions
            
            # Extract questions
            questions = self.extract_questions(max_questions)
            
            if questions:
                print(f"\n✅ Successfully extracted {len(questions)} questions!")
                
                # Display results
                if display_results:
                    self.print_results(questions)
                
                # Save to files
                if save_json:
                    self.save_to_json(questions)
                if save_csv:
                    self.save_to_csv(questions)
            else:
                print("❌ No questions were extracted")
            
            # Keep browser open briefly if not headless
            if not self.headless and questions:
                print("\nKeeping browser open for 3 seconds...")
                time.sleep(3)
                
        except Exception as e:
            print(f"❌ Scraping failed: {str(e)}")
            
        finally:
            self.cleanup()
        
        return questions
    
    def cleanup(self):
        """Clean up resources"""
        if self.driver:
            try:
                self.driver.quit()
                print("🧹 Browser closed successfully")
            except Exception as e:
                print(f"Warning: Error closing browser: {str(e)}")


def main():
    """Main execution function"""
    print("Stack Overflow Enhanced Web Scraper v2.1")
    print("=" * 50)
    print("🔥 Now scraping full question and answer content!")
    print("📊 This will take longer due to individual page visits...")
    print()
    
    # Configuration
    scraper = StackOverflowScraper(
        headless=False,  # Set to True for headless mode
        timeout=20  # Increased timeout for page loads
    )
    
    # Run scraper with fewer questions since we're doing deep scraping
    results = scraper.scrape(
        url="https://stackoverflow.com",
        max_questions=5,  # Reduced for detailed scraping
        save_json=True,
        save_csv=False,  # Skip CSV for complex nested data
        display_results=True
    )
    
    print(f"\n🎉 Enhanced scraping completed! Found {len(results)} questions with full content.")
    print(f"📁 Check the generated JSON file for complete question and answer data.")


if __name__ == "__main__":
    main()