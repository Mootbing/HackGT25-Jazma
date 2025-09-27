-- Enable extensions (Supabase usually allows these)
create extension if not exists pgcrypto;
create extension if not exists vector;

-- Entries table: core knowledge objects
create table if not exists entries (
  id uuid primary key default gen_random_uuid(),
  type text not null check (type in ('bug','solution','doc')),
  title text not null,
  body text,
  stack_trace text,
  code text,
  repro_steps text,
  root_cause text,
  resolution text,
  severity text check (severity in ('low','medium','high','critical')),
  tags text[] default '{}',
  project text,
  repo text,
  commit text,
  branch text,
  os text,
  runtime text,
  language text,
  framework text,
  resolved boolean default false,
  visibility text default 'private',
  content_hash text,
  created_by text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  search_vector tsvector generated always as (
    setweight(to_tsvector('english', coalesce(title,'')), 'A') ||
    setweight(to_tsvector('english', coalesce(body,'')), 'B') ||
    setweight(to_tsvector('english', coalesce(code,'')), 'B') ||
    setweight(to_tsvector('english', coalesce(stack_trace,'')), 'A')
  ) stored
);

create index if not exists idx_entries_search_vector on entries using gin (search_vector);
create index if not exists idx_entries_tags on entries using gin (tags);
create index if not exists idx_entries_project_repo on entries (project, repo);
create index if not exists idx_entries_created_at on entries (created_at desc);
create unique index if not exists idx_entries_content_hash on entries (content_hash);

-- Links for relationships
create table if not exists links (
  from_entry_id uuid references entries(id) on delete cascade,
  to_entry_id uuid references entries(id) on delete cascade,
  relation text not null,
  created_at timestamptz not null default now(),
  primary key (from_entry_id, to_entry_id, relation)
);

-- Embeddings: per-chunk vectors
-- Dimension must match EMBEDDING_DIM; default 1536
do $$
declare
  dim int := coalesce(nullif(current_setting('app.embedding_dim', true), '')::int, 1536);
begin
  execute format($sql$
    create table if not exists embeddings (
      entry_id uuid references entries(id) on delete cascade,
      chunk_id int not null,
      chunk_text text not null,
      embedding vector(%s) not null,
      created_at timestamptz not null default now(),
      primary key (entry_id, chunk_id)
    )
  $sql$, dim);
end $$;

-- Create an IVFFlat index for vector search (requires analyze and setting lists)
-- Use L2 distance on normalized vectors (cosine-equivalent ranking)
create index if not exists idx_embeddings_vector on embeddings using ivfflat (embedding vector_l2_ops) with (lists = 100);

analyze embeddings;

