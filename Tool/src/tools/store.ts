import { z } from 'zod';
import { getSupabase } from '../lib/db.ts';
import { computeContentHash, redactSecrets } from '../util/text.ts';
import { embedChunks } from '../util/embeddings.ts';
import { chunkText } from '../util/chunking.ts';

export const storeInputSchema = z.object({
  type: z.enum(['bug','solution','doc']),
  title: z.string(),
  body: z.string().optional(),
  stack_trace: z.string().optional(),
  code: z.string().optional(),
  repro_steps: z.string().optional(),
  root_cause: z.string().optional(),
  resolution: z.string().optional(),
  severity: z.enum(['low','medium','high','critical']).optional(),
  tags: z.array(z.string()).optional(),
  metadata: z.object({
    project: z.string().optional(),
    repo: z.string().optional(),
    commit: z.string().optional(),
    branch: z.string().optional(),
    os: z.string().optional(),
    runtime: z.string().optional(),
    language: z.string().optional(),
    framework: z.string().optional()
  }).optional(),
  idempotency_key: z.string().optional(),
  related_ids: z.array(z.string()).optional()
}).strict();

type StoreArgs = z.infer<typeof storeInputSchema>;

export async function storeToolHandler(args: StoreArgs): Promise<{ id: string; duplicate_of?: string; created: boolean }> {
  const supabase = getSupabase();

  const body = redactSecrets(args.body ?? '');
  const code = redactSecrets(args.code ?? '');
  const stack = redactSecrets(args.stack_trace ?? '');
  const repro = redactSecrets(args.repro_steps ?? '');
  const resolution = redactSecrets(args.resolution ?? '');

  const payloadForHash = [args.type, args.title, body, code, stack, repro, resolution].join('\n\n');
  const contentHash = computeContentHash(payloadForHash);

  // Idempotency on content hash first
  const dup = await supabase.from('entries').select('id').eq('content_hash', contentHash).limit(1).maybeSingle();
  if (dup.data?.id) {
    const id = dup.data.id as string;
    return { id, duplicate_of: id, created: false };
  }

  const resolved = args.type === 'solution' || (!!resolution && resolution.trim().length > 0);

  const {
    project, repo, commit, branch, os, runtime, language, framework
  } = args.metadata ?? {};

  const insertRes = await supabase.rpc('rpc_insert_entry', {
    p_type: args.type,
    p_title: args.title,
    p_body: body || null,
    p_stack_trace: stack || null,
    p_code: code || null,
    p_repro_steps: repro || null,
    p_root_cause: args.root_cause || null,
    p_resolution: resolution || null,
    p_severity: args.severity || null,
    p_tags: args.tags ?? [],
    p_project: project || null,
    p_repo: repo || null,
    p_commit: commit || null,
    p_branch: branch || null,
    p_os: os || null,
    p_runtime: runtime || null,
    p_language: language || null,
    p_framework: framework || null,
    p_resolved: resolved,
    p_content_hash: contentHash
  });
  if (insertRes.error) throw insertRes.error;
  const entryId: string = insertRes.data as unknown as string;

  // Link related entries if provided
  if (args.related_ids?.length) {
    const linkRows = args.related_ids.map((rid) => ({ from_entry_id: entryId, to_entry_id: rid, relation: 'relates_to' }));
    // Upsert by primary key (from,to,relation)
    const linkRes = await supabase.from('links').upsert(linkRows, { onConflict: 'from_entry_id,to_entry_id,relation', ignoreDuplicates: true });
    if (linkRes.error) throw linkRes.error;
  }

  // Chunk important fields and embed
  const textToChunk = [body, code, stack, repro, resolution].filter(Boolean).join('\n\n');
  if (textToChunk.trim().length > 0) {
    const chunks = chunkText(textToChunk);
    const embeddings = await embedChunks(chunks);
    if (embeddings.length) {
      const chunkIds = embeddings.map((_, i) => i);
      const rpc = await supabase.rpc('rpc_insert_embeddings', {
        p_entry_id: entryId,
        p_chunk_ids: chunkIds,
        p_chunk_texts: chunks,
        p_embeddings: embeddings
      });
      if (rpc.error) throw rpc.error;
    }
  }

  return { id: entryId, created: true };
}

