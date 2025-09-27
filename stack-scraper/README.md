# Stack Overflow Web Scraper

A simple web scraper built with Selenium that opens a Chrome browser and navigates to Stack Overflow.

## Features

- Opens Chrome browser automatically
- Navigates to Stack Overflow
- Scrapes and displays the latest questions from the homepage
- Includes error handling and cleanup
- Two versions available: manual ChromeDriver setup and automatic setup

## Setup Instructions

### 1. Install Python Dependencies

```powershell
pip install -r requirements.txt
```

### 2. Chrome Browser

Make sure you have Google Chrome installed on your system.

### 3. ChromeDriver (for scraper.py)

If using `scraper.py`, you need to install ChromeDriver manually:

1. Check your Chrome version: `chrome://version/`
2. Download matching ChromeDriver from https://chromedriver.chromium.org/
3. Add ChromeDriver to your system PATH

### 4. Automatic ChromeDriver (for scraper_auto.py) - Recommended

The `scraper_auto.py` version automatically downloads and manages ChromeDriver for you using webdriver-manager.

## Usage

### Run the basic scraper:
```powershell
python scraper.py
```

### Run the auto-setup scraper (recommended):
```powershell
python scraper_auto.py
```

## What it does

1. Opens a Chrome browser window
2. Navigates to https://stackoverflow.com
3. Waits for the page to load
4. Extracts the titles and links of the first 5 questions
5. Displays the information in the console
6. Keeps the browser open for 5 seconds
7. Closes the browser automatically

## Customization

### Headless Mode
To run without opening a browser window, uncomment this line in either script:
```python
chrome_options.add_argument("--headless")
```

### Scrape More Questions
Change this line to get more questions:
```python
for i, question in enumerate(questions[:10], 1):  # Changed from 5 to 10
```

### Add More Scraping
You can extend the script to scrape additional information like:
- Question votes
- Answer counts
- Tags
- User information
- Question content

## Requirements

- Python 3.6+
- Google Chrome browser
- Internet connection

## Files

- `scraper.py` - Basic version requiring manual ChromeDriver setup
- `scraper_auto.py` - Recommended version with automatic ChromeDriver management
- `requirements.txt` - Python dependencies
- `README.md` - This file