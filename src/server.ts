import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { z } from 'zod';
import { createDbPool } from './lib/db.js';
import { searchToolHandler } from './tools/search.js';
import { storeToolHandler } from './tools/store.js';

export async function createMcpServer(): Promise<McpServer> {
  await createDbPool();
  const server = new McpServer({
    name: 'mcp-agent-knowledge',
    version: '0.1.0'
  });

  const searchShape = {
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
  } as const;

  server.registerTool(
    'search',
    {
      title: 'Search knowledge base',
      description: 'Search bugs, solutions, and docs. Returns ranked results.',
      inputSchema: searchShape as unknown as Record<string, z.ZodTypeAny>
    },
    async (args: any) => {
      try {
        const result = await searchToolHandler(args);
        return { content: [{ type: 'text', text: JSON.stringify(result, null, 2) }] };
      } catch (err: any) {
        const message = err?.message || 'search failed';
        const details = err?.error || err?.data || err;
        return { content: [{ type: 'text', text: `error: ${message}\n${safeStringify(details)}` }], isError: true } as any;
      }
    }
  );

  const storeShape = {
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
  } as const;

  server.registerTool(
    'store',
    {
      title: 'Store bug/solution/doc',
      description: 'Store a new bug or solution. Idempotent on content hash.',
      inputSchema: storeShape as unknown as Record<string, z.ZodTypeAny>
    },
    async (args: any) => {
      try {
        const result = await storeToolHandler(args);
        return { content: [{ type: 'text', text: JSON.stringify(result, null, 2) }] };
      } catch (err: any) {
        const message = err?.message || 'store failed';
        const details = err?.error || err?.data || err;
        return { content: [{ type: 'text', text: `error: ${message}\n${safeStringify(details)}` }], isError: true } as any;
      }
    }
  );

  function safeStringify(value: unknown): string {
    try {
      if (typeof value === 'string') return value;
      return JSON.stringify(value, null, 2);
    } catch {
      return String(value);
    }
  }

  return server;
}

