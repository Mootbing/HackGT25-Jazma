// Cloudflare Worker entry point
import { createMcpServer } from './src/server.js';

export default {
  async fetch(request, env, ctx) {
    // Handle CORS preflight requests
    if (request.method === 'OPTIONS') {
      return new Response(null, {
        status: 200,
        headers: {
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
          'Access-Control-Allow-Headers': 'Content-Type, Authorization, mcp-session-id',
        },
      });
    }

    // Only handle POST requests to /mcp
    if (request.method !== 'POST' || new URL(request.url).pathname !== '/mcp') {
      return new Response('Not Found', { status: 404 });
    }

    try {
      // Parse request body
      const body = await request.json();
      
      // Create MCP server instance
      const server = await createMcpServer();
      
      // Handle MCP request (you'll need to adapt this based on your MCP implementation)
      // This is a simplified version - you may need to adapt based on your StreamableHTTPServerTransport logic
      
      const response = {
        // Your MCP response logic here
        jsonrpc: '2.0',
        id: body.id,
        result: 'MCP server running'
      };

      return new Response(JSON.stringify(response), {
        headers: {
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*',
        },
      });
    } catch (error) {
      return new Response(JSON.stringify({ error: error.message }), {
        status: 500,
        headers: {
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*',
        },
      });
    }
  },
};