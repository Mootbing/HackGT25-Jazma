#!/usr/bin/env python3
"""
Script to run the MCP Bugfix Context Server.

This script provides an easy way to start the server with proper configuration.
"""

import os
import sys
import asyncio
from pathlib import Path


def check_environment():
    """Check if environment is properly configured."""
    required_vars = ["SUPABASE_URL", "SUPABASE_KEY", "OPENAI_API_KEY"]
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        print("Please set these in your .env file or environment")
        return False
    
    return True


async def main():
    """Main function to run the server."""
    print("🚀 Starting MCP Bugfix Context Server...")
    
    # Check environment
    if not check_environment():
        sys.exit(1)
    
    # Add src to Python path
    src_path = Path(__file__).parent.parent / "src"
    sys.path.insert(0, str(src_path))
    
    try:
        # Import and run the server
        from mcp_bugfix_server.server.mcp_server import main as server_main
        await server_main()
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
