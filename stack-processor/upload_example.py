#!/usr/bin/env python3
"""
Usage example for the Supabase poster

To use this script:
1. Install dependencies: pip install -r requirements.txt
2. Set environment variables:
   - SUPABASE_URL=https://your-project.supabase.co
   - SUPABASE_ANON_KEY=your-anon-key
3. Run: python upload_example.py
"""

import os
import asyncio
from pathlib import Path
from supabase_poster import SupabasePoster, SupabaseConfig

async def upload_sample():
    """Upload converted.json to Supabase"""
    
    # Check environment variables
    if not os.getenv('SUPABASE_URL') or not os.getenv('SUPABASE_ANON_KEY'):
        print("❌ Please set SUPABASE_URL and SUPABASE_ANON_KEY environment variables")
        print("Example:")
        print('export SUPABASE_URL="https://your-project.supabase.co"')
        print('export SUPABASE_ANON_KEY="your-anon-key"')
        return
    
    try:
        # Initialize configuration
        config = SupabaseConfig.from_env()
        poster = SupabasePoster(config)
        
        # Upload data
        json_file = Path(__file__).parent / 'converted.json'
        results = await poster.upload_from_json(json_file)
        
        print("\n✅ Upload completed successfully!")
        print(f"📊 Results: {results}")
        
    except Exception as e:
        print(f"❌ Upload failed: {e}")

if __name__ == '__main__':
    asyncio.run(upload_sample())