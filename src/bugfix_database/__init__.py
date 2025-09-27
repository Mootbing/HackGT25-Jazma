"""
Bugfix Database - A simple database client for storing and querying bug fixes.

This module provides a clean interface for:
- Storing bug fixes with embeddings in Supabase + pgvector
- Querying bug fixes using semantic search
- Managing bugfix metadata and context
"""

from .models import BugFix, QueryRequest, QueryResponse
from .database_client import BugfixDatabase
from .embedding_service import EmbeddingService

__version__ = "1.0.0"
__author__ = "HackGT25 Team"

__all__ = [
    "BugFix",
    "QueryRequest", 
    "QueryResponse",
    "BugfixDatabase",
    "EmbeddingService"
]
