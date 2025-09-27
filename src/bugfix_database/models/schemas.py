from typing import List, Optional
from pydantic import BaseModel, HttpUrl
from datetime import datetime


class BugFix(BaseModel):
    """Represents a bug fix with metadata and location information."""
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
    external_ref: Optional[HttpUrl] = None  # link to artifact/blob


class ContextUpdate(BaseModel):
    """Batch update of bug fixes from a commit."""
    commit: str
    branch: str
    fixes: List[BugFix]


class QueryRequest(BaseModel):
    """Request for querying bug fixes."""
    query: str
    file: Optional[str] = None
    limit: int = 5


class QueryResponse(BaseModel):
    """Response containing query results."""
    query: str
    results: List[BugFix]
    retrieved_at: datetime
