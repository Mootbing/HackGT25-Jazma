"""
Tests for the Pydantic models.
"""

import pytest
from datetime import datetime
from src.mcp_bugfix_server.models import BugFix, ContextUpdate, QueryRequest, QueryResponse


def test_bugfix_model():
    """Test BugFix model creation and validation."""
    fix = BugFix(
        id="test_id",
        file="src/test.py",
        line_start=10,
        line_end=12,
        description="Test bug fix",
        commit_hash="abc123",
        author="test@example.com",
        created_at=datetime.now(),
        resolved=True,
        related_issue="ISSUE-1"
    )
    
    assert fix.id == "test_id"
    assert fix.file == "src/test.py"
    assert fix.line_start == 10
    assert fix.line_end == 12
    assert fix.description == "Test bug fix"
    assert fix.commit_hash == "abc123"
    assert fix.author == "test@example.com"
    assert fix.resolved is True
    assert fix.related_issue == "ISSUE-1"


def test_bugfix_model_optional_fields():
    """Test BugFix model with optional fields."""
    fix = BugFix(
        id="test_id_2",
        file="src/test2.py",
        description="Test bug fix without optional fields",
        commit_hash="def456",
        author="test2@example.com",
        created_at=datetime.now()
    )
    
    assert fix.line_start is None
    assert fix.line_end is None
    assert fix.resolved is True  # Default value
    assert fix.related_issue is None
    assert fix.external_ref is None


def test_context_update_model():
    """Test ContextUpdate model creation."""
    fixes = [
        BugFix(
            id="fix1",
            file="src/file1.py",
            description="First fix",
            commit_hash="commit1",
            author="author1",
            created_at=datetime.now()
        ),
        BugFix(
            id="fix2",
            file="src/file2.py",
            description="Second fix",
            commit_hash="commit2",
            author="author2",
            created_at=datetime.now()
        )
    ]
    
    context = ContextUpdate(
        commit="main_commit",
        branch="main",
        fixes=fixes
    )
    
    assert context.commit == "main_commit"
    assert context.branch == "main"
    assert len(context.fixes) == 2
    assert context.fixes[0].id == "fix1"
    assert context.fixes[1].id == "fix2"


def test_query_request_model():
    """Test QueryRequest model creation."""
    request = QueryRequest(
        query="test query",
        file="src/test.py",
        limit=10
    )
    
    assert request.query == "test query"
    assert request.file == "src/test.py"
    assert request.limit == 10


def test_query_request_defaults():
    """Test QueryRequest model with default values."""
    request = QueryRequest(query="simple query")
    
    assert request.query == "simple query"
    assert request.file is None
    assert request.limit == 5  # Default value


def test_query_response_model():
    """Test QueryResponse model creation."""
    fixes = [
        BugFix(
            id="response_fix1",
            file="src/response.py",
            description="Response fix",
            commit_hash="response_commit",
            author="response_author",
            created_at=datetime.now()
        )
    ]
    
    response = QueryResponse(
        query="response query",
        results=fixes,
        retrieved_at=datetime.now()
    )
    
    assert response.query == "response query"
    assert len(response.results) == 1
    assert response.results[0].id == "response_fix1"
    assert isinstance(response.retrieved_at, datetime)


def test_bugfix_model_validation():
    """Test BugFix model validation with invalid data."""
    with pytest.raises(ValueError):
        BugFix(
            # Missing required fields
            id="incomplete_fix"
        )


def test_query_request_validation():
    """Test QueryRequest model validation with invalid data."""
    with pytest.raises(ValueError):
        QueryRequest(
            # Missing required query field
            limit=5
        )
