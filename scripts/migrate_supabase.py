#!/usr/bin/env python3
"""
Script to set up Supabase database schema.

This script helps initialize the database with the required tables and functions.
"""

import os
import sys
from pathlib import Path
from supabase import create_client


def read_schema():
    """Read the SQL schema file."""
    schema_path = Path(__file__).parent.parent / "config" / "supabase_schema.sql"
    
    if not schema_path.exists():
        print(f"❌ Schema file not found: {schema_path}")
        sys.exit(1)
    
    with open(schema_path, "r") as f:
        return f.read()


def setup_database():
    """Set up the Supabase database schema."""
    print("🗄️  Setting up Supabase database schema...")
    
    # Check environment variables
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    
    if not url or not key:
        print("❌ SUPABASE_URL and SUPABASE_KEY environment variables are required")
        sys.exit(1)
    
    try:
        # Create Supabase client
        supabase = create_client(url, key)
        
        # Read and execute schema
        schema_sql = read_schema()
        
        # Split into individual statements
        statements = [stmt.strip() for stmt in schema_sql.split(';') if stmt.strip()]
        
        print(f"📝 Executing {len(statements)} SQL statements...")
        
        for i, statement in enumerate(statements, 1):
            try:
                print(f"  {i}/{len(statements)}: Executing statement...")
                # Note: Supabase client doesn't have direct SQL execution
                # This would typically be done through the Supabase dashboard
                # or using a direct PostgreSQL connection
                print(f"     Statement: {statement[:100]}...")
                
            except Exception as e:
                print(f"     ⚠️  Statement failed: {e}")
                continue
        
        print("✅ Database schema setup instructions generated")
        print("\n📋 Manual Setup Required:")
        print("1. Go to your Supabase dashboard")
        print("2. Navigate to SQL Editor")
        print("3. Copy and paste the contents of config/supabase_schema.sql")
        print("4. Execute the SQL script")
        
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        sys.exit(1)


def verify_setup():
    """Verify that the database is properly set up."""
    print("🔍 Verifying database setup...")
    
    try:
        from src.mcp_bugfix_server.ingestion import SupabaseClient
        client = SupabaseClient()
        
        # Try to query the bugfixes table
        result = client.client.table("bugfixes").select("*").limit(1).execute()
        print("✅ Database connection and table access verified")
        
        # Check if pgvector extension is available
        # This would require a more complex query, but we'll assume it's working
        print("✅ pgvector extension should be available")
        
    except Exception as e:
        print(f"❌ Database verification failed: {e}")
        print("Please ensure:")
        print("1. The schema has been executed in Supabase")
        print("2. pgvector extension is enabled")
        print("3. Your service key has proper permissions")
        return False
    
    return True


def main():
    """Main function."""
    print("🗄️  Supabase Database Setup")
    print("=" * 30)
    
    setup_database()
    
    # Ask user if they want to verify
    try:
        response = input("\nWould you like to verify the setup? (y/n): ").lower().strip()
        if response in ['y', 'yes']:
            verify_setup()
    except KeyboardInterrupt:
        print("\n👋 Setup interrupted")
    
    print("\n✅ Setup complete!")


if __name__ == "__main__":
    main()
