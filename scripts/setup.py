#!/usr/bin/env python3
"""
Setup script for the MCP Bugfix Context Server.

This script helps with initial setup and configuration.
"""

import os
import sys
import subprocess
from pathlib import Path


def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        sys.exit(1)
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")


def install_dependencies():
    """Install Python dependencies."""
    print("📦 Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        sys.exit(1)


def setup_environment():
    """Set up environment file."""
    env_example = Path("config.env.example")
    env_file = Path(".env")
    
    if env_file.exists():
        print("⚠️  .env file already exists, skipping creation")
        return
    
    if not env_example.exists():
        print("❌ config.env.example not found")
        sys.exit(1)
    
    print("🔧 Creating .env file...")
    with open(env_example, "r") as f:
        content = f.read()
    
    with open(env_file, "w") as f:
        f.write(content)
    
    print("✅ .env file created. Please edit it with your credentials.")


def check_credentials():
    """Check if required credentials are set."""
    print("🔑 Checking credentials...")
    
    required_vars = ["SUPABASE_URL", "SUPABASE_KEY", "OPENAI_API_KEY"]
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"⚠️  Missing environment variables: {', '.join(missing_vars)}")
        print("Please set these in your .env file")
        return False
    
    print("✅ All required credentials are set")
    return True


def test_supabase_connection():
    """Test Supabase connection."""
    print("🔌 Testing Supabase connection...")
    try:
        from src.mcp_bugfix_server.ingestion import SupabaseClient
        client = SupabaseClient()
        print("✅ Supabase connection successful")
        return True
    except Exception as e:
        print(f"❌ Supabase connection failed: {e}")
        return False


def test_openai_connection():
    """Test OpenAI connection."""
    print("🤖 Testing OpenAI connection...")
    try:
        from src.mcp_bugfix_server.ingestion import EmbeddingService
        service = EmbeddingService()
        # Test with a simple embedding
        embedding = service.embed("test")
        if embedding and len(embedding) > 0:
            print("✅ OpenAI connection successful")
            return True
        else:
            print("❌ OpenAI returned empty embedding")
            return False
    except Exception as e:
        print(f"❌ OpenAI connection failed: {e}")
        return False


def run_tests():
    """Run the test suite."""
    print("🧪 Running tests...")
    try:
        subprocess.check_call([sys.executable, "-m", "pytest", "tests/", "-v"])
        print("✅ All tests passed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Tests failed: {e}")
        return False


def main():
    """Main setup function."""
    print("🚀 MCP Bugfix Context Server Setup")
    print("=" * 40)
    
    # Check Python version
    check_python_version()
    
    # Install dependencies
    install_dependencies()
    
    # Set up environment
    setup_environment()
    
    # Check if credentials are available
    if not check_credentials():
        print("\n⚠️  Setup incomplete. Please configure your .env file and run again.")
        return
    
    # Test connections
    supabase_ok = test_supabase_connection()
    openai_ok = test_openai_connection()
    
    if not (supabase_ok and openai_ok):
        print("\n❌ Connection tests failed. Please check your credentials.")
        return
    
    # Run tests
    if not run_tests():
        print("\n⚠️  Some tests failed, but setup is mostly complete.")
        return
    
    print("\n🎉 Setup completed successfully!")
    print("\nNext steps:")
    print("1. Run the MCP server: python -m src.mcp_bugfix_server.server.mcp_server")
    print("2. Try the example: python examples/example_usage.py")
    print("3. Check the README for more information")


if __name__ == "__main__":
    main()
