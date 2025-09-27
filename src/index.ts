import 'dotenv/config';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { createMcpServer } from './server.js';

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
      const status = await fetch('http://localhost:8000/process');
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

