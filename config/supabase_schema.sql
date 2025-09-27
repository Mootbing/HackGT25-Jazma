-- Enable pgvector extension for semantic search
CREATE EXTENSION IF NOT EXISTS vector;

-- Bugfixes table with vector embeddings and storage references
CREATE TABLE bugfixes (
    id TEXT PRIMARY KEY,
    file TEXT NOT NULL,
    line_start INT,
    line_end INT,
    description TEXT NOT NULL,
    commit_hash TEXT NOT NULL,
    author TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    resolved BOOLEAN DEFAULT TRUE,
    related_issue TEXT,
    -- Supabase Storage references for patches, logs, and artifacts
    patch_blob_url TEXT,        -- URL to patch file in Supabase Storage
    log_blob_url TEXT,          -- URL to log file in Supabase Storage  
    artifact_blob_url TEXT,     -- URL to other artifacts in Supabase Storage
    embedding VECTOR(1536)      -- OpenAI text-embedding-3-small dimensions
);

-- Index for vector similarity search
CREATE INDEX bugfix_embedding_idx
ON bugfixes
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Metadata indexes for fast filtering
CREATE INDEX bugfix_file_idx ON bugfixes (file);
CREATE INDEX bugfix_commit_idx ON bugfixes (commit_hash);
CREATE INDEX bugfix_author_idx ON bugfixes (author);
CREATE INDEX bugfix_created_idx ON bugfixes (created_at);

-- Storage indexes for blob references
CREATE INDEX bugfix_patch_url_idx ON bugfixes (patch_blob_url);
CREATE INDEX bugfix_log_url_idx ON bugfixes (log_blob_url);
CREATE INDEX bugfix_artifact_url_idx ON bugfixes (artifact_blob_url);

-- Function for semantic similarity search
CREATE OR REPLACE FUNCTION match_bugfixes(
    query_embedding VECTOR(1536),
    match_threshold FLOAT DEFAULT 0.75,
    match_count INT DEFAULT 5,
    filter_file TEXT DEFAULT NULL
)
RETURNS TABLE (
    id TEXT,
    file TEXT,
    line_start INT,
    line_end INT,
    description TEXT,
    commit_hash TEXT,
    author TEXT,
    created_at TIMESTAMP,
    resolved BOOLEAN,
    related_issue TEXT,
    external_ref TEXT,
    similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        b.id,
        b.file,
        b.line_start,
        b.line_end,
        b.description,
        b.commit_hash,
        b.author,
        b.created_at,
        b.resolved,
        b.related_issue,
        b.external_ref,
        1 - (b.embedding <=> query_embedding) AS similarity
    FROM bugfixes b
    WHERE 
        (filter_file IS NULL OR b.file = filter_file)
        AND 1 - (b.embedding <=> query_embedding) > match_threshold
    ORDER BY b.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;
