"""
Database client for bugfix storage and retrieval.

This module provides the main interface for interacting with the bugfix database,
including ingestion and semantic search capabilities.
"""

import os
from typing import List, Optional, Dict, Any
from datetime import datetime
from supabase import create_client, Client

from .models import BugFix, QueryRequest, QueryResponse
from .embedding_service import EmbeddingService
from .storage_client import StorageClient


class BugfixDatabase:
    """Main database client for bugfix operations."""
    
    def __init__(self, supabase_url: str = None, supabase_key: str = None, openai_api_key: str = None):
        """Initialize the database client.
        
        Args:
            supabase_url: Supabase project URL
            supabase_key: Supabase service role key
            openai_api_key: OpenAI API key for embeddings
        """
        self.supabase_url = supabase_url or os.getenv("SUPABASE_URL")
        self.supabase_key = supabase_key or os.getenv("SUPABASE_KEY")
        openai_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Supabase URL and key are required")
        
        if not openai_key:
            raise ValueError("OpenAI API key is required")
        
        # Initialize the three core components
        self.client: Client = create_client(self.supabase_url, self.supabase_key)  # Relational DB
        self.embedding_service = EmbeddingService(openai_key)  # Vector DB (pgvector)
        self.storage_client = StorageClient(self.supabase_url, self.supabase_key)  # Blob Storage
    
    def add_bugfix(self, bugfix: BugFix) -> Dict[str, Any]:
        """Add a single bugfix to the database.
        
        Args:
            bugfix: BugFix object to store
            
        Returns:
            Result of the database insertion
        """
        try:
            # Generate embedding from description
            embedding = self.embedding_service.embed(bugfix.description)
            
            # Prepare data for database
            data = {
                "id": bugfix.id,
                "file": bugfix.file,
                "line_start": bugfix.line_start,
                "line_end": bugfix.line_end,
                "description": bugfix.description,
                "commit_hash": bugfix.commit_hash,
                "author": bugfix.author,
                "created_at": bugfix.created_at.isoformat(),
                "resolved": bugfix.resolved,
                "related_issue": bugfix.related_issue,
                # Supabase Storage references
                "patch_blob_url": bugfix.patch_blob_url,
                "log_blob_url": bugfix.log_blob_url,
                "artifact_blob_url": bugfix.artifact_blob_url,
                "embedding": embedding
            }
            
            # Insert into database
            result = self.client.table("bugfixes").insert(data).execute()
            return {"success": True, "data": result.data[0] if result.data else None}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def add_bugfixes(self, bugfixes: List[BugFix]) -> List[Dict[str, Any]]:
        """Add multiple bugfixes to the database.
        
        Args:
            bugfixes: List of BugFix objects to store
            
        Returns:
            List of results for each bugfix
        """
        results = []
        for bugfix in bugfixes:
            result = self.add_bugfix(bugfix)
            results.append(result)
        return results
    
    def search_bugfixes(self, request: QueryRequest) -> QueryResponse:
        """Search for bugfixes using semantic similarity.
        
        Args:
            request: QueryRequest with search parameters
            
        Returns:
            QueryResponse with matching bugfixes
        """
        try:
            # Generate embedding for the query
            query_embedding = self.embedding_service.embed(request.query)
            
            # Convert embedding to string format for PostgreSQL
            embedding_str = str(query_embedding)
            
            # Call the database function
            result = self.client.rpc(
                "match_bugfixes",
                {
                    "query_embedding": embedding_str,
                    "match_threshold": 0.75,
                    "match_count": request.limit,
                    "filter_file": request.file
                }
            ).execute()
            
            # Convert results to BugFix objects
            bugfixes = []
            for item in result.data or []:
                try:
                    # Handle datetime conversion
                    created_at = item.get('created_at')
                    if isinstance(created_at, str):
                        created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    elif not isinstance(created_at, datetime):
                        created_at = datetime.now()
                    
                    bugfix = BugFix(
                        id=item['id'],
                        file=item['file'],
                        line_start=item.get('line_start'),
                        line_end=item.get('line_end'),
                        description=item['description'],
                        commit_hash=item['commit_hash'],
                        author=item['author'],
                        created_at=created_at,
                        resolved=item.get('resolved', True),
                        related_issue=item.get('related_issue'),
                        # Supabase Storage references
                        patch_blob_url=item.get('patch_blob_url'),
                        log_blob_url=item.get('log_blob_url'),
                        artifact_blob_url=item.get('artifact_blob_url')
                    )
                    bugfixes.append(bugfix)
                    
                except Exception as e:
                    print(f"Error converting result to BugFix: {e}")
                    continue
            
            return QueryResponse(
                query=request.query,
                results=bugfixes,
                retrieved_at=datetime.utcnow()
            )
            
        except Exception as e:
            # Return empty response on error
            return QueryResponse(
                query=request.query,
                results=[],
                retrieved_at=datetime.utcnow()
            )
    
    def get_bugfix_by_id(self, bugfix_id: str) -> Optional[BugFix]:
        """Get a specific bugfix by ID.
        
        Args:
            bugfix_id: Unique ID of the bugfix
            
        Returns:
            BugFix object or None if not found
        """
        try:
            result = self.client.table("bugfixes").select("*").eq("id", bugfix_id).execute()
            
            if not result.data:
                return None
            
            item = result.data[0]
            
            # Handle datetime conversion
            created_at = item.get('created_at')
            if isinstance(created_at, str):
                created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            elif not isinstance(created_at, datetime):
                created_at = datetime.now()
            
            return BugFix(
                id=item['id'],
                file=item['file'],
                line_start=item.get('line_start'),
                line_end=item.get('line_end'),
                description=item['description'],
                commit_hash=item['commit_hash'],
                author=item['author'],
                created_at=created_at,
                resolved=item.get('resolved', True),
                related_issue=item.get('related_issue'),
                external_ref=item.get('external_ref')
            )
            
        except Exception as e:
            print(f"Error retrieving bugfix {bugfix_id}: {e}")
            return None
    
    def get_bugfixes_by_file(self, file_path: str, limit: int = 10) -> List[BugFix]:
        """Get all bugfixes for a specific file.
        
        Args:
            file_path: Path to the file
            limit: Maximum number of results
            
        Returns:
            List of BugFix objects
        """
        try:
            result = self.client.table("bugfixes").select("*").eq("file", file_path).limit(limit).execute()
            
            bugfixes = []
            for item in result.data or []:
                try:
                    # Handle datetime conversion
                    created_at = item.get('created_at')
                    if isinstance(created_at, str):
                        created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    elif not isinstance(created_at, datetime):
                        created_at = datetime.now()
                    
                    bugfix = BugFix(
                        id=item['id'],
                        file=item['file'],
                        line_start=item.get('line_start'),
                        line_end=item.get('line_end'),
                        description=item['description'],
                        commit_hash=item['commit_hash'],
                        author=item['author'],
                        created_at=created_at,
                        resolved=item.get('resolved', True),
                        related_issue=item.get('related_issue'),
                        # Supabase Storage references
                        patch_blob_url=item.get('patch_blob_url'),
                        log_blob_url=item.get('log_blob_url'),
                        artifact_blob_url=item.get('artifact_blob_url')
                    )
                    bugfixes.append(bugfix)
                    
                except Exception as e:
                    print(f"Error converting result to BugFix: {e}")
                    continue
            
            return bugfixes
            
        except Exception as e:
            print(f"Error retrieving bugfixes for file {file_path}: {e}")
            return []
    
    def get_bugfixes_by_commit(self, commit_hash: str) -> List[BugFix]:
        """Get all bugfixes from a specific commit.
        
        Args:
            commit_hash: Git commit hash
            
        Returns:
            List of BugFix objects
        """
        try:
            result = self.client.table("bugfixes").select("*").eq("commit_hash", commit_hash).execute()
            
            bugfixes = []
            for item in result.data or []:
                try:
                    # Handle datetime conversion
                    created_at = item.get('created_at')
                    if isinstance(created_at, str):
                        created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    elif not isinstance(created_at, datetime):
                        created_at = datetime.now()
                    
                    bugfix = BugFix(
                        id=item['id'],
                        file=item['file'],
                        line_start=item.get('line_start'),
                        line_end=item.get('line_end'),
                        description=item['description'],
                        commit_hash=item['commit_hash'],
                        author=item['author'],
                        created_at=created_at,
                        resolved=item.get('resolved', True),
                        related_issue=item.get('related_issue'),
                        # Supabase Storage references
                        patch_blob_url=item.get('patch_blob_url'),
                        log_blob_url=item.get('log_blob_url'),
                        artifact_blob_url=item.get('artifact_blob_url')
                    )
                    bugfixes.append(bugfix)
                    
                except Exception as e:
                    print(f"Error converting result to BugFix: {e}")
                    continue
            
            return bugfixes
            
        except Exception as e:
            print(f"Error retrieving bugfixes for commit {commit_hash}: {e}")
            return []
    
    def generate_bugfix_id(self, commit_hash: str, file: str, line_start: int = None) -> str:
        """Generate a unique ID for a bugfix.
        
        Args:
            commit_hash: Git commit hash
            file: File path
            line_start: Starting line number (optional)
            
        Returns:
            Unique ID string
        """
        if line_start:
            return f"{commit_hash}_{file}_{line_start}"
        else:
            return f"{commit_hash}_{file}"
