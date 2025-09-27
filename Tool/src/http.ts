import 'dotenv/config';
import express, { Request, Response } from 'express';
import { randomUUID } from 'node:crypto';
import { StreamableHTTPServerTransport } from '@modelcontextprotocol/sdk/server/streamableHttp.js';
import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { createMcpServer } from './server.js';

async function main(): Promise<void> {
  const app = express();
  app.use(express.json());

  const transports: Record<string, StreamableHTTPServerTransport> = {};

  app.post('/mcp', async (req: Request, res: Response) => {
    const sessionId = req.headers['mcp-session-id'] as string | undefined;
    let transport = sessionId ? transports[sessionId] : undefined;

    if (!transport) {
      transport = new StreamableHTTPServerTransport({
        sessionIdGenerator: () => randomUUID(),
        onsessioninitialized: (sid) => { transports[sid] = transport!; }
      });

      const server: McpServer = await createMcpServer();
      await server.connect(transport);

      transport.onclose = () => {
        if (transport?.sessionId) delete transports[transport.sessionId];
      };
    }

    await transport.handleRequest(req, res);
  });

  const port = Number(process.env.PORT || '8080');
  app.listen(port, () => {
    // eslint-disable-next-line no-console
    console.error(`HTTP MCP listening on :${port}`);
  });
}

main().catch((err) => {
  // eslint-disable-next-line no-console
  console.error('HTTP MCP fatal:', err);
  process.exit(1);
});

