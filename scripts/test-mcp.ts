import 'dotenv/config';
import { experimental_createMCPClient } from 'ai';
import { StdioClientTransport } from '@modelcontextprotocol/sdk/client/stdio.js';

async function run(): Promise<void> {
  const transport = new StdioClientTransport({
    command: 'node',
    args: ['dist/index.js'],
    env: process.env as Record<string, string>
  });

  const client = await experimental_createMCPClient({ transport });
  try {
    const tools = await client.tools();
    // Inspect available tool API
    // eslint-disable-next-line no-console
    console.log('available tools:', Object.keys(tools));
    // eslint-disable-next-line no-console
    console.log('store keys:', Object.keys((tools as any).store || {}));
    // Store a sample entry
    const storeResult = await (tools as any).store.execute({
      type: 'bug',
      title: 'Test bug null pointer',
      body: 'Repro: clicking save crashes. Stack: TypeError: Cannot read properties of undefined',
      metadata: { project: 'demo', repo: 'example' },
      tags: ['demo','test']
    });
    // Print tool text output for readability
    const storeText = (storeResult as any)?.content?.find((c: any) => c.type === 'text')?.text;
    // eslint-disable-next-line no-console
    console.log('store:', storeText ?? JSON.stringify(storeResult, null, 2));

    // Search for it
    const searchResult = await (tools as any).search.execute({ query: 'Cannot read properties of undefined', filters: { project: 'demo' }, top_k: 5 });
    const searchText = (searchResult as any)?.content?.find((c: any) => c.type === 'text')?.text;
    // eslint-disable-next-line no-console
    console.log('search:', searchText ?? JSON.stringify(searchResult, null, 2));
  } finally {
    await client.close();
  }
}

run().catch((err) => {
  // eslint-disable-next-line no-console
  console.error(err);
  process.exit(1);
});

