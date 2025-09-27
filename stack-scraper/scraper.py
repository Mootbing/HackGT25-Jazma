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
        self.scraped_ids_file = "scraped_question_ids.txt"
        self.scraped_ids = set()
        self.persistent_json_file = "stackoverflow_questions_persistent.json"
        
    def load_scraped_ids(self) -> None:
        """Load previously scraped question IDs from log file"""
        try:
            with open(self.scraped_ids_file, 'r', encoding='utf-8') as f:
                self.scraped_ids = set(line.strip() for line in f if line.strip())
            print(f"📋 Loaded {len(self.scraped_ids)} previously scraped question IDs")
        except FileNotFoundError:
            print("📋 No previous scrape log found, starting fresh")
            self.scraped_ids = set()
    
    def save_scraped_id(self, question_id: str) -> None:
        """Save a question ID to the log file"""
        try:
            with open(self.scraped_ids_file, 'a', encoding='utf-8') as f:
                f.write(f"{question_id}\n")
            self.scraped_ids.add(question_id)
        except Exception as e:
            print(f"⚠️  Warning: Could not save question ID {question_id}: {e}")
    
    def extract_question_id_from_url(self, url: str) -> str:
        """Extract question ID from Stack Overflow URL"""
        try:
            # URL format: https://stackoverflow.com/questions/{id}/title-slug
            parts = url.split('/questions/')
            if len(parts) > 1:
                question_part = parts[1].split('/')[0]
                return question_part
        except Exception:
            pass
        return None
    
    def is_question_already_scraped(self, question_id: str) -> bool:
        """Check if question ID has already been scraped"""
        return question_id in self.scraped_ids
    
    def load_existing_json_data(self) -> List[Dict]:
        """Load existing data from persistent JSON file"""
        try:
            with open(self.persistent_json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"📚 Loaded {len(data)} existing questions from {self.persistent_json_file}")
            return data
        except FileNotFoundError:
            print(f"📚 No existing persistent file found, creating {self.persistent_json_file}")
            return []
        except json.JSONDecodeError:
            print(f"⚠️  Warning: Corrupted JSON file, starting fresh")
            return []
    
    def save_to_persistent_json(self, all_data: List[Dict]) -> bool:
        """Save all data to the persistent JSON file"""
        try:
            with open(self.persistent_json_file, 'w', encoding='utf-8') as f:
                json.dump(all_data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"❌ Error saving to persistent JSON: {e}")
            return False
    
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
            
            processed_count = 0
            for i, question in enumerate(questions):
                if processed_count >= max_questions:
                    break
                    
                try:
                    question_data = self._extract_question_data(question, i + 1)
                    if question_data and question_data.get('link') != 'N/A':
                        # Extract question ID and check if already scraped
                        question_id = self.extract_question_id_from_url(question_data['link'])
                        if question_id and self.is_question_already_scraped(question_id):
                            print(f"  ⏭️  Skipping question {i + 1} - already scraped (ID: {question_id})")
                            continue
                        
                        # Scrape full question and answer content
                        print(f"  🔗 Clicking on question {i + 1}: {question_data['title'][:60]}... (ID: {question_id})")
                        full_content = self.scrape_full_question_and_answer(question_data['link'])
                        
                        # Merge full content with basic data
                        question_data.update(full_content)
                        question_data['question_id'] = question_id  # Add question ID to data
                        questions_data.append(question_data)
                        processed_count += 1
                        
                        # Log the question ID
                        if question_id:
                            self.save_scraped_id(question_id)
                        
                        # Save to persistent JSON incrementally
                        if hasattr(self, 'persistent_data'):
                            formatted_question = self.convert_to_new_format(question_data)
                            self.persistent_data.append(formatted_question)
                            self.save_to_persistent_json(self.persistent_data)
                            print(f"  💾 Added to persistent JSON (Total: {len(self.persistent_data)} questions)")
                        
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
                ".s-post-summary--stats-item[title*='answer'] .s-post-summary--stats-item-number",
                ".s-post-summary--stats-item:nth-child(2) .s-post-summary--stats-item-number",
                ".status strong",
                "[title*='answer']",
                ".js-answer-count"
            ], "0")
            
            # Skip questions without answers
            try:
                if int(answer_count) == 0:
                    print(f"  ⏭️  Skipping question {index} - no answers (title: {title[:50]}...)")
                    return None
            except (ValueError, TypeError):
                # If answer_count is not a valid number, skip this question
                print(f"  ⏭️  Skipping question {index} - invalid answer count: '{answer_count}'")
                return None
            
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
    
    def navigate_to_page(self, page_number: int) -> bool:
        """
        Navigate to a specific page of Stack Overflow questions
        
        Args:
            page_number: Page number to navigate to
            
        Returns:
            bool: Success status
        """
        try:
            url = f"https://stackoverflow.com/questions?tab=newest&page={page_number}"
            print(f"📄 Navigating to page {page_number}: {url}")
            return self.navigate_to_stackoverflow(url)
        except Exception as e:
            print(f"Error navigating to page {page_number}: {str(e)}")
            return False
    
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
            print(f"📈 Total questions saved: {len(data)}")
            return filename
        except Exception as e:
            print(f"Error saving to JSON: {str(e)}")
            return ""
    
    def save_single_question_incremental(self, question_data: Dict, filename: str) -> bool:
        """Save a single question incrementally to existing JSON file"""
        try:
            # Try to read existing file
            existing_data = []
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                existing_data = []
            
            # Convert to new format
            formatted_question = self.convert_to_new_format(question_data)
            
            # Add new question
            existing_data.append(formatted_question)
            
            # Save back to file
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, indent=2, ensure_ascii=False)
            
            print(f"  💾 Saved question {len(existing_data)} to {filename}")
            return True
            
        except Exception as e:
            print(f"  ❌ Error saving incremental data: {str(e)}")
            return False
    
    def convert_to_new_format(self, question_data: Dict) -> Dict:
        """Convert question data to the new format matching the schema"""
        # Extract code blocks from question and answer
        question_code = "\n\n".join(question_data.get('question_code', []))
        answer_code = "\n\n".join(question_data.get('top_answer_code', []))
        all_code = "\n\n".join([question_code, answer_code]).strip()
        
        # Determine type based on content
        question_type = "solution" if question_data.get('top_answer_content') else "bug"
        
        # Extract tags
        tags = question_data.get('tags', [])
        if isinstance(tags, str):
            tags = [tag.strip() for tag in tags.split(',') if tag.strip()]
        
        # Create metadata
        metadata = {
            "project": "stackoverflow",
            "repo": None,
            "commit": None,
            "branch": None,
            "os": None,
            "runtime": None,
            "language": self.extract_language_from_tags(tags),
            "framework": self.extract_framework_from_tags(tags)
        }
        
        return {
            "type": question_type,
            "title": question_data.get('title', ''),
            "body": question_data.get('question_content', ''),
            "stack_trace": None,  # SO questions don't typically have stack traces in structured format
            "code": all_code if all_code else None,
            "repro_steps": question_data.get('excerpt', ''),
            "root_cause": None,
            "resolution": question_data.get('top_answer_content', ''),
            "severity": self.determine_severity(question_data),
            "tags": tags,
            "metadata": metadata,
            "idempotency_key": question_data.get('question_id'),  # Use question ID as idempotency key
            "related_ids": None,
            "source_url": question_data.get('link', ''),
            "question_id": question_data.get('question_id', ''),
            "votes": question_data.get('votes', '0'),
            "answers_count": question_data.get('answers', '0'),
            "views": question_data.get('views', '0'),
            "author": question_data.get('author', ''),
            "scraped_at": question_data.get('scraped_at', '')
        }
    
    def extract_language_from_tags(self, tags: List[str]) -> str:
        """Extract programming language from tags"""
        language_tags = {'python', 'javascript', 'java', 'c#', 'cpp', 'c++', 'c', 'php', 'ruby', 'go', 'rust', 'swift', 'kotlin', 'scala', 'r', 'matlab', 'typescript', 'html', 'css'}
        for tag in tags:
            if tag.lower() in language_tags:
                return tag.lower()
        return None
    
    def extract_framework_from_tags(self, tags: List[str]) -> str:
        """Extract framework from tags"""
        framework_tags = {'react', 'angular', 'vue', 'django', 'flask', 'spring', 'express', 'laravel', 'rails', 'asp.net', 'nodejs', 'jquery'}
        for tag in tags:
            if tag.lower() in framework_tags:
                return tag.lower()
        return None
    
    def determine_severity(self, question_data: Dict) -> str:
        """Determine severity based on votes and views"""
        try:
            votes = int(question_data.get('votes', '0'))
            views = int(question_data.get('views', '0'))
            
            if votes >= 10 or views >= 1000:
                return "high"
            elif votes >= 5 or views >= 500:
                return "medium"
            else:
                return "low"
        except (ValueError, TypeError):
            return "low"
    
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
        print(f"📊 ENHANCED SCRAPING RESULTS: {len(questions)} QUESTIONS WITH FULL CONTENT")
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
    
    def scrape_continuous(self, 
                         max_questions_total: int = 50,
                         max_questions_per_page: int = 10,
                         start_page: int = 1,
                         max_pages: int = 10,
                         save_json: bool = True,
                         save_csv: bool = False,
                         display_results: bool = True) -> List[Dict]:
        """
        Continuous scraping method that goes through multiple pages
        
        Args:
            max_questions_total: Maximum total questions to collect
            max_questions_per_page: Maximum questions to try per page
            start_page: Page number to start from
            max_pages: Maximum number of pages to scrape
            save_json: Save results to JSON file
            save_csv: Save results to CSV file
            display_results: Print results to console
            
        Returns:
            List of scraped question data
        """
        all_questions = []
        current_page = start_page
        
        try:
            print("🚀 Starting continuous Stack Overflow scraper...")
            print(f"Target: {max_questions_total} total questions")
            print(f"Max per page: {max_questions_per_page}")
            print(f"Starting from page: {start_page}")
            print(f"Max pages: {max_pages}")
            print(f"Headless mode: {self.headless}")
            
            # Load existing data and IDs
            self.load_scraped_ids()
            self.persistent_data = self.load_existing_json_data()
            print(f"📊 Starting with {len(self.persistent_data)} existing questions")
            
            # Set up incremental saving filename (for backup/session log)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.current_filename = f"stackoverflow_session_{timestamp}.json"
            print(f"💾 Session backup saving to: {self.current_filename}")
            print(f"💾 Persistent data in: {self.persistent_json_file}")
            
            # Initialize driver once
            self.driver = self.setup_driver()
            
            while len(all_questions) < max_questions_total and (current_page - start_page) < max_pages:
                print(f"\n{'='*80}")
                print(f"📄 SCRAPING PAGE {current_page} - Progress: {len(all_questions)}/{max_questions_total} questions")
                print(f"{'='*80}")
                
                # Navigate to current page
                if not self.navigate_to_page(current_page):
                    print(f"❌ Failed to load page {current_page}, stopping...")
                    break
                
                # Extract questions from this page
                remaining_needed = max_questions_total - len(all_questions)
                questions_to_get = min(max_questions_per_page, remaining_needed)
                
                page_questions = self.extract_questions(questions_to_get)
                
                if page_questions:
                    all_questions.extend(page_questions)
                    print(f"✅ Page {current_page}: Added {len(page_questions)} questions")
                    print(f"📊 Total collected so far: {len(all_questions)}/{max_questions_total}")
                else:
                    print(f"⚠️  Page {current_page}: No valid questions found")
                
                # Check if we have enough questions
                if len(all_questions) >= max_questions_total:
                    print(f"\n🎯 Target reached! Collected {len(all_questions)} questions")
                    break
                
                # Move to next page
                current_page += 1
                
                # Add delay between pages
                if current_page <= start_page + max_pages:
                    delay = random.uniform(2, 4)
                    print(f"⏰ Waiting {delay:.1f}s before next page...")
                    time.sleep(delay)
            
            if all_questions:
                print(f"\n✅ Continuous scraping completed! Session: {len(all_questions)} new questions")
                print(f"� Total questions in database: {len(self.persistent_data)}")
                print(f"📁 Persistent data: {self.persistent_json_file}")
                print(f"📋 Question IDs logged: {self.scraped_ids_file}")
                
                # Display results
                if display_results:
                    self.print_results(all_questions)
                
                # Save CSV if requested (JSON already saved incrementally)
                if save_csv:
                    self.save_to_csv(all_questions)
            else:
                print("❌ No new questions were collected")
                print(f"📊 Total questions in database: {len(self.persistent_data)}")
            
            # Keep browser open briefly if not headless
            if not self.headless and all_questions:
                print("\nKeeping browser open for 3 seconds...")
                time.sleep(3)
                
        except Exception as e:
            print(f"❌ Continuous scraping failed: {str(e)}")
            
        finally:
            self.cleanup()
        
        return all_questions
    
    def scrape(self, 
               url: str = "https://stackoverflow.com",
               max_questions: int = 10,
               save_json: bool = True,
               save_csv: bool = False,
               display_results: bool = True) -> List[Dict]:
        """
        Single page scraping method (legacy)
        
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
    print("Stack Overflow Enhanced Web Scraper v2.2 - Continuous Mode")
    print("=" * 60)
    print("🔥 Now scraping full question and answer content across multiple pages!")
    print("📊 This will take longer due to individual page visits and navigation...")
    print()
    
    # Configuration
    scraper = StackOverflowScraper(
        headless=False,  # Set to True for headless mode
        timeout=20  # Increased timeout for page loads
    )
    
    # Run continuous scraper across multiple pages
    results = scraper.scrape_continuous(
        max_questions_total=20,   # Total questions to collect
        max_questions_per_page=5, # Questions to try per page
        start_page=1,            # Starting page number
        max_pages=10,            # Maximum pages to check
        save_json=True,
        save_csv=False,          # Skip CSV for complex nested data
        display_results=True
    )
    
    print(f"\n🎉 Continuous enhanced scraping completed! Found {len(results)} questions with full content.")
    print(f"📁 Check the generated JSON file for complete question and answer data.")
    print(f"🔄 Scraper navigated through multiple pages to find questions with answers.")


if __name__ == "__main__":
    main()