# Cloudflare Deployment Guide

Since Wrangler CLI isn't compatible with ARM64 Windows, here are alternative deployment methods:

## Method 1: Cloudflare Dashboard (Recommended)

### Step 1: Create a Worker

1. Go to [Cloudflare Dashboard](https://dash.cloudflare.com/)
2. Navigate to **Workers & Pages**
3. Click **Create application** → **Create Worker**
4. Give it a name like `mcp-knowledge-base`

### Step 2: Deploy the Code

1. Copy the entire contents of `cloudflare-worker.js`
2. Paste it into the Cloudflare Workers editor
3. Click **Save and Deploy**

### Step 3: Set Environment Variables

In your Worker's Settings → Variables, add:

```
SUPABASE_URL = https://kfymzqagopnywhsgizio.supabase.co
SUPABASE_ANON_KEY = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtmeW16cWFnb3BueXdoc2dpemlvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTg5NDA1MDQsImV4cCI6MjA3NDUxNjUwNH0.5Pnh2HPN9jLRF9jUdnaLxbeDvAlZPtp5aRIsa9Loxxs
OPENAI_API_KEY = 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
EMBEDDING_MODEL = text-embedding-3-small
EMBEDDING_DIM = 1536
```

**Important**: Use "Encrypt" for sensitive values like API keys!

### Step 4: Test Your Deployment

Your worker will be available at: `https://mcp-knowledge-base.<your-subdomain>.workers.dev`

Test endpoints:
- `GET /` - Documentation
- `GET /health` - Health check
- `POST /mcp` - MCP protocol endpoint

## Method 2: GitHub Actions (Automated)

### Step 1: Set GitHub Secrets

In your repository settings → Secrets and variables → Actions, add:

```
CLOUDFLARE_API_TOKEN = <your_cloudflare_api_token>
SUPABASE_URL = <your_supabase_url>
SUPABASE_ANON_KEY = <your_supabase_key>
OPENAI_API_KEY = <your_openai_key>
```

### Step 2: Get Cloudflare API Token

1. Go to [Cloudflare API Tokens](https://dash.cloudflare.com/profile/api-tokens)
2. Click **Create Token**
3. Use the **Custom token** template
4. Set permissions:
   - Account: Cloudflare Workers:Edit
   - Zone: Zone:Read (if using custom domain)

### Step 3: Push to GitHub

The `.github/workflows/deploy.yml` file will automatically deploy when you push to the `main` or `mcp` branch.

## Method 3: Local Development Alternative

Since Wrangler CLI doesn't work on your system, you can:

1. **Use GitHub Codespaces** (Linux environment)
2. **Use WSL2** (Windows Subsystem for Linux)
3. **Use Docker** with a Linux container

## Testing Your Deployment

### Basic Health Check
```bash
curl https://your-worker.workers.dev/health
```

### Test MCP Protocol
```bash
curl -X POST https://your-worker.workers.dev/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/list",
    "params": {}
  }'
```

### Test Search Tool
```bash
curl -X POST https://your-worker.workers.dev/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0", 
    "id": 2,
    "method": "tools/call",
    "params": {
      "name": "search",
      "arguments": {
        "query": "typescript errors"
      }
    }
  }'
```

## Next Steps

1. **Deploy using Method 1** (Dashboard) for immediate results
2. **Set up GitHub Actions** for automated deployments
3. **Integrate Supabase** for real database operations
4. **Add authentication** if needed
5. **Set up custom domain** (optional)

## Troubleshooting

- **Worker not responding**: Check the deployment logs in Cloudflare Dashboard
- **Environment variables**: Ensure all secrets are set correctly
- **CORS issues**: The worker includes CORS headers for browser compatibility
- **MCP errors**: Check the console output in the Cloudflare Workers editor

## Production Considerations

- Replace mock data with actual Supabase integration
- Add rate limiting and authentication
- Use Cloudflare Durable Objects for session management
- Set up monitoring and alerts
- Configure custom domain and SSL