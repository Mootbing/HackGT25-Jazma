#!/usr/bin/env python3
"""
Basic usage example for the Bugfix Database.

This example shows how to:
1. Add bug fixes to the database
2. Search for bug fixes using semantic search
3. Retrieve bug fixes by file or commit
"""

import os
import sys
from datetime import datetime
from pathlib import Path

# Add src to Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from bugfix_database import BugFix, QueryRequest, BugfixDatabase


def create_sample_bugfixes():
    """Create some sample bug fixes for testing."""
    fixes = [
        BugFix(
            id="commit123_src/main.py_42",
            file="src/main.py",
            line_start=42,
            line_end=44,
            description="Fixed null pointer exception in user authentication",
            commit_hash="commit123",
            author="developer@example.com",
            created_at=datetime.now(),
            resolved=True,
            related_issue="ISSUE-123"
        ),
        BugFix(
            id="commit124_src/utils.py_15",
            file="src/utils.py",
            line_start=15,
            line_end=17,
            description="Resolved memory leak in data processing function",
            commit_hash="commit124",
            author="developer@example.com",
            created_at=datetime.now(),
            resolved=True,
            related_issue="ISSUE-124"
        ),
        BugFix(
            id="commit125_src/auth.py_89",
            file="src/auth.py",
            line_start=89,
            line_end=91,
            description="Fixed authentication bypass vulnerability",
            commit_hash="commit125",
            author="security@example.com",
            created_at=datetime.now(),
            resolved=True,
            related_issue="SEC-001"
        ),
        BugFix(
            id="commit126_src/main.py_156",
            file="src/main.py",
            line_start=156,
            line_end=158,
            description="Fixed race condition in concurrent user sessions",
            commit_hash="commit126",
            author="developer@example.com",
            created_at=datetime.now(),
            resolved=True,
            related_issue="ISSUE-125"
        )
    ]
    return fixes


def example_add_bugfixes():
    """Example of adding bug fixes to the database."""
    print("=== Adding Bug Fixes ===")
    
    try:
        # Initialize database client
        db = BugfixDatabase()
        
        # Create sample bug fixes
        fixes = create_sample_bugfixes()
        
        # Add bug fixes to database
        results = db.add_bugfixes(fixes)
        
        print(f"Attempted to add {len(fixes)} bug fixes:")
        for i, result in enumerate(results):
            if result["success"]:
                print(f"  ✅ Fix {i+1}: {fixes[i].description}")
            else:
                print(f"  ❌ Fix {i+1}: {result['error']}")
        
        return len([r for r in results if r["success"]])
        
    except Exception as e:
        print(f"Error adding bug fixes: {e}")
        return 0


def example_search_bugfixes():
    """Example of searching for bug fixes."""
    print("\n=== Searching Bug Fixes ===")
    
    try:
        # Initialize database client
        db = BugfixDatabase()
        
        # Example searches
        search_queries = [
            QueryRequest(query="null pointer exception", limit=3),
            QueryRequest(query="memory leak", file="src/utils.py", limit=2),
            QueryRequest(query="authentication security", limit=5),
            QueryRequest(query="race condition", limit=3)
        ]
        
        for i, query in enumerate(search_queries, 1):
            print(f"\nSearch {i}: '{query.query}'")
            if query.file:
                print(f"  File filter: {query.file}")
            
            response = db.search_bugfixes(query)
            
            print(f"  Found {len(response.results)} results:")
            for j, fix in enumerate(response.results):
                print(f"    {j+1}. {fix.description}")
                print(f"       File: {fix.file}:{fix.line_start}-{fix.line_end}")
                print(f"       Commit: {fix.commit_hash}")
                print(f"       Author: {fix.author}")
                if fix.related_issue:
                    print(f"       Issue: {fix.related_issue}")
                print()
        
    except Exception as e:
        print(f"Error searching bug fixes: {e}")


def example_get_by_file():
    """Example of getting bug fixes by file."""
    print("\n=== Getting Bug Fixes by File ===")
    
    try:
        # Initialize database client
        db = BugfixDatabase()
        
        # Get bug fixes for specific files
        files = ["src/main.py", "src/utils.py", "src/auth.py"]
        
        for file_path in files:
            print(f"\nBug fixes in {file_path}:")
            fixes = db.get_bugfixes_by_file(file_path)
            
            if fixes:
                for i, fix in enumerate(fixes, 1):
                    print(f"  {i}. {fix.description}")
                    print(f"     Lines: {fix.line_start}-{fix.line_end}")
                    print(f"     Commit: {fix.commit_hash}")
            else:
                print("  No bug fixes found")
        
    except Exception as e:
        print(f"Error getting bug fixes by file: {e}")


def example_get_by_commit():
    """Example of getting bug fixes by commit."""
    print("\n=== Getting Bug Fixes by Commit ===")
    
    try:
        # Initialize database client
        db = BugfixDatabase()
        
        # Get bug fixes for specific commits
        commits = ["commit123", "commit125"]
        
        for commit_hash in commits:
            print(f"\nBug fixes in commit {commit_hash}:")
            fixes = db.get_bugfixes_by_commit(commit_hash)
            
            if fixes:
                for i, fix in enumerate(fixes, 1):
                    print(f"  {i}. {fix.description}")
                    print(f"     File: {fix.file}:{fix.line_start}-{fix.line_end}")
                    print(f"     Author: {fix.author}")
            else:
                print("  No bug fixes found")
        
    except Exception as e:
        print(f"Error getting bug fixes by commit: {e}")


def main():
    """Main example function."""
    print("🐛 Bugfix Database - Basic Usage Example")
    print("=" * 50)
    
    # Check if environment is configured
    required_vars = ["SUPABASE_URL", "SUPABASE_KEY", "OPENAI_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        print("Please set these in your .env file or environment")
        print("\nExample .env file:")
        print("SUPABASE_URL=your_supabase_project_url")
        print("SUPABASE_KEY=your_supabase_service_role_key")
        print("OPENAI_API_KEY=your_openai_api_key")
        return
    
    try:
        # Run examples
        added_count = example_add_bugfixes()
        
        if added_count > 0:
            example_search_bugfixes()
            example_get_by_file()
            example_get_by_commit()
        else:
            print("\n⚠️  No bug fixes were added, skipping other examples")
        
        print("\n✅ Example completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Example failed: {e}")
        print("\nMake sure you have:")
        print("1. Set up your .env file with proper credentials")
        print("2. Created the Supabase database schema")
        print("3. Installed all dependencies")


if __name__ == "__main__":
    main()
