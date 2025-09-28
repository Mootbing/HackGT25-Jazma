import 'dotenv/config';
import { experimental_createMCPClient } from 'ai';
import { StdioClientTransport } from '@modelcontextprotocol/sdk/client/stdio.js';
async function run() {
    const transport = new StdioClientTransport({
        command: 'node',
        args: ['dist/index.js'],
        env: process.env
    });
    const client = await experimental_createMCPClient({ transport });
    try {
        // Get tools first
        const tools = await client.tools();
        
        // Store a sample entry using the working approach
        const storeResult = await tools.store.execute({
            type: 'bug',
            title: 'Test bug null pointer',
            body: 'Repro: clicking save crashes. Stack: TypeError: Cannot read properties of undefined',
            metadata: { project: 'demo', repo: 'example' },
            tags: ['demo', 'test']
        });
        // eslint-disable-next-line no-console
        console.log('store:', JSON.stringify(storeResult, null, 2));
        
        // Search for it using the working approach
        const searchResult = await tools.search.execute({
            query: 'Cannot read properties of undefined',
            filters: { project: 'demo' },
            top_k: 5
        });
        // eslint-disable-next-line no-console
        console.log('search:', JSON.stringify(searchResult, null, 2));
    }
    finally {
        await client.close();
    }
}
run().catch((err) => {
    // eslint-disable-next-line no-console
    console.error(err);
    process.exit(1);
});
