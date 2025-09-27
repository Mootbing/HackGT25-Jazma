#!/bin/bash
# Local deployment script - Set up everything on a single machine

set -e

echo "🏠 Setting up Local Distributed Stack Overflow Scraper"

# Check Python version
python_version=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
required_version="3.8"

if ! python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)" 2>/dev/null; then
    echo "❌ Python 3.8+ required. Current version: $python_version"
    exit 1
fi

echo "✅ Python version: $python_version"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements_distributed.txt

# Install Chrome and ChromeDriver (Ubuntu/Debian)
if command -v apt-get >/dev/null 2>&1; then
    echo "🌐 Installing Chrome and ChromeDriver..."
    
    # Install Chrome
    if ! command -v google-chrome >/dev/null 2>&1; then
        wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
        echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" | sudo tee /etc/apt/sources.list.d/google.list
        sudo apt-get update
        sudo apt-get install -y google-chrome-stable
    fi
    
    # Install ChromeDriver
    if ! command -v chromedriver >/dev/null 2>&1; then
        CHROME_DRIVER_VERSION=$(curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE)
        wget -N https://chromedriver.storage.googleapis.com/$CHROME_DRIVER_VERSION/chromedriver_linux64.zip
        unzip chromedriver_linux64.zip
        chmod +x chromedriver
        sudo mv chromedriver /usr/local/bin/
        rm chromedriver_linux64.zip
    fi
    
    echo "✅ Chrome and ChromeDriver installed"

elif command -v brew >/dev/null 2>&1; then
    # macOS with Homebrew
    echo "🍺 Installing Chrome and ChromeDriver via Homebrew..."
    brew install --cask google-chrome
    brew install chromedriver
    
    echo "✅ Chrome and ChromeDriver installed"

else
    echo "⚠️  Please install Chrome and ChromeDriver manually"
    echo "   Chrome: https://www.google.com/chrome/"
    echo "   ChromeDriver: https://chromedriver.chromium.org/"
fi

# Set up Redis (using Docker)
echo "🗄️ Setting up Redis..."

if command -v docker >/dev/null 2>&1; then
    # Check if Redis container is already running
    if ! docker ps | grep -q "redis-scraper"; then
        echo "🐳 Starting Redis container..."
        docker run -d \
            --name redis-scraper \
            -p 6379:6379 \
            --restart unless-stopped \
            redis:7-alpine redis-server --appendonly yes
    else
        echo "✅ Redis container already running"
    fi
else
    echo "⚠️  Docker not found. Please install Redis manually:"
    echo "   Ubuntu/Debian: sudo apt-get install redis-server"
    echo "   macOS: brew install redis"
    echo "   Or use Redis Cloud: https://redis.com/"
fi

# Set up MongoDB (using Docker)
echo "🍃 Setting up MongoDB..."

if command -v docker >/dev/null 2>&1; then
    # Check if MongoDB container is already running
    if ! docker ps | grep -q "mongo-scraper"; then
        echo "🐳 Starting MongoDB container..."
        docker run -d \
            --name mongo-scraper \
            -p 27017:27017 \
            -e MONGO_INITDB_ROOT_USERNAME=admin \
            -e MONGO_INITDB_ROOT_PASSWORD=password123 \
            --restart unless-stopped \
            -v mongodb_data:/data/db \
            mongo:7
    else
        echo "✅ MongoDB container already running"
    fi
else
    echo "⚠️  Docker not found. Please install MongoDB manually:"
    echo "   Ubuntu/Debian: sudo apt-get install mongodb"
    echo "   macOS: brew install mongodb/brew/mongodb-community"
    echo "   Or use MongoDB Atlas: https://www.mongodb.com/atlas"
fi

# Create local .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "⚙️ Creating local .env configuration..."
    cp .env.example .env
    
    # Update for local development
    sed -i.bak 's/REDIS_HOST=.*/REDIS_HOST=localhost/' .env
    sed -i.bak 's/MONGO_URI=.*/MONGO_URI=mongodb:\/\/admin:password123@localhost:27017\//' .env
    sed -i.bak 's/INSTANCE_TYPE=.*/INSTANCE_TYPE=local/' .env
    sed -i.bak 's/HEADLESS=.*/HEADLESS=false/' .env  # Show browser for local testing
    sed -i.bak 's/MAX_WORKERS=.*/MAX_WORKERS=3/' .env  # Conservative for local
    
    rm -f .env.bak
    
    echo "✅ Local .env configuration created"
fi

# Test the setup
echo "🧪 Testing the setup..."

# Test Redis connection
python3 -c "
import redis
try:
    r = redis.Redis(host='localhost', port=6379, decode_responses=True)
    r.ping()
    print('✅ Redis connection: OK')
except Exception as e:
    print(f'❌ Redis connection failed: {e}')
    print('   Make sure Redis is running: docker ps')
"

# Test MongoDB connection
python3 -c "
try:
    from pymongo import MongoClient
    client = MongoClient('mongodb://admin:password123@localhost:27017/')
    client.server_info()
    print('✅ MongoDB connection: OK')
except Exception as e:
    print(f'❌ MongoDB connection failed: {e}')
    print('   Make sure MongoDB is running: docker ps')
"

# Test Selenium
python3 -c "
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(options=options)
    driver.get('https://google.com')
    print('✅ Selenium/Chrome: OK')
    driver.quit()
except Exception as e:
    print(f'❌ Selenium/Chrome failed: {e}')
    print('   Make sure Chrome and ChromeDriver are installed')
"

echo ""
echo "🎉 Local setup completed!"
echo ""
echo "📋 Ready to run:"
echo "   # Activate virtual environment"
echo "   source venv/bin/activate"
echo ""
echo "   # Start local scraping (small test)"
echo "   python main.py local --workers 3 --target 1000"
echo ""
echo "   # Start local scraping (full scale)"
echo "   python main.py local --workers 5 --target 100000"
echo ""
echo "🔧 Monitor your scraping:"
echo "   - Health: http://localhost:8080/health"
echo "   - Stats: http://localhost:8080/stats"
echo "   - Metrics: http://localhost:9090/metrics"
echo ""
echo "📊 Docker containers:"
echo "   - Redis: docker logs redis-scraper"
echo "   - MongoDB: docker logs mongo-scraper"
echo ""
echo "⚡ The scraper will:"
echo "   • Distribute work across multiple threads"
echo "   • Avoid duplicate questions automatically"
echo "   • Store data in MongoDB with full deduplication"
echo "   • Provide real-time progress monitoring"
echo "   • Export final results to JSON"