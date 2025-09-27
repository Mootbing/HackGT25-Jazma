// Simplified Cloudflare Worker for MCP Knowledge Base
// This is a basic implementation - you may need to adapt based on your specific MCP server logic

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type, Authorization, mcp-session-id',
};

export default {
  async fetch(request, env, ctx) {
    // Handle CORS preflight
    if (request.method === 'OPTIONS') {
      return new Response(null, { status: 200, headers: corsHeaders });
    }

    const url = new URL(request.url);
    
    // Health check endpoint
    if (url.pathname === '/health') {
      return new Response('OK', { 
        headers: { 'Content-Type': 'text/plain', ...corsHeaders } 
      });
    }

    // MCP endpoint
    if (url.pathname === '/mcp' && request.method === 'POST') {
      try {
        const body = await request.json();
        
        // Basic MCP response structure
        const response = {
          jsonrpc: '2.0',
          id: body.id || 1,
          result: {
            status: 'success',
            message: 'MCP Knowledge Base Worker is running',
            timestamp: new Date().toISOString()
          }
        };

        return new Response(JSON.stringify(response), {
          headers: {
            'Content-Type': 'application/json',
            ...corsHeaders
          }
        });
      } catch (error) {
        return new Response(JSON.stringify({
          jsonrpc: '2.0',
          id: null,
          error: {
            code: -32700,
            message: 'Parse error',
            data: error.message
          }
        }), {
          status: 400,
          headers: {
            'Content-Type': 'application/json',
            ...corsHeaders
          }
        });
      }
    }

    // Default response
    return new Response('MCP Knowledge Base API', {
      headers: { 'Content-Type': 'text/plain', ...corsHeaders }
    });
  }
};