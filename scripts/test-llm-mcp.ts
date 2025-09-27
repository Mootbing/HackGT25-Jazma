import 'dotenv/config';
import { experimental_createMCPClient, generateText } from 'ai';
import { StdioClientTransport } from '@modelcontextprotocol/sdk/client/stdio.js';
import { openai } from '@ai-sdk/openai';

async function run(): Promise<void> {
  // Connect to the local MCP server (stdio)
  const transport = new StdioClientTransport({
    command: 'node',
    args: ['dist/index.js'],
    env: process.env as Record<string, string>
  });

  const client = await experimental_createMCPClient({ transport });

  try {
    const tools = await client.tools();

    // Ask the LLM to use the MCP tools, preferring the `search` tool
    const result = await generateText({
      model: openai('gpt-4o'),
      tools,
      maxSteps: 8,
      temperature: 0.2,
      system: [
        'You have access to MCP tools: search, store.',
        'Use search as needed, then ALWAYS produce a final plain-text answer summarizing the findings.',
        'Do not skip the final summary. If tool output is JSON, interpret and then answer in plain text.'
      ].join(' '),
      prompt: [
        'Find similar issues for this error and summarize likely root causes and fixes:',
        '"TypeError: Cannot read properties of undefined (reading toLowerCase)".',
        'Focus on project="demo" repo="example". Return top 3 findings as bullets.'
      ].join('\n'),
      onStepFinish: (step) => {
        // eslint-disable-next-line no-console
        console.log('\n[step]', JSON.stringify({
          type: step.type,
          toolCalls: step.toolCalls,
          toolResults: step.toolResults
        }, null, 2));
      }
    });

    // eslint-disable-next-line no-console
    console.log('\nLLM answer:\n');
    // eslint-disable-next-line no-console
    if (result.text && result.text.trim().length > 0) {
      console.log(result.text);
    } else {
      // eslint-disable-next-line no-console
      console.log('[no text body returned]');
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

