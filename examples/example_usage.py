#!/usr/bin/env python3
"""
Example usage of the MCP Bugfix Context Server.

This script demonstrates how to use the server programmatically
without going through the MCP protocol.
"""

import asyncio
from datetime import datetime
from src.mcp_bugfix_server.models import BugFix, ContextUpdate, QueryRequest
from src.mcp_bugfix_server.ingestion import IngestionService
from src.mcp_bugfix_server.query import QueryService


async def example_ingestion():
    """Example of ingesting bug fixes."""
    print("=== Ingestion Example ===")
    
    # Create sample bug fixes
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
        )
    ]
    
    # Create context update
    context_update = ContextUpdate(
        commit="commit125",
        branch="main",
        fixes=fixes
    )
    
    # Initialize ingestion service
    ingestion_service = IngestionService()
    
    try:
        # Ingest the fixes
        results = ingestion_service.ingest_fixes(context_update.fixes)
        print(f"Successfully ingested {len(results)} bug fixes")
        
        for i, result in enumerate(results):
            if "error" in result:
                print(f"  Fix {i+1}: Error - {result['error']}")
            else:
                print(f"  Fix {i+1}: Success - {result.get('id', 'Unknown ID')}")
                
    except Exception as e:
        print(f"Error during ingestion: {e}")


async def example_query():
    """Example of querying bug fixes."""
    print("\n=== Query Example ===")
    
    # Initialize query service
    query_service = QueryService()
    
    # Example queries
    queries = [
        QueryRequest(query="null pointer exception", limit=3),
        QueryRequest(query="memory leak", file="src/utils.py", limit=2),
        QueryRequest(query="authentication bug", limit=5)
    ]
    
    for i, query in enumerate(queries):
        print(f"\nQuery {i+1}: {query.query}")
        if query.file:
            print(f"  File filter: {query.file}")
        
        try:
            response = query_service.query_fixes(query)
            print(f"  Found {len(response.results)} results:")
            
            for j, fix in enumerate(response.results):
                print(f"    {j+1}. {fix.description}")
                print(f"       File: {fix.file}:{fix.line_start}-{fix.line_end}")
                print(f"       Commit: {fix.commit_hash}")
                
        except Exception as e:
            print(f"  Error during query: {e}")


async def main():
    """Main example function."""
    print("MCP Bugfix Context Server - Example Usage")
    print("=" * 50)
    
    # Note: These examples require proper environment configuration
    # Make sure to set up your .env file with Supabase and OpenAI credentials
    
    try:
        await example_ingestion()
        await example_query()
    except Exception as e:
        print(f"Example failed: {e}")
        print("\nMake sure you have:")
        print("1. Set up your .env file with proper credentials")
        print("2. Created the Supabase database schema")
        print("3. Installed all dependencies")


if __name__ == "__main__":
    asyncio.run(main())
