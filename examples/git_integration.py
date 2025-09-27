#!/usr/bin/env python3
"""
Git integration example for the Bugfix Database.

This example shows how to:
1. Parse git commits to extract bug fixes
2. Automatically add bug fixes from git history
3. Generate bugfix IDs from git metadata
"""

import os
import sys
from datetime import datetime
from pathlib import Path
import re

# Add src to Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from bugfix_database import BugFix, BugfixDatabase


def parse_commit_message(message: str) -> dict:
    """Parse a git commit message to extract bug fix information.
    
    Args:
        message: Git commit message
        
    Returns:
        Dictionary with parsed information
    """
    # Common patterns for bug fix commits
    bug_patterns = [
        r'fix(?:es)?\s+(?:bug|issue|problem|error|crash|leak|race|deadlock)',
        r'resolv(?:e|es)?\s+(?:bug|issue|problem|error|crash|leak|race|deadlock)',
        r'patch(?:es)?\s+(?:bug|issue|problem|error|crash|leak|race|deadlock)',
        r'correct(?:s)?\s+(?:bug|issue|problem|error|crash|leak|race|deadlock)',
        r'repair(?:s)?\s+(?:bug|issue|problem|error|crash|leak|race|deadlock)',
    ]
    
    # Check if commit message indicates a bug fix
    is_bugfix = any(re.search(pattern, message.lower()) for pattern in bug_patterns)
    
    if not is_bugfix:
        return {"is_bugfix": False}
    
    # Extract issue number if present
    issue_match = re.search(r'(?:fix|resolve|patch|correct|repair)\s*#?(\d+)', message.lower())
    issue_number = issue_match.group(1) if issue_match else None
    
    # Extract file information from message if present
    file_match = re.search(r'in\s+([^\s,]+)', message.lower())
    file_path = file_match.group(1) if file_match else None
    
    return {
        "is_bugfix": True,
        "description": message.strip(),
        "related_issue": f"ISSUE-{issue_number}" if issue_number else None,
        "file_hint": file_path
    }


def create_bugfix_from_git(commit_hash: str, author: str, message: str, 
                          file_changes: list, db: BugfixDatabase) -> list:
    """Create BugFix objects from git commit information.
    
    Args:
        commit_hash: Git commit hash
        author: Commit author
        message: Commit message
        file_changes: List of file paths that changed
        db: Database client for generating IDs
        
    Returns:
        List of BugFix objects
    """
    # Parse commit message
    parsed = parse_commit_message(message)
    
    if not parsed["is_bugfix"]:
        return []
    
    bugfixes = []
    
    # Create a bugfix for each changed file
    for file_path in file_changes:
        # Generate unique ID
        fix_id = db.generate_bugfix_id(commit_hash, file_path)
        
        bugfix = BugFix(
            id=fix_id,
            file=file_path,
            description=parsed["description"],
            commit_hash=commit_hash,
            author=author,
            created_at=datetime.now(),
            resolved=True,
            related_issue=parsed.get("related_issue")
        )
        
        bugfixes.append(bugfix)
    
    return bugfixes


def example_git_parsing():
    """Example of parsing git commits for bug fixes."""
    print("=== Git Commit Parsing Example ===")
    
    # Sample commit messages
    sample_commits = [
        {
            "hash": "abc123",
            "author": "dev@example.com",
            "message": "Fix null pointer exception in user authentication",
            "files": ["src/auth.py", "src/user.py"]
        },
        {
            "hash": "def456",
            "author": "security@example.com", 
            "message": "Resolve memory leak in data processing #123",
            "files": ["src/processor.py"]
        },
        {
            "hash": "ghi789",
            "author": "dev@example.com",
            "message": "Add new feature for user dashboard",
            "files": ["src/dashboard.py", "src/components.py"]
        },
        {
            "hash": "jkl012",
            "author": "qa@example.com",
            "message": "Patch race condition in concurrent operations",
            "files": ["src/concurrent.py"]
        }
    ]
    
    try:
        # Initialize database client
        db = BugfixDatabase()
        
        all_bugfixes = []
        
        for commit in sample_commits:
            print(f"\nProcessing commit {commit['hash']}:")
            print(f"  Message: {commit['message']}")
            
            # Parse commit
            bugfixes = create_bugfix_from_git(
                commit["hash"],
                commit["author"], 
                commit["message"],
                commit["files"],
                db
            )
            
            if bugfixes:
                print(f"  ✅ Found {len(bugfixes)} bug fix(es):")
                for fix in bugfixes:
                    print(f"    - {fix.file}: {fix.description}")
                    if fix.related_issue:
                        print(f"      Issue: {fix.related_issue}")
                all_bugfixes.extend(bugfixes)
            else:
                print("  ⚪ No bug fixes detected")
        
        # Add all bugfixes to database
        if all_bugfixes:
            print(f"\nAdding {len(all_bugfixes)} bug fixes to database...")
            results = db.add_bugfixes(all_bugfixes)
            
            successful = len([r for r in results if r["success"]])
            print(f"Successfully added {successful}/{len(all_bugfixes)} bug fixes")
        
    except Exception as e:
        print(f"Error in git parsing example: {e}")


