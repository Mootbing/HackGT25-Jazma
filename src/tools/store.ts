import { z } from 'zod';
import { getDbPool } from '../lib/db.js';
import { computeContentHash, redactSecrets } from '../util/text.js';
import { embedChunks } from '../util/embeddings.js';
import { chunkText } from '../util/chunking.js';

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
  const pool = getDbPool();

  const body = redactSecrets(args.body ?? '');
  const code = redactSecrets(args.code ?? '');
  const stack = redactSecrets(args.stack_trace ?? '');
  const repro = redactSecrets(args.repro_steps ?? '');
  const resolution = redactSecrets(args.resolution ?? '');

  const payloadForHash = [args.type, args.title, body, code, stack, repro, resolution].join('\n\n');
  const contentHash = computeContentHash(payloadForHash);

  // Idempotency on content hash first
  const dup = await pool.query('select id from entries where content_hash = $1 limit 1', [contentHash]);
  if (dup.rowCount) {
    const id = dup.rows[0].id as string;
    return { id, duplicate_of: id, created: false };
  }

  const resolved = args.type === 'solution' || (!!resolution && resolution.trim().length > 0);

  const {
    project, repo, commit, branch, os, runtime, language, framework
  } = args.metadata ?? {};

  const insertRes = await pool.query(
    `insert into entries (
      type, title, body, stack_trace, code, repro_steps, root_cause, resolution,
      severity, tags, project, repo, commit, branch, os, runtime, language, framework,
      resolved, content_hash
    ) values (
      $1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,$17,$18,$19,$20
    ) returning id`,
    [
      args.type, args.title, body || null, stack || null, code || null, repro || null, args.root_cause || null,
      resolution || null, args.severity || null, args.tags ?? [], project || null, repo || null, commit || null,
      branch || null, os || null, runtime || null, language || null, framework || null, resolved, contentHash
    ]
  );

  const entryId: string = insertRes.rows[0].id;

  // Link related entries if provided
  if (args.related_ids?.length) {
    const values: unknown[] = [];
    const tuples = args.related_ids.map((rid, i) => {
      values.push(entryId, rid, 'relates_to');
      const base = i * 3;
      return `($${base + 1}, $${base + 2}, $${base + 3})`;
    }).join(',');
    await pool.query(`insert into links (from_entry_id, to_entry_id, relation) values ${tuples} on conflict do nothing`, values);
  }

  // Chunk important fields and embed
  const textToChunk = [body, code, stack, repro, resolution].filter(Boolean).join('\n\n');
  if (textToChunk.trim().length > 0) {
    const chunks = chunkText(textToChunk);
    const embeddings = await embedChunks(chunks);
    if (embeddings.length) {
      const values: unknown[] = [];
      const rows: string[] = [];
      embeddings.forEach((emb, idx) => {
        values.push(entryId, idx, chunks[idx], emb);
        const base = idx * 4;
        rows.push(`($${base + 1}, $${base + 2}, $${base + 3}, $${base + 4}::vector)`);
      });
      await pool.query(
        `insert into embeddings (entry_id, chunk_id, chunk_text, embedding) values ${rows.join(',')}`,
        values
      );
    }
  }

  return { id: entryId, created: true };
}

