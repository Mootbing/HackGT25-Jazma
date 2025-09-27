#!/usr/bin/env python3
"""
Core Components Example - Demonstrates the three essential parts:

1. Relational DB (Supabase Postgres) → canonical bugfix metadata
2. Vector DB (pgvector) → semantic similarity search  
3. Blob Storage (Supabase Storage) → patches, logs, large artifacts
"""

import os
import sys
from datetime import datetime
from pathlib import Path

# Add src to Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from bugfix_database import BugFix, BugfixDatabase, StorageClient


def example_relational_db():
    """Demonstrate Relational DB (Supabase Postgres) for canonical bugfix metadata."""
    print("=== 1. Relational DB (Supabase Postgres) ===")
    print("Purpose: Store canonical bugfix metadata")
    
    try:
        db = BugfixDatabase()
        
        # Create a bug fix with metadata
        bugfix = BugFix(
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
        )
        
        # Store in relational database
        result = db.add_bugfix(bugfix)
        
        if result["success"]:
            print("✅ Bugfix metadata stored in relational DB")
            print(f"   ID: {bugfix.id}")
            print(f"   File: {bugfix.file}")
            print(f"   Description: {bugfix.description}")
            print(f"   Commit: {bugfix.commit_hash}")
            print(f"   Author: {bugfix.author}")
        else:
            print(f"❌ Failed to store metadata: {result['error']}")
        
        return bugfix
        
    except Exception as e:
        print(f"❌ Relational DB error: {e}")
        return None


def example_vector_db(bugfix):
    """Demonstrate Vector DB (pgvector) for semantic similarity search."""
    print("\n=== 2. Vector DB (pgvector) ===")
    print("Purpose: Semantic similarity search")
    
    try:
        db = BugfixDatabase()
        
        # Search for similar bug fixes using natural language
        search_queries = [
            "null pointer exception",
            "authentication bug",
            "user login error",
            "memory leak"
        ]
        
        for query in search_queries:
            print(f"\n🔍 Searching for: '{query}'")
            
            # This uses pgvector for semantic similarity
            response = db.search_bugfixes({
                "query": query,
                "limit": 3
            })
            
            print(f"   Found {len(response.results)} similar bug fixes:")
            for i, fix in enumerate(response.results, 1):
                print(f"     {i}. {fix.description}")
                print(f"        File: {fix.file}:{fix.line_start}-{fix.line_end}")
        
        print("\n✅ Semantic search using pgvector embeddings")
        
    except Exception as e:
        print(f"❌ Vector DB error: {e}")


def example_blob_storage():
    """Demonstrate Blob Storage (Supabase Storage) for patches, logs, artifacts."""
    print("\n=== 3. Blob Storage (Supabase Storage) ===")
    print("Purpose: Store patches, logs, large artifacts")
    
    try:
        storage = StorageClient()
        
        # Example patch content
        patch_content = """
--- a/src/main.py
+++ b/src/main.py
@@ -40,7 +40,7 @@ def authenticate_user(user_id):
-    if user is None:
+    if user is None or user.id is None:
         raise AuthenticationError("Invalid user")
     return user
"""
        
        # Example log content
        log_content = """
[2024-01-01 12:00:00] ERROR: NullPointerException in user authentication
[2024-01-01 12:00:01] STACK_TRACE: 
  at authenticate_user (main.py:42)
  at login_handler (auth.py:15)
[2024-01-01 12:00:02] FIX: Added null check for user.id
"""
        
        # Example artifact (binary data)
        artifact_content = b"Binary artifact data: crash dump, memory snapshot, etc."
        
        # Upload to Supabase Storage
        patch_url = storage.upload_patch(patch_content, "commit123_src/main.py_42")
        log_url = storage.upload_log(log_content, "commit123_src/main.py_42")
        artifact_url = storage.upload_artifact(artifact_content, "commit123_src/main.py_42", "bin")
        
        print("✅ Files uploaded to Supabase Storage:")
        if patch_url:
            print(f"   📄 Patch: {patch_url}")
        if log_url:
            print(f"   📋 Log: {log_url}")
        if artifact_url:
            print(f"   📦 Artifact: {artifact_url}")
        
        return {
            "patch_url": patch_url,
            "log_url": log_url,
            "artifact_url": artifact_url
        }
        
    except Exception as e:
        print(f"❌ Blob Storage error: {e}")
        return None


def example_integrated_workflow():
    """Demonstrate all three components working together."""
    print("\n=== 4. Integrated Workflow ===")
    print("All three components working together")
    
    try:
        db = BugfixDatabase()
        storage = StorageClient()
        
        # 1. Create bug fix with storage references
        bugfix = BugFix(
            id="commit456_src/auth.py_89",
            file="src/auth.py",
            line_start=89,
            line_end=91,
            description="Fixed authentication bypass vulnerability",
            commit_hash="commit456",
            author="security@example.com",
            created_at=datetime.now(),
            resolved=True,
            related_issue="SEC-001",
            # Storage URLs (would be populated from actual uploads)
            patch_blob_url="https://storage.example.com/patches/commit456_src/auth.py_89.patch",
            log_blob_url="https://storage.example.com/logs/commit456_src/auth.py_89.log",
            artifact_url="https://storage.example.com/artifacts/commit456_src/auth.py_89.bin"
        )
        
        # 2. Store in relational DB with metadata
        result = db.add_bugfix(bugfix)
        
        if result["success"]:
            print("✅ Bugfix stored with all components:")
            print(f"   📊 Metadata in Relational DB")
            print(f"   🔍 Embedding in Vector DB (pgvector)")
            print(f"   📄 Patch: {bugfix.patch_blob_url}")
            print(f"   📋 Log: {bugfix.log_blob_url}")
            print(f"   📦 Artifact: {bugfix.artifact_blob_url}")
        
        # 3. Demonstrate semantic search
        print("\n🔍 Searching for 'security vulnerability'...")
        response = db.search_bugfixes({
            "query": "security vulnerability",
            "limit": 2
        })
        
        for fix in response.results:
            print(f"   Found: {fix.description}")
            print(f"   Storage: {fix.patch_blob_url}")
        
        print("\n✅ All three components working together!")
        
    except Exception as e:
        print(f"❌ Integrated workflow error: {e}")


def main():
    """Main example function."""
    print("🐛 Bugfix Database - Core Components Example")
    print("=" * 60)
    
    # Check if environment is configured
    required_vars = ["SUPABASE_URL", "SUPABASE_KEY", "OPENAI_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        print("Please set these in your .env file or environment")
        return
    
    try:
        # Demonstrate each component
        bugfix = example_relational_db()
        example_vector_db(bugfix)
        storage_urls = example_blob_storage()
        example_integrated_workflow()
        
        print("\n🎉 Core components example completed!")
        print("\nSummary:")
        print("1. ✅ Relational DB (Supabase Postgres) - canonical metadata")
        print("2. ✅ Vector DB (pgvector) - semantic similarity search")
        print("3. ✅ Blob Storage (Supabase Storage) - patches, logs, artifacts")
        
    except Exception as e:
        print(f"\n❌ Example failed: {e}")


if __name__ == "__main__":
    main()
