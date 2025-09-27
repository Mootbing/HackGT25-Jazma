"""
Multithreaded Stack Overflow Scraper Worker
Enhanced version of the original scraper with threading and distributed coordination
"""

import threading
import queue
import time
import random
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Optional
from datetime import datetime
import json
import re

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException

from config import CONFIG
from distributed_queue import task_queue, ScrapingTask
from data_storage import DataStorage

logger = logging.getLogger(__name__)


class ThreadSafeStackOverflowScraper:
    """Thread-safe version of the Stack Overflow scraper"""
    
    def __init__(self, worker_id: str):
        self.worker_id = worker_id
        self.data_storage = DataStorage()
        self.question_count = 0
        self.session_start_time = datetime.now()
        
        # Thread-local storage for WebDriver instances
        self.local_data = threading.local()
    
    def get_driver(self) -> webdriver.Chrome:
        """Get or create a WebDriver instance for the current thread"""
        if not hasattr(self.local_data, 'driver'):
            self.local_data.driver = self._create_driver()
        return self.local_data.driver
    
    def _create_driver(self) -> webdriver.Chrome:
        """Create a new Chrome WebDriver instance"""
        chrome_options = Options()
        
        # Headless mode for EC2
        if CONFIG.scraping.headless:
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--window-size=1920,1080")
        
        # Performance optimizations for EC2
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--disable-features=VizDisplayCompositor")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--disable-logging")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-plugins")
        chrome_options.add_argument("--disable-images")
        chrome_options.add_argument("--silent")
        chrome_options.add_argument("--log-level=3")
        chrome_options.add_argument("--memory-pressure-off")
        chrome_options.add_argument("--max_old_space_size=4096")
        
        # Random user agent for better stealth
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ]
        chrome_options.add_argument(f"--user-agent={random.choice(user_agents)}")
        
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        try:
            driver = webdriver.Chrome(options=chrome_options)
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            driver.set_page_load_timeout(CONFIG.scraping.timeout)
            driver.implicitly_wait(10)
            
            return driver
            
        except Exception as e:
            logger.error(f"Failed to initialize Chrome driver: {str(e)}")
            raise WebDriverException(f"Failed to initialize Chrome driver: {str(e)}")
    
    def extract_question_id_from_url(self, url: str) -> Optional[str]:
        """Extract question ID from Stack Overflow URL"""
        try:
            # Pattern: /questions/{question_id}/...
            match = re.search(r'/questions/(\d+)/', url)
            return match.group(1) if match else None
        except Exception:
            return None
    
    def scrape_questions_from_page(self, url: str) -> List[Dict]:
        """Scrape questions from a single page"""
        questions_data = []
        driver = self.get_driver()
        
        try:
            logger.info(f"[{self.worker_id}] Scraping page: {url}")
            
            # Check if URL already scraped
            if task_queue.is_duplicate_url(url):
                logger.info(f"[{self.worker_id}] URL already scraped, skipping: {url}")
                return questions_data
            
            driver.get(url)
            
            # Random delay to appear human-like
            delay = random.uniform(CONFIG.scraping.min_delay, CONFIG.scraping.max_delay)
            time.sleep(delay)
            
            # Wait for questions to load
            wait = WebDriverWait(driver, CONFIG.scraping.timeout)
            
            # Try multiple selectors for questions
            question_selectors = [
                ".s-post-summary",
                "div[data-post-id]", 
                ".question-summary"
            ]
            
            questions = None
            for selector in question_selectors:
                try:
                    questions = wait.until(
                        EC.presence_of_all_elements_located((By.CSS_SELECTOR, selector))
                    )
                    break
                except TimeoutException:
                    continue
            
            if not questions:
                logger.warning(f"[{self.worker_id}] No questions found on page: {url}")
                return questions_data
            
            logger.info(f"[{self.worker_id}] Found {len(questions)} questions on page")
            
            for i, question_element in enumerate(questions):
                try:
                    question_data = self._extract_question_data_fast(question_element, i + 1)
                    
                    if not question_data or not question_data.get('link'):
                        continue
                    
                    # Extract question ID and check for duplicates
                    question_id = self.extract_question_id_from_url(question_data['link'])
                    if not question_id:
                        continue
                    
                    # Skip if already scraped
                    if task_queue.is_duplicate_question(question_id):
                        logger.debug(f"[{self.worker_id}] Duplicate question {question_id}, skipping")
                        continue
                    
                    # Add question ID to prevent duplicates
                    task_queue.add_question_id(question_id)
                    question_data['question_id'] = question_id
                    
                    # Scrape full content (with rate limiting)
                    if random.random() < 0.7:  # Only scrape full content for 70% of questions to speed up
                        full_content = self.scrape_full_question_content(question_data['link'])
                        question_data.update(full_content)
                    
                    questions_data.append(question_data)
                    self.question_count += 1
                    
                    # Small delay between questions
                    time.sleep(random.uniform(0.5, 1.5))
                    
                except Exception as e:
                    logger.error(f"[{self.worker_id}] Error extracting question {i + 1}: {str(e)}")
                    continue
            
            # Mark URL as scraped
            task_queue.add_scraped_url(url)
            
            return questions_data
            
        except Exception as e:
            logger.error(f"[{self.worker_id}] Error scraping page {url}: {str(e)}")
            return questions_data
    
    def _extract_question_data_fast(self, question_element, index: int) -> Optional[Dict]:
        """Fast extraction of basic question data"""
        try:
            # Extract title and link
            title_selectors = [
                "h3.s-post-summary--content-title a",
                ".s-post-summary--content h3 a",
                "a.s-link"
            ]
            
            title = "N/A"
            link = "N/A"
            
            for selector in title_selectors:
                try:
                    title_element = question_element.find_element(By.CSS_SELECTOR, selector)
                    title = title_element.get_attribute("title") or title_element.text.strip()
                    link = title_element.get_attribute("href")
                    break
                except:
                    continue
            
            if link == "N/A":
                return None
            
            # Extract metadata quickly
            votes = self._safe_extract_text(question_element, [
                ".s-post-summary--stats-item-number"
            ], "0")
            
            answers = self._safe_extract_text(question_element, [
                ".s-post-summary--stats-item:nth-child(2) .s-post-summary--stats-item-number"
            ], "0")
            
            # Skip questions without answers
            try:
                if int(answers) == 0:
                    return None
            except (ValueError, TypeError):
                # If answers is not a valid number, skip this question
                return None
            
            views = self._safe_extract_text(question_element, [
                ".s-post-summary--stats-item:nth-child(3) .s-post-summary--stats-item-number"
            ], "0")
            
            # Extract tags
            tags = []
            try:
                tag_elements = question_element.find_elements(By.CSS_SELECTOR, ".s-tag")
                tags = [tag.text.strip() for tag in tag_elements[:5]]  # Limit to first 5 tags
            except:
                pass
            
            # Extract author
            author = self._safe_extract_text(question_element, [
                ".s-user-card--link"
            ], "Anonymous")
            
            return {
                "index": index,
                "title": title,
                "link": link,
                "votes": votes,
                "answers": answers,
                "views": views,
                "tags": tags,
                "author": author,
                "scraped_at": datetime.now().isoformat(),
                "worker_id": self.worker_id
            }
            
        except Exception as e:
            logger.error(f"Error extracting question data: {str(e)}")
            return None
    
    def scrape_full_question_content(self, question_url: str) -> Dict:
        """Scrape full question and answer content (simplified for speed)"""
        full_data = {
            "question_content": "",
            "question_code": [],
            "top_answer_content": "",
            "top_answer_votes": "0",
            "top_answer_accepted": False
        }
        
        try:
            driver = self.get_driver()
            driver.get(question_url)
            
            # Quick delay
            time.sleep(random.uniform(1, 2))
            
            # Extract question content
            try:
                question_body = driver.find_element(By.CSS_SELECTOR, ".s-prose.js-post-body")
                full_data["question_content"] = question_body.text.strip()[:1000]  # Limit content
                
                # Extract code blocks
                code_elements = question_body.find_elements(By.CSS_SELECTOR, "pre code")
                full_data["question_code"] = [code.text.strip() for code in code_elements[:3]]  # Limit to 3 blocks
            except:
                pass
            
            # Extract top answer (simplified)
            try:
                top_answer = driver.find_element(By.CSS_SELECTOR, ".answer:first-of-type")
                
                # Get vote count
                try:
                    vote_element = top_answer.find_element(By.CSS_SELECTOR, ".js-vote-count")
                    full_data["top_answer_votes"] = vote_element.get_attribute("data-value") or vote_element.text.strip()
                except:
                    pass
                
                # Check if accepted
                try:
                    accepted = top_answer.find_element(By.CSS_SELECTOR, ".js-accepted-answer-indicator")
                    full_data["top_answer_accepted"] = "d-none" not in accepted.get_attribute("class")
                except:
                    pass
                
                # Get answer content
                try:
                    answer_body = top_answer.find_element(By.CSS_SELECTOR, ".s-prose.js-post-body")
                    full_data["top_answer_content"] = answer_body.text.strip()[:1000]  # Limit content
                except:
                    pass
                    
            except:
                pass
                
        except Exception as e:
            logger.error(f"Error scraping full content from {question_url}: {str(e)}")
        
        return full_data
    
    def _safe_extract_text(self, parent_element, selectors: List[str], default: str = "N/A") -> str:
        """Safely extract text using multiple selectors"""
        for selector in selectors:
            try:
                element = parent_element.find_element(By.CSS_SELECTOR, selector)
                text = element.text.strip() or element.get_attribute('textContent').strip()
                if text:
                    return text
            except:
                continue
        return default
    
    def cleanup(self):
        """Clean up WebDriver instances for this thread"""
        if hasattr(self.local_data, 'driver'):
            try:
                self.local_data.driver.quit()
            except Exception as e:
                logger.error(f"Error cleaning up driver: {str(e)}")


