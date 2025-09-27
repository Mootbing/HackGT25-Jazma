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
    // Store comprehensive bug
    const bugPayload = {
      type: 'bug',
      title: 'Crash on save when user profile missing lastName',
      body: [
        'When saving a user profile without lastName, the app crashes.',
        'Expected: Save should succeed and default lastName to empty string.'
      ].join('\n'),
      stack_trace: [
        "TypeError: Cannot read properties of undefined (reading 'toLowerCase')",
        '    at saveProfile (/app/src/profile/save.ts:42:18)',
        '    at onClick (/app/src/components/ProfileForm.tsx:88:11)'
      ].join('\n'),
      code: [
        'export function saveProfile(user: { firstName?: string; lastName?: string }) {',
        '  // Fails when lastName is undefined',
        '  return user.lastName.toLowerCase();',
        '}'
      ].join('\n'),
      repro_steps: [
        '1. Go to Profile page',
        '2. Clear the Last Name field',
        '3. Click Save',
        '4. Observe crash'
      ].join('\n'),
      root_cause: 'Null/undefined lastName calls toLowerCase()',
      resolution: 'Add nullish coalescing default before toLowerCase()',
      severity: 'high' as const,
      tags: ['frontend','profile','TypeError','null'],
      metadata: {
        project: 'demo',
        repo: 'example',
        commit: 'abc1234',
        branch: 'main',
        os: 'macOS 14.5',
        runtime: 'Node 18.20',
        language: 'TypeScript',
        framework: 'React 18'
      },
      idempotency_key: `bug-${Date.now()}`
    };
    const storeBugResult = await (tools as any).store.execute(bugPayload);
    const storeBugText = (storeBugResult as any)?.content?.find((c: any) => c.type === 'text')?.text;
    // eslint-disable-next-line no-console
    console.log('store (bug):', storeBugText ?? JSON.stringify(storeBugResult, null, 2));
    let bugId: string | undefined;
    try { bugId = JSON.parse(storeBugText || '{}')?.id; } catch {}

    // Store solution linked to bug
    const solutionPayload = {
      type: 'solution' as const,
      title: 'Fix: Guard lastName before toLowerCase and default to empty',
      body: [
        'Guarded undefined lastName with nullish coalescing and added unit tests.',
        'Verified no crash when lastName is missing.'
      ].join('\n'),
      stack_trace: 'N/A after fix',
      code: [
        'export function saveProfile(user: { firstName?: string; lastName?: string }) {',
        '  const lastName = (user.lastName ?? "").toLowerCase();',
        '  return lastName;',
        '}'
      ].join('\n'),
      repro_steps: [
        '1. Clear Last Name',
        '2. Click Save',
        '3. No crash; save succeeds'
      ].join('\n'),
      root_cause: 'Call to toLowerCase on possibly undefined value',
      resolution: 'Applied nullish coalescing and default; added tests',
      severity: 'medium' as const,
      tags: ['fix','PR-123','regression-test-added'],
      metadata: {
        project: 'demo',
        repo: 'example',
        commit: 'def5678',
        branch: 'main',
        os: 'macOS 14.5',
        runtime: 'Node 18.20',
        language: 'TypeScript',
        framework: 'React 18'
      },
      related_ids: bugId ? [bugId] : undefined,
      idempotency_key: `solution-${Date.now()}`
    };
    const storeSolutionResult = await (tools as any).store.execute(solutionPayload);
    const storeSolutionText = (storeSolutionResult as any)?.content?.find((c: any) => c.type === 'text')?.text;
    // eslint-disable-next-line no-console
    console.log('store (solution):', storeSolutionText ?? JSON.stringify(storeSolutionResult, null, 2));

    // Search that should match both lexical and vector
    const searchResult = await (tools as any).search.execute({
      query: 'toLowerCase undefined crash profile save',
      filters: { project: 'demo', repo: 'example' },
      top_k: 5
    });
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

