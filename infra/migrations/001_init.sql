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

-- RLS and permissive policies (adjust in production)
alter table entries enable row level security;
alter table embeddings enable row level security;
alter table links enable row level security;

create policy "entries read" on entries for select using (true);
create policy "entries write" on entries for insert with check (true);
create policy "embeddings read" on embeddings for select using (true);
create policy "embeddings write" on embeddings for insert with check (true);
create policy "links read" on links for select using (true);
create policy "links write" on links for insert with check (true);

-- RPC: insert entry, returns id
create or replace function rpc_insert_entry(
  p_type text,
  p_title text,
  p_body text,
  p_stack_trace text,
  p_code text,
  p_repro_steps text,
  p_root_cause text,
  p_resolution text,
  p_severity text,
  p_tags text[],
  p_project text,
  p_repo text,
  p_commit text,
  p_branch text,
  p_os text,
  p_runtime text,
  p_language text,
  p_framework text,
  p_resolved boolean,
  p_content_hash text
)
returns uuid
language plpgsql
as $$
declare v_id uuid;
begin
  insert into entries (
    type, title, body, stack_trace, code, repro_steps, root_cause, resolution, severity, tags,
    project, repo, commit, branch, os, runtime, language, framework, resolved, content_hash
  ) values (
    p_type, p_title, p_body, p_stack_trace, p_code, p_repro_steps, p_root_cause, p_resolution, p_severity, coalesce(p_tags,'{}'),
    p_project, p_repo, p_commit, p_branch, p_os, p_runtime, p_language, p_framework, p_resolved, p_content_hash
  ) returning id into v_id;
  return v_id;
end $$;

-- RPC: batch insert embeddings
create or replace function rpc_insert_embeddings(
  p_entry_id uuid,
  p_chunk_ids int[],
  p_chunk_texts text[],
  p_embeddings vector[]
)
returns void
language plpgsql
as $$
begin
  insert into embeddings (entry_id, chunk_id, chunk_text, embedding)
  select p_entry_id, unnest(p_chunk_ids), unnest(p_chunk_texts), unnest(p_embeddings);
end $$;

-- RPC: simple lexical search
create or replace function rpc_hybrid_search(
  p_query text,
  p_limit int default 10,
  p_project text default null,
  p_repo text default null,
  p_language text default null,
  p_tags text[] default null,
  p_severity text default null,
  p_resolved boolean default null,
  p_since timestamptz default null
)
returns table (
  id uuid,
  title text,
  body text,
  code text,
  project text,
  repo text,
  language text,
  tags text[],
  severity text,
  resolved boolean,
  rank real
)
language sql
as $$
  select id, title, body, code, project, repo, language, tags, severity, resolved,
         ts_rank(search_vector, plainto_tsquery('english', p_query)) as rank
    from entries
   where (p_project is null or project = p_project)
     and (p_repo is null or repo = p_repo)
     and (p_language is null or language = p_language)
     and (p_severity is null or severity = p_severity)
     and (p_resolved is null or resolved = p_resolved)
     and (p_since is null or created_at >= p_since)
     and (p_tags is null or tags && p_tags)
    order by rank desc nulls last
    limit p_limit
$$;

-- RPC: vector similarity search with optional filters
create or replace function match_embeddings(
  query_embedding vector(1536),
  match_count int default 10,
  p_project text default null,
  p_repo text default null,
  p_language text default null,
  p_tags text[] default null,
  p_severity text default null,
  p_resolved boolean default null,
  p_since timestamptz default null
)
returns table (
  id uuid,
  title text,
  body text,
  code text,
  project text,
  repo text,
  language text,
  tags text[],
  severity text,
  resolved boolean,
  sim double precision
)
language sql
as $$
  select e.id, e.title, e.body, e.code, e.project, e.repo, e.language, e.tags, e.severity, e.resolved,
         1 - (m.embedding <#> query_embedding) as sim
    from embeddings m
    join entries e on e.id = m.entry_id
   where (p_project is null or e.project = p_project)
     and (p_repo is null or e.repo = p_repo)
     and (p_language is null or e.language = p_language)
     and (p_severity is null or e.severity = p_severity)
     and (p_resolved is null or e.resolved = p_resolved)
     and (p_since is null or e.created_at >= p_since)
     and (p_tags is null or e.tags && p_tags)
   order by m.embedding <#> query_embedding asc
   limit match_count
$$;