def example_git_log_parsing():
    """Example of parsing actual git log output."""
    print("\n=== Git Log Parsing Example ===")
    
    # Sample git log output format
    sample_git_log = """
commit abc123def456
Author: developer@example.com <developer@example.com>
Date:   Mon Jan 1 12:00:00 2024 +0000

    Fix authentication bypass vulnerability
    
    Fixed a critical security issue where users could bypass
    authentication by manipulating session tokens.

commit def456ghi789  
Author: security@example.com <security@example.com>
Date:   Mon Jan 1 11:30:00 2024 +0000

    Resolve memory leak in data processing #456
    
    Fixed memory leak that occurred during large dataset processing.
    Added proper cleanup and resource management.

commit ghi789jkl012
Author: developer@example.com <developer@example.com>  
Date:   Mon Jan 1 11:00:00 2024 +0000

    Add user preferences feature
    
    Implemented new user preferences system with customizable
    dashboard and notification settings.
"""
    
    try:
        # Parse git log (simplified version)
        commits = []
        current_commit = {}
        
        for line in sample_git_log.strip().split('\n'):
            if line.startswith('commit '):
                if current_commit:
                    commits.append(current_commit)
                current_commit = {
                    'hash': line.split()[1],
                    'message': '',
                    'author': '',
                    'files': []  # Would need actual git log with --name-only
                }
            elif line.startswith('Author: '):
                current_commit['author'] = line.replace('Author: ', '').split('<')[0].strip()
            elif line.strip() and not line.startswith('Date:'):
                if not current_commit['message']:
                    current_commit['message'] = line.strip()
        
        if current_commit:
            commits.append(current_commit)
        
        # Process commits
        db = BugfixDatabase()
        all_bugfixes = []
        
        for commit in commits:
            print(f"\nProcessing commit {commit['hash'][:8]}...")
            print(f"  Message: {commit['message']}")
            
            # Parse commit message
            parsed = parse_commit_message(commit['message'])
            
            if parsed['is_bugfix']:
                # For demo, assume files were affected
                demo_files = ["src/main.py", "src/auth.py"]
                
                bugfixes = create_bugfix_from_git(
                    commit['hash'],
                    commit['author'],
                    commit['message'], 
                    demo_files,
                    db
                )
                
                if bugfixes:
                    print(f"  ✅ Detected {len(bugfixes)} bug fix(es)")
                    all_bugfixes.extend(bugfixes)
                else:
                    print("  ⚪ No bug fixes detected")
            else:
                print("  ⚪ Not a bug fix commit")
        
        print(f"\nTotal bug fixes found: {len(all_bugfixes)}")
        
    except Exception as e:
        print(f"Error in git log parsing example: {e}")


def main():
    """Main example function."""
    print("🐛 Bugfix Database - Git Integration Example")
    print("=" * 50)
    
    # Check if environment is configured
    required_vars = ["SUPABASE_URL", "SUPABASE_KEY", "OPENAI_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        print("Please set these in your .env file or environment")
        return
    
    try:
        example_git_parsing()
        example_git_log_parsing()
        
        print("\n✅ Git integration example completed!")
        
    except Exception as e:
        print(f"\n❌ Example failed: {e}")


if __name__ == "__main__":
    main()
