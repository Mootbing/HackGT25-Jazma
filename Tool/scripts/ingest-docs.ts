import 'dotenv/config';
import { experimental_createMCPClient } from 'ai';
import { StdioClientTransport } from '@modelcontextprotocol/sdk/client/stdio.js';
import { readdirSync, statSync, readFileSync } from 'node:fs';
import { join, basename, extname } from 'node:path';

type IngestOptions = {
  dir: string;
  project?: string;
  repo?: string;
  tags?: string[];
};

function walkFiles(dir: string, exts: string[]): string[] {
  const out: string[] = [];
  const entries = readdirSync(dir);
  for (const entry of entries) {
    const p = join(dir, entry);
    const st = statSync(p);
    if (st.isDirectory()) {
      out.push(...walkFiles(p, exts));
    } else if (st.isFile() && exts.includes(extname(p).toLowerCase())) {
      out.push(p);
    }
  }
  return out;
}

async function run(): Promise<void> {
  const dir = process.argv[2] || 'docs';
  const project = process.env.INGEST_PROJECT || process.argv[3];
  const repo = process.env.INGEST_REPO || process.argv[4];
  const tagStr = process.env.INGEST_TAGS || process.argv[5];
  const tags = tagStr ? tagStr.split(',').map(s => s.trim()).filter(Boolean) : [];
  const options: IngestOptions = { dir, project, repo, tags };

  const files = walkFiles(options.dir, ['.md', '.mdx', '.txt']);
  if (files.length === 0) {
    // eslint-disable-next-line no-console
    console.error(`No docs found in ${options.dir} (.md|.mdx|.txt)`);
    process.exit(1);
  }

  const transport = new StdioClientTransport({ command: 'node', args: ['dist/index.js'], env: process.env as Record<string, string> });
  const client = await experimental_createMCPClient({ transport });
  try {
    const tools = await client.tools();
    const store = (tools as any).store;
    if (!store) throw new Error('store tool not available');

    // eslint-disable-next-line no-console
    console.log(`Ingesting ${files.length} file(s) from ${options.dir} ...`);

    for (const file of files) {
      const body = readFileSync(file, 'utf8');
      const title = basename(file);
      const res = await store.execute({
        type: 'doc',
        title,
        body,
        tags: options.tags,
        metadata: { project: options.project, repo: options.repo, language: 'markdown' }
      });
      const text = (res as any)?.content?.find((c: any) => c.type === 'text')?.text;
      // eslint-disable-next-line no-console
      console.log(`${title}: ${text}`);
    }
  } finally {
    await client.close();
  }
}

run().catch((err) => {
  // eslint-disable-next-line no-console
  console.error(err);
  process.exit(1);
});

