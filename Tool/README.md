# MCP Knowledge Base for Coding Agents

Persistent, searchable memory of bugs and fixes for MCP-capable agents.

## Quickstart

1. Copy env and set secrets
   ```bash
   cp .env.example .env
   # set DATABASE_URL (Supabase Postgres), OPENAI_API_KEY
   ```

2. Install deps
   ```bash
   npm i
   ```

3. Create schema in Supabase (one-time)
   - Open your Supabase project → SQL Editor
   - Copy contents of `infra/migrations/001_init.sql` and run

4. Start MCP server (stdio)
   ```bash
   npm run dev
   ```

Integrate the server via MCP with tools `search` and `store`.

## Environment

- `SUPABASE_URL`: Your project URL (e.g., `https://<ref>.supabase.co`)
- `SUPABASE_ANON_KEY`: Supabase anon key
- `OPENAI_API_KEY`: For embeddings (text-embedding-3-small)
- `EMBEDDING_MODEL`: Embedding model id (default: `text-embedding-3-small`)
- `EMBEDDING_DIM`: Vector dimension (default: 1536)

## Notes

- Ensure pgvector extension is enabled in Supabase.
- This MVP performs synchronous embedding on `store` for simplicity.
