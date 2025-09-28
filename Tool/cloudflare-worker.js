// Cloudflare Worker for MCP Knowledge Base
// Compatible with Cloudflare Workers runtime

// CORS headers for API responses
const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type, Authorization, mcp-session-id, x-api-key',
};

// Simple in-memory session storage (for demo purposes)
// In production, you'd use Cloudflare Durable Objects or KV
const sessions = new Map();

export default {
  async fetch(request, env, ctx) {
    // Handle CORS preflight requests
    if (request.method === 'OPTIONS') {
      return new Response(null, {
        status: 200,
        headers: corsHeaders
      });
    }

    const url = new URL(request.url);

    // Health check endpoint
    if (url.pathname === '/health') {
      return new Response(JSON.stringify({
        status: 'healthy',
        timestamp: new Date().toISOString(),
        service: 'mcp-knowledge-base'
      }), {
        headers: {
          'Content-Type': 'application/json',
          ...corsHeaders
        }
      });
    }

    // Main MCP endpoint
    if (url.pathname === '/mcp' && request.method === 'POST') {
      try {
        const body = await request.json();
        const sessionId = request.headers.get('mcp-session-id') || 'default';
        
        // Handle different MCP method types
        const response = await handleMcpRequest(body, sessionId, env);
        
        return new Response(JSON.stringify(response), {
          headers: {
            'Content-Type': 'application/json',
            ...corsHeaders,
            'mcp-session-id': sessionId
          }
        });
      } catch (error) {
        console.error('MCP request error:', error);
        
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

    // API documentation endpoint
    if (url.pathname === '/' || url.pathname === '/docs') {
      return new Response(`
# MCP Knowledge Base API

This is a Model Context Protocol (MCP) server for managing coding knowledge.

## Endpoints

- \`POST /mcp\` - Main MCP protocol endpoint
- \`GET /health\` - Health check
- \`GET /docs\` - This documentation

## MCP Methods

- \`tools/list\` - List available tools
- \`tools/call\` - Execute a tool
  - \`search\` - Search the knowledge base
  - \`store\` - Store new knowledge

## Headers

- \`mcp-session-id\` - Session identifier for stateful operations
- \`Content-Type: application/json\`

## Environment Variables

Set these in your Cloudflare Worker:
- \`SUPABASE_URL\` - Your Supabase project URL
- \`SUPABASE_ANON_KEY\` - Supabase anonymous key
- \`OPENAI_API_KEY\` - OpenAI API key for embeddings

Deployed at: ${new Date().toISOString()}
      `, {
        headers: {
          'Content-Type': 'text/plain',
          ...corsHeaders
        }
      });
    }

    // 404 for other paths
    return new Response('Not Found', { 
      status: 404,
      headers: corsHeaders
    });
  }
};

// Handle MCP protocol requests
async function handleMcpRequest(body, sessionId, env) {
  const { method, params, id } = body;

  switch (method) {
    case 'initialize':
      return {
        jsonrpc: '2.0',
        id,
        result: {
          protocolVersion: '2024-11-05',
          capabilities: {
            tools: {},
            logging: {},
          },
          serverInfo: {
            name: 'mcp-agent-knowledge',
            version: '0.1.0'
          }
        }
      };

    case 'tools/list':
      return {
        jsonrpc: '2.0',
        id,
        result: {
          tools: [
            {
              name: 'search',
              description: 'Search the knowledge base for bugs, solutions, and documentation',
              inputSchema: {
                type: 'object',
                properties: {
                  query: { type: 'string', description: 'Search query' },
                  top_k: { type: 'number', default: 10, minimum: 1, maximum: 50 },
                  filters: {
                    type: 'object',
                    properties: {
                      project: { type: 'string' },
                      language: { type: 'string' },
                      tags: { type: 'array', items: { type: 'string' } },
                      severity: { type: 'string', enum: ['low', 'medium', 'high', 'critical'] }
                    }
                  }
                },
                required: ['query']
              }
            },
            {
              name: 'store',
              description: 'Store new knowledge entry in the database',
              inputSchema: {
                type: 'object',
                properties: {
                  title: { type: 'string', description: 'Title of the knowledge entry' },
                  content: { type: 'string', description: 'Content/solution description' },
                  project: { type: 'string' },
                  language: { type: 'string' },
                  tags: { type: 'array', items: { type: 'string' } },
                  severity: { type: 'string', enum: ['low', 'medium', 'high', 'critical'] }
                },
                required: ['title', 'content']
              }
            }
          ]
        }
      };

    case 'tools/call':
      return await handleToolCall(params, env);

    default:
      return {
        jsonrpc: '2.0',
        id,
        error: {
          code: -32601,
          message: `Method not found: ${method}`
        }
      };
  }
}

// Handle tool execution
async function handleToolCall(params, env) {
  const { name, arguments: args } = params;

  switch (name) {
    case 'search':
      return await handleSearchTool(args, params, env);
    case 'store':
      return await handleStoreTool(args, params, env);
    default:
      throw new Error(`Unknown tool: ${name}`);
  }
}

// Search tool implementation
async function handleSearchTool(args, params, env) {
  try {
    // For now, return mock data - you'll integrate with Supabase
    const mockResults = [
      {
        id: '1',
        title: 'Common TypeScript Build Errors',
        summary: 'Solutions for module resolution and type checking issues',
        content: 'When encountering TypeScript build errors...',
        project: 'hackgt25',
        language: 'typescript',
        tags: ['build', 'typescript', 'errors'],
        severity: 'medium',
        similarity: 0.95,
        created_at: new Date().toISOString()
      },
      {
        id: '2', 
        title: 'Cloudflare Worker Deployment Issues',
        summary: 'Platform compatibility and deployment troubleshooting',
        content: 'ARM64 compatibility issues with Wrangler CLI...',
        project: 'deployment',
        language: 'javascript',
        tags: ['cloudflare', 'deployment', 'workers'],
        severity: 'high',
        similarity: 0.88,
        created_at: new Date().toISOString()
      }
    ];

    const filteredResults = mockResults.filter(r => 
      r.title.toLowerCase().includes(args.query.toLowerCase()) ||
      r.summary.toLowerCase().includes(args.query.toLowerCase())
    );

    return {
      jsonrpc: '2.0',
      id: params.id,
      result: {
        content: [{
          type: 'json',
          json: {
            results: filteredResults.slice(0, args.top_k || 10),
            total: filteredResults.length,
            query: args.query,
            timestamp: new Date().toISOString()
          }
        }]
      }
    };
  } catch (error) {
    throw new Error(`Search failed: ${error.message}`);
  }
}

// Store tool implementation  
async function handleStoreTool(args, params, env) {
  try {
    // For now, simulate storage - you'll integrate with Supabase
    const entry = {
      id: Date.now().toString(),
      title: args.title,
      content: args.content,
      project: args.project || 'unknown',
      language: args.language || 'unknown', 
      tags: args.tags || [],
      severity: args.severity || 'medium',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    };

    return {
      jsonrpc: '2.0',
      id: params.id,
      result: {
        content: [{
          type: 'json',
          json: {
            success: true,
            id: entry.id,
            message: 'Knowledge entry stored successfully',
            entry: entry
          }
        }]
      }
    };
  } catch (error) {
    throw new Error(`Store failed: ${error.message}`);
  }
}