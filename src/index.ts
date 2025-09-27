import 'dotenv/config';
import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { z } from 'zod';
import { createDbPool } from './lib/db.js';
import { searchToolHandler, searchInputSchema } from './tools/search.js';
import { storeToolHandler, storeInputSchema } from './tools/store.js';

async function main(): Promise<void> {
  const server = new McpServer({
    name: 'mcp-agent-knowledge',
    version: '0.1.0'
  });

  // Ensure DB initializes once during server boot
  await createDbPool();

  server.registerTool(
    'search',
    {
      title: 'Search knowledge base',
      description: 'Search bugs, solutions, and docs. Returns ranked results.',
      inputSchema: searchInputSchema
    },
    async (args) => {
      const result = await searchToolHandler(args);
      return {
        content: [
          { type: 'json', json: result }
        ]
      };
    }
  );

  server.registerTool(
    'store',
    {
      title: 'Store bug/solution/doc',
      description: 'Store a new bug or solution. Idempotent on content hash.',
      inputSchema: storeInputSchema
    },
    async (args) => {
      const result = await storeToolHandler(args);
      return {
        content: [
          { type: 'json', json: result }
        ]
      };
    }
  );

  const transport = new StdioServerTransport();
  await server.connect(transport);
  // eslint-disable-next-line no-console
  console.error('MCP server running (stdio)');
}

main().catch((err) => {
  // eslint-disable-next-line no-console
  console.error('Fatal error starting server:', err);
  process.exit(1);
});

