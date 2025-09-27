# 🐛 Bugfix Database

A simple database system with three core components for storing and querying bug fixes:

## 📚 Overview

This system provides three essential components for bugfix knowledge management:

- **Relational DB (Supabase Postgres)** → canonical bugfix metadata
- **Vector DB (pgvector)** → semantic similarity search  
- **Blob Storage (Supabase Storage)** → patches, logs, large artifacts

## 🏗 Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Your App      │    │   Bugfix DB      │    │   Supabase      │
│                 │    │                  │    │                 │
│ • Git Hooks     │◄──►│ • Relational DB  │◄──►│ • Postgres DB   │
│ • CI/CD         │    │ • Vector DB      │    │ • pgvector      │
│ • Dev Tools     │    │ • Blob Storage   │    │ • Storage       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 🗂 Data Models

### BugFix
```python
class BugFix(BaseModel):
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
    patch_blob_url: Optional[str] = None    # URL to patch file
    log_blob_url: Optional[str] = None      # URL to log file
    artifact_blob_url: Optional[str] = None # URL to artifacts
```

### QueryRequest
```python
class QueryRequest(BaseModel):
    query: str
    file: Optional[str] = None
    limit: int = 5
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Supabase account
- OpenAI API key

### Installation

1. **Clone and install dependencies:**
```bash
git clone <repository-url>
cd HackGT25
pip install -r requirements.txt
```

2. **Set up environment variables:**
```bash
cp config.env.example .env
# Edit .env with your credentials
```

3. **Set up Supabase database:**
```sql
-- Run the schema from config/supabase_schema.sql
```

4. **Run the core components example:**
```bash
python examples/core_components.py
```

## 🔧 Configuration

### Environment Variables

```bash
# Required
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_service_role_key
OPENAI_API_KEY=your_openai_api_key

# Optional
GIT_REPO_PATH=/path/to/repository
LOG_LEVEL=INFO
SIMILARITY_THRESHOLD=0.75
```

### Supabase Setup

1. Create a new Supabase project
2. Enable the pgvector extension
3. Run the SQL schema from `config/supabase_schema.sql`
4. Get your project URL and service role key

## 📖 Usage

### Basic Usage

#### Adding Bug Fixes
```python
from bugfix_database import BugFix, BugfixDatabase
from datetime import datetime

# Initialize database client
db = BugfixDatabase()

# Create a bug fix
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

# Add to database
result = db.add_bugfix(bugfix)
if result["success"]:
    print("Bug fix added successfully!")
```

#### Searching Bug Fixes
```python
from bugfix_database import QueryRequest

# Search for similar bug fixes
query = QueryRequest(
    query="null pointer exception in authentication",
    file="src/auth.py",  # Optional file filter
    limit=5
)

response = db.search_bugfixes(query)
for fix in response.results:
    print(f"- {fix.description}")
    print(f"  File: {fix.file}:{fix.line_start}-{fix.line_end}")
    print(f"  Commit: {fix.commit_hash}")
```

#### Getting Bug Fixes by File or Commit
```python
# Get all bug fixes for a specific file
fixes = db.get_bugfixes_by_file("src/main.py")
for fix in fixes:
    print(f"- {fix.description}")

# Get all bug fixes from a specific commit
fixes = db.get_bugfixes_by_commit("commit123")
for fix in fixes:
    print(f"- {fix.description}")

# Get a specific bug fix by ID
fix = db.get_bugfix_by_id("commit123_src/main.py_42")
if fix:
    print(f"Found: {fix.description}")
```

## 🧪 Testing

Run the test suite:

```bash
pytest tests/
```

Run the core components example:

```bash
python examples/core_components.py
```

## 🏗 Development

### Project Structure

```
src/bugfix_database/
├── models.py              # Pydantic data models
├── database_client.py     # Main client (all 3 components)
├── embedding_service.py   # Vector DB (pgvector) component
├── storage_client.py      # Blob Storage component
└── __init__.py           # Package exports

config/                   # Database schemas and config
examples/                 # Core components example
tests/                    # Test suite
scripts/                  # Helper scripts
```

### Adding New Features

1. **New Data Models**: Add to `models.py`
2. **New Database Operations**: Add methods to `BugfixDatabase` class
3. **New Services**: Create new modules in the `src/bugfix_database/` directory

## 🔍 Key Features

- **Relational DB**: Supabase Postgres for canonical bugfix metadata
- **Vector DB**: pgvector for semantic similarity search using OpenAI embeddings
- **Blob Storage**: Supabase Storage for patches, logs, and large artifacts
- **Simple API**: Clean Python interface for all three components
- **Rich Metadata**: Store file locations, commit info, and related issues
- **Scalable Architecture**: Built on Supabase for enterprise scale

## 🤝 Contributing

This project was created for HackGT 2025. Contributions are welcome!

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is open source and available under the MIT License.

## 🏆 HackGT 2025

Built with ❤️ at Georgia Tech's HackGT 2025 hackathon.