class DistributedScrapingWorker:
    """Main worker class that coordinates scraping tasks"""
    
    def __init__(self, worker_id: str = None):
        self.worker_id = worker_id or f"worker-{CONFIG.worker_id}-{random.randint(1000, 9999)}"
        self.scrapers = {}  # Thread ID -> Scraper instance
        self.is_running = False
        self.data_storage = DataStorage()
        
        # Statistics
        self.total_questions_scraped = 0
        self.tasks_completed = 0
        self.start_time = datetime.now()
        
        logger.info(f"Initialized worker: {self.worker_id}")
    
    def run_worker(self) -> None:
        """Main worker loop - processes tasks from the distributed queue"""
        self.is_running = True
        
        logger.info(f"[{self.worker_id}] Starting worker with {CONFIG.scraping.max_workers} threads")
        
        with ThreadPoolExecutor(max_workers=CONFIG.scraping.max_workers) as executor:
            while self.is_running:
                try:
                    # Get next task from queue
                    task = task_queue.get_next_task(self.worker_id)
                    
                    if not task:
                        logger.info(f"[{self.worker_id}] No tasks available, waiting...")
                        time.sleep(10)
                        continue
                    
                    # Submit task to thread pool
                    future = executor.submit(self.process_task, task)
                    
                    # Wait for task completion (with timeout)
                    try:
                        questions_scraped = future.result(timeout=300)  # 5 minute timeout per task
                        task_queue.complete_task(task, questions_scraped)
                        self.tasks_completed += 1
                        self.total_questions_scraped += questions_scraped
                        
                        logger.info(f"[{self.worker_id}] Task {task.task_id} completed: {questions_scraped} questions")
                        
                    except Exception as e:
                        logger.error(f"[{self.worker_id}] Task {task.task_id} failed: {str(e)}")
                        task_queue.fail_task(task, str(e))
                    
                    # Send heartbeat
                    task_queue.register_worker_heartbeat(self.worker_id)
                    
                except KeyboardInterrupt:
                    logger.info(f"[{self.worker_id}] Received interrupt signal, stopping...")
                    self.is_running = False
                    break
                    
                except Exception as e:
                    logger.error(f"[{self.worker_id}] Unexpected error: {str(e)}")
                    time.sleep(5)
        
        self.cleanup_scrapers()
        logger.info(f"[{self.worker_id}] Worker stopped. Total questions scraped: {self.total_questions_scraped}")
    
    def process_task(self, task: ScrapingTask) -> int:
        """Process a single scraping task"""
        thread_id = threading.current_thread().ident
        
        # Get or create scraper for this thread
        if thread_id not in self.scrapers:
            self.scrapers[thread_id] = ThreadSafeStackOverflowScraper(self.worker_id)
        
        scraper = self.scrapers[thread_id]
        questions_scraped = 0
        
        try:
            logger.info(f"[{self.worker_id}] Processing task {task.task_id}: pages {task.start_page}-{task.end_page}")
            
            # Generate URLs for the page range
            base_url = task.url.split('?')[0]  # Remove existing query params
            
            for page in range(task.start_page, task.end_page + 1):
                if not self.is_running:
                    break
                
                page_url = f"{base_url}?page={page}"
                questions_data = scraper.scrape_questions_from_page(page_url)
                
                if questions_data:
                    # Store questions in database
                    self.data_storage.store_questions_batch(questions_data)
                    questions_scraped += len(questions_data)
                    
                    logger.info(f"[{self.worker_id}] Page {page}: {len(questions_data)} questions")
                
                # Rate limiting between pages
                delay = random.uniform(CONFIG.scraping.min_delay, CONFIG.scraping.max_delay)
                time.sleep(delay)
            
        except Exception as e:
            logger.error(f"[{self.worker_id}] Error processing task {task.task_id}: {str(e)}")
            raise
        
        return questions_scraped
    
    def cleanup_scrapers(self):
        """Clean up all scraper instances"""
        for scraper in self.scrapers.values():
            scraper.cleanup()
        self.scrapers.clear()
    
    def get_worker_stats(self) -> Dict:
        """Get current worker statistics"""
        runtime = datetime.now() - self.start_time
        
        return {
            "worker_id": self.worker_id,
            "tasks_completed": self.tasks_completed,
            "total_questions_scraped": self.total_questions_scraped,
            "runtime_minutes": runtime.total_seconds() / 60,
            "questions_per_minute": self.total_questions_scraped / (runtime.total_seconds() / 60) if runtime.total_seconds() > 0 else 0,
            "is_running": self.is_running,
            "active_threads": len(self.scrapers)
        }


def main():
    """Main function to start a distributed scraping worker"""
    import sys
    
    # Set up logging
    logging.basicConfig(
        level=getattr(logging, CONFIG.monitoring.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    worker_id = sys.argv[1] if len(sys.argv) > 1 else None
    worker = DistributedScrapingWorker(worker_id)
    
    try:
        worker.run_worker()
    except KeyboardInterrupt:
        logger.info("Shutting down worker...")
        worker.is_running = False
    except Exception as e:
        logger.error(f"Worker crashed: {str(e)}")
        raise


if __name__ == "__main__":
    main()