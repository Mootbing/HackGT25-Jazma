# Supabase Poster for Stack Overflow Data

This script uploads processed Stack Overflow data from `converted.json` to a Supabase database, following the schema and patterns from the provided TypeScript implementation.

## Features

- ✅ Uploads entries with deduplication using content hashing
- ✅ Redacts sensitive information (API keys, passwords, etc.)
- ✅ Links related entries 
- ✅ Chunks text and generates embeddings (mock implementation included)
- ✅ Handles errors gracefully with detailed logging
- ✅ Async processing for better performance
- ✅ Progress tracking and statistics

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy the example environment file:
```bash
cp .env.example .env
```

Edit `.env` and add your Supabase credentials:
```env
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_ANON_KEY=your-anon-key-here
```

### 3. Database Schema Requirements

Your Supabase database should have the following RPC functions:
- `rpc_insert_entry` - Inserts a new entry and returns the ID
- `rpc_insert_embeddings` - Inserts text chunks and embeddings

And these tables:
- `entries` - Main entries table
- `links` - Entry relationships 
- `embeddings` - Text chunks and embeddings (if using)

## Usage

### Basic Upload

```python
import asyncio
from supabase_poster import SupabasePoster, SupabaseConfig

async def main():
    config = SupabaseConfig.from_env()
    poster = SupabasePoster(config)
    
    results = await poster.upload_from_json('converted.json')
    print(f"Results: {results}")

asyncio.run(main())
```

### Using the Command Line

```bash
python supabase_poster.py
```

Or use the example script:
```bash
python upload_example.py
```

## Data Format

The script expects data in the format from `converted.json`:

```json
{
  "type": "solution|bug|doc",
  "title": "Entry title",
  "body": "Entry description",
  "code": "Code snippets",
  "stack_trace": "Error stack trace",
  "repro_steps": "Reproduction steps",
  "resolution": "Solution/fix",
  "severity": "low|medium|high|critical",
  "tags": ["tag1", "tag2"],
  "metadata": {
    "language": "python",
    "framework": "django",
    "stackoverflow_question_id": "12345"
  },
  "idempotency_key": "unique-key",
  "related_ids": []
}
```

## Configuration Options

### Environment Variables

- `SUPABASE_URL` - Your Supabase project URL (required)
- `SUPABASE_ANON_KEY` - Your Supabase anon key (required)
- `SUPABASE_SERVICE_ROLE_KEY` - Service role key for admin operations (optional)
- `MAX_CHUNK_SIZE` - Maximum size for text chunks (default: 1000)
- `BATCH_SIZE` - Number of entries to process in batch (default: 50)

### Redaction Patterns

The script automatically redacts:
- API keys and tokens
- Passwords and credentials  
- Database URLs with credentials
- Email addresses (partial)

## Embeddings

The current implementation includes a mock embedding generator for development. For production, replace the `generate_mock_embeddings` method with a real embedding service like:

- OpenAI Embeddings API
- Sentence Transformers
- Cohere Embeddings
- Azure Cognitive Services

Example with OpenAI:

```python
import openai

def generate_real_embeddings(self, chunks: List[str]) -> List[List[float]]:
    embeddings = []
    for chunk in chunks:
        response = openai.Embedding.create(
            model="text-embedding-ada-002",
            input=chunk
        )
        embeddings.append(response['data'][0]['embedding'])
    return embeddings
```

## Error Handling

The script includes comprehensive error handling:
- Network timeouts and retries
- Duplicate detection and handling
- Validation errors
- Detailed logging for troubleshooting

## Performance

- Async processing for concurrent operations
- Batch processing to reduce API calls
- Content hashing for efficient deduplication
- Configurable chunk sizes for optimal embedding performance

## Monitoring

Check the logs for:
- Upload progress and statistics
- Error details and failed entries
- Duplicate detection results
- Performance metrics

## Troubleshooting

### Common Issues

1. **Import Error**: Install dependencies with `pip install -r requirements.txt`
2. **Connection Error**: Check your `SUPABASE_URL` and `SUPABASE_ANON_KEY`
3. **RPC Function Not Found**: Ensure your database has the required RPC functions
4. **Permission Denied**: Check your Supabase Row Level Security policies

### Debug Mode

Set log level to DEBUG for detailed output:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```