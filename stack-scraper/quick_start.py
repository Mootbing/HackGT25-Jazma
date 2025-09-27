#!/usr/bin/env python3
"""
Quick Start Guide for Distributed Stack Overflow Scraper
Run this to get started quickly with the right configuration
"""

import os
import sys
import subprocess
import shutil

def check_requirements():
    """Check if basic requirements are available"""
    print("🔍 Checking requirements...")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required")
        return False
    
    print("✅ Python version OK")
    
    # Check if Chrome is available
    chrome_paths = [
        "google-chrome",
        "chrome", 
        "chromium-browser",
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    ]
    
    chrome_found = False
    for chrome_path in chrome_paths:
        if shutil.which(chrome_path) or os.path.exists(chrome_path):
            chrome_found = True
            break
    
    if not chrome_found:
        print("⚠️  Chrome not found. Please install Google Chrome")
        return False
    
    print("✅ Chrome found")
    
    # Check Docker
    if shutil.which("docker"):
        print("✅ Docker found")
    else:
        print("⚠️  Docker not found. You'll need to install Redis and MongoDB manually")
    
    return True

def setup_environment():
    """Set up the basic environment"""
    print("\n📦 Setting up environment...")
    
    # Create virtual environment if it doesn't exist
    if not os.path.exists("venv"):
        print("Creating virtual environment...")
        subprocess.run([sys.executable, "-m", "venv", "venv"])
    
    # Install basic requirements
    print("Installing requirements...")
    pip_path = os.path.join("venv", "Scripts" if os.name == 'nt' else "bin", "pip")
    
    try:
        subprocess.run([pip_path, "install", "selenium", "redis", "pymongo"], check=True)
        print("✅ Basic requirements installed")
    except subprocess.CalledProcessError:
        print("❌ Failed to install requirements")
        return False
    
    return True

def create_basic_env():
    """Create a basic .env file"""
    if not os.path.exists(".env"):
        print("\n⚙️ Creating basic .env configuration...")
        
        env_content = """# Basic Local Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
MONGO_URI=mongodb://localhost:27017/
MONGO_DB=stackoverflow_scraper
MAX_WORKERS=3
HEADLESS=false
INSTANCE_TYPE=local
TARGET_QUESTIONS=1000
LOG_LEVEL=INFO
"""
        
        with open(".env", "w") as f:
            f.write(env_content)
        
        print("✅ Basic .env created")

def show_next_steps():
    """Show what to do next"""
    print("\n🎉 Quick setup complete!")
    print("\n📋 Next Steps:")
    print("\n1. 🐳 Start Docker services (if available):")
    print("   docker run -d --name redis-scraper -p 6379:6379 redis:alpine")
    print("   docker run -d --name mongo-scraper -p 27017:27017 mongo")
    print("\n2. 🧪 Test the scraper (small scale):")
    
    if os.name == 'nt':  # Windows
        print("   .\\venv\\Scripts\\activate")
        print("   python main.py local --workers 2 --target 100")
    else:  # Unix/Linux/Mac
        print("   source venv/bin/activate")
        print("   python main.py local --workers 2 --target 100")
    
    print("\n3. 📈 Scale up for production:")
    print("   python main.py local --workers 5 --target 10000")
    
    print("\n4. ☁️  For cloud deployment:")
    print("   - Configure AWS CLI: aws configure") 
    print("   - Run: chmod +x deploy_aws.sh && ./deploy_aws.sh")
    print("   - Deploy: python main.py cloud --instances 10 --target 100000")
    
    print("\n🔧 Monitor your scraping:")
    print("   Health: http://localhost:8080/health")
    print("   Stats:  http://localhost:8080/stats")
    
    print("\n📊 Expected Performance:")
    print("   Local (5 workers): ~300-500 questions/minute")
    print("   Cloud (10 instances): ~3,000-5,000 questions/minute")
    print("   Target 100k questions: 20-35 minutes with cloud setup")

def main():
    print("🚀 Distributed Stack Overflow Scraper - Quick Start")
    print("=" * 60)
    
    if not check_requirements():
        print("\n❌ Please install missing requirements and run again")
        return
    
    if not setup_environment():
        print("\n❌ Environment setup failed")
        return
    
    create_basic_env()
    show_next_steps()
    
    print(f"\n✨ Ready to scrape! Run this from {os.getcwd()}")

if __name__ == "__main__":
    main()