from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time

def create_driver():
    """Create and configure Chrome WebDriver with automatic driver management"""
    chrome_options = Options()
    
    # Optional: Run in headless mode (uncomment the line below)
    # chrome_options.add_argument("--headless")
    
    # Additional options for better compatibility
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # Automatically download and setup ChromeDriver
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    # Execute script to prevent detection
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver

def scrape_stackoverflow():
    """Main scraping function for Stack Overflow"""
    driver = None
    
    try:
        print("Initializing Chrome browser...")
        driver = create_driver()
        
        print("Navigating to Stack Overflow...")
        driver.get("https://stackoverflow.com")
        
        # Wait for page to load
        wait = WebDriverWait(driver, 10)
        
        # Wait for the main content to load
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "s-topbar")))
        
        print("Successfully loaded Stack Overflow!")
        print(f"Page title: {driver.title}")
        print(f"Current URL: {driver.current_url}")
        
        # Example: Get the latest questions from the homepage
        print("\nFetching latest questions...")
        
        # Wait for questions to load
        questions = wait.until(EC.presence_of_all_elements_located(
            (By.CSS_SELECTOR, ".s-post-summary--content h3 a")
        ))
        
        print(f"Found {len(questions)} questions:")
        
        for i, question in enumerate(questions[:5], 1):  # Show first 5 questions
            title = question.get_attribute("title") or question.text
            link = question.get_attribute("href")
            print(f"{i}. {title}")
            print(f"   Link: {link}\n")
        
        # Keep browser open for a few seconds to see the result
        print("Keeping browser open for 5 seconds...")
        time.sleep(5)
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        
    finally:
        if driver:
            print("Closing browser...")
            driver.quit()

def main():
    """Main function"""
    print("Stack Overflow Web Scraper")
    print("=" * 30)
    scrape_stackoverflow()

if __name__ == "__main__":
    main()