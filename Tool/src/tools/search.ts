import { z } from 'zod';
import { getSupabase } from '../lib/db.js';
import { textEmbedding } from '../util/embeddings.js';

export const searchInputSchema = z.object({
  query: z.string(),
  top_k: z.number().int().min(1).max(50).optional().default(10),
  filters: z.object({
    project: z.string().optional(),
    repo: z.string().optional(),
    language: z.string().optional(),
    tags: z.array(z.string()).optional(),
    severity: z.enum(['low','medium','high','critical']).optional(),
    resolved: z.boolean().optional(),
    since: z.string().datetime().optional()
  }).optional()
}).strict();

type SearchArgs = z.infer<typeof searchInputSchema>;

export async function searchToolHandler(args: SearchArgs): Promise<{ results: Array<{
  id: string; title: string; summary: string; snippet?: string; score: number; metadata: Record<string, unknown>
}> }> {
  const supabase = getSupabase();
  const topK = args.top_k ?? 10;

  // Build filter clauses
  const filters: string[] = [];
  const params: unknown[] = [];
  let p = 0;
  if (args.filters?.project) { params.push(args.filters.project); p++; filters.push(`project = $${p}`); }
  if (args.filters?.repo) { params.push(args.filters.repo); p++; filters.push(`repo = $${p}`); }
  if (args.filters?.language) { params.push(args.filters.language); p++; filters.push(`language = $${p}`); }
  if (args.filters?.severity) { params.push(args.filters.severity); p++; filters.push(`severity = $${p}`); }
  if (typeof args.filters?.resolved === 'boolean') { params.push(args.filters.resolved); p++; filters.push(`resolved = $${p}`); }
  if (args.filters?.since) { params.push(args.filters.since); p++; filters.push(`created_at >= $${p}::timestamptz`); }
  if (args.filters?.tags?.length) { params.push(args.filters.tags); p++; filters.push(`tags && $${p}::text[]`); }
  const where = filters.length ? `(${filters.join(' and ')})` : 'true';

  // Lexical via RPC
  const [lexicalRes, queryEmbedding] = await Promise.all([
    supabase.rpc('rpc_hybrid_search', {
      p_query: args.query,
      p_limit: Math.max(topK, 20),
      p_project: args.filters?.project ?? null,
      p_repo: args.filters?.repo ?? null,
      p_language: args.filters?.language ?? null,
      p_tags: args.filters?.tags ?? null,
      p_severity: args.filters?.severity ?? null,
      p_resolved: args.filters?.resolved ?? null,
      p_since: args.filters?.since ?? null
    }),
    textEmbedding(args.query)
  ]);

  // Vector: similarity search on chunk embeddings
  const vectorRes = await supabase
    .rpc('match_embeddings', {
      query_embedding: queryEmbedding,
      match_count: Math.max(topK, 20),
      p_project: args.filters?.project ?? null,
      p_repo: args.filters?.repo ?? null,
      p_language: args.filters?.language ?? null,
      p_tags: args.filters?.tags ?? null,
      p_severity: args.filters?.severity ?? null,
      p_resolved: args.filters?.resolved ?? null,
      p_since: args.filters?.since ?? null
    })
    .select();

  // Reciprocal rank fusion (lightweight)
  const fused = new Map<string, { score: number; row: any; }>();
  const addList = (rows: any[], key: 'rank' | 'sim') => {
    rows.forEach((row, idx) => {
      const id = row.id as string;
      const rrf = 1 / (60 + idx + 1);
      const prev = fused.get(id);
      const base = key === 'rank' ? (row.rank ?? 0) : (row.sim ?? 0);
      const score = (prev?.score ?? 0) + base + rrf;
      fused.set(id, { score, row });
    });
  };
  if (lexicalRes.error) throw lexicalRes.error;
  const lexRows = lexicalRes.data ?? [];
  addList(lexRows as any[], 'rank');

  if ((vectorRes as any).error) throw (vectorRes as any).error;
  const vecRows = (vectorRes as any).data ?? [];
  addList(vecRows as any[], 'sim');

  const sorted = Array.from(fused.values())
    .sort((a, b) => b.score - a.score)
    .slice(0, topK);

  const results = sorted.map(({ score, row }) => {
    const body: string = row.body ?? '';
    const code: string = row.code ?? '';
    const snippet = (body || code).slice(0, 400);
    const summary = body ? body.slice(0, 200) : code.slice(0, 200);
    return {
      id: row.id,
      title: row.title,
      summary,
      snippet,
      score: Number(score),
      metadata: {
        project: row.project,
        repo: row.repo,
        language: row.language,
        tags: row.tags,
        severity: row.severity,
        resolved: row.resolved
      }
    };
  });

  return { results };
}

