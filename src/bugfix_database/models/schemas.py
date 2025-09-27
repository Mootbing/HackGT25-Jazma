from typing import Optional
from pydantic import BaseModel
from datetime import datetime


class BugFix(BaseModel):
    """Represents a bug fix with metadata and storage references."""
    id: str                       # unique ID (commit+file+line)
    file: str                     # file path
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    description: str              # human-readable summary
    commit_hash: str
    author: str
    created_at: datetime
    resolved: bool = True
    related_issue: Optional[str] = None
    # Supabase Storage references
    patch_blob_url: Optional[str] = None    # URL to patch file in Supabase Storage
    log_blob_url: Optional[str] = None      # URL to log file in Supabase Storage
    artifact_blob_url: Optional[str] = None # URL to other artifacts in Supabase Storage


class QueryRequest(BaseModel):
    """Request for querying bug fixes."""
    query: str
    file: Optional[str] = None
    limit: int = 5


class QueryResponse(BaseModel):
    """Response containing query results."""
    query: str
    results: list[BugFix]
    retrieved_at: datetime
